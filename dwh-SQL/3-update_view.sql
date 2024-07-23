USE DWH;
DELIMITER //
DROP PROCEDURE IF EXISTS updateViews;
CREATE PROCEDURE IF NOT EXISTS updateViews() BEGIN
    CREATE OR REPLACE VIEW vw_clients_info AS
    SELECT 
        c.client_id,
        c.first_name,
        c.last_name,
        cp.phone_number,
        ce.email
    FROM CLIENTS c
    LEFT JOIN CLIENT_PHONES cp ON c.client_id = cp.person_id
    LEFT JOIN CLIENT_EMAILS ce ON c.client_id = ce.person_id;
    CREATE OR REPLACE VIEW vw_current_product_prices AS
    SELECT 
        product_id,
        product_name,
        product_line,
        product_description,
        price,
        date_from
    FROM PRODUCTS 
    WHERE is_current = TRUE;
    CREATE OR REPLACE VIEW vw_orders_details AS
    SELECT DISTINCT
        ORDERS_FACT.invoice_id,
        CONCAT(CLIENTS.first_name, ' ', CLIENTS.last_name) AS client_name,
        BRANCHES.branch_name,
        BRANCHES.city AS branch_city,
        CONCAT(SALESMEN.first_name, ' ', SALESMEN.last_name) AS salesman_name,
        ORDERS_FACT.order_date,
        ORDERS_FACT.order_time,
        ORDERS_FACT.payment_method,
        PRODUCTS.product_name,
        PRODUCTS.product_line,
        PRODUCTS.product_description,
        PRODUCTS.price,
        SUM(PRODUCT_ORDER.order_amount) AS quantity
    FROM ORDERS_FACT
    LEFT JOIN PRODUCT_ORDER ON ORDERS_FACT.invoice_id = PRODUCT_ORDER.invoice_id
    LEFT JOIN BRANCHES ON BRANCHES.branch_id = ORDERS_FACT.branch_id
    LEFT JOIN SALESMEN ON SALESMEN.salesman_id = ORDERS_FACT.salesman_id
    LEFT JOIN CLIENTS ON CLIENTS.client_id = ORDERS_FACT.client_id
    LEFT JOIN PRODUCTS ON PRODUCT_ORDER.product_id = PRODUCTS.product_id
    GROUP BY
        ORDERS_FACT.invoice_id,
        client_name,
        BRANCHES.branch_name,
        branch_city,
        salesman_name,
        ORDERS_FACT.order_date,
        ORDERS_FACT.order_time,
        ORDERS_FACT.payment_method,
        PRODUCTS.product_name,
        PRODUCTS.product_line,
        PRODUCTS.product_description,
        PRODUCTS.price
    ;
END //
DELIMITER ;