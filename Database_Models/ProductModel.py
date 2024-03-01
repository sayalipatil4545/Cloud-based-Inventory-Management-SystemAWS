from typing import Optional
from pydantic import BaseModel
from datetime import datetime

##base model for post - creating the product
class productPydanticModel(BaseModel):
    id: Optional[int] = -1
    name: Optional[str] = "default"
    description: Optional[str] = "default"
    sku: Optional[str] = "default"
    manufacturer: Optional[str] = "default"
    quantity: Optional[str] = "default"  
    date_added: Optional[datetime] = '1900-01-00 00:00:00'
    date_last_updated: Optional[datetime] = '1900-01-00 00:00:00'
    owner_user_id: Optional[int] = -1