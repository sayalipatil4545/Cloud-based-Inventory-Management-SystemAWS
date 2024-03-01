import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from Database_Connection_Funcs.initDB import User,Product
from Database_Connection_Funcs.initDB import creatingTable
from Database_Models.ProductModel import productPydanticModel
from Database_Models.UserModel import userPydanticModel
from datetime import datetime
from sqlalchemy import select,update, text
from Database_Connection_Funcs.initDB import User,Product,Image
import bcrypt
import re
import boto3
from fastapi import UploadFile
from fastapi.encoders import jsonable_encoder
import json
from fastapi.responses import JSONResponse
# establishing database connection
import logging
# logging.basicConfig(filename="std.log", format='%(asctime)s %(message)s', filemode='w')
logging.basicConfig(filename='app1.log', format='%(name)s - %(levelname)s - %(message)s',level=logging.DEBUG)

# logging = logging.getlogging()
class databaseConnection():
    def __init__(self):
        load_dotenv(verbose=True)
        host = os.getenv('HOST')
        user = os.getenv('CLOUD_USERNAME')
        password = os.getenv('PASSWORD')
        schemaName = os.getenv('SCHEMA_NAME')
        self.db_url = 'mysql+pymysql://' + user + ':' + password + '@' + host + '/' + schemaName + ''
        self.engine = create_engine(self.db_url)
        creatingTable()
        
  
    # verifying the database connection
    def databaseConnectionVerification(self):
        conn = None
        try:
            conn = self.engine.connect()
            logging.info("Database connected")
            return True
        except Exception as e:
            logging.error("Error in connecting to database")
            return 'error-503'
        finally:
            if conn == None:
                logging.error("Error in connecting to database")
                return 'error-503'
            conn.close()
        #   function for hasahing password  

    def creatingPasswordHashing(self,password,salt_encrypted=None):
        bytes = password.encode('utf-8')
        if salt_encrypted== None:
            salt_encrypted = bcrypt.gensalt(12)
        encryptedPassword = bcrypt.hashpw(bytes,salt_encrypted)
        return encryptedPassword
    
    # function for email verification
    def EmailVerification(self,email):
        emailRegex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        if re.match(emailRegex,email):
            logging.info("Email Verified")
            return True
        else:
            logging.error("Email not verified")
            return False   
        # function for writing data in pydantic model


    def writeUserdata(self,user:userPydanticModel):
        Session = None
        try:
            Session = sessionmaker(bind = self.engine)
            session = Session()
            if not (self.EmailVerification(user.username)):
                logging.warning("Email not found")
                return '400_email'
            objectDataTime = datetime.now()
            encryptedPassword = str(self.creatingPasswordHashing(user.password))[1:]
            newUser = User(first_name = user.first_name,
                           last_name = user.last_name,
                           password = encryptedPassword.encode(),
                           username = user.username,
                           account_created = objectDataTime,
                           account_updated = objectDataTime
                           ) 
            session.add(newUser)
            session.commit()
            logging.info("User Created")
            return{
                "id": newUser.id,
                "first_name" : newUser.first_name,
                "last_name" : newUser.last_name,
                "username" : newUser.username,
                "account_created" : newUser.account_created,
                "account_updated" : newUser.account_updated,
            }  
        except Exception as e:
            print(e)
            logging.warning("User not created")
            return '400_bad'
        finally:
            if Session is None:
                session.close()
                     
    #####################Reading user data###################
    def readUserData(self,user_id=-1,userName=None):
        Session = None  
        query1 = None     
        try:
            dbConnection=self.databaseConnectionVerification()
            if dbConnection :
                Session = sessionmaker(bind = self.engine)
                session = Session()  
                if userName!=None and user_id==-1:
                    query1 = session.query(User).filter(User.username == userName).first()

                    return query1
                elif user_id!=-1 and userName==None:
                    query1 = session.query(User).filter(User.id == user_id).first()                  
                    return query1
                else:
                    query1 = session.query(User).filter(User.id == user_id).filter(User.username == userName).first()
                    return query1  
            return query1    
        except Exception as e:
            print(e)
            logging.warning("User not created. Exception")
            return '400_badRequest'
        finally:
            if Session is None:
                Session.close()

                
