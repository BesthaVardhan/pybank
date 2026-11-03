import hashlib
import random
import string
from datetime import datetime
from decimal import Decimal

from mysql.connector import Error

from banking import config, validators
from banking.exceptions import (
    AccountLockedException,
    AccountNotFoundException,
    AccountInactiveException,
    InvalidPinException,
    DuplicateAccountException,
)



def hash_pin(pin: str) -> str:
    
    return hashlib.sha256(pin.encode("utf-8")).hexdigest()


def generate_account_number(cursor) -> str:
    
    year = datetime.now().year
    for _ in range(20):  
        suffix = "".join(random.choices(string.digits, k=6))
        candidate = f"ACC{year}{suffix}"
        cursor.execute(
            "SELECT 1 FROM accounts WHERE account_no = %s", (candidate,)
        )
        if cursor.fetchone() is None:
            return candidate
    raise DuplicateAccountException(
        "Could not generate a unique account number. Please try again."
    )


def log_audit(cursor, account_no, event_type: str, details: str = "") -> None:
    
    cursor.execute(
        """INSERT INTO audit_log (account_no, event_type, details)
        VALUES (%s, %s, %s)""",
        (account_no, event_type, details),
    )
# Account Creation
def create_account(holder_name: str, pin: str, account_type: str,
                    opening_deposit) -> dict:
    
    holder_name = validators.validate_name(holder_name)
    pin = validators.validate_pin(pin)
    account_type = validators.validate_account_type(account_type)
    opening_deposit = validators.validate_amount(opening_deposit, "Opening deposit")

    conn = None
    cursor = None
    try:
        conn = config.get_connection()
        cursor = conn.cursor()

        if opening_deposit < Decimal(str(config.MIN_OPENING_DEPOSIT)):
            raise ValueError(
                f"Opening deposit must be at least "
                f"{config.CURRENCY_SYMBOL}{config.MIN_OPENING_DEPOSIT:.2f}."
            )

        account_no = generate_account_number(cursor)
        pin_hash = hash_pin(pin)

        cursor.execute(
            """INSERT INTO accounts
            (account_no, holder_name, pin_hash, balance, account_type, status)
            VALUES (%s, %s, %s, %s, %s, 'ACTIVE')""",
            (account_no, holder_name, pin_hash, opening_deposit, account_type),
        )

        cursor.execute(
            """INSERT INTO transactions
            (account_no, txn_type, amount, balance_after, description)
            VALUES (%s, 'DEPOSIT', %s, %s, %s)""",
            (account_no, opening_deposit, opening_deposit, "Opening deposit"),
        )

        log_audit(cursor, account_no, "ACCOUNT_CREATED",
                f"New {account_type} account opened for {holder_name}")

        conn.commit()

        return {
            "account_no": account_no,
            "holder_name": holder_name,
            "account_type": account_type,
            "balance": opening_deposit,
            "status": "ACTIVE",
        }

    except Error as e:
        if conn:
            conn.rollback()
        raise ConnectionError(f"Database error while creating account: {e}") from e
    except ValueError:
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
# Authentication
def authenticate(account_no: str, pin: str) -> dict:
    
    account_no = validators.validate_account_no(account_no)
    pin = validators.validate_pin(pin)
    pin_hash = hash_pin(pin)

    conn = None
    cursor = None
    try:
        conn = config.get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM accounts WHERE account_no = %s FOR UPDATE",
            (account_no,),
        )
        account = cursor.fetchone()

        if account is None:
            log_audit(cursor, account_no, "LOGIN_FAILED", "Account not found")
            conn.commit()
            raise AccountNotFoundException(
                f"No account found with number {account_no}."
            )

        if account["status"] == "LOCKED":
            log_audit(cursor, account_no, "LOGIN_BLOCKED", "Account is LOCKED")
            conn.commit()
            raise AccountLockedException(
                "This account is LOCKED due to too many failed PIN attempts. "
                "Please contact bank support."
            )

        if account["status"] == "INACTIVE":
            log_audit(cursor, account_no, "LOGIN_BLOCKED", "Account is INACTIVE")
            conn.commit()
            raise AccountInactiveException("This account is INACTIVE.")

        if account["pin_hash"] != pin_hash:
            new_attempts = account["failed_attempts"] + 1
            if new_attempts >= config.MAX_FAILED_ATTEMPTS:
                cursor.execute(
                    """UPDATE accounts SET failed_attempts = %s, status = 'LOCKED'
                    WHERE account_no = %s""",
                    (new_attempts, account_no),
                )
                log_audit(cursor, account_no, "ACCOUNT_LOCKED",
                        f"Locked after {new_attempts} failed PIN attempts")
                conn.commit()
                raise AccountLockedException(
                    "Incorrect PIN. Maximum attempts reached — account is now LOCKED."
                )
            else:
                cursor.execute(
                    "UPDATE accounts SET failed_attempts = %s WHERE account_no = %s",
                    (new_attempts, account_no),
                )
                log_audit(cursor, account_no, "LOGIN_FAILED",
                        f"Wrong PIN, attempt {new_attempts}/{config.MAX_FAILED_ATTEMPTS}")
                conn.commit()
                remaining = config.MAX_FAILED_ATTEMPTS - new_attempts
                raise InvalidPinException(
                    f"Incorrect PIN. {remaining} attempt(s) remaining before lock."
                )

        # Success: reset failed attempts
        cursor.execute(
            "UPDATE accounts SET failed_attempts = 0 WHERE account_no = %s",
            (account_no,),
        )
        log_audit(cursor, account_no, "LOGIN_SUCCESS", "")
        conn.commit()

        return account

    except Error as e:
        if conn:
            conn.rollback()
        raise ConnectionError(f"Database error during authentication: {e}") from e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_account(account_no: str) -> dict:
    
    account_no = validators.validate_account_no(account_no)
    conn = None
    cursor = None
    try:
        conn = config.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM accounts WHERE account_no = %s", (account_no,))
        account = cursor.fetchone()
        if account is None:
            raise AccountNotFoundException(f"No account found with number {account_no}.")
        return account
    except Error as e:
        raise ConnectionError(f"Database error: {e}") from e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
