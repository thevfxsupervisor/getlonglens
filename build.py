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
LINK_LINE = "Every link is checked, and dead links are dropped."
AI_LINE = "AI drafts each issue from the news you trust, and LongLens checks names and figures against the original story. You read and change every line first, so every line sounds like you."


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
    return f'''<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <div class="wrap">
    <a class="brand" href="/" aria-label="LongLens home"><img src="/assets/mark-e1.svg" alt="" width="32" height="32"><span>LongLens</span></a>
    <a class="btn btn-a hdr-cta" href="/contact/">{CTA_LABEL}</a>
    <nav aria-label="Main">{links}{'<a href="/sign-in/">Sign in</a>' if signin else ""}<a class="btn btn-a" href="/contact/">{CTA_LABEL}</a></nav>
  </div>
</header>'''


def footer() -> str:
    links = "".join(f'<a href="{h}">{l}</a>' for l, h in NAV)
    return f'''<footer>
  <div class="wrap">
    <div>
      <p class="by">LongLens. Built by <a href="{GEOFF_SITE}">Geoffrey Hancock</a>.</p>
      <p class="tiny">No tracking, no cookies on this site.</p>
    </div>
    <nav aria-label="Footer">{links}<a href="/contact/">Free week</a><a href="/sign-in/">Sign in</a><a href="/privacy/">Privacy</a></nav>
  </div>
</footer>'''


def page(slug: str, title: str, description: str, body: str, current: str = "",
         robots: str = "", signin: bool = True) -> str:
    path = "/" if slug == "" else f"/{slug}/"
    canonical = SITE + path
    robots_tag = f'\n<meta name="robots" content="{robots}">' if robots else ""
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="canonical" href="{canonical}">{robots_tag}
<meta name="theme-color" content="#131619">
<meta property="og:type" content="website">
<meta property="og:site_name" content="LongLens">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE}/assets/og-card.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(title)}">
<meta name="twitter:description" content="{html.escape(description)}">
<meta name="twitter:image" content="{SITE}/assets/og-card.png">
<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">
<link rel="icon" type="image/png" sizes="64x64" href="/assets/favicon-64.png">
<link rel="apple-touch-icon" href="/assets/mark-e1-96.png">
<link rel="stylesheet" href="/assets/site.css">
</head>
<body>
{header(current, signin)}
<main id="main">
{body}
</main>
{footer()}
</body>
</html>
'''


CTA_TEXT = "See what your clients would hear from you, free"
HERO_OFFER = "AI writes the first version, you make it yours, and only your name is on it. Free for a week, then from $19 a month."


def close_cta(h2: str, text: str, cta: str = "") -> str:
    return f'''<section class="close">
  <div class="wrap"><div>
    <h2>{h2}</h2>
    <p class="k">{text}</p>
    <div class="cta-row"><a class="btn btn-a" href="/contact/">{cta or CTA_TEXT}</a></div>
  </div></div>
</section>'''


M = "/assets/media/"

EXAMPLE_LABEL = "Geoff's own newsletter about his own field, visual effects for film and TV"

# One name per format, used on every page (term map: newsletter-samples/research/
# media-audit-2026-11-07/TERMS-MAP.md). "Reel" is our label for the format, never a product name.
F_EMAIL, F_POD, F_REEL, F_EXPL, F_INFO, F_CAR = (
    "Email", "Podcast", "Reel", "Explainer video", "Infographic", "Carousel")
F_LEADS = (f"the full {F_EMAIL}, a short {F_EMAIL} with a button to the whole issue, "
           f"the {F_POD}, the {F_REEL}, the {F_INFO} or the {F_EXPL}")

# What a reader can count on, per format (app media ladder, 2026-11-08): the Email goes out with
# every issue; the Podcast (two AI voices, else one AI voice reading), the Reel and the Infographic
# are attempted for every issue but can be left off (no public story in the issue, or not right);
# the Carousel was switched on 2026-11-08 with no track record yet, and the Explainer video has no
# fallback when the shared allowance runs out. Never "every issue" for anything but the Email.
FORMAT_LADDER = (f"The {F_EMAIL} comes with every issue. Most issues also bring a {F_POD}, a {F_REEL} "
                 f"and an {F_INFO}; some bring a {F_CAR} or an {F_EXPL}.")

FORMAT_STRIP = f'''<p class="eyebrow strip-label">Real examples from Geoff's own newsletter, with their dates</p>
<div class="fmt-strip" role="list" aria-label="One issue in five formats, real examples">
  <div class="fmt-card" role="listitem"><div class="fmt-media tall"><a href="{M}read-letter.png"><img src="{M}read-letter.png" width="780" height="1276" loading="lazy" alt="Geoff's own issue of 13 Oct 2026 as an email on a phone: the date, the headline and a short paragraph on what it means for the reader."></a></div>
    <div class="fmt-txt"><b>{F_EMAIL}</b><p>What changed and what it means, in two minutes.</p><p class="fmt-date">13 Oct 2026</p></div></div>
  <div class="fmt-card" role="listitem"><div class="fmt-media"><img src="{M}issue-audio-wave.png" width="780" height="352" loading="lazy" alt="The sound wave of the audio clip below."></div>
    <div class="fmt-txt"><b>{F_POD}</b><p>Two AI voices talk the issue through, or one AI voice reads it.</p>
    <audio controls preload="none" src="{M}issue-audio.m4a" aria-label="The first 16 seconds of the issue's Podcast"></audio><p class="fmt-date">13 Oct 2026, the first 16 seconds</p></div></div>
  <div class="fmt-card" role="listitem"><div class="fmt-media"><a href="{M}issue-infographic.jpg"><img src="{M}issue-infographic.jpg" width="1280" height="714" loading="lazy" alt="An infographic of a whole issue: headed panels, each with a drawing and a short line."></a></div>
    <div class="fmt-txt"><b>{F_INFO}</b><p>The whole issue on one image.</p><p class="fmt-date">30 Oct 2026</p></div></div>
  <div class="fmt-card" role="listitem"><div class="fmt-media"><video controls preload="none" playsinline poster="{M}issue-explainer-poster.jpg" src="{M}issue-explainer.mp4" width="640" height="360" aria-label="The first 15 seconds of an Explainer video"></video></div>
    <div class="fmt-txt"><b>{F_EXPL}</b><p>A few narrated minutes, a drawing for each point.</p><p class="fmt-date">1 Nov 2026, the first 15 seconds of 7 minutes</p></div></div>
  <div class="fmt-card" role="listitem"><div class="fmt-media tall"><video controls preload="none" playsinline poster="{M}issue-short-poster.jpg" src="{M}issue-short.mp4" width="540" height="960" aria-label="The first 15 seconds of a Reel, a short vertical video"></video></div>
    <div class="fmt-txt"><b>{F_REEL}</b><p>Captioned vertical video, sized for Instagram Reels, TikTok and YouTube Shorts.</p><p class="fmt-date">4 Nov 2026, the first 15 seconds</p></div></div>
</div>
<p class="fmt-hint">{FORMAT_LADDER} Geoff's newsletter is about his field; yours is about yours.</p>'''

