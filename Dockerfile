FROM python:3.11-buster
ENV PYTHONUNBUFFERED=1

WORKDIR /src

RUN pip install poetry

COPY pyproject.toml* poetry.lock* ./

RUN poetry config virtualenvs.in-project false
RUN if [ -f pyproject.toml ]; then poetry install --no-root; fi

COPY . .

ENTRYPOINT ["poetry", "run", "uvicorn", "ws.main:app", "--host", "0.0.0.0", "--reload"]