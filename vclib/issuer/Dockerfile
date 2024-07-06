FROM python:3.12-slim-bookworm

WORKDIR /usr/src

# copy init files
COPY --from=root __init__.py ./vclib/__init__.py
COPY --from=root common/__init__.py ./vclib/common/__init__.py
COPY __init__.py ./vclib/issuer/__init__.py

# install python dependencies
COPY requirements.txt .
COPY --from=root common/requirements.txt ./common.txt
RUN pip install -r requirements.txt
RUN pip install -r common.txt

# remove build dependencies
RUN pip uninstall -y pip

# copy application code over
COPY examples examples

ENTRYPOINT uvicorn examples.default_agent:credential_issuer_server --host "0.0.0.0" --port "$CS3900_ISSUER_AGENT_PORT" --log-level "debug" --reload
