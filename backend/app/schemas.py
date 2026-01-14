from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ItemBase(BaseModel):
    slug: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    price_cents: int = Field(..., ge=0)
    currency: str = Field(default="MOP")
    in_stock: bool = True

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price_cents: Optional[int] = None
    currency: Optional[str] = None
    in_stock: Optional[bool] = None

class ItemResponse(ItemBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class PriceHistoryResponse(BaseModel):
    id: str
    item_id: str
    old_cents: Optional[int]
    new_cents: int
    changed_by: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class CSVImportResponse(BaseModel):
    success: bool
    imported_count: int
    errors: List[str] = []
