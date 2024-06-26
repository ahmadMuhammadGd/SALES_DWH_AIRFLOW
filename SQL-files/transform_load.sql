USE DWH;

-- Set the current batch ID by selecting the maximum existing batch ID from ETL_BATCH and adding 1
SET @CURRENT_BATCH_ID = (
    SELECT
      COALESCE(MAX(batch_id), 0) AS next_id
    FROM
      ETL_BATCH
    WHERE (start_time IS NOT NULL) AND (finish_time IS NOT NULL)
  ) + 1;
  
-- Insert a new record into ETL_BATCH with the current batch ID and the current timestamp as start_time
INSERT INTO ETL_BATCH (batch_id, start_time)
VALUES (@CURRENT_BATCH_ID, NOW()); 


-- Insert distinct branch names and cities from CSV_STAGING into BRANCHES if they do not already exist in BRANCHES
INSERT INTO BRANCHES(branch_name, city)
SELECT DISTINCT branch_name, city
FROM CSV_STAGING
WHERE (branch_name, city) NOT IN (
    SELECT branch_name, city FROM BRANCHES
    );

-- Insert distinct client names from CSV_STAGING into CLIENTS if they do not already exist in CLIENTS and do not have existing phone numbers or emails in CLIENT_PHONES or CLIENT_EMAILS
INSERT INTO CLIENTS (first_name, last_name)
SELECT DISTINCT client_fname, client_lname
FROM CSV_STAGING
WHERE (client_fname, client_lname) NOT IN (
    SELECT first_name, last_name
    FROM CLIENTS
) 
AND client_phone NOT IN (SELECT phone_number FROM CLIENT_PHONES)
AND client_email NOT IN (SELECT email FROM CLIENT_EMAILS);

-- Insert distinct client emails from CSV_STAGING into CLIENT_EMAILS if they do not already exist in CLIENT_EMAILS
INSERT INTO CLIENT_EMAILS (person_id, email)
SELECT DISTINCT CLIENTS.client_id, CSV_STAGING.client_email
FROM CSV_STAGING
LEFT JOIN CLIENTS ON CLIENTS.first_name = CSV_STAGING.client_fname 
AND CLIENTS.last_name = CSV_STAGING.client_lname
WHERE CSV_STAGING.client_email IS NOT NULL
AND CSV_STAGING.client_email NOT IN (
    SELECT email FROM CLIENT_EMAILS
);

-- Insert distinct client phone numbers from CSV_STAGING into CLIENT_PHONES if they do not already exist in CLIENT_PHONES
INSERT INTO CLIENT_PHONES (person_id, phone_number)
SELECT DISTINCT CLIENTS.client_id, CSV_STAGING.client_phone
FROM CSV_STAGING
JOIN CLIENTS ON CLIENTS.first_name = CSV_STAGING.client_fname 
AND CLIENTS.last_name = CSV_STAGING.client_lname
WHERE CSV_STAGING.client_phone IS NOT NULL
AND CSV_STAGING.client_phone NOT IN (
    SELECT phone_number FROM CLIENT_PHONES
);

-- Insert distinct salesman names from CSV_STAGING into SALESMEN if they do not already exist in SALESMEN
INSERT INTO SALESMEN (first_name, last_name)
SELECT DISTINCT salesman_fname, salesman_lname
FROM CSV_STAGING
WHERE (CSV_STAGING.salesman_fname, CSV_STAGING.salesman_lname) NOT IN (SELECT first_name, last_name FROM SALESMEN);

-- SCD2: PRODUCTS
-- Insert new product records from CSV_STAGING into PRODUCTS for SCD2
INSERT INTO `DWH`.`PRODUCTS` (
    product_name,
    product_line,
    price,
    date_from
)
SELECT 
    product_name,
    product_line,
    product_price,
    MIN(order_date)
FROM
    `DWH`.`CSV_STAGING` AS SRC
