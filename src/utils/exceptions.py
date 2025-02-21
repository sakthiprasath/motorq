

class ApplicationException(Exception):
    """
    Helps identify class of exceptions supported by `siai`

    It is recommended only to use sub classes of ApplicationException
    """
    def __init__(self, message, reason=''):
        self.message = message
        super(ApplicationException, self).__init__(message)
        self.reason = reason


class ValidationException(ApplicationException):
    """
    Indicates a problem with client input

    Equivalent of HTTP client error (4xx)
    """
    def __init__(self, message, reason=''):
        ApplicationException.__init__(self, message)
        self.reason = reason
