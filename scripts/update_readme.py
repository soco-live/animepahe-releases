import json, subprocess, sys, os, re, datetime, requests
REPO=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README=os.path.join(REPO,"README.md")
def get_latest():
    result=subprocess.run([sys.executable, os.path.join(REPO,"scripts/get_latest.py")], capture_output=True, text=True, timeout=30)
    if result.returncode!=0: raise RuntimeError(result.stderr or result.stdout)
    return json.loads(result.stdout)["latest"]
def fmt(items):
    rows=[]
    for it in items[:6]:
        cover=it.get("cover",""); title=it.get("title","").replace('"','&quot;')
        ep=f"Ep {it.get('episode')}" if it.get("episode") else ""
        score=f"{it['score']/10:.1f}★" if it.get("score") else ""
        # All links to our download anchor, not external
        rows.append(f'<td align="center"><a href="#download"><img src="{cover}" width="110" alt="{title}"><br><sub><strong>{title}</strong></sub><br><sub>{ep} {score}</sub></a></td>')
    html=['<table><tr>']
    for i, cell in enumerate(rows):
        html.append(cell)
        if (i+1)%3==0 and i!=len(rows)-1: html.append('</tr><tr>')
    html.append('</tr></table>')
    return "\n".join(html)
def post_fb(latest):
    fb_page=os.environ.get("FB_PAGE_ID"); fb_token=os.environ.get("FB_PAGE_ACCESS_TOKEN")
    if not fb_page or not fb_token: return
    try:
        lines=["🔥 Today on AnimePahe TV"]
        for it in latest[:5]:
            title=it.get("title",""); ep=f" Ep{it.get('episode')}" if it.get("episode") else ""
            lines.append(f"🎬 {title}{ep}")
        lines.append("\n📲 https://github.com/soco-live/animepahe-releases#download")
        message="\n".join(lines)
        last_file=os.path.join(REPO,".fb_last_post_id")
        if os.path.exists(last_file):
            try:
                with open(last_file) as f: pid=f.read().strip()
                if pid: requests.delete(f"https://graph.facebook.com/v25.0/{pid}", params={"access_token":fb_token}, timeout=15)
            except: pass
        cover=latest[0].get("cover") if latest else None
        if cover and cover.startswith("http"):
            url=f"https://graph.facebook.com/v25.0/{fb_page}/photos"; data={"url":cover,"message":message,"access_token":fb_token}
        else:
            url=f"https://graph.facebook.com/v25.0/{fb_page}/feed"; data={"message":message,"access_token":fb_token}
        r=requests.post(url, data=data, timeout=30); j=r.json()
        if "id" in j:
            with open(last_file,"w") as f: f.write(j["id"])
    except: pass
def update():
    latest=get_latest(); block=fmt(latest)
    with open(README,"r",encoding="utf-8") as f: txt=f.read()
    new=re.sub(r'<!-- LATEST_START -->.*?<!-- LATEST_END -->', f'<!-- LATEST_START -->\n{block}\n<!-- LATEST_END -->', txt, flags=re.DOTALL)
    if new!=txt:
        with open(README,"w",encoding="utf-8") as f: f.write(new)
        post_fb(latest)
    else:
        post_fb(latest)
if __name__=="__main__": update()