# verifying user password
    def verifyPassword(self,user_id=-1,password=None):
        Session = None
        try:
            Session = sessionmaker(bind = self.engine)
            session = Session()           
            query1 = session.query(User).filter(User.password == password).first()
            logging.warning("Invalid password for user with id ")
            return query1
        except Exception as e:
            print(e)
            logging.error("Error checking password for user with id")
            return '400_badRequest'
        finally:
            if Session is None:
                Session.close()
    
    # updating user details
    def UserDataUpdate(self,user_id:int,userName: str,inputUser:userPydanticModel):
        if ( inputUser.id != -1 or inputUser.account_created != '1900-01-00 00:00:00' or inputUser.account_updated != '1900-01-00 00:00:00'):
            logging.error("400 BAD REQUEST")
            return "400_bad_request"
        try:
            logging.warning(f"Updating user data for user with ID ")
            dbConnection=self.databaseConnectionVerification()
            if dbConnection :
                Session = sessionmaker(bind = self.engine)
                session = Session() 
                password_enrypted = str(self.creatingPasswordHashing(inputUser.password))[1:]
                objectDataTime = datetime.now()
                              
                stmt = (update(User).where(User.id == user_id).values(
                    first_name=inputUser.first_name,
                    last_name = inputUser.last_name,
                    password = password_enrypted,
                   username =inputUser.username,
                    account_updated = str(objectDataTime)
                    ))
                
                session.execute(stmt)              
                session.commit()
                logging.info("User Data Updated")
                return "200_success"
        except Exception as e:
            logging.error(f"Exception while updating user data")
            return -1
        finally:
            if Session is None:
                Session.close()


#    getting product data
    def readProductData(self,product_id=-1,sku=None):
        Session = None   
        p1 = None
        try:
                dbConnection=self.databaseConnectionVerification()
                if dbConnection :
                    Session = sessionmaker(bind = self.engine)
                    session = Session()  
                    if sku!=None and product_id==-1:
                        p1 = session.query(Product).filter(Product.sku == sku).first()
                     
                    elif product_id!=-1 and sku==None:
                        p1 = session.query(Product).filter(Product.id == product_id).first()
                
                    else:
                        p1 = session.query(Product).filter(Product.id == product_id).filter(Product.sku == sku).first()
                print(p1)
                logging.info("User data reading successful")
                return p1
        except Exception as e:
                print(e)
                logging.error("400 BAD REQUEST ERROR READING USER DATA")
                return '400_badRequest'
       
                    
#    inerting new products inside database
    def writeProductInfo(self,product:productPydanticModel, owner_user_id: int):
            Session = None

           
            if(int(product.quantity) > 100 or int(product.quantity)  < 0 ):
                logging.error(" quantity greater than 100 or less than 0")
                return( "400")
            try:

                Session = sessionmaker(bind = self.engine)
                session = Session()
                objectDataTime = datetime.now()
                print("objectDataTime ", objectDataTime)
                newProduct = Product(
                            name = product.name,
                            description = product.description,
                            sku = product.sku,
                            manufacturer = product.manufacturer,
                            quantity = product.quantity,
                            date_added = objectDataTime,
                            date_last_updated = objectDataTime,
                            owner_user_id = owner_user_id
                            ) 
                session.add(newProduct)
                session.commit()
                logging.info("Product created")
                return{
                    "id": newProduct.id,
                    "name" : newProduct.name,
                    "description" : newProduct.description,
                    "sku" : newProduct.sku,
                    "manufacturer" : newProduct.manufacturer,
                    "quantity" : newProduct.quantity,
                    "date_added" : str(newProduct.date_added),
                    "date_last_updated" : str(newProduct.date_last_updated),
                    "owner_user_id" : newProduct.owner_user_id
                }  
            except Exception as e:
                print(e)
                logging.error("Product not created")
                return '400_bad'
            finally:
                if Session is None:
                    session.close()
                    
  
