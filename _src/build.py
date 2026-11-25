#!/usr/bin/env python3
"""Τέταρτος Τοίχος: παράγει το site από το _src/reviews.json.

Τρέξιμο από τη ρίζα του repo:  python3 _src/build.py
Γράφει: index.html, arxeio/, sxetika/, έναν φάκελο ανά κριτική, 404.html,
assets/, sitemap.xml, robots.txt. Το CNAME δεν το αγγίζει.

Πεδία κριτικής στο reviews.json:
  slug (λατινικά, αριθμοί, παύλες), title, company, venue, date ('ΕΕΕΕ-ΜΜ-ΗΗ' ή 'ΕΕΕΕ-ΜΜ'),
  rating (0-10 ή null), tags, excerpt, featured (true για καρφίτσωμα στην αρχική),
  body: {"p": παράγραφος} | {"q": παράθεμα} | {"q":..., "by": πηγή} | {"br": true}
        | {"img": "αρχείο", "caption":..., "credit":...}
  Μέσα σε παράγραφο, *λέξη* γίνεται πλάγια.
"""
import datetime
import html
import json
import re
import shutil
import unicodedata
from pathlib import Path

SRC = Path(__file__).resolve().parent
OUT = SRC.parent
SITE = 'https://tetartostoixos.gr/'
NAME = 'Τέταρτος Τοίχος'
HOME_ROWS = 6

MONTHS_GEN = ['Ιανουαρίου', 'Φεβρουαρίου', 'Μαρτίου', 'Απριλίου', 'Μαΐου', 'Ιουνίου', 'Ιουλίου',
              'Αυγούστου', 'Σεπτεμβρίου', 'Οκτωβρίου', 'Νοεμβρίου', 'Δεκεμβρίου']
MONTHS_NOM = ['Ιανουάριος', 'Φεβρουάριος', 'Μάρτιος', 'Απρίλιος', 'Μάιος', 'Ιούνιος', 'Ιούλιος',
              'Αύγουστος', 'Σεπτέμβριος', 'Οκτώβριος', 'Νοέμβριος', 'Δεκέμβριος']

esc = lambda s: html.escape(str(s), quote=True)


def rich(s):
    return re.sub(r'\*([^*]+)\*', r'<em>\1</em>', esc(s))


def plain(s):
    return s.replace('*', '')


def fmt_date(iso):
    parts = [int(x) for x in iso.split('-')]
    return f'{parts[2]} {MONTHS_GEN[parts[1] - 1]}' if len(parts) == 3 else MONTHS_NOM[parts[1] - 1]


def norm(s):
    s = unicodedata.normalize('NFD', s.lower())
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn').replace('ς', 'σ')


def minutes(r):
    text = ' '.join(b.get('p') or (b.get('q') if b.get('by') else '') or '' for b in r['body'])
    return max(1, round(len(text.split()) / 200))


def trim(s, n=155):
    s = plain(s)
    if len(s) <= n:
        return s
    return s[:n].rsplit(' ', 1)[0].rstrip(',.:;') + '…'


def page(root, current, title, desc, path, main, og_type='website', extra_head='', body_attrs=''):
    url = SITE + path
    nav = []
    for key, href, label in (('home', root or './', 'Αρχική'), ('arxeio', root + 'arxeio/', 'Αρχείο'),
                             ('sxetika', root + 'sxetika/', 'Σχετικά')):
        cur = ' aria-current="page"' if key == current else ''
        nav.append(f'<a href="{href}"{cur}>{label}</a>')
    return f'''<!DOCTYPE html>
<html lang="el">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:site_name" content="{NAME}">
<meta property="og:locale" content="el_GR">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary">
{extra_head}<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Literata:ital,wght@0,400;0,600;1,400&family=Sofia+Sans+Condensed:wght@400;500;600&family=Sofia+Sans+Extra+Condensed:wght@700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{root}assets/site.css">
<script>try{{if(localStorage.getItem('tt-lights')==='on')document.documentElement.setAttribute('data-lights','on')}}catch(e){{}}</script>
</head>
<body{body_attrs}>
<div id="progress" aria-hidden="true"></div>

<header class="wrap bar">
  <a class="mark" href="{root or './'}" aria-label="{NAME}, αρχική">Τεταρτος <b>Τοιχος</b></a>
  <nav class="nav" aria-label="Κύρια πλοήγηση">
    {nav[0]}
    {nav[1]}
    {nav[2]}
    <button class="lights" id="lights" type="button" aria-pressed="false"><i></i>Φώτα πλατείας</button>
  </nav>
</header>

<main id="view" class="wrap">
{main}
</main>

<footer class="wrap">
  <span>© 2026 {NAME}</span>
  <span>Ανώνυμες σημειώσεις πλατείας</span>
</footer>

<script src="{root}assets/site.js"></script>
</body>
</html>
'''


