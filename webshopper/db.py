import sqlite3
from sqlite3 import Connection
from typing import Tuple

import click
from flask import current_app, g
from flask.cli import with_appcontext
from werkzeug.security import check_password_hash, generate_password_hash


class DBInterface:
    """ Static class """

    @staticmethod
    def _execute_query(sql_string: str
                       , parameters: tuple = None
                       , selection: bool = False) -> Tuple[int, dict]:
        """ selection: returns cursor after executing query
        """
        db: sqlite3.Connection = DBInterface.get_db()
        cursor: sqlite3.Cursor = db.cursor()
        try:
            if parameters is None:
                cursor.execute(sql_string)
                db.commit()
            else:
                cursor.execute(sql_string, parameters)
                db.commit()
            if selection:
                return 0, {'cursor': cursor}
            else:
                return 0, {}
        except sqlite3.Error as e:
            return -1, {'error': e}

    @staticmethod
    def close_db(e=None):
        """ Runs on teardown """
        db = g.pop('db', None)
        if db is not None:
            db.close()

    @staticmethod
    def get_db() -> sqlite3.Connection:
        """ If multiple db calls are made per request this will
            prevent opening multiple connections to the database

            Helper for all db functions
        """
        if 'db' not in g:
            g.db = sqlite3.connect(
                current_app.config['DATABASE'],
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            g.db.row_factory = sqlite3.Row
        return g.db

    @staticmethod
    def new_user(username: str, password) -> Tuple[int, dict]:
        query = """ INSERT INTO user (username, password_hash)
                    VALUES (?, ?)
                """
        ret = DBInterface._execute_query(query,
                                         (username, generate_password_hash(password)))
        if ret[0] != 0:
            err: sqlite3.Error = ret[1]['error']
            if err is sqlite3.IntegrityError:
                return -1, {'error': 'Username already taken'}
            else:
                return -1, {'error': str(err)}
        return 0, {}

    @staticmethod
    def get_user(username: str, password: str) -> Tuple[int, dict]:
        """ Does credential checking
        """
        query = """ SELECT * 
                    FROM user
                    WHERE username = ?
                """
        ret = DBInterface._execute_query(query, (username,), selection=True)
        if ret[0] != 0:
            return -1, {'error': str(ret[1])}
        user: sqlite3.Row = ret[1]['cursor'].fetchone()
        if user is None:
            return -1, {'error': 'Invalid username or password'}
        elif not check_password_hash(user['password_hash'], password):
            return -1, {'error': 'Invalid username or password'}
        return 0, {'user': user}

    @staticmethod
    def deposit_tokens(user_id: int, token_dict: dict) -> Tuple[int, dict]:
        """ responsible for depositing tokens into db """
        query = """  UPDATE user 
                     SET access_token = ?
                        ,access_token_timestamp = ?
                        ,refresh_token = ?
                        ,refresh_token_timestamp = ? 
                    WHERE user_id = ?
                """
        ret = DBInterface._execute_query(query, (token_dict['access_token']
                                                 , token_dict['access_token_timestamp']
                                                 , token_dict['refresh_token']
                                                 , token_dict['refresh_token_timestamp']
                                                 , user_id))
        if ret[0] != 0:
            return -1, {'error': str(ret[1])}
        return 0, {}


def init_db():
    db = DBInterface.get_db()
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


def init_app(app):
    app.teardown_appcontext(DBInterface.close_db)
    app.cli.add_command(init_db_command)


@click.command('init-db')
@with_appcontext
def init_db_command():
    """ Clear the existing data and create new tables"""
    init_db()
    click.echo('Initialized the database')