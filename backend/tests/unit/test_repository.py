from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.repository import DataRepository


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_timestamp_dedupe():
    db = make_session()
    repo = DataRepository(db)

    # create source
    source = repo.create_source("test_ts", "hourly")

    ts = datetime.now(tz=UTC)
    points = [
        {"timestamp": ts, "value": 1},
        {"timestamp": ts, "value": 2},
    ]

    # save first time -> one saved
    saved = repo.save_data_points(source.id, points, unique_key=None)
    assert saved == 1

    # save again -> zero saved (duplicate timestamp)
    saved2 = repo.save_data_points(source.id, points, unique_key=None)
    assert saved2 == 0


def test_unique_key_nested_and_payload_extraction():
    db = make_session()
    repo = DataRepository(db)

    source = repo.create_source("test_json_blob", "json")

    ts = datetime.now(tz=UTC)

    # Points where unique_key is nested under payload['id']
    points = [
        {"timestamp": ts, "payload": {"id": "a", "val": 1}},
        {"timestamp": ts, "payload": {"id": "b", "val": 2}},
        {"timestamp": ts, "payload": {"id": "a", "val": 3}},
    ]

    # unique_key set to 'payload.id' should allow a and b but skip duplicate a
    saved = repo.save_data_points(source.id, points, unique_key="payload.id")
    assert saved == 2


def test_unique_key_timestamp_string_fallback():
    db = make_session()
    repo = DataRepository(db)

    source = repo.create_source("test_created_at", "json")

    # Points without top-level timestamp, but with created_at string
    created = "2025-10-04T10:00:00Z"
    points = [
        {"created_at": created, "data": {"x": 1}},
        {"created_at": created, "data": {"x": 2}},
    ]

    # unique_key points to 'created_at' which is parsed into timestamp
    saved = repo.save_data_points(source.id, points, unique_key="created_at")
    assert saved == 1
