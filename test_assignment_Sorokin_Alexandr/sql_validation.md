# Блок 1 — SQL анализ и валидация данных
Для первого задания была развернута база данных PostgreSQL. Весь код содержится в папке block_1.

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
docker exec -it 8c13fe8bc176 /bin/bash
```

Далее внутри контейнера можно подключиться при помощи psql

```
psql -U postgres -d postgres
```

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
Файл init.sql находится в папке block_1 и выполняется автоматически при первом запуске контейнера.
Он создаёт таблицы с сырыми и агрегированными данными.

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
Исследовав данные внутри csv файлов можно указать нужные типы:
```
PRIMARY KEY - Гарантирует уникальность записей и предотвращает дублирование данных.
NOT NULL - Исключает появление неполных записей.
timestamptz - Дает возможность работать с датами с учетом временных зон.
numeric - Используется для хранения значений без потери точости.
```


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

## Вопросы

##### 1.Найди пользователей, у которых расхождение между orders_agg.total_orders и реальным количеством заказов в orders_raw

Чтобы посчитать расхождение между заказами внутри таблиц сначала стоит обратиться понять что именно нам необходимо посчитать.
```
select * from orders_agg;

user_id | total_orders |  total_revenue  
---------+--------------+-----------------
       1 |            8 | 2323.0000000000
       2 |            5 | 1212.0000000000
       3 |            6 | 1856.0000000000
       4 |            4 | 1035.0000000000
       5 |            6 | 1727.0000000000
       6 |            4 |  882.0000000000



select * from orders_raw;

order_id | user_id |     created_at      | total_amount 
----------+---------+---------------------+--------------
        1 |     103 | 2024-07-07 15:11:00 |          473
        2 |     180 | 2024-06-07 18:20:00 |          418
        3 |      93 | 2024-05-09 17:56:00 |          285
        4 |      15 | 2024-06-14 23:18:00 |          132
        5 |     107 | 2024-06-05 01:40:00 |           91
        6 |      72 | 2024-06-20 02:30:00 |          474
        7 |     189 | 2024-06-15 06:40:00 |          150

```
Внутри таблицы orders_raw необходимо посчитать кол-во заказов для каждого пользователя.

```
SELECT 
    user_id, 
    COUNT(*) AS total_orders
FROM orders_raw
GROUP BY user_id
ORDER BY user_id;


user_id | total_orders 
---------+--------------
       1 |            8
       2 |            5
       3 |            6
       4 |            4
       5 |            6
       6 |            4
       7 |            3
       8 |            9
       9 |            5
      10 |            2
```

Теперь можно объединить его с таблицей, которая содержит агрегированные данные.

```
SELECT
    raw.user_id AS raw_user_id,
    raw.total_orders AS raw_total_orders,
    agg.user_id AS agg_user_id,
    agg.total_orders AS agg_total_orders
FROM (

    SELECT
        user_id,
        COUNT(*) AS total_orders
    FROM orders_raw
    GROUP BY user_id
    ) AS raw
LEFT JOIN orders_agg AS agg
ON raw.user_id = agg.user_id 
WHERE raw.total_orders <> agg.total_orders;

 raw_user_id | raw_total_orders | agg_user_id | agg_total_orders 
-------------+------------------+-------------+------------------
           9 |                5 |           9 |                4
          23 |                4 |          23 |                3
          35 |                5 |          35 |                4
          41 |                3 |          41 |                2
          42 |                3 |          42 |                2
          50 |                4 |          50 |                3
          60 |                5 |          60 |                4
          63 |                6 |          63 |                5
          65 |                5 |          65 |                4
          66 |                3 |          66 |                2
          78 |                3 |          78 |                2
          80 |                3 |          80 |                2
          88 |                3 |          88 |                2
          96 |                8 |          96 |                7
          97 |                2 |          97 |                1
         116 |                5 |         116 |                4
         117 |                8 |         117 |                7
         127 |                4 |         127 |                3
         169 |                1 |         169 |                0
         180 |                6 |         180 |                5
         191 |                7 |         191 |                6
         194 |                5 |         194 |                4
         200 |                5 |         200 |                4
(23 rows)

```

Попробуем ускорить запрос включив паметр timing

```
\timing on
```

После выполнения запроса мы получили следующее значение

```
postgres=# SELECT
    raw.user_id AS raw_user_id,
    raw.total_orders AS raw_total_orders,
    agg.user_id AS agg_user_id,
    agg.total_orders AS agg_total_orders
FROM (

    SELECT
        user_id,
        COUNT(*) AS total_orders
    FROM orders_raw
    GROUP BY user_id
    ) AS raw
LEFT JOIN orders_agg AS agg
ON raw.user_id = agg.user_id
WHERE raw.total_orders <> agg.total_orders;
 raw_user_id | raw_total_orders | agg_user_id | agg_total_orders 
