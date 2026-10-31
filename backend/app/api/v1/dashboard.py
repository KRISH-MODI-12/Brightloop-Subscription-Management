from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.models.customer import Customer
from app.core.deps import get_current_user
from app.schemas.dashboard import DashboardAnalyticsResponse
from app.services.analytics_service import get_dashboard_analytics

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Analytics"])


@router.get("/analytics", response_model=DashboardAnalyticsResponse)
def get_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cust_id = None
    if current_user.role == UserRole.CUSTOMER:
        cust = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if cust:
            cust_id = cust.id

    return get_dashboard_analytics(db, customer_id=cust_id)
