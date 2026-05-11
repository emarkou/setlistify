from __future__ import annotations

import os
from collections import Counter
from typing import Any

from dotenv import load_dotenv

load_dotenv()

from mcp.server.fastmcp import FastMCP

import setlistfm
import spotify
from matching import best_match

mcp = FastMCP("setlistify")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_artist(artist: str) -> dict:
    result = setlistfm.search_artist(artist)
    if result is None:
        raise ValueError(
            f"Artist '{artist}' not found on setlist.fm. "
            "Check spelling or try the full official name."
        )
    return result


def _find_spotify_track(title: str, artist_name: str) -> dict | None:
    track = spotify.search_track(title, artist_name)
    if track:
        return track
    # fuzzy: search by title only, then pick best name match
    import spotipy  # noqa: F401 — ensure client initialised
    sp = spotify._client()
    result = sp.search(q=title, type="track", limit=10)
    items = result.get("tracks", {}).get("items", [])
    if not items:
        return None
    return best_match(title, items)


# ---------------------------------------------------------------------------
# Tool: get_setlists
# ---------------------------------------------------------------------------

@mcp.tool()
def get_setlists(
    artist: str,
    year: int | None = None,
    city: str | None = None,
    limit: int = 5,
) -> list[dict]:
    """
    Return recent setlists for an artist as structured data.

    Args:
        artist: Artist name.
        year: Filter by year (optional).
        city: Filter by city name (optional).
        limit: Max number of setlists to return (default 5).
    """
    info = _resolve_artist(artist)
    mbid = info["mbid"]
    raw_setlists = setlistfm.search_artist_setlists(mbid, year=year, city=city, limit=limit)
    if not raw_setlists:
        return []
    return [setlistfm.parse_setlist(s) for s in raw_setlists]


# ---------------------------------------------------------------------------
# Tool: create_playlist_from_setlist
# ---------------------------------------------------------------------------

@mcp.tool()
def create_playlist_from_setlist(
    artist: str,
    year: int | None = None,
    venue: str | None = None,
    city: str | None = None,
    mode: str = "latest",
    n_setlists: int = 10,
) -> dict[str, Any]:
    """
    Create a Spotify playlist from a live setlist.

    Args:
        artist: Artist name.
        year: Filter by year (optional).
        venue: Filter by venue name (optional).
        city: Filter by city name (optional).
        mode: 'latest' uses the most recent setlist; 'best-of' aggregates
              the last n_setlists and ranks by play frequency.
        n_setlists: How many setlists to aggregate in best-of mode (default 10).

    Returns:
        Dict with 'playlist_url', 'matched', 'unmatched', 'description'.
    """
    info = _resolve_artist(artist)
    mbid = info["mbid"]
    artist_name: str = info.get("name", artist)

    fetch_limit = 1 if mode == "latest" else n_setlists
    raw_setlists = setlistfm.search_artist_setlists(
        mbid, year=year, city=city, venue=venue, limit=fetch_limit
    )
    if not raw_setlists:
        raise ValueError(f"No setlists found for '{artist_name}' with the given filters.")

    if mode == "latest":
        parsed = setlistfm.parse_setlist(raw_setlists[0])
        tracks_ordered = parsed["tracks"]
        playlist_name = f"{artist_name} — Live Setlist ({parsed['date']})"
        playlist_desc = (
            f"Setlist from {parsed['venue']}, {parsed['city']} — {parsed['date']}."
        )
        source_label = f"{parsed['venue']}, {parsed['city']}, {parsed['date']}"
    else:
        counter: Counter[str] = Counter()
        for raw in raw_setlists:
            p = setlistfm.parse_setlist(raw)
            for t in p["tracks"]:
                counter[t] += 1
        tracks_ordered = [t for t, _ in counter.most_common()]
        playlist_name = f"{artist_name} — Best Of Live (last {len(raw_setlists)} shows)"
        playlist_desc = (
            f"Most-played songs across {len(raw_setlists)} recent {artist_name} setlists."
        )
        source_label = f"aggregated {len(raw_setlists)} shows"

    # Match each track on Spotify
    track_uris: list[str] = []
    unmatched: list[str] = []
    for title in tracks_ordered:
        t = _find_spotify_track(title, artist_name)
        if t:
            track_uris.append(t["uri"])
        else:
            unmatched.append(title)

    matched_count = len(track_uris)
    total_count = len(tracks_ordered)
    full_desc = (
        f"{playlist_desc} {matched_count}/{total_count} tracks matched."
        + (f" Unmatched: {', '.join(unmatched[:5])}{'…' if len(unmatched) > 5 else ''}." if unmatched else "")
    )

    playlist = spotify.create_playlist(playlist_name, description=full_desc[:300])
    if track_uris:
        spotify.add_tracks_to_playlist(playlist["id"], track_uris)

    return {
        "playlist_url": playlist["external_urls"]["spotify"],
        "playlist_name": playlist_name,
        "matched": matched_count,
        "unmatched": len(unmatched),
        "unmatched_tracks": unmatched,
        "total": total_count,
        "source": source_label,
        "description": full_desc,
    }


# ---------------------------------------------------------------------------
# Tool: diff_setlist_vs_discography
# ---------------------------------------------------------------------------

@mcp.tool()
def diff_setlist_vs_discography(artist: str) -> dict[str, Any]:
    """
    Compare an artist's live setlists against their full Spotify discography.

    Returns songs they always play, songs they never play live, and rarities.

    Args:
        artist: Artist name.
    """
    info = _resolve_artist(artist)
    mbid = info["mbid"]
    artist_name: str = info.get("name", artist)

    # Collect live tracks from last 10 setlists
    raw_setlists = setlistfm.search_artist_setlists(mbid, limit=10)
    if not raw_setlists:
        raise ValueError(f"No setlists found for '{artist_name}'.")

    live_counter: Counter[str] = Counter()
    n_shows = len(raw_setlists)
    for raw in raw_setlists:
        p = setlistfm.parse_setlist(raw)
        for t in p["tracks"]:
            live_counter[t.lower()] += 1

    # Collect studio discography from Spotify
    albums = spotify.get_artist_albums(artist_name)
    seen_album_ids: set[str] = set()
    studio_tracks: set[str] = set()
    for album in albums:
        aid = album["id"]
        if aid in seen_album_ids:
            continue
        seen_album_ids.add(aid)
        for t in spotify.get_album_tracks(aid):
            studio_tracks.add(t["name"].lower())

    live_set = set(live_counter.keys())

    always_played = [t for t, count in live_counter.items() if count == n_shows]
    never_played = sorted(studio_tracks - live_set)
    rarities = [t for t, count in live_counter.items() if count == 1]

    return {
        "artist": artist_name,
        "shows_analysed": n_shows,
        "always_played": sorted(always_played),
        "never_played_live": never_played,
        "rarities": sorted(rarities),
        "studio_track_count": len(studio_tracks),
        "unique_live_songs": len(live_set),
    }


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
