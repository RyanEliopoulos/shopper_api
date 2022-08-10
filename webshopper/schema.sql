DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS products_imgurls;

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
    unit_type TEXT NOT NULL,            --'weight' or 'volume'
    include_alternate INTEGER NOT NULL,     -- boolean: 'true' or 'false'
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