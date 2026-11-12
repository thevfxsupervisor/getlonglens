#!/usr/bin/env python3
"""Build getlonglens.com: plain HTML pages from the copy in this file, one shared header and
footer. Standard library only. Run `python3 build.py` from the repo root; it writes each page as
<slug>/index.html (the home page as index.html, plus 404.html) and `preview.html`, one
self-contained file with every page in it (CSS and media inlined) for review. The output is
committed, so GitHub Pages serves it with no build step. preview.html is git-ignored.

Every product claim here comes from the LongLens page and guide on thevfxsupervisor.com
(content/pages/longlens*.md) or the app (~/projects/newsletter). Anything not live today carries
the "coming" tag. Change the copy here, rebuild, commit the output.
"""

from __future__ import annotations

import base64
import html
import json
import mimetypes
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = "https://getlonglens.com"
APP = "https://newsletter-edge.thevfxsupervisor.workers.dev"
SIGNIN = APP + "/login"
APP_PRIVACY = APP + "/privacy"
DAILY = "https://thevfxsupervisor.com/daily/"
GEOFF_SITE = "https://thevfxsupervisor.com/"
EMAIL = "geoff@wanglemedia.com"
# Who runs LongLens (Geoff 2026-11-12: the address may be published; no phone number on the site).
COMPANY = "Hedge Holding ApS"
CVR = "41583290"
COMPANY_ADDRESS = "Bakkevej 8, 3050 Humleb\u00e6k, Denmark"
IDENTITY = f"LongLens is run by {COMPANY}, CVR {CVR}, {COMPANY_ADDRESS}."

# The inquiry form posts to the app's endpoint (POST /hooks/inquiry), which accepts
# https://getlonglens.com (NL_INQUIRY_ORIGINS). Set FORM_LIVE to False to fall back to email only.
FORM_LIVE = True
INQUIRY_ENDPOINT = APP + "/hooks/inquiry"
# The wording of the small print under the start form's button. The app keeps a table of what each
# version said (accounts/first_issue.py CONSENT_TEXTS): change the words, change this too.
CONSENT_VERSION = "consent-2026-11-07"
INQUIRY_CONSENT = "I agree to be contacted about this message at the email address I gave."
# Cloudflare Turnstile on the form (the app checks the token when NL_TURNSTILE_SECRET is set).
# The site key is PUBLIC; paste it from Cloudflare > Turnstile > the getlonglens.com widget.
# Empty = no widget is rendered and the page is exactly as before. Deploy order: the app first,
# then this key here, then the secret in nl.env LAST (a widget the app does not check is
# harmless; an app that checks with no widget on the page refuses every post).
TURNSTILE_SITE_KEY = "0x4AAAAAAF2l6EOGFK5dERe5"
TURNSTILE_ACTION = "start"  # must match newsletter.turnstile.FORM_ACTION in the app
# Geoff 2026-11-06: the sources box stays optional (topics are required). True makes it
# required; flip the app's newsletter.inquiry.SOURCES_REQUIRED to match, or the app accepts
# what the page refuses.
# DEPLOY ORDER for the three-field start form (inquiry_form below): the APP first (branch
# signup-one-step, with `nl db upgrade` to alembic e3a9c6b1d047), then this site. An app older
# than that refuses every post from this form (no name, no message, no checkbox) with a page
# asking for fields the visitor cannot see, and nothing is stored or mailed. The app accepts the
# older form too, so app-first is safe in both directions.
SOURCES_REQUIRED = False
# Geoff 2026-11-06: the start form writes the first issue at once; no start link to click first.
# The minutes come from a measurement on 2026-11-06 (scratch instance, real model calls, fake
# mailer): 27 s and 122 s from sending the form to the first issue. 5 leaves room for a queue of
# sign-ups and the job starting. Change it here only after a new measurement. DEPLOY ORDER: the app first (it sends the visitor to the new thanks page
# below), then this site; this site with an older app would promise an issue that never comes.
FIRST_ISSUE_MINUTES = 5

# THE ONE PRICE SOURCE (SEO pass 2026-11-08). Every visible price, the JSON-LD Offers and llms.txt
# come from here, and check_output() refuses any "$n" on a page that is not one of these. The one
# copy outside this file: assets/og-card.png shows the Solo price in pixels, so remake it when
# PRICE_SOLO changes (and bump OG_VERSION so social sites fetch the new card).
PRICE_FREE, PRICE_SOLO, PRICE_BUSINESS = 0, 19, 95
CURRENCY = "USD"
FREE_DAYS = 7
OFFER_LINE = f"Free for a week, then from ${PRICE_SOLO} a month"
OG_VERSION = "2026-11-08"
# The plain definition, said the same way on the home page, the FAQ, the JSON-LD and llms.txt.
DEFINITION = ("LongLens is an AI newsletter service for businesses. LongLens finds what changed in your "
              "field and tells your clients what it means, under your name only. The Email, Podcast, Reel, "
              "Infographic, Carousel and Explainer video are all part of the issue. Every issue comes to you "
              "first, and you make it yours on the page before you send it.")
YOUTUBE = "https://www.youtube.com/@getlonglens"
# Cloudflare Web Analytics (Geoff approved 2026-11-08). The token is PUBLIC, not a secret. It goes on
# every generated page, 404 included, and never in preview.html. Cloudflare: the beacon "does not use
# any client-side state, such as cookies or localStorage" (cloudflare.com/web-analytics, read
# 2026-11-08), which is why the site may still say it sets no cookies. Empty = no beacon.
CF_BEACON_TOKEN = "1f336ebfe8c4455d866eefbd78962e59"
CF_BEACON = (f"""<script defer src="https://static.cloudflareinsights.com/beacon.min.js" """
             f"""data-cf-beacon='{{"token": "{CF_BEACON_TOKEN}"}}'></script>""" if CF_BEACON_TOKEN else "")
ORG_ID = SITE + "/#org"
PERSON_ID = GEOFF_SITE + "#person"

NAV = [("Features", "/features/"), ("Pricing", "/pricing/"), ("How it works", "/how-it-works/"),
       ("FAQ", "/faq/")]
CTA_LABEL = "Free week"


def mailto(subject: str, body: str = "") -> str:
    from urllib.parse import quote
    q = "subject=" + quote(subject)
    if body:
        q += "&body=" + quote(body)
    return f"mailto:{EMAIL}?{q}"


CALL_MAIL = mailto(
    "LongLens: a free week for my business",
    "Who reads my newsletter (or should), and what should they hear from me first?\n\n\n"
    "My name:\nMy business:\n",
)


OWN_LINE = "Every issue carries your name and only yours, never ours, and we match the look to your brand when you start."
# MUST 2 (2026-11-07): existing clients can be added in the app (existing_client.py, web/clients_pages.py):
# one required tick box, the From name is the owner's sender name, every letter carries a one-click stop
# link and List-Unsubscribe, and nothing goes out until the owner approves the issue. The From ADDRESS is
# the tenant's mail domain set up by the operator, so never claim "from your own address". Sending needs
# the operator's setup (DPA on record, network sends switched on): SEND_SETUP says so.
CLIENT_LINE = "Add your existing clients with a single tick, and LongLens sends them each issue you sign off, with only your name on it and a one-click opt-out in every email."
CLIENT_LINE_FIRM = CLIENT_LINE.replace("only your name", "only your firm's name")
SEND_SETUP = "We switch sending on with you when you start."
LINK_LINE = "Every story links to its original."
AI_LINE = "AI drafts each issue from the news you trust, and every story links to its original. Every issue comes to you first, and you change what you like before you send it, so it sounds like you."


def coming(text: str = "") -> str:
    tag = '<span class="tag-coming">coming</span>'
    return f"{tag} {text}" if text else tag


# --------------------------------------------------------------------------------------------
# Shared pieces
# --------------------------------------------------------------------------------------------

CUR = ' aria-current="page"'


def header(current: str, signin: bool = True) -> str:
    links = "".join(
        f'<a href="{href}"{CUR if href == current else ""}>{label}</a>'
        for label, href in NAV
    )
    signin_link = '<a href="/sign-in/">Sign in</a>' if signin else ""
    # Under 860px the nav folds into a <details> menu (no script); over it, the nav is one row.
    return f'''<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <div class="wrap">
    <a class="brand" href="/" aria-label="LongLens home"><img src="/assets/mark-e1.svg" alt="" width="32" height="32"><span>LongLens</span></a>
    <nav class="main" aria-label="Main">{links}{signin_link}<a class="btn btn-a" href="/contact/">{CTA_LABEL}</a></nav>
    <a class="btn btn-a hdr-cta" href="/contact/">{CTA_LABEL}</a>
    <details class="menu"><summary aria-label="Menu"><svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true"><path d="M3 6h14M3 10h14M3 14h14" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg></summary>
      <nav aria-label="Menu">{links}{signin_link}</nav></details>
  </div>
</header>'''


def footer() -> str:
    links = "".join(f'<a href="{h}">{l}</a>' for l, h in NAV)
    return f'''<footer>
  <div class="wrap">
    <div>
      <p class="by">LongLens (getlonglens.com). Built by <a href="{GEOFF_SITE}">Geoffrey Hancock</a>.</p>
      <p class="tiny">No cookies on this site. Visits are counted with Cloudflare Web Analytics.</p>
      <p class="tiny idline">{IDENTITY}</p>
    </div>
    <nav aria-label="Footer">{links}<a href="/for-accountants/">For accountants</a><a href="/contact/">Free week</a><a href="/sign-in/">Sign in</a><a href="/privacy/">Privacy</a><a href="/terms/">Terms</a></nav>
  </div>
</footer>'''


# Headline line breaks. In a heading's copy, "|" marks a place where a line may break: between
# phrases, never inside one ("up to date,|without costing you hours"); "^" marks a weaker break
# inside a phrase, taken only when the whole phrase will not fit. Each phrase becomes an
# inline-block (.ph in site.css), so a line breaks only between phrases; a phrase longer than a
# phone line still wraps inside itself (balanced) rather than overflowing. The marks never reach
# the page; the visible text is unchanged.
_HEADING = re.compile(r"(<h([123])\b[^>]*>)(.*?)(</h\2>)", re.S)


def phrase_chunks(body: str) -> str:
    def one(m):
        inner = m.group(3)
        if "|" not in inner:
            return m.group(0)
        assert "<" not in inner, "phrase marks only in plain-text headings: " + inner
        def chunk(p):
            subs = [q.strip() for q in p.split("^")]
            inside = " ".join(f'<span class="ph">{q}</span>' for q in subs) if len(subs) > 1 else subs[0]
            return f'<span class="ph">{inside}</span>'
        return m.group(1) + " ".join(chunk(p.strip()) for p in inner.split("|")) + m.group(4)
    out = _HEADING.sub(one, body)
    assert not re.search(r"[|^]", "".join(m.group(3) for m in _HEADING.finditer(out))), "stray mark in a heading"
    return out


