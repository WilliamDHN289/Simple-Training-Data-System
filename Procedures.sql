USE CSC3170;

DROP PROCEDURE IF EXISTS get_data_statistics;
DROP PROCEDURE IF EXISTS get_combined_md5_ids;
DROP PROCEDURE IF EXISTS get_history_contents;
DROP PROCEDURE IF EXISTS get_finance_contents;
DROP PROCEDURE IF EXISTS get_physics_contents;
DROP PROCEDURE IF EXISTS get_chemistry_contents;
DROP PROCEDURE IF EXISTS upload_data;
DROP PROCEDURE IF EXISTS get_training_data_by_id;
DROP PROCEDURE IF EXISTS get_data_info;
DROP PROCEDURE IF EXISTS delete_data_by_id;
DROP PROCEDURE IF EXISTS GetHighScoreDataIds;
DROP PROCEDURE IF EXISTS GetLowScoreDataIds;
DROP PROCEDURE IF EXISTS AddSeedData;
DROP PROCEDURE IF EXISTS DeleteSeedData;
DROP PROCEDURE IF EXISTS CheckDataLoader;
DROP PROCEDURE IF EXISTS CheckDataAccepter;


-- Function One: Check the information of current data
DELIMITER //

CREATE PROCEDURE get_data_statistics()
BEGIN
    DECLARE total_data_count INT;               -- Total number of data
    DECLARE history_count INT;                  -- Number of history data
    DECLARE finance_count INT;                  -- Number of finance data
    DECLARE physics_count INT;                  -- Number of physics data
    DECLARE chemistry_count INT;                -- Number of chemistry data

    SELECT COUNT(data_id) INTO total_data_count FROM training_data_process;
    SELECT COUNT(data_id) INTO history_count FROM training_data_process WHERE history_flag = 1;
    SELECT COUNT(data_id) INTO finance_count FROM training_data_process WHERE finance_flag = 1;
    SELECT COUNT(data_id) INTO physics_count FROM training_data_process WHERE physics_flag = 1;
    SELECT COUNT(data_id) INTO chemistry_count FROM training_data_process WHERE chemistry_flag = 1;

    -- Output
    SELECT CONCAT('Total data entries: ', total_data_count) AS 'Total Data Count';
    SELECT CONCAT('History-related entries: ', history_count) AS 'History Count';
    SELECT CONCAT('Finance-related entries: ', finance_count) AS 'Finance Count';
    SELECT CONCAT('Physics-related entries: ', physics_count) AS 'Physics Count';
    SELECT CONCAT('Chemistry-related entries: ', chemistry_count) AS 'Chemistry Count';
END //

DELIMITER ;


-- Function Two: Select md5_id from both tables training_data_process and seed_data
DELIMITER //

CREATE PROCEDURE get_combined_md5_ids()
BEGIN
    SELECT md5_id FROM training_data_process
    UNION
    SELECT md5_id FROM seed_data;
END //

DELIMITER ;


-- Function Three: Select the history content from seed_data 
DELIMITER //

CREATE PROCEDURE get_history_contents()
BEGIN
    SELECT content FROM seed_data
    WHERE history_flag = 1;
END //

DELIMITER ;


-- Function Four: Select the finance content from seed_data 
DELIMITER //

CREATE PROCEDURE get_finance_contents()
BEGIN
    SELECT content FROM seed_data
    WHERE finance_flag = 1;
END //

DELIMITER ;


-- Function Five: Select the physics content from seed_data 
DELIMITER //

CREATE PROCEDURE get_physics_contents()
BEGIN
    SELECT content FROM seed_data
    WHERE physics_flag = 1;
END //

DELIMITER ;


-- Function Six: Select the chemistry content from seed_data 
DELIMITER //

CREATE PROCEDURE get_chemistry_contents()
BEGIN
    SELECT content FROM seed_data
    WHERE chemistry_flag = 1;
END //

DELIMITER ;


-- Function Seven: Upload the data into tables
DELIMITER //

CREATE PROCEDURE upload_data(
    IN input_data_id INT,
    IN input_content TEXT,
    IN input_md5_id VARCHAR(32),
    IN input_history_flag TINYINT,
    IN input_finance_flag TINYINT,
    IN input_physics_flag TINYINT,
    IN input_chemistry_flag TINYINT,
    IN input_category ENUM('history', 'finance', 'physics', 'chemistry'),
    IN input_filter_method ENUM('keywords', 'seeds'),
    IN input_history_score DECIMAL(3, 2),
    IN input_finance_score DECIMAL(3, 2),
    IN input_physics_score DECIMAL(3, 2),
    IN input_chemistry_score DECIMAL(3, 2)
)
BEGIN
    -- Insert data into training_data_process table
    INSERT INTO training_data_process (
        data_id, content, md5_id, history_flag, finance_flag, physics_flag, chemistry_flag
    )
    VALUES (
        input_data_id, input_content, input_md5_id,
        input_history_flag, input_finance_flag, input_physics_flag, input_chemistry_flag
    );

    -- Insert data into data_processing_log table
    INSERT INTO data_processing_log (
        data_id, content, md5_id, category, filter_method,
        history_score, finance_score, physics_score, chemistry_score
    )
    VALUES (
        input_data_id, input_content, input_md5_id, input_category, input_filter_method,
        input_history_score, input_finance_score, input_physics_score, input_chemistry_score
    );
