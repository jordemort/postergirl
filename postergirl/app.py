import dataclasses
import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import cast

from mastodon import Mastodon  # type: ignore
from pydantic_yaml import parse_yaml_file_as, to_yaml_file  # type: ignore
from rich.logging import RichHandler
from rich.traceback import install as install_traceback_handler
from tempora import parse_timedelta  # type: ignore

import postergirl.paths as paths
from postergirl.feedparserfeed import FeedparserFeed
from postergirl.models import (
    FeedparserFeedConfig,
    FeedState,
    PostergirlConfig,
    PostergirlState,
    XPathFeedConfig,
)
from postergirl.templates import Renderers, render_template
from postergirl.xpathfeed import XPathFeed


def run_once(
    config_path: Path, state_path: Path, debug_mode: bool = False
) -> timedelta:
    config = parse_yaml_file_as(PostergirlConfig, config_path)
    if debug_mode:
        logging.info("config = %s", config.model_dump_json(indent=2))

    try:
        state = parse_yaml_file_as(PostergirlState, state_path)
    except Exception:
        state = PostergirlState()

    client = Mastodon(
        client_id=config.mastodon.client_id,
        client_secret=config.mastodon.client_secret,
        access_token=config.mastodon.access_token,
        api_base_url=config.mastodon.instance_url,
        version_check_mode="none",
    )

    for feed_config in config.feeds:
        if debug_mode:
            logging.info("feed_config = %s", feed_config.model_dump_json(indent=2))

        feed_state = state.feeds.get(feed_config.url, FeedState())
        if isinstance(feed_config, FeedparserFeedConfig):
            feed = FeedparserFeed(feed_config, feed_state)
        elif isinstance(feed_config, XPathFeedConfig):  # type: ignore
            feed = XPathFeed(feed_config, feed_state)
        else:
            raise Exception(
                f"Unknown feed config type: {feed_config.__class__.__name___}"
            )

        fetch_time = time.time()
        max_age = cast(
            timedelta, parse_timedelta(feed_config.max_age or config.max_age)
        )
        feed_state.last_fetch = fetch_time
        feed_state.num_fetches += 1

        for entry in reversed(feed.parse()):
            if debug_mode:
                logging.info(
                    "entry = %s",
                    json.dumps(
                        dataclasses.asdict(entry), indent=2, sort_keys=True, default=str
                    ),
                )

            if entry.link in feed_state.seen:
                logging.info("Already saw %s", entry.link)
                continue

            if entry.date is not None:
                entry_age = datetime.now(tz=timezone.utc) - entry.date
                if entry_age > max_age:
                    logging.info(
                        "Entry %s too old: %s > %s", entry.link, entry_age, max_age
                    )
                    if not debug_mode:
                        feed_state.seen[entry.link] = fetch_time
                    continue

            try:
                tags = {
                    tag.upper().strip().lstrip("#"): tag.strip().lstrip("#")
                    for tag in feed_config.add_tags + config.add_tags
                }
                for tag in entry.tags:
                    if tag.upper().strip().lstrip("#") not in tags:
                        tags[tag.upper().strip().lstrip("#")] = tag.strip().lstrip("#")

                if debug_mode:
                    logging.info("Final tags: %s", ",".join(sorted(tags.values())))

                entry.tags = sorted(tags.values())

                template = feed_config.template or config.template or "default"
                if template in Renderers:
                    post_text = Renderers[template](entry)
                else:
                    post_text = render_template(entry, template)

                if debug_mode:
                    logging.info("Would post: %s", repr(post_text))
                else:
                    logging.info("Posting %s (%s)", entry.link, entry.title)
                    client.status_post(post_text, visibility="public")  # type: ignore
                    feed_state.seen[entry.link] = fetch_time
            except Exception:
                logging.exception(f"Exception while posting {entry.link}")

        state.feeds[feed_config.url] = feed_state

    if not debug_mode:
        to_yaml_file(state_path, state)

    return cast(timedelta, parse_timedelta(config.fetch_interval))


def run(debug_mode: bool = False):
    install_traceback_handler()

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
    )

    postergirl_path = paths.postergirl_path()
    os.chdir(postergirl_path)

    config_path = paths.config_path()
    state_path = paths.state_path()

    keep_running = True
    while keep_running:
        try:
            delay = run_once(config_path, state_path, debug_mode)
            if debug_mode:
                keep_running = False
            else:
                logging.info("Going to sleep for %s", delay)
                time.sleep(delay.total_seconds())
        except KeyboardInterrupt:
            logging.info("Got interrupt, exiting")
            keep_running = False
        except Exception:
            logging.exception(
                "Exception while processing feed, trying again in a minute"
            )
            time.sleep(60)