def page(slug: str, title: str, description: str, body: str, current: str = "",
         robots: str = "", signin: bool = True, graph: list | None = None) -> str:
    path = "/" if slug == "" else f"/{slug}/"
    canonical = SITE + path
    # The 404 page has no URL of its own (GitHub Pages serves it at any missing path): no canonical.
    canonical_tag = "" if slug == "404" else f'\n<link rel="canonical" href="{canonical}">'
    if slug == "404":
        canonical = SITE + "/"
    robots_tag = f'\n<meta name="robots" content="{robots}">' if robots else ""
    ld_tag = "\n" + ld(graph) if graph else ""
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="google-site-verification" content="YgmFLbLdiFc4zNjw-3vSVNpJbJmgxIqkL6glHpnmsYw">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">{canonical_tag}{robots_tag}
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#f4efe6">
<meta name="theme-color" media="(prefers-color-scheme: dark)" content="#131619">
<meta property="og:type" content="website">
<meta property="og:site_name" content="LongLens">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE}/assets/og-card.png?v={OG_VERSION}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(title)}">
<meta name="twitter:description" content="{html.escape(description)}">
<meta name="twitter:image" content="{SITE}/assets/og-card.png?v={OG_VERSION}">
<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">
<link rel="icon" type="image/png" sizes="64x64" href="/assets/favicon-64.png">
<link rel="apple-touch-icon" sizes="180x180" href="/assets/apple-touch-icon.png">
<link rel="stylesheet" href="/assets/site.css">
<link rel="alternate" type="text/markdown" href="/llms.txt" title="LongLens in plain text">{ld_tag}
</head>
<body>
{header(current, signin)}
<main id="main">
{phrase_chunks(body)}
</main>
{footer()}{mobile_bar(slug, body)}
{CF_BEACON}
</body>
</html>
'''


# Sticky start bar on phones (Geoff 2026-11-12): the page's own hero button (label and target),
# or the home page's when the hero has none. It is `hidden` in the HTML, so with no script it is
# simply absent; the script shows it once the hero button (or the H1) has scrolled up out of view,
# and hides it again while the start form, the closing call to action or the footer is on screen.
# Over 760px the CSS never shows it. Not on the form page itself or the plain pages.
MBAR_SKIP = {"contact", "sign-in", "privacy", "terms", "thanks", "contact/thanks-first-issue",
             "contact/thanks-personal", "404"}
MBAR_JS = """<script>(function(){var b=document.getElementById("mbar");if(!b||!("IntersectionObserver"in window))return;
var t=document.querySelector("main .hero .btn-a")||document.querySelector("main h1");if(!t)return;
var past=false,near=[].slice.call(document.querySelectorAll("form.contact-card,.close .btn,footer"));
function set(){var n=near.some(function(x){return x._in});b.classList.toggle("on",past&&!n)}
b.hidden=false;document.body.classList.add("has-mbar");
new IntersectionObserver(function(e){e=e[e.length-1];past=!e.isIntersecting&&e.boundingClientRect.top<0;set()}).observe(t);
var io=new IntersectionObserver(function(es){es.forEach(function(e){e.target._in=e.isIntersecting});set()});
near.forEach(function(x){io.observe(x)})})();</script>"""


def mobile_bar(slug: str, body: str) -> str:
    if slug in MBAR_SKIP:
        return ""
    hero = re.search(r'<section class="hero[^"]*">(.*?)</section>', body, re.S)
    m = hero and re.search(r'<a class="btn btn-a[^"]*" href="([^"]+)">([^<]+)</a>', hero.group(1))
    href, label = (m.group(1), m.group(2)) if m else ("/contact/", CTA_TEXT)
    return (f'\n<div class="mbar" id="mbar" hidden><a class="btn btn-a" href="{href}">{label}</a></div>'
            f"\n{MBAR_JS}")


CTA_TEXT = "See what your clients would hear from you, free"
HERO_OFFER = f"AI writes the first version, you make it yours, and only your name is on it. {OFFER_LINE}."


def close_cta(h2: str, text: str, cta: str = "") -> str:
    return f'''<section class="close">
  <div class="wrap"><div>
    <div><h2>{h2}</h2>
    <p class="k">{text}</p></div>
    <div class="cta-row"><a class="btn btn-a btn-lg" href="/contact/">{cta or CTA_TEXT}</a></div>
  </div></div>
</section>'''


M = "/assets/media/"


def pic(src: str, w: int, h: int, alt: str, attrs: str = "") -> str:
    """A PNG with its WebP sibling (same name, .webp) offered first. Width and height stay on the
    <img>, so the box is reserved before either file loads."""
    webp = src.rsplit(".", 1)[0] + ".webp"
    return (f'<picture><source type="image/webp" srcset="{webp}">'
            f'<img src="{src}" width="{w}" height="{h}"{attrs} alt="{alt}"></picture>')

EXAMPLE_LABEL = "Geoff's own newsletter about his own field, visual effects for film and TV"

# One name per format, used on every page (term map: newsletter-samples/research/
# media-audit-2026-11-07/TERMS-MAP.md). "Reel" is our label for the format, never a product name.
F_EMAIL, F_POD, F_REEL, F_EXPL, F_INFO, F_CAR = (
    "Email", "Podcast", "Reel", "Explainer video", "Infographic", "Carousel")

# What a reader can count on, per format (app media ladder, 2026-11-08): the Email goes out with
# every issue; the Podcast (two AI voices, else one AI voice reading), the Reel and the Infographic
# are attempted for every issue but can be left off (no public story in the issue, or not right);
# the Carousel was switched on 2026-11-08 with no track record yet, and the Explainer video has no
# fallback when the shared allowance runs out. Never "every issue" for anything but the Email.
FORMAT_LADDER = (f"The {F_EMAIL}, {F_POD}, {F_REEL}, {F_INFO}, {F_CAR} and {F_EXPL} are all part of the issue.")

FORMAT_STRIP = f'''<div class="fmt-strip" role="list" aria-label="One issue in five formats, real examples">
  <div class="fmt-card" role="listitem"><div class="fmt-media"><a href="https://thevfxsupervisor.com/daily/20/">{pic(M + "read-letter.png", 780, 1276, "A real issue of The VFX Supervisor Daily as it arrives by email", ' loading="lazy"')}</a></div>
    <div class="fmt-txt"><b>{F_EMAIL}</b><p>What changed and what it means, in two minutes.</p></div></div>
  <div class="fmt-card" role="listitem"><div class="fmt-media audio"><img class="wave" src="{M}issue-audio-wave.png" width="780" height="352" loading="lazy" alt="The sound wave of the audio clip below.">
    <audio controls preload="none" src="{M}issue-audio.m4a" aria-label="The first 16 seconds of the issue's Podcast"></audio></div>
    <div class="fmt-txt"><b>{F_POD}</b><p>Two AI voices talk the issue through, or one AI voice reads it.</p><p class="fmt-date">The first 16 seconds</p></div></div>
  <div class="fmt-card" role="listitem"><div class="fmt-media"><a href="{M}issue-infographic.jpg"><img src="{M}issue-infographic.jpg" width="1080" height="1350" loading="lazy" alt="An Infographic of a whole issue: the headline, then one line on what each story means, with its source."></a></div>
    <div class="fmt-txt"><b>{F_INFO}</b><p>The whole issue on one image.</p></div></div>
  <div class="fmt-card" role="listitem"><div class="fmt-media wide"><video controls preload="none" playsinline poster="{M}issue-explainer-poster.jpg" src="{M}issue-explainer.mp4" width="640" height="360" aria-label="The first 15 seconds of an Explainer video"></video></div>
    <div class="fmt-txt"><b>{F_EXPL}</b><p>A few narrated minutes, a drawing for each point.</p><p class="fmt-date">The first 15 seconds of 7 minutes</p></div></div>
  <div class="fmt-card" role="listitem"><div class="fmt-media"><video controls preload="none" playsinline poster="{M}issue-short-poster.jpg" src="{M}issue-short.mp4" width="540" height="960" aria-label="The first 15 seconds of a Reel, a short vertical video"></video></div>
    <div class="fmt-txt"><b>{F_REEL}</b><p>Captioned vertical video, sized for Instagram Reels, TikTok and YouTube Shorts.</p><p class="fmt-date">The first 15 seconds</p></div></div>
</div>
<p class="fmt-hint">{FORMAT_LADDER} Yours is about your field.</p>'''

EDITOR_SHOT = f'''<figure class="shot"><a href="{M}edit-in-place.png"><img src="{M}edit-in-place.png" width="1100" height="770" loading="lazy" alt="The LongLens editor open on a real issue: a bar with Save, Discard and the inbox preview line on top, and every line of the issue below outlined, ready to click and change."></a><figcaption>The real editor, open on a real issue.</figcaption></figure>'''

PROOF = f'''<div class="proof">
  <h3>Who built LongLens</h3>
  <p>Geoffrey Hancock, VES Award winner for Changeling, built LongLens and runs his own newsletter on it. Yours covers your field.</p>
  <a class="txtlink" href="{DAILY}">Read The VFX Supervisor Daily</a>
</div>'''

# Sample issues for other kinds of business. Each: (image, alt, what it is, date, link or "").
# The section renders only when this list has entries, so nothing placeholder is ever published.
SAMPLES = [
    ("dk-accounting", "Client Update", "For the clients of a Copenhagen accounting firm",
     "Corporate tax overpayment window closes soon, and new EU parcel fees add to import costs",
     "The dates your clients must act on come first, so the deadline is the first thing they see."),
    ("ux-research", "Research Notes", "For the prospects of an independent UX researcher",
     "AI moderators and synthetic users: early data says use them for practice, not evidence",
     "Prospects see that you know where AI research is heading, a few lines on each story."),
    ("bakery", "The Proving Room", "For the members of a bakery owners\' community",
     "Cocoa has fallen, but your costs may not follow soon",
     "Members scan the headlines, and see what falling cocoa prices mean for their costs."),
]


def samples_section() -> str:
    if not SAMPLES:
        return ""
    cards = "".join(
        f'<div class="fmt-card" role="listitem"><div class="fmt-media">'
        f'<a href="/samples/{slug}/"><img src="/assets/samples/{slug}-top.png" width="600" height="900" loading="lazy" '
        f'alt="The top of {html.escape(name)}, a sample issue: {html.escape(headline)}"></a></div>'
        f'<div class="fmt-txt"><b>{html.escape(name)}</b><p>{html.escape(who)}.</p><a class="txtlink" href="/samples/{slug}/">Read the issue</a></div></div>'
        for slug, name, who, headline, how in SAMPLES)
    return f'''<hr class="rule">
<section id="samples">
  <div class="wrap">
    <div class="sec-head">      <h2>Your clients get|what the news means for them,|not a pile of links</h2>
      <p>Three example businesses, three issues LongLens wrote from real news.</p></div>
    <div class="fmt-strip samples" role="list" aria-label="Sample issues for other businesses">{cards}</div>
  </div>
