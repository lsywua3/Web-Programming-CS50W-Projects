CREATE TABLE reviews(
    id SERIAL PRIMARY KEY,
    rating INTEGER NOT NULL CHECK(rating > 0 AND rating <= 5),
    content VARCHAR NOT NULL,
    userid INTEGER NOT NULL REFERENCES users,
    book_id INTEGER NOT NULL REFERENCES books
);