FROM python:3.12-slim-bookworm

WORKDIR /usr/src

# install python dependencies
COPY requirements.txt .
COPY --from=root common/requirements.txt ./common.txt
RUN pip install -r requirements.txt
RUN pip install -r common.txt

# copy init files
COPY --from=root __init__.py ./vclib/__init__.py
COPY __init__.py ./vclib/owner/__init__.py

# remove build dependencies
RUN pip uninstall -y pip

# copy application code over
COPY examples examples

ENTRYPOINT uvicorn examples.default_agent:identity_owner_server --host "0.0.0.0" --port "$CS3900_OWNER_AGENT_PORT" --log-level "debug" --reload
