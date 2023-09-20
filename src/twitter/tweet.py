from dataclasses import dataclass

@dataclass
class Tweet:
    text: str
    pic_url: list
    vid_url: list
    created_at: str
