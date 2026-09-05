# Undead Mongoose

Django application for the mongoose backend & board interface.

## Prerequisites

- Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and then let uv install the correct python version and the dependencies.

  ```bash
  git clone https://github.com/svsticky/undead-mongoose.git
  cd undead-mongoose
  uv sync
  ```

  While installing packages, you might run into the error that pg_config cannot be found. One way of solving this is installing development libraries for postgres. This differs per operating system, but commands along the following should fix the error:

  ```bash
  sudo apt update && sudo apt install libpq-dev -y # On debian/ubuntu
  brew install postgresql@14 # On macos with homebrew
  ```
- During development you need [docker](https://www.docker.com/) installed to get a postgres database up and runnning.

## Setting up

Copy `sample.env` to `.env` and make sure the database options are correct. By default the credentials are setup to use the docker database. Then run the following commands to setup the database:

```bash
docker compose up -d
uv run --env-file .env manage.py migrate
```

Optionally, you might want to populate the mongoose database with random mock data, run:

```bash
uv run --env-file .env manage.py seed
```
Then you need to set up Keycloak: ask a team member for the `mongoose-backend` / `mongoose-frontend` client secrets on the `master` realm at `keycloak.dev.svsticky.nl`, then fill out the `.env` file:

```env
ALLOWED_HOSTS=localhost

KEYCLOAK_URL=https://keycloak.dev.svsticky.nl
KEYCLOAK_REALM=master
KEYCLOAK_CLIENT_ID=mongoose-backend
KEYCLOAK_CLIENT_SECRET=<secret from staging>

OIDC_RP_CLIENT_ID=oauth2_proxy
OIDC_RP_CLIENT_SECRET=<secret from staging>

OIDC_OP_AUTHORIZATION_ENDPOINT=https://keycloak.dev.svsticky.nl/realms/master/protocol/openid-connect/auth
OIDC_OP_TOKEN_ENDPOINT=https://keycloak.dev.svsticky.nl/realms/master/protocol/openid-connect/token
OIDC_OP_USER_ENDPOINT=https://keycloak.dev.svsticky.nl/realms/master/protocol/openid-connect/userinfo
OIDC_OP_JWKS_ENDPOINT=https://keycloak.dev.svsticky.nl/realms/master/protocol/openid-connect/certs
OIDC_OP_LOGOUT_ENDPOINT=https://keycloak.dev.svsticky.nl/realms/master/protocol/openid-connect/logout
```

Make sure `mongoose-frontend`'s redirect URIs in that realm include `http://localhost:8000/oidc/callback/`.

### iDeal payments

If you want to work with the iDeal payment system, make sure you have the mollie api key. If you leave it blank, mongoose will still work, except for submitting the top up form. For development you want to use a test token, which can be found in the IT Crowd bitwarden.

```env
MOLLIE_API_KEY=test_<secret from bitwarden>
```

To do test payments, you need to use [ngrok](https://ngrok.com/) to forward your local mongoose installation to a public domain, so that mollie can send webhook requests to your local installation. If you have mongoose running as usual, then you only need to run the following command in a separate terminal:

```bash
ngrok http http://localhost:8000
```

ngrok will open a tunnel and bind your mongoose to a public url, update the `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` fields to include the url from ngrok. Lastly, add the ngrok url's `/oidc/callback/` as an additional redirect URI on the `mongoose-frontend` client in Keycloak (as explained above).

Visiting the ngrok url should give your mongoose installation, and you can just use that url to continue development.

## Running

``` bash
# Start the database, if it wasn't already running
docker compose up -d

# Server
uv run --env-file .env manage.py runserver
```
