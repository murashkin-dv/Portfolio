MESSAGE_MAX_LENGTH = 4096


def message_max_length(text) -> tuple[str, str]:
    """
    Function splits the incoming text/message to the max limit of a
    Telegram's single message - 4096 symbols. The valid part of 4096 symbols
    is extracted from the beginning of the incoming text and stored in
    variable #1. The rest of text is stored in a variable #2.

    :param text: str
    :return: tuple[str_1, str_2] where
                str_1 - valid max length message to publish
                str_2 - the "tail" of the incoming text.
    """
    valid_message = text[:4096]
    tail_message = text[4096:]
    return valid_message, tail_message
