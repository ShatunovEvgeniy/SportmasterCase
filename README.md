# Спортмастер — AI-summary отзывов (кейс)

Прототип фичи: автоматическая AI-сводка отзывов покупателей на карточке товара
(суть отзыва, достоинства/недостатки, аспекты, цитаты) + презентационный сайт кейса.

## Архитектура

```
SportmasterCase/
├── backend/               Python: сбор/очистка отзывов, LLM-пайплайн (YandexGPT),
│                           FastAPI (порт 8000) — единственная точка записи в БД sportmaster
├── Sportmaster_frontend/  Java/Tomcat (порт 8080): каталог, карточка товара,
│                           статичный сайт-презентация кейса (sportmaster-case.html)
├── start-all.ps1          Запуск всего стека одной командой (Windows)
├── start-all.sh           То же самое, но для Ubuntu / Linux
├── docker-compose.yml     Альтернативный запуск: MySQL + backend + frontend + nginx
└── nginx/, mysql-init/    Конфиг nginx и init-скрипт MySQL для Docker Compose
```

Две базы MySQL на одном сервере:
- `sportmaster` — отзывы, рейтинги, AI-сводки, аспекты (пишет только backend)
- `online_shop` — карточки товаров, категории, пользователи (пишет только Java)

Фронтенд (Java) **читает** обе базы напрямую, но **пишет** только через FastAPI
(лайк/дизлайк сводки, новый отзыв, обратная связь) — так работа с LLM и пересчёт
сводки остаются на стороне Python.

## Требования

- Windows, MySQL Server 8.4 (запущенный локально, схемы `sportmaster` и `online_shop`
  уже созданы — см. `backend/src/scripts/create_database.sql` и
  `Sportmaster_frontend/src/main/resources/db/create_online_shop.sql`)
- JDK 17+, Maven 3.9+
- Python 3.11+ с виртуальным окружением в `backend/.venv`
  (если его нет: `cd backend; python -m venv .venv; .venv\Scripts\pip install -r requirements.txt`)
- Файл `backend/.env` с ключом YandexGPT (`YANDEX_API_KEY`, `YANDEX_FOLDER_ID`) и
  настройками MySQL (`MYSQL_USER`, `MYSQL_PASSWORD`, ...)

## Запуск одной командой

```powershell
powershell -ExecutionPolicy Bypass -File .\start-all.ps1
```

Скрипт поднимает MySQL → FastAPI → Tomcat по очереди, пропуская то, что уже
запущено. В конце печатает ссылку на сайт (локально и в локальной сети).

## Запуск вручную (если нужно по шагам)

1. **MySQL**: `mysqld --defaults-file="C:\ProgramData\MySQL\MySQL Server 8.4\my.ini"`
2. **Backend**:
   ```
   cd backend
   .venv\Scripts\python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000
   ```
3. **Frontend**:
   ```
   cd Sportmaster_frontend
   mvn -q package -DskipTests
   copy target\Project-1.0-SNAPSHOT.war "<CATALINA_HOME>\webapps\ROOT.war"
   <CATALINA_HOME>\bin\startup.bat
   ```

Открыть: **http://localhost:8080/sportmaster-case.html**

## Раздать сайт в локальной сети

FastAPI и Tomcat уже слушают все интерфейсы (`0.0.0.0`), поэтому достаточно:

1. Узнать свой IP: `ipconfig` → IPv4-адрес Wi-Fi/Ethernet
2. Открыть порты 8080 и 8000 в файрволе (один раз, от администратора):
   ```powershell
   New-NetFirewallRule -DisplayName "SportmasterCase-LAN" -Direction Inbound -Protocol TCP -LocalPort 8080,8000 -Action Allow -Profile Private
   ```
3. Дать коллеге ссылку: `http://<твой-IP>:8080/sportmaster-case.html`
   (нужно быть в одной Wi-Fi-сети, не гостевой)

## Раздать сайт из интернета (не только локальная сеть)

Сайт использует **два** порта на одном хосте — Tomcat (8080, сама страница) и
FastAPI (8000, API для лайков/отзывов/AI-сводки), причём фронтенд сам
подставляет адрес API как `<хост-страницы>:8000` (см. `product_info.jsp`).
Поэтому проще всего сохранить именно эту связку «один хост — два порта», а не
городить два независимых туннеля с разными адресами.

### Вариант А (рекомендуется для разовой защиты): ngrok — без роутера и без риска для домашней сети

Ngrok поднимает временный публичный HTTPS-адрес поверх твоих локальных портов,
не трогая настройки роутера и файрвол наружу. Идеально для «показать один раз
на защите» — после защиты просто закрываешь туннель.

