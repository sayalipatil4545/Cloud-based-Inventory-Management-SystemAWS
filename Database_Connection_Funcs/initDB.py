from dotenv import load_dotenv
from sqlalchemy import create_engine,Column,Integer,String, LargeBinary,DateTime,ForeignKey, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
import mysql.connector
import pymysql
import os
from sqlalchemy.orm import declarative_base

Base = declarative_base()
# defining the parameters of table user
class User(Base):
    __tablename__ = 'Users'
    id = Column(Integer, primary_key = True, autoincrement = True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    password = Column(String(255))
    username = Column(String(50), unique=True)
    account_created = Column(DateTime)
    account_updated = Column(DateTime)
    user_info = relationship("Product",back_populates="product_info")

# defining the parameters of table product  
class Product(Base):
    __tablename__ = 'Products'
    id = Column(Integer, primary_key = True, autoincrement = True)
    name = Column(String(50))
    description = Column(String(50))
    sku = Column(String(50),unique=True, nullable=True)
    manufacturer = Column(String(50))
    quantity = Column(Integer)
    date_added = Column(DateTime)
    date_last_updated = Column(DateTime)
    owner_user_id = Column(Integer,ForeignKey("Users.id"))
    product_info = relationship("User",back_populates="user_info")
    # product_images_info= relationship("user_info",back_populates="image_info")
    product_images_info= relationship("Image",back_populates="image_info")

class Image(Base):
    __tablename__= 'Image'
    image_id = Column(Integer,primary_key=True,autoincrement=True)
    product_id=Column(Integer,ForeignKey("Products.id"))
    file_name=Column(String(100))
    date_created=Column(DateTime)
    s3_bucket_path=Column(String(100))
    image_info=relationship("Product",back_populates="product_images_info")

# establishing connection
class creatingTable():
    def __init__(self):
        load_dotenv(verbose=True)
        host = os.getenv('HOST')
        user = os.getenv('CLOUD_USERNAME')
        password = os.getenv('PASSWORD')
        schema_name = os.getenv('SCHEMA_NAME')
        db_url = 'mysql+pymysql://' + user + ':' + password + '@' + host + '/' + schema_name + ''
        engine = create_engine(db_url)
        Base.metadata.create_all(engine)
