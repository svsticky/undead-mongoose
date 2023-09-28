# Undead Mongoose

Django application for the mongoose backend & board interface, build in Django.

## Prerequisites

To run Undead Mongoose, you need:

- docker
- docker-compose
- nix
- Python 3.8

## Setting up
First, run

Copy `sample.env` to `.env` and edit where necessary.

Setup the database with:

``` bash
docker-compose up -d
nix-shell --run "./manage.py migrate"
```

In development, create an admin superuser
``` bash
nix-shell --run "./manage.py createsuperuser"
```

### Setup Koala connection (local)

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

To enable oauth, you should go to koala.rails.local:3000/api/oauth/applications and create a new application with {{ canonical_hostname }}/oidc/callback/ as the callback url.

It's also possible to generate the client through your CLI in the `constipiated-koala` project by running the command below
```bash
bundle exec rake "doorkeeper:create[undead Mongoose, http://localhost:8000/oidc/callback/, openid profile email member-read]"
```

Ensure scopes 'openid member-read email profile' are present. Also ensure to copy the application_id and secret and put them in your `.env` file. 

```ini
API_TOKEN=koala

OIDC_RP_CLIENT_ID=example_id
OIDC_RP_CLIENT_SECRET=example_secret

ALLOWED_HOSTS=localhost
```

Make sure that the `OIDC_OP_*_ENDPOINT` endpoints are correct. The ones in sample.env should suffice.

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
