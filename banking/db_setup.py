from mysql.connector import Error
from banking import config


CREATE_DATABASE_SQL = "CREATE DATABASE IF NOT EXISTS banking_db"

CREATE_ACCOUNTS_TABLE = """
CREATE TABLE IF NOT EXISTS accounts (
    account_no      VARCHAR(15) PRIMARY KEY,
    holder_name     VARCHAR(50) NOT NULL,
    pin_hash        VARCHAR(64) NOT NULL,
    balance         DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    account_type    ENUM('SAVINGS','CURRENT') NOT NULL DEFAULT 'SAVINGS',
    status          ENUM('ACTIVE','INACTIVE','LOCKED') NOT NULL DEFAULT 'ACTIVE',
    failed_attempts TINYINT NOT NULL DEFAULT 0,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP
)
"""

CREATE_TRANSACTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS transactions (
    txn_id         INT AUTO_INCREMENT PRIMARY KEY,
    account_no     VARCHAR(15) NOT NULL,
    txn_type       ENUM('DEPOSIT','WITHDRAWAL','BALANCE_CHECK') NOT NULL,
    amount         DECIMAL(15,2) DEFAULT NULL,
    balance_after  DECIMAL(15,2) NOT NULL,
    description    VARCHAR(255) DEFAULT NULL,
    txn_date       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_no) REFERENCES accounts(account_no) ON DELETE CASCADE
)
"""

CREATE_AUDIT_LOG_TABLE = """
CREATE TABLE IF NOT EXISTS audit_log (
    log_id      INT AUTO_INCREMENT PRIMARY KEY,
    account_no  VARCHAR(15) DEFAULT NULL,
    event_type  VARCHAR(50) NOT NULL,
    details     TEXT DEFAULT NULL,
    event_time  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_DAILY_LIMITS_TABLE = """
CREATE TABLE IF NOT EXISTS daily_withdrawal_limits (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    account_no       VARCHAR(15) NOT NULL,
    limit_date       DATE NOT NULL,
    total_withdrawn  DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    UNIQUE KEY uq_account_date (account_no, limit_date),
    FOREIGN KEY (account_no) REFERENCES accounts(account_no) ON DELETE CASCADE
)
"""


def create_database_if_not_exists() -> None:
    
    conn = None
    cursor = None
    try:
        conn = config.get_connection(with_database=False)
        cursor = conn.cursor()
        cursor.execute(CREATE_DATABASE_SQL)
        conn.commit()
    except Error as e:
        raise ConnectionError(f"Could not create database: {e}") from e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def create_tables() -> None:
    
    conn = None
    cursor = None
    try:
        conn = config.get_connection(with_database=True)
        cursor = conn.cursor()
        cursor.execute(CREATE_ACCOUNTS_TABLE)
        cursor.execute(CREATE_TRANSACTIONS_TABLE)
        cursor.execute(CREATE_AUDIT_LOG_TABLE)
        cursor.execute(CREATE_DAILY_LIMITS_TABLE)
        conn.commit()
    except Error as e:
        raise ConnectionError(f"Could not create tables: {e}") from e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def initialize_database() -> None:
    
    create_database_if_not_exists()
    create_tables()
