class ApiAnswerError(Exception):
    """Ошибка ответа API."""
    pass


class SendMessageError(Exception):
    """Ошибка отправки сообщения в Телеграм."""
    pass
