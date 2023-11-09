from dataclasses import dataclass
from pathlib import Path
import os

@dataclass
class Project:
    root_dir =  Path(os.getenv('appdata')).joinpath('tmd2')
    logs_dir = root_dir.joinpath('logs')
    usersj_dir = root_dir.joinpath('users.json')
    conf_dir = root_dir.joinpath('config.json')
    cookie_dir = root_dir.joinpath('cookie')
    listj_dir = root_dir.joinpath('list.json')
    


@dataclass
class Config:
    cookies: list[str]
    authorization: str

    store_dir: Path

    @classmethod
    def load(cls, pj: Project):
        import json
        if not pj.root_dir.exists():
            pj.root_dir.mkdir()
        if not pj.logs_dir.exists():
            pj.logs_dir.mkdir()
        if not pj.listj_dir.exists():
            pj.listj_dir.write_text(json.dumps(dict()))
        if not pj.usersj_dir.exists():
            pj.usersj_dir.write_text(json.dumps(dict()))

        while True:
            try:
                _config: dict = json.loads(pj.conf_dir.read_text())
            except FileNotFoundError:
                template = {"authorization": "", "store_dir": ""}
                data = json.dumps(template, indent=4, allow_nan=True, ensure_ascii=False)
                pj.conf_dir.write_text(data)
                print('请填写配置后保存')
                os.system("notepad {}".format(str(pj.conf_dir)))
                pass
            else:
                break
        
        while True:
            try:
                _cookie = pj.cookie_dir.read_text().strip()
                _cookie = [c for c in _cookie.split('\n')]
            except FileNotFoundError:
                pj.cookie_dir.open('w')
                print('请填写 Cookie 后保存（换行分隔）')
                os.system("notepad {}".format(str(pj.cookie_dir)))
            else:
                break
        
        return cls(
            _cookie,
            _config['authorization'],
            Path(_config['store_dir'])
        )


project = Project()
config = Config.load(project)
print('配置已加载')