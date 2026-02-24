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



COPY orders_raw
FROM '/data/orders_raw.csv'
DELIMITER ','
CSV HEADER;

COPY orders_agg
FROM '/data/orders_agg.csv'
DELIMITER ','
CSV HEADER;