</section>'''


TODAY_PLACES = ("Your inbox first, then your existing clients' inboxes, with a one-click opt-out in every email",
                "A web page for every issue you publish",
                "Every issue on one web page, like a blog, with your name on it",
                "Your Slack or Discord channel",
                "A private RSS feed")
COMING_PLACES = ("Your Podcast in podcast apps",
                 "Your Reel and Carousel ready to post to your own Instagram, LinkedIn and TikTok",
                 "A block on your website", "Telegram")

# The home headline's two rotating words: the audience and the verb. The H1's TEXT is always one
# plain sentence, "Your clients hear the news from you.": the first word of each group is a real,
# visually hidden text node (.rot-txt). The words you SEE are drawn by CSS from data-w
# (site.css .rot>span[data-w]::before) on aria-hidden spans with no text, so neither innerText,
# textContent, the accessibility tree nor a rendering crawler ever reads the rotation (BREAK S3,
# 2026-11-08). No-script visitors still see the first words. The script adds the other words from
# data-words the same way: absolutely placed and invisible until shown, so adding them moves nothing. Reduced motion still swaps the words, as a plain fade with no movement.
# Each box is the width of the word showing, so a short word leaves no gap; site.css caps the font
# so the longest pair still fits one line and the headline never changes its line count.
# Every pair makes a complete, true sentence: "Your ___ ___ the news from you."
ROT = ("clients", "prospects", "members", "customers", "readers")
ROT_VERBS = ("hear", "read", "watch")


def rot_group(words, cls: str = "rot") -> str:
    assert all("," not in w and "|" not in w for w in words)
    return (f'<span class="{cls}" data-words="{",".join(words[1:])}"><span class="rot-txt">{words[0]}</span>'
            f'<span class="on" data-w="{words[0]}" aria-hidden="true"></span></span>')


ROT_JS = """<script>
(function(){
  var h = document.querySelector('.rot-h1'); if (!h) return;
  Array.prototype.forEach.call(h.querySelectorAll('.rot[data-words]'), function(r){
    r.getAttribute('data-words').split(',').forEach(function(w){
      var s = document.createElement('span'); s.setAttribute('data-w', w); s.setAttribute('aria-hidden', 'true'); r.appendChild(s);
    });
  });
  var groups = h.querySelectorAll('.rot'), paused = false, t = 0;
  var g = Array.prototype.map.call(groups, function(r){ return {w: r.querySelectorAll(':scope > span[data-w]'), i: 0}; });
  function step(x){
    // The old word keeps its place while it fades (.out), so the next word never lands under it;
    // only then does the line take the new word's width and the new word fades in.
    var old = x.w[x.i]; x.i = (x.i + 1) % x.w.length; var nw = x.w[x.i];
    old.classList.add('out'); old.classList.remove('on');
    setTimeout(function(){ old.classList.remove('out'); nw.classList.add('on'); }, 160);
  }
  h.addEventListener('mouseenter', function(){ paused = true; });
  h.addEventListener('mouseleave', function(){ paused = false; });
  // One 700 ms clock. The audience word moves on even ticks (every 1.4 s), the verb on
  // every fourth odd tick (every 2.8 s), so the two never change on the same frame.
  setInterval(function(){
    if (paused || document.hidden) return;
    t++;
    if (t % 2 === 0 && g[0]) step(g[0]);
    if (t % 4 === 1 && g[1]) step(g[1]);
  }, 700);
})();
</script>"""

# --------------------------------------------------------------------------------------------
# Home
# --------------------------------------------------------------------------------------------

HOME = f'''<section class="hero skim-hero">
  <div class="wrap split">
    <div class="s7">
    <h1 class="rot-h1"><span class="ph">Your {rot_group(ROT)} {rot_group(ROT_VERBS, "rot rot-v")}</span> <span class="ph">the news from you.</span></h1>
    <p class="lede">LongLens tells your clients what changed in your field and what it means for them, in a newsletter under your name. You see every issue first, with every original one click away.</p>
    <div class="cta-row">
      <a class="btn btn-a" href="/contact/">{CTA_TEXT}</a>
      <a class="txtlink" href="/pricing/">See prices</a>
    </div>
    <p class="price-line">{HERO_OFFER}</p>
    </div>
    <div class="s5 hero-visual">
      <a class="hero-mail" href="https://thevfxsupervisor.com/daily/20/">{pic(M + "read-letter.png", 780, 1276, "A real issue of The VFX Supervisor Daily as it arrives by email", ' fetchpriority="high"')}</a>
      <div class="hero-pod"><b class="kick">{F_POD}</b><img class="wave" src="{M}issue-audio-wave.png" width="780" height="352" alt="">
        <audio controls preload="none" src="{M}issue-audio.m4a" aria-label="The first 16 seconds of the issue's Podcast"></audio></div>
    </div>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head">      <h2>Reach the people|who never read a newsletter</h2>
      <p>The commuter plays the {F_POD}. The scroller watches the {F_REEL}. Everyone else reads the {F_EMAIL}.</p></div>
    {FORMAT_STRIP}
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap split every-line">
    <div class="sec-head el-head">      <h2>Every line|sounds like you</h2>
      <p>Click any line and type. Or hit Reply on the issue in your inbox, write "more on the new rules", and LongLens covers more of them from the next issue.</p></div>
    <div class="el-fig">{EDITOR_SHOT}</div>
    <ol class="nrows el-rows">
      <li><strong>Your name only</strong>Your name, logo and colours on every issue, never ours.</li>
      <li><strong>Your words on top</strong>The headline, the opening and the line people see in their inbox.</li>
      <li><strong>Facts that point home</strong>Every story links to where it came from.</li>
    </ol>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head">      <h2>For any business|whose clients ask|"what does this mean for me?"</h2>
      <p>Accountants, law firms, vet practices, consultants, coaches, clubs and associations.</p>
      <p>{DEFINITION}</p></div>
    <div class="cards">
      <div class="card"><h3>Firms</h3><p>A new rule lands, and your clients hear what it means from you first.</p><a class="txtlink" href="/for-accountants/">See one for accountants</a></div>
      <div class="card"><h3>Consultants and coaches</h3><p>Week after week, people see you know your field.</p></div>
      <div class="card"><h3>Clubs and associations</h3><p>Something worth opening between events.</p></div>
    </div>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head">      <h2>Free for a week.|Then from ${PRICE_SOLO} a month.</h2>
      <p>No card and no call. Your first issue is with you in about {FIRST_ISSUE_MINUTES} minutes.</p></div>
    <div class="cards">
      <div class="card price-card"><b class="kick">Free week</b><span class="amt">${PRICE_FREE}</span><p>A week of real issues, in every format, for you to judge.</p></div>
      <div class="card price-card lead"><b class="kick">Solo</b><span class="amt">${PRICE_SOLO} <small>a month</small></span><p>Your newsletter in your name, sent to your existing clients for you.</p></div>
      <div class="card price-card"><b class="kick">Business</b><span class="amt">${PRICE_BUSINESS} <small>a month</small></span><p>A custom design, plus all your issues on one web page like a blog, your Slack or Discord, and RSS, so new people can follow you.</p></div>
    </div>
    <div class="after-cards"><a class="btn btn-b" href="/pricing/#plans">Compare the plans</a></div>
  </div>
</section>

<section class="proof-sec">
  <div class="wrap">{PROOF}</div>
</section>

{close_cta("Be the first|your clients hear from,|starting this week.",
           f"Name a few websites you trust, list your topics, add your email. Your first issue arrives in about {FIRST_ISSUE_MINUTES} minutes.")}
{ROT_JS}'''

# --------------------------------------------------------------------------------------------
# Features
# --------------------------------------------------------------------------------------------

# Inline stroke icons for the format cards (SPEC 2.5): 20px, currentColor, no emoji.
def icon(paths: str) -> str:
    return (f'<span class="ico" aria-hidden="true"><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" '
            f'stroke-width="1.6">{paths}</svg></span>')


ICONS = {
    F_EMAIL: icon('<rect x="2" y="4" width="16" height="12" rx="2"/><path d="M3 6l7 5 7-5"/>'),
    F_POD: icon('<rect x="7" y="2" width="6" height="10" rx="3"/><path d="M4 10a6 6 0 0012 0M10 16v2"/>'),
    F_REEL: icon('<rect x="5" y="2" width="10" height="16" rx="2"/><path d="M9 8l3 2-3 2z" fill="currentColor" stroke="none"/>'),
    F_EXPL: icon('<rect x="2" y="4" width="16" height="11" rx="2"/><path d="M8.5 7.5l4 2-4 2z" fill="currentColor" stroke="none"/><path d="M6 18h8"/>'),
    F_INFO: icon('<rect x="3" y="2" width="14" height="16" rx="2"/><path d="M6 6h8M6 10h5M6 14h7"/>'),
    F_CAR: icon('<rect x="5" y="4" width="10" height="12" rx="2"/><path d="M2 6v8M18 6v8"/>'),
}

FEATURES = f'''<section class="hero">
  <div class="wrap">
    <h1 class="long">Your readers learn|what changed in your field|from you,|in the form^they will take in.</h1>
    <div class="ledes2">
      <p class="lede">Reach the people who never read a newsletter: a {F_POD} for the drive in, a {F_REEL} for their phone, and the {F_EMAIL} for everyone else.</p>
      <p>{AI_LINE}</p>
    </div>
    <nav class="chips" aria-label="On this page"><a href="#samples">Sample issues</a><a href="#formats">Every format</a><a href="#where">Where it goes</a><a href="#edit">Edit in place</a><a href="#compare">An honest comparison</a></nav>
  </div>
</section>

{samples_section()}

<hr class="rule">
<section id="formats">
  <div class="wrap">
    <div class="sec-head">      <h2>Meet each reader|the way they like|to take in news</h2>
      <p>Whichever way a reader opens you, they get the same news. Every format that is live today is switched on for a new account, and each comes from the same stories.</p></div>
    <div class="cards fmt-cards">
      <div class="card">{ICONS[F_EMAIL]}<h3>{F_EMAIL}</h3><p>What changed and what it means for them, with a link to every original story, in their inbox and on the web once you publish the issue. For the reader with no time, a short version: the one line that matters most and a button to the whole issue.</p></div>
      <div class="card">{ICONS[F_POD]}<h3>{F_POD}</h3><p>Your news in their ears on the drive in: two AI voices talk the issue through, or one AI voice reads it.</p></div>
      <div class="card">{ICONS[F_REEL]}<h3>{F_REEL}</h3><p>A short vertical video with captions that keeps you on their phone, sized for Instagram Reels, TikTok and YouTube Shorts.</p></div>
      <div class="card">{ICONS[F_EXPL]}<h3>{F_EXPL}</h3><p>A few minutes on the issue's stories, narrated, with a drawing for each point.</p></div>
      <div class="card">{ICONS[F_INFO]}<h3>{F_INFO}</h3><p>The whole issue on one image, for the reader who will not read: the headline, then one line on what each story means.</p></div>
      <div class="card">{ICONS[F_CAR]}<h3>{F_CAR}</h3><p>Swipeable slides of the issue that show your followers you know your field.</p></div>
    </div>
  </div>
</section>

<hr class="rule">
<section id="where">
  <div class="wrap">
    <div class="sec-head">      <h2>Be where|your readers already are</h2>
      <p>Your newsletter's name and issue number are on every one, wherever it lands.</p></div>
    <div class="where">
      <div class="card"><h3>Where they can follow you now</h3><ul class="checks rows">
        <li><strong>In your own inbox first</strong>, with every format on its page in your account.</li>
        <li><strong>In your clients' inboxes</strong>: {CLIENT_LINE} {SEND_SETUP} Or forward it from your own email.</li>
        <li><strong>On the web</strong>: each issue you publish gets a page of its own that anyone can open from a link, with no sign-in.</li>
        <li><strong>On one web page of all your issues, like a blog</strong>, with every format of each issue. Geoff sets it up with you. <a href="{DAILY}">See an example</a>.</li>
        <li><strong>In a Slack or Discord channel</strong>: a short post with a link to each issue you publish.</li>
        <li><strong>In a feed reader</strong>: a private RSS link to your published issues.</li>
      </ul></div>
      <div class="card"><h3>Coming soon</h3><ul class="list">
        <li>{coming(f"<strong>In podcast apps</strong>: every issue's {F_POD} in a show your readers can follow.")}</li>
        <li>{coming(f"<strong>On your own Instagram, LinkedIn and TikTok</strong>: your {F_REEL} and {F_CAR} from each issue, ready to post.")}</li>
        <li>{coming("<strong>On your own website</strong>: a block that shows your latest issue.")}</li>
        <li>{coming("<strong>On Telegram</strong>: each issue in a Telegram channel.")}</li>
      </ul></div>
    </div>
  </div>
</section>

<hr class="rule">
<section id="edit">
  <div class="wrap">
    <div class="feat media-row">
      <div class="txt">
        <h2>Your words,|your view of the news:|every line is yours|before it goes out</h2>
        <p class="lead2">Open any issue from the link in your email, press Review and approve, then press Edit in place. The issue opens exactly as your readers will see it, with every line you can change outlined. Click, type, Save. Discard puts back everything you have not saved.</p>
      </div>
      <div class="media">{EDITOR_SHOT}</div>
      <div class="txt frest">
        <ul class="checks">
          <li><strong>What you can change</strong>: the headline, the opening paragraph, the inbox preview line, each section heading, the line on what each story means for your readers, each story summary, the quick links and the points to watch next.</li>
          <li><strong>What stays as published</strong>: story titles, links and the names of the websites they came from, so every fact still points home.</li>
          <li><strong>Type as you would in an email</strong>: on Save, the issue updates everywhere with your words.</li>
          <li><strong>Every version kept</strong>: the issue as LongLens first wrote it, and every save after that.</li>
          <li><strong>Locked once it goes out</strong>: once an issue is approved or sent, it stays exactly as it went.</li>
        </ul>
        <p class="tiny">Edit in place works on daily newsletters. A weekly newsletter has its own editor, section by section.</p>
      </div>
    </div>

    <div class="feat">
      <div class="txt">
        <h2>Put first|what your readers most need to see</h2>
        <p class="lead2">Lay your issue out like a page. On a daily newsletter, the Sections page lists every part of the issue, with a live preview of your latest issue beside it.</p>
        <ul class="checks grid2">
          <li><strong>Your order</strong>: drag a section, or use the arrows, to move it.</li>
          <li><strong>Only what you need</strong>: hide a section with one tick, and show only as many topics as you want.</li>
          <li><strong>Your headings</strong>: rename the extra sections, such as quick links and what to watch, in your own words.</li>
          <li><strong>A note from you</strong>: add your own note, with its own heading, or a divider, anywhere in the issue.</li>
          <li><strong>Back to the usual</strong>: one button puts the usual sections back.</li>
        </ul>
        <p>Your next issue uses the new layout. Issues already written stay as they were.</p>
      </div>
    </div>

    <div class="feat media-row flip">
      <div class="txt">
        <h2>Tell LongLens once|what your readers care about,|and every issue after follows</h2>
        <p class="lead2">Tell LongLens the way you would tell a new hire: hit Reply on any issue in your inbox and write what you want, like "shorter" or "more on the new rules". LongLens answers in the same email thread with what it understood, and the next issue follows it.</p>
      </div>
      <div class="media"><div class="exchange" aria-label="An example email to LongLens and its answer">
        <span class="who">You, replying to your issue email</span>
        <p class="you">Longer please. More on the new rules, less on conferences.</p>
        <span class="who">LongLens, answering in the same email thread</span>
        <div class="ll">
          <p>Got it. Your issues will be the usual length from the next one.</p>
          <p>You'll see more on the new rules from the next issue.</p>
          <p>You'll see less on conferences from the next issue.</p>
          <p>Changed your mind? Just reply UNDO.</p>
        </div>
      </div></div>
      <div class="txt frest">
        <ul class="checks">
          <li><strong>Length</strong>: shorter, longer, or how many stories.</li>
          <li><strong>Topics</strong>: more of one thing, less of another.</li>
          <li><strong>Your readers</strong>: a new sentence about who they are and what matters to them.</li>
          <li><strong>Websites</strong>: paste a link to add one, name one to drop it.</li>
          <li><strong>Tone and layout</strong>: how it sounds, how each story is laid out.</li>
          <li><strong>Formats</strong>: add or drop a format, such as the {F_POD}.</li>
        </ul>
        <p>Write what you want changed in your reply, and every issue after follows it. Only emails from your own address count, so forwarding an issue to a colleague changes nothing.</p>
      </div>
    </div>

    <div class="feat">
      <div class="txt">
        <h2>Built from the websites,|forums and videos|your field already trusts</h2>
        <p class="lead2">Every issue covers what is new on the websites, forums, YouTube channels and topics your field follows. Name them when you start, or add one any time: reply to your issue email with its link.</p>
        <ul class="checks grid2">
          <li><strong>Forward the newsletters you never open</strong>, or save a page from your phone or browser. What matters lands in your next issue under "You sent".</li>
          <li><strong>One tap to turn a website off</strong>, one more to turn it back on. LongLens never adds a website you turned off back by itself.</li>
          <li><strong>New websites, found for you</strong>: LongLens lists the ones your stories came from, each with a way to remove it.</li>
        </ul>
      </div>
    </div>

    <div class="feat">
      <div class="txt">
        <h2>Give clients facts|they can follow in one click:|every name and number|links to the original</h2>
        <ul class="checks grid2">
          <li><strong>What it means for them</strong>: stories carry a line on why they matter to your readers, so the issue is never a list of links.</li>
          <li><strong>No repeats</strong>: a story they have already seen stays out until something changes, then comes back marked as an update.</li>
          <li><strong>Names and figures</strong> sit beside a link to the original story.</li>
          <li><strong>{LINK_LINE}</strong> The original is one click away.</li>
        </ul>
      </div>
    </div>

    <div class="feat-pair">
      <div class="card">
        <h2 class="sub">On your desk|when you sit down</h2>
        <p>LongLens arrives on weekdays at 07:00 your time to start, or on the days and at the time you pick.</p>
        <p>Away for a week? Press Pause this newsletter at the bottom of any issue. The same page starts it again.</p>
      </div>
      <div class="card">
        <h2 class="sub">Yours to keep</h2>
        <p>You own what LongLens writes for you: every issue, every website you chose, every lesson you taught LongLens.</p>
        <p>Your lessons shape your newsletter and nobody else's.</p>
      </div>
    </div>
  </div>
