from __future__ import annotations
import concurrent.futures as cf
import hashlib, html, json, os, re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import feedparser
import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/sources.json"
OUTPUT = ROOT / "data/articles.json"
UA = "AI-Intel-Web/1.1 (personal research dashboard)"

CATEGORY_KEYWORDS = {
    "投资商业":["funding","raised","valuation","invest","investment","venture capital","ipo","acquisition","merger","revenue","earnings","stock","shares","融资","估值","投资","并购","收购","上市","财报","营收","利润","股价","商业化","资本"],
    "技术研究":["model","benchmark","paper","research","dataset","training","inference","architecture","open source","github","api","agent","multimodal","reasoning","robotics","chip","gpu","论文","模型","基准","数据集","训练","推理","架构","开源","智能体","多模态","机器人","芯片","算法","大模型"],
    "产品应用":["launch","release","product","feature","assistant","copilot","app","tool","platform","enterprise","发布","上线","产品","功能","助手","工具","平台","应用","落地"],
    "政策治理":["regulation","policy","law","act","safety","governance","copyright","privacy","antitrust","监管","政策","法律","法案","安全","治理","版权","隐私","反垄断","合规","标准"],
    "产业动态":["partnership","partner","industry","market","company","hiring","layoff","data center","cloud","合作","产业","市场","公司","招聘","裁员","数据中心","云计算","供应链","生态"]
}
CORE_TERMS=["artificial intelligence","generative ai","genai","large language model","llm","machine learning","deep learning","openai","anthropic","deepseek","gemini","claude","nvidia","人工智能","生成式ai","大模型","机器学习","深度学习","智能体","aigc"]

def clean(v):
    v = html.unescape(str(v or ""))
    v = re.sub(r"<[^>]+>"," ",v)
    return re.sub(r"\s+"," ",v).strip()

def dt(v):
    try:
        d=dateparser.parse(str(v))
        if not d.tzinfo:d=d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc)
    except Exception:return datetime.now(timezone.utc)

def canonical(url):
    try:
        p=urlsplit(url.strip())
        bad={"utm_source","utm_medium","utm_campaign","utm_term","utm_content","spm","ref","source","from","share"}
        q=[(k,v) for k,v in parse_qsl(p.query,keep_blank_values=True) if k.lower() not in bad]
        return urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path.rstrip("/"),urlencode(q),""))
    except Exception:return url

def load_previous_payload():
    try:
        return json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    except Exception:
        return {}

def previous_x_articles(previous):
    return [a for a in previous.get("articles", []) if a.get("source_type") == "X"]

