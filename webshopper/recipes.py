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

bp = Blueprint('recipes', __name__, url_prefix='/recipes')


@bp.route('/new_recipe', methods=('POST',))
@login_required
def new_recipe():
    """
        This endpoint is hit as soon as the user confirms the name
        of a new recipe.

    :return:
    """
    json: dict = request.json
    recipe_name: str = json['recipe_name']
    ret = DBInterface.new_recipe(session['user_id'], recipe_name)
    if ret[0] != 0:
        return ret[1], 500
    return ret[1], 200


@bp.route('/new_ingredient', methods=('POST',))
@login_required
def new_ingredient():
    """
        Needs to return ingredient id upon success for accounting client side
    :return:
    """
    json: dict = request.json
    print(f'Here are the json values in new_ingredient: {json}')
    recipe_id: int = json['new_ingredient']['recipe_id']
    productId: str = json['new_ingredient']['productId']
    ingredient_name = json['new_ingredient']['ingredient_name']
    ingredient_qty = json['new_ingredient']['ingredient_quantity']
    ingredient_unit = json['new_ingredient']['ingredient_unit']
    product_description = json['new_ingredient']['product_description']
    ret = DBInterface.new_ingredient(session['user_id'],
                                     recipe_id,
                                     productId,
                                     ingredient_name,
                                     ingredient_qty,
                                     ingredient_unit,
                                     product_description)
    if ret[0] != 0:
        print(ret)
        return ret[1], 500
    return ret[1], 200


@bp.route('/delete_ingredient', methods=('POST',))
@login_required
def delete_ingredient():
    json: dict = request.json
    ingredient_id: str = json['ingredient_id']
    ret = DBInterface.delete_ingredient(ingredient_id)
    if ret[0] != 0:
        return ret[1], 500
    return {}, 200


@bp.route('/recipe_text', methods=('POST',))
@login_required
def update_recipe_text():
    """ Updates the recipe_text field for the given recipe """
    json: dict = request.json
    recipe: dict = json['recipe']
    recipe_text: str = recipe['recipe_text']
    recipe_id: int = int(recipe['recipe_id'])
    ret = DBInterface.update_recipe_text(session['user_id'], recipe_id, recipe_text)
    if ret[0] != 0:
        return ret[1], 500
    return {}, 200


@bp.route('/order_recipes', methods=('POST',))
@login_required
def order_recipes():
    """
        POST data can include the complete list of ingredients and their corresponding
        productId values.

        We would pull the productId serving information from the DB, then
    :return:
    """
    json: dict = request.json
