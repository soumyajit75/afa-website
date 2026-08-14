#!/usr/bin/env python3
"""
Amuzi Centre of Excellence — static site build script.

Assembles final, deployable HTML pages from:
  - source/templates/base.html        (base document shell)
  - source/templates/partials/*.html  (shared header / footer)
  - source/templates/pages/*.html     (per-page content, with {{ }} slots)
  - content/*.json                    (CMS-ready structured content)

No Node.js / build tooling required to run this — plain Python 3 standard
library only. Output is plain static HTML/CSS/JS, deployable to any static
host (or droppable into a future CMS / Next.js migration, since content is
already separated from markup in content/*.json).

Usage:
    python3 build.py
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "source" / "templates"
CONTENT = ROOT / "content"
SITE_URL = "https://www.amuzi.in"

# --------------------------------------------------------------------------
# Icon library — hand-authored line icons, 24x24, stroke=currentColor.
# Keeps the site free of icon-font/CDN dependencies.
# --------------------------------------------------------------------------
ICONS = {
    "shield": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l7 3v6c0 4.5-3 7.7-7 9-4-1.3-7-4.5-7-9V6l7-3Z"/></svg>',
    "flag": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 21V4"/><path d="M5 4h13l-3 4 3 4H5"/></svg>',
    "whistle": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="15" r="5"/><path d="M13 12h5a3 3 0 0 0 3-3V7h-4l-4 3"/><path d="M8 15h.01"/></svg>',
    "chart": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20V10M12 20V4M20 20v-7"/><path d="M3 20h18"/></svg>',
    "target": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r="0.6" fill="currentColor"/></svg>',
    "globe": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17M12 3.5c2.5 2.4 3.8 5.3 3.8 8.5s-1.3 6.1-3.8 8.5c-2.5-2.4-3.8-5.3-3.8-8.5S9.5 5.9 12 3.5Z"/></svg>',
    "cap": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 9l10-4 10 4-10 4-10-4Z"/><path d="M6 11v4c0 1.7 2.7 3 6 3s6-1.3 6-3v-4"/><path d="M22 9v6"/></svg>',
    "building": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="3" width="16" height="18"/><path d="M9 8h1M14 8h1M9 12h1M14 12h1M9 16h1M14 16h1"/></svg>',
    "network": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="5" r="2.2"/><circle cx="5" cy="19" r="2.2"/><circle cx="19" cy="19" r="2.2"/><path d="M12 7.2V13M12 13L6.4 17.3M12 13l5.6 4.3"/></svg>',
    "trend": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/></svg>',
    "arrow-right": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
    "check-circle": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.5 2.5L16 9"/></svg>',
    "video": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="6" width="12" height="12" rx="2"/><path d="M15 10l6-3v10l-6-3"/></svg>',
    "brain": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 4a3 3 0 0 0-3 3 3 3 0 0 0-1.5 5.6A3 3 0 0 0 7 17a3 3 0 0 0 5.5 1.7"/><path d="M15 4a3 3 0 0 1 3 3 3 3 0 0 1 1.5 5.6A3 3 0 0 1 17 17a3 3 0 0 1-5.5 1.7V6"/></svg>',
    "users": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="8" r="3.2"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/><circle cx="17.5" cy="9" r="2.6"/><path d="M15.5 14.3c2.6.4 4.5 2.6 4.5 5.7"/></svg>',
    "heart-hand": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12l4 4 6-6"/><path d="M13 6l8 8"/></svg>',
    "pin": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s7-6.5 7-11.5A7 7 0 0 0 5 9.5C5 14.5 12 21 12 21Z"/><circle cx="12" cy="9.5" r="2.3"/></svg>',
    "mail": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>',
    "phone": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5c0 8.3 6.7 15 15 15l3-4-6-3-2 2c-2.4-1.2-4.3-3.1-5.5-5.5l2-2-3-6-4 .5"/></svg>',
    "clock": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/></svg>',
    "quote": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 7c-2.2 0-4 1.8-4 4 0 2 1.4 3.7 3.3 4-.2 2-1.6 3-3.3 3.4V21c3.6-.4 6-2.9 6-6.6V11c0-2.2-.9-4-2-4Zm10 0c-2.2 0-4 1.8-4 4 0 2 1.4 3.7 3.3 4-.2 2-1.6 3-3.3 3.4V21c3.6-.4 6-2.9 6-6.6V11c0-2.2-.9-4-2-4Z"/></svg>',
}


def icon(name: str, css_class: str = "") -> str:
    svg = ICONS.get(name, ICONS["target"])
    if css_class:
        svg = svg.replace("<svg ", f'<svg class="{css_class}" ', 1)
    return svg


def load_json(name: str):
    with open(CONTENT / f"{name}.json", encoding="utf-8") as f:
        return json.load(f)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# Component renderers — turn content/*.json into markup fragments.
# --------------------------------------------------------------------------

def render_trust_bar() -> str:
    items = load_json("trust-bar")
    out = []
    for it in items:
        chip_class = "icon-chip icon-chip--saffron" if it.get("variant") == "saffron" else "icon-chip icon-chip--dark"
        out.append(f"""
        <div class="trust-item" data-reveal>
          <span class="{chip_class}">{icon(it['icon'])}</span>
          <span class="trust-item__text">
            <span class="trust-item__label">{it['label']}</span>
            <span class="trust-item__detail">{it['detail']}</span>
          </span>
        </div>""")
    return "".join(out)


def render_philosophy() -> str:
    pillars = load_json("philosophy")
    out = []
    for p in pillars:
        out.append(f"""
        <div class="philosophy-pillar" data-reveal tabindex="0">
          <span class="philosophy-pillar__index">{p['index']}</span>
          <span class="philosophy-pillar__name">{p['name']}</span>
          <p class="philosophy-pillar__summary">{p['summary']}</p>
          <p class="philosophy-pillar__detail">{p['detail']}</p>
        </div>""")
    return "".join(out)


def render_pathway(variant="home") -> str:
    stages = load_json("pathway")
    out = []
    for s in stages:
        stage_class = ""
        if s["key"] == "coe":
            stage_class = " pathway-stage--coe"
        elif s["key"] == "feeder":
            stage_class = " pathway-stage--feeder"
        objectives = "".join(f"<li>{o}</li>" for o in s["objectives"])
        out.append(f"""
        <div class="pathway-stage{stage_class}" data-reveal>
          <div class="pathway-stage__head">
            <span class="pathway-stage__num">{s['stage']}</span>
            <span class="pathway-stage__age">{s['ageRange']}</span>
          </div>
          <div>
            <h3 class="pathway-stage__name">{s['name']}</h3>
            <span class="pathway-stage__tag">{s['tagline']}</span>
          </div>
          <p class="pathway-stage__summary">{s['summary']}</p>
          <ul class="pathway-stage__list">{objectives}</ul>
          <div class="pathway-stage__meta">
            <div class="pathway-stage__meta-row"><span>Intensity</span><span>{s['intensity']}</span></div>
            <div class="pathway-stage__meta-row"><span>Evaluation</span><span>{s['evaluation']}</span></div>
            <div class="pathway-stage__meta-row"><span>Progression</span><span>{s['progression']}</span></div>
          </div>
        </div>""")
    return "".join(out)


def render_afa_credentials() -> str:
    creds = load_json("afa-credentials")
    out = []
    for c in creds:
        out.append(f"""
        <div class="afa-credential" data-reveal>
          <div class="afa-credential__value" data-counter="{re.sub('[^0-9.]', '', c['value']) or 0}" data-suffix="×">0×</div>
          <div class="afa-credential__label">{c['label']}</div>
          <div class="afa-credential__detail">{c['detail']}</div>
        </div>""")
    return "".join(out)


def render_performance_metrics() -> str:
    metrics = load_json("performance-metrics")
    out = []
    for m in metrics:
        out.append(f"""
        <div class="metric-row">
          <div class="metric-row__head"><strong>{m['label']}</strong><span>{m['value']}/100</span></div>
          <div class="metric-bar"><div class="metric-bar__fill" data-bar="{m['value']}"></div></div>
        </div>""")
    return "".join(out)


def radar_chart_svg() -> str:
    metrics = load_json("performance-metrics")
    n = len(metrics)
    # Generous viewBox margin around the label ring so long labels (e.g.
    # "Match Impact") never clip against the SVG edge at any angle.
    cx, cy, r = 230, 230, 128
    size = 460
    import math
    def point(i, value, radius=r):
        angle = -math.pi / 2 + i * (2 * math.pi / n)
        val_r = radius * (value / 100)
        return (cx + val_r * math.cos(angle), cy + val_r * math.sin(angle))
    def ring_point(i, radius=r):
        angle = -math.pi / 2 + i * (2 * math.pi / n)
        return (cx + radius * math.cos(angle), cy + radius * math.sin(angle))

    rings = []
    for frac in (0.33, 0.66, 1.0):
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (ring_point(i, r * frac) for i in range(n)))
        rings.append(f'<polygon points="{pts}" fill="none" stroke="rgba(255,255,255,0.14)" stroke-width="1"/>')

    spokes = "".join(
        f'<line x1="{cx}" y1="{cy}" x2="{ring_point(i)[0]:.1f}" y2="{ring_point(i)[1]:.1f}" stroke="rgba(255,255,255,0.1)"/>'
        for i in range(n)
    )

    data_points = [point(i, m["value"]) for i, m in enumerate(metrics)]
    data_pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in data_points)
    markers = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="#0A2049" stroke="#D4AF37" stroke-width="1.6"/>'
        for x, y in data_points
    )

    labels = []
    for i, m in enumerate(metrics):
        lx, ly = ring_point(i, r + 34)
        anchor = "middle"
        if lx < cx - 24:
            anchor = "end"
        elif lx > cx + 24:
            anchor = "start"
        labels.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" dominant-baseline="middle" font-family="Poppins, sans-serif" font-size="12" font-weight="600" fill="rgba(255,255,255,0.8)">{m["label"]}</text>'
        )

    return f"""<svg viewBox="0 0 {size} {size}" role="img" aria-label="Illustrative player development radar chart">
  <defs>
    <linearGradient id="radarFill" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#D4AF37" stop-opacity="0.55"/>
      <stop offset="1" stop-color="#F7D878" stop-opacity="0.28"/>
    </linearGradient>
  </defs>
  {''.join(rings)}
  {spokes}
  <polygon points="{data_pts}" fill="url(#radarFill)" stroke="#D4AF37" stroke-width="2" stroke-linejoin="round"/>
  {markers}
  {''.join(labels)}
