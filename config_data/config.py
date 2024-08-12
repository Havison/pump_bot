from dataclasses import dataclass
from environs import Env



@dataclass
class ByBit:
    api_key: str         # ключ от bybit
    api_secret: str          # секрет от ключа bybit


@dataclass
class TgBot:
    token: str            # Токен для доступа к телеграм-боту


@dataclass
class Config:
    tg_bot: TgBot
    by_bit: ByBit


def load_config(path: str | None = None) -> Config:

    env: Env = Env()
    env.read_env(path)

    return Config(
        tg_bot=TgBot(
            token=env('BOT_TOKEN'),
        ),
        by_bit=ByBit(
            api_key=env('API_KEY'),
            api_secret=env('API_SECRET'),
        )
    )

