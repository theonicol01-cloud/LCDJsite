# Prépare l'aperçu multi-pages (artifact) à partir de dist/ : chemins relatifs, formulaire en mode démo.
import re, json, shutil
from pathlib import Path
shutil.rmtree('preview', ignore_errors=True); Path('preview').mkdir(); shutil.copytree('dist/assets','preview/assets')
PAGES={'':'index.html','frigo-connecte':'frigo-connecte.html','plateaux-repas':'plateaux-repas.html','traiteur-evenements':'traiteur-evenements.html','notre-histoire':'notre-histoire.html','contact':'contact.html','mentions-legales':'mentions-legales.html'}
used=set()
def fix(h):
    h=h.replace('"/assets/','"assets/').replace(' /assets/',' assets/').replace(',/assets/',',assets/')
    h=re.sub(r'<link rel="preload"[^>]*>\n','',h)
    def link(m):
        slug,anchor=m.group(1).strip('/'),m.group(2) or ''
        return 'href="%s%s"'%(PAGES.get(slug,'index.html'),anchor)
    h=re.sub(r'href="/([\w-]*)/?(#[\w-]+)?"',link,h)
    used.update(re.findall(r'assets/[\w/.-]+',h))
    return h
for slug,out in PAGES.items():
    src=Path('dist',slug,'index.html')
    h=fix(src.read_text())
    if out=='index.html':
        h=re.sub(r'<!doctype html>\s*<html[^>]*>\s*<head>\s*','',h)
        h=h.replace('</head>\n<body>\n','').replace('</body>\n</html>\n','')
        h=h.replace('<meta charset="utf-8">\n','').replace('<meta name="viewport" content="width=device-width, initial-scale=1">\n','')
        h=re.sub(r'<title>.*?</title>','<title>La Cuisine de Jeanine</title>',h)
    Path('preview',out).write_text(h)
js=Path('preview/assets/js/site.js'); s=js.read_text()
s=s.replace("    btn.disabled = true;\n    var label","    if (location.hostname.indexOf('lacuisinedejeanine') === -1) {\n      show('ok', \"Aperçu : sur le vrai site, votre demande partira à contact@lacuisinedejeanine.fr.\");\n      return;\n    }\n    btn.disabled = true;\n    var label",1)
js.write_text(s)
used|={'assets/css/site.css','assets/js/site.js','assets/fonts/outfit-latin.woff2','assets/fonts/mona-sans-latin.woff2'}
files={u:u for u in sorted(used) if Path('preview',u).exists()}
for out in PAGES.values():
    if out!='index.html': files[out]=out
print(json.dumps(files)); print(len(files))