def classify(a):
    text=f"{a.get('title','')} {a.get('summary','')} {a.get('content','')}".lower()
    scores={}
    tags=[]
    for cat,kws in CATEGORY_KEYWORDS.items():
        n=0
        for kw in kws:
            if kw.lower() in text:
                n+=1
                if len(tags)<10:tags.append(kw)
        scores[cat]=n
    a["category"]=max(scores,key=scores.get) if max(scores.values(),default=0)>0 else "产业动态"
    core=sum(1 for t in CORE_TERMS if t in text)
    age=max(0,(datetime.now(timezone.utc)-dt(a.get("published_at"))).total_seconds()/3600)
    fresh=max(0,25-int(age/4))
    engagement=min(15,int(a.get("engagement",0) or 0)//20)
    a["relevance_score"]=min(100,20+min(30,core*6)+min(25,sum(scores.values())*3)+fresh+engagement)
    a["tags"]=list(dict.fromkeys(tags))
    a["summary"]=clean(a.get("summary") or a.get("content") or a.get("title"))[:260]
    a.pop("content",None)
    return a

def rss_collect(cfg):
    out=[]
    for src in cfg.get("rss",[]):
        if not src.get("enabled",True):continue
        feed=feedparser.parse(src["url"])
        for e in feed.entries[:50]:
            title=clean(e.get("title")); url=e.get("link","")
            if not title or not url:continue
            content=clean(e.get("summary") or e.get("description") or "")
            if e.get("content"):content=clean(" ".join(x.get("value","") for x in e.get("content",[])))
            out.append({"title":title,"url":url,"source":src.get("name","RSS"),"source_type":src.get("source_type","RSS"),"published_at":dt(e.get("published") or e.get("updated")).isoformat(),"content":content})
    return out

def gdelt_collect(cfg):
    c=cfg.get("gdelt",{})
    if not c.get("enabled",True):return []
    r=requests.get("https://api.gdeltproject.org/api/v2/doc/doc",params={"query":c["query"],"mode":"ArtList","format":"json","maxrecords":c.get("max_items",80),"sort":"HybridRel","timespan":c.get("timespan","1d")},headers={"User-Agent":UA},timeout=35)
    r.raise_for_status()
    return [{"title":clean(x.get("title")),"url":x.get("url",""),"source":x.get("domain","GDELT"),"source_type":"全球新闻","published_at":dt(x.get("seendate")).isoformat(),"content":""} for x in r.json().get("articles",[]) if x.get("title") and x.get("url")]

def arxiv_collect(cfg):
    c=cfg.get("arxiv",{})
    if not c.get("enabled",True):return []
    u="https://export.arxiv.org/api/query?"+urlencode({"search_query":c["query"],"start":0,"max_results":c.get("max_items",40),"sortBy":"submittedDate","sortOrder":"descending"})
    f=feedparser.parse(u)
    return [{"title":clean(e.get("title")),"url":e.get("link",""),"source":"arXiv","source_type":"论文","published_at":dt(e.get("published")).isoformat(),"content":clean(e.get("summary"))} for e in f.entries if e.get("title") and e.get("link")]

def hn_collect(cfg):
    c=cfg.get("hackernews",{})
    if not c.get("enabled",True):return []
    ids=requests.get("https://hacker-news.firebaseio.com/v0/newstories.json",timeout=25).json()[:c.get("scan_items",200)]
    kws=[x.lower() for x in c.get("keywords",[])]
    def one(i):
        try:return requests.get(f"https://hacker-news.firebaseio.com/v0/item/{i}.json",timeout=12).json() or {}
        except:return {}
    out=[]
    with cf.ThreadPoolExecutor(max_workers=12) as ex:
        for x in ex.map(one,ids):
            title=x.get("title","")
            if not title or not any(k in f"{title} {x.get('text','')}".lower() for k in kws):continue
            out.append({"title":title,"url":x.get("url") or f"https://news.ycombinator.com/item?id={x.get('id')}","source":"Hacker News","source_type":"技术社区","published_at":datetime.fromtimestamp(x.get("time",0),tz=timezone.utc).isoformat(),"content":clean(x.get("text",""))})
    return out[:c.get("max_items",40)]

def x_collect(cfg, previous):
    c=cfg.get("x",{})
    token=os.getenv("X_BEARER_TOKEN","").strip()
    cached=previous_x_articles(previous)
    previous_status=previous.get("source_status",{}).get("X",{})
    if not c.get("enabled",True):
        return cached,{"enabled":False,"configured":bool(token),"state":"disabled","count":len(cached)}
    if not token:
        return cached,{"enabled":True,"configured":False,"state":"missing_token","count":len(cached),"message":"请在GitHub Secrets中配置 X_BEARER_TOKEN"}
    interval=max(30,int(c.get("fetch_interval_minutes",180)))
    last_fetch=previous_status.get("last_fetch_at")
    if last_fetch:
        elapsed=(datetime.now(timezone.utc)-dt(last_fetch)).total_seconds()/60
        if elapsed < interval:
            return cached,{"enabled":True,"configured":True,"state":"cached","count":len(cached),"last_fetch_at":last_fetch,"next_fetch_minutes":max(1,int(interval-elapsed))}
    params={"query":c["query"],"max_results":min(100,max(10,int(c.get("max_items",10)))),"tweet.fields":"created_at,author_id,lang,public_metrics,possibly_sensitive","expansions":"author_id","user.fields":"name,username,verified,public_metrics"}
    r=requests.get("https://api.x.com/2/tweets/search/recent",params=params,headers={"Authorization":f"Bearer {token}"},timeout=35)
    r.raise_for_status()
    payload=r.json(); users={u["id"]:u for u in payload.get("includes",{}).get("users",[])}
    out=[]
    for post in payload.get("data",[]):
        user=users.get(post.get("author_id"),{}); username=user.get("username",""); text=clean(post.get("text"))
        if not text:continue
        metrics=post.get("public_metrics",{})
        engagement=sum(int(metrics.get(k,0) or 0) for k in ("like_count","retweet_count","reply_count","quote_count"))
        out.append({"title":text[:180],"url":f"https://x.com/{username}/status/{post['id']}" if username else f"https://x.com/i/web/status/{post['id']}","source":f"X · @{username}" if username else "X","source_type":"X","published_at":dt(post.get("created_at")).isoformat(),"content":text,"engagement":engagement,"verified":bool(user.get("verified",False))})
    now=datetime.now(timezone.utc).isoformat()
    return out,{"enabled":True,"configured":True,"state":"fetched","count":len(out),"last_fetch_at":now,"interval_minutes":interval}

def wechat_collect(cfg):
    p=ROOT/cfg.get("wechat_urls_file","config/wechat_urls.txt")
    if not p.exists():return []
    out=[]
    for url in [x.strip() for x in p.read_text(encoding="utf-8").splitlines() if x.strip() and not x.lstrip().startswith("#")]:
        try:
            r=requests.get(url,headers={"User-Agent":"Mozilla/5.0 Chrome/124 Safari/537.36"},timeout=30)
            r.raise_for_status(); s=BeautifulSoup(r.text,"html.parser")
            m=s.select_one("meta[property='og:title']")
            title=(m.get("content") if m else "") or clean(s.select_one("#activity-name").get_text(" ",strip=True) if s.select_one("#activity-name") else "")
            author=clean(s.select_one("#js_name").get_text(" ",strip=True) if s.select_one("#js_name") else "")
            body=clean(s.select_one("#js_content").get_text(" ",strip=True) if s.select_one("#js_content") else "")
            if title:out.append({"title":title,"url":url,"source":author or "微信公众号","source_type":"微信公众号","published_at":datetime.now(timezone.utc).isoformat(),"content":body})
        except Exception:pass
    return out

def main():
    cfg=json.loads(CONFIG.read_text(encoding="utf-8")); previous=load_previous_payload()
    collectors=[("GDELT",gdelt_collect),("RSS",rss_collect),("arXiv",arxiv_collect),("Hacker News",hn_collect),("微信",wechat_collect)]
    all_items=[]; errors=[]; source_status={}
    with cf.ThreadPoolExecutor(max_workers=5) as ex:
        jobs={ex.submit(fn,cfg):name for name,fn in collectors}
        for fut,name in [(f,n) for f,n in jobs.items()]:
            try:
                items=fut.result(); all_items.extend(items); source_status[name]={"state":"fetched","count":len(items)}
            except Exception as e:
                errors.append(f"{name}: {e}"); source_status[name]={"state":"error","count":0,"message":str(e)}
    try:
        x_items,x_status=x_collect(cfg,previous); all_items.extend(x_items); source_status["X"]=x_status
    except Exception as e:
        cached=previous_x_articles(previous); all_items.extend(cached); errors.append(f"X: {e}")
        source_status["X"]={"enabled":True,"configured":True,"state":"error_cached","count":len(cached),"message":str(e),"last_fetch_at":previous.get("source_status",{}).get("X",{}).get("last_fetch_at")}
    seen=set(); out=[]
    for a in all_items:
        key=hashlib.sha256((re.sub(r"\W+","",a.get("title","").lower())+"|"+canonical(a.get("url",""))).encode()).hexdigest()
        if key in seen:continue
        seen.add(key); out.append(classify(a))
    out.sort(key=lambda x:(x.get("relevance_score",0),x.get("engagement",0),dt(x.get("published_at"))),reverse=True)
    payload={"updated_at":datetime.now(timezone.utc).isoformat(),"count":len(out),"errors":errors,"source_status":source_status,"articles":out[:500]}
    OUTPUT.parent.mkdir(parents=True,exist_ok=True); OUTPUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"count":len(out),"errors":errors,"x":source_status.get("X")},ensure_ascii=False))
if __name__=="__main__":main()
