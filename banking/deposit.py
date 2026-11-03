from decimal import Decimal

from mysql.connector import Error

from banking import config, validators
from banking.account import log_audit
from banking.exceptions import (
    AccountLockedException,
    AccountInactiveException,
    AccountNotFoundException,
    DepositLimitException,
)


def deposit(account_no: str, amount) -> dict:
    
    account_no = validators.validate_account_no(account_no)
    amount = validators.validate_amount(amount, "Deposit amount")

    min_dep = Decimal(str(config.MIN_DEPOSIT))
    max_dep = Decimal(str(config.MAX_DEPOSIT))
    if amount < min_dep or amount > max_dep:
        raise DepositLimitException(
            f"Deposit amount must be between {config.CURRENCY_SYMBOL}{min_dep:.2f} "
            f"and {config.CURRENCY_SYMBOL}{max_dep:.2f}."
        )

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
            raise AccountLockedException("This account is LOCKED. Deposit not allowed.")

        if account["status"] == "INACTIVE":
            conn.rollback()
            raise AccountInactiveException("This account is INACTIVE. Deposit not allowed.")

        new_balance = Decimal(str(account["balance"])) + amount

        cursor.execute(
            "UPDATE accounts SET balance = %s WHERE account_no = %s",
            (new_balance, account_no),
        )

        cursor.execute(
            """INSERT INTO transactions
            (account_no, txn_type, amount, balance_after, description)
            VALUES (%s, 'DEPOSIT', %s, %s, %s)""",
            (account_no, amount, new_balance, "Cash deposit"),
        )
        txn_id = cursor.lastrowid

        log_audit(cursor, account_no, "DEPOSIT",
                f"Deposited {config.CURRENCY_SYMBOL}{amount:.2f}")

        conn.commit()

        cursor.execute("SELECT txn_date FROM transactions WHERE txn_id = %s", (txn_id,))
        txn_row = cursor.fetchone()

        return {
            "account_no": account_no,
            "holder_name": account["holder_name"],
            "amount": amount,
            "balance_after": new_balance,
            "txn_id": txn_id,
            "txn_date": txn_row["txn_date"] if txn_row else None,
        }

    except Error as e:
        if conn:
            conn.rollback()
        raise ConnectionError(f"Database error during deposit: {e}") from e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