def row(r, root):
    rating = f"{r['rating']}/10" if r['rating'] is not None else ''
    return (f'<li class="row" data-slug="{r["slug"]}" data-no="{int(r["no"])}" data-tags="{esc("|".join(r["tags"]))}" '
            f'data-venue="{esc(r["venue"] or "")}" data-rating="{r["rating"] if r["rating"] is not None else -1}">'
            f'<a href="{root}{r["slug"]}/">'
            f'<span class="n">№ {r["no"]}</span>'
            f'<span class="d">{fmt_date(r["date"])}</span>'
            f'<span class="t">{esc(r["title"])}<small>{esc(plain(r["excerpt"]))}</small></span>'
            f'<span class="v">{esc(r["venue"] or "")}</span>'
            f'<span class="r">{rating}</span></a></li>')


def meta_line(r, with_no=True):
    parts = ([f'№ {r["no"]}'] if with_no else []) + ([esc(r['venue'])] if r['venue'] else [])
    return ' · '.join(parts + [fmt_date(r['date']), f'{minutes(r)}′ ανάγνωσης'])


def build_home(reviews, by_new):
    pinned = next((r for r in by_new if r.get('featured')), None)
    first = pinned or by_new[0]
    rest = [r for r in by_new if r is not first]
    label = 'Επιλεγμένη σημείωση' if pinned else 'Τελευταία σημείωση'
    head = 'Πρόσφατες' if pinned else 'Προηγούμενες'
    venues = {r['venue'] for r in reviews if r['venue']}
    main = f'''<section class="hero">
  <h1 aria-label="{NAME}">
    <span aria-hidden="true">Τεταρτος</span>
    <div class="wall" aria-hidden="true"><em class="stage">Σκηνή ↑</em><em class="house">Πλατεία ↓</em></div>
    <span aria-hidden="true">Τοιχος</span>
  </h1>
  <div class="thesis">
    <p>Ό,τι συμβαίνει στη σκηνή σταματά σε μια αόρατη γραμμή. Εδώ γράφεται ό,τι την πέρασε.</p>
    <p>Ανώνυμες κριτικές θεάτρου από παραστάσεις στην Αθήνα, γραμμένες αφού ανάψουν τα φώτα.</p>
  </div>
</section>

<section class="featured" aria-labelledby="feat-title">
  <p class="eyebrow">{label}<br>№ {first["no"]}</p>
  <div>
    <p class="eyebrow">{meta_line(first, with_no=False)}</p>
    <h2 id="feat-title"><a href="{first["slug"]}/">{esc(first["title"])}</a></h2>
    <p class="excerpt">{esc(plain(first["excerpt"]))}</p>
    <a class="more" href="{first["slug"]}/">Διάβασε την κριτική</a>
  </div>
</section>

<div class="section-head">
  <p class="eyebrow">{head}</p>
  <a class="back" href="arxeio/">Όλο το αρχείο ({len(reviews)}) →</a>
</div>
<ul class="rows">
{chr(10).join(row(r, "") for r in rest[:HOME_ROWS])}
</ul>

<div class="stats">
  <span><b>{len(reviews)}</b>Παραστάσεις</span>
  <span><b>{len(venues)}</b>Χώροι</span>
  <span><b>{sum(minutes(r) for r in reviews)}</b>Λεπτά ανάγνωσης</span>
</div>'''
    ld = {'@context': 'https://schema.org', '@type': 'WebSite', 'name': NAME, 'url': SITE, 'inLanguage': 'el'}
    extra = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>\n'
    routes = ' '.join(['arxeio', 'sxetika'] + [r['slug'] for r in reviews])
    return page('', 'home', f'{NAME} · Κριτικές θεάτρου στην Αθήνα',
                'Ανώνυμες κριτικές θεάτρου από παραστάσεις στην Αθήνα. Ό,τι πέρασε τη γραμμή από τη σκηνή στην πλατεία.',
                '', main, extra_head=extra, body_attrs=f' data-routes="{routes}"')


