from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models.product import Product, ProductVariant, ProductType, ProductStatus
from app.models.user import User, UserRole
from app.core.deps import get_current_user, get_admin_user, get_staff_or_admin
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse,
    ProductVariantCreate, ProductVariantResponse
)
from app.services.audit_service import log_action

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=List[ProductResponse])
def list_products(
    search: Optional[str] = None,
    product_type: Optional[ProductType] = None,
    product_status: Optional[ProductStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(Product).filter(Product.is_deleted == False)

    if search:
        query = query.filter(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%")
            )
        )
    if product_type:
        query = query.filter(Product.product_type == product_type)
    if product_status:
        query = query.filter(Product.status == product_status)

    return query.offset(skip).limit(limit).all()


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    prod_in: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    product = Product(
        name=prod_in.name,
        product_type=prod_in.product_type,
        sales_price=prod_in.sales_price,
        cost_price=prod_in.cost_price,
        description=prod_in.description,
        status=prod_in.status
    )
    db.add(product)
    db.flush()

    if prod_in.variants:
        for v in prod_in.variants:
            variant = ProductVariant(
                product_id=product.id,
                variant_name=v.variant_name,
                additional_price=v.additional_price,
                description=v.description,
                is_active=v.is_active
            )
            db.add(variant)

    db.commit()
    db.refresh(product)

    log_action(
        db=db,
        action="PRODUCT_CREATED",
        entity_type="product",
        entity_id=product.id,
        user_id=current_user.id,
        details=f"Product '{product.name}' created with base price ₹{product.sales_price}"
    )

    return product


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id, Product.is_deleted == False).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    prod_in: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    product = db.query(Product).filter(Product.id == product_id, Product.is_deleted == False).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    for field, val in prod_in.model_dump(exclude_unset=True).items():
        setattr(product, field, val)

    db.commit()
    db.refresh(product)

    log_action(
        db=db,
        action="PRODUCT_UPDATED",
        entity_type="product",
        entity_id=product.id,
        user_id=current_user.id,
        details=f"Product '{product.name}' updated"
    )

    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    product = db.query(Product).filter(Product.id == product_id, Product.is_deleted == False).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    # Soft delete
    product.is_deleted = True
    product.status = ProductStatus.ARCHIVED
    db.commit()

    log_action(
        db=db,
        action="PRODUCT_DELETED",
        entity_type="product",
        entity_id=product.id,
        user_id=current_user.id,
        details=f"Product '{product.name}' archived/soft-deleted"
    )
    return None


@router.post("/{product_id}/variants", response_model=ProductVariantResponse, status_code=status.HTTP_201_CREATED)
def add_product_variant(
    product_id: int,
    v_in: ProductVariantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    product = db.query(Product).filter(Product.id == product_id, Product.is_deleted == False).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    variant = ProductVariant(
        product_id=product.id,
        variant_name=v_in.variant_name,
        additional_price=v_in.additional_price,
        description=v_in.description,
        is_active=v_in.is_active
    )
    db.add(variant)
    db.commit()
    db.refresh(variant)

    log_action(
        db=db,
        action="VARIANT_ADDED",
        entity_type="product_variant",
        entity_id=variant.id,
        user_id=current_user.id,
        details=f"Variant '{variant.variant_name}' (+₹{variant.additional_price}) added to product {product.name}"
    )

    return variant
