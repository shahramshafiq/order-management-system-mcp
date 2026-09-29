_history = []


def get_history() -> list:
    return _history


def remember(messages: list):
    _history.extend(messages)