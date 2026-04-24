from myapp.models import Product
from sqlalchemy import select
from sqlalchemy.orm import Session


def search_products(session: Session, term: str):
    stmt = select(Product).where(Product.name.ilike(f"%{term}%"))
    return session.scalars(stmt).all()
