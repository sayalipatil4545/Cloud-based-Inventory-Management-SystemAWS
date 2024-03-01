from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# ##base model for post - creating the product
# class Image_Pydantic(BaseModel):
#     image_id: Optional[int] = -1
#     product_id: int
#     file_name: Optional[str] = "default"
#     date_created: Optional[datetime] = '1900-01-00 00:00:00'
#     s3_bucket_path: Optional[str] = "default"

class Image_Pydantic(BaseModel):
    image_id: Optional[int] = -1
    product_id: Optional[int] =-1
    file_name: Optional[str] = None
    date_created: Optional[datetime] = '1900-01-00 00:00:00'
    s3_bucket_path: Optional[str] = None
    