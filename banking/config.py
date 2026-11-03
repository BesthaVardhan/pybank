import mysql.connector
from mysql.connector import Error
# Database Connection Settings
DB_CONFIG = {
    "host": "localhost",
    "user": "root",           
    "password": "Vardhan888",  
    "database": "banking_db",
}
DB_CONFIG_NO_DATABASE = {
    "host": DB_CONFIG["host"],
    "user": DB_CONFIG["user"],
    "password": DB_CONFIG["password"],
}


def get_connection(with_database: bool = True):
    try:
        cfg = DB_CONFIG if with_database else DB_CONFIG_NO_DATABASE
        conn = mysql.connector.connect(**cfg)
        return conn
    except Error as e:
        raise ConnectionError(f"Failed to connect to MySQL server: {e}") from e



# Banking Rule Constants
MIN_DEPOSIT = 500.00
MAX_DEPOSIT = 100000.00

MIN_WITHDRAWAL = 100.00
MIN_BALANCE = 1000.00
DAILY_WITHDRAWAL_LIMIT = 50000.00

PIN_LENGTH = 4
MAX_FAILED_ATTEMPTS = 3


MIN_OPENING_DEPOSIT = MIN_BALANCE

ACCOUNT_TYPES = ("SAVINGS", "CURRENT")
ACCOUNT_STATUSES = ("ACTIVE", "INACTIVE", "LOCKED")
TXN_TYPES = ("DEPOSIT", "WITHDRAWAL", "BALANCE_CHECK")


DEFAULT_HISTORY_PAGE_SIZE = 10

CURRENCY_SYMBOL = "Rs."
