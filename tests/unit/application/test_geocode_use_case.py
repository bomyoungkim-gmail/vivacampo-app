import asyncio

from app.application.dtos.geocoding import GeocodeCommand
from app.application.use_cases.geocoding import GeocodeUseCase


class _StubGeocodeProvider:
    async def geocode(self, query, limit=5):
        return [{"display_name": query, "lat": "0", "lon": "0"}]


def test_geocode_use_case():
    use_case = GeocodeUseCase(_StubGeocodeProvider())

    async def run():
        return await use_case.execute(GeocodeCommand(query="test"))

    result = asyncio.run(run())
    assert result[0]["display_name"] == "test"
