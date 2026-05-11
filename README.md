# setlistify

> "Make me a Spotify playlist from Radiohead's last show" → done.

An MCP server that connects [setlist.fm](https://setlist.fm) and Spotify. Tell Claude which artist and show you want — it fetches the real setlist, matches every track on Spotify, and creates the playlist.

Works with **Claude Code** and **Claude Desktop**.

---

## Example

```
You:    Create a playlist from Phoebe Bridgers' most recent show.

Claude: Created "Phoebe Bridgers — Live Setlist (06-10-2023)"
        Setlist from Red Rocks Amphitheatre, Morrison — 06-10-2023.
        17/18 tracks matched.
        → https://open.spotify.com/playlist/...
```

```
You:    Which songs does The National always play live vs. their rarities?

Claude: Always played (last 10 shows): Bloodbuzz Ohio, Terrible Love, Mr. November
        Rarities (played once): Sorrow, Available, Green Gloves
        Never played live: 34 studio tracks
```

---

## What it does

- Fetches real setlists from setlist.fm for any artist
- Searches Spotify for each track with fuzzy matching for live variants
- Creates a Spotify playlist and returns the URL
- `mode="latest"` — most recent show
- `mode="best-of"` — aggregates last N shows, ranks by play frequency
- Diffs live setlists against full studio discography (always played / never played / rarities)

---

## Tools

### `get_setlists(artist, year?, city?, limit?)`
Browse recent setlists before creating a playlist.

### `create_playlist_from_setlist(artist, year?, venue?, city?, mode?)`
Create a Spotify playlist from a setlist. Returns playlist URL, matched/unmatched track counts.

### `diff_setlist_vs_discography(artist)`
Compare last 10 setlists against full Spotify discography.

---

## Installation

### Prerequisites

- Python 3.11+
- [setlist.fm API key](https://www.setlist.fm/settings/api) — free
- [Spotify Developer app](https://developer.spotify.com/dashboard) — free

### 1. Clone and install

```bash
git clone https://github.com/emarkou/setlistify.git
cd setlistify
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
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
2. Create an app → select **Web API**
3. Add `http://localhost:8888/callback` as a Redirect URI
4. Copy Client ID and Client Secret

### 3. Register with Claude Code

```bash
claude mcp add setlistify \
  /path/to/setlistify/.venv/bin/python \
  -- /path/to/setlistify/server.py
```

Or add to `~/.claude/mcp.json`:

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

On first use a browser window opens for Spotify authorisation. Log in and allow access. Token is cached locally in `.cache` and reused automatically.

If auth expires, delete `.cache` and retry.

---

## Test without Claude

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
├── requirements.txt
├── .env.example
└── LICENSE
```

---

## License

MIT
