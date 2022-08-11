DROP TABLE IF EXISTS units;
DROP TABLE IF EXISTS unit_translations;
DROP TABLE IF EXISTS ingredients;
DROP TABLE IF EXISTS products_imgurls;
DROP TABLE IF EXISTS recipes;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    access_token TEXT default '',
    access_token_timestamp FLOAT DEFAULT 0,
    refresh_token TEXT default '',
    refresh_token_timestamp FLOAT DEFAULT 0,
    locationId TEXT DEFAULT '',
    location_chain TEXT DEFAULT '',
    location_address TEXT DEFAULT ''
);

CREATE TABLE products (
    user_id INTEGER NOT NULL,
    productId TEXT NOT NULL,
    upc TEXT NOT NULL,
    description TEXT NO NULL,
    serving_size float NOT NULL,
    servings_per_container FLOAT NOT NULL,
    serving_unit TEXT NOT NULL,
    unit_type TEXT NOT NULL,                    --  'weight' or 'volume'
    total_container_quantity FLOAT NOT NULL,    --   normalized to either grams or milliliters
    total_quantity_unit TEXT CHECK(total_quantity_unit IN ('gram', 'ml')),
    include_alternate INTEGER NOT NULL,         -- boolean: 'true' or 'false'
    alternate_ss FLOAT,
    alternate_spc FLOAT,
    alternate_su TEXT,

    PRIMARY KEY (user_id, productId),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE products_imgurls (
    user_id INTEGER NOT NULL,
    productId TEXT NOT NULL,
    perspective TEXT NOT NULL,
    url TEXT NOT NULL,

    PRIMARY KEY(user_id, productId, perspective, url),
    FOREIGN KEY(user_id, productId) REFERENCES products(user_id, productId)
);


CREATE TABLE recipes (
    recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    recipe_name TEXT NOT NULL,
    recipe_text TEXT NOT NULL DEFAULT '',  -- User-provided details on the recipe i.e. directions

    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE ingredients (
    ingredient_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    recipe_id INTEGER NOT NULL,
    productId TEXT NOT NULL,
    ingredient_name TEXT NOT NULL,
    ingredient_quantity FLOAT NOT NULL,
    ingredient_unit TEXT NOT NULL,
    product_description TEXT NOT NULL,

    FOREIGN KEY (user_id, productId) REFERENCES products(user_id, productId),
    FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id)

);

CREATE TABLE unit_translations (
    from_unit TEXT NOT NULL,
    from_value INTEGER CHECK (from_value IN (1)) DEFAULT 1,  -- This column should always have a value of 1
    to_unit TEXT NOT NULL,
    to_value FLOAT NOT NULL,
    type TEXT CHECK (type IN ('weight', 'volume'))
);

CREATE TABLE units (
    unit TEXT NOT NULL,  -- e.g. gram, cup
    unit_type TEXT CHECK(unit_type IN ('weight', 'volume'))
);


-----  Units
-- weight measures
insert into units (unit, unit_type) values ('oz', 'weight');
insert into units (unit, unit_type) values ('gram', 'weight');
insert into units (unit, unit_type) values ('lb', 'weight');
-- volume measures
insert into units (unit, unit_type) values ('tbsp', 'volume');
insert into units (unit, unit_type) values ('tsp', 'volume');
insert into units (unit, unit_type) values ('cup', 'volume');
insert into units (unit, unit_type) values ('floz', 'volume');
insert into units (unit, unit_type) values ('ml', 'volume');


---- Unit Translations

-- Weight measures
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('oz', 1, 'gram', 28.3495, 'weight');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('oz', 1, 'lb', .0625, 'weight');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('oz', 1, 'oz', 1, 'weight');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('gram', 1, 'gram', 1, 'weight');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('gram', 1, 'lb', .00220462, 'weight');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('gram', 1, 'oz', .035274, 'weight');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('lb', 1, 'gram', 453.592, 'weight');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('lb', 1, 'oz', 16, 'weight');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('lb', 1, 'lb', 1, 'weight');
-- Volume measures
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('tbsp', 1, 'tsp', 3, 'volume');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('tbsp', 1, 'cup', .0625, 'volume');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('tbsp', 1, 'floz', .5, 'volume');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('tbsp', 1, 'tbsp', 1, 'volume');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('tbsp', 1, 'ml', 14.7868, 'volume');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('tsp', 1, 'tsp', 1, 'volume');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('tsp', 1, 'tbsp', .33333, 'volume');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('tsp', 1, 'cup', .0208333, 'volume');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('tsp', 1, 'floz', .166667, 'volume');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('tsp', 1, 'ml', 4.92892, 'volume');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('cup', 1, 'cup', 1, 'volume');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('cup', 1, 'tbsp', 16, 'volume');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('cup', 1, 'tsp', 48, 'volume');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('cup', 1, 'floz', 8, 'volume');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('cup', 1, 'ml', 236.588, 'volume');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('floz', 1, 'floz', 1, 'volume');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('floz', 1, 'tbsp', 2, 'volume');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('floz', 1, 'tsp', 6, 'volume');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('floz', 1, 'cup', .125, 'volume');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('floz', 1, 'ml', 29.5735, 'volume');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('ml', 1, 'ml', 1, 'volume');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('ml', 1, 'tbsp', .067628, 'volume');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('ml', 1, 'tsp', .202884, 'volume');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('ml', 1, 'cup', .00422675, 'volume');
insert into unit_translations (from_unit, from_value, to_unit, to_value, type) values ('ml', 1, 'floz', .033814, 'volume');