EDITOR_SHOT = f'''<figure class="shot"><a href="{M}edit-in-place.png"><img src="{M}edit-in-place.png" width="1100" height="770" loading="lazy" alt="The LongLens editor open on a real issue: a bar with Save, Discard and the inbox preview line on top, and every line of the issue below outlined, ready to click and change."></a><figcaption>The real editor, on {EXAMPLE_LABEL}, 13 Oct 2026.</figcaption></figure>'''

PROOF = f'''<div class="proof">
  <b>Who built it</b>
  <p>Geoffrey Hancock, VES Award winner for Changeling, built LongLens and runs his own newsletter on it most mornings. Yours covers your field.</p>
  <p class="links"><a href="{DAILY}">Read Geoff's own newsletter</a></p>
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
SAMPLE_DATE = "Wed 4 Nov 2026"


def samples_section() -> str:
    if not SAMPLES:
        return ""
    cards = "".join(
        f'<div class="fmt-card" role="listitem"><div class="fmt-media tall">'
        f'<a href="/samples/{slug}/"><img src="/assets/samples/{slug}-top.png" width="600" height="900" loading="lazy" '
        f'alt="The top of {html.escape(name)}, a sample issue: {html.escape(headline)}"></a></div>'
        f'<div class="fmt-txt"><b>{html.escape(name)}</b><p>{html.escape(who)}. <a href="/samples/{slug}/">Read the issue</a></p></div></div>'
        for slug, name, who, headline, how in SAMPLES)
    return f'''<hr class="rule">
<section class="skim">
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Sample issues</span>
      <h2>Your clients get what the news means for them, not a pile of links</h2>
      <p>Three invented businesses, three issues LongLens wrote from real news on {SAMPLE_DATE}.</p></div>
    <div class="fmt-strip six" role="list" aria-label="Sample issues for other businesses">{cards}</div>
  </div>
</section>'''


TODAY_PLACES = ("Your inbox first, then your existing clients' inboxes, with a one-click opt-out in every email",
                "A web page for every issue you publish",
                "A public page of all your issues",
                "Your Slack or Discord channel",
                "A private RSS feed")
COMING_PLACES = ("Your Podcast in podcast apps",
                 "Your Reel and Carousel ready to post to your own Instagram, LinkedIn and TikTok",
                 "A block on your website", "Telegram")

# The home headline's two rotating words: the audience and the verb. The first of each is the
# static headline (no script, screen readers). Reduced motion still swaps the words, as a plain
# fade with no movement. Each box is the width of the word showing, so a short word leaves no gap.
# Every pair makes a complete, true sentence: "Your ___ ___ the news from you."
ROT = ("clients", "prospects", "members", "customers", "readers")
ROT_VERBS = ("hear", "read", "watch")


def rot_words(words) -> str:
    return "".join(('<span class="on">' if i == 0 else "<span>") + w + "</span>" for i, w in enumerate(words))


ROT_WORDS = rot_words(ROT)
ROT_VERB_WORDS = rot_words(ROT_VERBS)
ROT_JS = """<script>
(function(){
  var h = document.querySelector('.rot-h1'); if (!h) return;
  var groups = h.querySelectorAll('.rot'), paused = false, t = 0;
  var g = Array.prototype.map.call(groups, function(r){ return {w: r.querySelectorAll(':scope > span'), i: 0}; });
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
  <div class="wrap">
    <span class="eyebrow"><img src="/assets/mark-e1.svg" alt="" width="40" height="40">LongLens</span>
    <h1 class="rot-h1"><span class="sr-only">Your clients hear the news from you.</span><span aria-hidden="true">Your <span class="rot">{ROT_WORDS}</span> <span class="rot rot-v">{ROT_VERB_WORDS}</span> the news from you.</span></h1>
    <p class="lede">LongLens tells your clients what changed and what it means for them. You see every issue first, with every original one click away.</p>
    <div class="cta-row">
      <a class="btn btn-a" href="/contact/">{CTA_TEXT}</a>
    </div>
    <p class="price-line">{HERO_OFFER} <a href="/pricing/">See prices</a>.</p>
  </div>
</section>

{samples_section()}

<hr class="rule">
<section class="skim">
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">{F_EMAIL}, {F_POD}, {F_REEL} and more</span>
      <h2>Reach the people who never read a newsletter</h2>
      <p>The commuter plays the {F_POD}. The scroller watches the {F_REEL}. Everyone else reads the {F_EMAIL}.</p></div>
    {FORMAT_STRIP}
  </div>
</section>

<hr class="rule">
<section class="skim">
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Your name, your words</span>
      <h2>Every line sounds like you</h2>
      <p>Click any line and type. Or reply "more on the new rules", and LongLens follows it from the next issue.</p></div>
    <div class="feat">
      <ul class="skim-pts">
        <li><strong>Your name only</strong>Your name, logo and colours on every issue, never ours.</li>
        <li><strong>Your words on top</strong>The headline, the opening and the line people see in their inbox.</li>
        <li><strong>Facts that point home</strong>Every story links to where it came from.</li>
      </ul>
      {EDITOR_SHOT}
    </div>
  </div>
</section>

<hr class="rule">
<section class="skim">
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Who it is for</span>
      <h2>For any business whose clients ask "what does this mean for me?"</h2>
      <p>Accountants, law firms, vet practices, consultants, coaches, clubs and associations.</p></div>
    <ul class="skim-pts three">
      <li><strong>Firms</strong>A new rule lands, and your clients hear what it means from you first. <a href="/for-accountants/">See one for accountants</a>.</li>
      <li><strong>Consultants and coaches</strong>Week after week, people see you know your field.</li>
      <li><strong>Clubs and associations</strong>Something worth opening between events.</li>
    </ul>
  </div>
</section>

<hr class="rule">
<section class="skim">
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Price</span>
      <h2>Free for a week. Then from $19 a month.</h2>
      <p>No card and no call. Your first issue is with you in about {FIRST_ISSUE_MINUTES} minutes.</p></div>
    <ul class="skim-pts three">
      <li><strong>Free week</strong>A week of real issues, in every format, for you to judge.</li>
      <li><strong>Solo, $19 a month</strong>Your newsletter in your name, sent to your existing clients for you.</li>
      <li><strong>Business, $95 a month</strong>A custom design, plus a public page, Slack or Discord and RSS, so new people can follow you.</li>
    </ul>
    <p class="k"><a href="/pricing/">Compare the plans</a></p>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">{PROOF}</div>
</section>

{close_cta("Be the first your clients hear from, starting this week.",
           f"Name a few websites you trust, list your topics, add your email. Your first issue arrives in about {FIRST_ISSUE_MINUTES} minutes.")}
{ROT_JS}'''

# --------------------------------------------------------------------------------------------
# Features
# --------------------------------------------------------------------------------------------

