import json
import re
import openai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.config.settings import settings


class YandexGPTClient:
    def __init__(self):
        self.client = openai.OpenAI(
            api_key=settings.yandex_api_key,
            base_url="https://ai.api.cloud.yandex.net/v1",
            project=settings.yandex_folder_id
        )
        self.model_uri = f"gpt://{settings.yandex_folder_id}/{settings.yandex_model}"

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

        content = getattr(response, "output_text", None) or response.output[0].content[0].text
        content = re.sub(r'^```json\s*|^\s*```|```\s*$', '', content, flags=re.MULTILINE).strip()
        return json.loads(content)


if __name__ == "__main__":
    # Тест клиента (требует валидных ключей в .env)
    try:
        client = YandexGPTClient()
        res = client.call_json("Ты бот.", "Верни JSON: {'status': 'ok'}")
        print("LLM Client test passed:", res)
    except Exception as e:
        print(f"LLM Client test failed (check .env): {e}")