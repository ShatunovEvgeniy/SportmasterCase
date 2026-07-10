FROM python:3.12-slim

WORKDIR /app

# Системные зависимости для сборки cryptography/pandas и т.п.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Непривилегированный пользователь — не запускаем сервис от root внутри контейнера
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

ENV PYTHONIOENCODING=utf-8 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
