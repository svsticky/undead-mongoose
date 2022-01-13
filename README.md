# Undead Mongoose

Django application for the mongoose backend & board interface, build in Django.

## Prerequisites

To run Undead Mongoose, you need:

- Postgresql
- pipenv
- Python 3.8

## Setting up

Create a database with the name `undead_mongoose`.
Then, copy `sample.env` to `.env` and put in your credentials.
Setup the database with:

``` bash
pipenv run ./manage.py migrate
```

## Running

``` bash
pipenv run ./manage.py runserver
```
