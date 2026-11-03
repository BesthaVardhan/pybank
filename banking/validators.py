from decimal import Decimal, InvalidOperation

from banking import config
from banking.exceptions import (
    InvalidAmountException,
    InvalidInputException,
)


def validate_pin(pin: str) -> str:
    if pin is None:
        raise InvalidInputException("PIN cannot be empty.")
    pin = pin.strip()
    if not pin.isdigit():
        raise InvalidInputException("PIN must contain digits only.")
    if len(pin) != config.PIN_LENGTH:
        raise InvalidInputException(
            f"PIN must be exactly {config.PIN_LENGTH} digits long."
        )
    return pin


def validate_name(name: str) -> str:
    
    if not name or not name.strip():
        raise InvalidInputException("Holder name cannot be empty.")
    name = name.strip()
    if len(name) < 2 or len(name) > 50:
        raise InvalidInputException("Holder name must be 2-50 characters long.")
    if not all(ch.isalpha() or ch in " .'-" for ch in name):
        raise InvalidInputException(
            "Holder name may only contain letters, spaces, apostrophes, "
            "periods and hyphens."
        )
    return name


def validate_account_type(account_type: str) -> str:
    if not account_type:
        raise InvalidInputException("Account type cannot be empty.")
    account_type = account_type.strip().upper()
    if account_type not in config.ACCOUNT_TYPES:
        raise InvalidInputException(
            f"Account type must be one of {config.ACCOUNT_TYPES}."
        )
    return account_type


def validate_amount(amount, field_name: str = "Amount") -> Decimal:
    
    try:
        value = Decimal(str(amount))
    except (InvalidOperation, ValueError, TypeError):
        raise InvalidAmountException(f"{field_name} must be a valid number.")

    if value <= 0:
        raise InvalidAmountException(f"{field_name} must be greater than zero.")

    
    if value.as_tuple().exponent < -2:
        raise InvalidAmountException(
            f"{field_name} cannot have more than 2 decimal places."
        )

    return value


def validate_account_no(account_no: str) -> str:
    if not account_no or not account_no.strip():
        raise InvalidInputException("Account number cannot be empty.")
    return account_no.strip().upper()
