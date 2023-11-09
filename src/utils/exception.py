class TWRequestError(RuntimeError):
    @property
    def msg(self, i = 0)->str:
        return self.args[i]['message']
    pass


class TwUserError(RuntimeError):
    def __init__(self, user, reason: str) -> None:
        self.reason = reason
        self.user = user
    
    @property
    def fmt_msg(self):
        return '{} {}: {}'.format(self.user.prefix, self.user.rest_id, self.reason)
