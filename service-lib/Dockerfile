FROM python:3.12-slim-bookworm

WORKDIR /usr/src

# install python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# remove build dependencies
RUN pip uninstall -y pip

# copy application code over
COPY service service
COPY examples examples

ENTRYPOINT uvicorn examples.default_agent:service_provider_server --host "0.0.0.0" --port "$CS3900_SERVICE_AGENT_PORT" --log-level "debug" --reload
