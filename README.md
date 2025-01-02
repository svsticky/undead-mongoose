# Undead Mongoose

Django application for the mongoose backend & board interface.

## Prerequisites

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and then let uv install the correct python version and the dependencies.

```bash
git clone https://github.com/svsticky/undead-mongoose.git
cd undead-mongoose
uv sync
```

## Setting up

Copy `sample.env` to `.env` and make sure the database options are correct. By default the credentials are setup to use the docker database. Then run the following commands to setup the database:

```bash
docker compose up -d
uv run --env-file .env manage.py migrate
```

Then depending on whether you want to use a local version of koala, you need to do some additional setup:

- *If you have a locally running version of koala*: (In development) Change `KOALA_DB_NAME` to `koala-development`

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

- *Alternatively, use the staging version of koala:* create an oauth application for your mongoose installation via <https://koala.dev.svsticky.nl/api/oauth/applications>. Make sure you log in with the <dev@svsticky.nl> account to access the page. Create a new application with the following information:
  - Confidential: `true`
  - Callback url: `http://localhost:8000/oidc/callback/`
  - Scopes: `openid profile email member-read`
  
  Copy the application id and secret into the `.env` file and make sure you update the oauth urls to point to koala.dev.svsticky.nl.

  Then complete the `.env` file by filling out the following values:

  ```env
  USER_URL=https://koala.dev.svsticky.nl

  ALLOWED_HOSTS=localhost
  OIDC_RP_CLIENT_ID=<secret from koala>
  OIDC_RP_CLIENT_SECRET=<secret from koala>

  OIDC_OP_AUTHORIZATION_ENDPOINT=https://koala.dev.svsticky.nl/api/oauth/authorize
  OIDC_OP_TOKEN_ENDPOINT=https://koala.dev.svsticky.nl/api/oauth/token
  OIDC_OP_USER_ENDPOINT=https://koala.dev.svsticky.nl/oauth/userinfo
  OIDC_OP_JWKS_ENDPOINT=https://koala.dev.svsticky.nl/oauth/discovery/keys
  OIDC_OP_LOGOUT_ENDPOINT=https://koala.dev.svsticky.nl/signout
  ```

### iDeal payments

If you want to work with the iDeal payment system, make sure you have the mollie api key. If you leave it blank, mongoose will still work, except for submitting the top up form. For development you want to use a test token, which can be found in the IT Crowd bitwarden.

```env
MOLLIE_API_KEY=test_<secret from bitwarden>
```

To do test payments, you need to use [ngrok](https://ngrok.com/) to forward your local mongoose installation to a public domain, so that mollie can send webhook requests to your local installation. If you have mongoose running as usual, then you only need to run the following command in a separate terminal:

```bash
ngrok http http://localhost:8000
```

ngrok will open a tunnel and bind your mongoose to a public url, update the `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` fields to include the url from ngrok. Lastly, update the koala oauth application (at `<koala_url>/api/oauth/applications` as explained above) to use the ngrok url as an additional callback uri.

Visiting the ngrok url should give your mongoose installation, and you can just use that url to continue development.

## Running

``` bash
# Start the database, if it wasn't already running
docker compose up -d

# Server
uv run --env-file .env manage.py runserver
```
