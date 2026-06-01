"""FastAPI app entrypoint."""
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from reports.dashboard import get_dashboard_data
from tasks.nightly_export import export_to_s3

app = FastAPI()
scheduler = AsyncIOScheduler()


@app.get("/dashboard")
async def dashboard():
    return await get_dashboard_data()


@app.on_event("startup")
async def start_scheduler():
    # Run nightly export at 02:00 UTC every day
    scheduler.add_job(export_to_s3, "cron", hour=2, minute=0)
    scheduler.start()


@app.on_event("shutdown")
async def stop_scheduler():
    scheduler.shutdown()
