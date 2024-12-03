from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Generic, TypeVar

from postergirl.models import BaseFeedConfig, FeedState

T = TypeVar("T", bound=BaseFeedConfig)


@dataclass
class FeedEntry:
    title: str
    link: str
    summary: str | None = None
    date: datetime | None = None
    tags: list[str] = field(default_factory=list)


class BaseFeed(ABC, Generic[T]):
    def __init__(self, state: FeedState):
        self.state = state
        self.config: T

    @abstractmethod
    def parse(self) -> list[FeedEntry]:
        raise NotImplementedError()