</section>

<hr class="rule">
<section id="compare">
  <div class="wrap">
    <div class="sec-head">      <h2>Keeping your clients^up to date,|without costing you hours</h2></div>
    <div class="cards">
      <div class="card"><h3><span class="kick">Instead of</span> <span class="ct">writing it yourself</span></h3><p>No more hours reading the press and writing it up. LongLens finds the news and writes each issue. You spend a few minutes reading it over, and it keeps going in your busiest week.</p></div>
      <div class="card"><h3><span class="kick">Instead of</span> <span class="ct">a newsletter platform alone</span></h3><p>A platform sends, but you still find the news and write every word. LongLens does the finding and the writing, then sends it for you.</p></div>
      <div class="card"><h3><span class="kick">Instead of</span> <span class="ct">a personal AI summary</span></h3><p>No more turning your own summary into something fit for clients. LongLens writes for your readers, under your name, ready to send.</p></div>
    </div>
    <div class="split compare-foot">
      <p class="statement s6">LongLens tells your readers what the news in your field means for them, ready to send, as a letter and in every other format. You keep the name, the last word and the readers.</p>
      <div class="notfor at7"><h3>What LongLens does not do</h3><ul class="checks cross rows">
        <li><strong>Write your own company news.</strong> LongLens works from what the press, the forums and the videos in your field say. Your own announcements are still yours to write, and you can add them as a note in any issue.</li>
        <li><strong>Run ads or paid subscriptions.</strong> Use a newsletter platform built for that.</li>
        <li><strong>Replace you.</strong> Your judgment is the point. LongLens puts it in front of more people, issue after issue.</li>
      </ul></div>
    </div>
  </div>
</section>

{close_cta("Be the first|your clients hear from,|starting this week.",
           f"Name a few websites you trust, list your topics, add your email. Your first issue is with you in about {FIRST_ISSUE_MINUTES} minutes.")}'''

# --------------------------------------------------------------------------------------------
# Pricing
# --------------------------------------------------------------------------------------------

# The plan bullets, word for word on the cards and in the comparison table (Geoff 2026-11-08: "i like
# the pricing table"). The table has no Free week column: the site does not state each row for the
# free week, so nothing is inferred for it.
SOLO_ROWS = ("A newsletter every day or every week",
             f"Every format: {F_EMAIL}, {F_POD}, {F_REEL}, {F_INFO}, {F_CAR}, {F_EXPL}",
             "Your name, logo and colours, never ours",
             "Sent to your existing clients for you, with a one-click opt-out")
# Slack, Discord and the RSS feed are listed under Business only (Geoff 2026-11-08). The app has no
# plan gate on them, so any owner can still set them up; the site just does not sell them on Solo,
# and no page may say they come with every plan.
BUSINESS_ROWS = ("A custom design of your emails, pages and videos, built with you",
                 "All your issues on one web page, like a blog",
                 "Each issue posted to your Slack or Discord channel, and an RSS feed")
# Edit or reply: on every plan, so the table ticks it for both (BREAK S3); same words as the Free week card.
EDIT_ROW = "Edit any line, or reply to your issue email with what to change"
BUSINESS_COMING = f"Your {F_POD} in podcast apps; your {F_REEL} and {F_CAR} ready to post to Instagram, LinkedIn and TikTok"


def plan_table() -> str:
    yes = '<span class="yes" role="img" aria-label="Included"></span>'
    no = '<span class="no"><span aria-hidden="true">-</span><span class="sr-only">Not included</span></span>'
    rows = [(r, yes, yes) for r in SOLO_ROWS[:2]] + [(EDIT_ROW, yes, yes)] + [(r, yes, yes) for r in SOLO_ROWS[2:]]
    rows += [(r, no, yes) for r in BUSINESS_ROWS]
    rows.append((BUSINESS_COMING, no, coming()))
    # data-label: on phones each value carries its plan name (site.css, BREAK S4).
    body = "".join(f'<tr><th scope="row">{r}</th><td class="v" data-label="Solo">{a}</td>'
                   f'<td class="v" data-label="Business">{b}</td></tr>' for r, a, b in rows)
    return (f'<table class="ptable"><thead><tr><th scope="col"><span class="sr-only">What you get</span></th>'
            f'<th scope="col" class="v lead">Solo ${PRICE_SOLO}</th><th scope="col" class="v">Business ${PRICE_BUSINESS}</th></tr></thead>'
            f'<tbody>{body}</tbody></table>')


PRICING = f'''<section class="hero">
  <div class="wrap">
    <div class="sec-head center" style="margin-bottom:0">    <h1>Free for a week.|Then from ${PRICE_SOLO} a month.</h1>
    <p class="lede">No card, no call. Your first issue is with you in about {FIRST_ISSUE_MINUTES} minutes.</p></div>
    <div class="plans">
      <div class="plan"><h2>Free week</h2>
        <p class="plan-price">${PRICE_FREE}</p>
        <p class="plan-outcome">Judge a week of real issues before anyone else sees them.</p>
        <ul class="checks">
          <li>Every format: {F_EMAIL}, {F_POD}, {F_REEL}, {F_INFO}, {F_CAR}, {F_EXPL}</li>
          <li>{EDIT_ROW}</li>
          <li>Your name only, in a look matched to your brand</li>
        </ul>
        <a class="btn btn-b" href="/contact/">Start my free week</a></div>
      <div class="plan lead"><h2>Solo</h2>
        <p class="plan-price">${PRICE_SOLO} <small>a month</small></p>
        <p class="plan-outcome">Keep your clients hearing from you, every week.</p>
        <ul class="checks">{"".join(f"<li>{r}</li>" for r in SOLO_ROWS)}</ul>
        <a class="btn btn-a" href="/contact/">Start with a free week</a></div>
      <div class="plan"><h2>Business</h2>
        <p class="plan-price">${PRICE_BUSINESS} <small>a month</small></p>
        <p class="plan-outcome">Reach people beyond your own list.</p>
        <ul class="checks">
          <li><strong>Everything in Solo</strong></li>
          {"".join(f"<li>{r}</li>" for r in BUSINESS_ROWS)}
          <li class="plan-coming plain">{coming(BUSINESS_COMING)}</li>
        </ul>
        <a class="btn btn-b" href="/contact/">Start with a free week</a></div>
    </div>
    <div class="plan-notes"><p>{FORMAT_LADDER}</p>
    <p>Prices in US dollars, after the free week, paid by invoice. {SEND_SETUP}</p></div>
  </div>
</section>

<hr class="rule">
<section id="plans">
  <div class="wrap">
    <div class="sec-head">      <h2>What each plan includes</h2></div>
    {plan_table()}
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head">      <h2>One short form starts it.|One click stops it.</h2>
      <p>Nothing to install, no password, and nothing owed if you stop.</p></div>
    <ol class="steps three">
      <li><strong>Day one</strong><p>Your first issue arrives in about {FIRST_ISSUE_MINUTES} minutes.</p></li>
      <li><strong>Every weekday</strong><p>A new issue at 07:00 your time, or the days and time you choose.</p></li>
      <li><strong>Room to try</strong><p>One newsletter, with as many sources as you like, and 25 readers. Every issue ends with a Stop button.</p></li>
    </ol>
  </div>
</section>

{close_cta("Be the first|your clients hear from,|starting this week.",
           "One short form, then a week of real issues to judge before anyone else sees them.")}'''

# --------------------------------------------------------------------------------------------
# How it works
# --------------------------------------------------------------------------------------------

HOW = f'''<section class="hero">
  <div class="wrap">
    <h1 class="long">Stay in front of your clients,|starting today.|One short form|and your first issue^is with you in minutes.</h1>
    <p class="lede">Nothing to learn and no password to remember. From then on, change any line right on the issue, or hit Reply on the issue email and say what you want different. Every issue sounds more like you.</p>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><h2>See what your clients|would read from you,|in minutes</h2></div>
    <ol class="steps two">
      <li><h3>Get a free week,|with your own news</h3>
        <p>Paste a few sources, list your topics, add your email.</p>
        <p><a href="/contact/">{CTA_TEXT}</a></p></li>
      <li><h3>Your first issue arrives|in about {FIRST_ISSUE_MINUTES} minutes</h3>
        <p>By email, written from the sources and topics you gave. Already have an account? The email holds your sign-in link instead.</p></li>
      <li><h3>Every weekday morning,|something worth passing on|is in your inbox</h3>
        <p>On weekdays at 07:00 your time, with nothing to press. Every issue ends with a Stop button.</p></li>
      <li><h3>Make it yours:|topics, websites, name and timing|in one place</h3>
        <p>What it follows, its sources, its name, who reads it, and the days and time it arrives. Sooner? Open Issues and press Make an issue now: LongLens starts on it within ten minutes and emails it to you.</p></li>
    </ol>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><h2>Why your clients can trust|what they read from you</h2>
      <p>Not a pasted feed: only the stories your clients care about, in plain words.</p></div>
    <ol class="steps two">
      <li><h3>Stop checking|ten websites a day</h3><p>LongLens reads the websites, feeds and channels you pick, and brings you what matters.</p></li>
      <li><h3>Each story is judged against|what your readers care about</h3><p>Write back "more on the new rules, less on events" and the next issue picks its stories that way.</p></li>
      <li><h3>The same story from two outlets|appears only once</h3><p>A story your readers already had stays out unless something changed. Then it comes back marked as an update, linked to the earlier coverage.</p></li>
      <li><h3>Every story is retold|in plain words, under your name</h3><p>With a line on why it matters to your readers, not pasted from the original.</p></li>
      <li><h3>Every name, title and number|links to the original article</h3><p>The original is one click away.</p></li>
      <li><h3>A website that stops working|or fills with junk|is paused automatically</h3><p>You can see which one, and turn it back on with one tap.</p></li>
      <li><h3>Every issue|comes to you first</h3><p>Change what you like on the page before you send it. If your issues also go on a web page, you choose: each one goes up on its own, or when you put it up. {CLIENT_LINE}</p></li>
      <li><h3>The {F_POD}, {F_REEL} and the rest follow</h3><p>{FORMAT_LADDER} The email has a link to each one, and they open on the issue's page.</p></li>
    </ol>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><h2>Five quick moves|keep every issue yours</h2></div>
    <ul class="list">
      <li><strong>Change a line</strong>: open the issue from the link in your email, press Review and approve, then Edit in place, click any line and type (daily newsletters; a weekly newsletter has its own editor).</li>
      <li><strong>Change the next issue</strong>: reply to the issue email and say what you want, for example "shorter please". LongLens emails back what it changed, and the next issue follows it.</li>
      <li><strong>Undo a change</strong>: reply with the one word UNDO.</li>
      <li><strong>Pause it</strong>: press Pause this newsletter at the bottom of any issue. The same page starts it again.</li>
      <li><strong>Sign in</strong>: type your email on the <a href="/sign-in/">sign-in page</a> and a fresh link arrives by email. Each link works once, and keeps you signed in for 30 days on that device.</li>
    </ul>
    <p class="k">Prefer to send it yourself? Forward any issue from your own email.</p>
  </div>