def build_archive(reviews, by_new):
    tags, venues = [], []
    for r in reviews:
        for t in r['tags']:
            if t not in tags:
                tags.append(t)
        if r['venue'] and r['venue'] not in venues:
            venues.append(r['venue'])
    chip = lambda key, v: (f'<button type="button" class="chip" data-key="{key}" data-val="{esc(v)}" '
                           f'aria-pressed="false">{"#" if key == "tag" else ""}{esc(v)}</button>')
    index = {r['slug']: norm(' '.join([r['title'], r['venue'] or '', r['company'] or '', ' '.join(r['tags']),
                                      r['excerpt']] + [plain(b.get('p') or b.get('q') or '') for b in r['body']]))
             for r in reviews}
    idx_json = json.dumps(index, ensure_ascii=False).replace('</', '<\\/')
    main = f'''<div class="page-head"><h1>Αρχείο</h1></div>
<div class="tools">
  <input id="q" type="search" placeholder="Ψάξε παράσταση, θέατρο ή λέξη-κλειδί…" aria-label="Αναζήτηση">
  <select id="sort" aria-label="Ταξινόμηση">
    <option value="new">Νεότερες πρώτα</option>
    <option value="old">Παλαιότερες πρώτα</option>
    <option value="rating">Κατά βαθμολογία</option>
  </select>
</div>
<div class="filters">
  <div><span>Θέμα</span>{"".join(chip("tag", t) for t in tags)}</div>
  <div><span>Χώρος</span>{"".join(chip("venue", v) for v in venues)}</div>
</div>
<p class="eyebrow count" id="count" aria-live="polite">{len(reviews)} σημειώσεις</p>
<ul class="rows" id="rows">
{chr(10).join(row(r, "../") for r in by_new)}
</ul>
<p class="empty" id="empty" hidden>Σκοτάδι. Καμία σημείωση δεν ταιριάζει με αυτά τα φίλτρα. <button type="button" id="clear">Καθάρισε τα φίλτρα</button></p>
<script type="application/json" id="idx">{idx_json}</script>'''
    return page('../', 'arxeio', f'Αρχείο κριτικών · {NAME}',
                f'Όλες οι κριτικές θεάτρου του Τέταρτου Τοίχου: {len(reviews)} παραστάσεις στην Αθήνα, με αναζήτηση ανά θέμα και χώρο.',
                'arxeio/', main)


def build_about():
    main = '''<div class="page-head"><h1>Σχετικά</h1></div>
<div class="about">
  <section class="entry">
    <h2>τέταρτος τοίχος <small>(ο), θεατρικός όρος</small></h2>
    <p>Ο νοητός τοίχος που χωρίζει τη σκηνή από την πλατεία. Οι ηθοποιοί παίζουν σαν να μην υπάρχει κοινό και το κοινό κοιτάζει σαν να μην το βλέπει κανείς.</p>
    <p>Η ιδέα αποδίδεται στον Ντιντερό, τον 18ο αιώνα. Ο Μπρεχτ έκανε το γκρέμισμά του μέθοδο.</p>
  </section>
  <section class="plain">
    <h2>Από την πλατεία</h2>
    <p>Εδώ μαζεύονται οι σημειώσεις ενός ανθρώπου που βλέπει πολύ θέατρο και κρατάει όσα δεν σβήνουν μόλις ανάψουν τα φώτα της αίθουσας.</p>
    <p>Όσα διαβάζεις είναι εντελώς προσωπικά, καμιά φορά άδικα, πάντα ειλικρινή. Η υπογραφή δεν έχει καμία σημασία, γι’ αυτό και δεν υπάρχει.</p>
  </section>
</div>'''
    return page('../', 'sxetika', f'Σχετικά · {NAME}',
                'Τι είναι ο τέταρτος τοίχος και τι θα βρεις εδώ: ανώνυμες, προσωπικές σημειώσεις για θεατρικές παραστάσεις στην Αθήνα.',
                'sxetika/', main)