FEATURES = f'''<section class="hero">
  <div class="wrap">
    <span class="eyebrow">Features</span>
    <h1>Your readers learn what changed in your field from you, in the form they will take in.</h1>
    <p class="lede">Reach the people who never read a newsletter: a {F_POD} for the drive in, a {F_REEL} for their phone, and the {F_EMAIL} for everyone else.</p>
    <p class="price-line">{AI_LINE}</p>
    {FORMAT_STRIP}
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Every format</span>
      <h2>Meet each reader the way they like to take in news</h2>
      <p>Whichever way a reader opens you, they get the same news. Every format that is live today is switched on for a new account, and each comes from the same stories.</p></div>
    <div class="cards">
      <div class="card"><h3>{F_EMAIL}</h3><p>What changed and what it means for them, with a link to every original story, in their inbox and on the web once you publish the issue. For the reader with no time, a short version: the one line that matters most and a button to the whole issue.</p></div>
      <div class="card"><h3>{F_POD}</h3><p>Your news in their ears on the drive in: two AI voices talk the issue through, or one AI voice reads it. With most issues.</p></div>
      <div class="card"><h3>{F_REEL}</h3><p>A short vertical video with captions that keeps you on their phone, sized for Instagram Reels, TikTok and YouTube Shorts. With most issues.</p></div>
      <div class="card"><h3>{F_EXPL}</h3><p>A few minutes on the issue's stories, narrated, with a drawing for each point. On some issues.</p></div>
      <div class="card"><h3>{F_INFO}</h3><p>The whole issue on one image, for the reader who will not read. A drawing and a short line for each point. With most issues.</p></div>
      <div class="card"><h3>{F_CAR}</h3><p>Swipeable slides of the issue that show your followers you know your field. On some issues.</p></div>
      <div class="card"><h3>Story pictures</h3><p>Turn them on and your top stories each get a small picture in your colours, so the issue looks like yours. {coming("A picture generated for each story, in your own style.")}</p></div>
    </div>
    <ul class="list">
      <li><strong>Not every issue gets every format.</strong> The {F_EMAIL} always goes out. A format that does not come out right is left off that issue.</li>
      <li><strong>You pick what leads your own email</strong>: {F_LEADS}. The full letter always follows.</li>
      <li><strong>Each reader, their own way</strong>: today the public page of your issues carries every format side by side. {coming("Each reader picks once at the bottom of their email, and LongLens sends every issue that way.")}</li>
    </ul>

    <div class="sec-head"><span class="eyebrow">Where it goes</span>
      <h2>Be where your readers already are</h2>
      <p>Your newsletter's name and issue number are on every one, wherever it lands.</p></div>
    <div class="cards two">
      <div class="card"><h3>Where they can follow you now</h3><ul class="list">
        <li><strong>In your own inbox first</strong>, with every format on its page in your account.</li>
        <li><strong>In your clients' inboxes</strong>: {CLIENT_LINE} {SEND_SETUP} Or forward it from your own email.</li>
        <li><strong>On the web</strong>: each issue you publish gets a page of its own that anyone can open from a link, with no sign-in.</li>
        <li><strong>On a public page of all your issues</strong>, with every format of each issue. Geoff sets it up with you.</li>
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

    <div class="feat">
      <div class="txt">
        <h2>Your words, your view of the news: every line is yours before it goes out</h2>
        <p>Open any issue and press Edit in place. The issue opens exactly as your readers will see it, with every line you can change outlined. Click, type, Save. Discard puts back everything you have not saved.</p>
        <ul>
          <li><strong>What you can change</strong>: the headline, the opening paragraph, the inbox preview line, each section heading, the line on what each story means for your readers, each story summary, the quick links and the points to watch next.</li>
          <li><strong>What stays as published</strong>: story titles, links and the names of the websites they came from, so every fact still points home.</li>
          <li><strong>Type as you would in an email</strong>: on Save, the issue updates everywhere with your words.</li>
          <li><strong>Every version kept</strong>: the issue as LongLens first wrote it, and every save after that.</li>
          <li><strong>Locked once it goes out</strong>: once an issue is approved or sent, it stays exactly as it went.</li>
        </ul>
        <p class="tiny">Edit in place works on daily newsletters. A weekly newsletter has its own editor, section by section.</p>
      </div>
      {EDITOR_SHOT}
    </div>

    <div class="feat">
      <div class="txt">
        <h2>Put first what your readers most need to see</h2>
        <p>Lay your issue out like a page. On a daily newsletter, the Sections page lists every part of the issue, with a live preview of your latest issue beside it.</p>
        <ul>
          <li><strong>Your order</strong>: drag a section, or use the arrows, to move it.</li>
          <li><strong>Only what you need</strong>: hide a section with one tick, and show only as many topics as you want.</li>
          <li><strong>Your headings</strong>: rename the extra sections, such as quick links and what to watch, in your own words.</li>
          <li><strong>A note from you</strong>: add your own note, with its own heading, or a divider, anywhere in the issue.</li>
          <li><strong>Back to the usual</strong>: one button puts the usual sections back.</li>
        </ul>
        <p>Your next issue uses the new layout. Issues already written stay as they were.</p>
      </div>
      <div class="txt">
        <h2>Pictures that are yours to use</h2>
        <p>Turn on story pictures and your top stories each get a small picture beside them: a card drawn for your newsletter, in your colours, with the topic and the website the story came from. From one to six an issue, top stories only.</p>
        <ul>
          <li><strong>Never copied</strong>: LongLens never takes the picture from the article itself, so there is nothing to credit and nothing to take down.</li>
          <li><strong>Still reads well without them</strong>: the words come first, so the issue works in an inbox that hides pictures.</li>
          <li>{coming("A picture generated for each story, in your own style, never the article's own photo.")}</li>
        </ul>
      </div>
    </div>

    <div class="feat">
      <div class="txt">
        <h2>Tell LongLens once what your readers care about, and every issue after follows</h2>
        <p>Teach LongLens the way you would teach a new hire: reply to any issue in your own words. LongLens answers in the same thread with what it understood, and the next issue follows it.</p>
        <ul>
          <li><strong>Length</strong>: shorter, longer, or how many stories.</li>
          <li><strong>Topics</strong>: more of one thing, less of another.</li>
          <li><strong>Your readers</strong>: a new sentence about who they are and what matters to them.</li>
          <li><strong>Websites</strong>: paste a link to add one, name one to drop it.</li>
          <li><strong>Tone and layout</strong>: how it sounds, how each story is laid out.</li>
          <li><strong>Formats</strong>: add or drop a format, such as the {F_POD}.</li>
        </ul>
        <p>Reply UNDO to take back the last change. LongLens acts only on replies from you: a forward to a colleague changes nothing.</p>
      </div>
      <div class="exchange" aria-label="An example reply and the answer">
        <span class="who">You</span>
        <p class="you">Longer please. More on the new rules, less on conferences.</p>
        <span class="who">LongLens, in the same thread</span>
        <div class="ll">
          <p>Got it. Your issues will be the usual length from the next one.</p>
          <p>You'll see more on the new rules from the next issue.</p>
          <p>You'll see less on conferences from the next issue.</p>
          <p>Changed your mind? Just reply UNDO.</p>
        </div>
      </div>
    </div>

    <div class="feat">
      <div class="txt">
        <h2>Built from the websites, forums and videos your field already trusts</h2>
        <p>Every issue covers what is new on the websites, forums, YouTube channels and topics your field follows. Name them when you start, or paste a link into a reply any time.</p>
        <ul>
          <li><strong>Forward the newsletters you never open</strong>, or save a page from your phone or browser. What matters lands in your next issue under "You sent".</li>
          <li><strong>One tap to turn a website off</strong>, one more to turn it back on. LongLens never adds a website you turned off back by itself.</li>
          <li><strong>New websites, found for you</strong>: LongLens lists the ones your stories came from, each with a way to remove it.</li>
        </ul>
      </div>
      <div class="txt">
        <h2>Give clients facts they can check in one click: names and figures matched to the original, every link checked</h2>
        <ul>
          <li><strong>What it means for them</strong>: most stories carry one line on why they matter to your readers, so the issue is never a list of links.</li>
          <li><strong>No repeats</strong>: a story they have already seen stays out until something changes, then comes back marked as an update.</li>
          <li><strong>Names and figures</strong> are checked against the original story.</li>
          <li><strong>{LINK_LINE}</strong> The last line of each issue says how many links were checked.</li>
        </ul>
      </div>
    </div>

    <div class="feat">
      <div class="txt">
        <h2>On your desk when you sit down</h2>
        <p>LongLens arrives on weekdays at 07:00 your time to start, or on the days and at the time you pick.</p>
        <p>Away for a week? Press Pause this newsletter at the bottom of any issue. The same page starts it again.</p>
      </div>
      <div class="txt">
        <h2>Yours to keep</h2>
        <p>You own what LongLens writes for you: every issue, every website you chose, every lesson you taught LongLens.</p>
      </div>
    </div>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">An honest comparison</span>
      <h2>Three other ways to keep your clients up to date, and what each one costs you</h2></div>
    <div class="cards">
      <div class="card"><h3>By hand</h3><p>Read the industry press and write it up yourself. Full control. It costs the hours you do not have, and it stops the first busy week.</p></div>
      <div class="card"><h3>A newsletter platform</h3><p>Good at sending and at growing a list. No idea what to say. You still find the news and write every word.</p></div>
      <div class="card"><h3>A personal AI summary</h3><p>Fast, often free, and fine for keeping yourself informed. Written for you alone. Nobody else reads it, and your name is nowhere on it.</p></div>
    </div>
    <p class="k">LongLens tells your readers what the news in your field means for them, ready to send, as a letter and in every other format. You keep the name, the last word and the readers.</p>
    <div class="notfor"><h3>What LongLens does not do</h3><ul>
      <li><strong>Write your own company news.</strong> LongLens works from what the press, the forums and the videos in your field say. Your own announcements are still yours to write, and you can add them as a note in any issue.</li>
      <li><strong>Run ads or paid subscriptions.</strong> Use a newsletter platform built for that.</li>
      <li><strong>Replace you.</strong> Your judgment is the point. LongLens puts it in front of more people, issue after issue.</li>
    </ul></div>
  </div>
</section>

{close_cta("Be the first your clients hear from, starting this week.",
           f"Name a few websites you trust, list your topics, add your email. Your first issue is with you in about {FIRST_ISSUE_MINUTES} minutes.")}'''