```powershell
# 1. Установить (один раз)
winget install ngrok.ngrok

# 2. Зарегистрироваться на ngrok.com (бесплатно) и добавить свой токен (один раз)
ngrok config add-authtoken <твой-токен-из-личного-кабинета>

# 3. Поднять туннель сразу на оба порта (два туннеля в одном процессе)
ngrok start --all --config ngrok.yml
```

Файл `ngrok.yml` рядом со скриптом (создать один раз):
```yaml
version: "2"
authtoken: <твой-токен>
tunnels:
  site:
    proto: http
    addr: 8080
  api:
    proto: http
    addr: 8000
```

Ngrok выведет два разных публичных адреса (для `site` и для `api`). Так как
это уже **разные** хосты (не `<тот же хост>:8000`), нужно один раз подменить
в `Sportmaster_frontend/src/main/webapp/product_info.jsp` строку:
```js
const API_BASE = "http://" + window.location.hostname + ":8000";
```
на постоянный адрес туннеля `api` (например `const API_BASE = "https://xxxx.ngrok-free.app";`),
пересобрать и передеплоить (`mvn -q package`, скопировать WAR, перезапустить Tomcat).
После защиты верни строку обратно, чтобы не потерять работу в локальной сети.

### Вариант Б: проброс портов на роутере + DDNS (для постоянной ссылки)

Менее безопасно (домашняя сеть становится доступна снаружи), но не требует
сторонних сервисов и правки JS — хост остаётся тем же самым, просто снаружи.

1. В админке роутера пробросить порты `8080` и `8000` (TCP) на локальный IP
   этого компьютера (`172.27.87.224` или свежий из `ipconfig`).
2. Разрешить эти порты в файрволе уже для профиля **Public** (не только Private):
   ```powershell
   New-NetFirewallRule -DisplayName "SportmasterCase-WAN" -Direction Inbound -Protocol TCP -LocalPort 8080,8000 -Action Allow -Profile Public
   ```
3. Узнать внешний IP: `curl.exe ifconfig.me` — или настроить бесплатный DDNS
   (например DuckDNS/No-IP), если провайдер меняет IP динамически.
4. Дать ссылку: `http://<внешний-IP-или-DDNS>:8080/sportmaster-case.html`

⚠️ **Не пробрасывай порт 3306 (MySQL) наружу** — только 8080 и 8000. Этот
вариант держит сервер реально открытым в интернет, поэтому после защиты
рекомендуется закрыть проброс портов и удалить правило файрвола.

## Запуск на Ubuntu / Linux

Тот же стек, только сервисы ставятся через `apt` и управляются `systemd`
вместо `.exe`/`.bat`. Рассчитано на Ubuntu 22.04/24.04 (пакет `tomcat10` в
`apt` появился именно с этих версий); я собирал и тестировал проект только на
Windows, так что команды ниже — по стандартным практикам Ubuntu, а не
проверены живьём. Если что-то не взлетит с первого раза — это ожидаемо,
пиши, поправим.

### 1. Пакеты (один раз)

```bash
sudo apt update
sudo apt install -y mysql-server openjdk-17-jdk maven python3-venv python3-pip tomcat10
```

### 2. MySQL — базы и пользователи (один раз)

Схемы `sportmaster` и `online_shop` совпадают с Windows-версией. Учётные данные
для `online_shop` (`root`/`mipt!mySQL8045`) захардкожены в
`Sportmaster_frontend/src/main/java/com/example/util/DatabaseConnection.java` —
Java не читает `.env`, поэтому либо заведи такого же пользователя на Ubuntu,
либо один раз поправь эти константы под себя и пересобери.

```bash
sudo mysql <<'SQL'
ALTER USER 'root'@'localhost' IDENTIFIED BY 'mipt!mySQL8045';
CREATE USER IF NOT EXISTS 'sportmaster'@'localhost' IDENTIFIED BY 'sportmaster123';
CREATE DATABASE IF NOT EXISTS online_shop;
CREATE DATABASE IF NOT EXISTS sportmaster;
GRANT ALL PRIVILEGES ON online_shop.* TO 'root'@'localhost';
GRANT ALL PRIVILEGES ON sportmaster.* TO 'sportmaster'@'localhost';
FLUSH PRIVILEGES;
SQL

mysql -u root -p'mipt!mySQL8045' online_shop < Sportmaster_frontend/src/main/resources/db/create_online_shop.sql
mysql -u sportmaster -psportmaster123 sportmaster < backend/src/scripts/create_database.sql
```

