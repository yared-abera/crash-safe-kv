FROM python:3.12.7-slim-bookworm

RUN useradd -m -u 1000 -s /bin/bash agent

WORKDIR /app

COPY workspace/ /app/

RUN chown -R agent:agent /app
