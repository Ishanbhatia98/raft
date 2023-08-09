import asyncio
import logging

from sqlalchemy.orm import Session

from app.workers.celery import BaseDbTask, celery_app, loop


async def run_async_test_task(session: Session):
    # session is the db session from sqlalchemy
    logging.info("Entering test task (next message will appear in 5 seconds)")
    await asyncio.sleep(5)
    logging.info("Exiting test task")


@celery_app.task(
    bind=True,
    max_retries=3,
    acks_late=True,
    base=BaseDbTask,
    retry_jitter=True,
    retry_backoff=True,
    default_retry_delay=5,
    reject_on_worker_lost=True,
)
def run_test_task(self):
    try:
        # Example of async task running within celery
        loop.run_until_complete(run_async_test_task(self.session))
    except Exception as exc:
        logging.exception("exception while running task. retrying")
        raise self.retry(exc=exc)
