import httpx, json, sys, datetime
def fetch_today():
    now = datetime.datetime.now(datetime.timezone.utc)
    start = datetime.datetime(now.year, now.month, now.day, tzinfo=datetime.timezone.utc)
    end = start + datetime.timedelta(days=1)
    start_ts = int(start.timestamp()); end_ts = int(end.timestamp())
    QUERY = """
    query ($page: Int, $perPage: Int, $airingAt_greater: Int, $airingAt_lesser: Int) {
      Page(page: $page, perPage: $perPage) {
        airingSchedules(airingAt_greater: $airingAt_greater, airingAt_lesser: $airingAt_lesser, sort: TIME) {
          airingAt episode media { title { romaji english } coverImage { large } averageScore }
        }
      }
    }
    """
    try:
        with httpx.Client(timeout=15) as c:
            r = c.post("https://graphql.anilist.co", json={"query": QUERY, "variables": {"page":1, "perPage":6, "airingAt_greater": start_ts, "airingAt_lesser": end_ts}}, headers={"Content-Type":"application/json"})
            r.raise_for_status()
            data = r.json()["data"]["Page"]["airingSchedules"]
            if data:
                out=[]
                for s in data:
                    m=s["media"]; title=m["title"]["english"] or m["title"]["romaji"]
                    out.append({"title": title, "cover": m["coverImage"]["large"], "score": m.get("averageScore"), "episode": s.get("episode")})
                return out
    except Exception as e:
        print(f"today fetch failed {e}", file=sys.stderr)
    return None

def fetch_popular():
    Q="""query { Page(perPage: 6) { media(type: ANIME, status: RELEASING, sort: POPULARITY_DESC) { title { romaji english } coverImage { large } averageScore } } }"""
    with httpx.Client(timeout=15) as c:
        r=c.post("https://graphql.anilist.co", json={"query": Q}, headers={"Content-Type":"application/json"})
        r.raise_for_status()
        data=r.json()["data"]["Page"]["media"]
        return [{"title": (m["title"]["english"] or m["title"]["romaji"]), "cover": m["coverImage"]["large"], "score": m.get("averageScore"), "episode": None} for m in data]

def get_latest():
    today = fetch_today()
    if today: return today
    return fetch_popular()

if __name__=="__main__":
    print(json.dumps({"latest": get_latest()}, indent=2))
