import os
import sqlite3
import time
import psycopg2
import pytest
from dotenv import load_dotenv

from utils import manage_pg_db


@pytest.fixture
def db_token():
    return [
        manage_pg_db.Tokens(1, 'access_token_1', 'refresh_token_1', int(time.time()) + 100),
        manage_pg_db.Tokens(2, 'access_token_2', 'refresh_token_2', int(time.time()) - 100),
        manage_pg_db.Tokens(3, 'access_token_3', 'refresh_token_3', int(time.time()))
    ]


@pytest.fixture
def db_settings():
    return manage_pg_db.Settings(1, 111, 222, 333, 444, 'en')


@pytest.fixture
def database(db_token, db_settings):
    db = sqlite3.connect(':memory:')
    db.row_factory = sqlite3.Row
    sql_script_path = os.path.dirname(os.path.abspath(__file__)).replace('/tests', '')
    with open(os.path.join(sql_script_path, 'sql_db.sql')) as sql_script:
        db.executescript(sql_script.read())
    cur = db.cursor()
    cur.execute("INSERT INTO subscribers VALUES (?, ?, ?, ?)", db_token[0])
    cur.execute("INSERT INTO subscribers VALUES (?, ?, ?, ?)", db_token[1])
    cur.execute("INSERT INTO settings VALUES (?, ?, ?, ?, ?, ?)", db_settings)
    db.commit()
    return db


@pytest.fixture(scope='session', autouse=True)
def test_dot_env_mock():
    env_path = os.path.join(os.path.dirname(__file__).replace('/tests', ''), '.env')
    load_dotenv(env_path)
