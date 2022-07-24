import sqlite3
from typing import Tuple
from typing import List

import click
from flask import current_app, g
from flask.cli import with_appcontext
from werkzeug.security import check_password_hash, generate_password_hash


class DBInterface:
    """ Static class """

    @staticmethod
    def _execute_query(sql_string: str
                       , parameters: tuple = None
                       , selection: bool = False) -> Tuple[int, dict]:
        """ selection: returns cursor after executing query
        """
        db: sqlite3.Connection = DBInterface.get_db()
        cursor: sqlite3.Cursor = db.cursor()
        cursor.execute('PRAGMA foreign_keys = 1')  # Enforce foreign key constraints per connection
        try:
            if parameters is None:
                cursor.execute(sql_string)
                db.commit()
            else:
                cursor.execute(sql_string, parameters)
                db.commit()
            if selection:
                return 0, {'cursor': cursor}
            else:
                return 0, {}
        except sqlite3.Error as e:
            return -1, {'error': e}

    @staticmethod
    def close_db(e=None):
        """ Runs on teardown """
        db = g.pop('db', None)
        if db is not None:
            db.close()

    @staticmethod
    def get_db() -> sqlite3.Connection:
        """ If multiple db calls are made per request this will
            prevent opening multiple connections to the database

            Helper for all db functions
        """
        if 'db' not in g:
            g.db = sqlite3.connect(
                current_app.config['DATABASE'],
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            g.db.row_factory = sqlite3.Row
        return g.db

    @staticmethod
    def new_user(username: str, password) -> Tuple[int, dict]:
        query = """ INSERT INTO users (username, password_hash)
                    VALUES (?, ?)
                """
        ret = DBInterface._execute_query(query,
                                         (username, generate_password_hash(password)))
        if ret[0] != 0:
            err: sqlite3.Error = ret[1]['error']
            if err is sqlite3.IntegrityError:
                return -1, {'error': 'Username already taken'}
            else:
                return -1, {'error': str(err)}
        return 0, {}

    @staticmethod
    def get_user(username: str, password: str) -> Tuple[int, dict]:
        """ Does credential checking
        """
        query = """ SELECT * 
                    FROM users
                    WHERE username = ?
                """
        ret = DBInterface._execute_query(query, (username,), selection=True)
        if ret[0] != 0:
            return -1, {'error': str(ret[1])}
        user: sqlite3.Row = ret[1]['cursor'].fetchone()
        if user is None:
            return -1, {'error': 'Invalid username or password'}
        elif not check_password_hash(user['password_hash'], password):
            return -1, {'error': 'Invalid username or password'}
        return 0, {'user': user}

    @staticmethod
    def deposit_tokens(user_id: int, token_dict: dict) -> Tuple[int, dict]:
        """ responsible for depositing tokens into db """
        query = """  UPDATE users 
                     SET access_token = ?
                        ,access_token_timestamp = ?
                        ,refresh_token = ?
                        ,refresh_token_timestamp = ? 
                    WHERE user_id = ?
                """
        ret = DBInterface._execute_query(query, (token_dict['access_token']
                                                 , token_dict['access_token_timestamp']
                                                 , token_dict['refresh_token']
                                                 , token_dict['refresh_token_timestamp']
                                                 , user_id))
        if ret[0] != 0:
            return -1, {'error': str(ret[1])}
        return 0, {}

    @staticmethod
    def update_location(user_id: int, locationId: str,
                        location_chain: str, location_address: str):
        """ Updates user locationId value """
        query = """ UPDATE users
                    SET locationId = ?
                        ,location_chain = ?
                        ,location_address = ?
                    WHERE user_id = ?
                """
        ret = DBInterface._execute_query(query, (locationId,
                                                 location_chain,
                                                 location_address,
                                                 user_id))
        if ret[0] != 0:
            return -1, ret
        return 0, {}

    @staticmethod
    def add_product(user_id: int, new_product: dict) -> Tuple[int, dict]:
        """
            Requires interacting with two different tables, so we will not rely upon ._execute_query
            but will take destiny into our own hands here.

        :param user_id:
        :param new_product: {
            'productId': <>,
            'upc': <>,
            'description': <>,
            'image_urls': [{'perspective': <>, 'url': <>}, ...],
            'servingSize': <>,
            'servingsPerContainer': <>,
            'servingUnit': <gram, lb, oz, cup, tbsp, tsp, floz>,
            'unitType: <'weight', 'volume'>,
            'includeAlternate': <'true', 'false'>,
            'alternateSS': <>,
            'alternateSPC: <>,
            'alternateSU': <>}
        """
        db: sqlite3.Connection = DBInterface.get_db()
        crsr: sqlite3.Cursor = db.cursor()
        product_query = """ INSERT INTO products
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """
        try:
            crsr.execute(product_query, (user_id,
                                         new_product['productId'],
                                         new_product['upc'],
                                         new_product['description'],
                                         float(new_product['servingSize']),
                                         float(new_product['servingsPerContainer']),
                                         new_product['servingUnit'],
                                         new_product['unitType'],
                                         new_product['includeAlternate'],
                                         float(new_product['alternateSS']),
                                         float(new_product['alternateSPC']),
                                         new_product['alternateSU']))
        except sqlite3.Error as e:
            return -1, {'error': str(e)}
        # else:  # No alternate values
        #     product_query = """ INSERT INTO products (user_id
        #                                                 , productId
        #                                                 , upc
        #                                                 , description
        #                                                 , serving_size
        #                                                 , servings_per_container
        #                                                 , serving_unit
        #                                                 , unit_type
        #                                                 , include_alternate
        #                                                 , alternate_ss
        #                                                 , alternate_spc
        #                                                 , alternate_su)
        #                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        #                     """
        #     try:
        #         crsr.execute(product_query, (user_id,
        #                                      new_product['productId'],
        #                                      new_product['upc'],
        #                                      new_product['description'],
        #                                      float(new_product['servingSize']),
        #                                      float(new_product['servingsPerContainer']),
        #                                      new_product['servingUnit'],
        #                                      new_product['unitType'],
        #                                      new_product['includeAlternate'],
        #                                      0,
        #                                      0,
        #                                      new_product['alternate_su']))
        #     except sqlite3.Error as e:
        #         return -1, {'error': str(e)}
        # product_query successful. Now entering URLs
        url_query = """ INSERT INTO products_imgurls
                        VALUES (?, ?, ?, ?)
                    """
        urls: list = new_product['image_urls']
        for url in urls:
            try:
                crsr.execute(url_query, (user_id,
                                        new_product['productId'],
                                        url['perspective'],
                                        url['url']))
            except sqlite3.Error as e:
                return -1, {'error': str(e)}
        # Successfully inserted all values
        db.commit()
        return 0, {}

    @staticmethod
    def get_user_prods(user_id: int) -> Tuple[int, dict]:
        """
            Pulls from products table. Calls helper function to pull
            image urls from products_imgurls table.

            Failure by get_imgurls helper function results in total failure
            of this function call.

        :param user_id:
        :return:  On success the results value will be a list of:
            { 'productId': <>,
            'upc': <>,
            'description': <>,
            'image_urls': [{'perspective': <>, 'url': <>}, ...],
            'servingSize': <>,
            'servingsPerContainer': <>,
            'servingUnit': <>,
            'unitType: <'weight', 'volume'>,
            'includeAlternate': <'true', 'false'>,
            'alternateSS': <>,
            'alternateSPC: <>,
            'alternateSU': <>}
        """

        query = """ SELECT *
                    FROM products 
                    WHERE products.user_id = ?
                """
        ret = DBInterface._execute_query(query, (user_id,), selection=True)
        if ret[0] != 0:
            return ret
        cursor: sqlite3.Cursor = ret[1]['cursor']
        ret_rows: List[dict] = cursor.fetchall()
        # Building return list
        products: list = []
        for row in ret_rows:
            prod_dict = {
                'productId': row['productId'],
                'upc': row['upc'],
                'description': row['description'],
                'image_urls': 'PLACEHOLDER',
                'servingSize': row['serving_size'],
                'servingUnit': row['serving_unit'],
                'servingsPerContainer': row['servings_per_container'],
                'unitType': row['unit_type'],
                'includeAlternate': row['include_alternate'],
                'alternateSS': row['alternate_ss'],
                'alternateSPC': row['alternate_spc'],
                'alternateSU': row['alternate_su']
            }
            # Retrieving the img_urls
            ret = DBInterface.get_imgurls(user_id, prod_dict['productId'])
            if ret[0] != 0:
                return ret
            prod_dict['image_urls'] = ret[1]['urls']
            products.append(prod_dict)
        return 0, {'products': products}

    @staticmethod
    def get_imgurls(user_id: int, productId: str) -> Tuple[int, dict]:
        """
            Returns a [{'perspective': <>, 'url': <>}, ...]
            Intended as a helper function for get_user_prods.
        """
        query = """  SELECT *
                    FROM products p, products_imgurls pi
                    WHERE p.user_id = pi.user_id
                         AND p.productId = pi.productId
                         AND p.user_id = ?
                         and p.productId = ?
                """
        ret = DBInterface._execute_query(query, (user_id, productId), selection=True)
        if ret[0] != 0:
            return ret
        cursor: sqlite3.Cursor = ret[1]['cursor']
        ret_rows = cursor.fetchall()
        url_list: list = []
        for row in ret_rows:
            tmp_dict = {
                'perspective': row['perspective'],
                'url':  row['url']
            }
            url_list.append(tmp_dict)
        return 0, {'urls': url_list}

    @staticmethod
    def edit_product(user_id: int, edited_product: dict) -> Tuple[int, dict]:
        """
            Expects a pull product object as documented in DBInterface.add_product
        """
        query = """ UPDATE products
                    SET 
                      serving_size = ?
                      , servings_per_container = ?
                      , serving_unit = ?
                      , unit_type = ?
                      , include_alternate = ?
                      , alternate_ss = ?
                      , alternate_spc = ?
                      , alternate_su = ?  
                   WHERE
                        products.user_id = ?
                        AND products.productId = ?
                """
        ret = DBInterface._execute_query(query, (float(edited_product['servingSize']),
                                                 float(edited_product['servingsPerContainer']),
                                                 edited_product['servingUnit'],
                                                 edited_product['unitType'],
                                                 edited_product['includeAlternate'],
                                                 float(edited_product['alternateSS']),
                                                 float(edited_product['alternateSPC']),
                                                 edited_product['alternateSU'],
                                                 user_id,
                                                 edited_product['productId']))
        if ret[0] != 0:
            return -1, {'error': str(ret[1]['error'])}
        return 0, {}


# Auxiliary functions
def init_db():
    db = DBInterface.get_db()
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


def init_app(app):
    app.teardown_appcontext(DBInterface.close_db)
    app.cli.add_command(init_db_command)


@click.command('init-db')
@with_appcontext
def init_db_command():
    """ Clear the existing data and create new tables"""
    init_db()
    click.echo('Initialized the database')