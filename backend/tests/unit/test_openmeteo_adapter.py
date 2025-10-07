from datetime import datetime

from app.adapters.openmeteo import OpenMeteoAdapter, OpenMeteoConfig


class DummyResponse:
    def __init__(self, json_data):
        self._json = json_data

    def raise_for_status(self):
        return None

    def json(self):
        return self._json


class DummyAsyncClient:
    def __init__(self, json_data):
        self._json = json_data

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, *args, **kwargs):
        return DummyResponse(self._json)


async def test_openmeteo_transforms():
    sample = {
        "hourly": {
            "time": ["2025-10-07T10:00:00Z", "2025-10-07T11:00:00Z"],
            "temperature_2m": [20.5, 21.0],
            "wind_speed_10m": [5.0, 6.0],
        }
    }

    adapter = OpenMeteoAdapter(
        OpenMeteoConfig(
            base_url="http://example.test",
            params={},
            field_mapping={
                "temperature_2m": "temperature",
                "wind_speed_10m": "wind_speed",
            },
        )
    )

    # Patch httpx.AsyncClient in the adapter module
    import app.adapters.openmeteo as adapter_module

    adapter_module.httpx = type(
        "M", (), {"AsyncClient": lambda *a, **k: DummyAsyncClient(sample)}
    )

    data = await adapter.fetch_data()
    assert len(data) == 2
    assert data[0]["temperature"] == 20.5
    assert data[1]["wind_speed"] == 6.0
    assert isinstance(data[0]["timestamp"], datetime)