# --------------------------------------------------------------------------------------------
# Pricing
# --------------------------------------------------------------------------------------------

PRICING = f'''<section class="hero skim-hero">
  <div class="wrap">
    <span class="eyebrow">Pricing</span>
    <h1>Free for a week. Then from $19 a month.</h1>
    <p class="lede">No card, no call. Your first issue is with you in about {FIRST_ISSUE_MINUTES} minutes.</p>
  </div>
</section>

<section class="skim" style="padding-top:0">
  <div class="wrap">
    <div class="plans">
      <div class="plan"><h2>Free week</h2>
        <p class="plan-price">$0</p>
        <p class="plan-outcome">Judge a week of real issues before anyone else sees them.</p>
        <ul>
          <li>Every format: {F_EMAIL}, {F_POD}, {F_REEL}, {F_INFO}, {F_CAR}, {F_EXPL}</li>
          <li>Change any line, or reply in plain words</li>
          <li>Your name only, in a look matched to your brand</li>
        </ul>
        <a class="btn btn-a" href="/contact/">Start my free week</a></div>
      <div class="plan lead"><h2>Solo</h2>
        <p class="plan-price">$19 <small>a month</small></p>
        <p class="plan-outcome">Keep your clients hearing from you, every week.</p>
        <ul>
          <li>A newsletter every day or every week</li>
          <li>Every format: {F_EMAIL}, {F_POD}, {F_REEL}, {F_INFO}, {F_CAR}, {F_EXPL}</li>
          <li>Your name, logo and colours, never ours</li>
          <li>Sent to your existing clients for you, with a one-click opt-out</li>
        </ul>
        <a class="btn btn-a" href="/contact/">Start with a free week</a></div>
      <div class="plan"><h2>Business</h2>
        <p class="plan-price">$95 <small>a month</small></p>
        <p class="plan-outcome">Reach people beyond your own list.</p>
        <ul>
          <li>Everything in Solo</li>
          <li>A custom design of your emails, pages and videos, built with you</li>
          <li>A public page of all your issues</li>
          <li>Each issue posted to your Slack or Discord channel, and an RSS feed</li>
          <li class="plan-coming">{coming(f"Your {F_POD} in podcast apps; your {F_REEL} and {F_CAR} ready to post to Instagram, LinkedIn and TikTok")}</li>
        </ul>
        <a class="btn btn-a" href="/contact/">Start with a free week</a></div>
    </div>
    <p class="price-line">{FORMAT_LADDER}</p>
    <p class="price-line">Prices in US dollars, after the free week, paid by invoice. {SEND_SETUP}</p>
  </div>
</section>

<hr class="rule">
<section class="skim">
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">The free week</span>
      <h2>One short form starts it. One click stops it.</h2>
      <p>Nothing to install, no password, and nothing owed if you stop.</p></div>
    <ul class="skim-pts three">
      <li><strong>Day one</strong>Your first issue arrives in about {FIRST_ISSUE_MINUTES} minutes.</li>
      <li><strong>Every weekday</strong>A new issue at 07:00 your time, or the days and time you choose.</li>
      <li><strong>Room to try</strong>One newsletter, up to 10 sources and 25 readers. Every issue ends with a Stop button.</li>
    </ul>
  </div>
</section>

{close_cta("Be the first your clients hear from, starting this week.",
           "One short form, then a week of real issues to judge before anyone else sees them.")}'''

# --------------------------------------------------------------------------------------------
# How it works
# --------------------------------------------------------------------------------------------

