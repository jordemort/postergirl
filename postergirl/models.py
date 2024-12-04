from typing import Literal, Union

from pydantic import BaseModel


class MastodonConfig(BaseModel):
    instance_url: str
    client_id: str
    client_secret: str
    access_token: str


class BaseFeedConfig(BaseModel):
    url: str
    max_age: str | None = None
    add_tags: list[str] = []
    template: str | None = None


class FeedparserFeedConfig(BaseFeedConfig):
    kind: Literal["feed"]
    passthrough_tags: bool = False


class XPathConfig(BaseModel):
    entry: str
    title: str
    link: str
    summary: str | None = None
    date: str | None = None


class XPathFeedConfig(BaseFeedConfig):
    kind: Literal["xpath"]
    xpath: XPathConfig


FeedConfig = Union[FeedparserFeedConfig, XPathFeedConfig]


class PostergirlConfig(BaseModel):
    mastodon: MastodonConfig
    feeds: list[FeedConfig]
    fetch_interval: str = "10 minutes"
    max_age: str = "1 day"
    add_tags: list[str] = []
    template: str | None = None


class FeedState(BaseModel):
    last_fetch: float | None = None
    num_fetches: int = 0
    seen: dict[str, float] = {}
    meta: dict[str, int | float | str | None] = {}


class PostergirlState(BaseModel):
    feeds: dict[str, FeedState] = {}
