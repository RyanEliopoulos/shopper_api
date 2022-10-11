from typing import Tuple
from typing import List
from webshopper.auth import login_required
from webshopper.auth import valid_tokens
from webshopper.auth import location_required
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
@location_required
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


@bp.route('/product_detail', methods=('POST', 'GET'))
@login_required
@valid_tokens
@location_required
def product_detail():
    """
        Gets details on a specific product, specified by UPC
        Returns 'categories' list, 'soldBy' str, size

    :return:
    """
    print('here')
    # json: dict = request.json
    # upc: str = json['upc']
    locationId = session['locationId']
    upc = '0022571700000'
    ret = Communicator.product_details(upc, locationId)
    if ret[0] != 0:
        print('bad request to Kroger')
        return ret[1], 500
    print(ret)
    print(ret[1]['response']['data']['items'])
    return {'details': ret[1]['response']['data']['items']}, 200


@bp.route('/add_product', methods=('POST',))
@login_required
def add_product():
    """
        Remember that all incoming JSON values are strings, even if we don't want them to be.

        'total_container_quantity' is calculated for the new product by normalizing weight measures
        to grams and volume measures to ml.

    """
    json = request.json
    new_product: dict = json['new_product']
    ret = validate_new_product(new_product, new_product['includeAlternate'])
    if ret[0] != 0:
        print(f'error validating serving stuff: {ret}')
        return ret[1], 400
    print(new_product)

    # Calculating total weight/volume based on the serving size and servings per container
    # Getting the unit_conversion table
    ret = set_container_quantity(new_product)
    if ret[0] != 0:
        return ret[1], 500
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
    # Calculating total weight/volume based on the serving size and servings per container
    # Getting the unit_conversion table
    ret = set_container_quantity(edited_product)
    if ret[0] != 0:
        return ret[1], 500
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


def set_container_quantity(product: dict) -> Tuple[int, dict]:
    """ Modifies the given product dictionary to include the total_container_quantity
        and container_quantity_unit fields.

        Dictionary is pass by reference so it is not returned
    """
    ret = DBInterface.get_unit_translations()
    if ret[0] != 0:
        return ret
    conversion_dict = ret[1]['conversion_dict']
    # Getting unit type lists
    ret = DBInterface.get_units()
    if ret[0] != 0:
        return ret
    unit_dict = ret[1]['unit_dict']
    if product['servingUnit'] in unit_dict['weight']:
        unit_type = 'weight'
    elif product['servingUnit'] in unit_dict['volume']:
        unit_type = 'volume'
    else:
        # Should never be here
        unit_type = product['servingUnit']
        return -1, {'error': f'${unit_type} is not a recognized weight/measure..'}
    # Normalizing to either gram or ml
    total_container_quantity: float = 0
    if unit_type == 'weight':
        unconverted_total = float(product['servingsPerContainer']) * float(product['servingSize'])
        serving_unit: str = product['servingUnit']
        total_container_quantity = float(conversion_dict[serving_unit]['gram']) * unconverted_total
        product['total_quantity_unit'] = 'gram'
    else:
        unconverted_total = float(product['servingsPerContainer']) * float(product['servingSize'])
        print(f'unconverted total: {unconverted_total}')
        serving_unit: str = product['servingUnit']
        total_container_quantity = float(conversion_dict[serving_unit]['ml']) * unconverted_total
        print(f'converted total: {total_container_quantity}')
        product['total_quantity_unit'] = 'ml'
    product['total_container_quantity'] = total_container_quantity
    return 0, {}
