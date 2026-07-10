#!/usr/bin/env bash
# Sportmaster AI-Summary demo — запуск всего стека одной командой (Ubuntu/Linux).
#
# Поднимает по порядку (пропускает то, что уже запущено):
#   1. MySQL   (порт 3306, через systemd)
#   2. FastAPI (порт 8000, слушает 0.0.0.0 — доступен и из локальной сети)
#   3. Tomcat  (порт 8080, слушает 0.0.0.0 — доступен и из локальной сети)
#
# Использование:
#   chmod +x start-all.sh && ./start-all.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT_DIR/backend"
VENV_PYTHON="$BACKEND/.venv/bin/python"

port_open() {
    timeout 1 bash -c "echo > /dev/tcp/127.0.0.1/$1" 2>/dev/null
}

echo "=== 1. MySQL (3306) ==="
if port_open 3306; then
    echo "уже запущен, пропускаю"
else
    sudo systemctl start mysql
    sleep 3
    if port_open 3306; then echo "MySQL поднят"; else echo "MySQL не поднялся, смотри: journalctl -u mysql -n 50"; fi
fi

echo
echo "=== 2. FastAPI (8000) ==="
if port_open 8000; then
    echo "уже запущен, пропускаю"
else
    if [ ! -x "$VENV_PYTHON" ]; then
        echo "Не найден venv: $VENV_PYTHON"
        echo "Создай его один раз: cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
    else
        (cd "$BACKEND" && PYTHONIOENCODING=utf-8 nohup "$VENV_PYTHON" -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000 \
            > "$BACKEND/uvicorn.log" 2> "$BACKEND/uvicorn.err.log" & disown)
        sleep 4
        if port_open 8000; then echo "FastAPI поднят"; else echo "FastAPI не поднялся, смотри $BACKEND/uvicorn.err.log"; fi
    fi
fi

echo
echo "=== 3. Tomcat (8080) ==="
if port_open 8080; then
    echo "уже запущен, пропускаю"
else
    sudo systemctl start tomcat10
    sleep 5
    if port_open 8080; then echo "Tomcat поднят"; else echo "Tomcat не поднялся, смотри: journalctl -u tomcat10 -n 50"; fi
fi

LAN_IP="$(hostname -I 2>/dev/null | awk '{print $1}' || true)"

echo
echo "=== Готово ==="
echo "На этом компьютере:  http://localhost:8080/sportmaster-case.html"
if [ -n "$LAN_IP" ]; then
    echo "В локальной сети:    http://$LAN_IP:8080/sportmaster-case.html"
    echo "(порты 8080 и 8000 должны быть разрешены в ufw — см. README.md)"
fi
