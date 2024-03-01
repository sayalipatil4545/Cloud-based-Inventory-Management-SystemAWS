from Database_Connection_Funcs.initDB import creatingTable
from fastapi import FastAPI,HTTPException,status,Depends,File, UploadFile
from sqlalchemy.ext.declarative import declarative_base
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import json
from Database_Models.ProductModel import productPydanticModel
from sqlalchemy import create_engine
from Database_Connection_Funcs import newDBConn as db
from Database_Connection_Funcs.newDBConn import databaseConnection
from sqlalchemy.orm import sessionmaker
from Database_Models.UserModel import userPydanticModel
import pymysql
import os
from fastapi.encoders import jsonable_encoder
from json import JSONEncoder
from fastapi.responses import JSONResponse
import logging

import statsd

statsd_total = statsd.StatsClient(host='localhost', port=8125)



####################Initial setup for FAST API######################
app=FastAPI()

#######################Sting Up the Database#####################
dbConnect = None
databaseObj = databaseConnection()
creatingTable()
security = HTTPBasic()
# -----------logging------------

logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s',level=logging.DEBUG)

##################healtz####################
@app.get('/healthz',status_code=status.HTTP_200_OK)
def CheckingHealthParameter():

    statsd_total.incr("total", 1)
    statsd_total.incr("healthz",1)

    dbCon=databaseObj.databaseConnectionVerification()
    if dbCon == 'error-503':
        logging.fatal("Fatal Error")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str("Cant esablish connection with Mysql Server"))
    elif dbCon == True: 
        logging.info("Database connected")
        return {"status": "Database Connected Successfully"}
    
@app.get('/health',status_code=status.HTTP_200_OK)
def CheckingHealthParameter():

    statsd_total.incr("total", 1)
    statsd_total.incr("healthz",1)

    dbCon=databaseObj.databaseConnectionVerification()
    if dbCon == 'error-503':
        logging.fatal("Fatal Error")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str("Cant esablish connection with Mysql Server"))
    elif dbCon == True: 
        logging.info("Database connected")
        return {"status": "Database Connected Successfully"}
    
 
##############User Authentication###############33
def CurrentUserName(credentials: HTTPBasicCredentials = Depends(security)):
    getInputUserName = credentials.username.encode("utf8")
    UserFetched=databaseObj.readUserData(userName=credentials.username)

    if UserFetched==None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Could not Find User")
    if UserFetched == '400_badRequest':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Enter correct password")      
    else: 
        UsernameValidation = secrets.compare_digest(getInputUserName, UserFetched.username.encode("utf-8"))
        salt=str(UserFetched.password)[1:31].encode()
        is_correct_password = secrets.compare_digest(databaseObj.creatingPasswordHashing(credentials.password,salt),UserFetched.password.encode("utf-8")[1:-1])
       
    
    if not (UsernameValidation and is_correct_password ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password Incorrect"
        ) 
    return credentials.username

##################Create and save user ##################
@app.post('/v2/user',status_code=status.HTTP_201_CREATED)
def CreateNewUser(user:userPydanticModel):

    statsd_total.incr("total", 1)
    statsd_total.incr("Create User",1)


    searchExistinUser = databaseObj.readUserData(userName = user.username)

    
    if searchExistinUser == None:
        userExist= databaseObj.writeUserdata(user)


        if userExist == '400_email' or userExist == '400_bad':
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kindly provide a valid email address",
        )
        else:
            return userExist
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists.",
        )

############Get user account details##################
@app.get("/v1/user/{userId}")
def getUserDetails(userId:int,username: str = Depends(CurrentUserName)):
    statsd_total.incr("total", 1)
    statsd_total.incr("Get User",1)

    if not type(userId) is int:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header Invalid")
    userExist = databaseObj.readUserData(userName = username)
    if(userExist == 'no_user'):
       raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cannot found user")
    else:
        if(userId == userExist.id):
            return {
                    "id": userExist.id,
                    "first_name": userExist.first_name,
                    "last_name": userExist.last_name,
                    "username": userExist.username,
                    "account_created":userExist.account_created,
                    "account_updated": userExist.account_updated
            }
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden request")

