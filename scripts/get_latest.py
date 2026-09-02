import httpx, json, sys
# Try AnimePahe first (will be 403 behind CF), then AniList fallback — user requested try -> fallback
QUERY = """
query { Page(perPage: 6) { media(type: ANIME, status: RELEASING, sort: POPULARITY_DESC) { title { romaji english } coverImage { large } averageScore episodes format seasonYear } } }
"""
def fetch_animepahe():
    try:
        with httpx.Client(timeout=12, follow_redirects=True, headers={"User-Agent":"Mozilla/5.0", "Referer":"https://animepahe.com/"}) as c:
            r = c.get("https://animepahe.com/api", params={"m":"airing","page":"1"})
            if r.status_code == 200 and r.headers.get("content-type","").startswith("application/json"):
                j = r.json()
                out=[]
                for i in j.get("data", [])[:6]:
                    out.append({"title": i.get("anime_title",""), "cover": i.get("snapshot",""), "score": None, "episodes": i.get("episode"), "format":"TV"})
                if out:
                    return out
    except Exception as e:
        print(f"animepahe fetch failed {e}", file=sys.stderr)
    return None

def fetch_anilist():
    with httpx.Client(timeout=15) as c:
        r = c.post("https://graphql.anilist.co", json={"query": QUERY}, headers={"Content-Type":"application/json"})
        r.raise_for_status()
        data = r.json()["data"]["Page"]["media"]
        out=[]
        for m in data:
            title = m["title"]["english"] or m["title"]["romaji"]
            out.append({"title": title, "cover": m["coverImage"]["large"], "score": m.get("averageScore"), "episodes": m.get("episodes"), "format": m.get("format")})
        return out

def get_latest():
    ap = fetch_animepahe()
    if ap:
        return ap
    return fetch_anilist()

if __name__ == "__main__":
    print(json.dumps({"latest": get_latest()}, indent=2))
