from mysql.connector import Error

from banking import config, validators
from banking.account import log_audit
from banking.exceptions import (
    AccountLockedException,
    AccountInactiveException,
    AccountNotFoundException,
)


def check_balance(account_no: str) -> dict:
    
    account_no = validators.validate_account_no(account_no)

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
            conn.rollback()
            raise AccountNotFoundException(f"No account found with number {account_no}.")

        if account["status"] == "LOCKED":
            conn.rollback()
            raise AccountLockedException("This account is LOCKED. Balance enquiry denied.")

        if account["status"] == "INACTIVE":
            conn.rollback()
            raise AccountInactiveException("This account is INACTIVE. Balance enquiry denied.")

        cursor.execute(
            """INSERT INTO transactions
            (account_no, txn_type, amount, balance_after, description)
            VALUES (%s, 'BALANCE_CHECK', NULL, %s, %s)""",
            (account_no, account["balance"], "Balance enquiry"),
        )

        log_audit(cursor, account_no, "BALANCE_CHECK", "")
        conn.commit()

        return {
            "account_no": account["account_no"],
            "holder_name": account["holder_name"],
            "account_type": account["account_type"],
            "status": account["status"],
            "balance": account["balance"],
        }

    except Error as e:
        if conn:
            conn.rollback()
        raise ConnectionError(f"Database error during balance check: {e}") from e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
