#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Construit le site de Rébecca Massé dans le dossier _site/.

Lit :   contenu/   (œuvres, séries, thèmes, À propos, réglages — fichiers JSON)
        originaux/ (photos des œuvres en pleine taille)
        statique/  (CSS, JavaScript, polices, documents, images du site)
Écrit : _site/     (le site prêt à publier, avec vignettes générées automatiquement)

Utilisation :  python outils/construire.py
Puis ouvrir _site/index.html dans un navigateur.
GitHub lance ce script tout seul à chaque modification (voir .github/workflows/publier.yml).
"""
import html
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Il manque la bibliothèque Pillow. Installez-la avec :  pip install Pillow")

RACINE = Path(__file__).resolve().parent.parent
CONTENU = RACINE / "contenu"
ORIGINAUX = RACINE / "originaux"
STATIQUE = RACINE / "statique"
SORTIE = RACINE / "_site"
CACHE = RACINE / ".cache-images"

DOMAINE = "https://www.rebeccamasse.com"
TAILLE_GRANDE = 2000
TAILLE_MINI = 900
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}
NBSP = " "
NOMBRES = ["zéro", "une", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix"]

avertissements = []


def avertir(msg):
    if msg not in avertissements:
        avertissements.append(msg)


# ============================================================ utilitaires
def typo(s):
    """Espaces insécables avant : ! ? (typographie française)."""
    return re.sub(r" ([:!?])", NBSP + r"\1", s or "")


def e(s):
    return html.escape(typo(s), quote=True)


def slugifier(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def pluriel(n):
    return f"{n} œuvre" if n == 1 else f"{n} œuvres"


def phrase_compte(modele, n):
    modele = (modele or "").strip() or "{n} œuvres"
    return modele.replace("{n} œuvres", pluriel(n)).replace("{n}", str(n))


def lire_json(chemin):
    try:
        with open(chemin, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as err:
        sys.exit(f"Erreur dans {chemin.relative_to(RACINE)} : {err}")


def lire_collection(dossier):
    elements = []
    for f in sorted((CONTENU / dossier).glob("*.json")):
        d = lire_json(f)
        if isinstance(d, dict):
            d["_id"] = f.stem
            elements.append(d)
    return elements


def nombre(v, defaut=None):
    try:
        return float(v) if v not in (None, "") else defaut
    except (TypeError, ValueError):
        return defaut


def chemin_local(valeur):
    """'/originaux/bible/a.jpg' -> 'bible/a.jpg' ; '/images/site/x.jpg' -> 'images/site/x.jpg'."""
    v = (valeur or "").strip().replace("\\", "/").lstrip("/")
    return v[len("originaux/"):] if v.startswith("originaux/") else v


# ============================================================ données
REGLAGES = lire_json(CONTENU / "site.json")
APROPOS = lire_json(CONTENU / "apropos.json")
FACEBOOK = REGLAGES.get("facebook") or ""

SERIES = sorted(lire_collection("series"), key=lambda s: (nombre(s.get("ordre"), 999), s.get("nom", "")))
SERIES_MASQUEES = [s for s in SERIES if s.get("visible") is False]
SERIES = [s for s in SERIES if s.get("visible") is not False]
THEMES = sorted(lire_collection("themes"), key=lambda t: (nombre(t.get("ordre"), 999), t.get("nom", "")))
for groupe in (SERIES, THEMES):
    for x in groupe:
        x["slug"] = slugifier(x.get("slug") or x.get("nom") or x["_id"])


def resoudre(valeur, groupe):
    """Retrouve une série ou un thème à partir de la valeur enregistrée (slug, nom de fichier ou nom)."""
    if not valeur:
        return None
    if isinstance(valeur, dict):
        valeur = valeur.get("slug") or valeur.get("value") or valeur.get("nom") or ""
    v = str(valeur).strip()
    v = Path(v).stem if "/" in v or v.endswith(".json") else v
    for x in groupe:
        if v in (x["slug"], x["_id"], x.get("nom")) or slugifier(v) == x["slug"]:
            return x
    return None


SERIE_PAR_SLUG = {s["slug"]: s for s in SERIES}
THEME_PAR_SLUG = {t["slug"]: t for t in THEMES}


# ============================================================ images
def produire_images(rel):
    """Crée la grande image et la vignette dans _site/images/ ; renvoie (grand, mini, (l, h) de la vignette)."""
    src = ORIGINAUX / rel
    base = Path(rel).with_suffix(".jpg")
    grand = Path("images") / base
    mini = Path("images") / base.parent / "mini" / base.name
    sorties = [(grand, TAILLE_GRANDE, 86), (mini, TAILLE_MINI, 80)]
    dims = None
    a_faire = []
    for chemin, taille, q in sorties:
        cache = CACHE / chemin
        if cache.exists() and cache.stat().st_mtime >= src.stat().st_mtime:
            continue
        a_faire.append((chemin, taille, q))
    if a_faire:
        with Image.open(src) as im:
            im = ImageOps.exif_transpose(im)
            if im.mode in ("RGBA", "LA", "P"):
                im = im.convert("RGBA")
                fond = Image.new("RGB", im.size, (255, 255, 255))
                fond.paste(im, mask=im.split()[-1])
                im = fond
            elif im.mode != "RGB":
                im = im.convert("RGB")
            for chemin, taille, q in a_faire:
                copie = im.copy()
                copie.thumbnail((taille, taille), Image.LANCZOS)
                (CACHE / chemin).parent.mkdir(parents=True, exist_ok=True)
                copie.save(CACHE / chemin, "JPEG", quality=q, optimize=True, progressive=True)
    for chemin, _t, _q in sorties:
        (SORTIE / chemin).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(CACHE / chemin, SORTIE / chemin)
    with Image.open(SORTIE / mini) as m:
        dims = m.size
    return grand.as_posix(), mini.as_posix(), dims


def preparer_oeuvres():
    oeuvres = []
    for o in lire_collection("oeuvres"):
        rel = chemin_local(o.get("image"))
        o["titre"] = (o.get("titre") or "").strip()
        o["serie_obj"] = resoudre(o.get("serie"), SERIES)
        if o.get("serie") and not o["serie_obj"]:
            if resoudre(o.get("serie"), SERIES_MASQUEES):
                continue  # série masquée : l'œuvre n'apparaît nulle part
            avertir(f"{o['_id']} : série inconnue « {o.get('serie')} »")
        themes = o.get("themes") or []
        if isinstance(themes, (str, dict)):
            themes = [themes]
        o["themes_obj"] = []
        for t in themes:
            th = resoudre(t, THEMES)
            if th:
                o["themes_obj"].append(th)
            else:
                avertir(f"{o['_id']} : thème inconnu « {t} »")
        if rel and (ORIGINAUX / rel).is_file() and Path(rel).suffix.lower() in EXTENSIONS:
            o["grand"], o["mini"], o["dims"] = produire_images(rel)
        else:
            avertir(f"{o['_id']} : photo introuvable ({o.get('image')}), œuvre ignorée")
            continue
        o["details"] = ", ".join(str(o.get(k)).strip() for k in ("technique", "dimensions", "annee")
                                 if str(o.get(k) or "").strip())
        oeuvres.append(o)
    return oeuvres


def cle_tri(o):
    return (nombre(o.get("ordre"), 1e9), o["_id"])


# ============================================================ fragments HTML
def img_oeuvre(o, lazy=True, extra="", alt=None):
    d = o.get("dims")
    taille = f' width="{d[0]}" height="{d[1]}"' if d else ""
    charge = ' loading="lazy" decoding="async"' if lazy else ""
    texte = o["alt"] if alt is None else alt
    return f'<img src="{o["mini"]}" alt="{e(texte)}"{taille}{charge} draggable="false"{extra}>'


def lien_oeuvre(o, contenu, classe="oeuvre", style=""):
    attrs = ""
    if o["titre"]:
        attrs += f' data-titre="{e(o["titre"])}"'
    if o["details"]:
        attrs += f' data-details="{e(o["details"])}"'
    serie = o["serie_obj"]["nom"] if o["serie_obj"] else ""
    st = f' style="{style}"' if style else ""
    return f'<a class="{classe}" href="{o["grand"]}"{attrs} data-serie="{e(serie)}"{st}>{contenu}</a>'


def carte_oeuvre(o, lazy):
    legende = ""
    if o["titre"] or o["details"]:
        titre = e(o["titre"]) if o["titre"] else ""
        details = f'<span class="oeuvre-details">{e(o["details"])}</span>' if o["details"] else ""
        legende = f"<figcaption>{titre}{details}</figcaption>"
    return f'        <figure class="oeuvre-carte">{lien_oeuvre(o, img_oeuvre(o, lazy=lazy))}{legende}</figure>'


def nav_themes(liste, actif=None, etiquette="Thèmes"):
    """liste : [(thème, nombre d'œuvres)]"""
    if not liste:
        return ""
    elements = []
    for t, n in liste:
        courant = ' aria-current="page"' if t["slug"] == actif else ""
        elements.append(f'<li><a class="pastille" href="theme-{t["slug"]}.html"{courant}>'
                        f'{e(t["nom"])}<span>{n}</span></a></li>')
    return (f'      <nav class="themes" aria-label="{e(etiquette)}">\n'
            f'        <p class="themes-titre">{e(etiquette)}</p>\n'
            f'        <ul>{"".join(elements)}</ul>\n'
            f'      </nav>')


def liste_expos(expos):
    lignes = []
    for x in expos:
        lieu = (x.get("lieu") or "").strip()
        if not lieu:
            continue
        t = f'<span class="expo-titre">{e(x["titre"])}</span>' if (x.get("titre") or "").strip() else ""
        n = f'<span class="expo-note">{e(x["note"])}</span>' if (x.get("note") or "").strip() else ""
        lignes.append(f'          <li><span class="expo-lieu">{e(lieu)}</span>{t}{n}</li>')
    return '        <ul class="expositions">\n' + "\n".join(lignes) + "\n        </ul>"


def image_site(cle):
    """Image du site rangée dans statique/ (chaîne vide si elle n'existe pas)."""
    rel = chemin_local(REGLAGES.get(cle))
    if rel and (STATIQUE / rel).is_file():
        return rel
    if rel:
        avertir(f"image du site introuvable : statique/{rel}")
    return ""


# ============================================================ gabarit de page
NAV = [("index.html", "Accueil"), ("a-propos.html", "À propos"),
       ("portfolio.html", "Portfolio"), ("contact.html", "Contact")]


def page(fichier, titre, description, contenu, actif=None, racine="", jsonld=None, indexer=True):
    canon = "" if fichier == "index.html" else fichier[:-5]
    url = f"{DOMAINE}/{canon}"
    r = racine
    courant = ' aria-current="page"'
    nav = "\n".join(f'          <li><a href="{r}{h}"{courant if h == actif else ""}>{e(t)}</a></li>'
                    for h, t in NAV)
    facebook_nav = (f'\n          <li><a href="{FACEBOOK}" rel="noopener" target="_blank">Facebook</a></li>'
                    if FACEBOOK else "")
    facebook_pied = (f'\n        <li><a href="{FACEBOOK}" rel="noopener" target="_blank">Facebook</a></li>'
                     if FACEBOOK else "")
    ld = (f'\n  <script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>'
          if jsonld else "")
    robots = "" if indexer else '\n  <meta name="robots" content="noindex">'
    partage = image_site("image_partage")
    og_image = partage if partage.startswith("http") else f"{DOMAINE}/{partage}"
    return f"""<!doctype html>
<html lang="fr-CA">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(titre)}</title>
  <meta name="description" content="{e(description)}">{robots}
  <link rel="canonical" href="{url}">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="fr_CA">
  <meta property="og:site_name" content="Rébecca Massé, artiste peintre">
  <meta property="og:title" content="{e(titre)}">
  <meta property="og:description" content="{e(description)}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{og_image}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="theme-color" content="#F0F1F1">
  <link rel="icon" href="{r}favicon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="{r}apple-touch-icon.png">
  <link rel="preload" href="{r}polices/cardo-400.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="{r}css/style.css">
  <script>document.documentElement.className+=' js';</script>
  <script src="{r}js/main.js" defer></script>{ld}
</head>
<body>
  <a class="saut" href="#contenu">Aller au contenu</a>

  <header class="entete">
    <div class="conteneur">
      <a class="signature" href="{r}index.html"><span>Rébecca Massé</span><small>Artiste peintre</small></a>
      <button class="menu-bouton" type="button" aria-expanded="false" aria-controls="nav-principale"><span class="barres" aria-hidden="true"></span>Menu</button>
      <nav id="nav-principale" class="nav" aria-label="Navigation principale">
        <ul>
{nav}{facebook_nav}
        </ul>
      </nav>
    </div>
  </header>

  <main id="contenu">
{contenu}
  </main>

  <footer class="pied">
    <div class="conteneur">
      <div>
        <p class="pied-signature">Rébecca Massé</p>
        <p class="pied-metier">Artiste peintre</p>
      </div>
      <ul>
        <li><a href="{r}a-propos.html">À propos</a></li>
        <li><a href="{r}portfolio.html">Portfolio</a></li>
        <li><a href="{r}contact.html">Contact</a></li>{facebook_pied}
      </ul>
      <p class="pied-droits">© <span data-annee>2026</span> Rébecca Massé. Toute reproduction des images est totalement interdite.</p>
    </div>
  </footer>
</body>
</html>
"""


# ============================================================ pages
def page_accueil(oeuvres, par_serie):
    # Le vitrail : 8 cases ; 1 = l'arche du haut, 4 = la case large du milieu. La lumière monte du bas.
    places = {}
    for o in oeuvres:
        p = nombre(o.get("vitrail"))
        if p and 1 <= int(p) <= 8 and int(p) not in places:
            places[int(p)] = o
    reserve = [o for o in sorted(oeuvres, key=cle_tri) if o["titre"] and o not in places.values()]
    for p in range(1, 9):
        if p not in places and reserve:
            places[p] = reserve.pop(0)
    cellules = []
    for p in sorted(places):
        o = places[p]
        extra = ' fetchpriority="high"' if p == 1 else ""
        classe = "oeuvre large" if p in (1, 4) else "oeuvre"
        cellules.append("            " + lien_oeuvre(o, img_oeuvre(o, lazy=False, extra=extra), classe, f"--i:{8 - p}"))

    series = []
    for s in SERIES:
        liste = par_serie.get(s["slug"])
        if not liste:
            continue
        c = next((o for o in liste if o.get("couverture")), liste[0])
        series.append(
            f'          <li><a class="serie-lien" href="{s["slug"]}.html">{img_oeuvre(c, alt="")}'
            f'<h3>{e(s["nom"])}</h3><p class="serie-compte">{e(phrase_compte(s.get("phrase_compte"), len(liste)))}</p></a></li>')

    bio = APROPOS.get("bio") or []
    citation = ""
    for p in bio:
        if "Chagall" in p:
            citation = [x for x in re.split(r"(?<=\.) ", p) if "Chagall" in x][0]
    citation = citation or (bio[-1] if bio else "")
    lien_memoire = ('<a class="lien-action" href="a-propos.html#memoire">Mon mémoire sur la Bible de Chagall</a>'
                    if APROPOS.get("memoire", {}).get("titre") else "")

    contenu = f"""    <section class="accueil-hero" aria-labelledby="titre-accueil">
      <div class="conteneur">
        <div class="hero-texte">
          <h1 id="titre-accueil"><span>Rébecca</span> <span>Massé</span></h1>
          <p class="hero-metier">Artiste peintre</p>
          <p class="hero-chapeau">Inspirée par la force symbolique des récits bibliques, je crée des œuvres où couleur, texture et lumière deviennent des langages expressifs.</p>
          <div class="actions">
            <a class="bouton" href="portfolio.html">Voir le portfolio</a>
            <a class="lien-action" href="a-propos.html">Lire ma démarche</a>
          </div>
        </div>
        <div class="vitrail" role="group" aria-label="Œuvres choisies">
          <div class="vitrail-verre" data-galerie="accueil">
{chr(10).join(cellules)}
          </div>
        </div>
      </div>
    </section>

    <section class="section" aria-labelledby="titre-series">
      <div class="conteneur">
        <div class="section-tete">
          <h2 id="titre-series">Les séries</h2>
          <a class="lien-action" href="portfolio.html">Tout le portfolio</a>
        </div>
        <ul class="series-grille">
{chr(10).join(series)}
        </ul>
      </div>
    </section>

    <section class="section" aria-labelledby="titre-demarche">
      <div class="conteneur">
        <div class="section-tete">
          <h2 id="titre-demarche">Démarche</h2>
        </div>
        <blockquote class="demarche-citation">
          <p>{e(citation)}</p>
        </blockquote>
        <p class="lien-suite"><a class="lien-action" href="a-propos.html">Lire la démarche complète</a>{lien_memoire}</p>
      </div>
    </section>

    <section class="section" aria-labelledby="titre-expos">
      <div class="conteneur">
        <div class="section-tete">
          <h2 id="titre-expos">Expositions récentes</h2>
          <a class="lien-action" href="a-propos.html#expositions">Toutes les expositions</a>
        </div>
{liste_expos((APROPOS.get("expositions") or [])[:6])}
      </div>
    </section>

    <section class="section" aria-labelledby="titre-appel">
      <div class="conteneur">
        <div class="appel">
          <div>
            <h2 id="titre-appel">{e("Au plaisir de vous lire !")}</h2>
            <p>{e("Une question sur une œuvre ou une exposition ? Écrivez-moi.")}</p>
          </div>
          <a class="bouton" href="contact.html">M'écrire</a>
        </div>
      </div>
    </section>"""
    partage = image_site("image_partage")
    ld = {"@context": "https://schema.org", "@type": "Person", "name": "Rébecca Massé",
          "jobTitle": "Artiste peintre", "url": DOMAINE + "/",
          "image": partage if partage.startswith("http") else f"{DOMAINE}/{partage}",
          "alumniOf": {"@type": "CollegeOrUniversity", "name": "Université Laval"},
          "sameAs": [FACEBOOK] if FACEBOOK else []}
    return page("index.html", "Rébecca Massé, artiste peintre",
                "Rébecca Massé, artiste peintre. Acrylique sur toile et sur bois, faux vitrail et récits bibliques : ses séries, sa démarche et ses expositions.",
                contenu, actif="index.html", jsonld=ld)


def bloc_memoire():
    m = APROPOS.get("memoire") or {}
    if not m.get("titre"):
        return "", None
    fichier = chemin_local(m.get("fichier"))
    existe = fichier and (STATIQUE / fichier).is_file()
    taille = f"PDF, {round((STATIQUE / fichier).stat().st_size / 1e6)} Mo" if existe else "PDF"
    page_titre = chemin_local(m.get("page_titre"))
    couverture = ""
    if existe and page_titre and (STATIQUE / page_titre).is_file():
        couverture = (f'          <a class="memoire-couverture" href="{fichier}" target="_blank" rel="noopener" tabindex="-1" aria-hidden="true">\n'
                      f'            <img src="{page_titre}" alt="" width="560" height="734" loading="lazy" decoding="async">\n'
                      f'          </a>\n')
    meta = ", ".join(x for x in (m.get("diplome"), m.get("etablissement"), str(m.get("annee") or "")) if x)
    if m.get("pages"):
        meta += f". {int(nombre(m['pages']))} pages."
    resume = "\n".join(f"            <p>{e(p)}</p>" for p in (m.get("resume") or []))
    bouton = (f'            <p class="memoire-action">\n'
              f'              <a class="bouton" href="{fichier}" target="_blank" rel="noopener" type="application/pdf">Lire le mémoire</a>\n'
              f'              <span>{taille}</span>\n'
              f'            </p>\n') if existe else ""
    html_bloc = f"""      <section class="section" id="memoire" aria-labelledby="titre-memoire">
        <div class="section-tete">
          <h2 id="titre-memoire">Mémoire de maîtrise</h2>
        </div>
        <div class="memoire">
{couverture}          <div class="memoire-texte">
            <p class="memoire-titre">{e(m['titre'])}</p>
            <p class="memoire-meta">{e(meta)}</p>
            <div class="memoire-resume">
{resume}
            </div>
{bouton}          </div>
        </div>
      </section>"""
    ld = {"@context": "https://schema.org", "@type": "Thesis", "name": m["titre"],
          "author": {"@type": "Person", "name": "Rébecca Massé"}, "datePublished": str(m.get("annee") or ""),
          "inSupportOf": m.get("diplome") or "", "inLanguage": "fr",
          "sourceOrganization": {"@type": "CollegeOrUniversity", "name": m.get("etablissement") or ""}}
    if existe:
        ld["url"] = f"{DOMAINE}/{fichier}"
    return html_bloc, ld


def page_apropos():
    paragraphes = "\n".join(f"          <p>{e(p)}</p>" for p in (APROPOS.get("bio") or []) if p)
    photo = image_site("photo_apropos")
    alt = REGLAGES.get("photo_apropos_alt") or ""
    figure = (f'        <figure class="apropos-photo">\n          <img src="{photo}" alt="{e(alt)}" decoding="async">\n        </figure>\n'
              if photo else "")
    memoire, ld = bloc_memoire()
    contenu = f"""    <div class="conteneur">
      <header class="page-tete">
        <h1>À propos</h1>
      </header>
      <div class="apropos">
{figure}        <div class="apropos-texte">
          <h2>Voici quelques mots à mon sujet</h2>
{paragraphes}
        </div>
      </div>

{memoire}

      <section class="section" id="expositions" aria-labelledby="titre-expos">
        <div class="section-tete">
          <h2 id="titre-expos">Dernières expositions</h2>
        </div>
{liste_expos(APROPOS.get("expositions") or [])}
      </section>
    </div>"""
    return page("a-propos.html", "À propos | Rébecca Massé, artiste peintre",
                "Formation, démarche, mémoire de maîtrise et expositions de Rébecca Massé, artiste peintre inspirée par la force symbolique des récits bibliques.",
                contenu, actif="a-propos.html", jsonld=ld)


def themes_de(oeuvres):
    compte = {}
    for o in oeuvres:
        for t in o["themes_obj"]:
            compte[t["slug"]] = compte.get(t["slug"], 0) + 1
    return [(t, compte[t["slug"]]) for t in THEMES if t["slug"] in compte]


def page_portfolio(par_serie, tous_themes):
    rangees = []
    total = 0
    for s in SERIES:
        liste = par_serie.get(s["slug"])
        if not liste:
            continue
        total += len(liste)
        vignettes = "".join(f'<a href="{s["slug"]}.html" tabindex="-1" aria-hidden="true">{img_oeuvre(o, alt="")}</a>'
                            for o in liste[:6])
        rangees.append(f"""        <li class="rangee">
          <div>
            <h2><a href="{s['slug']}.html">{e(s['nom'])}</a></h2>
            <p class="serie-compte">{e(phrase_compte(s.get("phrase_compte"), len(liste)))}</p>
            <a class="lien-action" href="{s['slug']}.html">Voir la série</a>
          </div>
          <div class="bande">{vignettes}</div>
        </li>""")
    nb = len(rangees)
    mot = NOMBRES[nb] if nb < len(NOMBRES) else str(nb)
    chapeau = f"{pluriel(total)} réparties en {mot} série{'s' if nb > 1 else ''}."
    par_theme = ""
    if tous_themes:
        par_theme = f"""
      <section class="section" aria-labelledby="titre-themes">
        <div class="section-tete">
          <h2 id="titre-themes">Par thème</h2>
        </div>
{nav_themes(tous_themes, etiquette="Thèmes").replace('<p class="themes-titre">Thèmes</p>', '')}
      </section>"""
    contenu = f"""    <div class="conteneur">
      <header class="page-tete">
        <h1>Portfolio</h1>
        <p class="chapeau">{e(chapeau)}</p>
      </header>
      <ul class="rangees">
{chr(10).join(rangees)}
      </ul>{par_theme}
    </div>"""
    noms = [s["nom"].rstrip("…") for s in SERIES if par_serie.get(s["slug"])]
    desc = "Les séries de Rébecca Massé : " + (", ".join(noms[:-1]) + " et " + noms[-1] if len(noms) > 1 else "".join(noms)) + "."
    return page("portfolio.html", "Portfolio | Rébecca Massé, artiste peintre", desc, contenu, actif="portfolio.html")


def page_serie(s, liste, voisines):
    cartes = "\n".join(carte_oeuvre(o, lazy=k >= 6) for k, o in enumerate(liste))
    prec, suiv = voisines
    nav_series = ""
    if prec and suiv and prec is not s:
        nav_series = f"""
      <nav class="series-voisines" aria-label="Autres séries">
        <a class="precedente" href="{prec['slug']}.html"><small>Série précédente</small><span>{e(prec['nom'])}</span></a>
        <a class="suivante" href="{suiv['slug']}.html"><small>Série suivante</small><span>{e(suiv['nom'])}</span></a>
      </nav>"""
    contenu = f"""    <div class="conteneur">
      <header class="page-tete">
        <nav class="fil" aria-label="Fil d'Ariane"><a href="portfolio.html">Portfolio</a></nav>
        <h1>{e(s['nom'])}</h1>
        <p class="chapeau">{e(phrase_compte(s.get("phrase_compte"), len(liste)))}</p>
{nav_themes(themes_de(liste), etiquette="Thèmes de la série")}
      </header>
      <div class="galerie" data-galerie="{s['slug']}">
{cartes}
      </div>{nav_series}
    </div>"""
    nom = s["nom"].rstrip("…")
    return page(f"{s['slug']}.html", f"{s['nom']} | Rébecca Massé, artiste peintre",
                f"{nom} : {pluriel(len(liste))} de Rébecca Massé, artiste peintre.",
                contenu, actif="portfolio.html")


def page_theme(t, liste, tous_themes):
    cartes = "\n".join(carte_oeuvre(o, lazy=k >= 6) for k, o in enumerate(liste))
    contenu = f"""    <div class="conteneur">
      <header class="page-tete">
        <nav class="fil" aria-label="Fil d'Ariane"><a href="portfolio.html">Portfolio</a></nav>
        <h1>{e(t['nom'])}</h1>
        <p class="chapeau">{e(pluriel(len(liste)))}</p>
{nav_themes(tous_themes, actif=t["slug"], etiquette="Thèmes")}
      </header>
      <div class="galerie" data-galerie="theme-{t['slug']}">
{cartes}
      </div>
    </div>"""
    return page(f"theme-{t['slug']}.html", f"{t['nom']} | Rébecca Massé, artiste peintre",
                f"{t['nom']} : {pluriel(len(liste))} de Rébecca Massé, artiste peintre.",
                contenu, actif="portfolio.html")


def page_contact():
    cle = (REGLAGES.get("cle_web3forms") or "").strip() or "REMPLACER_PAR_VOTRE_CLE_WEB3FORMS"
    autre = (f'        <p class="contact-autre">Vous pouvez aussi me joindre sur <a href="{FACEBOOK}" rel="noopener" target="_blank">Facebook</a>.</p>\n'
             if FACEBOOK else "")
    contenu = f"""    <div class="conteneur contact">
      <div>
        <h1>{e("Au plaisir de vous lire !")}</h1>
        <p class="contact-signature">Rébecca Massé - BK</p>
{autre}      </div>
      <form class="formulaire" action="https://api.web3forms.com/submit" method="POST">
        <input type="hidden" name="access_key" value="{e(cle)}">
        <input type="hidden" name="subject" value="Nouveau message depuis rebeccamasse.com">
        <input type="hidden" name="from_name" value="Site rebeccamasse.com">
        <input type="checkbox" name="botcheck" class="pot-de-miel" tabindex="-1" autocomplete="off" aria-hidden="true">
        <div class="champ">
          <label for="nom">Nom</label>
          <input id="nom" name="name" type="text" autocomplete="name" required>
        </div>
        <div class="champ">
          <label for="courriel">Courriel</label>
          <input id="courriel" name="email" type="email" autocomplete="email" required>
        </div>
        <div class="champ">
          <label for="sujet">Sujet <span>(facultatif)</span></label>
          <input id="sujet" name="sujet" type="text">
        </div>
        <div class="champ">
          <label for="message">Message</label>
          <textarea id="message" name="message" required></textarea>
        </div>
        <button class="bouton" type="submit">Envoyer</button>
        <p class="formulaire-etat" role="status" aria-live="polite"></p>
      </form>
    </div>"""
    return page("contact.html", "Contact | Rébecca Massé, artiste peintre",
                "Écrivez à Rébecca Massé, artiste peintre.", contenu, actif="contact.html")


def page_introuvable():
    contenu = """    <div class="conteneur">
      <div class="introuvable">
        <h1>Cette page n'existe pas</h1>
        <p>Le site a été refait et certaines adresses ont changé. Toutes les œuvres sont dans le portfolio.</p>
        <div class="actions">
          <a class="bouton" href="/portfolio.html">Voir le portfolio</a>
          <a class="lien-action" href="/index.html">Retour à l'accueil</a>
        </div>
      </div>
    </div>"""
    return page("404.html", "Page introuvable | Rébecca Massé, artiste peintre",
                "Cette page n'existe pas.", contenu, racine="/", indexer=False)


def redirection(cible, nom):
    return f"""<!doctype html>
<html lang="fr-CA">
<head>
  <meta charset="utf-8">
  <title>{e(nom)} | Rébecca Massé</title>
  <meta name="robots" content="noindex">
  <link rel="canonical" href="{DOMAINE}/{cible[:-5]}">
  <meta http-equiv="refresh" content="0; url={cible}">
</head>
<body>
  <p>Cette page a déménagé : <a href="{cible}">{e(nom)}</a>.</p>
</body>
</html>
"""


# ============================================================ construction
def ecrire(rel, texte):
    chemin = SORTIE / rel
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(texte, encoding="utf-8", newline="\n")


def main():
    if SORTIE.exists():
        shutil.rmtree(SORTIE)
    shutil.copytree(STATIQUE, SORTIE)

    oeuvres = preparer_oeuvres()
    for o in oeuvres:
        nom_serie = o["serie_obj"]["nom"].rstrip("…") if o["serie_obj"] else ""
        o["alt"] = o["titre"] or (f"Œuvre de la série {nom_serie}" if nom_serie else "Œuvre de Rébecca Massé")

    par_serie = {}
    for o in sorted(oeuvres, key=cle_tri):
        if o["serie_obj"]:
            par_serie.setdefault(o["serie_obj"]["slug"], []).append(o)
    # numéroter les œuvres sans titre dans leur série
    for s in SERIES:
        liste = par_serie.get(s["slug"], [])
        for n, o in enumerate(liste, 1):
            if not o["titre"]:
                o["alt"] = f"Œuvre {n} sur {len(liste)} de la série {s['nom'].rstrip('…')}"

    ordre_serie = {s["slug"]: k for k, s in enumerate(SERIES)}

    def cle_theme(o):
        return (ordre_serie.get(o["serie_obj"]["slug"], 99) if o["serie_obj"] else 99,) + cle_tri(o)

    tous_themes = themes_de(oeuvres)

    ecrire("index.html", page_accueil(oeuvres, par_serie))
    ecrire("a-propos.html", page_apropos())
    ecrire("portfolio.html", page_portfolio(par_serie, tous_themes))
    actives = [s for s in SERIES if par_serie.get(s["slug"])]
    for k, s in enumerate(actives):
        voisines = (actives[k - 1], actives[(k + 1) % len(actives)]) if len(actives) > 1 else (None, None)
        ecrire(f"{s['slug']}.html", page_serie(s, par_serie[s["slug"]], voisines))
    for t, _n in tous_themes:
        liste = sorted((o for o in oeuvres if t in o["themes_obj"]), key=cle_theme)
        ecrire(f"theme-{t['slug']}.html", page_theme(t, liste, tous_themes))
    ecrire("contact.html", page_contact())
    ecrire("404.html", page_introuvable())

    # Anciennes adresses Wix
    redirs = [("gallery", "portfolio", "Portfolio")]
    for s in SERIES:
        ancien = slugifier(s.get("ancienne_adresse") or "")
        if ancien and ancien != s["slug"] and par_serie.get(s["slug"]):
            redirs.append((ancien, s["slug"], s["nom"]))
    for ancien, cible, nom in redirs:
        ecrire(f"{ancien}.html", redirection(f"{cible}.html", nom))
    ecrire("_redirects", "# Anciennes adresses du site Wix (Cloudflare Pages, Netlify)\n"
           + "".join(f"/{a}  /{c}  301\n" for a, c, _n in redirs))

    pages = ["", "a-propos", "portfolio"] + [s["slug"] for s in actives] \
        + [f"theme-{t['slug']}" for t, _n in tous_themes] + ["contact"]
    urls = "\n".join(f"  <url><loc>{DOMAINE}/{p}</loc></url>" for p in pages)
    ecrire("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n'
           f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n')

    print(f"Site construit dans {SORTIE.relative_to(RACINE)}/ : {len(oeuvres)} œuvres, "
          f"{len(actives)} séries, {len(tous_themes)} thèmes avec des œuvres.")
    vides = [t["nom"] for t in THEMES if t["slug"] not in {x["slug"] for x, _n in tous_themes}]
    if vides:
        print("Thèmes sans œuvre (pas encore de page) : " + ", ".join(vides))
    if SERIES_MASQUEES:
        print("Séries masquées : " + ", ".join(s.get("nom", s["_id"]) for s in SERIES_MASQUEES))
    for a in avertissements:
        print("Attention : " + a)


if __name__ == "__main__":
    main()
