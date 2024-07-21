USE DWH;

DROP PROCEDURE IF EXISTS initBatch;
DROP PROCEDURE IF EXISTS populateBranch;
DROP PROCEDURE IF EXISTS populateClientsInfo;
DROP PROCEDURE IF EXISTS populateSalesInfo;
DROP PROCEDURE IF EXISTS priceChangeCapture;
DROP PROCEDURE IF EXISTS populateProductsInfo;
DROP PROCEDURE IF EXISTS populateFact;
DROP PROCEDURE IF EXISTS establishProductOrderManyToMany;
DROP PROCEDURE IF EXISTS loadBatchIdIntoETL_BATCH;
DROP PROCEDURE IF EXISTS closeBatch;
DROP PROCEDURE IF EXISTS transformLoad;
DROP PROCEDURE IF EXISTS CSV_transformLoad;
DROP PROCEDURE IF EXISTS mongoDB_transformLoad;
DROP PROCEDURE IF EXISTS truncateStagingTable;
-- Set the current batch ID by selecting the maximum existing batch ID from ETL_BATCH and adding 1
DELIMITER // 
CREATE PROCEDURE  initBatch() 
BEGIN
    SET
        @CURRENT_BATCH_ID = (
            SELECT
                COALESCE(MAX(batch_id), 0) AS next_id
            FROM
                ETL_BATCH
            WHERE
                (start_time IS NOT NULL)
                AND (finish_time IS NOT NULL)
        ) + 1;
    SET @START_TIME = NOW();
END //


CREATE PROCEDURE  populateBranch(IN Staging_table_name TEXT) 
-- Insert distinct branch names and cities from STAGING_TABLE into BRANCHES if they do not already exist in BRANCHES
BEGIN
    SET @tableName = Staging_table_name;
    SET @sql = CONCAT('INSERT INTO
        BRANCHES(branch_name, city)
    SELECT
        DISTINCT branch_name,
        city
    FROM
        ',@tableName ,' AS Staging_table
    WHERE
        (branch_name, city) NOT IN (
            SELECT
                branch_name,
                city
            FROM
                BRANCHES
        );'
    );
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
END //

CREATE PROCEDURE  populateClientsInfo(IN Staging_table_name TEXT) 
-- Insert distinct client names from STAGING_TABLE into CLIENTS if they do not already exist in CLIENTS and do not have existing phone numbers or emails in CLIENT_PHONES or CLIENT_EMAILS
BEGIN
    SET @tableName = Staging_table_name;
    SET @sql1 = CONCAT('INSERT INTO
        CLIENTS (first_name, last_name)
    SELECT
        DISTINCT client_fname,
        client_lname
    FROM
        ',@tableName, ' AS Staging_table
    WHERE
        (client_fname, client_lname) NOT IN (
            SELECT
                first_name,
                last_name
            FROM
                CLIENTS
        )
        AND client_phone NOT IN (
            SELECT
                phone_number
            FROM
                CLIENT_PHONES
        )
        AND client_email NOT IN (
            SELECT
                email
            FROM
                CLIENT_EMAILS
        );'
    );
    -- Insert distinct client emails from STAGING_TABLE into CLIENT_EMAILS if they do not already exist in CLIENT_EMAILS
    SET @sql2 = CONCAT('INSERT INTO
        CLIENT_EMAILS (person_id, email)
    SELECT
        DISTINCT CLIENTS.client_id,
        Staging_table.client_email
    FROM
        ', @tableName, ' AS Staging_table
        LEFT JOIN CLIENTS ON CLIENTS.first_name = Staging_table.client_fname
        AND CLIENTS.last_name = Staging_table.client_lname
    WHERE
        Staging_table.client_email IS NOT NULL
        AND Staging_table.client_email NOT IN (
            SELECT
                email
            FROM
                CLIENT_EMAILS
        );'
    );

    -- Insert distinct client phone numbers from STAGING_TABLE into CLIENT_PHONES if they do not already exist in CLIENT_PHONES
    SET @sql3 = CONCAT('INSERT INTO
        CLIENT_PHONES (person_id, phone_number)
    SELECT
        DISTINCT CLIENTS.client_id,
        Staging_table.client_phone
    FROM
        ', @tableName ,' AS Staging_table
        JOIN CLIENTS ON CLIENTS.first_name = Staging_table.client_fname
        AND CLIENTS.last_name = Staging_table.client_lname
    WHERE
        Staging_table.client_phone IS NOT NULL
        AND Staging_table.client_phone NOT IN (
            SELECT
                phone_number
            FROM
                CLIENT_PHONES
        );'
    );

    PREPARE stmt1 FROM @sql1;
    EXECUTE stmt1;
    DEALLOCATE PREPARE stmt1;

    PREPARE stmt2 FROM @sql2;
    EXECUTE stmt2;
    DEALLOCATE PREPARE stmt2;

    PREPARE stmt3 FROM @sql3;
    EXECUTE stmt3;
    DEALLOCATE PREPARE stmt3;
