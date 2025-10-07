"""Scheduler for fetching data from sources."""

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.adapters import DataSourceAdapter
from app.adapters.factory import create_adapter
from app.config import DATA_SOURCES_CONFIG
from app.database import SessionLocal
from app.repository import DataRepository

logger = logging.getLogger(__name__)


class DataFetchScheduler:
    """
    Generic scheduler for fetching data from multiple sources.

    Works with any adapter without knowing its internals.
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.adapters: dict[str, DataSourceAdapter] = {}

    async def fetch_and_store(self, adapter: DataSourceAdapter) -> None:
        """
        Fetch data from an adapter and store it in the database.

        Args:
            adapter: The data source adapter to fetch from
        """
        source_name = adapter.get_source_name()

        try:
            logger.info(f"Fetching data from {source_name}...")

            # Fetch data from the source
            data_points = await adapter.fetch_data()

            if not data_points:
                logger.warning(f"No data points received from {source_name}")
                return

            # Store in database
            db = SessionLocal()
            try:
                repo = DataRepository(db)

                # Extract metadata from adapter config
                config = getattr(adapter, "config", {})
                metadata = {}
                # Copy simple metadata fields
                if "location" in config:
                    metadata["location"] = config["location"]
                if "location_coords" in config:
                    metadata["location_coords"] = config["location_coords"]
                # Per-field metadata (units, formatting, aggregates to compute)
                # Adapter configs may provide a `fields` map, store it as-is
                if "fields" in config and isinstance(config["fields"], dict):
                    metadata["fields"] = config["fields"]

                # Get or create source
                source = repo.get_or_create_source(
                    name=source_name,
                    type=adapter.get_data_type(),
                    description=adapter.get_description(),
                    metadata=metadata if metadata else None,
                )

                # Save data points (support optional per-source unique_key to dedupe)
                unique_key = (
                    config.get("unique_key") if isinstance(config, dict) else None
                )
                count = repo.save_data_points(
                    source.id, data_points, unique_key=unique_key
                )
                logger.info(
                    f"Saved {count} data points from {source_name} "
                    f"(source_id: {source.id})"
                )

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error fetching data from {source_name}: {e}", exc_info=True)

    def register_adapter(
        self, adapter: DataSourceAdapter, interval_minutes: int
    ) -> None:
        """
        Register an adapter to be called periodically.

        Args:
            adapter: The data source adapter
            interval_minutes: How often to fetch data (in minutes)
        """
        source_name = adapter.get_source_name()
        self.adapters[source_name] = adapter

        # Add job to scheduler
        self.scheduler.add_job(
            self.fetch_and_store,
            trigger=IntervalTrigger(minutes=interval_minutes),
            args=[adapter],
            id=f"fetch_{source_name}",
            name=f"Fetch data from {source_name}",
            replace_existing=True,
            next_run_time=None,
        )

        logger.info(
            f"Registered {source_name} to fetch every {interval_minutes} minutes"
        )

    def start(self) -> None:
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")

    def shutdown(self) -> None:
        """Shutdown the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler shutdown")

    async def fetch_all_now(self) -> None:
        """Immediately fetch data from all registered adapters."""
        tasks = []
        for adapter in self.adapters.values():
            tasks.append(self.fetch_and_store(adapter))

        await asyncio.gather(*tasks)


# Global scheduler instance
_scheduler: DataFetchScheduler | None = None


def get_scheduler() -> DataFetchScheduler:
    """Get the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = DataFetchScheduler()
    return _scheduler


def initialize_scheduler() -> DataFetchScheduler:
    """
    Initialize scheduler with all configured data sources.

    This is called on application startup.
    """
    scheduler = get_scheduler()

    # Register all configured sources
    for source_config in DATA_SOURCES_CONFIG:
        if not source_config.get("enabled", True):
            logger.info(f"Skipping disabled source: {source_config['name']}")
            continue

        try:
            # Create adapter from config
            adapter = create_adapter(
                source_config["adapter_class"], source_config["config"]
            )

            # Register with scheduler
            interval = source_config.get(
                "fetch_interval_minutes",
                60,  # default to 60 minutes
            )
            scheduler.register_adapter(adapter, interval)

        except Exception as e:
            logger.error(
                f"Failed to register source {source_config['name']}: {e}", exc_info=True
            )

    return scheduler
