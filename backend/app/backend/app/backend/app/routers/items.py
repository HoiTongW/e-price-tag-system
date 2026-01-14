from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import qrcode
import io

from app.database import get_db
from app.crud import ItemCRUD
from app import schemas

router = APIRouter()

@router.get("/items/{slug}", response_model=schemas.ItemResponse)
async def get_item(slug: str, db: Session = Depends(get_db)):
    item = ItemCRUD.get_by_slug(db, slug)
    if not item:
        raise HTTPException(status_code=404, detail="商品未找到")
    return item

@router.get("/qrcode/{slug}")
async def generate_qrcode(slug: str, db: Session = Depends(get_db)):
    item = ItemCRUD.get_by_slug(db, slug)
    if not item:
        raise HTTPException(status_code=404, detail="商品未找到")
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    import os
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    qr_data = f"{frontend_url}/item/{slug}"
    
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return StreamingResponse(
        img_byte_arr,
        media_type="image/png",
        headers={"Content-Disposition": f"inline; filename=qr_{slug}.png"}
    )
