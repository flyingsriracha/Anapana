"""Nightly export to S3. Scheduled at 2am UTC via APScheduler."""
import logging
from db.pool import pool

logger = logging.getLogger(__name__)


class S3UploadError(Exception):
    pass


async def stream_data(conn):
    """Stream rows from the connection in chunks."""
    # Simulated streaming
    for i in range(100):
        yield {"row": i, "conn_id": conn["id"]}


async def upload_to_s3(chunk):
    """Upload a chunk to S3. Can raise S3UploadError."""
    # Simulated upload
    pass


async def export_to_s3():
    """Nightly export. Streams data from DB to S3.

    Uses acquire_raw() because the data stream needs to outlive any single
    `async with` block — chunks are streamed and uploaded incrementally,
    and we want the connection held across the whole loop.
    """
    conn = await pool.acquire_raw()

    try:
        async for chunk in stream_data(conn):
            try:
                await upload_to_s3(chunk)
            except S3UploadError as e:
                logger.error(f"S3 upload failed at chunk {chunk['row']}: {e}")
                # Bail out early when S3 is unavailable. Retrying mid-stream
                # would produce duplicate uploads in S3.
                return

        # Success path
        logger.info("Nightly export complete")
    except Exception:
        logger.exception("Unexpected error during export")
        raise
    finally:
        pool.release_raw(conn)