</section>

{close_cta("Be the first|your clients hear from,|starting this week.",
           "You read a week of real issues before anyone else does.")}'''

# --------------------------------------------------------------------------------------------
# FAQ
# --------------------------------------------------------------------------------------------

def qa(q, a):
    return f"<details><summary>{q}</summary>{a}</details>"


# B3, B1, B2 in newsletter-samples/research/positioning-2026-11-07 (TRUTH-learning-training.md,
# MARKETER-learning-training.md). Answer only, never hero, headline, button or pricing.
CLIENT_DETAILS_QA = ("What happens to my clients' details?",
                     "<p>Your clients' names and email addresses are used for one thing: sending them your updates. "
                     "They never go to an AI. Your replies shape your own newsletter and nobody else's, and your "
                     "content is never used to teach an AI.</p>")

# The accountants page never explains replying elsewhere, so its answer says how (BREAK S1, 2026-11-08).
FA_CLIENT_DETAILS_QA = (CLIENT_DETAILS_QA[0],
                        "<p>Your clients' names and email addresses are used for one thing: sending them your updates. "
                        "They never go to an AI. Hit Reply on any update in your inbox and write what you want changed. "
                        "Your replies shape your firm's updates and nobody else's, and your content is never used to "
                        "teach an AI.</p>")


FAQ_ITEMS = [
    ("Getting started", [
        ("What is LongLens?", f"<p>{DEFINITION}</p>"),
        ("How soon can my clients start hearing from me?",
         f"<p>Your first issue is with you in about {FIRST_ISSUE_MINUTES} minutes, written from the websites and topics you gave. You read a week of real issues before anyone else does. Then {CLIENT_LINE[0].lower() + CLIENT_LINE[1:]} {SEND_SETUP}</p>"),
        ("Can I sign up on my own?",
         f"<p>Yes, from the form. <a href=\"/contact/\">Start your free week</a>. Your first issue arrives by email in about {FIRST_ISSUE_MINUTES} minutes. On a very busy day you get a start link instead: click it and answer three short questions.</p>"),
        ("How do I sign in?",
         "<p>With a link by email. There is no password. Type your email on the <a href=\"/sign-in/\">sign-in page</a> and a fresh link arrives. Each link works once and keeps you signed in for 30 days on that device.</p>"),
    ]),
    ("Trust and control", [
        ("Is this just my news feeds pasted into an email?",
         "<p>No. LongLens judges each story against what you said your readers care about, and leaves out what does not fit. What stays is retold in plain words, under your name, with a line on why it matters to your readers, not pasted from the original. The same story from two outlets appears only once. Every name, title and number links to the original article. Every story links to its original, one click away, and every issue comes to you first.</p>"),
        ("Does anything reach my clients before I see it?",
         "<p>No. Nothing goes to your clients until you approve it. Every issue comes to you by email first: you read it, change any line, and decide what to send and to whom. If your issues also go up on a web page, like a blog, each one waits for your OK there too, unless you choose a setting that puts it up for you: Automatic, or Publish at noon without my take (if you have not added your own comment by 12:00, it goes up without it). Both are off until you choose them, you are emailed when an issue goes up, and what goes up also reaches your Slack or Discord channel and your feed.</p>"),
        ("What if LongLens gets something wrong?",
         "<p>Every issue comes to you first, and you can change or cut any line before you send it. If your issues also go on a web page, you choose: each one goes up on its own, or when you put it up. LongLens links every story to its original, so you or your client can follow any fact in one click. Your name is on it, so the last word is yours.</p>"),
        ("Whose name is on what my clients read, and will it look like my brand?",
         "<p>Yours, and only yours, so it looks like your firm, not a template. On every plan, every issue carries your name, logo and colours, never ours. Business adds a custom design of your letters, pages and videos, built with you when you start.</p>"),
        ("Who is responsible for record keeping and professional rules?",
         "<p>Your firm is. You decide what your clients are told, and you keep the records your own professional rules require. When LongLens sends for you, it keeps the proof of who was added as a client and who stopped.</p>"),
        ("Will AI-drafted issues sound like me?",
         "<p>AI drafts each issue and links every story to its original. Every issue comes to you first, and you make it yours: type on the page to change a line, or reply to the issue email to change the next issue. So it sounds like you.</p>"),
        ("Can I make every line sound like me?",
         "<p>Yes. Open the issue from the link in your email, press Review and approve, then Edit in place, click any line and type, then Save. Every version is kept. This works on daily newsletters; a weekly newsletter has its own editor, section by section.</p>"),
    ]),
    ("Your clients' details", [
        ("Does LongLens need my client list?",
         f"<p>Only if you want LongLens to send for you. {CLIENT_LINE} Each letter to a client also shows your business name and postal address. {SEND_SETUP} Or keep your list where it is and forward each issue yourself.</p>"),
        CLIENT_DETAILS_QA,
        ("Can LongLens follow news from my country?",
         "<p>Yes. LongLens follows the websites, feeds and forums you name, wherever they are: a tax authority's news page, an industry association, a regulator.</p>"),
    ]),
    ("What you get", [
        ('What does "issue" mean?',
         f"<p>One day's or one week's newsletter: the stories LongLens picked, each with what it means for your readers. {FORMAT_LADDER}</p>"),
        ("Is LongLens only for one kind of business?",
         "<p>No. LongLens works for any business whose readers need to know what is changing: an accountancy, a vet practice, a law firm, a recruiter, a consultancy, a school or a members' association. Geoff built it first for his own field, visual effects, and that is the example on this site. Yours follows the websites, forums and newsletters of your field.</p>"),
        (f"Is the {F_POD} voice AI?",
         f"<p>Yes. Every {F_POD} is spoken by AI voices, never a person: two AI hosts talking the issue through, or one AI voice reading it.</p>"),
        ("What happens when a rule changes after I have written about it?",
         "<p>Your readers see it as one story, not a second surprise. A story that moves stays one story: LongLens watches for updates and reversals and links back to earlier coverage.</p>"),
        ("Can LongLens show my readers where their field is heading?",
         "<p>After your first few issues, a section shows what keeps coming up across your last few weeks of issues.</p>"),
        ("Can LongLens write my own company news?",
         "<p>No. LongLens works from what the press, the forums and the videos in your field say. Your own announcements are still yours to write, and you can add them as a note in an issue.</p>"),
    ]),
    ("Day to day", [
        ("How do I change what I get?",
         "<p>Hit Reply on any issue in your inbox and write what you want, like \"shorter\", \"more on VAT\" or \"drop this website\". LongLens emails back in the same thread with what it changed, and the next issue follows it. Reply with the word UNDO to take it back. Issues arrive on weekdays at 07:00 your time to start; change the days and the time on your settings page after you sign in. Every issue ends with a Stop button. If you never tap a link, reply or sign in for five issues, LongLens asks once whether you still want them and waits for your yes.</p>"),
        ("Can I stop it for a while?",
         "<p>Yes. Press Pause this newsletter at the bottom of any issue. The same page starts it again.</p>"),
        ("If I forward an issue to a colleague, can they change it?",
         "<p>No. Only an email from the address your issues go to changes anything. A colleague who writes back to a forwarded issue changes nothing.</p>"),
        ("What if my issue is late?",
         "<p>If an issue has not gone out an hour after its usual time, LongLens emails you once to say so. You do not need to do anything: it goes out as soon as it is ready, or, if something went wrong while making it, we have already been told.</p>"),
    ]),
    ("Money and ownership", [
        ("What does LongLens cost?",
         f"<p>Free for a week with no card, then from ${PRICE_SOLO} a month. Solo is ${PRICE_SOLO} a month and Business is ${PRICE_BUSINESS} a month, in US dollars, paid by invoice. <a href=\"/pricing/\">See what each plan includes</a>.</p>"),
        ("Is there a limit during the free week?",
         "<p>Yes: one newsletter, with as many sources as you like and up to 25 readers on your list.</p>"),
        ("Who owns what LongLens writes?",
         "<p>You do. Every issue, every website you chose, every lesson you taught LongLens.</p>"),
        ("Who is behind LongLens?",
         f"<p>Geoffrey Hancock. He built LongLens first for his own field, visual effects for film and TV, and his own newsletter runs on it: <a href=\"{DAILY}\">The VFX Supervisor Daily</a>. He won a VES Award for Changeling and was nominated for another for Invictus.</p>"),
    ]),
]

FAQ = f'''<section class="hero">
  <div class="wrap">
    <h1 class="long">Straight answers,|including what LongLens|does not do yet.</h1>
    <p class="lede">Answers before you ask, including what LongLens does not do yet.</p>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="faq">{"".join(f"<h2>{h}</h2>" + "".join(qa(q, a) for q, a in items) for h, items in FAQ_ITEMS)}</div>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><h2>Not built yet,|and we say so</h2></div>
    <ul class="coming">
      <li><strong>Each reader picks their format</strong> {coming()}<br>{F_EMAIL}, {F_POD}, {F_REEL}, {F_INFO}, {F_CAR} or {F_EXPL}, from a link at the bottom of every issue they get.</li>
      <li><strong>Your {F_REEL} and {F_CAR} ready to post to your own Instagram, LinkedIn and TikTok; your {F_POD} in podcast apps; Telegram; your website</strong> {coming()}<br>Today each issue goes by email and on the web, and on Business to your Slack or Discord channel and an RSS feed.</li>
    </ul>
  </div>
</section>

