# Блок 1 — SQL анализ и валидация данных
Для первого задания была развернута база данных PostgreSQL. Весь код содержиться в папке block_1.

Для запуска образа можно воспользоваться командой.
```
docker-compose up -d
```
После чего будет создан docker-контейнер

Для подключения можно посмотреть ID контейнера
```
docker ps

CONTAINER ID   IMAGE         COMMAND                  CREATED          STATUS          PORTS                                         NAMES
8c13fe8bc176   postgres:16   "docker-entrypoint.s…"   32 minutes ago   Up 31 minutes   0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp   block_1-pgdatabase-1
```

Чтобы подключиться к контейнеру
```
sudo docker exec -it 8c13fe8bc176 /bin/bash
```

Далее внутри контейнера можно подключиться при помощи psql-клиента
```
psql -U postgres -d postgres
``

И проверить созданные таблицы
```
postgres=# \dt
           List of relations
 Schema |    Name    | Type  |  Owner   
--------+------------+-------+----------
 public | orders_agg | table | postgres
 public | orders_raw | table | postgres
(2 rows)

```

#### init.sql
Данный файл находиться в block_1 и создает две таблицы с сырыми и агрегированными данными.

```
CREATE TABLE IF NOT EXISTS orders_raw(
        order_id int PRIMARY KEY,
        user_id int NOT NULL,
        created_at timestamptz NOT NULL,
        total_amount numeric(18,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS orders_agg(
        user_id int PRIMARY KEY,
        total_orders int NOT NULL,
        total_revenue numeric(20,12) NOT NULL
);
```
Исследовав данные, можно сделать вывод для создания типов по столбцам. Во первых стоит создать первичные ключи для двух таблиц по order_id и user_id для того, чтобы наши данные не дублировались по строкам. Также стоит учитывать пустые строки, указав NOT NULL. При работе с более точными значениями внутри таблиц был выбран тип numeric и указана точность и масштаб.

После чего скрипт скопирует наши данные внутрь таблиц orders_agg и orders_raw.
```
COPY orders_raw
FROM '/data/orders_raw.csv'
DELIMITER ','
CSV HEADER;

COPY orders_agg
FROM '/data/orders_agg.csv'
DELIMITER ','
CSV HEADER;
```