HOW = f'''<section class="hero">
  <div class="wrap">
    <span class="eyebrow">How it works</span>
    <h1>Stay in front of your clients, starting today. One short form and your first issue is with you in minutes.</h1>
    <p class="lede">Nothing to learn and no password to remember. From then on, change any line right on the issue, or reply in plain words, and every issue sounds more like you.</p>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Getting started</span><h2>See what your clients would read from you, in minutes</h2></div>
    <ol class="steps two">
      <li><h3>Get a free week, with your own news</h3>
        <p>Paste a few sources, list your topics, add your email.</p>
        <p><a href="/contact/">{CTA_TEXT}</a></p></li>
      <li><h3>Your first issue arrives in about {FIRST_ISSUE_MINUTES} minutes</h3>
        <p>By email, written from the sources and topics you gave. Already have an account? The email holds your sign-in link instead.</p></li>
      <li><h3>Every weekday morning, something worth passing on is in your inbox</h3>
        <p>On weekdays at 07:00 your time, with nothing to press. Every issue ends with a Stop button.</p></li>
      <li><h3>Make it yours: topics, websites, name and timing in one place</h3>
        <p>What it follows, its sources, its name, who reads it, and the days and time it arrives. Sooner? Open Issues and press Make an issue now: LongLens starts on it within ten minutes and emails it to you.</p></li>
    </ol>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Behind every issue</span><h2>Why your clients can trust what they read from you</h2>
      <p>Not a pasted feed. In our own daily issues, about 1 in 20 stories makes the cut.</p></div>
    <ol class="steps two">
      <li><h3>Stop checking ten websites a day</h3><p>LongLens reads the websites, feeds and channels you pick, and brings you what matters.</p></li>
      <li><h3>Each story is judged against what your readers care about</h3><p>Your replies, such as "more on X, less on Y", change what is chosen next time.</p></li>
      <li><h3>The same story from two outlets appears once</h3><p>A story your readers already had stays out unless something changed. Then it comes back marked as an update, linked to the earlier coverage.</p></li>
      <li><h3>Each story is written in LongLens's own words</h3><p>With a line on why it matters to your readers, not pasted from the original.</p></li>
      <li><h3>Names, titles and numbers are checked against the original article</h3><p>Every story keeps a link to the original.</p></li>
      <li><h3>{LINK_LINE}</h3><p>A line at the foot of each issue says how many links were checked.</p></li>
      <li><h3>A website that stops working or fills with junk is paused automatically</h3><p>You can see which one, and turn it back on with one tap.</p></li>
      <li><h3>You read it before your readers do</h3><p>Change any line first. {CLIENT_LINE}</p></li>
      <li><h3>The {F_POD}, {F_REEL} and the rest follow on most issues</h3><p>{FORMAT_LADDER} Each appears on the issue's page when it is ready.</p></li>
    </ol>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Day to day</span><h2>Five quick moves keep every issue yours</h2></div>
    <ul class="list">
      <li><strong>Change a line</strong>: open the issue, press Edit in place, click any line and type (daily newsletters; a weekly newsletter has its own editor).</li>
      <li><strong>Change the next issue</strong>: reply in plain words, for example "shorter please". The next issue follows it.</li>
      <li><strong>Undo a change</strong>: reply UNDO.</li>
      <li><strong>Pause it</strong>: press Pause this newsletter at the bottom of any issue. The same page starts it again.</li>
      <li><strong>Sign in</strong>: type your email on the <a href="/sign-in/">sign-in page</a> and a fresh link arrives by email, usually within a minute. Each link works once, and keeps you signed in for 30 days on that device.</li>
    </ul>
    <p class="k">Prefer to send it yourself? Forward any issue from your own email.</p>
  </div>
</section>

{close_cta("Be the first your clients hear from, starting this week.",
           "You read a week of real issues before anyone else does.")}'''

# --------------------------------------------------------------------------------------------
# FAQ
# --------------------------------------------------------------------------------------------

def qa(q, a):
    return f"<details><summary>{q}</summary>{a}</details>"


FAQ_ITEMS = [
    ("Getting started", [
        ("How soon can my clients start hearing from me?",
         f"<p>Your first issue is with you in about {FIRST_ISSUE_MINUTES} minutes, written from the websites and topics you gave. You read a week of real issues before anyone else does. Then {CLIENT_LINE[0].lower() + CLIENT_LINE[1:]} {SEND_SETUP}</p>"),
        ("Can I sign up on my own?",
         f"<p>Yes, from the form. <a href=\"/contact/\">Start your free week</a>. Your first issue arrives by email in about {FIRST_ISSUE_MINUTES} minutes. On a very busy day you get a start link instead: click it and answer three short questions.</p>"),
        ("How do I sign in?",
         "<p>With a link by email. There is no password. Type your email on the <a href=\"/sign-in/\">sign-in page</a> and a fresh link arrives, usually within a minute. Each link works once and keeps you signed in for 30 days on that device.</p>"),
    ]),
    ("Trust and control", [
        ("Is this just my news feeds pasted into an email?",
         "<p>No. LongLens judges each story against what you said your readers care about, and in our own daily issues about 1 in 20 stories makes the cut. What stays is written in LongLens's own words with a line on why it matters to your readers. The same story from two outlets appears once, names, titles and numbers are checked against the original article, and every link is checked, and dead links are dropped. Every story links to its original, one click away, and you read the issue before your readers do.</p>"),
        ("Does anything reach my clients before I see it?",
         "<p>No. Nothing goes to your clients until you approve it. Every issue comes to you by email first: you read it, change any line, and decide what to send and to whom. If your issues also go up on a public page on your own website, each one waits for your OK there too, unless you choose a setting that puts it up for you: Automatic, or Publish at noon without my take (if you have not added your own comment by 12:00, it goes up without it). Both are off until you choose them, you are emailed when an issue goes up, and what goes up also reaches your Slack or Discord channel and your feed.</p>"),
        ("What if LongLens gets something wrong?",
         "<p>You read every issue before your readers do, and you can change or cut any line. LongLens checks names and figures against the original story and links every story to it, so each fact can be checked in one click. Your name is on it, so the last word is yours.</p>"),
        ("Whose name is on what my clients read, and will it look like my brand?",
         "<p>Yours, and only yours, so it looks like your firm, not a template. On every plan, every issue carries your name, logo and colours, never ours. Business adds a custom design of your letters, pages and videos, built with you when you start.</p>"),
        ("Who is responsible for record keeping and professional rules?",
         "<p>Your firm is. You decide what your clients are told, and you keep the records your own professional rules require. When LongLens sends for you, it keeps the proof of who was added as a client and who stopped.</p>"),
        ("Will AI-drafted issues sound like me?",
         "<p>AI drafts each issue, checks names and figures against the original story, and checks links before the issue goes out. You read and change every line first, on the page or by replying, so it sounds like you.</p>"),
        ("Can I make every line sound like me?",
         "<p>Yes. Open the issue, press Edit in place, click any line and type, then Save. Every version is kept. This works on daily newsletters; a weekly newsletter has its own editor, section by section.</p>"),
    ]),
    ("Your clients' details", [
        ("Does LongLens need my client list?",
         f"<p>Only if you want LongLens to send for you. {CLIENT_LINE} Each letter to a client also shows your business name and postal address. {SEND_SETUP} Or keep your list where it is and forward each issue yourself.</p>"),
        ("Can LongLens follow news from my country?",
         "<p>Yes. LongLens follows the websites, feeds and forums you name, wherever they are: a tax authority's news page, an industry association, a regulator.</p>"),
    ]),
    ("What you get", [
        ('What does "issue" mean?',
         f"<p>One edition of your newsletter: the stories LongLens picked for that day or week, each with what it means for your readers. Every issue comes as an {F_EMAIL}, and can also come as a {F_POD}, {F_REEL}, {F_INFO}, {F_CAR} or {F_EXPL}.</p>"),
        ("Is LongLens only for one kind of business?",
         "<p>No. LongLens works for any business whose readers need to know what is changing: an accountancy, a vet practice, a law firm, a recruiter, a consultancy, a school or a members' association. Geoff built it first for his own field, visual effects, and that is the example on this site. Yours follows the websites, forums and newsletters of your field.</p>"),
        (f"Is the {F_POD} voice AI?",
         f"<p>Yes. Every {F_POD} is spoken by AI voices, never a person: usually two AI hosts talking the issue through, and on some issues one AI voice reading it.</p>"),
        (f"What if the {F_POD}, {F_REEL} or {F_EXPL} is missing?",
         f"<p>Not every issue gets every format. {FORMAT_LADDER} If the format that leads your email is missing, you get the full letter with one line saying so.</p>"),
        ("What happens when a rule changes after I have written about it?",
         "<p>Your readers see it as one story, not a second surprise. A story that moves stays one story: LongLens watches for updates and reversals and links back to earlier coverage.</p>"),
        ("Can LongLens show my readers where their field is heading?",
         "<p>In part. After your first few issues, a section shows what keeps coming up across your last few weeks of issues.</p>"),
        ("Can LongLens write my own company news?",
         "<p>No. LongLens works from what the press, the forums and the videos in your field say. Your own announcements are still yours to write, and you can add them as a note in an issue.</p>"),
    ]),
    ("Day to day", [
        ("How do I change what I get?",
         "<p>Reply to any issue in plain words: shorter, more on one topic, drop a website. LongLens confirms what it understood in the same thread, and the next issue follows it. Reply UNDO to take it back. Issues arrive on weekdays at 07:00 your time to start; change the days and the time on your settings page after you sign in. Every issue ends with a Stop button. If you never tap a link, reply or sign in for five issues, LongLens asks once whether you still want them and waits for your yes.</p>"),
        ("Can I stop it for a while?",
         "<p>Yes. Press Pause this newsletter at the bottom of any issue. The same page starts it again.</p>"),
        ("Can a colleague change my issue by replying?",
         "<p>No. LongLens acts only on replies from the address your issue goes to. A forward to a colleague changes nothing.</p>"),
        ("What if my issue is late?",
         "<p>If an issue has not gone out an hour after its usual time, LongLens emails you once to say so. You do not need to do anything: it goes out as soon as it is ready, or, if something went wrong while making it, we have already been told.</p>"),
    ]),
    ("Money and ownership", [
        ("What does LongLens cost?",
         "<p>Nothing during the pilot. After it, Solo is $19 a month and Business is $95 a month. <a href=\"/pricing/\">See what each plan includes</a>.</p>"),
        ("Is there a limit during the free week?",
         "<p>Yes: one newsletter, up to 10 sources and up to 25 readers on your list. There is also a monthly cap on writing. If a newsletter reaches it, LongLens says so on your pages, and new issues start again the next month.</p>"),
        ("Who owns what LongLens writes?",
         "<p>You do. Every issue, every website you chose, every lesson you taught LongLens.</p>"),
        ("Who is behind LongLens?",
         f"<p>Geoffrey Hancock. He built LongLens first for his own field, visual effects for film and TV, and his own newsletter runs on it most mornings: <a href=\"{DAILY}\">The VFX Supervisor Daily</a>. He won a VES Award for Changeling and was nominated for another for Invictus.</p>"),
    ]),
]

