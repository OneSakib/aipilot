FOLLOW_UP_WORDS = 8


def is_follow_up(request: str) -> bool:
    return len(request.split()) <= FOLLOW_UP_WORDS
