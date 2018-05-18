import sqlite3
import click
from flask import current_app, g
from flask.cli import with_appcontext

def get_db():
  if 'db' not in g:
    g.db = sqlite3.connect(
      current_app.config['DATABASE'],
      detect_types=sqlite3.PARSE_DECLTYPES
    )
    g.db.row_factory = sqlite3.Row

  return g.db

def update_db(info, cmd):
  db = get_db()

  if cmd == "insert":
    db.execute(
      'INSERT INTO post (title, body, author_id, tags)'
      ' VALUES (?, ?, ?, ?)',
      (info['title'],
       info['body'],
       g.user['id'],
       info['tags'],)
    )

  if cmd == "update":
    db.execute(
      'UPDATE post SET title = ?, body = ?, author_id = ?, tags = ? WHERE uuid = ?',
      (info['title'],
       info['body'],
       info['author_id'],
       info['tags'],
       info['uuid'],)
    )

  db.commit()

def close_db(e=None):
  """If this request connected to the database, close the
  connection.
  """
  db = g.pop('db', None)

  if db is not None:
    db.close()


def init_db():
  """Clear existing data and create new tables."""
  db = get_db()

  with current_app.open_resource('schema.sql') as f:
    db.executescript(f.read().decode('utf8'))


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


def init_app(app):
    """Register database functions with the Flask app. This is called by
    the application factory.
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