FAQ = f'''<section class="hero">
  <div class="wrap">
    <span class="eyebrow">FAQ</span>
    <h1>Straight answers, including what LongLens does not do yet.</h1>
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
    <div class="sec-head"><span class="eyebrow">Coming</span><h2>Not built yet, and we say so</h2></div>
    <ul class="coming">
      <li><strong>Each reader picks their format</strong> {coming()}<br>{F_EMAIL}, {F_POD}, {F_REEL}, {F_INFO}, {F_CAR} or {F_EXPL}, from a link at the bottom of every issue they get.</li>
      <li><strong>Your {F_REEL} and {F_CAR} ready to post to your own Instagram, LinkedIn and TikTok; your {F_POD} in podcast apps; Telegram; your website</strong> {coming()}<br>Today each issue goes by email, on the web, to your Slack or Discord channel and to an RSS feed.</li>
    </ul>
  </div>
</section>

{close_cta("Be the first your clients hear from, starting this week.",
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


def inquiry_form() -> str:
    """The start form, three fields (Geoff 2026-11-06: "just paste sources and list concepts and
    give your email. that starts it"). The app fills setup with the answers and asks the rest
    (who reads it, the name competition) on the next page."""
    sources_label = "Sources to follow" + ("" if SOURCES_REQUIRED else " (optional)")
    required = " required" if SOURCES_REQUIRED else ""
    return f'''<form class="contact-card" method="post" action="{INQUIRY_ENDPOINT}" accept-charset="utf-8">
  <p><label for="f-sources">{sources_label}: paste websites or feeds, one per line, up to 5</label><br><textarea id="f-sources" name="sources" rows="4" maxlength="4000"{required} placeholder="https://www.accountingtoday.com&#10;https://www.journalofaccountancy.com"></textarea></p>
  <p><label for="f-concepts">Topics to follow</label><br><textarea id="f-concepts" name="concepts" rows="4" required maxlength="4000" placeholder="New tax and payroll rules for small businesses, and what my clients should do before each deadline."></textarea></p>
  <p><label for="f-email">Your email</label><br><input id="f-email" type="email" name="email" required maxlength="320" autocomplete="email"></p>
  <input type="hidden" name="offer" value="brief"><input type="hidden" name="source" value="longlens">
  <input type="hidden" name="tz" id="f-tz" value="">
  <script>try{{document.getElementById("f-tz").value=Intl.DateTimeFormat().resolvedOptions().timeZone||""}}catch(e){{}}</script>
  <p style="position:absolute;left:-9999px" aria-hidden="true"><label for="f-website">Leave this empty</label><input id="f-website" name="website" tabindex="-1" autocomplete="off"></p>{turnstile_widget()}
  <input type="hidden" name="consent_version" value="{CONSENT_VERSION}">
  <button class="btn btn-a" type="submit">See my first issue, free</button>
  <p class="fine">By starting, you agree to get these emails. Stop them any time with one click.</p>
  <p class="email-line">We never add you to a list.</p>
</form>'''


CONTACT_BODY = inquiry_form() if FORM_LIVE else f'''<div class="contact-card">
  <h2 style="font-size:22px">Email Geoff. Three lines are enough.</h2>
  <ol>
    <li>The websites or feeds you read.</li>
    <li>The topics you follow.</li>
    <li>Your name and your business.</li>
  </ol>
  <a class="btn btn-a" href="{html.escape(CALL_MAIL)}">Email Geoff for a free week</a>
  <p class="email-line">Or write to <a href="mailto:{EMAIL}">{EMAIL}</a></p>
  <p class="tiny">Writing does not add you to any list. Geoff replies personally.</p>
