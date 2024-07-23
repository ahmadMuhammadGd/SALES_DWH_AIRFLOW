-- DROP SCHEMA IF EXISTS DWH;

CREATE SCHEMA IF NOT EXISTS DWH;

USE DWH;

SET @CURRENT_BATCH_ID = 0;

CREATE TABLE IF NOT EXISTS CLIENTS (
    client_id               INTEGER PRIMARY KEY AUTO_INCREMENT,
    first_name              VARCHAR(20),
    last_name               VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS SALESMEN (
    salesman_id             INTEGER PRIMARY KEY AUTO_INCREMENT,
    first_name              VARCHAR(20),
    last_name               VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS CLIENT_PHONES (
    person_id               INTEGER,
    phone_number            VARCHAR(15),
    FOREIGN KEY (person_id) REFERENCES CLIENTS(client_id)
);

CREATE TABLE IF NOT EXISTS CLIENT_EMAILS (
    person_id               INTEGER,
    email                   VARCHAR(30),
    FOREIGN KEY (person_id) REFERENCES CLIENTS(client_id)
);

CREATE TABLE IF NOT EXISTS PRODUCTS (
    product_id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    product_name            VARCHAR(20),
    product_line            VARCHAR(20),
    product_description     VARCHAR(50),
    price                   FLOAT,
    date_from               DATE,
    date_to                 DATE,
    is_current              BOOLEAN
);


CREATE TABLE IF NOT EXISTS ETL_BATCH (
    batch_id                INTEGER PRIMARY KEY AUTO_INCREMENT,
    source_name             TEXT,
    start_time              DATETIME,
    finish_time             DATETIME
);

CREATE TABLE IF NOT EXISTS BRANCHES (
    branch_id               INTEGER PRIMARY KEY AUTO_INCREMENT,
    branch_name             TEXT,
    city                    TEXT
);

CREATE TABLE IF NOT EXISTS ORDERS_FACT (
    invoice_id              INTEGER,
    client_id               INTEGER,
    batch_id                INTEGER,
    branch_id               INTEGER,
    salesman_id             INTEGER,
    order_date              DATE,
    order_time              TIME,
    payment_method          TEXT,
    PRIMARY KEY (invoice_id, branch_id),
    FOREIGN KEY (client_id) REFERENCES CLIENTS(client_id),
    FOREIGN KEY (salesman_id) REFERENCES SALESMEN(salesman_id),
    FOREIGN KEY (branch_id) REFERENCES BRANCHES(branch_id),
    FOREIGN KEY (batch_id) REFERENCES ETL_BATCH(batch_id)
);

CREATE TABLE IF NOT EXISTS PRODUCT_ORDER (
    invoice_id              INTEGER,
    product_id              INTEGER,
    order_amount            DECIMAL(10, 2),
    FOREIGN KEY (invoice_id) REFERENCES ORDERS_FACT(invoice_id),
    FOREIGN KEY (product_id) REFERENCES PRODUCTS(product_id)
);

CREATE TABLE IF NOT EXISTS CSV_staging(
invoice_id          INTEGER,
branch_name         TEXT,
city                TEXT,
client_fname        TEXT,
client_lname        TEXT,
salesman_fname      TEXT,
salesman_lname      TEXT,
client_email        TEXT,
client_phone        TEXT,
product_name        TEXT,
product_line        TEXT,
product_price       FLOAT,
amount              INTEGER,
order_date          DATE,
order_time          TIME,
payment_method      TEXT
);

CREATE TABLE IF NOT EXISTS Mongo_Staging LIKE CSV_staging;