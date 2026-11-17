"""Descarga el data-*.json más reciente de la carpeta pública de Drive y lo
copia a data.json si es válido y más nuevo que el actual."""
import html, json, re, sys, urllib.request

folder, out = sys.argv[1], sys.argv[2]
UA = {"User-Agent": "Mozilla/5.0 (monitor-fatiga sync)"}

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read()

page = get(f"https://drive.google.com/embeddedfolderview?id={folder}").decode("utf-8", "replace")
entries = re.findall(r'id="entry-([\w-]{20,})".*?flip-entry-title">([^<]+)<', page, re.S)
files = sorted(((html.unescape(t).strip(), i) for i, t in entries
                if re.fullmatch(r"data-\d{8}T\d{4}\.json", html.unescape(t).strip())), reverse=True)
print("Archivos en Drive:", [t for t, _ in files][:5])
if not files:
    sys.exit("No hay data-*.json en la carpeta (¿carpeta no pública?)")

for title, fid in files[:3]:
    try:
        raw = get(f"https://drive.usercontent.google.com/download?id={fid}&export=download")
        new = json.loads(raw)
        assert isinstance(new.get("days"), dict) and new.get("publishedUntil") and new.get("generated")
        break
    except Exception as e:
        print("No válido:", title, e)
else:
    sys.exit("Ningún archivo válido")

try:
    cur = json.load(open(out, encoding="utf-8"))
except Exception:
    cur = {}
if cur.get("signature") == new.get("signature") and cur.get("generated", "") >= new["generated"]:
    print("Ya al día:", title); sys.exit(0)
if cur.get("generated", "") > new["generated"]:
    print("El data.json actual es más nuevo; no se toca"); sys.exit(0)
json.dump(new, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("Actualizado desde", title, "→ publicado hasta", new["publishedUntil"])
