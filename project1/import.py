import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("books.csv")
    reader = csv.reader(f)
    next(reader)
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO books (ISBN, title, author, PublicationYear) VALUES (:isbn, :title, :author, :year)", 
                    {"isbn": isbn, "title": title, "author": author, "year": year})
    
    print("Finished adding books")
    db.commit()

if __name__ == "__main__":
    main()
