FROM python:3.12-slim-bookworm

WORKDIR /pydentity

COPY pyproject.toml ./

RUN pip install uv
RUN uv sync

COPY app ./app
COPY config.py main.py ./

CMD [ "uv", "run", "main.py" ]