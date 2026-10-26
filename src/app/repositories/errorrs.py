class RepositoryError(Exception):
    status_code: int
    detail: str
    error: Exception | None

    def __init__(
        self,
        status_code: int = 500,
        detail: str = "Execute error",
        error: Exception | None = None,
    ) -> None:
        self.status_code = status_code
        self.detail = detail
        if error is not None:
            self.error = error

        super().__init__(detail)
