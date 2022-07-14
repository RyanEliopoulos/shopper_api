from webshopper.auth import login_required
from webshopper.auth import valid_tokens
from webshopper.Communicator import Communicator
from webshopper.db import DBInterface

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, jsonify, Response, make_response
)

bp = Blueprint('endpoints', __name__)


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
    for store in store_list:
        tmp_dict = {
            store['location_id'],
            store['location_brand'],
            store['location_address']
        }
        trimmed_stores.append(tmp_dict)
    return {'locations': trimmed_stores}, 200