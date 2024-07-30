class IssuerError(Exception):
    def __init__(self, message: str, details: str | None = None):
        super().__init__()
        self.message = message
        self.details = details