###################Update User###################
@app.put("/v1/user/{userId}",status_code=status.HTTP_204_NO_CONTENT)
def updateUserCloud(user:userPydanticModel,userId:int,username: str = Depends(CurrentUserName)):  
    statsd_total.incr("total", 1)
    statsd_total.incr("Update User",1)

    if type(userId) != int:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=" Header Invalid")
    userExists=databaseObj.readUserData(userName = username)
    if(userExists == None):
       raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User doesnt exists")
    else:
        if userId==userExists.id: 
            ExistingUserName = databaseObj.readUserData(userName=user.username)
           
            if(ExistingUserName !=None and ExistingUserName.id != userId):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="User with same username already exists")
            else:           
                updatedUserHandling=databaseObj.UserDataUpdate(user_id = userId,userName=username,inputUser=user)
                if updatedUserHandling=='400_bad_request':
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="User have  rights to update only last_name, first_name and password fields",)
                else:
                            return {}
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden request")


###################create product###################
@app.post('/v1/product',status_code=status.HTTP_201_CREATED)
def createUserProducts(product:productPydanticModel, username: str = Depends(CurrentUserName)):
            statsd_total.incr("total", 1)
            statsd_total.incr("Post User",1)

            userExists = databaseObj.readUserData(userName = username)
            productExistscheck=databaseObj.readProductData(sku=product.sku)
            if (product.name == "default" or 
       product.description == "default" or 
       product.sku == "default" or 
       product.manufacturer == "default" or 
       product.quantity == None or product.quantity== "default"):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="please enter all required fields", )  
            if product.name == "" or product.description == "" or product.sku == "" or product.manufacturer == "" or product.quantity == "":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Required fields cant be empty", 
                )
            
            if(product.quantity != None):
                if(product.quantity.isalpha()):    
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Quantity can't be string", 
                    )   
                else:
                    if(int(product.quantity) < 0):
                        raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Quantity can't be less than 0", 
                    )


            if product.name == None or product.description == None or product.sku == None or product.manufacturer == None or product.quantity == None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Required fields are missing", 
                )
            
            

            if productExistscheck == None:
                newProductId= databaseObj.writeProductInfo(product,userExists.id)
                if newProductId == "400":
                    raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Quantity cannot be negative or greater than 100",                    
                )
                if newProductId == "400_id":
                    raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Please Enter valid user ID",                    
                )
                if(newProductId!= None):
                   raise HTTPException(
                    status_code=status.HTTP_201_CREATED,
                    detail= newProductId,
                   )
                else:
                    raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Client Error occurred"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Product already exists.",
                )


############Get product details##################
@app.get("/v1/product/{productId}",status_code=status.HTTP_200_OK)
def FetchProduct(productId:int,product:productPydanticModel):
    statsd_total.incr("total", 1)
    statsd_total.incr("Fetch Product",1)

    if not type(productId) is int:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid header")
    productExistscheck=databaseObj.readProductData(product_id= productId)
    if(productExistscheck == None):
       raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="product does not exists")    
    else:
        productExistscheck=databaseObj.readProductData(product_id=productId)      
        return {
                            "id": productExistscheck.id,
                            "name": productExistscheck.name,
                            "description": productExistscheck.description,
                            "sku": productExistscheck.sku,
                            "manufacturer":productExistscheck.manufacturer,
                            "quantity": productExistscheck.quantity,
                            "date_added": productExistscheck.date_added,
                            "date_last_updated": productExistscheck.date_last_updated,
                            "owner_user_id": productExistscheck.owner_user_id
            }
        
