import sys
from getpass import getpass

from banking import db_setup, display
from banking.account import create_account, authenticate
from banking.deposit import deposit
from banking.withdraw import withdraw
from banking.balance import check_balance
from banking.history import get_transaction_history, get_account_summary
from banking.exceptions import BankingException


def pause() -> None:
    input("\nPress Enter to continue...")


def prompt_pin(label: str = "Enter PIN: ") -> str:
    
    try:
        return getpass(label)
    except Exception:
        return input(label)



def open_new_account_flow() -> None:
    display.print_header("Open New Account")
    try:
        holder_name = input("Enter holder name: ")
        account_type = input("Enter account type (SAVINGS/CURRENT): ")
        pin = prompt_pin(f"Set a {4}-digit PIN: ")
        confirm_pin = prompt_pin("Confirm PIN: ")
        if pin != confirm_pin:
            display.print_error("PIN and confirmation PIN do not match.")
            return
        opening_deposit = input("Enter opening deposit amount: ")

        account = create_account(holder_name, pin, account_type, opening_deposit)
        display.print_account_created(account)

    except BankingException as e:
        display.print_error(str(e))
    except (ValueError, ConnectionError) as e:
        display.print_error(str(e))


def account_menu_flow(account: dict) -> None:
    account_no = account["account_no"]
    holder_name = account["holder_name"]

    while True:
        display.print_account_menu(holder_name)
        choice = input("Select an option (1-6): ").strip()

        try:
            if choice == "1":  # Deposit
                amount = input("Enter deposit amount: ")
                receipt = deposit(account_no, amount)
                display.print_receipt("Deposit", receipt)

            elif choice == "2":  # Withdraw
                amount = input("Enter withdrawal amount: ")
                receipt = withdraw(account_no, amount)
                display.print_receipt("Withdrawal", receipt)

            elif choice == "3":  # Check Balance
                info = check_balance(account_no)
                display.print_balance(info)

            elif choice == "4":  # Transaction History
                print("Filter by type? (DEPOSIT/WITHDRAWAL/BALANCE_CHECK or blank for all)")
                txn_type = input("Type: ").strip() or None
                start_date = input("Start date (YYYY-MM-DD, blank to skip): ").strip() or None
                end_date = input("End date (YYYY-MM-DD, blank to skip): ").strip() or None
                page_input = input("Page number (default 1): ").strip()
                page = int(page_input) if page_input.isdigit() else 1

                history = get_transaction_history(
                    account_no, page=page, txn_type=txn_type,
                    start_date=start_date, end_date=end_date,
                )
                display.print_transaction_table(history)

            elif choice == "5":  # Account Summary
                summary = get_account_summary(account_no)
                display.print_account_summary(summary)

            elif choice == "6":  # Logout
                display.print_success(f"Logged out. Goodbye, {holder_name}!")
                break

            else:
                display.print_error("Invalid option. Please choose 1-6.")

        except BankingException as e:
            display.print_error(str(e))
        except (ValueError, ConnectionError) as e:
            display.print_error(str(e))

        pause()


def login_flow() -> None:
    display.print_header("Login to Existing Account")
    try:
        account_no = input("Enter Account Number: ")
        pin = prompt_pin("Enter PIN: ")
        account = authenticate(account_no, pin)
        display.print_success(f"Login successful. Welcome, {account['holder_name']}!")
        account_menu_flow(account)

    except BankingException as e:
        display.print_error(str(e))
    except (ValueError, ConnectionError) as e:
        display.print_error(str(e))


def main() -> None:
    print("Initializing PyBank database...")
    try:
        db_setup.initialize_database()
    except ConnectionError as e:
        print(f"\nFATAL: Could not set up the database.\n{e}\n")
        print("Check banking/config.py DB_CONFIG (host/user/password) and that "
            "your MySQL server is running.")
        sys.exit(1)

    print("Database ready.\n")

    while True:
        display.print_main_menu()
        choice = input("Select an option (1-3): ").strip()

        if choice == "1":
            open_new_account_flow()
            pause()
        elif choice == "2":
            login_flow()
        elif choice == "3":
            print("\nThank you for using PyBank. Visit again!\n")
            break
        else:
            display.print_error("Invalid option. Please choose 1-3.")
            pause()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Exiting PyBank. Goodbye!")
        sys.exit(0)
        
        