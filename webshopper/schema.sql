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