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
    print(ret)
    return {'ret': 'made call'}