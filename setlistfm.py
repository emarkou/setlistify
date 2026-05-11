import os
import httpx
from typing import Any

BASE_URL = "https://api.setlist.fm/rest/1.0"
_HEADERS = {
    "Accept": "application/json",
}


def _headers() -> dict:
    key = os.environ.get("SETLISTFM_API_KEY", "")
    return {**_HEADERS, "x-api-key": key}


def search_artist(name: str) -> dict | None:
    """Return first matching artist dict, or None."""
    resp = httpx.get(
        f"{BASE_URL}/search/artists",
        headers=_headers(),
        params={"artistName": name, "sort": "relevance", "p": 1},
        timeout=10,
    )
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    data = resp.json()
    artists = data.get("artist", [])
    if not artists:
        return None
    return artists[0]


def search_artist_setlists(
    mbid: str,
    year: int | None = None,
    city: str | None = None,
    venue: str | None = None,
    limit: int = 5,
) -> list[dict]:
    """Fetch paginated setlists for artist MBID, filtered by optional params."""
    results: list[dict] = []
    page = 1
    while len(results) < limit:
        params: dict[str, Any] = {"p": page}
        if year:
            params["year"] = year
        if city:
            params["cityName"] = city
        if venue:
            params["venueName"] = venue
        resp = httpx.get(
            f"{BASE_URL}/artist/{mbid}/setlists",
            headers=_headers(),
            params=params,
            timeout=10,
        )
        if resp.status_code == 404:
            break
        resp.raise_for_status()
        data = resp.json()
        setlists = data.get("setlist", [])
        if not setlists:
            break
        results.extend(setlists)
        total = int(data.get("total", 0))
        items_per_page = int(data.get("itemsPerPage", 20))
        if page * items_per_page >= total:
            break
        page += 1
    return results[:limit]


def parse_setlist(raw: dict) -> dict:
    """Normalize raw setlist dict into structured form."""
    tracks: list[str] = []
    seen: set[str] = set()
    for s in raw.get("sets", {}).get("set", []):
        for song in s.get("song", []):
            name = song.get("name", "").strip()
            if name and name not in seen:
                tracks.append(name)
                seen.add(name)
    venue = raw.get("venue", {})
    city = venue.get("city", {})
    return {
        "date": raw.get("eventDate", ""),
        "venue": venue.get("name", ""),
        "city": city.get("name", ""),
        "country": city.get("country", {}).get("name", ""),
        "tracks": tracks,
        "url": raw.get("url", ""),
        "id": raw.get("id", ""),
    }