def build_piece(r, by_old):
    i = by_old.index(r)
    prev = by_old[i - 1] if i > 0 else None
    nxt = by_old[i + 1] if i + 1 < len(by_old) else None
    blocks = []
    for b in r['body']:
        if b.get('p'):
            blocks.append(f'<p>{rich(b["p"])}</p>')
        elif b.get('q') and b.get('by'):
            blocks.append(f'<blockquote class="cited">{rich(b["q"])}<cite>{rich(b["by"])}</cite></blockquote>')
        elif b.get('q'):
            blocks.append(f'<blockquote>«{rich(b["q"])}»</blockquote>')
        elif b.get('img'):
            cap = esc(b.get('caption') or '') + (' Φωτογραφία: ' + esc(b['credit']) if b.get('credit') else '')
            alt = esc(b.get('alt') or b.get('caption') or r['title'])
            blocks.append(f'<figure><img src="{esc(b["img"])}" alt="{alt}">'
                          + (f'<figcaption>{cap}</figcaption>' if cap else '') + '</figure>')
        elif b.get('br'):
            blocks.append('<hr>')
    card = [f'<div><dt>Παράσταση</dt><dd>{esc(r["title"])}</dd></div>']
    if r['company']:
        card.append(f'<div><dt>Ομάδα</dt><dd>{esc(r["company"])}</dd></div>')
    if r['venue']:
        card.append(f'<div><dt>Χώρος</dt><dd>{esc(r["venue"])}</dd></div>')
    card.append(f'<div><dt>Ημερομηνία</dt><dd>{fmt_date(r["date"])}</dd></div>')
    score = (f'<div class="tear"></div><div class="score"><span>Βαθμολογία</span><b>{r["rating"]}/10</b></div>'
             if r['rating'] is not None else '')
    tags = ''.join(f'<a href="../arxeio/?tag={esc(t)}">#{esc(t)}</a>' for t in r['tags'])
    adj = (f'<a href="../{prev["slug"]}/"><span class="eyebrow">← Προηγούμενη</span><strong>{esc(prev["title"])}</strong></a>'
           if prev else '<span></span>')
    if nxt:
        adj += f'<a href="../{nxt["slug"]}/"><span class="eyebrow">Επόμενη →</span><strong>{esc(nxt["title"])}</strong></a>'
    main = f'''<article class="piece">
  <a class="back" href="../arxeio/">← Αρχείο</a>
  <header class="piece-head">
    <p class="eyebrow">{meta_line(r)}</p>
    <h1>{esc(r["title"])}</h1>
  </header>
  <div class="cols">
    <div class="prose" id="prose">
{chr(10).join(blocks)}
    </div>
    <aside class="stub" aria-label="Ταυτότητα παράστασης">
      <h2>Ταυτότητα παράστασης</h2>
      <dl>{"".join(card)}</dl>
      {score}
      <div class="tear"></div>
      <div class="tags">{tags}</div>
      <div class="tear"></div>
      <div class="size"><span>Μέγεθος γραμμάτων</span>
        <div><button type="button" id="minus" aria-label="Μικρότερα γράμματα">Α−</button><button type="button" id="plus" aria-label="Μεγαλύτερα γράμματα">Α+</button></div>
      </div>
    </aside>
  </div>
  <nav class="adjacent" aria-label="Γειτονικές σημειώσεις">{adj}</nav>
</article>'''
    where = f' ({r["venue"]})' if r['venue'] else ''
    title = f'{r["title"]}{where}: κριτική παράστασης · {NAME}'
    desc = trim(r['excerpt'])
    url = SITE + r['slug'] + '/'
    item = {'@type': 'Play', 'name': r['title']}
    ld = {'@context': 'https://schema.org', '@type': 'Review', 'headline': f'{r["title"]}: κριτική παράστασης',
          'url': url, 'inLanguage': 'el', 'datePublished': r['date'], 'description': desc, 'itemReviewed': item,
          'author': {'@type': 'Organization', 'name': NAME, 'url': SITE},
          'publisher': {'@type': 'Organization', 'name': NAME, 'url': SITE}}
    if r['rating'] is not None:
        ld['reviewRating'] = {'@type': 'Rating', 'ratingValue': r['rating'], 'bestRating': 10, 'worstRating': 0}
    ld_json = json.dumps(ld, ensure_ascii=False).replace('</', '<\\/')
    extra = f'<script type="application/ld+json">{ld_json}</script>\n'
    return page('../', 'arxeio', title, desc, r['slug'] + '/', main, og_type='article', extra_head=extra)