############Delete product details##################
@app.delete("/v1/product/{productId}",status_code=status.HTTP_204_NO_CONTENT)
def DeleteProduct(productId:int,product:productPydanticModel, username: str = Depends(CurrentUserName)):
    statsd_total.incr("total", 1)
    statsd_total.incr("Delete Product",1)

    if not type(productId) is int:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid header")
    userExists = databaseObj.readUserData(userName = username)
    productExistscheckcheck=databaseObj.readProductData(product_id= productId)
    if(productExistscheckcheck == None):
       raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="product not found")    
    else:
        if productExistscheckcheck.owner_user_id == userExists.id:
            productExistscheckcheck=databaseObj.deleteProductInfo(productId=productId)      
            if(productExistscheckcheck == 'Deleted_Successfully'):
                return "Product deleted successfully"
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden request")

###################Update Product###################
@app.put("/v1/product/{productId}",status_code=status.HTTP_204_NO_CONTENT)
def updateProduct(product:productPydanticModel,productId:int,username: str = Depends(CurrentUserName)):   
    statsd_total.incr("total", 1)
    statsd_total.incr("Update Product",1)

    if type(productId) != int:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="header Invalid")
      
    if product.name == "" or product.description == "" or product.sku == "" or product.manufacturer == "" or product.quantity == "" :
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Required fields cant be empty", 
                )
    if (product.name == "default" or 
       product.description == "default" or 
       product.sku == "default" or 
       product.manufacturer == "default" or 
       product.quantity == None or product.quantity== "default"):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="please enter all required fields", )  
    if(product.quantity != "default"):
        if(product.quantity.isalpha()):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Quantity should not be string")   
        elif(product.quantity.isnumeric()):
            if(int(product.quantity) < 0):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Quantity should be greater than", )
    
    
    userExists = databaseObj.readUserData(userName = username)
    productExistscheck=databaseObj.readProductData(product_id= productId)



    if(productExistscheck == None):
       raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    else:
        if productExistscheck.owner_user_id == userExists.id: 
            #Check if sku is updated
            if(product.sku != productExistscheck.sku):
                IsSkuExist = databaseObj.readProductData(sku=product.sku)               
                if IsSkuExist == None :
                    updatedProductData=databaseObj.productInfoUpdate(product_id = productId,inputProduct = product)
                    if updatedProductData=='400_bad_request':
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="User can update only name, description, sku, manufacturer, quantity fields",)
                        
                    if updatedProductData == "400":
                        raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Quantity cannot be negative or greater than 100",                    
                )
                        
                else:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Sku named Product already Exists")
            else:
                    updatedProductData=databaseObj.productInfoUpdate(product_id = productId,inputProduct = product)
                    if updatedProductData=='400_bad_request':
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Bad request",)
                   
                    if updatedProductData == "400":
                        raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Quantity cannot be negative or greater than 100",                    
                )

        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden request")

@app.patch("/v1/product/{productId}",status_code=status.HTTP_204_NO_CONTENT)
def patchProduct(product:productPydanticModel,productId:int,username: str = Depends(CurrentUserName)):   
    statsd_total.incr("total", 1)
    statsd_total.incr("Patch Product",1)

    if product.name == "" or product.description == "" or product.sku == "" or product.manufacturer == "" or product.quantity == "" :
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Required fields cant be empty", 
                )
    if type(productId) != int:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="header Invalid ")
    if(product.quantity != None):
        if(product.quantity.isalpha()):
            if product.quantity!= "default":  
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Quantity must be a number")   
        elif(product.quantity.isnumeric()):
            if(int(product.quantity) < 0):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Quantity can't be negative" )  
    userExists = databaseObj.readUserData(userName = username)
    productExistscheck=databaseObj.readProductData(product_id= productId)
    if(productExistscheck == None):
       raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    else:
        if productExistscheck.owner_user_id == userExists.id: 
            if(product.sku != productExistscheck.sku):
                IsSkuExist = databaseObj.readProductData(sku=product.sku)               
                if IsSkuExist == None :
                    updatedProductData=databaseObj.patchProductData(product_id = productId,inputProduct = product)
                    if updatedProductData=='400_bad_request':
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Bad Request",)
                    if updatedProductData == "400":
                        raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Quantity cannot be negative or greater than 100",                    
                )      
                else:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="SKU already Exists")
            else:
                    updatedProductData=databaseObj.patchProductData(product_id = productId,inputProduct = product)
                    if updatedProductData=='400_bad_request':
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Bad Request",)
                   
                    if updatedProductData == "400":
                        raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Quantity cannot be negative or greater than 100",                    
                )
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden request")


