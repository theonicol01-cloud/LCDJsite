#!/usr/bin/env python3
"""
Générateur du site La Cuisine de Jeanine.

  python3 build.py        -> génère le site complet dans dist/

Chaque page de src/pages/ commence par un bloc  <!--meta { ...json... } -->
(titre, description, chemin...). Le reste est le contenu de <main>.
Le header, le footer et le <head> viennent de src/partials/.
Dans les pages et partials :
  {{icon:nom}}      -> insère une icône SVG (voir src/icons.py)
  {{nav:chemin}}    -> ajoute aria-current="page" si c'est la page courante
Le dossier dist/ est ce qu'on envoie sur Hostinger (public_html).
"""
import json, re, shutil, sys
from pathlib import Path
from datetime import date

ROOT = Path(__file__).parent
SRC, DIST = ROOT / "src", ROOT / "dist"
SITE_URL = "https://lacuisinedejeanine.fr"

sys.path.insert(0, str(SRC))
from icons import ICONS  # noqa: E402


def render(text, ctx):
    # {{partial:nom}} -> contenu de src/partials/nom.html (récursif)
    for _ in range(3):
        text = re.sub(r"\{\{partial:([\w-]+)\}\}",
                      lambda m: (SRC / "partials" / (m.group(1) + ".html")).read_text(), text)
    # {{checked:Valeur}} -> coche la case du formulaire si la page l'a demandé (meta "form_pick")
    text = re.sub(r"\{\{checked:([^}]*)\}\}",
                  lambda m: " checked" if m.group(1) in ctx.get("form_pick", "") else "", text)
    text = re.sub(r"\{\{icon:([\w-]+)\}\}", lambda m: ICONS[m.group(1)], text)
    text = re.sub(r"\{\{nav:([^}]*)\}\}",
                  lambda m: ' aria-current="page"' if m.group(1) == ctx["path"] else "", text)
    for k, v in ctx.items():
        text = text.replace("{{" + k + "}}", str(v))
    return text


def _txt(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html)).strip()


def structured_data(main, meta, ctx):
    """FAQ (générée à partir des <details> de la page) + fil d'Ariane."""
    out = []
    qa = re.findall(r"<details[^>]*>\s*<summary>(.*?)<i>.*?</summary>\s*<p>(.*?)</p>", main, re.S)
    if qa:
        out.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": _txt(q),
             "acceptedAnswer": {"@type": "Answer", "text": _txt(a)}} for q, a in qa]})
    if meta["path"] not in ("/", "/404/"):
        out.append({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Accueil", "item": SITE_URL + "/"},
            {"@type": "ListItem", "position": 2, "name": meta.get("crumb", meta["title"]), "item": ctx["canonical"]}]})
    return "".join('<script type="application/ld+json">' + json.dumps(o, ensure_ascii=False) + "</script>\n" for o in out)


def build():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    shutil.copytree(ROOT / "assets", DIST / "assets")
    for f in (SRC / "static").iterdir():
        shutil.copy(f, DIST / f.name)
    # empreinte CSP du petit script inline du <head>
    import base64, hashlib
    inline = re.search(r"<script>(.*?)</script>", (SRC / "partials/head.html").read_text()).group(1)
    sha = base64.b64encode(hashlib.sha256(inline.encode()).digest()).decode()
    ht = DIST / ".htaccess"
    ht.write_text(ht.read_text().replace("sha256-REPLACE", "sha256-" + sha))

    head = (SRC / "partials/head.html").read_text()
    header = (SRC / "partials/header.html").read_text()
    footer = (SRC / "partials/footer.html").read_text()
    urls = []

    for page in sorted((SRC / "pages").glob("*.html")):
        raw = page.read_text()
        m = re.match(r"\s*<!--meta\s*(\{.*?\})\s*-->", raw, re.S)
        meta = json.loads(m.group(1))
        body = raw[m.end():]
        ctx = {
            "title": meta["title"],
            "description": meta["description"],
            "path": meta["path"],
            "canonical": SITE_URL + meta["path"],
            "og_image": SITE_URL + meta.get("og_image", "/assets/img/og-image.jpg"),
            "jsonld": "",
            "form_pick": meta.get("form_pick", ""),
            "year": date.today().year,
        }
        main = render(body, ctx)
        ctx["jsonld"] = structured_data(main, meta, ctx)
        html = ("<!doctype html>\n<html lang=\"fr\">\n<head>\n" + render(head, ctx) +
                "</head>\n<body>\n" + render(header, ctx) +
                "<main id=\"contenu\">\n" + main + "</main>\n" +
                render(footer, ctx) + "</body>\n</html>\n")
        out = DIST / meta["path"].strip("/") / "index.html" if meta["path"] != "/" else DIST / "index.html"
        if meta.get("noindex"):
            html = html.replace('<meta name="viewport"', '<meta name="robots" content="noindex">\n<meta name="viewport"', 1)
        else:
            urls.append(ctx["canonical"])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html)
        print("  ", meta["path"], "->", out.relative_to(ROOT))

    today = date.today().isoformat()
    sm = "".join(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls)
    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + sm + "</urlset>\n")
    print("OK ->", DIST)


def build_github(base="/LCDJsite"):
    """Version de test pour GitHub Pages (dist-github/) :
    chemins préfixés par le nom du dépôt, site non indexé par Google,
    formulaire en mode démonstration (GitHub Pages n'exécute pas PHP)."""
    build()
    gh = ROOT / "dist-github"
    if gh.exists():
        shutil.rmtree(gh)
    shutil.copytree(DIST, gh)
    for f in (".htaccess", "contact.php", "sitemap.xml"):
        (gh / f).unlink(missing_ok=True)
    (gh / ".nojekyll").write_text("")
    (gh / "robots.txt").write_text("User-agent: *\nDisallow: /\n")
    def fix(m):
        attr, url = m.group(1), m.group(2)
        return f'{attr}="{base}{url}"'
    for p in gh.rglob("*.html"):
        h = p.read_text()
        h = re.sub(r'(href|src|action)="(/(?!/)[^"]*)"', fix, h)
        h = re.sub(r'srcset="([^"]+)"', lambda m: 'srcset="' + re.sub(r'(^|, )/(?!/)', lambda n: n.group(1) + base + "/", m.group(1)) + '"', h)
        h = h.replace('<meta name="viewport"', '<meta name="robots" content="noindex, nofollow">\n<meta name="viewport"', 1)
        p.write_text(h)
    shutil.copy(gh / "404" / "index.html", gh / "404.html")
    js = gh / "assets/js/site.js"
    s = js.read_text()
    s = s.replace("    btn.disabled = true;\n    var label",
                  "    if (location.hostname.indexOf('github.io') !== -1) {\n"
                  "      show('ok', \"Version de test : sur le vrai site, votre demande partira à contact@lacuisinedejeanine.fr.\");\n"
                  "      return;\n    }\n    btn.disabled = true;\n    var label", 1)
    js.write_text(s)
    print("OK ->", gh)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "github":
        build_github(sys.argv[2] if len(sys.argv) > 2 else "/LCDJsite")
    else:
        build()
