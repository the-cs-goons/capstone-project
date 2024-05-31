FROM python:3.12-slim-bookworm

ARG CS3900_ENV=development

ENV CS3900_ENV=${CS3900_ENV} \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR="/var/cache/pypoetry" \
    POETRY_HOME="/usr/local" \
    POETRY_VERSION=1.8.2

RUN apt update && apt install -y curl
RUN curl -sSL https://install.python-poetry.org | python -

WORKDIR /usr/src/app

COPY pyproject.toml poetry.lock .
RUN poetry install $(test "$CS3900_ENV" = "production" && echo "--only=main") --no-interaction --no-ansi

COPY src .

EXPOSE 8443
ENTRYPOINT python main.py
