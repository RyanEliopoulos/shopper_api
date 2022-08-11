from typing import Tuple
from typing import List
from webshopper.auth import login_required
from webshopper.auth import valid_tokens
from webshopper.Communicator import Communicator
from webshopper.db import DBInterface
import sqlite3
from math import floor
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, jsonify, Response, make_response
)


ROUNDING_THRESHOLD = .05

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
@valid_tokens
def order_recipes():
    """
        POST data can include the complete list of ingredients and their corresponding
        productId values.

        We would pull the productId serving information from the DB, then
    :return:
    """
    # Normalizing product quantities across selected recipes
    json: dict = request.json
    ret = normalize_products_from_recipes(json['selected_recipes'])
    if ret[0] != 0:
        return ret[1], 500
    order_tally: dict = ret[1]['order_tally']
    # Determining total containers count for each product
    productIds = list(order_tally.keys())
    ret = DBInterface.get_specific_prods(session['user_id'], productIds)
    if ret[0] != 0:
        return ret[1], 500
    products_dict = ret[1]['products_dict']
    # Conducting final tally (# of containers (e.g. servings per container) needed for each productId)
    final_tally: dict = {}
    rounded_values: dict = {}  # Keyed on productId
    for prod_id in productIds:
        final_tally[prod_id] = order_tally[prod_id] / products_dict[prod_id]['total_container_quantity']
        # Handling rounding
        floored: int = floor(final_tally[prod_id])
        diff: float = final_tally[prod_id] - floored
        if diff > ROUNDING_THRESHOLD:
            # Rounding to next whole number
            rounded_values[prod_id] = {
                'product_description': products_dict[prod_id]['description'],
                'original_value': final_tally[prod_id],
            }
            intermediate_rounding = final_tally[prod_id] + 1
            final_tally[prod_id] = floor(intermediate_rounding)
            rounded_values[prod_id]['rounded_value'] = final_tally[prod_id]
    # Should have a complete final_tally dictionary {<productId>: <integer>, ...}
    print(f'Here is the final_tally dict: {final_tally}')
    list_ft = list(final_tally)
    print(f'Here is the final_tally in list form: {list_ft}')
    print(f'Here is the rounded_values dict: {rounded_values}')
    # Transforming into a list of dicts before sending off to Kroger
    order_list: list = []
    for productId in final_tally:
        tmp_dict = {
            'upc': productId,
            'quantity': final_tally[productId]
        }
        order_list.append(tmp_dict)
    ret = Communicator.add_to_cart(order_list)
    if ret[0] != 0:
        return ret, 500
    return {'rounded_values': rounded_values}, 200


def normalize_products_from_recipes(recipes: list) -> Tuple[int, dict]:
    """
        Returns a dictionary with {<productId>: <normalized quantity>, ... }
        Normalized to gram/ml
    :return:
    """
    ret = DBInterface.get_unit_translations()
    if ret[0] != 0:
        return ret
    conversion_dict = ret[1]['conversion_dict']
    ret = DBInterface.get_units()
    if ret[0] != 0:
        return ret
    unit_dict = ret[1]['unit_dict']  # {'weight': ['gram', 'lb', ...], 'volume': ['cup', ..]}
    # Normalizing per recipe
    tally: dict = {}
    print(recipes)
    for recipe in recipes:
        ingredients: dict = recipe['ingredients']
        for ing_id in ingredients:
            ingredient = ingredients[ing_id]
            productId = ingredient['productId']
            unit = ingredient['ingredient_unit']
            quantity = ingredient['ingredient_quantity']
            print(f'conversion_dict: {conversion_dict}')
            if ingredient['ingredient_unit'] in unit_dict['weight']:
                normalized_quantity = float(conversion_dict[unit]['gram']) * float(quantity)
            elif ingredient['ingredient_unit'] in unit_dict['volume']:
                normalized_quantity = float(conversion_dict[unit]['ml']) * float(quantity)
            else:
                return -1, {'error': f'unit type of ingredient {ingredient} in recipe {recipe} is invalid'}
            if productId in tally:
                tally[productId] += normalized_quantity
            else:
                tally[productId] = normalized_quantity
    # normalizing across all recipes
    order_tally: dict = {}
    for productId in tally:
        if productId in order_tally:
            order_tally[productId] += tally[productId]
        else:
            order_tally[productId] = tally[productId]
    return 0, {'order_tally': tally}