#    using patch request  on product
    def patchProductData(self,product_id: int,inputProduct:productPydanticModel):
        print("inputProduct.id ", inputProduct.id)

        logging.info("Received request to patch product data with ID ")

        if (inputProduct.id != -1 or inputProduct.date_added != '1900-01-00 00:00:00' or inputProduct.date_last_updated != '1900-01-00 00:00:00'):
            logging.error("Invalid inputProduct provided")
            return "400_bad_request"
        
        print (inputProduct.quantity)
        if inputProduct.quantity is None:
            logging.error("inputProduct.quantity is None")
            return ("400")
        try:
            inputProduct.quantity = int(inputProduct.quantity)
        except:
            logging.error("Unable to convert inputProduct.quantity to integer")
            return ("400")
        if(int(inputProduct.quantity) > 100 or int(inputProduct.quantity)  < 0):
                logging.error("inputProduct.quantity is not between 0 and 100")
                return("400")
        try:
            dbConnection=self.databaseConnectionVerification()
            if dbConnection:
                Session = sessionmaker(bind = self.engine)
                session = Session() 
                objectDataTime = datetime.now()
                
                if inputProduct.name != "default" :
                    stmt = (update(Product).where(Product.id == product_id).values(
                    name=inputProduct.name,
                    ))
                    session.execute(stmt)
                if inputProduct.description != "default" :
                    stmt = (update(Product).where(Product.id == product_id).values(
                    description = inputProduct.description,
                    ))
                    session.execute(stmt)
                if inputProduct.sku != "default" :
                    stmt = (update(Product).where(Product.id == product_id).values(
                    sku = inputProduct.sku,
                    ))
                    session.execute(stmt)
                if inputProduct.manufacturer != "default" :
                    stmt = (update(Product).where(Product.id == product_id).values(
                    manufacturer = inputProduct.manufacturer,
                    ))
                    session.execute(stmt)
                if inputProduct.quantity != "default" :
                    stmt = (update(Product).where(Product.id == product_id).values(
                    quantity = inputProduct.quantity,
                    ))
                    session.execute(stmt)
                
                session.commit()
                logging.info("Successfully patched product data with ID ")

                return "200_success"
        except Exception as e:
            print("Exception :"+str(e))
            logging.error("Error occurred while patching product data with ID ")
            return "400_bad_request"
        finally:
            if Session is None:
                Session.close()

  # deleteing product
    def deleteProductInfo(self,productId):
            Session = None
            try:
                Session = sessionmaker(bind = self.engine)
                session = Session()
                objectDataTime = datetime.now()                
                session.query(Product).filter(Product.id == productId).delete()               
                session.commit()
                logging.info("Product deleted successfully")
                logging.info(f"Product with  deleted successfully")
                return 'Deleted_Successfully' 
            except Exception as e:
                print(e)
                logging.error(f"Error deleting product with ID")
                return '400_bad'
            finally:
                if Session is None:
                    session.close()
