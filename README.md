# Undead Mongoose

Django application for the mongoose backend & board interface, build in Django.

## Prerequisites

To run Undead Mongoose, you need:

- docker
- docker-compose
- pipenv
- Python 3.8

## Setting up

Copy `sample.env` to `.env`.
Setup the database with:

``` bash
docker-compose up -d
pipenv run ./manage.py migrate
```

## Running

``` bash
# database
docker-compose up -d
# server
pipenv run ./manage.py runserver
```