GROUP BY
    product_name,
    product_line,
    product_price
HAVING (
    product_name,
    product_line,
    product_price
) NOT IN (
    SELECT DISTINCT  
        product_name,
        product_line,
        price 
    FROM `DWH`.`PRODUCTS`
    );

-- Close prices by setting date_to and is_current flags in PRODUCTS
SET @MAXDATE = '9999-12-31';
UPDATE `DWH`.`PRODUCTS` AS P
INNER JOIN (
    SELECT 
        product_id,
        COALESCE(
            LEAD(date_from) OVER (
                PARTITION BY product_name, product_line, product_description
                ORDER BY date_from 
            ),
        @MAXDATE) AS close_date
    FROM `DWH`.`PRODUCTS`
) AS T
On P.product_id = T.product_id
SET P.date_to = close_date,
    P.is_current = CASE 
        WHEN T.close_date = @MAXDATE THEN TRUE
        ELSE FALSE
    END
WHERE TRUE;

-- Insert new records into ORDERS_FACT from CSV_STAGING if they do not already exist, updating existing ones if necessary
INSERT INTO ORDERS_FACT(
    client_id,
    invoice_id,
    batch_id,
    branch_id,
    salesman_id,
    order_date,
    order_time,
    payment_method)
SELECT 
    CLIENT_PHONES.person_id, 
    CSV_STAGING.invoice_id, 
    @CURRENT_BATCH_ID, 
    BRANCHES.branch_id, 
    SALESMEN.salesman_id, 
    CSV_STAGING.order_date, 
    CSV_STAGING.order_time, 
    CSV_STAGING.payment_method
FROM
    CSV_STAGING
LEFT JOIN 
    CLIENT_PHONES ON CSV_STAGING.client_phone = CLIENT_PHONES.phone_number
LEFT JOIN 
    SALESMEN ON (
        CSV_STAGING.salesman_fname = SALESMEN.first_name
        AND CSV_STAGING.salesman_lname = SALESMEN.last_name
    )
LEFT JOIN
    BRANCHES ON BRANCHES.branch_name = CSV_STAGING.branch_name
WHERE (CSV_STAGING.invoice_id, BRANCHES.branch_id) NOT IN (
    SELECT invoice_id, branch_id FROM ORDERS_FACT
)
ON DUPLICATE KEY UPDATE
    client_id = VALUES(client_id),
    batch_id = VALUES(batch_id),
    salesman_id = VALUES(salesman_id),
    order_date = VALUES(order_date),
    order_time = VALUES(order_time),
    payment_method = VALUES(payment_method);



-- Insert new records into PRODUCT_ORDER from CSV_STAGING if they do not already exist
INSERT INTO PRODUCT_ORDER (invoice_id, product_id, order_amount)
SELECT 
    ORDERS_FACT.invoice_id, 
    PRODUCTS.product_id, 
    CSV_STAGING.amount
FROM 
    CSV_STAGING
LEFT JOIN 
    ORDERS_FACT ON ORDERS_FACT.invoice_id = CSV_STAGING.invoice_id
LEFT JOIN 
    PRODUCTS ON PRODUCTS.product_name = CSV_STAGING.product_name
WHERE 
    NOT EXISTS (
        SELECT 1 
        FROM PRODUCT_ORDER
        WHERE PRODUCT_ORDER.invoice_id = ORDERS_FACT.invoice_id
          AND PRODUCT_ORDER.product_id = PRODUCTS.product_id
          AND PRODUCT_ORDER.order_amount = CSV_STAGING.amount
    );


-- Update the finish_time in ETL_BATCH with the current timestamp for the current batch ID
UPDATE ETL_BATCH
SET ETL_BATCH.ETL_errors = %(ETL_errors)s ,
    ETL_BATCH.source_name = %(source_name)s ,
    ETL_BATCH.finish_time = NOW()
WHERE batch_id = @CURRENT_BATCH_ID;