{close_cta("Be the first|your clients hear from,|starting this week.",
           "One short form, and your first issue is with you in minutes.")}'''

# --------------------------------------------------------------------------------------------
# Contact
# --------------------------------------------------------------------------------------------

def turnstile_widget() -> str:
    """The Turnstile widget (managed mode is set on the widget in Cloudflare), or nothing while
    TURNSTILE_SITE_KEY is empty. It adds the hidden cf-turnstile-response field to the form."""
    if not TURNSTILE_SITE_KEY:
        return ""
    return (
        f'\n  <div class="cf-turnstile" data-sitekey="{html.escape(TURNSTILE_SITE_KEY)}"'
        f' data-action="{TURNSTILE_ACTION}" data-theme="auto"></div>'
        '\n  <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>'
    )


# The start form's script. With no script the form posts as before (the browser checks the
# required fields, the app answers with its own page). With it: our own inline messages instead of
# the browser's bubbles, a "Sending..." button, and the post sent with Accept: application/json, so
# the app answers in JSON (web/inquiry_pages.py): ok + next (the thanks page to open), or errors per
# field, or a message. Anything else (the edge's 502, an app 500 with no CORS header, no network)
# shows FORM_OOPS, never a raw page. The Turnstile token works once, so it is reset after a refusal.
FORM_OOPS = f"Sorry, your form did not reach us. Please try again in a minute, or email {EMAIL}."
FORM_JS = """<script>(function(){var f=document.getElementById("start-form");if(!f||!window.fetch||!window.FormData||!window.URLSearchParams)return;
f.noValidate=true;var btn=f.querySelector("button[type=submit]"),label=btn.textContent,box=document.getElementById("f-status");
var fields=[].slice.call(f.querySelectorAll("textarea,input[type=email]"));
var NEED={concepts:"Please list a few topics you want to follow.",sources:"Please paste at least one website or feed.",email:"Please add your email address."};
var OOPS=%s;
function show(el,m){var p=document.getElementById(el.id+"-err");el.setAttribute("aria-invalid",m?"true":"false");p.textContent=m||"";p.hidden=!m}
function check(el){var v=el.value.trim();if(el.required&&!v)return NEED[el.name]||"Please fill this in.";
if(el.type=="email"&&v&&!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(v))return "That email address does not look right. Please check it.";
if(el.maxLength>0&&el.value.length>el.maxLength)return "Please make this a little shorter.";return ""}
fields.forEach(function(el){el.addEventListener("input",function(){if(el.getAttribute("aria-invalid")=="true")show(el,check(el))})});
function say(m){box.textContent=m||"";box.hidden=!m}
function busy(on){btn.disabled=on;btn.textContent=on?"Sending...":label;f.setAttribute("aria-busy",on?"true":"false")}
function again(){busy(false);try{if(window.turnstile)window.turnstile.reset()}catch(e){}}
f.addEventListener("submit",function(ev){ev.preventDefault();if(btn.disabled)return;say("");var first=null;
fields.forEach(function(el){var m=check(el);show(el,m);if(m&&!first)first=el});if(first){first.focus();return}
busy(true);fetch(f.action,{method:"POST",body:new URLSearchParams(new FormData(f)),headers:{"Accept":"application/json"}})
.then(function(r){return r.json().then(function(d){return[r.status,d||{}]},function(){return[r.status,{}]})})
.then(function(x){var st=x[0],d=x[1];if(d.ok){if(d.next){location.href=d.next;return}busy(false);btn.disabled=true;say(d.message||"Thanks. Your form has reached us.");return}
again();var e=d.errors||{},hit=null;fields.forEach(function(el){if(e[el.name]){show(el,e[el.name]);hit=hit||el}});if(hit){hit.focus();return}
var rest=Object.keys(e).map(function(k){return e[k]});say(rest.length?rest.join(" "):(st==403||st==413||st==429)&&d.message?d.message:OOPS)})
.catch(function(){again();say(OOPS)})})})();</script>""" % json.dumps(FORM_OOPS)


def inquiry_form() -> str:
    """The start form, three fields (Geoff 2026-11-06: "just paste sources and list concepts and
    give your email. that starts it"). The app fills setup with the answers and asks the rest
    (who reads it, the name competition) on the next page.
    The hidden honeypot is ``hp_note`` (2026-11-08), not ``website``: autofill and AI agents fill
    a field called "website", and the app then treated real people as bots. The app accepts
    both names; it had to be deployed before this page."""
    sources_label = "Sources to follow" + ("" if SOURCES_REQUIRED else " (optional)")
    required = " required" if SOURCES_REQUIRED else ""
    return f'''<form class="contact-card" id="start-form" method="post" action="{INQUIRY_ENDPOINT}" accept-charset="utf-8">
  <p><label for="f-sources">{sources_label}: paste websites or feeds, one per line</label><br><textarea id="f-sources" name="sources" rows="4" maxlength="4000"{required} aria-describedby="f-sources-err" placeholder="https://www.accountingtoday.com&#10;https://www.journalofaccountancy.com"></textarea><span class="ferr" id="f-sources-err" role="alert" hidden></span></p>
  <p><label for="f-concepts">Topics to follow</label><br><textarea id="f-concepts" name="concepts" rows="4" required maxlength="4000" aria-describedby="f-concepts-err" placeholder="New tax and payroll rules for small businesses, and what my clients should do before each deadline."></textarea><span class="ferr" id="f-concepts-err" role="alert" hidden></span></p>
  <p><label for="f-email">Your email</label><br><input id="f-email" type="email" name="email" required maxlength="320" autocomplete="email" aria-describedby="f-email-err"><span class="ferr" id="f-email-err" role="alert" hidden></span></p>
  <input type="hidden" name="offer" value="brief"><input type="hidden" name="source" value="longlens">
  <input type="hidden" name="tz" id="f-tz" value="">
  <script>try{{document.getElementById("f-tz").value=Intl.DateTimeFormat().resolvedOptions().timeZone||""}}catch(e){{}}</script>
  <p style="position:absolute;left:-9999px" aria-hidden="true"><label for="f-hp-note">Leave this empty</label><input id="f-hp-note" name="hp_note" tabindex="-1" autocomplete="off" aria-hidden="true"></p>{turnstile_widget()}
  <input type="hidden" name="consent_version" value="{CONSENT_VERSION}">
  <button class="btn btn-a" type="submit">See my first issue, free</button>
  <p class="form-msg" id="f-status" role="alert" hidden></p>
  <p class="fine">By starting, you agree to get these emails. Stop them any time with one click.</p>
  <p class="email-line">We never add you to a list. Read the <a href="/terms/">terms</a> and <a href="/privacy/">privacy</a>.</p>
</form>
{FORM_JS}'''


CONTACT_BODY = inquiry_form() if FORM_LIVE else f'''<div class="contact-card">
  <h2 style="font-size:22px">Email Geoff.|Three lines are enough.</h2>
  <ul>
    <li>The websites or feeds you read.</li>
    <li>The topics you follow.</li>
    <li>Your name and your business.</li>
  </ul>
  <a class="btn btn-a" href="{html.escape(CALL_MAIL)}">Email Geoff for a free week</a>
  <p class="email-line">Or write to <a href="mailto:{EMAIL}">{EMAIL}</a></p>
  <p class="tiny">Writing does not add you to any list. Geoff replies personally.</p>
</div>'''

CONTACT = f'''<section class="hero">
  <div class="wrap">
    <h1 class="long">Read a week|of what your clients|would hear|from you, free.</h1>
    <p class="lede">Name a few websites you trust, list your topics, add your email. In about {FIRST_ISSUE_MINUTES} minutes you read your first issue. {OFFER_LINE}.</p>
    {CONTACT_BODY}
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><h2>A week of real issues,|read before^anyone else sees them</h2></div>
    <ol class="steps three">
      <li><h3>Your first issue is with you|in about {FIRST_ISSUE_MINUTES} minutes</h3><p>Written from the websites and topics you just gave.</p></li>
      <li><h3>Something worth passing on|every weekday morning</h3><p>On weekdays at 07:00 your time, with nothing to press. Every issue ends with a Stop button.</p></li>
      <li><h3>Your first week</h3><p>Change what it covers and when on one page, if you like. You read a week of real issues before anyone else does.</p></li>
    </ol>
    <p class="k">Before you start, read a real one: <a href="{DAILY}">The VFX Supervisor Daily</a>, Geoff's own newsletter about his own field. Yours covers your field, for your readers.</p>
  </div>
</section>'''

THANKS = f'''<section class="hero">
  <div class="wrap prose">
    <h1>Thanks.|Check your inbox|for your start link.</h1>
    <p>LongLens has emailed you a one-time link. Click it: what you wrote on this form is already filled in. Check it, add who reads it if you like, and pick where and when it arrives. Your first issue arrives on the schedule you pick, and your free week starts there. The link works once, for 24 hours.</p>
    <p>Already have an account? The email holds your sign-in link instead. Nothing else is sent to you. We never add you to a list.</p>
    <p>Before you start, read <a href="{DAILY}">Geoff's own newsletter</a>, or go back to the <a href="/">LongLens home page</a>.</p>
  </div>
</section>'''

THANKS_FIRST = f'''<section class="hero">
  <div class="wrap prose">
    <h1>Check your email|in about {FIRST_ISSUE_MINUTES} minutes.</h1>
    <p>Your first issue is on its way. The next ones follow on weekdays at 07:00 your time, with nothing to press, and every issue ends with a Stop button.</p>
    <p>We never add you to a list.</p>
    <p>While you wait, read <a href="{DAILY}">Geoff's own newsletter</a>, or go back to the <a href="/">LongLens home page</a>.</p>
  </div>
</section>'''

THANKS_PERSONAL = f'''<section class="hero">
  <div class="wrap prose">
    <h1>Thanks.|Geoff will reply|to you personally.</h1>
    <p>LongLens could not start your newsletter straight away, so Geoff will email you himself. You may also get a short thank-you email from LongLens. We never add you to a list.</p>
    <p>Before you start, read <a href="{DAILY}">Geoff's own newsletter</a>, or go back to the <a href="/">LongLens home page</a>.</p>
  </div>
</section>'''

# --------------------------------------------------------------------------------------------
# Sign in, privacy, 404
# --------------------------------------------------------------------------------------------

SIGNIN_PAGE = f'''<section class="hero">
  <div class="wrap">
    <h1>Sign in with one link.|No password.</h1>
    <p class="lede">The button below opens the LongLens app's sign-in page. Type your email and a link arrives by email. The link keeps you signed in for 30 days on that device.</p>
    <div class="cta-row"><a class="btn btn-a" href="{SIGNIN}">Get my sign-in link</a></div>
    <p class="k">Not set up yet? <a href="/contact/">Start your free week</a> and your first issue arrives by email in minutes.</p>
  </div>
</section>'''

PRIVACY = f'''<section class="hero">
  <div class="wrap prose">
    <h1>No cookies on this site.|Your email reaches one person.</h1>
    <p>This website, getlonglens.com, uses Cloudflare Web Analytics to count visits. It sets no cookies and does not follow you to other sites. The pages are hosted on GitHub Pages.</p>
    <h2>When you write|to Geoff</h2>
    <p>Your email goes to Geoffrey Hancock at {EMAIL}. LongLens uses it to make your account and email you your newsletter, and Geoff uses it only to reply to you. Writing does not add you to any list.</p>
    <h2>Once you use LongLens</h2>
    <p>We notice if you tap a link in your issues, only so we stop emailing anyone who never reads them. Nothing else is read from your issues, and it is not used for anything else.</p>
    <p>What the LongLens app keeps about you, where it lives and who else sees anything is set out on the app's own privacy page: <a href="{APP_PRIVACY}">LongLens app privacy</a>.</p>
    <h2>Who runs|LongLens</h2>
    <p>{IDENTITY} Write to <a href="mailto:{EMAIL}">{EMAIL}</a>. The <a href="/terms/">terms</a> are on their own page.</p>
  </div>
</section>'''

# Terms (Geoff 2026-11-12: short plain terms, approved to go live with the identity line). The
# full text and its review are in newsletter-samples/research/site-checklist-2026-11-12/TERMS-DRAFT.md.
TERMS_UPDATED = "12 November 2026"
TERMS = f'''<section class="hero">
  <div class="wrap prose">
    <h1>Your content stays yours.|Stop any time.</h1>
    <p class="lede">These terms cover LongLens, the newsletter service at getlonglens.com, run by {COMPANY}. They are short on purpose. Last updated {TERMS_UPDATED}.</p>
    <h2>Your first week|is free</h2>
    <p>Starting costs nothing and needs no card. After your free week you pay only if you pick a paid plan; plans and prices are on the <a href="/pricing/">pricing page</a>, invoiced in US dollars. LongLens is new and still changing, so we may limit how many new newsletters start each day.</p>
    <h2>Your content|and your readers stay yours</h2>
    <p>Your topics, the websites you name, your readers' email addresses and the issues you send are yours. LongLens uses them to write and deliver your newsletter, as the <a href="/privacy/">privacy page</a> sets out, and for nothing else. We never sell your readers' addresses or add them to any list. Every story links to its original, and the original belongs to its publisher.</p>
    <h2>Your name,|your call</h2>
    <p>LongLens writes each issue with AI, and every issue comes to you first. You make it yours and you decide what goes out under your name, so what you send is your responsibility.</p>
    <h2>No guarantees</h2>
    <p>LongLens is provided as it is. We work to keep it running and its stories right, but we cannot promise it is free of mistakes or always available. As far as Danish law allows, we are not liable for any loss that comes from using it.</p>
    <h2>Stop|any time</h2>
    <p>You can stop whenever you like: press Stop at the end of any issue, or email <a href="mailto:{EMAIL}">{EMAIL}</a>. We can stop your newsletter too, and when we do we tell you by email first whenever we can.</p>
    <h2>Changes|and the law</h2>
    <p>We may change these terms as LongLens changes. The date at the top shows the latest version, and we email you about any change that affects you. Danish law applies, and the Danish courts decide any dispute.</p>
    <h2>Who we are</h2>
    <p>{COMPANY}, CVR {CVR}, {COMPANY_ADDRESS}. Email <a href="mailto:{EMAIL}">{EMAIL}</a>.</p>
  </div>
</section>'''

NOT_FOUND = '''<section class="hero">
  <div class="wrap prose">
    <h1>That page|is not here.</h1>
    <p><a href="/">Go to the LongLens home page</a>, or <a href="/contact/">ask Geoff for a free week</a>.</p>
  </div>
