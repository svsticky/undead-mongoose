#!/usr/bin/env python
import psycopg2
import os

# TODO wrap database stuff in a try-block and close it in a finally block

def get_koala_connection():
    db_name = os.getenv("KOALA_DB_NAME")
    db_user = os.getenv("KOALA_DB_USER")
    db_password = os.getenv("KOALA_DB_PASSWORD")
    db_host = os.getenv("KOALA_DB_HOST")
    db_port = os.getenv("KOALA_DB_PORT")
    return psycopg2.connect(f"dbname={db_name} user={db_user} password={db_password} host={db_host} port={db_port}")

def get_mongoose_connection():
    # The databasename is hardcoded, this should be changed in the future (TODO)
    db_name = "undead_mongoose"
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    return psycopg2.connect(f"dbname={db_name} user={db_user} password={db_password} host={db_host} port={db_port}")

koala_cursor = get_koala_connection().cursor()
mongoose_cursor = get_mongoose_connection().cursor()

select_members_with_tegoed = "select * from members"

koala_cursor.execute(select_members_with_tegoed)
print(koala_cursor.fetchall())
