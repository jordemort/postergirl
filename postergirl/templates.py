import dataclasses

import mstache

from postergirl.feed import FeedEntry

DEFAULT_TEMPLATE = """
{{title}}
{{link}}

{{#tags}}#{{.}} {{/tags}}
"""

CONTENT_TEMPLATE = """
{{content}}

{{link}}

{{#tags}}#{{.}} {{/tags}}
"""


def render_template(entry: FeedEntry, template: str) -> str:
    return mstache.render(  # type: ignore
        template.strip(), dataclasses.asdict(entry), escape=lambda x: x
    ).strip()


def render_default(entry: FeedEntry) -> str:
    return render_template(entry, DEFAULT_TEMPLATE)


def render_content(entry: FeedEntry) -> str:
    return render_template(entry, CONTENT_TEMPLATE)


Renderers = {"default": render_default, "content": render_content}
