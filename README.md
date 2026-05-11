# setlistify

A Python MCP server that connects [setlist.fm](https://setlist.fm) and Spotify to turn live concert setlists into Spotify playlists.

## What it does

- Fetches real setlists from setlist.fm for any artist
- Searches Spotify for each track with fuzzy matching for live variants
- Creates a Spotify playlist and returns the URL
- Supports "latest show" or "best-of" mode (aggregated by play frequency)
- Can diff an artist's live setlists against their full studio discography

## Tools

### `get_setlists(artist, year?, city?, limit?)`
Browse recent setlists before creating a playlist.

```
get_setlists("Radiohead", year=2023, limit=3)
```

### `create_playlist_from_setlist(artist, year?, venue?, city?, mode?)`
Create a Spotify playlist from a setlist.

- `mode="latest"` — most recent show (default)
- `mode="best-of"` — aggregate last N shows, ranked by play frequency

```
create_playlist_from_setlist("Phoebe Bridgers", mode="best-of")
create_playlist_from_setlist("The National", city="New York", mode="latest")
```

Returns: playlist URL, matched/unmatched track counts, source show details.

### `diff_setlist_vs_discography(artist)`
Analyse last 10 setlists vs full Spotify discography.

Returns:
- `always_played` — every show without fail
- `never_played_live` — studio tracks never performed
- `rarities` — played only once in last 10 shows

```
diff_setlist_vs_discography("Arcade Fire")
```

---

## Installation

### Prerequisites

- Python 3.11+
- A [setlist.fm API key](https://www.setlist.fm/settings/api) (free)
- A [Spotify Developer app](https://developer.spotify.com/dashboard) (free)

### 1. Clone and set up environment

```bash
git clone https://github.com/emarkou/setlistify.git
cd setlistify
python3.11 -m venv .venv
source .venv/bin/activate
pip install mcp spotipy httpx python-dotenv
```

### 2. Configure credentials

```bash
cp .env.example .env
```

Edit `.env`:

```
SETLISTFM_API_KEY=your_setlistfm_key
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
```

**setlist.fm:** Register at https://www.setlist.fm/settings/api, copy the API key.

**Spotify:**
1. Go to https://developer.spotify.com/dashboard
2. Create an app, select **Web API**
3. Add `http://localhost:8888/callback` as a Redirect URI
4. Copy Client ID and Client Secret

### 3. Register with Claude Code

Add to `~/.claude/mcp.json`:

```json
{
  "mcpServers": {
    "setlistify": {
      "command": "/path/to/setlistify/.venv/bin/python",
      "args": ["/path/to/setlistify/server.py"]
    }
  }
}
```

Or use the CLI:

```bash
claude mcp add setlistify \
  /path/to/setlistify/.venv/bin/python \
  -- /path/to/setlistify/server.py
```

### 4. Register with Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "setlistify": {
      "command": "/path/to/setlistify/.venv/bin/python",
      "args": ["/path/to/setlistify/server.py"],
      "env": {
        "SETLISTFM_API_KEY": "your_key",
        "SPOTIFY_CLIENT_ID": "your_client_id",
        "SPOTIFY_CLIENT_SECRET": "your_client_secret",
        "SPOTIFY_REDIRECT_URI": "http://localhost:8888/callback"
      }
    }
  }
}
```

### 5. First run — Spotify OAuth

On first use, a browser window opens for Spotify authorisation. Log in and allow access. The token is cached locally in `.cache` and reused automatically.

If auth expires, delete `.cache` and retry.

---

## Test with MCP Inspector

```bash
npx @modelcontextprotocol/inspector \
  /path/to/setlistify/.venv/bin/python \
  /path/to/setlistify/server.py
```

Opens a browser UI at `http://localhost:6274` to call tools interactively.

---

## Project structure

```
setlistify/
├── server.py       # MCP server and tool definitions
├── setlistfm.py    # setlist.fm API client
├── spotify.py      # Spotify/spotipy wrapper
├── matching.py     # Fuzzy track title matching
├── .env.example    # Credential template
└── README.md
```
