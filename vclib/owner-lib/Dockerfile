FROM python:3.12-slim-bookworm

WORKDIR /usr/src

# install python dependencies
COPY requirements.txt .
COPY --from=common requirements.txt ./common.txt
RUN pip install -r requirements.txt
RUN pip install -r common.txt

# remove build dependencies
RUN pip uninstall -y pip

# copy application code over
COPY examples examples

ENTRYPOINT uvicorn examples.default_agent:identity_owner_server --host "0.0.0.0" --port "$CS3900_OWNER_AGENT_PORT" --log-level "debug" --reload
