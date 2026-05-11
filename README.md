# setlistify

MCP server — connects setlist.fm + Spotify to build playlists from live show setlists.

## Tools

| Tool | What it does |
|------|-------------|
| `get_setlists(artist, year?, city?, limit?)` | Browse recent setlists before committing |
| `create_playlist_from_setlist(artist, year?, venue?, city?, mode?)` | Build a Spotify playlist from a setlist |
| `diff_setlist_vs_discography(artist)` | Find always-played, never-played, and rarity tracks |

### `create_playlist_from_setlist` modes
- `mode="latest"` — most recent show  
- `mode="best-of"` — aggregate last N shows, rank by play frequency

## Setup

### 1. Clone & install

```bash
cd ~/Desktop/setlistify
python -m venv .venv
source .venv/bin/activate
pip install mcp spotipy httpx python-dotenv
```

### 2. Get API keys

**setlist.fm**  
Create a free account → https://www.setlist.fm/settings/api → copy API key.

**Spotify**  
1. Go to https://developer.spotify.com/dashboard  
2. Create an app, set Redirect URI to `http://localhost:8888/callback`  
3. Copy Client ID and Client Secret  

### 3. Configure .env

```bash
cp .env.example .env
```

Edit `.env`:

```
SETLISTFM_API_KEY=your_key_here
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
```

### 4. First run (Spotify OAuth)

```bash
python server.py
```

A browser window opens for Spotify login. Authorize once; token is cached locally.

---

## Register with Claude Code

Add to `~/.claude/mcp.json` (or `claude_desktop_config.json` for Claude Desktop):

```json
{
  "mcpServers": {
    "setlistify": {
      "command": "/Users/YOUR_USERNAME/Desktop/setlistify/.venv/bin/python",
      "args": ["/Users/YOUR_USERNAME/Desktop/setlistify/server.py"],
      "env": {
        "SETLISTFM_API_KEY": "your_key_here",
        "SPOTIFY_CLIENT_ID": "your_client_id",
        "SPOTIFY_CLIENT_SECRET": "your_client_secret",
        "SPOTIFY_REDIRECT_URI": "http://localhost:8888/callback"
      }
    }
  }
}
```

> **Tip:** replace `YOUR_USERNAME` with your macOS username (`whoami`).  
> If you use `.env` instead of inline env vars, remove the `"env"` block and ensure `.env` is in the same directory.

### Claude Desktop path

`~/Library/Application Support/Claude/claude_desktop_config.json`

---

## Usage examples

```
Get the last 3 setlists for Radiohead in 2023.

Build a Spotify playlist from Phoebe Bridgers' most recent show.

Make a best-of playlist from Taylor Swift's last 10 shows.

Which songs does The National always play vs. rarities?
```

---

## Project structure

```
setlistify/
├── server.py       # MCP server + all three tools
├── setlistfm.py    # setlist.fm HTTP client
├── spotify.py      # spotipy wrapper (OAuth + playlist ops)
├── matching.py     # fuzzy track title matching
├── .env.example
└── README.md
```

## Error handling

- **Artist not found** → message with spelling hint  
- **Track not found on Spotify** → skipped, counted in playlist description  
- **Spotify auth expired** → delete `.cache` file in project root, re-run server  
