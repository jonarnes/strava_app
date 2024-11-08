import psycopg2
import os
from dotenv import load_dotenv

from collections import namedtuple

import click
from flask import current_app, g
from flask.cli import with_appcontext

Tokens = namedtuple('Tokens', 'id access_token refresh_token expires_at')
Settings = namedtuple('Settings', 'id icon hum wind aqi lan')
DEFAULT_SETTINGS = Settings(0, 0, 1, 1, 1, 'ru')
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))


def get_db():
    conn = psycopg2.connect(database=os.environ.get('DATABASE_NAME'),
                    host=os.environ.get('DATABASE_HOST'),
                    user=os.environ.get('DATABASE_USER'),
                    password=os.environ.get('DATABASE_PASSWORD'))
    return conn


def get_athlete(athlete_id: int):
    db = get_db()
    cur = db.cursor()
    query= 'SELECT * FROM subscribers WHERE id = %s';
    cur.execute(query, (athlete_id,))
    record_db = cur.fetchone()

    if record_db:
        return Tokens(*record_db)


def add_athlete(tokens: Tokens):
    tokens_db = get_athlete(tokens.id)
    db = get_db()
    cur = db.cursor()
    if not tokens_db:
        sql = 'INSERT INTO subscribers VALUES(%s, %s, %s, %s)'
        cur.execute(sql, tokens)
    elif tokens.access_token != tokens_db.access_token:
        sql = f'UPDATE subscribers SET access_token = %s, refresh_token = %s, expires_at = %s WHERE id = {tokens.id};'
        cur.execute(sql, tokens[1:])
    else:
        return
    db.commit()


def add_settings(settings: Settings):
    """Write to database preferable metrics of weather description.

    :param settings: named tuple Settings
    """
    db = get_db()
    cur = db.cursor()
    query = 'SELECT * FROM settings WHERE id = %s;'
    cur.execute(query, (settings.id,))
    settings_db = cur.fetchone()
    if settings_db:
        if settings == Settings(*settings_db):
            return
        sql = f'UPDATE settings SET icon = %s, humidity = %s, wind = %s, aqi = %s, lan = %s WHERE id = {settings.id};'
        cur.execute(sql, settings[1:])
    else:
        if settings[1:] == DEFAULT_SETTINGS[1:]:
            return
        cur.execute('INSERT INTO settings VALUES(%s, %s, %s, %s, %s, %s)', settings)
    db.commit()


def get_settings(athlete_id: int):
    """Read database and return weather description settings. If settings not provided function
    returns default set with all metrics.

    :param athlete_id: integer Strava athlete id
    :return: named tuple Settings
    """
    db = get_db()
    cur = db.cursor()
    query = 'SELECT * FROM settings WHERE id = %s;'
    cur.execute(query, (athlete_id,))
    sel = cur.fetchone()
    if sel:
        return Settings(*sel)
    else:
        return DEFAULT_SETTINGS._replace(id=athlete_id)

def get_subscribers_count():
    """Count total count of application users
    """
    db = get_db()
    cur = db.cursor()
    query = 'SELECT COUNT(*) FROM subscribers;'
    cur.execute(query)
    result = cur.fetchone()
    return result[0]



def delete_athlete(athlete_id: int):
    """Remove athlete's tokens and settings.

    :param athlete_id: Strava athlete id
    """
    db = get_db()
    cur = db.cursor()
    cur.execute('DELETE FROM subscribers WHERE id = %s', (athlete_id,))
    cur.execute('DELETE FROM settings WHERE id = %s', (athlete_id,))
    db.commit()


def init_app(app):
    #app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)


def init_db():
    """Initial function for database creation."""
    db = get_db()
    print(db)


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear existing database and create new table."""
    init_db()
    click.echo('Initialized database.')


if __name__ == '__main__':  # pragma: no cover
    import os
    from dotenv import load_dotenv

    dotenv_path = os.path.join(os.path.dirname(__file__), '../.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
