from typing import Union


class User:
    name: str
    id: str
    discriminator: Union[str, int]
    avatar: str
    bot: bool
