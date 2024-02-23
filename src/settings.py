from dataclasses import dataclass
from pathlib import Path
import os
from rich import console

console = console.Console()

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
    cookie: str
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
                break
            except FileNotFoundError:
                template = {"authorization": "", "store_dir": "", "cookie": ""}
                
                console.print('Authorization: ', end='', style='slate_blue3')
                template['authorization'] = input().strip()
                console.print('Cookie: ', end='', style='slate_blue3')
                template['cookie'] = input().strip()
                console.print('存储目录: ', end='', style='slate_blue3')
                template['store_dir'] = input().strip()
                
                data = json.dumps(template, indent=4, ensure_ascii=False)
                pj.conf_dir.write_text(data)
            except json.decoder.JSONDecodeError as err:
                console.print(err)
                console.print('无法解析配置，请重新填写', style='red')
                pj.conf_dir.unlink()
         
        # while True:
        #     try:
        #         _cookie = pj.cookie_dir.read_text().strip()
        #         break
        #     except FileNotFoundError:
        #         pj.cookie_dir.open('w')
        #         print('填写 Cookie 并保存')
        #         os.system("notepad {}".format(str(pj.cookie_dir)))
        
        store_path = Path(_config['store_dir'])
        if not store_path.exists():
            store_path.mkdir(parents=True)
            
        return cls(
            _config['cookie'],
            _config['authorization'],
            store_path
        )


project = Project()
config = Config.load(project)
console.print('Config has been loaded', style='green')