class TWRequestError(RuntimeError):
    @property
    def msg(self)->str:
        return self.args[0]['message']
    pass

class TwUserError(RuntimeError):
    def __init__(self, user, reason: str) -> None:
        self.user = user
        self.reason = reason
    
    def fmt_msg(self):
        if type(self.user) == str:
            msg = '{}: {}'.format(self.user, self.reason)
        else:
            msg = '{}[{}]: {}'.format(self.user.prefix, self.user.rest_id, self.reason)
        return msg
