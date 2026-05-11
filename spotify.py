import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth

SCOPES = "playlist-modify-public playlist-modify-private user-library-read"

_sp: spotipy.Spotify | None = None


def _client() -> spotipy.Spotify:
    global _sp
    if _sp is None:
        auth = SpotifyOAuth(
            client_id=os.environ["SPOTIFY_CLIENT_ID"],
            client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
            redirect_uri=os.environ.get("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback"),
            scope=SCOPES,
            open_browser=True,
        )
        _sp = spotipy.Spotify(auth_manager=auth)
    return _sp


def current_user_id() -> str:
    return _client().current_user()["id"]


def search_track(title: str, artist: str) -> dict | None:
    """Search Spotify for a track. Returns track dict or None."""
    sp = _client()
    query = f"track:{title} artist:{artist}"
    result = sp.search(q=query, type="track", limit=5)
    items = result.get("tracks", {}).get("items", [])
    if items:
        return items[0]
    # fallback: looser search
    result = sp.search(q=f"{title} {artist}", type="track", limit=5)
    items = result.get("tracks", {}).get("items", [])
    return items[0] if items else None


def get_artist_albums(artist_name: str) -> list[dict]:
    sp = _client()
    results = sp.search(q=f"artist:{artist_name}", type="artist", limit=1)
    artists = results.get("artists", {}).get("items", [])
    if not artists:
        return []
    artist_id = artists[0]["id"]
    albums: list[dict] = []
    offset = 0
    while True:
        batch = sp.artist_albums(artist_id, album_type="album,single", limit=50, offset=offset)
        items = batch.get("items", [])
        albums.extend(items)
        if len(items) < 50:
            break
        offset += 50
    return albums


def get_album_tracks(album_id: str) -> list[dict]:
    sp = _client()
    tracks: list[dict] = []
    offset = 0
    while True:
        batch = sp.album_tracks(album_id, limit=50, offset=offset)
        items = batch.get("items", [])
        tracks.extend(items)
        if len(items) < 50:
            break
        offset += 50
    return tracks


def create_playlist(name: str, description: str, public: bool = True) -> dict:
    sp = _client()
    return sp._post("me/playlists", payload={"name": name, "public": public, "description": description})


def add_tracks_to_playlist(playlist_id: str, track_uris: list[str]) -> None:
    sp = _client()
    for i in range(0, len(track_uris), 100):
        sp.playlist_add_items(playlist_id, track_uris[i:i+100])