### 3. Backend (один раз — окружение, дальше просто запуск)

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cd ..
```
Убедись, что `backend/.env` содержит `MYSQL_HOST=localhost` и ключ YandexGPT
(`YANDEX_API_KEY`, `YANDEX_FOLDER_ID`) — как и на Windows.

### 4. Frontend — сборка и деплой в Tomcat

```bash
cd Sportmaster_frontend
mvn -q package -DskipTests
sudo cp target/Project-1.0-SNAPSHOT.war /var/lib/tomcat10/webapps/ROOT.war
sudo systemctl restart tomcat10
cd ..
```

### 5. Запуск одной командой

```bash
chmod +x start-all.sh   # один раз
./start-all.sh
```

Скрипт (лежит рядом, `start-all.sh`) поднимает MySQL → FastAPI → Tomcat через
`systemctl`, пропуская уже запущенное, и в конце печатает ссылку на сайт —
локально и по IP в локальной сети.

Открыть: **http://localhost:8080/sportmaster-case.html**

### Раздать в локальной сети / интернете — Ubuntu

Вместо `New-NetFirewallRule` — `ufw`:
```bash
sudo ufw allow 8080/tcp
sudo ufw allow 8000/tcp
```
Дальше всё как в разделах выше про Windows: свой IP — `ip addr show` (вместо
`ipconfig`), для интернета — тот же ngrok (`sudo snap install ngrok`, дальше
команды идентичны) или проброс портов на роутере с тем же предупреждением про
3306.

## Запуск через Docker Compose

Работает одинаково на Windows/macOS/Linux — нужен только Docker Desktop (или
Docker Engine + Compose plugin на Linux). Поднимает 4 контейнера: `mysql`,
`backend` (FastAPI), `frontend` (Tomcat) и `nginx` — единственный, который
торчит наружу, на порту 80. MySQL, backend и frontend наружу не публикуются
вообще — только по внутренней docker-сети.

```
SportmasterCase/
├── docker-compose.yml
├── .env.example           Шаблон секретов — скопировать в .env и заполнить
├── mysql-init/             Скрипт создания пользователя sportmaster в MySQL
├── nginx/nginx.conf        Единая точка входа: / → Tomcat, /api/ → FastAPI
├── backend/Dockerfile
└── Sportmaster_frontend/Dockerfile
```

### Запуск

```bash
cp .env.example .env
# открыть .env и заменить все "change-me-..." на реальные пароли,
# плюс вписать YANDEX_API_KEY / YANDEX_FOLDER_ID
notepad .env      # Windows
nano .env         # Linux/macOS

