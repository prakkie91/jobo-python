"""Sub-client for the Locations/Geocoding endpoints."""

from __future__ import annotations

import httpx

from jobo_enterprise._transport import arequest, request
from jobo_enterprise.models import GeocodeResultItem


class LocationsClient:
    """Synchronous sub-client for the Locations/Geocoding endpoints.

    Access via ``client.locations``.
    """

    def __init__(self, http: httpx.Client) -> None:
        self._client = http

    def geocode(self, location: str) -> GeocodeResultItem:
        """Geocode a location string into structured locations with coordinates.

        Args:
            location: The location string to geocode (e.g., "San Francisco, CA" or "London, UK").

        Returns:
            A :class:`GeocodeResultItem` with resolved locations.
        """
        params = {"location": location}
        payload = request(self._client, "GET", "/api/locations/geocode", params=params)
        return GeocodeResultItem.model_validate(payload)


class AsyncLocationsClient:
    """Asynchronous sub-client for the Locations/Geocoding endpoints.

    Access via ``client.locations``.
    """

    def __init__(self, http: httpx.AsyncClient) -> None:
        self._client = http

    async def geocode(self, location: str) -> GeocodeResultItem:
        """Geocode a location string into structured locations with coordinates.

        Args:
            location: The location string to geocode (e.g., "San Francisco, CA" or "London, UK").

        Returns:
            A :class:`GeocodeResultItem` with resolved locations.
        """
        params = {"location": location}
        payload = await arequest(self._client, "GET", "/api/locations/geocode", params=params)
        return GeocodeResultItem.model_validate(payload)
