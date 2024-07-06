FROM python:3.12-slim-bookworm

WORKDIR /usr/src

# install python dependencies
COPY requirements.txt .
COPY --from=root common/requirements.txt ./common.txt
RUN pip install -r requirements.txt
RUN pip install -r common.txt

# copy init files
COPY __init__.py ./vclib/issuer/__init__.py
COPY --from=root __init__.py ./vclib/__init__.py

# remove build dependencies
RUN pip uninstall -y pip

# copy application code over
COPY examples examples

ENTRYPOINT uvicorn examples.default_agent:credential_issuer_server --host "0.0.0.0" --port "$CS3900_ISSUER_AGENT_PORT" --log-level "debug" --reload