END //

DELIMITER ;


-- Function Eight: Obtain the original data
DELIMITER //

CREATE PROCEDURE get_training_data_by_id(IN input_data_id INT)
BEGIN
    SELECT * FROM training_data_process
    WHERE data_id = input_data_id;
END //

DELIMITER ;

-- Function Nine: Obtain the data information
DELIMITER //

CREATE PROCEDURE get_data_info(IN input_data_id INT)
BEGIN
    SELECT * FROM data_processing_log
    WHERE data_id = input_data_id;
END //

DELIMITER ;


-- Function Ten: Delete the specific data
DELIMITER //

CREATE PROCEDURE delete_data_by_id(IN input_data_id INT)
BEGIN
   
    DELETE FROM training_data_process WHERE data_id = input_data_id;
    DELETE FROM data_processing_log WHERE data_id = input_data_id;
    
    SET @row_number = 0;
    UPDATE training_data_process 
    SET data_id = (@row_number := @row_number + 1)
    ORDER BY data_id;
    
    SET @row_number = 0;
    UPDATE data_processing_log 
    SET data_id = (@row_number := @row_number + 1)
    ORDER BY data_id;
    
END //

DELIMITER ;

DELIMITER ;

-- Function Eleven: Obtain the ids of high-quality data
DELIMITER $$

CREATE PROCEDURE GetHighScoreDataIds(IN threshold DECIMAL(3,2))
BEGIN
    SELECT data_id
    FROM data_processing_log
    WHERE history_score > threshold
       OR finance_score > threshold
       OR physics_score > threshold
       OR chemistry_score > threshold;
END $$

DELIMITER ;


-- Function Twelve: Obtain the ids of low-quality data
DELIMITER $$

CREATE PROCEDURE GetLowScoreDataIds(IN threshold DECIMAL(3,2))
BEGIN
    SELECT data_id
    FROM data_processing_log
    WHERE history_score < threshold
       AND finance_score < threshold
       AND physics_score < threshold
       AND chemistry_score < threshold;
END $$

DELIMITER ;


-- Function Thirteen: Generate New Seed Data
DELIMITER //

CREATE PROCEDURE AddSeedData(IN input_data_id INT)
BEGIN
    DECLARE v_content TEXT;
    DECLARE v_md5_id VARCHAR(32);
    DECLARE v_history_flag TINYINT(1);
    DECLARE v_finance_flag TINYINT(1);
    DECLARE v_physics_flag TINYINT(1);
    DECLARE v_chemistry_flag TINYINT(1);
    
    SELECT content, md5_id, history_flag, finance_flag, physics_flag, chemistry_flag
    INTO v_content, v_md5_id, v_history_flag, v_finance_flag, v_physics_flag, v_chemistry_flag
    FROM training_data_process
    WHERE data_id = input_data_id;

    INSERT INTO seed_data (content, md5_id, history_flag, finance_flag, physics_flag, chemistry_flag)
    VALUES (v_content, v_md5_id, v_history_flag, v_finance_flag, v_physics_flag, v_chemistry_flag);
    
END //

DELIMITER ;



-- Function Fourteen: Delete Seed Data
DELIMITER //

CREATE PROCEDURE DeleteSeedData(IN input_data_id INT)
BEGIN
    DELETE FROM seed_data WHERE data_id = input_data_id;

    SET @row_number = 0;
    UPDATE seed_data 
    SET data_id = (@row_number := @row_number + 1)
    ORDER BY data_id;
    
END //

DELIMITER ;


-- Function Fifteen: Check Data Loader
DELIMITER //

CREATE PROCEDURE CheckDataLoader(IN input_username VARCHAR(255), OUT stored_hash VARCHAR(255))
BEGIN
    SELECT password_hash INTO stored_hash
    FROM data_loader
    WHERE username = input_username;

    IF stored_hash IS NULL THEN
        SET stored_hash = '';  
    END IF;
END //

DELIMITER ;

-- Function Sixteen: Check Data Accepter
DELIMITER //

CREATE PROCEDURE CheckDataAccepter(IN input_username VARCHAR(255), OUT stored_hash VARCHAR(255))
BEGIN
    SELECT password_hash INTO stored_hash
    FROM data_accepter
    WHERE username = input_username;

    IF stored_hash IS NULL THEN
        SET stored_hash = '';  
    END IF;
END //

DELIMITER ;