-------------+------------------+-------------+------------------
           9 |                5 |           9 |                4
          23 |                4 |          23 |                3
          35 |                5 |          35 |                4
          41 |                3 |          41 |                2
          42 |                3 |          42 |                2
          50 |                4 |          50 |                3
          60 |                5 |          60 |                4
          63 |                6 |          63 |                5
          65 |                5 |          65 |                4
          66 |                3 |          66 |                2
          78 |                3 |          78 |                2
          80 |                3 |          80 |                2
          88 |                3 |          88 |                2
          96 |                8 |          96 |                7
          97 |                2 |          97 |                1
         116 |                5 |         116 |                4
         117 |                8 |         117 |                7
         127 |                4 |         127 |                3
         169 |                1 |         169 |                0
         180 |                6 |         180 |                5
         191 |                7 |         191 |                6
         194 |                5 |         194 |                4
         200 |                5 |         200 |                4
(23 rows)

Time: 0.457 ms
postgres=# 

```

Для начала стоит посмотреть индексы внутри таблиц
```

postgres=# \d orders_agg
                    Table "public.orders_agg"
    Column     |      Type      | Collation | Nullable | Default 
---------------+----------------+-----------+----------+---------
 user_id       | integer        |           |          | 
 total_orders  | integer        |           |          | 
 total_revenue | numeric(18,10) |           |          | 


postgres=# \d orders_raw
                          Table "public.orders_raw"
    Column    |            Type             | Collation | Nullable | Default 
--------------+-----------------------------+-----------+----------+---------
 order_id     | integer                     |           |          | 
 user_id      | integer                     |           |          | 
 created_at   | timestamp without time zone |           |          | 
 total_amount | integer                     |           |          | 


```

Как видим индексы внутри таблиц отсутствуют, можно создать индексы по столбцу user_id для таблицы orders_agg и по столбцу order_id для таблицы orders_raw.

```
Для таблицы orders_agg:
CREATE INDEX user_id_idx ON orders_agg (user_id);


Для таблицы orders_raw:
CREATE INDEX order_id_idx ON orders_raw(order_id);


postgres=# \d orders_agg
                    Table "public.orders_agg"
    Column     |      Type      | Collation | Nullable | Default 
---------------+----------------+-----------+----------+---------
 user_id       | integer        |           |          | 
 total_orders  | integer        |           |          | 
 total_revenue | numeric(18,10) |           |          | 
Indexes:
    "user_id_idx" btree (user_id)

postgres=# \d orders_raw
                          Table "public.orders_raw"
    Column    |            Type             | Collation | Nullable | Default 
--------------+-----------------------------+-----------+----------+---------
 order_id     | integer                     |           |          | 
 user_id      | integer                     |           |          | 
 created_at   | timestamp without time zone |           |          | 
 total_amount | integer                     |           |          | 
Indexes:
    "order_id_idx" btree (order_id)



```

Теперь повторим наш запрос

```
 raw_user_id | raw_total_orders | agg_user_id | agg_total_orders 
-------------+------------------+-------------+------------------
           9 |                5 |           9 |                4
          23 |                4 |          23 |                3
          35 |                5 |          35 |                4
          41 |                3 |          41 |                2
          42 |                3 |          42 |                2
          50 |                4 |          50 |                3
          60 |                5 |          60 |                4
          63 |                6 |          63 |                5
          65 |                5 |          65 |                4
          66 |                3 |          66 |                2
          78 |                3 |          78 |                2
          80 |                3 |          80 |                2
          88 |                3 |          88 |                2
          96 |                8 |          96 |                7
          97 |                2 |          97 |                1
         116 |                5 |         116 |                4
         117 |                8 |         117 |                7
         127 |                4 |         127 |                3
         169 |                1 |         169 |                0
         180 |                6 |         180 |                5
         191 |                7 |         191 |                6
         194 |                5 |         194 |                4
         200 |                5 |         200 |                4
(23 rows)

Time: 0.441 ms
```

Также можно было бы использовать CTE, что могло бы ускорить выполнение запроса при повторном использовании. Используем MATERIALIZED, чтобы создать VIEW(при этом данные схраняются на диске). 

```


postgres=# SELECT
    raw.user_id AS raw_user_id,
    raw.total_orders AS raw_total_orders,
    agg.user_id AS agg_user_id,
    agg.total_orders AS agg_total_orders
FROM (

    SELECT      <-------------------------------------- создан MATERIALIZED VIEW; 
        user_id,
        COUNT(*) AS total_orders
    FROM orders_raw
    GROUP BY user_id
    ) AS raw
LEFT JOIN orders_agg AS agg
ON raw.user_id = agg.user_id
WHERE raw.total_orders <> agg.total_orders;



CREATE MATERIALIZED VIEW raw_counts AS
SELECT 
    user_id,
    COUNT(*) AS total_orders
FROM orders_raw
GROUP BY user_id;
```

##### 2.Найди таких пользователей, у которых расхождение по выручке более чем на 5%

Чтобы рассчитать расхождение по выручке между таблицами стоит снова рассмотреть что за данные мы в них используем. 
```
select * from orders_agg;

