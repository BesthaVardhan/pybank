from datetime import date
from decimal import Decimal

from mysql.connector import Error

from banking import config, validators
from banking.account import log_audit
from banking.exceptions import (
    AccountLockedException,
    AccountInactiveException,
    AccountNotFoundException,
    InsufficientBalanceException,
    DailyLimitExceededException,
    InvalidAmountException,
)


def _get_today_withdrawn(cursor, account_no: str, today: date) -> Decimal:
    
    cursor.execute(
        """SELECT total_withdrawn FROM daily_withdrawal_limits
        WHERE account_no = %s AND limit_date = %s FOR UPDATE""",
        (account_no, today),
    )
    row = cursor.fetchone()
    return Decimal(str(row["total_withdrawn"])) if row else Decimal("0.00")


def get_daily_withdrawn(account_no: str) -> Decimal:
    
    account_no = validators.validate_account_no(account_no)
    conn = None
    cursor = None
    try:
        conn = config.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT total_withdrawn FROM daily_withdrawal_limits
            WHERE account_no = %s AND limit_date = %s""",
            (account_no, date.today()),
        )
        row = cursor.fetchone()
        return Decimal(str(row["total_withdrawn"])) if row else Decimal("0.00")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def withdraw(account_no: str, amount) -> dict:
    account_no = validators.validate_account_no(account_no)
    amount = validators.validate_amount(amount, "Withdrawal amount")

    min_wd = Decimal(str(config.MIN_WITHDRAWAL))
    if amount < min_wd:
        raise InvalidAmountException(
            f"Minimum withdrawal amount is {config.CURRENCY_SYMBOL}{min_wd:.2f}."
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
            raise AccountLockedException("This account is LOCKED. Withdrawal not allowed.")

        if account["status"] == "INACTIVE":
            conn.rollback()
            raise AccountInactiveException("This account is INACTIVE. Withdrawal not allowed.")

        current_balance = Decimal(str(account["balance"]))
        min_balance = Decimal(str(config.MIN_BALANCE))
        daily_limit = Decimal(str(config.DAILY_WITHDRAWAL_LIMIT))
        today = date.today()


        if current_balance - amount < min_balance:
            conn.rollback()
            raise InsufficientBalanceException(
                f"Insufficient balance. A minimum balance of "
                f"{config.CURRENCY_SYMBOL}{min_balance:.2f} must remain."
            )

        already_withdrawn = _get_today_withdrawn(cursor, account_no, today)
        if already_withdrawn + amount > daily_limit:
            conn.rollback()
            remaining = daily_limit - already_withdrawn
            remaining = remaining if remaining > 0 else Decimal("0.00")
            raise DailyLimitExceededException(
                f"Daily withdrawal limit of {config.CURRENCY_SYMBOL}{daily_limit:.2f} "
                f"exceeded. You can withdraw up to "
                f"{config.CURRENCY_SYMBOL}{remaining:.2f} more today."
            )

        new_balance = current_balance - amount
        new_daily_total = already_withdrawn + amount

        cursor.execute(
            "UPDATE accounts SET balance = %s WHERE account_no = %s",
            (new_balance, account_no),
        )

        cursor.execute(
            """INSERT INTO daily_withdrawal_limits (account_no, limit_date, total_withdrawn)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE total_withdrawn = %s""",
            (account_no, today, new_daily_total, new_daily_total),
        )

        cursor.execute(
            """INSERT INTO transactions
            (account_no, txn_type, amount, balance_after, description)
            VALUES (%s, 'WITHDRAWAL', %s, %s, %s)""",
            (account_no, amount, new_balance, "Cash withdrawal"),
        )
        txn_id = cursor.lastrowid

        log_audit(cursor, account_no, "WITHDRAWAL",
                f"Withdrew {config.CURRENCY_SYMBOL}{amount:.2f}")

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
            "daily_total_after": new_daily_total,
        }

    except Error as e:
        if conn:
            conn.rollback()
        raise ConnectionError(f"Database error during withdrawal: {e}") from e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
