class TWRequestError(RuntimeError):
    @property
    def msg(self, i = 0)->str:
        return self.args[i]['message']
    pass


class TwUserError(RuntimeError):
    def __init__(self, reason, message, **kwds) -> None:
        super().__init__(message)
        self.reason = reason
        self.message = message
        self.user = kwds
    
    @property
    def fmt_msg(self):
        return '{}: {}'.format(self.user, self.message)
