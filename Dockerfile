FROM python:3.13-bookworm AS builder

RUN pip install poetry==1.8.4

ENV POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN python3 -m venv /app

ENV VIRTUAL_ENV=/app

WORKDIR /app/src

COPY ./ ./

RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install
#RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --without dev--no-root

##########

FROM python:3.13-slim-bookworm AS runtime

ENV VIRTUAL_ENV=/app \
    PATH="/app/bin:$PATH" \
    DEBIAN_FRONTEND=noninteractive \
    PUID=1000 \
    PGID=1000

RUN apt-get update && apt-get upgrade -y && apt-get install -y dumb-init gosu && apt-get clean

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

VOLUME [ "/data" ]
WORKDIR /data

RUN echo '#!/usr/bin/env bash\n\nexec dumb-init gosu "${PUID:-1000}:${PGID:-1000}" "$@"\n' > /usr/local/bin/entrypoint.sh && \
    chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh", "python3", "-m", "postergirl"]
CMD ["run"]
