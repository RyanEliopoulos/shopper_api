from typing import Tuple
from typing import List
from webshopper.auth import login_required
from webshopper.auth import valid_tokens
from webshopper.Communicator import Communicator
from webshopper.db import DBInterface
import sqlite3

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, jsonify, Response, make_response
)

bp = Blueprint('products', __name__, url_prefix='/products')


@bp.route('/search', methods=('POST',))
@login_required
@valid_tokens
def search_products():
    """
        Expects 'search_term' in the JSON.
        Must be >= 3 characters
    """
    # if request.method == 'OPTIONS':
    #     print('preflight request')
    # else:
    #     print('not preflight')

    json = request.json
    search_term = json.get('search_term', None)
    if search_term is None:
        return {'error': 'Search term missing'}, 400
    if session['locationId'] == '':
        return {'error': 'Must set locationId first'}, 400

    # Calling Kroger
    ret = Communicator.search_product(search_term, session['locationId'])
    if ret[0] != 0:
        print(f' Failure calling search_products: {ret}')
        return ret[1], 400
    # Call to Kroger succeeded
    products: list = ret[1]['results']['data']  # Going to be some sort of JSON
    # Now need to organize the relevant information
    print(products[0])
    ret_list: list = []
    for prod in products:
        tmp_dict = {
            'productId': prod['productId'],
            'upc': prod['upc'],
            'description': prod['description'],
            'image_urls': image_urls(prod['images']),
        }
        ret_list.append(tmp_dict)
    return {'products': ret_list}, 200


@bp.route('/add_product', methods=('POST',))
@login_required
def add_product():
    """
        Remember that all incoming JSON values are strings, even if we don't want them to be
    """
    json = request.json
    new_product: dict = json['new_product']
    ret = validate_new_product(new_product, new_product['includeAlternate'])
    if ret[0] != 0:
        print(f'error validating serving stuff: {ret}')
        return ret[1], 400
    print(new_product)
    # Inserting into database
    ret = DBInterface.add_product(session.get('user_id'), new_product)
    if ret[0] != 0:
        print(f'db error with new product: {ret}')
        return ret[1], 400
    return {}, 200


@bp.route('edit_product', methods=('POST',))
@login_required
def edit_product():
    """

    :return:
    """
    print('here')
    json = request.json
    edited_product = json['edited_product']
    ret = validate_new_product(edited_product, edited_product['includeAlternate'])
    if ret[0] != 0:
        return ret[1], 400
    # Updating product in database
    ret = DBInterface.edit_product(session['user_id'], edited_product)
    if ret[0] != 0:
        return ret[1], 500
    return {}, 200


@bp.route('delete_product', methods=('POST',))
@login_required
def delete_product():
    """ Expects the productId of the target product """
    json = request.json
    deleted_prod_id: str = json['deleted_product_id']
    ret = DBInterface.delete_product(session['user_id'], deleted_prod_id)
    if ret[0] != 0:
        return {'error': ret[1]['error']}, 500
    return {}, 200




""" 
    HELPER FUNCTIONS
"""


def validate_new_product(new_product: dict, optionals=False) -> Tuple[int, dict]:
    """
        Checks that required numeric fields are floats and positive
        :param optionals: Skips testing the alternate serving values
    """
    mandatory = [
        'servingSize',
        'servingsPerContainer',
    ]
    optional = [
        'alternateSS',
        'alternateSPC'
    ]

    if optionals:
        mandatory.extend(optional)

    def validator(key: str) -> Tuple[int, dict]:
        error: str = ''
        ret_val = 0
        try:
            float(new_product[key])
        except ValueError as e:
            error = f'{key} must be a float'
            ret_val = -1
        if float(new_product[key]) <= 0:
            error = f'{key} must be positive'
            ret_val = -1
        return ret_val, {'error': error}

    for item in mandatory:
        ret = validator(item)
        if ret[0] != 0:
            return ret

    return 0, {}


def image_urls(image_list: list) -> List[dict]:
    """  Help function for search_products

        image_list: list of objects keyed on 'perspective'
            {'perspective': 'front',
            'sizes': [{'size': 'large', 'url': 'http...'}, ...]
            }

        Pulls largest image for each perspective
    """
    size_map = {
        'thumbnail': 0,
        'small': 1,
        'medium': 2,
        'large': 3,
        'xlarge': 4
    }
    largest: int = -1
    url_list = []
    for entry in image_list:
        tmp_dict = {
            'perspective': entry['perspective'],
        }
        # Finding largest img for the perspective
        for size_set in entry['sizes']:
            size = size_set['size']
            if size_map[size] > largest:
                largest = size_map[size]
                tmp_dict['url'] = size_set['url']
        url_list.append(tmp_dict)

        largest = -1

    return url_list