#   updating the product
    def productInfoUpdate(self,product_id: int,inputProduct:productPydanticModel):
        print("inputProduct.id ", inputProduct.id)
        if (inputProduct.id != -1 or inputProduct.date_added != '1900-01-00 00:00:00' or inputProduct.date_last_updated != '1900-01-00 00:00:00'):
            logging.error(f"Invalid input product data")
            return "400_bad_request"
        if(int(inputProduct.quantity) > 100 or int(inputProduct.quantity)  < 0 or  int(inputProduct.quantity) == None ):
                logging.error(f"Invalid input product quantity")
                return("400")
        try:
            dbConnection=self.databaseConnectionVerification()
            if dbConnection :
                Session = sessionmaker(bind = self.engine)
                session = Session() 
                objectDataTime = datetime.now()
                
                print("inputProduct.name ",inputProduct.name," \nProduct id ", product_id)
                logging.debug(f"Updating product with ID ")
                stmt = (update(Product).where(Product.id == product_id).values(
                    name=inputProduct.name,
                    description = inputProduct.description,
                    sku = inputProduct.sku,
                    manufacturer = inputProduct.manufacturer,
                    quantity = inputProduct.quantity,
                    date_last_updated = objectDataTime
                    ))

                session.execute(stmt)              
                session.commit()
                logging.info("Updated product info")
                logging.info(f"Product with ID updated successfully")
                return "200_success"
        except Exception as e:
            print("Exception :"+str(e))
            logging.error(f"Error updating product with ID ")
            return "400_bad_request"
        finally:
            if Session is None:
                Session.close()



    def get_every_image_list(self,product_id):
        Session = None
        try:
            Session = sessionmaker(bind=self.engine)
            session = Session()
            found_user_image=session.query(Image).filter(Image.product_id == product_id).all()
            return found_user_image
        except Exception as e:
            return 'exception'
        finally:
            if Session != None:
                session.close()

    def getting_image(self,product_id,imageId):
        Session = None
        try:
            Session = sessionmaker(bind=self.engine)
            session = Session()
            found_user_image=session.query(Image).filter(Image.product_id == product_id, Image.image_id==imageId).all()
            if len(found_user_image) == 0:
                return 'no_image'
            return found_user_image
        except Exception as e:
            return 'exception'
        finally:
            if Session != None:
                session.close()


    def delete_s3_objects(self,image_id=-1):
        Session = None
        try:
            Session = sessionmaker(bind=self.engine)
            session = Session()
            if image_id==-1:
                images  = session.query(Image).filter(Image.product_id.is_(None)).all()
            else:
                images  = session.query(Image).filter(Image.image_id==image_id).all()
            json_objects = [img.__dict__ for img in images]
            s3_obj = boto3.client('s3')
            S3_Bucket = os.getenv('S3_Bucket_Name')
            for obj in json_objects:
                object_param = obj['s3_bucket_path']
                # delete the object
                s3_obj.delete_object(Bucket=S3_Bucket, Key=object_param)
            session.query(Image).filter(Image.product_id.is_(None)).delete()
            session.commit()
            logging.info("Delete S3 Bucket")
        except Exception as e:
            return 'exception'
        finally:
            if Session != None:
                session.close()

    def image_data_store(self,productId,image:UploadFile,file_path):
        Session = None
        try:
            Session = sessionmaker(bind=self.engine)
            session = Session()
            dateTimeParameter = datetime.now()
            DateString = dateTimeParameter.strftime('%Y%m%d')
            timeString = dateTimeParameter.strftime('%H%M%S')
            TimeDateString = f"{DateString}_{timeString}"
            #Create the s3 bucket path
            s3_obj = boto3.client('s3')
            S3_Bucket = os.getenv('S3_Bucket_Name')
            object_param = f'{productId}_'+str(TimeDateString)+'_'+str(image.filename)
            with open(file_path, 'rb') as f:
                s3_obj.upload_fileobj(f, S3_Bucket, object_param)
            s3_bucket_path=object_param
            s3_image = Image(product_id=productId,file_name=image.filename,date_created=dateTimeParameter,s3_bucket_path=s3_bucket_path)
            session.add(s3_image)
            session.commit()
            if s3_image:
                logging.info("Stored Image Data")
                return {
                    "image_id": s3_image.image_id,
                    "product_id":s3_image.product_id,
                    "file_name":s3_image.file_name,
                    "date_created":s3_image.date_created,
                    "s3_bucket_path":s3_image.s3_bucket_path     
            }
            else:
                return "no_image"
        except Exception as e:
            print(e)
            return 'exception'
        finally:
            if Session != None:
                session.close()
            

    def deleting_user_image(self,product_id,imageId):
        Session=None
        try:
            Session=sessionmaker(bind=self.engine)
            session=Session()
            user_image=session.query(Image).filter(Image.product_id == product_id, Image.image_id==imageId).first()
            self.delete_s3_objects(imageId)
            session.delete(user_image)
            session.commit() 
            logging.info("Deleting User Image")      
        except Exception as e:
            return {'user':'exception'}
        finally:
            if Session != None:
                session.close()
    