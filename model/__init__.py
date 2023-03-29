from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import mysql.connector

Base = declarative_base()

engine = create_engine('mysql://admin:C9SaiK9pRkmoHuXvTV10@localhost/cutting', echo=True)

Session = sessionmaker(bind=engine)
session = Session()

mydb = mysql.connector.connect(
  host="localhost",
  user="admin",
  password="C9SaiK9pRkmoHuXvTV10",
  database="cutting"
)
