FROM python:3.11

RUN apt-get update && apt-get install -y \
    libpq-dev \
    && pip install --upgrade pip

COPY requirements.txt .
RUN pip install -r requirements.txt