docker compose up -d --build
```

Открыть: **http://localhost/sportmaster-case.html** (порт 80, не 8080 — за
входом уже стоит nginx).

Данные (86k отзывов) при первом запуске не грузятся — поднимается только схема
и 3 демо-товара без AI-сводок. Загрузить реальный датасет и посчитать сводки:
```bash
docker compose exec backend python -m src.scripts.init_data --input-file data/raw/<файл>.xlsx
docker compose exec backend python -m src.scripts.run_single_product --model-id 17960
```

Логи: `docker compose logs -f backend` / `frontend` / `nginx` / `mysql`.
Остановить: `docker compose down` (данные MySQL остаются в volume `mysql-data`,
удалить насовсем — `docker compose down -v`).

### Как это устроено внутри

- **MySQL**: пароли/пользователи не хардкожены — `mysql-init/01-init-sportmaster-db.sh`
  создаёт пользователя `sportmaster` из переменных окружения контейнера (а не из
  файла в репозитории), пользователь `online_shop_app` создаётся автоматически
  самим образом MySQL через `MYSQL_USER`/`MYSQL_PASSWORD`.
- **backend**: контейнер работает от непривилегированного `appuser`, не от root.
- **frontend/backend**: узнают адрес БД через `DB_HOST`/`MYSQL_HOST=mysql` (имя
  сервиса в docker-сети) — при обычном запуске без Docker эти переменные не
  заданы, и код падает обратно на `localhost`, как раньше.
- **nginx**: единственная точка входа, скрывает свою версию (`server_tokens off`),
  ставит базовые заголовки (`X-Frame-Options`, `X-Content-Type-Options`), режет
  тело запроса (`client_max_body_size 1m`) и ограничивает частоту запросов к
  `/api/.../reviews` (эндпоинт дорогой — дёргает настоящий вызов LLM).

### Оценка безопасности

Что уже сделано правильно:
- Секреты не в репозитории — `.env` в `.gitignore`, в коде только `${ПЕРЕМЕННЫЕ}`.
- MySQL, backend, frontend не публикуют порты наружу — доступны только друг другу
  по внутренней docker-сети, единственный внешний вход — nginx на 80.
- Пароль MySQL-пользователя `sportmaster` попадает в БД через shell-скрипт из
  переменных окружения, а не хранится в закоммиченном `.sql`-файле.
- Контейнер backend не работает от root.
- Отзывы/лайки идут через `PreparedStatement` (Java) и SQLAlchemy ORM (Python) —
  SQL-инъекций не нашёл. Весь вывод пользовательского текста на JSP — через `${...}`
  (EL экранирует HTML по умолчанию), в JS — через явный `escapeHtml()` — XSS с
  текстом отзыва не воспроизводится.

Что оставил как есть, но стоит знать перед тем, как выкатывать это дальше учебного стенда:
- **Нет HTTPS.** nginx слушает голый HTTP — трафик (включая текст отзывов) идёт
  в открытом виде. Для локальной защиты/LAN это некритично, для реального
  интернета — нужен сертификат (Let's Encrypt/Cloudflare) перед портом 80.
- **Нет авторизации на запись.** Любой, кто достучится до `/api/products/{id}/reviews`
  или `/summary/like`, может слать что угодно от чужого имени без ограничений —
  сайта, привязки к пользователю, капчи нет вообще. Добавил на nginx лимит
  частоты запросов (6 отзывов/мин и 60 остальных запросов/мин с одного IP) —
  это снижает риск, но не заменяет настоящую авторизацию.
- **POST отзыва запускает платный вызов LLM.** Каждый новый отзыв — это реальный
  запрос к YandexGPT. Без лимита частоты (уже добавленного) кто угодно снаружи
  мог бы накручивать счёт за API просто спамом. Rate limit есть, полноценной
  защиты (например, по количеству отзывов в сутки на IP) — нет.
- **CORS `allow_origins="*"`** — намеренно, сайт открывают с разных адресов
  (localhost/LAN IP/домен), заранее их не перечислить. Отключил `allow_credentials`
  (было `True` без единой куки/сессии в проекте — небезопасная и бессмысленная
  комбинация с wildcard-origin), но сам wildcard оставил осознанно.
- **`/docs`, `/openapi.json`** проксируются наружу — весь API виден любому. Для
  демо это скорее плюс (можно показать на защите), для прод-версии — обычно
  прячут за отдельным доступом.
- **Fallback-пароли в исходниках.** Если забыть переменные окружения —
  `DatabaseConnection.java` и `settings.py` тихо откатятся на пароли по
  умолчанию, зашитые в код (те же, что использовались при разработке без
  Docker). В Docker это не сработает без `.env` (контейнер MySQL не поднимется
  без `MYSQL_ROOT_PASSWORD`), но сами дефолтные пароли всё равно стоит сменить
  перед тем, как показывать код кому-то ещё, раз они попадали в этот чат.

Итог: для демонстрации на защите — более чем достаточно (сервисы изолированы,
секретов в репозитории нет, базовая защита от спама есть). Для настоящего
прод-окружения с реальными пользователями не хватает HTTPS и авторизации —
это следующий шаг, если проект пойдёт дальше кейса.

## Полезное

- Пересчитать AI-сводку для товара вручную:
  `backend\.venv\Scripts\python -m src.scripts.run_single_product --model-id 17960`
- Пересчитать оценки/имена/плюсы-минусы для всех отзывов заново:
  `backend\.venv\Scripts\python -m src.scripts.calculate_review_ratings --input-file <путь к исходному xlsx>`
- Логи FastAPI: `backend\uvicorn.log` / `uvicorn.err.log`
- Логи Tomcat: `<CATALINA_HOME>\logs\catalina.out`

### Когда пересчитывается AI-сводка

Новый отзыв **не** запускает LLM-пайплайн каждый раз — это платный вызов, и на
товаре с сотнями отзывов один новый отзыв погоды не делает. Сводка
пересчитывается, только когда отзывов с момента прошлой генерации набралось
+20% (`Database.should_regenerate` в `backend/src/db/repository.py`). Рейтинг
на карточке при этом обновляется всегда, сразу же — порог касается только
дорогого вызова LLM. Пока порог не достигнут, API отвечает сразу (без прогресс-
бара) с текстом вида «Сводка обновится, когда наберётся ещё N новых отзывов».
Для товаров с малым числом отзывов (кеды/куртка в демо) порог — 1-2 отзыва, для
кроссовок (566 отзывов) — около сотни, так что на них перегенерацию так просто
не увидеть; для демонстрации эффекта лучше брать товар с малым количеством
отзывов или временно занизить порог в коде.
