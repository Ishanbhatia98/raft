from alembic.runtime.migration import MigrationContext
from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from sqlalchemy import create_engine

from app.database import db_instance
from app.workers.celery import celery_app
from app.workers.tasks import run_test_task
from router import router


async def root():
    return {"Hello": "World"}


# Health checks
def get_alembic_version():
    db_url = db_instance.get_database_url()
    engine = create_engine(db_url)
    conn = engine.connect()
    context = MigrationContext.configure(conn)
    return context.get_current_revision()


def celery_healthcheck():
    """Check if celery workers are alive with ping"""
    if celery_response := celery_app.control.ping(timeout=0.5):
        return celery_response
    else:
        return "No celery tasks currently active."


async def celery_send_test_task():
    """Celery task test example
    Check worker_1 logs for info messages to see if task was successfully entered and exited.
    """
    run_test_task.delay()
    return "Check worker_1 logs."


async def healthcheck():
    """Basic healthcheck endpoint.
    Connects to DB for alembic version string and pings Celery worker(s) for 'pong' alive response.
    """
    alembic_revision = get_alembic_version()
    celery_response = celery_healthcheck()

    return {
        "alembic_version": alembic_revision,
        "celery_response": celery_response,
    }


routes = [
    APIRoute("/", endpoint=root, methods=["GET"]),
    APIRoute("/health", endpoint=healthcheck, methods=["GET"]),
    APIRoute("/test-task", endpoint=celery_send_test_task, methods=["GET"]),
]

middleware = Middleware(CORSMiddleware)

app = FastAPI(routes=routes, middleware=[middleware])

app.include_router(router)
