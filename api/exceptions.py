class ApiError(Exception):
    """
    basic API error

    Args:
        Exception (_type_): status_code and message
    """

    def __init__(self, status_code: int, message: str, *args: object) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(*args)

    def __str__(self) -> str:
        return f"{self.message}. Status Code: {self.status_code}"
