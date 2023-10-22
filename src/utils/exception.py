class TWRequestError(RuntimeError):
    @property
    def msg(self)->str:
        return self.args[0]['message']
    pass

class TwUserError(RuntimeError):
    from src.twitter.user import TwitterUser
    def __init__(self, user: TwitterUser | str, reason: str) -> None:
        self.user = user
        self.reason = reason
    
    @property
    def fmt_msg(self):
        if type(self.user) == str:
            msg = '{}: {}'.format(self.user, self.reason)
        else:
            msg = '{} {}: {}'.format(self.user.prefix, self.user.rest_id, self.reason)
        return msg