</div>'''

CONTACT = f'''<section class="hero">
  <div class="wrap">
    <span class="eyebrow">Free pilot</span>
    <h1>Read a week of what your clients would hear from you, free.</h1>
    <p class="lede">Name a few websites you trust, list your topics, add your email. In about {FIRST_ISSUE_MINUTES} minutes you read your first issue. The pilot is free.</p>
    {CONTACT_BODY}
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">What happens next</span><h2>A week of real issues, read before anyone else sees them</h2></div>
    <ol class="steps three">
      <li><h3>Your first issue is with you in about {FIRST_ISSUE_MINUTES} minutes</h3><p>Written from the websites and topics you just gave.</p></li>
      <li><h3>Something worth passing on every weekday morning</h3><p>On weekdays at 07:00 your time, with nothing to press. Every issue ends with a Stop button.</p></li>
      <li><h3>Your first week</h3><p>Change what it covers and when on one page, if you like. You read a week of real issues before anyone else does.</p></li>
    </ol>
    <p class="k">Before you start, read a real one: <a href="{DAILY}">The VFX Supervisor Daily</a>, Geoff's own newsletter about his own field. Yours covers your field, for your readers.</p>
  </div>
</section>'''

THANKS = f'''<section class="hero">
  <div class="wrap prose">
    <span class="eyebrow">Message sent</span>
    <h1>Thanks. Check your inbox for your start link.</h1>
    <p>LongLens has emailed you a one-time link. Click it: what you wrote on this form is already filled in. Check it, add who reads it if you like, and pick where and when it arrives. Your first issue arrives on the schedule you pick, and your free week starts there. The link works once, for 24 hours.</p>
    <p>Already have an account? The email holds your sign-in link instead. Nothing else is sent to you. We never add you to a list.</p>
    <p>Before you start, read <a href="{DAILY}">Geoff's own newsletter</a>, or go back to the <a href="/">LongLens home page</a>.</p>
  </div>
</section>'''

THANKS_FIRST = f'''<section class="hero">
  <div class="wrap prose">
    <span class="eyebrow">Form sent</span>
    <h1>Check your email in about {FIRST_ISSUE_MINUTES} minutes.</h1>
    <p>Your first issue is on its way. The next ones follow on weekdays at 07:00 your time, with nothing to press, and every issue ends with a Stop button.</p>
    <p>We never add you to a list.</p>
    <p>While you wait, read <a href="{DAILY}">Geoff's own newsletter</a>, or go back to the <a href="/">LongLens home page</a>.</p>
  </div>
</section>'''

THANKS_PERSONAL = f'''<section class="hero">
  <div class="wrap prose">
    <span class="eyebrow">Message sent</span>
    <h1>Thanks. Geoff will reply to you personally.</h1>
    <p>LongLens could not start your newsletter straight away, so Geoff will email you himself. You may also get a short thank-you email from LongLens. We never add you to a list.</p>
    <p>Before you start, read <a href="{DAILY}">Geoff's own newsletter</a>, or go back to the <a href="/">LongLens home page</a>.</p>
  </div>
</section>'''

# --------------------------------------------------------------------------------------------
# Sign in, privacy, 404
# --------------------------------------------------------------------------------------------

SIGNIN_PAGE = f'''<section class="hero">
  <div class="wrap">
    <span class="eyebrow">Sign in</span>
    <h1>Sign in with one link. No password.</h1>
    <p class="lede">The button below opens the LongLens app's sign-in page. Type your email and a link arrives by email, usually within a minute. The link keeps you signed in for 30 days on that device.</p>
    <div class="cta-row"><a class="btn btn-a" href="{SIGNIN}">Get my sign-in link</a></div>
    <p class="k">Not set up yet? <a href="/contact/">Start your free week</a> and your first issue arrives by email in minutes.</p>
  </div>
</section>'''

PRIVACY = f'''<section class="hero">
  <div class="wrap prose">
    <span class="eyebrow">Privacy</span>
    <h1>No tracking on this site. No cookies. Your email reaches one person.</h1>
    <p>This website, getlonglens.com, runs no analytics or tracking scripts and sets no cookies. It is a set of plain pages hosted on GitHub Pages.</p>
    <h2>When you write to Geoff</h2>
    <p>Your email goes to Geoffrey Hancock at {EMAIL}. LongLens uses it to make your account and email you your newsletter, and Geoff uses it only to reply to you. Writing does not add you to any list.</p>
    <h2>Once you use LongLens</h2>
    <p>We notice if you tap a link in your issues, only so we stop emailing anyone who never reads them. Nothing else is read from your issues, and it is not used for anything else.</p>
    <p>What the LongLens app keeps about you, where it lives and who else sees anything is set out on the app's own privacy page: <a href="{APP_PRIVACY}">LongLens app privacy</a>.</p>
  </div>
</section>'''

NOT_FOUND = '''<section class="hero">
  <div class="wrap prose">
    <span class="eyebrow">Not found</span>
    <h1>That page is not here.</h1>
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

FA_OFFER = "Free for a week, then from $19 a month, invoiced."
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
])

