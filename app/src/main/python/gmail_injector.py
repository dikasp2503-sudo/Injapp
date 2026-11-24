import asyncio, random, string, json, logging
from pathlib import Path
import httpx
from faker import Faker

log = logging.getLogger("inj")
fake = Faker()
UA = ("Mozilla/5.0 (Linux; Android 13; Pixel 7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0.0.0 Mobile Safari/537.36")

def load_proxies(path):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"proxy file gak ada: {path}")
    return [ln.strip() for ln in p.read_text().splitlines() if ln.strip()]

def gen_identity():
    f, l = fake.first_name(), fake.last_name()
    return {
        "first": f, "last": l,
        "username": f"{f.lower()}{l.lower()}{random.randint(100,9999)}",
        "password": "".join(random.choices(
            string.ascii_letters + string.digits + "!@#$", k=14)),
    }

async def attempt(client, proxy, endpoint, ident):
    hdr = {
        "User-Agent": UA,
        "Accept-Language": "id-ID,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Origin": "https://accounts.google.com",
    }
    try:
        r = await client.post(endpoint, json=ident, headers=hdr, timeout=25.0,
                              proxies={"http://": proxy, "https://": proxy})
    except Exception as e:
        return {"status": "NET_ERR", "err": str(e), "ident": ident}
    b = r.text.lower()
    if r.status_code == 200 and "verification" not in b and "captcha" not in b:
        return {"status": "OK", "ident": ident}
    if "captcha" in b:
        return {"status": "CAPTCHA", "ident": ident}
    if "verification" in b or "verify" in b:
        return {"status": "VERIF_REQUIRED", "ident": ident}
    return {"status": f"HTTP_{r.status_code}", "ident": ident}

async def _run(proxies, endpoint, count):
    sem = asyncio.Semaphore(6)
    results = []
    async with httpx.AsyncClient(http2=True, follow_redirects=True) as client:
        async def w(p):
            async with sem:
                ident = gen_identity()
                res = None
                for _ in range(3):
                    res = await attempt(client, p, endpoint, ident)
                    log.info("proxy=%s status=%s", p, res["status"])
                    if res["status"] in ("OK", "CAPTCHA", "VERIF_REQUIRED"):
                        results.append(res); return
                    await asyncio.sleep(random.uniform(1.2, 3.5))
                if res: results.append(res)
        await asyncio.gather(*(w(p) for p in proxies[:max(count, 1)]))
    return results

def android_run(proxy_path, endpoint, count):
    try:
        proxies = load_proxies(proxy_path)
        out = asyncio.run(_run(proxies, endpoint, count))
        ok = sum(1 for r in out if r["status"] == "OK")
        return f"selesai: {ok}/{len(out)} OK\n\n" + json.dumps(out, indent=2)[:4000]
    except Exception as e:
        return f"ERR: {e}"
