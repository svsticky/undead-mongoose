# Undead Mongoose

Django application for the mongoose backend & board interface, built in Django.

## Prerequisites

To run Undead Mongoose, you need [docker](https://www.docker.com/) and python 3.9. To install python 3.9 on macos and linux, you can use [pyenv](https://github.com/pyenv/pyenv). On windows, you can just execute the installer for python 3.9 from python's [downloads page](https://www.python.org/downloads/windows/).

Then run the following set of commands to set up the development environment:

```bash
# Clone the repository
git clone https://github.com/svsticky/undead-mongoose.git
cd undead-mongoose

# Create virtual environment (platform-specific)
# On linux
pyenv sync # Installs the correct python version, if you haven't done so already
pyenv exec python -m venv .venv
source .venv/bin/activate

# On windows
python3.9 -m venv .venv
.\.venv\bin\Activate.ps1

# Install dependencies (platform-agnostic)
pip install -r requirements.txt
```

## Setting up

Copy `sample.env` to `.env` and make sure the database options are correct. By default the credentials are setup to use the docker database. Then run the following commands to setup the database:
```bash
docker compose up -d
dotenv run ./manage.py migrate
```

In development, create an admin superuser
```bash
dotenv run ./manage.py createsuperuser
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
- *Alternatively, use the staging version of koala:* create an oauth application for your mongoose installation via <https://koala.dev.svsticky.nl/api/oauth/applications>. Make sure you log in with the dev@svsticky.nl account to access the page. Create a new application with the following information:
  - Confidential: `true`
  - Callback url: `http://localhost:8000/oidc/callback/`
  - Scopes: `openid profile email member-read`
  
  Copy the application id and secret into the `.env` file and make sure you update the oauth urls to point to koala.dev.svsticky.nl.

## Running

``` bash
# Database
docker compose up -d

# Server
dotenv run ./manage.py runserver
```
