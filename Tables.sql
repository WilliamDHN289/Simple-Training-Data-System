USE CSC3170;


DROP TABLE IF EXISTS training_data_process;
DROP TABLE IF EXISTS seed_data;
DROP TABLE IF EXISTS data_processing_log;
DROP TABLE IF EXISTS data_loader;
DROP TABLE IF EXISTS data_accepter;




-- Table One: Store the current training data
CREATE TABLE training_data_process (
    data_id INT AUTO_INCREMENT PRIMARY KEY,                      -- Data id
    content TEXT NOT NULL,                        -- Data content
    md5_id VARCHAR(32) NOT NULL UNIQUE,           -- MD5 hash of each data (to make sure each data is unique)
    history_flag TINYINT(1),                      -- Category history 0/1
    finance_flag TINYINT(1),                      -- Category finance 0/1
    physics_flag TINYINT(1),                      -- Category physics 0/1
    chemistry_flag TINYINT(1)                     -- Category chemistry 0/1
);

-- Table Two: Store the seed data
CREATE TABLE seed_data (
    data_id INT AUTO_INCREMENT PRIMARY KEY,                      -- Data id
    content TEXT NOT NULL,                        -- Data content
    md5_id VARCHAR(32) NOT NULL UNIQUE,           -- MD5 hash of each data (to make sure each data is unique)
    history_flag TINYINT(1),                      -- Category history 0/1
    finance_flag TINYINT(1),                      -- Category finance 0/1
    physics_flag TINYINT(1),                      -- Category physics 0/1
    chemistry_flag TINYINT(1)                     -- Category chemistry 0/1
);

-- Table Three: Store the input process
CREATE TABLE data_processing_log (
    data_id INT AUTO_INCREMENT PRIMARY KEY,                        -- Data id
    content TEXT NOT NULL,                          -- Data content
    md5_id VARCHAR(32) NOT NULL,                    -- MD5 hash of each data (to make sure each data is unique)
    category ENUM('history', 'finance', 'physics', 'chemistry'),     -- Category 
    filter_method ENUM('keywords', 'seeds'),       -- Classification method
    history_score DECIMAL(3, 2) DEFAULT 0.00,         -- History score (0-1 with two decimal places)
    finance_score DECIMAL(3, 2) DEFAULT 0.00,         -- Finance score (0-1 with two decimal places)
    physics_score DECIMAL(3, 2) DEFAULT 0.00,         -- Physics score (0-1 with two decimal places)
    chemistry_score DECIMAL(3, 2) DEFAULT 0.00        -- Chemistry score (0-1 with two decimal places)
);


-- Table Four: Data Loader Information
CREATE TABLE data_loader (
    id INT AUTO_INCREMENT PRIMARY KEY,          
    username VARCHAR(255) NOT NULL UNIQUE,    
    password_hash VARCHAR(255) NOT NULL         
);


-- Table Five: Data Accepter Information
CREATE TABLE data_accepter (
    id INT AUTO_INCREMENT PRIMARY KEY,          
    username VARCHAR(255) NOT NULL UNIQUE,      
    password_hash VARCHAR(255) NOT NULL        
);

