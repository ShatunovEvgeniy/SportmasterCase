import json
import re
import openai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.config.settings import settings


class YandexGPTClient:
    """
    Обёртка над Responses API Yandex Cloud. Модель передаётся явно при создании
    клиента — MAP и REDUCE этапы пайплайна используют РАЗНЫЕ модели (см.
    settings.yandex_map_model / settings.yandex_reduce_model), поэтому клиент
    больше не читает единственную settings.yandex_model сам.

    У разных моделей разная форма ответа в Responses API:
    - gpt-oss (и вообще "message"-стиль): response.output[0].content[0].text
    - YandexGPT-нативные модели (yandexgpt / yandexgpt-lite): response.output[0].summary[0].text
    call_json пробует оба варианта по очереди, чтобы не завязываться на то, какая
    именно модель сейчас используется на каждом из этапов.
    """

    def __init__(self, model: str):
        self.client = openai.OpenAI(
            api_key=settings.yandex_api_key,
            base_url="https://ai.api.cloud.yandex.net/v1",
            project=settings.yandex_folder_id
        )
        self.model_uri = f"gpt://{settings.yandex_folder_id}/{model}"

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((openai.RateLimitError, openai.APIError, openai.APIConnectionError)),
        reraise=True,
    )
    def call_json(self, system: str, user: str, temperature: float = 0.2) -> dict:
        response = self.client.responses.create(
            model=self.model_uri,
            input=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=temperature,
            text={"format": {"type": "json_object"}}
        )

        content = self._extract_text(response)
        content = re.sub(r'^```json\s*|^\s*```|```\s*$', '', content, flags=re.MULTILINE).strip()
        return json.loads(content)

    @staticmethod
    def _extract_text(response) -> str:
        output_text = getattr(response, "output_text", None)
        if output_text:
            return output_text

        item = response.output[0]
        content = getattr(item, "content", None)
        if content:
            return content[0].text

        summary = getattr(item, "summary", None)
        if summary:
            return summary[0].text

        raise ValueError(f"Не удалось извлечь текст из ответа LLM: неизвестная форма output[0]={item!r}")


if __name__ == "__main__":
    # Тест клиента (требует валидных ключей в .env)
    try:
        client = YandexGPTClient(settings.yandex_reduce_model)
        res = client.call_json("Ты бот.", "Верни JSON: {'status': 'ok'}")
        print("LLM Client test passed:", res)
    except Exception as e:
        print(f"LLM Client test failed (check .env): {e}")