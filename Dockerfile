FROM python:3.11-slim

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update \
  && apt-get -y install gcc postgresql-client curl \
  && apt-get clean

# Install python dependencies
COPY ./requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Coping source code
COPY . .

# Create the test database initialization script directory
RUN mkdir -p /docker-entrypoint-initdb.d
