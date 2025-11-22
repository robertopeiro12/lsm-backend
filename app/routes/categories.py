from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import CategoryResponse, CategoryCreate, CategoryUpdate
from app.database import get_db_connection
from typing import List, Optional

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("/", response_model=List[CategoryResponse])
def get_categories(
    is_active: Optional[bool] = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """
    Obtener todas las categorías
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT c.*, 
                   (SELECT COUNT(*) FROM signs s WHERE s.category_id = c.id AND s.is_active = TRUE) as total_signs
            FROM categories c
            WHERE c.is_active = %s
            ORDER BY c.order_index ASC
            LIMIT %s OFFSET %s
        """
        
        cursor.execute(query, (is_active, limit, skip))
        categories = cursor.fetchall()
        
        cursor.close()
        db.close()
        
        return [CategoryResponse(**cat) for cat in categories]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int):
    """
    Obtener una categoría por ID
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT c.*, 
                   (SELECT COUNT(*) FROM signs s WHERE s.category_id = c.id AND s.is_active = TRUE) as total_signs
            FROM categories c
            WHERE c.id = %s
        """
        
        cursor.execute(query, (category_id,))
        category = cursor.fetchone()
        
        cursor.close()
        db.close()
        
        if not category:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
        
        return CategoryResponse(**category)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=CategoryResponse)
def create_category(category: CategoryCreate):
    """
    Crear una nueva categoría (solo admin)
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            INSERT INTO categories (name, description, icon_url, color, order_index)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        cursor.execute(query, (
            category.name,
            category.description,
            category.icon_url,
            category.color,
            category.order_index
        ))
        db.commit()
        
        category_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM categories WHERE id = %s", (category_id,))
        new_category = cursor.fetchone()
        new_category['total_signs'] = 0
        
        cursor.close()
        db.close()
        
        return CategoryResponse(**new_category)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(category_id: int, category: CategoryUpdate):
    """
    Actualizar una categoría (solo admin)
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Verificar que existe
        cursor.execute("SELECT * FROM categories WHERE id = %s", (category_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
        
        # Construir query de actualización
        updates = []
        values = []
        
        if category.name is not None:
            updates.append("name = %s")
            values.append(category.name)
        if category.description is not None:
            updates.append("description = %s")
            values.append(category.description)
        if category.icon_url is not None:
            updates.append("icon_url = %s")
            values.append(category.icon_url)
        if category.color is not None:
            updates.append("color = %s")
            values.append(category.color)
        if category.order_index is not None:
            updates.append("order_index = %s")
            values.append(category.order_index)
        if category.is_active is not None:
            updates.append("is_active = %s")
            values.append(category.is_active)
        
        if updates:
            values.append(category_id)
            query = f"UPDATE categories SET {', '.join(updates)} WHERE id = %s"
            cursor.execute(query, values)
            db.commit()
        
        cursor.execute("SELECT * FROM categories WHERE id = %s", (category_id,))
        updated_category = cursor.fetchone()
        updated_category['total_signs'] = 0
        
        cursor.close()
        db.close()
        
        return CategoryResponse(**updated_category)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{category_id}")
def delete_category(category_id: int):
    """
    Eliminar una categoría (solo admin)
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM categories WHERE id = %s", (category_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
        
        cursor.execute("DELETE FROM categories WHERE id = %s", (category_id,))
        db.commit()
        
        cursor.close()
        db.close()
        
        return {"message": "Categoría eliminada exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
