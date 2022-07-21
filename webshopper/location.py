from webshopper.auth import login_required
from webshopper.auth import valid_tokens
from webshopper.Communicator import Communicator
from webshopper.db import DBInterface
import sqlite3

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, jsonify, Response, make_response
)

bp = Blueprint('location', __name__, url_prefix='/location')


@bp.route('/search_loc', methods=('POST',))
@login_required
@valid_tokens
def search_loc():
    json = request.json
    print(f'This is the')
    zipcode = json.get('zipcode', None)
    if zipcode is None:
        return {'error': 'Missing zipcode'}, 400
    try:
        int(zipcode)
    except ValueError:
        return {'error': 'Zipcode must be only integers'}
    if len(zipcode) != 5:
        return {'error': 'Zipcode must be 5 digits'}

    ret = Communicator.search_locations(zipcode)
    if ret[0] != 0:
        print(f'error calling search_locations: {ret}')
        return ret[1], 500
    store_list: [dict] = ret[1]['results']['data']
    trimmed_stores = []
    # print(store_list)
    for store in store_list:
        tmp_dict = {
            'locationId': store['locationId'],
            'chain': store['chain'],
            'addressLine1': store['address']['addressLine1']
        }
        trimmed_stores.append(tmp_dict)
    print(trimmed_stores)
    return {'locations': trimmed_stores}, 200


@bp.route('/set_loc', methods=('POST',))
@login_required
@valid_tokens
def set_loc():
    # Validating locationId
    json = request.json
    locationId: str = json.get('locationId')
    if locationId is None:
        return {'error': 'missing locationId'}, 400
    try:
        int(locationId)
    except ValueError:
        return {'error': 'locationId must be integers only'}, 400
    # Depositing into DB
    print(f'Updating location id to: {locationId}')
    ret = DBInterface.update_location(session.get('user_id'), locationId)
    if ret[0] != 0:
        return ret[1], 400
    return {}, 200