</svg>"""


def render_success_stories() -> str:
    stories = load_json("success-stories")
    out = []
    for s in stories:
        flag = '<span class="note-flag">Sample format</span>' if s.get("placeholder") else ""
        out.append(f"""
        <div class="card story-card" data-reveal>
          {flag}
          <div class="story-card__path">{icon('arrow-right')}<span>{s['from']}</span>{icon('arrow-right')}<span>{s['to']}</span></div>
          <p class="story-card__quote">{icon('quote', 'quote-mark')} {s['quote']}</p>
          <div class="story-card__foot"><span>{s['name']}</span><span>{s['location']}</span></div>
        </div>""")
    return "".join(out)


def render_parent_faq() -> str:
    faqs = load_json("parent-faq")
    out = []
    for i, f in enumerate(faqs):
        open_state = " is-open" if i == 0 else ""
        max_h = "1000px" if i == 0 else None
        style = f' style="max-height:{max_h}"' if max_h else ""
        expanded = "true" if i == 0 else "false"
        out.append(f"""
      <div class="accordion-item{open_state}" data-reveal>
        <button class="accordion-trigger" aria-expanded="{expanded}">
          <span>{f['q']}</span>
          <span class="accordion-trigger__icon" aria-hidden="true"></span>
        </button>
        <div class="accordion-panel"{style}>
          <div class="accordion-panel__inner">{f['a']}</div>
        </div>
      </div>""")
    return "".join(out)


def render_news(limit=None) -> str:
    news = load_json("news")
    if limit:
        news = news[:limit]
    out = []
    for n in news:
        flag = '<span class="note-flag">Coming soon</span>' if n.get("placeholder") else ""
        out.append(f"""
        <article class="card news-card" data-reveal>
          <div class="news-card__media">{flag and f'<div style="position:absolute;top:14px;left:14px;">{flag}</div>'}</div>
          <div class="news-card__body">
            <span class="pill">{n['category']}</span>
            <h3 class="news-card__title">{n['title']}</h3>
            <p class="news-card__excerpt">{n['excerpt']}</p>
            <div class="news-card__meta"><span class="caption">{n['date']}</span></div>
          </div>
        </article>""")
    return "".join(out)


def render_programmes() -> str:
    programmes = load_json("programmes")
    out = []
    for p in programmes:
        out.append(f"""
        <div class="card programme-card" data-reveal>
          <span class="programme-card__index">{p['key'].upper()}</span>
          <h3 class="programme-card__title">{p['name']}</h3>
          <span class="programme-card__audience">{p['audience']}</span>
          <p class="programme-card__body">{p['summary']}</p>
          <a class="programme-card__cta" href="programmes.html#{p['key']}">{p['cta']} {icon('arrow-right')}</a>
        </div>""")
    return "".join(out)


# --------------------------------------------------------------------------
# Page registry
# --------------------------------------------------------------------------

PAGES = [
    dict(slug="index", nav="home", title="Amuzi Centre of Excellence | AFA Methodology. International Pathway. Indian Player Development.",
         description="AFA methodology, an international football pathway and Indian player development — from feeder centres to the Amuzi Centre of Excellence, our flagship destination."),
    dict(slug="about", nav="about", title="About | Amuzi Centre of Excellence",
         description="Amuzi Centre of Excellence is building India's structured football development ecosystem — feeder centres, intermediate centres and our flagship Centre of Excellence, powered by AFA methodology."),
    dict(slug="programmes", nav="programmes", title="Programmes | Amuzi Centre of Excellence",
         description="Explore the full programme architecture — Feeder Centres, Intermediate Centres, the Centre of Excellence, Beti Khilao and school partnerships."),
    dict(slug="intermediate-centres", nav="feeder", title="Intermediate Centres | Amuzi Centre of Excellence",
         description="AFA-affiliated Intermediate Centres bring AFA curriculum and methodology to centres across India, forming the structured bridge to the Centre of Excellence."),
    dict(slug="centre-of-excellence", nav="coe", title="Centre of Excellence | Amuzi Flagship Destination",
         description="The Amuzi Centre of Excellence is India's flagship elite football performance environment — coaching, sports science and international exposure under AFA methodology."),
    dict(slug="afa-partnership", nav="afa", title="AFA Partnership | Amuzi Centre of Excellence x Argentine Football Association",
         description="How the Argentine Football Association's methodology shapes the player development pathway toward the Amuzi Centre of Excellence."),
    dict(slug="news", nav="news", title="News | Amuzi Centre of Excellence",
         description="Updates on the AFA partnership, our network and player development programme."),
    dict(slug="contact", nav="contact", title="Contact & Enquiries | Amuzi Centre of Excellence",
         description="Start the conversation — player and parent enquiries, school partnerships and corporate partnership enquiries."),
    dict(slug="privacy-policy", nav="", title="Privacy Policy | Amuzi Centre of Excellence",
         description="How Amuzi Centre of Excellence collects, uses and protects personal data."),
    dict(slug="terms", nav="", title="Terms & Conditions | Amuzi Centre of Excellence",
         description="Terms and conditions for use of this website and its programmes."),
    dict(slug="safeguarding", nav="", title="Safeguarding | Amuzi Centre of Excellence",
         description="Our commitment to safeguarding every young player in our programmes."),
]

ICON_ALIASES = {
    "ARROW": "arrow-right",
    "CAP": "cap",
    "BUILDING": "building",
    "NETWORK": "network",
    "TREND": "trend",
    "BRAIN": "brain",
    "GLOBE": "globe",
    "SHIELD": "shield",
    "USERS": "users",
    "PIN": "pin",
    "MAIL": "mail",
    "PHONE": "phone",
    "CLOCK": "clock",
    "CHECK": "check-circle",
    "VIDEO": "video",
    "CHART": "chart",
    "TARGET": "target",
    "WHISTLE": "whistle",
    "FLAG": "flag",
    "HEART": "heart-hand",
}

NAV_KEYS = {
    "home": "NAV_HOME_CURRENT", "about": "NAV_ABOUT_CURRENT", "programmes": "NAV_PROGRAMMES_CURRENT",
    "feeder": "NAV_FEEDER_CURRENT", "coe": "NAV_COE_CURRENT", "afa": "NAV_AFA_CURRENT",
    "news": "NAV_NEWS_CURRENT", "contact": "NAV_CONTACT_CURRENT",
}

COMPONENT_SLOTS = {
    "{{TRUST_BAR}}": render_trust_bar,
    "{{PHILOSOPHY_PILLARS}}": render_philosophy,
    "{{PATHWAY_STAGES}}": render_pathway,
    "{{AFA_CREDENTIALS}}": render_afa_credentials,
    "{{PERFORMANCE_METRICS}}": render_performance_metrics,
    "{{RADAR_CHART}}": radar_chart_svg,
    "{{SUCCESS_STORIES}}": render_success_stories,
    "{{PARENT_FAQ}}": render_parent_faq,
    "{{NEWS_CARDS}}": lambda: render_news(),
    "{{NEWS_CARDS_3}}": lambda: render_news(3),
    "{{PROGRAMME_CARDS}}": render_programmes,
}


def build():
    base = read(SRC / "base.html")
    header_tpl = read(SRC / "partials" / "header.html")
    footer_tpl = read(SRC / "partials" / "footer.html")

    for page in PAGES:
        page_path = SRC / "pages" / f"{page['slug']}.html"
        content = read(page_path)

        # Inject reusable data-driven components
        for slot, renderer in COMPONENT_SLOTS.items():
            if slot in content:
                content = content.replace(slot, renderer())

        # Inject inline icons: {{ICON_NAME}} -> icon('name')
        content = re.sub(
            r"\{\{ICON_([A-Z0-9_]+)\}\}",
            lambda m: icon(ICON_ALIASES.get(m.group(1), m.group(1).lower().replace("_", "-"))),
            content,
        )

        # Header with correct active nav state
        header = header_tpl
        for key, marker in NAV_KEYS.items():
            header = header.replace("{{" + marker + "}}", 'aria-current="page"' if key == page["nav"] else "")

        html = base
        html = html.replace("{{TITLE}}", page["title"])
        html = html.replace("{{DESCRIPTION}}", page["description"])
        html = html.replace("{{CANONICAL}}", f"{SITE_URL}/{page['slug']}.html".replace("/index.html", "/"))
        html = html.replace("{{BODY_CLASS}}", f"page-{page['slug']}")
        html = html.replace("{{HEADER}}", header)
        html = html.replace("{{FOOTER}}", footer_tpl)
        html = html.replace("{{CONTENT}}", content)
        html = html.replace("{{EXTRA_HEAD}}", "")
        html = html.replace("{{JSONLD}}", json.dumps({
            "@context": "https://schema.org",
            "@type": "SportsOrganization",
            "name": "Amuzi Centre of Excellence",
            "url": SITE_URL,
            "sport": "Football",
            "description": page["description"],
        }))

        out_path = ROOT / f"{page['slug']}.html"
        out_path.write_text(html, encoding="utf-8")
        print(f"built {out_path.name}")

    write_sitemap()
    write_robots()


def write_sitemap():
    urls = []
    for page in PAGES:
        loc = f"{SITE_URL}/{page['slug']}.html".replace("/index.html", "/")
        urls.append(f"  <url><loc>{loc}</loc></url>")
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>\n"
    (ROOT / "sitemap.xml").write_text(xml, encoding="utf-8")


def write_robots():
    txt = f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n"
    (ROOT / "robots.txt").write_text(txt, encoding="utf-8")


if __name__ == "__main__":
    build()
