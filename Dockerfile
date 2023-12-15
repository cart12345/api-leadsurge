FROM python:3.11-slim-buster

WORKDIR /app
RUN python -m pip install poetry

COPY pyproject.toml poetry.lock ./
RUN poetry env use python3.11
RUN poetry install --no-root --only main

COPY . .

CMD ["poetry", "run", "gunicorn", "-w", "8", "-b", ":8080", "app:app"]