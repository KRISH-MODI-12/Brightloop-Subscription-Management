import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import engine, Base, SessionLocal
from app.api.v1 import (
    auth, users, customers, products, plans, quotations,
    subscriptions, invoices, payments, taxes, discounts,
    dashboard, notifications
)
from app.services.billing_service import run_recurring_billing_job

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()


def scheduled_billing_task():
    logger.info("Executing scheduled recurring billing and overdue check...")
    db = SessionLocal()
    try:
        results = run_recurring_billing_job(db)
        logger.info(f"Billing job completed: {results}")
    except Exception as e:
        logger.error(f"Error in background billing job: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure tables exist
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    # Setup background scheduler if available
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        # Run every 60 minutes, and once immediately at startup safely
        scheduler.add_job(scheduled_billing_task, 'interval', minutes=60, id='billing_job')
        scheduler.start()
        logger.info("APScheduler initialized for automated recurring billing.")
    except Exception as e:
        logger.warning(f"Background scheduler could not be initialized: {e}")

    yield

    # Shutdown
    try:
        if 'scheduler' in locals() and scheduler.running:
            scheduler.shutdown()
            logger.info("APScheduler stopped.")
    except Exception:
        pass


app = FastAPI(
    title="Brightloop Subscription Management System API",
    description="Full-featured RESTful API for subscriptions, invoices, automated billing, and revenue analytics.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers under /api/v1
api_v1_prefix = "/api/v1"
app.include_router(auth.router, prefix=api_v1_prefix)
app.include_router(users.router, prefix=api_v1_prefix)
app.include_router(customers.router, prefix=api_v1_prefix)
app.include_router(products.router, prefix=api_v1_prefix)
app.include_router(plans.router, prefix=api_v1_prefix)
app.include_router(quotations.router, prefix=api_v1_prefix)
app.include_router(subscriptions.router, prefix=api_v1_prefix)
app.include_router(invoices.router, prefix=api_v1_prefix)
app.include_router(payments.router, prefix=api_v1_prefix)
app.include_router(taxes.router, prefix=api_v1_prefix)
app.include_router(discounts.router, prefix=api_v1_prefix)
app.include_router(dashboard.router, prefix=api_v1_prefix)
app.include_router(notifications.router, prefix=api_v1_prefix)


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "status": "online",
        "documentation": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
