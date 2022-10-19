# Undead Mongoose

Django application for the mongoose backend & board interface, build in Django.

## Prerequisites

To run Undead Mongoose, you need:

- docker
- docker-compose
- nix
- Python 3.8
- dotenv (`python3-dotenv-cli` on Ubuntu)

## Setting up
First, run

Copy `sample.env` to `.env` and edit where necessary.

Setup the database with:

``` bash
docker-compose up -d
dotenv nix-shell --run "./manage.py migrate"
```

In development, create an admin superuser
``` bash
dotenv nix-shell --run "./manage.py createsuperuser"
```

## Running

``` bash
# database
docker-compose up -d
# server
nix-shell --run "./manage.py runserver"
```
