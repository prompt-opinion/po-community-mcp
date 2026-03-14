def create_text_response(text: str, is_error: bool = False) -> str:
    if is_error:
        raise ValueError(text)
    return text
