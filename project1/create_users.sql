CREATE TABLE users(
    id SERIAL PRIMARY KEY,
    username VARCHAR NOT NULL UNIQUE,
    passwords VARCHAR NOT NULL
);