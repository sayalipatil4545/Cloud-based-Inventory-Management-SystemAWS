import pymysql
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy import Table,Column
from sqlalchemy.types import DateTime
from typing import Optional

##creating new users- BaseModel for POST Method
class userPydanticModel(BaseModel):
    id: Optional[int] = -1
    first_name: str
    last_name: str
    password: Optional[str] = ""
    username: Optional[str] = ""
    account_created: Optional[datetime] = '1900-01-00 00:00:00'
    account_updated: Optional[datetime] = '1900-01-00 00:00:00'