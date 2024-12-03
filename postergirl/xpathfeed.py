import logging
from datetime import datetime

import requests_cache
import tempora  # type: ignore
from lxml import html  # type: ignore

import postergirl.paths as paths
from postergirl.feed import BaseFeed, FeedEntry
from postergirl.models import FeedState, XPathFeedConfig


class XPathFeed(BaseFeed[XPathFeedConfig]):
    def __init__(self, config: XPathFeedConfig, state: FeedState):
        self.config = config
        self.session = requests_cache.CachedSession(
            paths.postergirl_path().joinpath("xpath_requests"), cache_control=True
        )

        super().__init__(state)

    def parse(self) -> list[FeedEntry]:
        logging.info("Parsing %s with xpath", self.config.url)
        response = self.session.get(self.config.url)  # type: ignore

        if not response.ok:
            raise Exception(
                f"Fetching {self.config.url} failed with status {response.status_code}"
            )

        tree = html.fromstring(response.text)  # type: ignore
        entries: list[FeedEntry] = []

        for entry in tree.xpath(self.config.xpath.entry):
            titles = entry.xpath(self.config.xpath.title)
            if not len(titles):
                continue
            title = titles[0].strip()

            links = entry.xpath(self.config.xpath.link)
            if not len(links):
                continue
            link = links[0].strip()

            summary: str | None = None
            if self.config.xpath.summary is not None:
                summaries = entry.xpath(self.config.xpath.summary)
                if len(summaries):
                    summary = summaries[0].strip()

            date: datetime | None = None
            if self.config.xpath.date is not None:
                dates = entry.xpath(self.config.xpath.date)
                if len(dates):
                    try:
                        date = tempora.parse(dates[0].strip())  # type: ignore
                    except Exception:
                        logging.exception(
                            "Couldn't parse date '%s' in %s", dates[0], self.config.url
                        )

            entries.append(
                FeedEntry(title=title, link=link, summary=summary, date=date)
            )
        return entries
