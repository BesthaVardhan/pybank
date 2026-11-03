#all banking exceptions
class BankingException(Exception):
    
    pass

# Account related
#when user enter same account number which is already present in the database
class DuplicateAccountException(BankingException):
    
    pass

#when user enter the wrong account number
class AccountNotFoundException(BankingException):
    
    pass

#when user try to login the account with wrong or incorrect pin
class InvalidPinException(BankingException):
    pass

#user try to access on locked account due to use enter the pin wrong 3times
class AccountLockedException(BankingException):
    
    pass

#when user can try to access the inactive account
class AccountInactiveException(BankingException):
    
    pass


#Validation related  like non-numeric, ammount<=0
class InvalidAmountException(BankingException):
    
    pass

#invalid  details
class InvalidInputException(BankingException):
    
    pass
#Transaction and business-rule related
class InsufficientBalanceException(BankingException):
    """Raised when a withdrawal would breach the minimum balance rule."""
    pass

#withdraw amount more or less based on the range 100-50000
class DailyLimitExceededException(BankingException):
    
    pass

#deposit amount more or less based on the range 500-100000
class DepositLimitException(BankingException):
    
    pass
