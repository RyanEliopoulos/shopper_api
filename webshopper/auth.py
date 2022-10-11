import functools
import sqlite3
import json

from webshopper.Communicator import Communicator
from webshopper.db import DBInterface

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, jsonify, Response, make_response
)

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=('POST', 'OPTIONS'))
def login():
    """
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
        print('no username')
        return {'error': 'Missing username'}, 400
    if not password:
        print('no password')
        return {'error': 'Missing password'}, 400
    # Evaluating credentials
    ret = DBInterface.get_user(username, password)
    if ret[0] != 0:
        print('incorrect credentials')
        return ret[1], 401
    user: sqlite3.Row = ret[1]['user']
    # Credentials validated
    session.clear()
    session['user_id'] = user['user_id']
    session['access_token'] = user['access_token']
    session['access_token_timestamp'] = user['access_token_timestamp']
    session['refresh_token'] = user['refresh_token']
    session['refresh_token_timestamp'] = user['refresh_token_timestamp']
    session['locationId'] = user['locationId']
    # Pulling user's products
    ret = DBInterface.get_user_prods(user['user_id'])
    if ret[0] != 0:
        print(f'error retrieving products from database: {ret}')
        return {'error': f'error retrieving products from database: {ret}'}, 500
    products: list = ret[1]['products']
    # Pulling user's recipes
    ret = DBInterface.get_user_recipes(user['user_id'])
    if ret[0] != 0:
        return ret[1], 500
    recipes: dict = ret[1]['recipes']
    print(f"Here is the recipe set: {ret[1]['recipes']}")

    session.permanent = True
    # Sending response
    resp = Response(response=json.dumps({'username': user['username'],
                                         'location_chain': user['location_chain'],
                                         'location_address': user['location_address'],
                                         'products': products,
                                         'recipes': recipes}))
    resp.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
    resp.headers['Access-Control-Allow-Credentials'] = 'true'
    resp.headers['Access-Control-Allow-Headers'] = "Content-Type"
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
    return redirect('https://ryanpaulos.dev', code=302)


@bp.route('/authcode_to', methods=('GET',))
def authcode_to():
    # Constructs URL and redirects client to Kroger's client consent page.
    print('in authcode_to redirect endpoint')
    url: str = Communicator.build_auth_url()
    print(f'redirect url: {url}')
    return redirect(url)


"""
    Decorators
"""


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session['user_id'] is None:
            print('User is not logged in')
            return {'error': 'Must be logged in'}, 401
        print('user is logged in')
        return view(**kwargs)
    return wrapped_view


def location_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwarg):
        if session['locationId'] is None:
            print('User does not have location set')
            return {'error': 'Missing location'}, 401
        return view(**kwarg)
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
            resp.status_code = 401
            # if session['access_token'] == '0':
            #     print('tokens missing')
            #     resp.set_cookie('ktok', 'MIS')
            # else:
            #     print('tokens expired')
            #     resp.set_cookie('ktok', 'EXP')
            return resp
        else:
            return view(**kwargs)
    return wrapped_view