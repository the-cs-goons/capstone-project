# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.12.4
FROM python:${PYTHON_VERSION}-slim AS base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

WORKDIR /usr/src/app

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/go/dockerfile-user-best-practices/
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# copy init files
COPY --from=vclib-root __init__.py ./vclib/__init__.py
COPY --from=vclib-root common/__init__.py ./vclib/common/__init__.py
COPY __init__.py ./vclib/issuer/__init__.py

# install python dependencies
#COPY --from=root Pipfile.lock ./Pipfile.lock
#RUN pipenv requirements > requirements.txt
COPY --from=root requirements.txt ./requirements.txt

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to requirements.txt to avoid having to copy them into
# into this layer.
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install -r requirements.txt

# Switch to the non-privileged user to run the application.
USER appuser

# Copy the source code into the container.
COPY . .

# Expose the port that the application listens on.
EXPOSE ${CS3900_ISSUER_AGENT_PORT}

# Run the application.
CMD uvicorn examples.demo_agent:credential_issuer_server --reload \
# CMD uvicorn examples.demo_license:credential_issuer_server --reload \
# CMD uvicorn examples.demo_vaccination:credential_issuer_server --reload \
    --host=0.0.0.0 --port="$CS3900_ISSUER_AGENT_PORT" --log-level "debug" \
    --ssl-certfile=examples/example_ssl_certfile.crt \
    --ssl-keyfile=examples/example_ssl_keyfile.key
