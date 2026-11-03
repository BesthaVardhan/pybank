from mysql.connector import Error

from banking import config, validators
from banking.exceptions import AccountNotFoundException


def get_transaction_history(account_no: str, page: int = 1,
                            page_size: int = None, txn_type: str = None,
                            start_date: str = None, end_date: str = None) -> dict:
    
    account_no = validators.validate_account_no(account_no)
    page_size = page_size or config.DEFAULT_HISTORY_PAGE_SIZE
    page = max(1, page)
    offset = (page - 1) * page_size

    filters = ["account_no = %s"]
    params = [account_no]

    if txn_type:
        txn_type = txn_type.strip().upper()
        if txn_type not in config.TXN_TYPES:
            raise ValueError(f"txn_type must be one of {config.TXN_TYPES}.")
        filters.append("txn_type = %s")
        params.append(txn_type)

    if start_date:
        filters.append("DATE(txn_date) >= %s")
        params.append(start_date)

    if end_date:
        filters.append("DATE(txn_date) <= %s")
        params.append(end_date)

    where_clause = " AND ".join(filters)

    conn = None
    cursor = None
    try:
        conn = config.get_connection()
        cursor = conn.cursor(dictionary=True)

        
        cursor.execute("SELECT 1 FROM accounts WHERE account_no = %s", (account_no,))
        if cursor.fetchone() is None:
            raise AccountNotFoundException(f"No account found with number {account_no}.")

        cursor.execute(
            f"SELECT COUNT(*) AS cnt FROM transactions WHERE {where_clause}",
            tuple(params),
        )
        total_count = cursor.fetchone()["cnt"]

        cursor.execute(
            f"""SELECT txn_id, txn_type, amount, balance_after, description, txn_date
                FROM transactions
                WHERE {where_clause}
                ORDER BY txn_date DESC, txn_id DESC
                LIMIT %s OFFSET %s""",
            tuple(params) + (page_size, offset),
        )
        rows = cursor.fetchall()

        total_pages = max(1, (total_count + page_size - 1) // page_size)

        return {
            "rows": rows,
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": total_pages,
        }

    except Error as e:
        raise ConnectionError(f"Database error fetching history: {e}") from e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_account_summary(account_no: str) -> dict:
    
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

        cursor.execute(
            """SELECT
                COALESCE(SUM(CASE WHEN txn_type = 'DEPOSIT' THEN amount ELSE 0 END), 0)
                    AS total_deposits,
                COALESCE(SUM(CASE WHEN txn_type = 'WITHDRAWAL' THEN amount ELSE 0 END), 0)
                    AS total_withdrawals,
                SUM(CASE WHEN txn_type = 'DEPOSIT' THEN 1 ELSE 0 END)
                    AS deposit_count,
                SUM(CASE WHEN txn_type = 'WITHDRAWAL' THEN 1 ELSE 0 END)
                    AS withdrawal_count,
                SUM(CASE WHEN txn_type = 'BALANCE_CHECK' THEN 1 ELSE 0 END)
                    AS balance_check_count
            FROM transactions
            WHERE account_no = %s""",
            (account_no,),
        )
        stats = cursor.fetchone()

        return {
            "account_no": account["account_no"],
            "holder_name": account["holder_name"],
            "account_type": account["account_type"],
            "status": account["status"],
            "current_balance": account["balance"],
            "total_deposits": stats["total_deposits"],
            "total_withdrawals": stats["total_withdrawals"],
            "deposit_count": stats["deposit_count"] or 0,
            "withdrawal_count": stats["withdrawal_count"] or 0,
            "balance_check_count": stats["balance_check_count"] or 0,
        }

    except Error as e:
        raise ConnectionError(f"Database error building account summary: {e}") from e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
