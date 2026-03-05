import json
import os

ENV = os.getenv("APP_ENV", "dev")

CONFIG_DIR = os.path.dirname(__file__)
CONFIG_FILE = os.path.join(CONFIG_DIR, f"config.{ENV}.json")

with open(CONFIG_FILE, encoding="utf-8") as f:
    _data = json.load(f)

# Allow env vars to override any config value
for key in _data:
    env_val = os.getenv(key)
    if env_val is not None:
        _data[key] = env_val


class Config:
    pass


config = Config()
for key, value in _data.items():
    setattr(config, key, value)