def build_404():
    main = '''<div class="notfound">
  <div class="page-head"><h1>Αυλαία</h1></div>
  <p>Αυτή η σελίδα δεν υπάρχει ή άλλαξε διεύθυνση. Όλες οι κριτικές βρίσκονται στο <a href="/arxeio/">αρχείο</a>.</p>
</div>'''
    out = page('/', '', f'Η σελίδα δεν βρέθηκε · {NAME}', 'Η σελίδα δεν βρέθηκε.', '404.html', main)
    return out.replace('<meta name="description"', '<meta name="robots" content="noindex">\n<meta name="description"', 1)


def main():
    reviews = json.loads((SRC / 'reviews.json').read_text(encoding='utf-8'))
    slugs = [r['slug'] for r in reviews]
    assert len(set(slugs)) == len(slugs), 'διπλό slug'
    for r in reviews:
        assert re.fullmatch(r'[a-z0-9-]+', r['slug']) and r['slug'] not in ('arxeio', 'sxetika', 'assets'), r['slug']
        r.setdefault('company', None); r.setdefault('venue', None); r.setdefault('rating', None)
    by_new = sorted(reviews, key=lambda r: r['date'], reverse=True)
    by_old = by_new[::-1]
    for i, r in enumerate(by_old):
        r['no'] = f'{i + 1:02d}'

    # καθάρισμα παλιών παραγόμενων φακέλων (όσοι έχουν μόνο ένα index.html)
    for d in OUT.iterdir():
        if d.is_dir() and not d.name.startswith(('.', '_')) and d.name != 'assets':
            if [p.name for p in d.iterdir()] == ['index.html']:
                shutil.rmtree(d)

    def write(rel, text):
        p = OUT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8')

    write('index.html', build_home(reviews, by_new))
    write('arxeio/index.html', build_archive(reviews, by_new))
    write('sxetika/index.html', build_about())
    write('404.html', build_404())
    for r in reviews:
        write(f'{r["slug"]}/index.html', build_piece(r, by_old))
    (OUT / 'assets').mkdir(exist_ok=True)
    shutil.copy(SRC / 'site.css', OUT / 'assets' / 'site.css')
    shutil.copy(SRC / 'site.js', OUT / 'assets' / 'site.js')

    today = datetime.date.today().isoformat()
    urls = ['', 'arxeio/', 'sxetika/'] + [r['slug'] + '/' for r in by_new]
    write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + ''.join(f'  <url><loc>{SITE}{u}</loc><lastmod>{today}</lastmod></url>\n' for u in urls) + '</urlset>\n')
    write('robots.txt', f'User-agent: *\nAllow: /\n\nSitemap: {SITE}sitemap.xml\n')
    print(f'{len(reviews)} κριτικές, {len(urls)} σελίδες')


if __name__ == '__main__':
    main()