FOR_ACCOUNTANTS = f'''<section class="hero">
  <div class="wrap">
    <span class="eyebrow"><img src="/assets/mark-e1.svg" alt="" width="40" height="40">For accountants, tax advisers and bookkeepers</span>
    <h1>Be the accountant clients hear from first when the rules change</h1>
    <p class="lede">Tell your clients what a change means before they have to ask. LongLens explains each change in plain words, with a link to every original, and you change any line before your clients read a word. {FA_SETUP} Examples: {FA_AUTH}.</p>
    <div class="cta-row">
      <a class="btn btn-a" href="/contact/">{FA_CTA}</a>
    </div>
    <p class="price-line">{FA_OFFER} <a href="/pricing/">See prices</a>.</p>
    <p class="price-line">Every update carries your firm's name and only yours, never ours, and we match the look to your brand when you start.</p>
    <p class="price-line">{FA_PASS} <a href="/samples/{FA_SAMPLE[0]}/">Read a sample client update</a>.</p>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">A sample client update</span>
      <h2>See what your clients would hear from you the morning a tax rule changes</h2>
      <p>One example, written for an invented firm in Manchester, using real news: HMRC late payment interest going up, a Making Tax Digital deadline, Budget changes for April 2027. The firm is made up; the stories and links are real, and each section says what it means for the firm's clients. Yours would use the sources you trust, from any country.</p></div>
    <div class="fmt-strip six" role="list" aria-label="A sample client update for an accounting firm">
      <div class="fmt-card" role="listitem"><div class="fmt-media tall"><a href="/samples/{FA_SAMPLE[0]}/"><img src="/assets/samples/{FA_SAMPLE[0]}-top.png" width="600" height="900" loading="lazy" alt="The top of Client Update, a sample client update for an accounting firm: {html.escape(FA_SAMPLE[3])}"></a></div>
        <div class="fmt-txt"><b>{FA_SAMPLE[1]}</b><p>"{html.escape(FA_SAMPLE[3])}"</p>
        <p class="fmt-date">Sample written by LongLens, {FA_SAMPLE_DATE}. <a href="/samples/{FA_SAMPLE[0]}/">Read the whole update</a></p></div></div>
    </div>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">What your clients get</span>
      <h2>Explain each change once, and every client hears it from you</h2></div>
    <div class="cards">
      <div class="card"><h3>Your clients get what a change means for them, not the press release</h3><p>Each update says in plain words what most stories mean for your clients, with a link to every original. {FA_SETUP} Examples: {FA_AUTH}. Sources with a news feed work when pasted; some government pages need us to set them up by hand.</p></div>
      <div class="card"><h3>Names and numbers checked against the original before a client sees them</h3><p>LongLens checks names, titles and figures against the original article, and checks every link, before an update reaches you. You read it first, so a client only sees what you signed off.</p></div>
      <div class="card"><h3>Every line sounds like your firm, and any claim is one click from its original</h3><p>LongLens writes the first version with AI. Make it yours: change any line you like, and check any story against its original. LongLens cannot promise that a draft is right, so your judgement is what your clients are reading.</p></div>
      <div class="card"><h3>When a deadline moves, clients see it in the same story, not as a second surprise</h3><p>LongLens watches for updates and reversals and links back to earlier coverage, so a moved deadline reads as part of the story your clients already know.</p></div>
      <div class="card"><h3>Show clients what keeps coming up, so they know to ask you first</h3><p>After your first few updates, each one shows what keeps coming up across the last few weeks.</p></div>
      <div class="card"><h3>Reach the client who would rather listen than read</h3><p>Each update is an {F_EMAIL}, and most also come as a {F_POD} for the client who listens on the drive in and a {F_REEL} for the one who lives on their phone. Some add an {F_EXPL} or an {F_INFO}. Not every update has every format.</p></div>
      <div class="card"><h3>Know what changed in two minutes, before your day starts</h3><p>Each update takes about two minutes to read. Updates come to you weekdays at 07:00, or the days and time you choose.</p></div>
      <div class="card"><h3>Clients hear it from you, and only you</h3><p>The update comes to you first. {CLIENT_LINE_FIRM} {SEND_SETUP} Or forward it from your own email.</p></div>
    </div>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Getting started</span>
      <h2>Read a week of client updates free, then decide</h2></div>
    <ul class="list">
      <li><strong>Send one short form.</strong> The sources you trust, the topics you cover, your email. Your first update arrives in about {FIRST_ISSUE_MINUTES} minutes.</li>
      <li><strong>Sign in with a link by email.</strong> No password to remember.</li>
      <li><strong>Read a week of updates</strong> before your clients see any, then keep going or stop.</li>
    </ul>
    <p class="price-line">Prices in US dollars, after the pilot. The first plans are paid by invoice.</p>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Questions accountants ask</span>
      <h2>Straight answers before you start</h2></div>
    <div class="faq">{FA_FAQ}</div>
  </div>
</section>

{close_cta("See a week of client updates, free.",
           f"Be the first voice your clients hear when the rules change. Name the sources you trust, list your topics, add your email. Your first update arrives in about {FIRST_ISSUE_MINUTES} minutes, and you read a week of updates before your clients see any.",
           FA_CTA)}'''

PAGES = [
    # slug, title, description, body, nav-current
    ("", "LongLens: be the one your clients hear from first",
     "Be the one your clients, prospects or members turn to first when something changes in your field. Free for a week, then from $19 a month, invoiced.",
     HOME, ""),
    ("features", "Features | LongLens",
     "Reach every reader in the form they take in, and make every line sound like you. Email, Podcast, Reel, Infographic, Carousel and Explainer video, with editing on the page.",
     FEATURES, "/features/"),
    ("pricing", "Pricing | LongLens",
     "Free for a week. Then Solo at $19 a month or Business at $95 a month, invoiced, and what each includes today.",
     PRICING, "/pricing/"),
    ("how-it-works", "How it works | LongLens",
     "Stay in front of your clients every week. One short form, your first issue within minutes, and you change any line on the page or by replying.",
     HOW, "/how-it-works/"),
    ("faq", "FAQ | LongLens",
     "Straight answers: how soon your clients hear from you, what reaches them and when, whether it sounds like you, price and ownership.",
     FAQ, "/faq/"),
    ("for-accountants", "For accountants | LongLens",
     "Be the accountant clients hear from first when the rules change. Explain each change once, in plain words, with only your firm's name on it. Free for a week, then from $19 a month, invoiced.",
     FOR_ACCOUNTANTS, ""),
    ("contact", "Free week | LongLens",
     "Read what your clients would hear from you, free for a week: one short form, your first issue within minutes, a week of issues before anyone else sees them.",
     CONTACT, ""),
    ("sign-in", "Sign in | LongLens",
     "Sign in to LongLens with a link by email. No password.", SIGNIN_PAGE, ""),
    ("privacy", "Privacy | LongLens",
     "This site runs no tracking and sets no cookies. What happens when you write, and where the app's privacy page is.",
     PRIVACY, ""),
]


def write_site() -> list[tuple[str, str]]:
    out = []
    for slug, title, desc, body, cur in PAGES:
        doc = page(slug, title, desc, body, cur)
        target = ROOT / "index.html" if slug == "" else ROOT / slug / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(doc, encoding="utf-8")
        out.append((slug, doc))
    (ROOT / "thanks").mkdir(exist_ok=True)
    (ROOT / "thanks" / "index.html").write_text(
        page("thanks", "Thanks | LongLens", "Your start link is on its way.", THANKS, robots="noindex"),
        encoding="utf-8")
    (ROOT / "contact" / "thanks-first-issue").mkdir(parents=True, exist_ok=True)
    (ROOT / "contact" / "thanks-first-issue" / "index.html").write_text(
        page("contact/thanks-first-issue", "Thanks | LongLens", "Your first issue is on its way.",
             THANKS_FIRST, robots="noindex", signin=False),
        encoding="utf-8")
    (ROOT / "contact" / "thanks-personal").mkdir(parents=True, exist_ok=True)
    (ROOT / "contact" / "thanks-personal" / "index.html").write_text(
        page("contact/thanks-personal", "Thanks | LongLens", "Geoff will reply to you personally.",
             THANKS_PERSONAL, robots="noindex"),
        encoding="utf-8")
    (ROOT / "404.html").write_text(
        page("404", "Not found | LongLens", "That page is not here.", NOT_FOUND, robots="noindex"),
        encoding="utf-8")
    return out


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
        body = re.search(r"<body>\n(.*)\n</body>", doc, re.S).group(1)
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

    joined = re.sub(r'(src|href|poster)="(/assets/[^"]+)"', inline, joined)
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


def write_seo() -> None:
    urls = "".join(f"  <url><loc>{SITE}{'/' if s == '' else '/' + s + '/'}</loc></url>\n" for s, *_ in PAGES)
    (ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + '</urlset>\n', encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")


if __name__ == "__main__":
    write_seo()
    write_preview(write_site())
    print("built", len(PAGES) + 1, "pages and preview.html")
