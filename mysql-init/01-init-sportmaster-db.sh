#!/bin/bash
# Второй пользователь/база (sportmaster) — online_shop уже создан образом MySQL
# через MYSQL_DATABASE/MYSQL_USER/MYSQL_PASSWORD (см. docker-compose.yml).
# Это .sh, а не .sql, специально — только shell-скрипты в docker-entrypoint-initdb.d
# видят переменные окружения контейнера, а значит пароль не приходится хардкодить
# в файле, который лежит в репозитории.
set -euo pipefail

mysql -u root -p"${MYSQL_ROOT_PASSWORD}" <<-SQL
    CREATE DATABASE IF NOT EXISTS sportmaster CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    CREATE USER IF NOT EXISTS '${SPORTMASTER_DB_USER}'@'%' IDENTIFIED BY '${SPORTMASTER_DB_PASSWORD}';
    GRANT ALL PRIVILEGES ON sportmaster.* TO '${SPORTMASTER_DB_USER}'@'%';
    FLUSH PRIVILEGES;
SQL
