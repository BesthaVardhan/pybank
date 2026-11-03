import os
from banking import config

LINE_WIDTH = 60


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def print_header(title: str) -> None:
    print("=" * LINE_WIDTH)
    print(title.center(LINE_WIDTH))
    print("=" * LINE_WIDTH)


def print_divider() -> None:
    print("-" * LINE_WIDTH)


def print_main_menu() -> None:
    print_header("PyBank - Banking Management System")
    print("1. Open New Account")
    print("2. Login to Existing Account")
    print("3. Exit")
    print_divider()


def print_account_menu(holder_name: str) -> None:
    print_header(f"Welcome, {holder_name}")
    print("1. Deposit")
    print("2. Withdraw")
    print("3. Check Balance")
    print("4. Transaction History")
    print("5. Account Summary")
    print("6. Logout")
    print_divider()


def print_error(message: str) -> None:
    print(f"\n[ERROR] {message}\n")


def print_success(message: str) -> None:
    print(f"\n[OK] {message}\n")


def print_account_created(account: dict) -> None:
    print_divider()
    print("ACCOUNT CREATED SUCCESSFULLY".center(LINE_WIDTH))
    print_divider()
    print(f"Account Number : {account['account_no']}")
    print(f"Holder Name    : {account['holder_name']}")
    print(f"Account Type   : {account['account_type']}")
    print(f"Opening Balance: {config.CURRENCY_SYMBOL}{account['balance']:.2f}")
    print(f"Status         : {account['status']}")
    print_divider()
    print("IMPORTANT: Please remember your account number and PIN.")
    print_divider()


def print_receipt(txn_kind: str, receipt: dict) -> None:
    print_divider()
    print(f"{txn_kind.upper()} RECEIPT".center(LINE_WIDTH))
    print_divider()
    print(f"Account Number : {receipt['account_no']}")
    print(f"Holder Name    : {receipt['holder_name']}")
    print(f"Amount         : {config.CURRENCY_SYMBOL}{receipt['amount']:.2f}")
    print(f"Balance After  : {config.CURRENCY_SYMBOL}{receipt['balance_after']:.2f}")
    print(f"Transaction ID : {receipt['txn_id']}")
    print(f"Date/Time      : {receipt['txn_date']}")
    if "daily_total_after" in receipt:
        print(f"Today's Total Withdrawn: "
            f"{config.CURRENCY_SYMBOL}{receipt['daily_total_after']:.2f} "
            f"/ {config.CURRENCY_SYMBOL}{config.DAILY_WITHDRAWAL_LIMIT:.2f}")
    print_divider()


def print_balance(info: dict) -> None:
    print_divider()
    print("ACCOUNT BALANCE".center(LINE_WIDTH))
    print_divider()
    print(f"Account Number : {info['account_no']}")
    print(f"Holder Name    : {info['holder_name']}")
    print(f"Account Type   : {info['account_type']}")
    print(f"Status         : {info['status']}")
    print(f"Balance        : {config.CURRENCY_SYMBOL}{info['balance']:.2f}")
    print_divider()


def print_transaction_table(history: dict) -> None:
    rows = history["rows"]
    print_divider()
    print(f"TRANSACTION HISTORY  (Page {history['page']} of {history['total_pages']}, "
        f"{history['total_count']} total)".center(LINE_WIDTH))
    print_divider()
    if not rows:
        print("No transactions found for the given filters.")
    else:
        print(f"{'ID':<6}{'Type':<15}{'Amount':<14}{'Balance After':<16}{'Date'}")
        print("-" * LINE_WIDTH)
        for row in rows:
            amount = f"{row['amount']:.2f}" if row["amount"] is not None else "-"
            print(f"{row['txn_id']:<6}{row['txn_type']:<15}{amount:<14}"
                f"{float(row['balance_after']):<16.2f}{row['txn_date']}")
    print_divider()


def print_account_summary(summary: dict) -> None:
    print_divider()
    print("ACCOUNT SUMMARY".center(LINE_WIDTH))
    print_divider()
    print(f"Account Number      : {summary['account_no']}")
    print(f"Holder Name         : {summary['holder_name']}")
    print(f"Account Type        : {summary['account_type']}")
    print(f"Status              : {summary['status']}")
    print(f"Current Balance     : {config.CURRENCY_SYMBOL}{summary['current_balance']:.2f}")
    print(f"Total Deposits      : {config.CURRENCY_SYMBOL}{summary['total_deposits']:.2f} "
        f"({summary['deposit_count']} txns)")
    print(f"Total Withdrawals   : {config.CURRENCY_SYMBOL}{summary['total_withdrawals']:.2f} "
        f"({summary['withdrawal_count']} txns)")
    print(f"Balance Checks      : {summary['balance_check_count']}")
    print_divider()
