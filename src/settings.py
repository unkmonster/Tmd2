from dataclasses import dataclass
from pathlib import Path
import sys
from utils.logger import logger
import os

@dataclass
class Project:
    root_dir =  Path(os.getenv('appdata')).joinpath('tmd2')
    
    conf_dir = root_dir.joinpath('config.json')
    cookie_dir = root_dir.joinpath('cookie')
    listj_dir = root_dir.joinpath('list.json')
    list_dir = root_dir.joinpath('lists')


@dataclass
class Config:
    cookie: str
    authorization: str

    store_dir: Path

    @classmethod
    def load(cls, pj: Project):
        import json
        if not pj.root_dir.exists():
            pj.root_dir.mkdir()
        if not pj.list_dir.exists():
            pj.list_dir.mkdir()
        if not pj.listj_dir.exists():
            pj.listj_dir.write_text(json.dumps(dict()))

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
                _cookie = pj.cookie_dir.read_text()
            except FileNotFoundError:
                pj.cookie_dir.open('w')
                print('请填写 Cookie 后保存')
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