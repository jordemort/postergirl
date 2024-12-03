import os
from functools import cache
from pathlib import Path


@cache
def postergirl_path() -> Path:
    return Path(os.getenv("POSTERGIRL_PATH", ".")).resolve()


def _make_path(key: str, default: str):
    path = Path(os.getenv(key, default))
    if not path.is_absolute():
        path = postergirl_path().joinpath(path)
    return path.resolve()


@cache
def config_path() -> Path:
    return _make_path("POSTERGIRL_CONFIG", "./postergirl.yml")


@cache
def state_path() -> Path:
    return _make_path("POSTERGIRL_STATE", "./postergirl.state.yml")


@cache
def app_secret_path() -> Path:
    return _make_path("POSTERGIRL_APP_SECRET", "./app.secret")


@cache
def user_secret_path() -> Path:
    return _make_path("POSTERGIRL_USER_SECRET", "./user.secret")
