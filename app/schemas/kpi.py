from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date


class SeasonalProduct(BaseModel):
    pd_id: int
    name: str
    type: str
    explanation: Optional[str] = None
    is_main: bool = False
    update_date: date
    model_config = ConfigDict(from_attributes=True)


class SeasonalProductList(BaseModel):
    products: List[SeasonalProduct]
    total: int


class SeasonalProductDetail(BaseModel):
    pd_id: int
    name: str
    type: str
    explanation: str
    is_main: bool
    update_date: date
    matched_customer_count: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


SeasonalProductListResponse = SeasonalProductList
SeasonalProductDetailResponse = SeasonalProductDetail