</section>'''

# --------------------------------------------------------------------------------------------

# --------------------------------------------------------------------------------------------
# For accountants (outreach page: in the sitemap, not in the main navigation)
# --------------------------------------------------------------------------------------------

# The accountants page shows its own sample: an invented Manchester firm, real UK news, from a real
# pipeline run (newsletter-samples/samples-accountants-uk-2026-11-07, not hand-edited). Same shape as SAMPLES.
FA_SAMPLE = ("uk-accounting", "Client Update", "For the clients of a Manchester accounting firm",
             "Late payments cost more from 16 November, and MTD and Budget dates are closing in",
             "The dates clients must act on come first.")
FA_SAMPLE_DATE = "Sat 7 Nov 2026"
FA_CTA = "Get your first client update free"

FA_OFFER = f"{OFFER_LINE}, invoiced."
FA_PASS = f"Every update comes to you first. Your first one is with you in about {FIRST_ISSUE_MINUTES} minutes."
# Examples only: the value is the sources the accountant trusts. Do not name authorities that are not proven
# to work as sources (SOURCE-TEST-authorities.md).
FA_AUTH = "HMRC, the IRS, or your own professional body"
FA_SETUP = "Name the sources you trust and we set them up when you start."

FA_FAQ = "".join(qa(q, a) for q, a in [
    ("Can I pick sources from my own country?",
     "<p>Yes. Name the sources you trust, such as a tax authority, your professional body or the business press, and we set them up when you start. Sources with a news feed work when you paste them. Some government pages need us to set them up by hand, so tell us which ones matter most to you.</p>"),
    ("Whose name is on what my clients read, and will it look like my brand?",
     "<p>Yours, and only yours, so it looks like your firm, not a template. On every plan, every update carries your firm's name, logo and colours, never ours. Business adds a custom design of your letters, pages and videos, built with you when you start.</p>"),
    ("Who is responsible for record keeping and professional rules?",
     "<p>Your firm is. You decide what your clients are told, and you keep the records your own professional rules require. When LongLens sends for you, it keeps the proof of who was added as a client and who stopped.</p>"),
    FA_CLIENT_DETAILS_QA,
])

FOR_ACCOUNTANTS = f'''<section class="hero">
  <div class="wrap split">
    <div class="s7">
    <h1 class="long">Be the accountant|clients hear from first|when the rules change</h1>
    <p class="lede">Tell your clients what a change means before they have to ask. LongLens explains each change in your client newsletter, in plain words, with a link to every original, and you change any line before your clients read a word. {FA_SETUP} Examples: {FA_AUTH}.</p>
    <div class="cta-row">
      <a class="btn btn-a" href="/contact/">{FA_CTA}</a>
    </div>
    <p class="price-line">{FA_OFFER} <a href="/pricing/">See prices</a>.</p>
    <p class="price-line">Every update carries your firm's name and only yours, never ours, and we match the look to your brand when you start.</p>
    <p class="price-line">{FA_PASS} <a href="/samples/{FA_SAMPLE[0]}/">Read a sample client update</a>.</p>
    </div>
    <div class="s5 hero-visual"><a class="hero-mail" href="/samples/{FA_SAMPLE[0]}/"><img src="/assets/samples/{FA_SAMPLE[0]}-top.png" width="600" height="900" alt="The top of Client Update, a sample client update for an accounting firm: {html.escape(FA_SAMPLE[3])}"></a></div>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="split sample-split"><div class="s7">
    <div class="sec-head">      <h2>See what your clients|would hear from you|the morning^a tax rule changes</h2>
      <p>One example, written for an invented firm in Manchester, using real news: HMRC late payment interest going up, a Making Tax Digital deadline, Budget changes for April 2027. The firm is made up; the stories and links are real, and each section says what it means for the firm's clients. Yours would use the sources you trust, from any country.</p></div>
    </div>
    <div class="s5 fmt-strip one" role="list" aria-label="A sample client update for an accounting firm">
      <div class="fmt-card" role="listitem"><div class="fmt-media"><a href="/samples/{FA_SAMPLE[0]}/"><img src="/assets/samples/{FA_SAMPLE[0]}-top.png" width="600" height="900" loading="lazy" alt="The top of Client Update, a sample client update for an accounting firm: {html.escape(FA_SAMPLE[3])}"></a></div>
        <div class="fmt-txt"><b>{FA_SAMPLE[1]}</b><p>"{html.escape(FA_SAMPLE[3])}"</p>
        <p class="fmt-date">Sample written by LongLens, {FA_SAMPLE_DATE}.</p><a class="txtlink" href="/samples/{FA_SAMPLE[0]}/">Read the whole update</a></div></div>
    </div>
    </div>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head">      <h2>Explain each change once,|and every client hears it from you</h2></div>
    <div class="cards">
      <div class="card"><h3>Your clients get|what a change means for them,|not the press release</h3><p>Each update says in plain words what a change means for your clients, with a link to every original. {FA_SETUP} Examples: {FA_AUTH}. Sources with a news feed work when pasted; some government pages need us to set them up by hand.</p></div>
      <div class="card"><h3>You see every issue first,|with the original one click away</h3><p>Every name, title and number links to the original article. Every issue comes to you first, and you decide what your clients get by email.</p></div>
      <div class="card"><h3>Every line sounds like your firm,|and any claim is one click|from its original</h3><p>LongLens writes the first version with AI. Make it yours: change any line you like, and follow any story to its original. LongLens cannot promise that a draft is right, so your judgement is what your clients are reading.</p><p>Tell LongLens what you want the way you would tell a new junior: say it once in a reply to any update, and every update after follows it.</p></div>
      <div class="card"><h3>When a deadline moves,|clients see it in the same story,|not as a second surprise</h3><p>LongLens watches for updates and reversals and links back to earlier coverage, so a moved deadline reads as part of the story your clients already know.</p></div>
      <div class="card"><h3>Show clients^what keeps coming up,|so they know to ask you first</h3><p>After your first few updates, each one shows what keeps coming up across the last few weeks.</p></div>
      <div class="card"><h3>Reach the client|who would rather listen than read</h3><p>Each update is an {F_EMAIL}, a {F_POD} for the client who listens on the drive in, a {F_REEL} for the one who lives on their phone, and an {F_EXPL} or an {F_INFO} for the one who wants it at a glance.</p></div>
      <div class="card"><h3>Know what changed in two minutes,|before your day starts</h3><p>Each update takes about two minutes to read. Updates come to you weekdays at 07:00, or the days and time you choose.</p></div>
      <div class="card"><h3>Clients hear it from you,|and only you</h3><p>The update comes to you first. {CLIENT_LINE_FIRM} {SEND_SETUP} Or forward it from your own email.</p></div>
    </div>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head">      <h2>Read a week|of client updates free,|then decide</h2></div>
    <ul class="list">
      <li><strong>Send one short form.</strong> The sources you trust, the topics you cover, your email. Your first update arrives in about {FIRST_ISSUE_MINUTES} minutes.</li>
      <li><strong>Sign in with a link by email.</strong> No password to remember.</li>
      <li><strong>Read a week of updates</strong> before your clients see any, then keep going or stop.</li>
    </ul>
    <p class="price-line">Prices in US dollars, after the free week. The first plans are paid by invoice.</p>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head">      <h2>Straight answers|before you start</h2></div>
    <div class="faq">{FA_FAQ}</div>
  </div>
</section>

