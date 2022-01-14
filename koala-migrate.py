#!/usr/bin/env python
import psycopg2
import os

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

koala = get_koala_connection()
mongoose = get_mongoose_connection()

def migrate_users():
    select_members_with_tegoed = """
        select members.id, members.first_name, members.infix, members.last_name, members.birth_date, checkout_balances.balance
        from public.members
        inner join checkout_balances on members.id = checkout_balances.member_id;
    """

    with koala:
        koala_cursor = koala.cursor()

        koala_cursor.execute(select_members_with_tegoed)
        
        for user in koala_cursor.fetchall():
            id = user[0]
            
            if user[2] == None:
                name = f"{user[1]} {user[3]}"
            else:
                name = f"{user[1]} {user[2]} {user[3]}"

            birthday = user[4]
            balance = user[5]

            create_user_with_tegoed(id, balance, name, birthday)

# TODO: use execute_many to insert a whole batch at once and reuse the connection
# TODO: delete table contents before migration
def create_user_with_tegoed(id, balance, name, birthday):
    query = f"""
        insert into public.mongoose_app_user(user_id, balance, name, birthday)
        values (%s, %s, %s, %s)
    """

    with mongoose:
        mongoose_cursor = mongoose.cursor()

        mongoose_cursor.execute(query, (id, balance, name, birthday))


def migrate_cards():
    query = """
        select uuid, active, member_id
        from public.checkout_cards
    """

    with koala:
        koala_cursor = koala.cursor()

        koala_cursor.execute(query)
        
        for card in koala_cursor.fetchall():
            card_id = card[0]
            active = card[1]
            koala_id = card[2]
            mongoose_id = get_userid_by_koala_id(koala_id)

            create_card(card_id, active, mongoose_id)


def get_userid_by_koala_id(koala_id):
    query = f"""
        select id
        from mongoose_app_user
        where user_id = '{koala_id}'
    """

    with mongoose:
        mongoose_cursor = mongoose.cursor()

        mongoose_cursor.execute(query)

        return mongoose_cursor.fetchone()



def create_card(card_id, active, user_id):
    query = f"""
        insert into public.mongoose_app_card(card_id, active, user_id_id)
        values (%s, %s, %s)
    """

    with mongoose:
        mongoose_cursor = mongoose.cursor()

        mongoose_cursor.execute(query, (card_id, active, user_id))


migrate_users()
migrate_cards()
