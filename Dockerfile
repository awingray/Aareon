FROM python:3.9.2
ENV PYTHONUNBUFFERED=1

WORKDIR /code

COPY requirements/. /code/requirements
RUN pip install -r requirements/requirements.txt

COPY . /code/