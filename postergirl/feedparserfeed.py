import logging
import time
from datetime import datetime, timezone
from typing import Any

import feedparser  # type: ignore

from postergirl.feed import BaseFeed, FeedEntry
from postergirl.models import FeedparserFeedConfig, FeedState


def debug_message(parsed: object) -> str:
    return getattr(parsed, "debug_message", None) or "No debug message"


def parse_etag(parsed: object) -> str | None:
    etag = getattr(parsed, "etag", None)
    if etag is not None:
        etag = str(etag).strip('" ' "'")
        if len(etag) < 1:
            etag = None

    return etag


def parse_entry_date(entry: object) -> datetime | None:
    date_parsed = getattr(
        entry,
        "updated_parsed",
        getattr(entry, "published_parsed", getattr(entry, "created_parsed", None)),
    )

    if date_parsed is None:
        return None

    if not isinstance(date_parsed, tuple):
        logging.warning(
            "Strange date: %s (%s)", date_parsed, date_parsed.__class__.__name__
        )
        return None

    return datetime.fromtimestamp(time.mktime(date_parsed), tz=timezone.utc)  # type: ignore


class FeedparserFeed(BaseFeed[FeedparserFeedConfig]):
    def __init__(self, config: FeedparserFeedConfig, state: FeedState):
        self.config = config
        super().__init__(state)

    def parse_entry(self, entry: Any) -> FeedEntry | None:
        if not getattr(entry, "title", None):
            logging.warning("No title in entry of %s", self.config.url)
            return None

        if not getattr(entry, "link", None):
            logging.warning("No link in entry of %s", self.config.url)
            return None

        return FeedEntry(
            title=entry.title,
            link=entry.link,
            summary=getattr(entry, "summary", getattr(entry, "content", None)),
            date=parse_entry_date(entry),
        )

    def parse(self) -> list[FeedEntry]:
        logging.info("Parsing %s with feedparser", self.config.url)
        entries: list[FeedEntry] = []

        parsed: Any = feedparser.parse(  # type: ignore
            self.config.url,
            etag=self.state.meta.get("etag", None),
            modified=self.state.meta.get("modified", None),
        )

        if not hasattr(parsed, "status"):
            raise Exception(
                f"Failed to fetch {self.config.url}: {debug_message(parsed)}"
            )

        if (parsed.status >= 400) and (parsed.status <= 599):
            raise Exception(
                f"Fetching {self.config.url} failed with status {parsed.status}: {debug_message(parsed)}"
            )

        if parsed.status == 304:
            logging.info("Feed %s hasn't changed since last fetch", self.config.url)
            return []

        self.state.meta["etag"] = parse_etag(parsed)
        self.state.meta["modified"] = getattr(parsed, "modified", None)

        for entry in parsed.entries:
            try:
                entry = self.parse_entry(entry)
                if entry:
                    entries.append(entry)
            except Exception:
                logging.exception(
                    "Exception while parsing entry of %s", self.config.url
                )

        return entries
