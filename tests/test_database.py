import sqlite3

import pytest
from flask import g

from utils import manage_pg_db
from run import app as site


@pytest.fixture
def app():
    return site


def test_get_athlete(database, db_token, monkeypatch):
    # GIVEN configured database with athlete tokens
    monkeypatch.setattr(manage_pg_db, 'get_db', lambda: database)
    expected_tokens = db_token[0]  # athlete from database
    # WHEN requesting tokens for athlete ID
    actual_tokens = manage_pg_db.get_athlete(expected_tokens.id)
    # THEN check that tokens added to database equals to returned tokens
    assert actual_tokens == expected_tokens


def test_add_athlete_new(database, db_token, monkeypatch):
    # GIVEN configured database
    monkeypatch.setattr(manage_pg_db, 'get_db', lambda: database)
    expected_tokens = db_token[2]  # new athlete
    # WHEN add tokens for new athlete
    manage_pg_db.add_athlete(expected_tokens)
    # THEN check that tokens was added to database
    cur = database.cursor()
    record = cur.execute(f'SELECT * FROM subscribers WHERE id = {expected_tokens.id}')
    actual_tokens = manage_pg_db.Tokens(*record.fetchone())
    assert expected_tokens == actual_tokens


def test_add_athlete_no_changes(database, db_token, monkeypatch):
    # GIVEN configured database
    monkeypatch.setattr(manage_pg_db, 'get_db', lambda: database)
    expected_tokens = db_token[0]  # athlete from database
    # WHEN add tokens for existing athlete
    manage_pg_db.add_athlete(expected_tokens)
    # THEN check that database is not changed
    cur = database.cursor()
    record = cur.execute(f'SELECT * FROM subscribers WHERE id = {expected_tokens.id}')
    actual_tokens = manage_pg_db.Tokens(*record.fetchone())
    assert expected_tokens == actual_tokens


def test_add_athlete_update(database, db_token, monkeypatch):
    # GIVEN configured database
    monkeypatch.setattr(manage_pg_db, 'get_db', lambda: database)
    expected_tokens = db_token[0]  # athlete from database
    updated_tokens = expected_tokens._replace(access_token='updated_at1')
    # WHEN add changed tokens for existing athlete
    manage_pg_db.add_athlete(updated_tokens)
    # THEN check that tokens was updated in database
    cur = database.cursor()
    record = cur.execute(f'SELECT * FROM subscribers WHERE id = {expected_tokens.id}')
    actual_tokens = manage_pg_db.Tokens(*record.fetchone())
    assert updated_tokens == actual_tokens


def test_add_settings_no_changes(database, db_settings, monkeypatch):
    monkeypatch.setattr(manage_pg_db, 'get_db', lambda: database)
    expected_settings = db_settings  # athlete's settings from database
    # 1. Checking that we have the values with settings in database
    cur = database.cursor()
    record = cur.execute(f'SELECT * FROM settings WHERE id = {expected_settings.id}')
    assert expected_settings == manage_pg_db.Settings(*record.fetchone())
    # 2. Making transaction
    manage_pg_db.add_settings(expected_settings)
    # 3. Testing that there is no changes in first settings
    record = cur.execute(f'SELECT * FROM settings WHERE id = {expected_settings.id}')
    actual_settings = manage_pg_db.Settings(*record.fetchone())
    assert actual_settings == expected_settings


def test_add_settings_with_update(database, db_settings, monkeypatch):
    monkeypatch.setattr(manage_pg_db, 'get_db', lambda: database)
    expected_settings = db_settings  # athlete's settings from database
    # 1. Checking that we have the values with id=1 in database
    cur = database.cursor()
    record = cur.execute(f'SELECT * FROM settings WHERE id = {expected_settings.id}')
    assert expected_settings == manage_pg_db.Settings(*record.fetchone())
    # 2. Update values in Settings object
    expected_settings3 = expected_settings._replace(icon=0, hum=0, wind=1, aqi=0, lan='ru')
    manage_pg_db.add_settings(expected_settings3)
    # 3. Testing that changes have been applied
    record = cur.execute(f'SELECT * FROM settings WHERE id = {expected_settings.id}')
    actual_settings3 = manage_pg_db.Settings(*record.fetchone())
    assert actual_settings3 == expected_settings3


def test_add_settings_new(database, monkeypatch):
    monkeypatch.setattr(manage_pg_db, 'get_db', lambda: database)
    # 1. Checking that we have no settings for such athlete_id in database
    expected_settings2 = manage_pg_db.Settings(2, 0, 1, 2, 3, 'ru')
    cur = database.cursor()
    record = cur.execute(f'SELECT * FROM settings WHERE id = {expected_settings2.id}')
    assert record.fetchone() is None
    # 2. Call method to test it
    manage_pg_db.add_settings(expected_settings2)
    # 3. Testing that changes have been appended to database
    record = cur.execute(f'SELECT * FROM settings WHERE id = {expected_settings2.id}')
    actual_settings2 = manage_pg_db.Settings(*record.fetchone())
    assert actual_settings2 == expected_settings2


def test_add_settings_new_default(database, monkeypatch):
    monkeypatch.setattr(manage_pg_db, 'get_db', lambda: database)
    # 1. Checking that we have no settings for such athlete_id in database
    expected_settings2 = manage_pg_db.DEFAULT_SETTINGS._replace(id=2)
    cur = database.cursor()
    record = cur.execute(f'SELECT * FROM settings WHERE id = {expected_settings2.id}')
    assert record.fetchone() is None
    # 2. Call method to test it
    manage_pg_db.add_settings(expected_settings2)
    # 3. Testing that settings with default values will not be appended to database
    record = cur.execute(f'SELECT * FROM settings WHERE id = {expected_settings2.id}')
    assert record.fetchone() is None


def test_get_settings(database, db_settings, monkeypatch):
    monkeypatch.setattr(manage_pg_db, 'get_db', lambda: database)
    expected_settings = db_settings  # athlete's settings from database
    actual_settings = manage_pg_db.get_settings(expected_settings.id)
    assert actual_settings == expected_settings


def test_get_settings_default(database, monkeypatch):
    monkeypatch.setattr(manage_pg_db, 'get_db', lambda: database)
    actual_default_settings = manage_pg_db.get_settings(0)
    assert actual_default_settings == manage_pg_db.DEFAULT_SETTINGS


def test_delete_athlete(database, monkeypatch):
    monkeypatch.setattr(manage_pg_db, 'get_db', lambda: database)
    manage_pg_db.delete_athlete(1)
    cur = database.cursor()
    db_record_subcribers = cur.execute('SELECT * FROM subscribers WHERE id = 1')
    assert db_record_subcribers.fetchone() is None
    db_record_settings = cur.execute('SELECT * FROM settings WHERE id = 1')
    assert db_record_settings.fetchone() is None
