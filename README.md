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

### Setup Koala connection

(In development) Change `KOALA_DB_NAME` to `koala-development`

Create the `undead_mongoose` user in Koala's database:
```sql
CREATE USER undead_mongoose WITH PASSWORD 'mongoose123';
```

Configure privileges for the `undead_mongoose` user in Koala's database (Replace `koala` with `koala-development` in development):
```sql
\c "koala"
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO undead_mongoose;
```

Setup OAuth2:
In Koala's Database (Replace `koala` with `koala-development` in development):
```sql
\c "koala"
INSERT INTO public.oauth_applications(name, uid, secret, redirect_uri) VALUES ('mongoose', 'example_id', 'example_secret', 'http://localhost:8000/oidc/callback/');
```

Alter Mongoose's `.env` file such that the following keys have the following values:
```ini
API_TOKEN=koala

OIDC_RP_CLIENT_ID=example_id
OIDC_RP_CLIENT_SECRET=example_secret

ALLOWED_HOSTS=localhost
```

Alter Koala's `.env` file such that the following keys have the following values:
```ini
CHECKOUT_TOKEN=koala
```

## Running

``` bash
# database
docker-compose up -d
# server
nix-shell --run "./manage.py runserver"
```