user_id | total_orders |  total_revenue
---------+--------------+-----------------
       1 |            8 | 2323.0000000000
       2 |            5 | 1212.0000000000
       3 |            6 | 1856.0000000000
       4 |            4 | 1035.0000000000
       5 |            6 | 1727.0000000000
       6 |            4 |  882.0000000000



select * from orders_raw;

order_id | user_id |     created_at      | total_amount
----------+---------+---------------------+--------------
        1 |     103 | 2024-07-07 15:11:00 |          473
        2 |     180 | 2024-06-07 18:20:00 |          418
        3 |      93 | 2024-05-09 17:56:00 |          285
        4 |      15 | 2024-06-14 23:18:00 |          132
        5 |     107 | 2024-06-05 01:40:00 |           91
        6 |      72 | 2024-06-20 02:30:00 |          474
        7 |     189 | 2024-06-15 06:40:00 |          150


``` 


Находим total_revenue в таблице orders_raw
```
SELECT
    user_id,
    sum(total_amount) AS total_revenue_raw
FROM orders_raw
GROUP BY user_id
ORDER BY user_id;

user_id | total_revenue_raw 
---------+-------------------
       1 |              2323
       2 |              1212
       3 |              1856
       4 |              1035
       5 |              1727
       6 |               882
       7 |               873
       8 |              2485
       9 |              1384
      10 |               243

```

Проведем объединение двух таблиц в одну, после чего найдем процент расхождения между объединенными таблицами.

```
SELECT 
    raw.user_id,
    100.0 * abs(raw.total_revenue_raw - orders_agg.total_revenue ) / orders_agg.total_revenue as raznost
FROM orders_agg
LEFT JOIN (
    SELECT
        user_id,
        SUM(total_amount) AS total_revenue_raw
    FROM orders_raw
    GROUP BY user_id
) AS raw
ON raw.user_id = orders_agg.user_id
WHERE 100.0 * abs(raw.total_revenue_raw - orders_agg.total_revenue ) / orders_agg.total_revenue > 5;

 user_id |       raznost       
---------+---------------------
       9 | 10.2028971930582442
      23 | 10.2028971930581618
      35 | 10.2028971930605421
      41 | 10.2028971930651881
      42 | 10.2028971930682237
      50 | 10.2028971930604229
      60 | 10.2028971930573431
      63 | 10.2028971930565547
      65 | 10.2028971930602397
      66 | 10.2028971930631463
      78 | 10.2028971930615249
      80 | 10.2028971930554853
      88 | 10.2028971930612732
      96 | 10.2028971930628305
      97 | 10.2028971930557540
     116 | 10.2028971930633879
     117 | 10.2028971930587808
     127 | 10.2028971930563531
     169 | 10.2028971930702418
     180 | 10.2028971930620582
     191 | 10.2028971930581313
     194 | 10.2028971930619295
     200 | 10.2028971930624438
(23 rows)

Time: 0.607 ms

```


**Оптимизация:**

1) Так как наш запрос производит объединение по данным, которые не вызовут появления пустых значений NULL, то можно явно указать тип объединения как INNER JOIN. Это сделает наш код более читаемым.
```
SELECT
    raw.user_id,
    100.0 * abs(raw.total_revenue_raw - orders_agg.total_revenue ) / orders_agg.total_revenue as raznost
FROM orders_agg 
INNER JOIN (
    SELECT
        user_id,
        SUM(total_amount) AS total_revenue_raw
    FROM orders_raw
    GROUP BY user_id
) AS raw
ON raw.user_id = orders_agg.user_id
WHERE 100.0 * abs(raw.total_revenue_raw - orders_agg.total_revenue ) / orders_agg.total_revenue > 5;

```

2) Также мы можем учитывать размер таблиц и использовать наш GROUP BY внутри подзапроса. Например, когда таблица orders_raw имеет намного больше строк чем таблица orders_agg.
```
SELECT
    raw.user_id,
    100.0 * abs(raw.total_revenue_raw - orders_agg.total_revenue ) / orders_agg.total_revenue as raznost
FROM orders_agg
INNER JOIN (
    SELECT
        user_id,
        SUM(total_amount) AS total_revenue_raw
    FROM orders_raw
    GROUP BY user_id      <------------------------------------использование большей таблицы(HashAggregate или GroupAggregate)
) AS raw
ON raw.user_id = orders_agg.user_id
WHERE 100.0 * abs(raw.total_revenue_raw - orders_agg.total_revenue ) / orders_agg.total_revenue > 5;

``` 


3) Ранее созданный индекс внутри таблицы будет использоваться для оптимизации запросов по столбцу user_id. Однако стоит учитывать, что для небольших данных будет предпочтительнее SeqScan.
```
postgres=# \d orders_agg
                    Table "public.orders_agg"
    Column     |      Type      | Collation | Nullable | Default 
---------------+----------------+-----------+----------+---------
 user_id       | integer        |           |          | 
 total_orders  | integer        |           |          | 
 total_revenue | numeric(18,10) |           |          | 
Indexes:
    "user_id_idx" btree (user_id)

```


