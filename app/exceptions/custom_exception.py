class AppException(Exception):

    def __init__(
        self,
        message: str,
        status_code: int = 400
    ):
        self.message = message
        self.status_code = status_code

        super().__init__(message)


# =========================================================
# CUSTOMER NOT FOUND
# =========================================================

class CustomerNotFoundException(AppException):

    def __init__(self, customer_number: str):

        super().__init__(
            message=f"Customer with number {customer_number} not found",
            status_code=404
        )


# =========================================================
# ACCOUNT NOT FOUND
# =========================================================

class AccountNotFoundException(AppException):

    def __init__(self, account_number: str):

        super().__init__(
            message=f"Account with number {account_number} not found",
            status_code=404
        )


# =========================================================
# TRANSACTION NOT FOUND
# =========================================================

class TransactionNotFoundException(AppException):

    def __init__(self, transaction_number: str):

        super().__init__(
            message=f"Transaction with number {transaction_number} not found",
            status_code=404
        )


# =========================================================
# INVALID AMOUNT
# =========================================================

class InvalidAmountException(AppException):

    def __init__(self):

        super().__init__(
            message="Amount must be greater than zero",
            status_code=400
        )


# =========================================================
# INSUFFICIENT BALANCE
# =========================================================

class InsufficientBalanceException(AppException):

    def __init__(self):

        super().__init__(
            message="Insufficient account balance",
            status_code=400
        )