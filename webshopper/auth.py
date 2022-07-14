import functools
from sqlite3 import Connection
import sqlite3

from webshopper.Communicator import Communicator
from webshopper.db import DBInterface

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, jsonify, Response, make_response
)

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=('POST', 'OPTIONS'))
def login():
    """ Sets ktok cookie to reflect validity of the user's tokens.
        Includes tokens and their timestamps in session cookie if at least one is valid
    """
    if request.method == 'OPTIONS':
        # Preflighting
        resp = Response()
        resp.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
        resp.headers['Access-Control-Allow-Credentials'] = 'true'
        resp.headers['Access-Control-Allow-Headers'] = "Content-Type"
        return resp
    # Evaluating input
    credentials: dict = request.json
    username = credentials.get('username', None)
    password = credentials.get('password', None)
    if not username:
        return {'error': 'Missing username'}, 400
    if not password:
        return {'error': 'Missing password'}, 400
    # Evaluating credentials
    ret = DBInterface.get_user(username, password)
    if ret[0] != 0:
        return ret[1], 401
    user: sqlite3.Row = ret[1]['user']
    # Credentials validated
    session.clear()
    session['user_id'] = user['user_id']
    # Determining access token situation
    if user['access_token'] == '':
        ktok = 'MIS'  # Missing
    elif not Communicator.check_rtoken(user['refresh_token_timestamp']):
        ktok = 'EXP'  # Expired
    else:
        ktok = 'GUD'  # Good
    session['access_token'] = user['access_token']
    session['access_token_timestamp'] = user['access_token_timestamp']
    session['refresh_token'] = user['refresh_token']
    session['refresh_token_timestamp'] = user['refresh_token_timestamp']
    session.permanent = True
    # Sending response
    resp = Response()
    resp.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
    resp.headers['Access-Control-Allow-Credentials'] = 'true'
    resp.headers['Access-Control-Allow-Headers'] = "Content-Type"
    resp.set_cookie('username', user['username'])
    resp.set_cookie('ktok', ktok)
    return resp, 200


@bp.route('/register', methods=('POST', 'OPTIONS'))
def register():
    if request.method == 'OPTIONS':
        # Preflighting
        resp = Response()
        resp.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
        resp.headers['Access-Control-Allow-Credentials'] = 'true'
        resp.headers['Access-Control-Allow-Headers'] = "Content-Type"
        return resp
    # Handling credentials
    credentials: dict = request.json
    username = credentials.get('username', None)
    password = credentials.get('password', None)
    if not username:
        print('Missing username')
        return {'error_message': 'Missing username'}, 400
    if not password:
        print('Missing password')
        return {'error_message': 'Missing password'}, 400
    ret = DBInterface.new_user(username, password)
    if ret[0] != 0:
        return {'error': ret[1]}
    # Successfully registered
    # Client should redirect to login page
    resp = jsonify(success=True)
    resp.status_code = 200
    resp.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
    resp.headers['Access-Control-Allow-Credentials'] = 'true'
    resp.headers['Access-Control-Allow-Headers'] = "Content-Type"
    return resp


@bp.route('/authcode_from')
def authcode_from():
    # Redirect destination from kroger bringing auth code
    # Updates ktok cookie and redirects to hardcoded IP
    print('in authcode_from')
    auth_code: str = request.args.get('code')
    ret = Communicator.tokens_from_auth(auth_code)
    if ret[0] != 0:
        return f'error trading auth code for tokens: {ret[1]}'
    token_dict: dict = ret[1]
    ret = DBInterface.deposit_tokens(session['user_id'], token_dict)
    if ret[0] != 0:
        return f'Error writing tokens to db: {ret}'
    session['access_token'] = token_dict['access_token']
    session['access_token_timestamp'] = token_dict['access_token_timestamp']
    session['refresh_token'] = token_dict['refresh_token']
    session['refresh_token_timestamp'] = token_dict['refresh_token_timestamp']
    resp = make_response(redirect('http://35.88.61.178'))
    resp.set_cookie('ktok', 'GUD')
    return resp, 200


@bp.route('/authcode_to', methods=('GET',))
def authcode_to():
    # Constructs URL and redirects client to Kroger's client consent page.
    print('in authcode_to redirect endpoint')
    url: str = Communicator.build_auth_url()
    print(f'redirect url: {url}')
    return redirect(url)


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session['user_id'] is None:
            print('User is not logged in')
            return {'error': 'Must be logged in'}, 401
        print('user is logged in')
        return view(**kwargs)
    return wrapped_view


def valid_tokens(view):
    # Rejects calls if both tokens are expired
    # Called after login_required to ensure
    # session has relevant token entries
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        invalid_tokens = True
        if Communicator.check_ctoken(session['access_token_timestamp']):
            invalid_tokens = False
        elif Communicator.check_rtoken(session['refresh_token_timestamp']):
            invalid_tokens = False
        if invalid_tokens:
            print('tokens invalid')
            resp = jsonify(error='Invalid tokens')
            if session['access_token'] == '0':
                print('tokens missing')
                resp.set_cookie('ktok', 'MIS')
            else:
                print('tokens expired')
                resp.set_cookie('ktok', 'EXP')
            return resp
        else:
            return view(**kwargs)
    return wrapped_view