@app.get("/v1/product/{productId}/image",status_code=status.HTTP_200_OK)
def image_lists(productId:int,username: str = Depends(CurrentUserName)):
    statsd_total.incr("total", 1)
    statsd_total.incr("Get image",1)

    get_user_data=databaseObj.readUserData(userName=username)
    if(get_user_data == 'no_user'):
       raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    get_product_data=databaseObj.readProductData(product_id=productId)
    if get_product_data == 'no_product':
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    elif get_product_data == 'exception':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    else:
        if get_product_data.owner_user_id==get_user_data.id:
            retun_images= databaseObj.get_every_image_list(productId)
            return retun_images
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden request")
@app.post('/v1/product/{productId}/image',status_code=status.HTTP_201_CREATED)
def storing_images(productId:int,image: UploadFile=File(...),username: str = Depends(CurrentUserName)):
    statsd_total.incr("total", 1)
    statsd_total.incr("post image",1)

    get_user_data=databaseObj.readUserData(userName=username)
    if(get_user_data == 'no_user'):
       raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exists")
    get_product_data=databaseObj.readProductData(product_id=productId)
    if get_product_data == 'no_product':
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product does not exists")
    elif get_product_data == 'exception':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    else:
        if get_product_data.owner_user_id==get_user_data.id:
            with open(image.filename, "wb") as buffer:
                import shutil
                shutil.copyfileobj(image.file, buffer)
           
            file_path = os.path.join(os.getcwd(), image.filename)
            get_uploaded_image= databaseObj.image_data_store(productId,image,file_path)
            os.remove(file_path)
          
            if get_uploaded_image == 'exception':
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden request")
    return  get_uploaded_image  
 

@app.delete('/v1/product/{productId}/image/{imageId}',status_code=status.HTTP_204_NO_CONTENT)
def deleting_user_image(productId:int,imageId:int,username:str = Depends(CurrentUserName)):
    statsd_total.incr("total", 1)
    statsd_total.incr("Delete Image",1)

    get_user_data=databaseObj.readUserData(userName=username)
    if(get_user_data == 'no_user'):
       raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    get_product_data=databaseObj.readProductData(product_id=productId)
    if get_product_data == 'no_product':
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Could not find product")
    elif get_product_data == 'exception':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    else:
        if get_product_data.owner_user_id==get_user_data.id:
            retun_images= databaseObj.getting_image(productId,imageId)
            if retun_images == 'no_image':
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image does not exists")
            databaseObj.deleting_user_image(productId,imageId)
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden request")
        
@app.get("/v1/product/{productId}/image/{imageId}",status_code=status.HTTP_200_OK)
def image_lists(productId:int,imageId:int,username: str = Depends(CurrentUserName)):
    statsd_total.incr("total", 1)
    statsd_total.incr("get image",1)

    get_user_data=databaseObj.readUserData(userName=username)
    if(get_user_data == 'no_user'):
       raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User doesnt exists")
    get_product_data=databaseObj.readProductData(product_id=productId)
    if get_product_data == 'no_product':
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product doesnt exists")
    elif get_product_data == 'exception':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    else:
        if get_product_data.owner_user_id==get_user_data.id:
            retun_images= databaseObj.getting_image(productId,imageId)
            if retun_images == 'no_image':
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image does not exists")
            return retun_images
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden request")
     
if __name__ == "__main__":
    import uvicorn 
    uvicorn.run(app,host="0.0.0.0" ,port=3000)
