import functools
from sqlite3 import Connection

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify, Response
)

from flask.sessions import SecureCookieSessionInterface


from werkzeug.security import check_password_hash, generate_password_hash

from webshopper.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=('POST', 'OPTIONS'))
def login():

    if request.method == 'OPTIONS':
        resp = Response()
        resp.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
        resp.headers['Access-Control-Allow-Credentials'] = 'true'
        resp.headers['Access-Control-Allow-Headers'] = "Content-Type"

        print('options')
        return resp

    print(request.headers)

    credentials: dict = request.json
    username = credentials.get('username', None)
    password = credentials.get('password', None)
    if not username:
        return {'error_message': 'Missing username'}, 400
    if not password:
        return {'error_message': 'Missing password'}, 400

    db: Connection = get_db()
    user = db.execute(
        """ SELECT *
            FROM user
            WHERE username = ?
        """,
        (username,)
    ).fetchone()
    error = None
    if user is None:
        error = 'Invalid username'
    elif not check_password_hash(user['password_hash'], password):
        error = 'Invalid password'
    else:
        # login successful
        session.clear()
        session.user_id = user['user_id']
        session.permanent = True

    # Sending response
    if error:
        return {'error_message': error}, 401
    else:
        resp = Response()
        resp.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
        resp.headers['Access-Control-Allow-Credentials'] = 'true'
        resp.headers['Access-Control-Allow-Headers'] = "Content-Type"
        resp.set_cookie('username', user['username'])
        return resp, 200

        # This results in a session cookie being there ugghh fuck.
       # return #{'username': user['username']}


@bp.route('/register', methods=('POST', 'OPTIONS'))
def register():

    # if request.method == 'POST':
    #     print("It's a post request")
    #     print(request.json)
    # else:
    #     print('not a post request')
    #
    # if 'visits' in session:
    #     session['visits'] = session.get('visits') + 1
    #     print(session.get('visits'))
    # else:
    #     session['visits'] = 1
    #
    # print('hit registration endpoint')
    # resp = jsonify(example='example_json')
    # resp.set_cookie('username', 'Ryan Meyer')

    if request.method == 'OPTIONS':
        resp = Response()
        resp.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
        resp.headers['Access-Control-Allow-Credentials'] = 'true'
        resp.headers['Access-Control-Allow-Headers'] = "Content-Type"

        print('options')
        return resp



    credentials: dict = request.json
    username = credentials.get('username', None)
    password = credentials.get('password', None)
    if not username:
        print('Missing username')
        return {'error_message': 'Missing username'}, 400
    if not password:
        print('Missing password')
        return {'error_message': 'Missing password'}, 400

    db: Connection = get_db()
    try:
        db.execute(
            """  INSERT INTO user (username, password_hash)
                 VALUES (?, ?)
            """,
            (username, generate_password_hash(password))
        )
        db.commit()
    except db.IntegrityError:
        print('Username already tak,en')
        return {'error_message': 'Username already taken'}, 401

    # Successfully registered
    # Client should redirect to login page
    print('Registration successful')
    resp = jsonify(success=True)
    resp.status_code = 200
    resp.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
    resp.headers['Access-Control-Allow-Credentials'] = 'true'
    resp.headers['Access-Control-Allow-Headers'] = "Content-Type"

    return resp
