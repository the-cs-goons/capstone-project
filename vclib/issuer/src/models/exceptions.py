class IssuerError(Exception):
    def __init__(self, message: str, details: str):
        super().__init__()
        self.message = message
        self.details = details