END //

CREATE PROCEDURE  populateSalesInfo(IN Staging_table_name TEXT)
BEGIN
-- Insert distinct salesman names from STAGING_TABLE into SALESMEN if they do not already exist in SALESMEN
    SET @tableName = Staging_table_name;
    SET @sql = CONCAT('INSERT INTO
        SALESMEN (first_name, last_name)
    SELECT
        DISTINCT salesman_fname,
        salesman_lname
    FROM
        ',@tableName ,' AS Staging_table
    WHERE
        (
            Staging_table.salesman_fname,
            Staging_table.salesman_lname
        ) NOT IN (
            SELECT
                first_name,
                last_name
            FROM
                SALESMEN
        );');
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
END //
-- SCD2: PRODUCTS

CREATE PROCEDURE priceChangeCapture()
BEGIN
    -- Close prices by setting date_to and is_current flags in PRODUCTS
    SET
        @MAXDATE = '9999-12-31';

    UPDATE
        `DWH`.`PRODUCTS` AS P
        INNER JOIN (
            SELECT
                product_id,
                COALESCE(
                    LEAD(date_from) OVER (
                        PARTITION BY product_name,
                        product_line,
                        product_description
                        ORDER BY
                            date_from
                    ),
                    @MAXDATE
                ) AS close_date
            FROM
                `DWH`.`PRODUCTS`
        ) AS T On P.product_id = T.product_id
    SET
        P.date_to = close_date,
        P.is_current = CASE
            WHEN T.close_date = @MAXDATE THEN TRUE
            ELSE FALSE
        END
    WHERE
        TRUE;
END //

-- Insert new product records from STAGING_TABLE into PRODUCTS for SCD2
CREATE PROCEDURE  populateProductsInfo(IN Staging_table_name TEXT)
BEGIN
    SET @tableName = Staging_table_name;
    SET @sql = CONCAT('
    INSERT INTO
        `DWH`.`PRODUCTS` (
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
        ',@tableName,' AS SRC
    GROUP BY
        product_name,
        product_line,
        product_price
    HAVING
        (
            product_name,
            product_line,
            product_price
        ) NOT IN (
            SELECT
                DISTINCT product_name,
                product_line,
                price
            FROM
                `DWH`.`PRODUCTS`
        );');
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
END //

CREATE PROCEDURE populateFact(IN Staging_table_name TEXT)
BEGIN
    -- Insert new records into ORDERS_FACT from STAGING_TABLE if they do not already exist, updating existing ones if necessary
    SET @tableName = Staging_table_name;
    SET @sql = CONCAT(
    'INSERT INTO
        ORDERS_FACT(
            client_id,
            invoice_id,
            batch_id,
            branch_id,
            salesman_id,
            order_date,
            order_time,
            payment_method
        )
    SELECT
        CLIENT_PHONES.person_id,
        Staging_table.invoice_id,
        @CURRENT_BATCH_ID,
        BRANCHES.branch_id,
        SALESMEN.salesman_id,
        Staging_table.order_date,
        Staging_table.order_time,
        Staging_table.payment_method
    FROM
        ',@tableName,' AS Staging_table
        LEFT JOIN CLIENT_PHONES ON Staging_table.client_phone = CLIENT_PHONES.phone_number
        LEFT JOIN SALESMEN ON (
            Staging_table.salesman_fname = SALESMEN.first_name
            AND Staging_table.salesman_lname = SALESMEN.last_name
        )
        LEFT JOIN BRANCHES ON BRANCHES.branch_name = Staging_table.branch_name
    WHERE
        (Staging_table.invoice_id, BRANCHES.branch_id) NOT IN (
            SELECT
                invoice_id,
                branch_id
            FROM
                ORDERS_FACT
        ) ON DUPLICATE KEY
    UPDATE
        client_id =
    VALUES
    (client_id),
        batch_id =
    VALUES
    (batch_id),
        salesman_id =
    VALUES
    (salesman_id),
        order_date =
    VALUES
    (order_date),
        order_time =
    VALUES  
    (order_time),
        payment_method =
    VALUES
    (payment_method);'
    );

    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
END //

CREATE PROCEDURE  establishProductOrderManyToMany(IN Staging_table_name TEXT)
BEGIN
    SET @tableName = Staging_table_name;
    SET @sql = CONCAT('
    INSERT INTO
        PRODUCT_ORDER (invoice_id, product_id, order_amount)
    SELECT
        ORDERS_FACT.invoice_id,
        PRODUCTS.product_id,
        Staging_table.amount
    FROM
        ',@tableName,' AS Staging_table
        LEFT JOIN ORDERS_FACT ON ORDERS_FACT.invoice_id = Staging_table.invoice_id
        LEFT JOIN PRODUCTS ON PRODUCTS.product_name = Staging_table.product_name
    WHERE
        NOT EXISTS (
            SELECT
                1
            FROM
                PRODUCT_ORDER   
            WHERE
                PRODUCT_ORDER.invoice_id = ORDERS_FACT.invoice_id
                AND PRODUCT_ORDER.product_id = PRODUCTS.product_id
                AND PRODUCT_ORDER.order_amount = Staging_table.amount
        );');
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
END //

CREATE PROCEDURE loadBatchIdIntoETL_BATCH()
BEGIN
INSERT INTO ETL_BATCH (batch_id) VALUE (@CURRENT_BATCH_ID);
END //

CREATE PROCEDURE  closeBatch(IN source_name TEXT)
    -- Update the finish_time in ETL_BATCH with the current timestamp for the current batch ID
BEGIN
    INSERT INTO
        ETL_BATCH (start_time, finish_time, source_name)
        VALUES
        (@START_TIME, NOW(), source_name);
END //


CREATE PROCEDURE truncateStagingTable(IN Staging_table_name TEXT)
BEGIN
    SET @tableName = Staging_table_name;
    SET @sql = CONCAT('TRUNCATE TABLE ', @tableName, ';');
    PREPARE stmt FROM @sql;
    EXECUTE stmt;   
    DEALLOCATE PREPARE stmt;
END //
CREATE PROCEDURE transformLoad(IN Staging_table_name TEXT, IN source_name TEXT)
BEGIN
    SET @tableName = Staging_table_name;
    CALL initBatch();
    CALL populateBranch(@tableName);
    CALL populateClientsInfo(@tableName);
    CALL populateSalesInfo(@tableName);
    CALL populateProductsInfo(@tableName);
    CALL priceChangeCapture();
    CALL loadBatchIdIntoETL_BATCH();
    CALL populateFact(@tableName);
    CALL establishProductOrderManyToMany(@tableName);
    CALL closeBatch(source_name);
    CALL truncateStagingTable(@tableName);
END // 

CREATE PROCEDURE  CSV_transformLoad(IN source_name TEXT)
BEGIN
    CALL transformLoad('CSV_staging', source_name);
END //

CREATE PROCEDURE  mongoDB_transformLoad()
BEGIN
    CALL transformLoad('Mongo_Staging', 'transactions.invoices');
END //

DELIMITER ;