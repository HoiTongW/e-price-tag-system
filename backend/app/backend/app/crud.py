from sqlalchemy.orm import Session
from app import models, schemas
import csv
import io

class ItemCRUD:
    @staticmethod
    def get_by_slug(db: Session, slug: str):
        return db.query(models.Item).filter(models.Item.slug == slug).first()
    
    @staticmethod
    def get_by_id(db: Session, item_id: str):
        return db.query(models.Item).filter(models.Item.id == item_id).first()
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100, search: str = None):
        query = db.query(models.Item)
        if search:
            query = query.filter(
                models.Item.name.contains(search) | 
                models.Item.slug.contains(search)
            )
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def create(db: Session, item: schemas.ItemCreate):
        db_item = models.Item(**item.dict())
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item
    
    @staticmethod
    def update(db: Session, item_id: str, item_update: schemas.ItemUpdate, changed_by: str = "admin"):
        db_item = ItemCRUD.get_by_id(db, item_id)
        if not db_item:
            return None
        
        update_data = item_update.dict(exclude_unset=True)
        
        if "price_cents" in update_data and update_data["price_cents"] != db_item.price_cents:
            price_history = models.PriceHistory(
                item_id=item_id,
                old_cents=db_item.price_cents,
                new_cents=update_data["price_cents"],
                changed_by=changed_by
            )
            db.add(price_history)
        
        for key, value in update_data.items():
            setattr(db_item, key, value)
        
        db.commit()
        db.refresh(db_item)
        return db_item
    
    @staticmethod
    def delete(db: Session, item_id: str):
        db_item = ItemCRUD.get_by_id(db, item_id)
        if db_item:
            db.delete(db_item)
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_price_history(db: Session, item_id: str):
        return db.query(models.PriceHistory).filter(
            models.PriceHistory.item_id == item_id
        ).order_by(models.PriceHistory.created_at.desc()).all()
    
    @staticmethod
    def import_csv(db: Session, csv_content: str, changed_by: str = "admin"):
        imported_count = 0
        errors = []
        
        try:
            csv_file = io.StringIO(csv_content)
            reader = csv.DictReader(csv_file)
            
            for i, row in enumerate(reader, start=1):
                try:
                    if not all(k in row for k in ["slug", "name", "price_cents"]):
                        errors.append(f"行 {i}: 缺少必要欄位")
                        continue
                    
                    try:
                        price_cents = int(float(row["price_cents"]) * 100)
                    except ValueError:
                        errors.append(f"行 {i}: 價格格式錯誤")
                        continue
                    
                    existing = ItemCRUD.get_by_slug(db, row["slug"])
                    if existing:
                        errors.append(f"行 {i}: slug '{row['slug']}' 已存在")
                        continue
                    
                    item_data = {
                        "slug": row["slug"],
                        "name": row["name"],
                        "description": row.get("description", ""),
                        "price_cents": price_cents,
                        "currency": row.get("currency", "MOP"),
                        "in_stock": row.get("in_stock", "true").lower() == "true"
                    }
                    
                    item = schemas.ItemCreate(**item_data)
                    ItemCRUD.create(db, item)
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"行 {i}: {str(e)}")
                    
        except Exception as e:
            errors.append(f"CSV 解析錯誤: {str(e)}")
        
        return imported_count, errors
    
    @staticmethod
    def export_csv(db: Session):
        items = db.query(models.Item).all()
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            "slug", "name", "description", "price", 
            "currency", "in_stock"
        ])
        
        writer.writeheader()
        for item in items:
            writer.writerow({
                "slug": item.slug,
                "name": item.name,
                "description": item.description or "",
                "price": item.price_cents / 100,
                "currency": item.currency,
                "in_stock": "true" if item.in_stock else "false"
            })
        
        return output.getvalue()