{close_cta("See a week|of client updates, free.",
           f"Be the first voice your clients hear when the rules change. Name the sources you trust, list your topics, add your email. Your first update arrives in about {FIRST_ISSUE_MINUTES} minutes, and you read a week of updates before your clients see any.",
           FA_CTA)}'''

# slug, short label (breadcrumbs, llms.txt), title, description, body, nav-current, what the page
# is for (llms.txt). Titles stay under 60 characters and descriptions under 155 (check_output).
PAGES = [
    ("", "Home", "Client newsletter: clients hear the news from you | LongLens",
     f"Your clients hear what changed in your field from you first, in a client newsletter under your name. {OFFER_LINE}.",
     HOME, "", "what LongLens does, the formats, who it is for, prices"),
    ("features", "Features", "Reach people who never read a newsletter | LongLens",
     f"Reach every client the way they take in news: one client newsletter as {F_EMAIL}, {F_POD}, {F_REEL}, {F_INFO}, {F_CAR} and {F_EXPL}.",
     FEATURES, "/features/", "every format, where issues go, editing on the page, changing it by reply, what LongLens does not do"),
    ("pricing", "Pricing", f"Client newsletter pricing: from ${PRICE_SOLO} a month | LongLens",
     f"Free for a week. Then Solo at ${PRICE_SOLO} a month or Business at ${PRICE_BUSINESS} a month, invoiced, and what each includes today.",
     PRICING, "/pricing/", "Free week, Solo and Business, with a table of what each includes"),
    ("how-it-works", "How it works", "Your first client newsletter in minutes | LongLens",
     f"Your first client newsletter is with you in about {FIRST_ISSUE_MINUTES} minutes: name the websites you trust and your topics, then change any line before your clients read it.",
     HOW, "/how-it-works/", "from the start form to the first issue, and how stories are picked"),
    ("faq", "FAQ", "Client newsletter questions answered | LongLens",
     "Straight answers: how soon your clients hear from you, what reaches them and when, whether it sounds like you, price and ownership.",
     FAQ, "/faq/", "answers on control, client details, formats, price and ownership"),
    ("for-accountants", "For accountants", "Accountant client newsletter: first on new rules | LongLens",
     f"Be the accountant clients hear from first: a client newsletter on each tax and rule change, under your firm's name. {OFFER_LINE}.",
     FOR_ACCOUNTANTS, "", "LongLens as a client newsletter for accounting firms"),
    ("contact", "Start a free week", "Start your free week of client newsletters | LongLens",
     "Read what your clients would hear from you, free for a week: one short form, and your first issue is with you within minutes.",
     CONTACT, "", "the three-field start form"),
    ("sign-in", "Sign in", "Sign in | LongLens",
     "Sign in to LongLens with a link by email. No password.", SIGNIN_PAGE, "", "sign in with a link by email, no password"),
    ("privacy", "Privacy", "Privacy | LongLens",
     "This site counts visits with Cloudflare Web Analytics and sets no cookies. What happens when you write, and where the app's privacy page is.",
     PRIVACY, "", "this site counts visits with Cloudflare Web Analytics and sets no cookies"),
    ("terms", "Terms", "Terms | LongLens",
     "Plain terms for LongLens: the free week, your content and readers stay yours, stop any time, Danish law. Run by Hedge Holding ApS.",
     TERMS, "", "plain terms: the free week, ownership, stopping, Danish law, who runs LongLens"),
]

# --------------------------------------------------------------------------------------------
# Structured data (JSON-LD). Built from the same constants as the pages: PLANS from the one price
# source, FAQPage from FAQ_ITEMS, so the markup always says what the page says. No operating
# company is named: the publisher is the LongLens brand until Geoff decides who runs it. The
# founder has ONE VES Award win (Changeling); the Invictus nomination is not an award.
# --------------------------------------------------------------------------------------------

PLANS = (
    ("Free week", PRICE_FREE, "A week of real issues, no card. One newsletter, as many sources as you like, up to 25 readers."),
    ("Solo", PRICE_SOLO, ". ".join(SOLO_ROWS) + "."),
    ("Business", PRICE_BUSINESS, "Everything in Solo. " + ". ".join(BUSINESS_ROWS) + "."),
)


def ld(graph: list) -> str:
    doc = {"@context": "https://schema.org", "@graph": graph}
    return ('<script type="application/ld+json">'
            + json.dumps(doc, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>")


def plain(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", fragment))).strip()


PERSON = {"@type": "Person", "@id": PERSON_ID, "name": "Geoffrey Hancock", "url": GEOFF_SITE,
          "sameAs": [GEOFF_SITE],
          "award": "VES Award, Outstanding Supporting Visual Effects in a Feature Motion Picture, for Changeling"}
ORG = {"@type": "Organization", "@id": ORG_ID, "name": "LongLens", "url": SITE + "/",
       "logo": SITE + "/assets/mark-e1-512.png", "description": DEFINITION,
       "disambiguatingDescription": "LongLens at getlonglens.com, the newsletter service.",
       "founder": PERSON, "sameAs": [YOUTUBE]}
WEBSITE = {"@type": "WebSite", "@id": SITE + "/#site", "name": "LongLens", "url": SITE + "/",
           "publisher": {"@id": ORG_ID}}


def offer(name: str, price: int, desc: str) -> dict:
    o = {"@type": "Offer", "name": name, "price": str(price), "priceCurrency": CURRENCY,
         "description": desc, "url": SITE + "/pricing/"}
    if price:
        o["priceSpecification"] = {"@type": "UnitPriceSpecification", "price": str(price),
                                   "priceCurrency": CURRENCY, "unitCode": "MON", "billingDuration": "P1M"}
    else:
        o["eligibleDuration"] = {"@type": "QuantitativeValue", "value": FREE_DAYS, "unitCode": "DAY"}
    return o


PRODUCT = {"@type": "SoftwareApplication", "@id": SITE + "/#product", "name": "LongLens",
           "url": SITE + "/", "applicationCategory": "BusinessApplication", "operatingSystem": "Web",
           "description": DEFINITION, "publisher": {"@id": ORG_ID},
           "offers": [offer(*p) for p in PLANS]}


def faq_page() -> dict:
    return {"@type": "FAQPage", "@id": SITE + "/faq/#faq",
            "mainEntity": [{"@type": "Question", "name": plain(q),
                            "acceptedAnswer": {"@type": "Answer", "text": plain(a)}}
                           for _, items in FAQ_ITEMS for q, a in items]}


def breadcrumbs(slug: str, label: str) -> dict:
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": label, "item": f"{SITE}/{slug}/"}]}


def graph_for(slug: str, label: str) -> list:
    g = [ORG, WEBSITE]
    if slug in ("", "pricing"):
        g.append(PRODUCT)
    if slug == "faq":
        g.append(faq_page())
    if slug:
        g.append(breadcrumbs(slug, label))
    return g


def render_site() -> list[tuple[str, str, Path]]:
    """Every generated page as (slug, html, target), in memory: nothing is written until
    check_output() has passed, so a refused build leaves no failing page on disk."""
    out = []
    for slug, label, title, desc, body, cur, _about in PAGES:
        target = ROOT / "index.html" if slug == "" else ROOT / slug / "index.html"
        out.append((slug, page(slug, title, desc, body, cur, graph=graph_for(slug, label)), target))
    out.append(("thanks", page("thanks", "Thanks | LongLens", "Your start link is on its way.", THANKS,
                               robots="noindex"), ROOT / "thanks" / "index.html"))
    out.append(("contact/thanks-first-issue",
                page("contact/thanks-first-issue", "Thanks | LongLens", "Your first issue is on its way.",
                     THANKS_FIRST, robots="noindex", signin=False),
                ROOT / "contact" / "thanks-first-issue" / "index.html"))
    out.append(("contact/thanks-personal",
                page("contact/thanks-personal", "Thanks | LongLens", "Geoff will reply to you personally.",
                     THANKS_PERSONAL, robots="noindex"),
                ROOT / "contact" / "thanks-personal" / "index.html"))
    out.append(("404", page("404", "Not found | LongLens", "That page is not here.", NOT_FOUND,
                            robots="noindex"), ROOT / "404.html"))
    return out


def write_site(rendered: list[tuple[str, str, Path]]) -> list[tuple[str, str]]:
    for _slug, doc, target in rendered:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(doc, encoding="utf-8")
    return [(slug, doc) for slug, doc, _t in rendered if slug in {p[0] for p in PAGES}]


def data_uri(rel: str) -> str:
    p = ROOT / rel.lstrip("/")
    mime = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
    if p.suffix == ".m4a":
        mime = "audio/mp4"
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def write_preview(pages: list[tuple[str, str]]) -> None:
    """Every page in one self-contained file: CSS inline, media as data URIs, links between
    pages turned into in-file anchors. For review only; never published."""
    css = (ROOT / "assets" / "site.css").read_text(encoding="utf-8")
    anchors = {("/" if s == "" else f"/{s}/"): ("page-home" if s == "" else f"page-{s}") for s, *_ in PAGES}
    sections = []
    for slug, doc in pages:
        body = re.search(r"<body>\n(.*)\n</body>", doc, re.S).group(1).replace(CF_BEACON, "")
        label = "/" if slug == "" else f"/{slug}/"
        sections.append(f'<div id="{anchors[label]}" class="preview-page">'
                        f'<p class="preview-tag">getlonglens.com{label}</p>{body}</div>')
    joined = "\n".join(sections)
    joined = joined.replace(' id="main"', "").replace('<a class="skip" href="#main">Skip to content</a>', "")
    for path, anchor in sorted(anchors.items(), key=lambda kv: -len(kv[0])):
        joined = joined.replace(f'href="{path}"', f'href="#{anchor}"')
    cache = {}

    def inline(m):
        attr, rel = m.group(1), m.group(2)
        if rel not in cache:
            cache[rel] = data_uri(rel)
        return f'{attr}="{cache[rel]}"'

    joined = re.sub(r'(src|href|poster|srcset)="(/assets/[^"]+)"', inline, joined)
    fav = data_uri("/assets/favicon.svg")
    preview = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LongLens site preview</title>
<meta name="robots" content="noindex">
<link rel="icon" type="image/svg+xml" href="{fav}">
<style>{css}
.preview-page{{border-bottom:6px solid var(--accent)}}
.preview-tag{{font-family:var(--mono);font-size:12px;background:var(--accent);color:var(--on-accent);padding:6px 16px;margin:0}}
header.top{{position:static}}
</style>
</head>
<body>
<p class="preview-tag">Preview of getlonglens.com (branch site-v1), every page in one file. Not published.</p>
{joined}
</body>
</html>
'''
    (ROOT / "preview.html").write_text(preview, encoding="utf-8")


def llms_txt() -> str:
    """/llms.txt (llmstxt.org): a plain-text fact sheet for AI assistants and agents, generated
    from the same constants as the pages so a price or page change cannot leave it stale. Not in
    the sitemap: it is not a page for search results."""
    url = lambda slug: SITE + ("/" if slug == "" else f"/{slug}/")
    pages = "\n".join(f"- [{label}]({url(slug)}): {about}" for slug, label, _t, _d, _b, _c, about in PAGES
                      if slug not in ("sign-in", "privacy", "terms"))
    optional = "\n".join(f"- [{label}]({url(slug)}): {about}" for slug, label, _t, _d, _b, _c, about in PAGES
                         if slug in ("sign-in", "privacy", "terms"))
    plans = "\n".join(
        f"- {name}: ${price}" + ("" if not price else " a month") + f". {desc}" for name, price, desc in PLANS)
    return f"""# LongLens

> LongLens (getlonglens.com) writes a newsletter for a business, under the business's own name. It finds what changed in the business's field, writes an issue that says what it means for the business's clients. The owner can change the words of any issue on the page before sending it, and every issue comes to the owner first. {FORMAT_LADDER} {OFFER_LINE}.

{DEFINITION}

LongLens is for any business whose clients ask "what does this mean for me?": accountants, law firms, vet practices, consultants, coaches, recruiters, schools, clubs and associations. It is not a visual effects product. The VFX Supervisor Daily, its founder's own newsletter about his own field, is one example of what it makes.

How it differs from a feed in an email: LongLens judges each story against what the owner said their readers care about. Each story is retold in plain words with a line on why it matters to the reader, the same story from two outlets appears only once, a story readers already had comes back only when something changed, marked as an update, and every story links to its original.

How owners change it: hit Reply on any issue and write what you want in plain words, such as "shorter" or "more on the new rules". LongLens answers in the same email thread with what it understood, and the next issue follows it. Reply UNDO to take a change back. Owners can also click any line of an issue and type.

Prices, in US dollars, paid by invoice. {OFFER_LINE}.
{plans}

How to start: fill in the form at {SITE}/contact/ with the websites or feeds to follow (optional), the topics to follow, and an email address. The first issue arrives by email in about {FIRST_ISSUE_MINUTES} minutes. After that, issues arrive on weekdays at 07:00 local time, or on the days and time the owner picks. Every issue ends with a Stop button.

LongLens does not write a business's own company news, and does not run ads or paid subscriptions.

LongLens was built by Geoffrey Hancock, a visual effects supervisor and VES Award winner for Changeling, who runs his own newsletter on it.

## Pages

{pages}

## Examples

- [The VFX Supervisor Daily]({DAILY}): Geoffrey Hancock's own newsletter, made with LongLens
- [A sample issue for an accounting firm's clients]({SITE}/samples/uk-accounting/): written by LongLens from real UK news for an invented Manchester firm
- [A sample issue for a bakery owners' community]({SITE}/samples/bakery/): written by LongLens from real news for an invented community

## Optional

{optional}
- [LongLens on YouTube]({YOUTUBE})
- [About the founder]({GEOFF_SITE}longlens/)
"""


def beacon_samples() -> None:
    """The sample issues under samples/ are static pages made elsewhere (the pipeline's own
    render), so the analytics beacon is added here, once, before </body>. Idempotent."""
    if not CF_BEACON:
        return
    for f in sorted(ROOT.glob("samples/*/index.html")):
        doc = f.read_text(encoding="utf-8")
        if "static.cloudflareinsights.com/beacon.min.js" in doc:
            continue
        assert doc.count("</body>") == 1, ("sample page without one </body>", f)
        f.write_text(doc.replace("</body>", CF_BEACON + "\n</body>"), encoding="utf-8")


def write_seo() -> None:
    urls = "".join(f"  <url><loc>{SITE}{'/' if s == '' else '/' + s + '/'}</loc></url>\n" for s, *_ in PAGES)
    (ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + '</urlset>\n', encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
    (ROOT / "llms.txt").write_text(llms_txt(), encoding="utf-8")


# Words that never reach a buyer (house rules), checked on every page's visible text, alt text,
# JSON-LD and llms.txt: the house words with their plurals and inflections, and the hedges.
BANNED = re.compile(r"\b(pilot(?:s|ed|ing)?|editions?|trad(?:e|es|ed|ing|er|ers)|brief(?:s|ed|ing)?|"
                    r"digest(?:s|ed)?|dispatch(?:es|ed)?|verified|fact-checked|audit(?:s|ed|ing|or|ors)?|"
                    r"train(?:s|ed|ing|er|ers)?|secure[sd]?|confidential|GDPR|NotebookLM|Gemini|Roadbuilder|Ida|"
                    r"Midday|Road Intelligence|usually|some issues|often|typically|most)\b|\u2014", re.I)
# "most" is a hedge ("most issues"), but a superlative ("what matters most", "the most") is not.
MOST_OK = re.compile(r"(?:\bthe |\bmatters? |\bneed )most\b|\bmost\b(?= need\b)", re.I)


class BuildRefused(SystemExit):
    pass


def refuse(*why) -> None:
    raise BuildRefused("build refused, nothing written: " + repr(why))


def check_output(pages: list[tuple[str, str]]) -> None:
    """Refuse to finish a build that breaks the one price source, the house words, the title and
    description lengths, or the JSON-LD (every block must parse)."""
    prices = {str(p) for _, p, _ in PLANS}
    texts = []
    for slug, doc in pages:
        title = re.search(r"<title>(.*?)</title>", doc).group(1)
        desc = re.search(r'<meta name="description" content="([^"]*)"', doc).group(1)
        if len(html.unescape(title)) > 60:
            refuse("title over 60", slug, title)
        if len(html.unescape(desc)) > 155:
            refuse("description over 155", slug, desc)
        ld_text = []
        for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', doc, re.S):
            try:
                ld_text.append(json.dumps(json.loads(block), ensure_ascii=False))
            except ValueError as exc:
                refuse("JSON-LD does not parse", slug, str(exc))
        alts = " ".join(html.unescape(a) for a in re.findall(r'\balt="([^"]*)"', doc))
        # Tags become spaces here, so words in adjacent elements never glue together and hide a hit.
        visible = plain(re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)\b.*?</\1>", "", doc, flags=re.S)))
        texts.append((slug, " ".join([visible, title, desc, alts] + ld_text)))
    texts.append(("llms.txt", llms_txt()))
    for slug, text in texts:
        bad = sorted({p for p in re.findall(r"\$(\d+)", text)} - prices)
        if bad:
            refuse("price not from the one price source", slug, bad)
        for hit in BANNED.finditer(text):
            if hit.group(0).lower() == "most" and any(
                    m.start() <= hit.start() < m.end() for m in MOST_OK.finditer(text)):
                continue
            refuse("house rule", slug, hit.group(0), text[max(0, hit.start() - 60):hit.end() + 60])


if __name__ == "__main__":
    rendered = render_site()
    check_output([(slug, doc) for slug, doc, _t in rendered])
    write_seo()
    built = write_site(rendered)
    beacon_samples()
    write_preview(built)
    print("built", len(PAGES) + 1, "pages and preview.html")
