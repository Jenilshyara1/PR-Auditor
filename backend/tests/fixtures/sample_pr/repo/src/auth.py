API_KEY = "sk-live-hardcoded-12345"


def authenticate(token: str) -> bool:
    return token == API_KEY
