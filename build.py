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
INQUIRY_CONSENT = "I agree to be contacted about this message at the email address I gave."
# Cloudflare Turnstile on the form (the app checks the token when NL_TURNSTILE_SECRET is set).
# The site key is PUBLIC; paste it from Cloudflare > Turnstile > the getlonglens.com widget.
# Empty = no widget is rendered and the page is exactly as before. Deploy order: the app first,
# then this key here, then the secret in nl.env LAST (a widget the app does not check is
# harmless; an app that checks with no widget on the page refuses every post).
TURNSTILE_SITE_KEY = "0x4AAAAAAF2l6EOGFK5dERe5"
TURNSTILE_ACTION = "start"  # must match newsletter.turnstile.FORM_ACTION in the app

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


AI_LINE = "LongLens uses AI to write each issue, then checks names and figures against the original story before you see it."


def coming(text: str = "") -> str:
    tag = '<span class="tag-coming">coming</span>'
    return f"{tag} {text}" if text else tag


# --------------------------------------------------------------------------------------------
# Shared pieces
# --------------------------------------------------------------------------------------------

CUR = ' aria-current="page"'


def header(current: str) -> str:
    links = "".join(
        f'<a href="{href}"{CUR if href == current else ""}>{label}</a>'
        for label, href in NAV
    )
    return f'''<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <div class="wrap">
    <a class="brand" href="/" aria-label="LongLens home"><img src="/assets/mark-e1.svg" alt="" width="32" height="32"><span>LongLens</span></a>
    <a class="btn btn-a hdr-cta" href="/contact/">{CTA_LABEL}</a>
    <nav aria-label="Main">{links}<a href="/sign-in/">Sign in</a><a class="btn btn-a" href="/contact/">{CTA_LABEL}</a></nav>
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
         robots: str = "") -> str:
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
{header(current)}
<main id="main">
{body}
</main>
{footer()}
</body>
</html>
'''


CTA_TEXT = "Ask for a free week of issues"
OFFER_LINE = "Free pilot: a start link by email the moment you ask, then a week of real issues for your business. After the pilot, from $19 a month."
CONTROL_LINE = "Nothing reaches your clients unless you send it. Every issue comes to you first: read it, change any line, then send it on yourself."


def close_cta(h2: str, text: str) -> str:
    return f'''<section class="close">
  <div class="wrap"><div>
    <h2>{h2}</h2>
    <p class="k">{text}</p>
    <div class="cta-row"><a class="btn btn-a" href="/contact/">{CTA_TEXT}</a></div>
  </div></div>
</section>'''


M = "/assets/media/"

EXAMPLE_LABEL = "Geoff's own newsletter about his own field, visual effects for film and TV"

# One name per format, used on every page.
F_READ, F_SKIM, F_HEAR, F_WATCH, F_SHORT, F_PIC = (
    "Read it", "Skim it", "Hear it", "Watch it", "One minute", "One picture")

FORMAT_STRIP = f'''<p class="eyebrow strip-label">Real examples from Geoff's own newsletter, with their dates</p>
<div class="fmt-strip" role="list" aria-label="One issue in five formats, real examples">
  <div class="fmt-card" role="listitem"><div class="fmt-media tall"><a href="{M}read-letter.png"><img src="{M}read-letter.png" width="780" height="1276" loading="lazy" alt="Geoff's own issue of 13 Oct 2026 as an email on a phone: the date, the headline and a short paragraph on what it means for the reader."></a></div>
    <div class="fmt-txt"><b>{F_READ}</b><p>Two minutes with coffee. What is new, and what it means for the reader.</p><p class="fmt-date">13 Oct 2026</p></div></div>
  <div class="fmt-card" role="listitem"><div class="fmt-media"><img src="{M}issue-audio-wave.png" width="780" height="352" loading="lazy" alt="The sound wave of the audio clip below."></div>
    <div class="fmt-txt"><b>{F_HEAR}</b><p>The issue as audio, for the drive in. On some days, a longer conversation between two voices.</p>
    <audio controls preload="none" src="{M}issue-audio.m4a" aria-label="The first 16 seconds of the issue's audio"></audio><p class="fmt-date">13 Oct 2026, the first 16 seconds</p></div></div>
  <div class="fmt-card" role="listitem"><div class="fmt-media"><a href="{M}issue-infographic.jpg"><img src="{M}issue-infographic.jpg" width="1280" height="714" loading="lazy" alt="One picture of a whole issue: headed panels, each with a drawing and a short line."></a></div>
    <div class="fmt-txt"><b>{F_PIC}</b><p>The whole issue on one picture, for the reader who will not read. Tap to open it full size.</p><p class="fmt-date">30 Oct 2026</p></div></div>
  <div class="fmt-card" role="listitem"><div class="fmt-media"><video controls preload="none" playsinline poster="{M}issue-explainer-poster.jpg" src="{M}issue-explainer.mp4" width="640" height="360" aria-label="The first 15 seconds of an explainer video"></video></div>
    <div class="fmt-txt"><b>{F_WATCH}</b><p>A narrated explainer video of the issue, with a drawing for each point.</p><p class="fmt-date">1 Nov 2026, the first 15 seconds of 7 minutes</p></div></div>
  <div class="fmt-card" role="listitem"><div class="fmt-media tall"><video controls preload="none" playsinline poster="{M}issue-short-poster.jpg" src="{M}issue-short.mp4" width="540" height="960" aria-label="The first 15 seconds of a one-minute upright video"></video></div>
    <div class="fmt-txt"><b>{F_SHORT}</b><p>About a minute, upright for a phone, with captions on screen.</p><p class="fmt-date">4 Nov 2026, the first 15 seconds</p></div></div>
</div>
<p class="fmt-hint">The letter comes with every issue, and the other formats with many of them. Geoff's newsletter is about his field; yours is about yours.</p>'''

EDITOR_SHOT = f'''<figure class="shot"><a href="{M}edit-in-place.png"><img src="{M}edit-in-place.png" width="1100" height="770" loading="lazy" alt="The LongLens editor open on a real issue: a bar with Save, Discard and the inbox preview line on top, and every line of the issue below outlined, ready to click and change."></a><figcaption>The real editor, on {EXAMPLE_LABEL}, 13 Oct 2026.</figcaption></figure>'''

PROOF = f'''<div class="proof">
  <b>Who built it</b>
  <p>Geoffrey Hancock built LongLens for his own field first, visual effects for film and TV, and his own newsletter, The VFX Supervisor Daily, runs on it most mornings. He won a VES Award for Changeling and was nominated for another for Invictus. Now businesses in any field start LongLens from one short form, and Geoff reads every message.</p>
  <p class="links"><a href="{DAILY}">Read Geoff's own newsletter</a></p>
</div>'''

# Sample issues for other kinds of business. Each: (image, alt, what it is, date, link or "").
# The section renders only when this list has entries, so nothing placeholder is ever published.
SAMPLES = [
    ("dk-accounting", "Client Update", "For the clients of a Copenhagen accounting firm",
     "Corporate tax overpayment window closes soon, and new EU parcel fees add to import costs",
     "Made on the Sections page, where you pick and order the parts of each issue: a \"Dates to note\" box first, then a divider, then the stories. Colours chosen when the account was set up."),
    ("ux-research", "Research Notes", "For the prospects of an independent UX researcher",
     "AI moderators and synthetic users: early data says use them for practice, not evidence",
     "Made by replying to an issue in plain words: \"Please switch me to the short-summary layout.\" Now every story gets a few sentences and a read time."),
    ("bakery", "The Proving Room", "For the members of a bakery owners\' community",
     "Cocoa has fallen, but your costs may not follow soon",
     "Made by replying \"Just the headlines from now on please\" and turning on story pictures. LongLens draws the pictures itself, in the community\'s colours."),
]
SAMPLE_DATE = "Wed 4 Nov 2026"


def samples_section() -> str:
    if not SAMPLES:
        return ""
    cards = "".join(
        f'<div class="fmt-card" role="listitem"><div class="fmt-media tall">'
        f'<a href="/samples/{slug}/"><img src="/assets/samples/{slug}-top.png" width="600" height="900" loading="lazy" '
        f'alt="The top of {html.escape(name)}, a sample issue: {html.escape(headline)}"></a></div>'
        f'<div class="fmt-txt"><b>{html.escape(name)}</b><p>{html.escape(who)}: "{html.escape(headline)}"</p>'
        f'<p class="fmt-how">{html.escape(how)}</p>'
        f'<p class="fmt-date">Sample issue made by LongLens, {SAMPLE_DATE}. <a href="/samples/{slug}/">Read the whole issue</a></p></div></div>'
        for slug, name, who, headline, how in SAMPLES)
    return f'''<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Sample issues</span>
      <h2>Read an issue written for a business like yours</h2>
      <p>Three sample issues LongLens wrote on {SAMPLE_DATE} from that week's real news, each for a made-up business: an accounting firm, a UX researcher and a bakery owners' community. Each one has its own look, made with the same tools you get: the Sections page, story pictures, or a plain reply to an issue. Every story links to the original.</p></div>
    <div class="fmt-strip six" role="list" aria-label="Sample issues for other businesses">{cards}</div>
  </div>
</section>'''


TODAY_PLACES = ("Your inbox first, then sent through the email tool you already use, or forwarded",
                "A web page for every issue you publish",
                "A public page of all your issues",
                "Your Slack or Discord channel",
                "A private RSS feed")
COMING_PLACES = ("Straight to each reader from your own address",
                 "Podcast apps", "Instagram and LinkedIn posts", "A block on your website", "Telegram")

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

HOME = f'''<section class="hero">
  <div class="wrap">
    <span class="eyebrow"><img src="/assets/mark-e1.svg" alt="" width="40" height="40">LongLens</span>
    <h1 class="rot-h1"><span class="sr-only">Your clients hear the news from you.</span><span aria-hidden="true">Your <span class="rot">{ROT_WORDS}</span> <span class="rot rot-v">{ROT_VERB_WORDS}</span> the news from you.</span></h1>
    <p class="lede">LongLens follows the news sites, forums and videos you name, and writes a short newsletter under your name on what changed in your field and what it means for your clients, prospects or members. Every week, or every morning if your field moves fast, as a letter, audio, a picture and video. You never start from a blank page.</p>
    <div class="cta-row">
      <a class="btn btn-a" href="/contact/">{CTA_TEXT}</a>
    </div>
    <p class="price-line">{OFFER_LINE} <a href="/pricing/">See prices</a>.</p>
    <p class="price-line"><strong>{CONTROL_LINE}</strong></p>
    <p class="price-line">{AI_LINE}</p>
  </div>
</section>

{samples_section()}

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Who it is for</span>
      <h2>Three kinds of business that win work by knowing their field</h2></div>
    <div class="cards">
      <div class="card"><h3>Firms whose clients ask "what does this mean for me?"</h3><p>An accountancy, a law firm, a vet practice, an insurance broker. A new rule, a deadline or a recall lands, and your clients read what it means for them in your newsletter, before it reaches them as a problem.</p></div>
      <div class="card"><h3>Consultants and coaches out on their own</h3><p>No mailing list yet? Send each issue to the twenty people you would most like to work with. Week after week they see that you know what is moving in your field, long before you pitch them.</p></div>
      <div class="card"><h3>Communities, clubs and associations</h3><p>Your members get something worth opening from you every week, so your list stays alive between events. Put a note of your own at the top of any issue.</p></div>
    </div>
    <p class="k">Not sure how often? Start weekly. Daily is there for a field that changes by the hour. You choose what LongLens follows and who it writes for.</p>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Read, hear, see, watch</span>
      <h2>Your readers can read it, hear it, see it or watch it</h2>
      <p>One reader skims with coffee, another listens in the car, a third only looks at a picture. LongLens turns each issue into a letter, audio, a picture and a short video, so the same news reaches all of them.</p></div>
    {FORMAT_STRIP}
    <div class="cards two">
      <div class="card"><h3>Where your readers find it today</h3><p>{" · ".join(TODAY_PLACES)}.</p></div>
      <div class="card"><h3>Where it goes next</h3><p>{coming(" · ".join(COMING_PLACES) + ".")}</p></div>
    </div>
    <p class="k"><a href="/features/">See every format and every place it goes</a></p>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Your name, your words</span>
      <h2>Change any line right on the issue, exactly as your readers will see it</h2></div>
    <div class="feat">
      <div class="txt">
        <p>Open the issue, click the words you want to change, type, and press Save. The issue updates everywhere with your words, and every earlier version is kept. Or reply in plain words, "shorter" or "more on the new rules", and the next issue follows.</p>
        <ul>
          <li><strong>Your words on top</strong>: the headline, the opening, and the line people see in their inbox before they open it.</li>
          <li><strong>Your say on every story</strong>: the line on what it means for them, and each short summary.</li>
          <li><strong>The facts stay put</strong>: story titles and links stay as the original publisher wrote them, so every story still points to where it came from.</li>
          <li><strong>Your layout</strong>: put the sections in your order, hide the ones you do not need, and add a note from you.</li>
        </ul>
      </div>
      {EDITOR_SHOT}
    </div>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Price</span>
      <h2>Free during the pilot. $19 or $95 a month after it.</h2></div>
    <div class="cards">
      <div class="card"><h3>Pilot: free</h3><p>Send the form and a start link arrives by email at once. You get everything LongLens does today.</p></div>
      <div class="card"><h3>Solo: $19 a month</h3><p>One newsletter under your name, daily or weekly, with the letter, the audio, the picture and both videos.</p></div>
      <div class="card"><h3>Business: $95 a month</h3><p>Everything in Solo, plus a public page of your issues, your Slack or Discord channel and an RSS feed. {coming("Sending straight to your readers from your own address.")}</p></div>
    </div>
    <p class="k"><a href="/pricing/">See exactly what each plan includes</a></p>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">{PROOF}</div>
</section>

{close_cta("See a week of issues for your business, free.",
           "Tell Geoff who your readers are. A start link reaches your inbox at once, your first issue arrives on the schedule you pick, and you read a week of real issues before anyone else sees them.")}
{ROT_JS}'''

# --------------------------------------------------------------------------------------------
# Features
# --------------------------------------------------------------------------------------------

FEATURES = f'''<section class="hero">
  <div class="wrap">
    <span class="eyebrow">Features</span>
    <h1>One issue on what changed in your field, as a letter, audio, a picture and video.</h1>
    <p class="lede">LongLens writes each issue under your name, then turns the same issue into every format, so each reader takes the news in the way they like. You change any line on the page before anyone else sees it.</p>
    <p class="price-line">{AI_LINE}</p>
    {FORMAT_STRIP}
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Every format</span>
      <h2>The same news, in the way each reader likes it</h2>
      <p>Every format is switched on for a new account. Each one comes from the same stories, so whichever a reader picks, they get the same news.</p></div>
    <div class="cards">
      <div class="card"><h3>{F_READ}</h3><p>The letter: what changed and what it means for them, with a link to every original story. By email, and on the web once you publish the issue.</p></div>
      <div class="card"><h3>{F_SKIM}</h3><p>A short email with the one line that matters most and a button to read the whole issue on the web.</p></div>
      <div class="card"><h3>{F_HEAR}</h3><p>A spoken version of the issue. On some days, a longer conversation between two voices, for the drive in.</p></div>
      <div class="card"><h3>{F_PIC}</h3><p>The whole issue on one picture, with a drawing and a short line for each point. On some issues.</p></div>
      <div class="card"><h3>{F_WATCH}</h3><p>A narrated explainer video of the issue, a few minutes long. On some issues.</p></div>
      <div class="card"><h3>{F_SHORT}</h3><p>About a minute, upright for a phone, with captions on screen.</p></div>
      <div class="card"><h3>Story pictures</h3><p>Turn them on and your top stories each get a small picture in your colours. {coming("A picture generated for each story, in your own style.")}</p></div>
    </div>
    <ul class="list">
      <li><strong>Not every issue gets every format.</strong> The letter always goes out. Each other format is checked against the stories first, and one that fails is left off.</li>
      <li><strong>You pick what leads your own email</strong>: {F_READ}, {F_SKIM}, {F_HEAR}, {F_WATCH}, {F_PIC} or {F_SHORT}. The letter always follows.</li>
      <li><strong>Each reader, their own way</strong>: today the public page of your issues carries every format side by side. {coming("Each reader picks once at the bottom of their email, and LongLens sends every issue that way.")}</li>
    </ul>

    <div class="sec-head"><span class="eyebrow">Where it goes</span>
      <h2>Every place your readers can get each issue</h2>
      <p>Your newsletter's name and issue number are on every one, wherever it lands.</p></div>
    <div class="cards two">
      <div class="card"><h3>Today</h3><ul class="list">
        <li><strong>In your own inbox first</strong>, with every format on its page in your account.</li>
        <li><strong>In their inbox</strong>: send the letter through the email tool you already use, or simply forward it.</li>
        <li><strong>On the web</strong>: each issue you publish gets a page of its own that anyone can open from a link, with no sign-in.</li>
        <li><strong>On a public page of all your issues</strong>, with every format that passed its check. Geoff sets it up with you.</li>
        <li><strong>In a Slack or Discord channel</strong>: a short post with a link to each issue you publish.</li>
        <li><strong>In a feed reader</strong>: a private RSS link to your published issues.</li>
      </ul></div>
      <div class="card"><h3>Coming</h3><ul class="list">
        <li>{coming("<strong>Straight to each reader</strong> from your own address, for example news@yourbusiness.com, in the format each one picked.")}</li>
        <li>{coming("<strong>In podcast apps</strong>: the audio of every issue as a podcast your readers can follow.")}</li>
        <li>{coming("<strong>On Instagram and LinkedIn</strong>: posts from each issue, ready for you to put up.")}</li>
        <li>{coming("<strong>On your own website</strong>: a block that shows your latest issue.")}</li>
        <li>{coming("<strong>On Telegram</strong>: each issue in a Telegram channel.")}</li>
      </ul></div>
    </div>

    <div class="feat">
      <div class="txt">
        <h2>Change any line right on your issue. What you see is what they get.</h2>
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
        <h2>Lay out your issue the way you would lay out a page</h2>
        <p>On a daily newsletter, the Sections page lists every part of the issue, with a live preview of your latest issue beside it.</p>
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
        <h2>Reply in plain words to change the next issue</h2>
        <p>Teach LongLens the way you would brief a new hire: reply to any issue in your own words. LongLens answers in the same thread with what it understood, and the next issue follows it.</p>
        <ul>
          <li><strong>Length</strong>: shorter, longer, or how many stories.</li>
          <li><strong>Topics</strong>: more of one thing, less of another.</li>
          <li><strong>Your readers</strong>: a new sentence about who they are and what matters to them.</li>
          <li><strong>Websites</strong>: paste a link to add one, name one to drop it.</li>
          <li><strong>Tone and layout</strong>: how it sounds, how each story is laid out.</li>
          <li><strong>Formats</strong>: add or drop the two-voice audio.</li>
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
        <h2>LongLens checks every story before your readers see it</h2>
        <ul>
          <li><strong>What it means for them</strong>: most stories carry one line on why they matter to your readers, so the issue is never a list of links.</li>
          <li><strong>No repeats</strong>: a story they have already seen stays out until something changes, then comes back marked as an update.</li>
          <li><strong>Names and figures</strong> are checked against the original story.</li>
          <li><strong>Links are checked</strong> before the issue goes out. A story whose only link is dead is left out, and the last line says how many links were checked.</li>
        </ul>
      </div>
    </div>

    <div class="feat">
      <div class="txt">
        <h2>On your desk when you sit down</h2>
        <p>LongLens arrives on the days and at the time you pick, in your time zone. Weekly suits most fields; daily suits a field that moves fast.</p>
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

{close_cta("See a week of issues for your business, free.",
           "Tell Geoff who your readers are and what they should hear from you first. A start link reaches your inbox at once, and your first issue arrives on the schedule you pick.")}'''

# --------------------------------------------------------------------------------------------
# Pricing
# --------------------------------------------------------------------------------------------

PRICING = f'''<section class="hero">
  <div class="wrap">
    <span class="eyebrow">Pricing</span>
    <h1>Free during the pilot. From $19 a month after it.</h1>
    <p class="lede">The pilot is free: send the form, a start link arrives by email at once, and you get everything LongLens does today. When the pilot ends, pick a plan or stop. Nothing is owed for the pilot, and no card is asked for.</p>
    <div class="cards" style="margin-top:28px">
      <div class="card"><h2 style="font-size:20px">Pilot: free</h2>
        <ul class="list" style="margin-top:8px">
          <li>Your newsletter, daily or weekly, under your name</li>
          <li>With most issues: the letter, a spoken version and the one-minute video</li>
          <li>Up to two a week: the two-voice audio, the explainer video or the one picture</li>
          <li>Change any line on the page, or reply in plain words</li>
          <li>A web page for every issue, a public page of all of them, your Slack or Discord channel and an RSS feed</li>
          <li>Started from one email link and three short questions</li>
        </ul></div>
      <div class="card"><h2 style="font-size:20px">Solo: $19 a month</h2>
        <ul class="list" style="margin-top:8px">
          <li>One newsletter under your name, daily or weekly</li>
          <li>The letter, the audio, the one picture and both videos</li>
          <li>Change any line on the page, or reply in plain words</li>
          <li>Every issue in your inbox and on a web page of its own, ready to send on</li>
        </ul></div>
      <div class="card"><h2 style="font-size:20px">Business: $95 a month</h2>
        <ul class="list" style="margin-top:8px">
          <li>Everything in Solo</li>
          <li>A public page of all your issues, with every format</li>
          <li>Each issue posted to your Slack or Discord channel, and an RSS feed</li>
          <li>{coming("Sent straight to each reader from your own address")}</li>
          <li>{coming("Podcast apps, Instagram and LinkedIn posts, Telegram, and a block on your website")}</li>
        </ul></div>
    </div>
    <div class="cta-row"><a class="btn btn-a" href="/contact/">{CTA_TEXT}</a></div>
    <p class="price-line">Prices in US dollars, after the pilot. The first plans are paid by invoice.</p>
    <p class="price-line"><strong>{CONTROL_LINE}</strong></p>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">How the pilot works</span>
      <h2>No card form. One email link starts your free week.</h2></div>
    <ul class="list">
      <li><strong>Start from the form.</strong> LongLens emails you a one-time start link at once, and Geoff still reads every message himself.</li>
      <li><strong>Three short questions, no call.</strong> What LongLens should follow, where and when it arrives, and where it starts looking. Your first issue arrives on the schedule you pick.</li>
      <li><strong>A monthly cap on writing.</strong> If a newsletter reaches it, LongLens says so on your pages, and new issues start again the next month.</li>
      <li><strong>Up to two of the bigger formats a week</strong>: the two-voice audio, the explainer video or the one picture. The letter, the spoken version and the one-minute video carry on as usual.</li>
      <li><strong>Stop any time.</strong> Tell Geoff, and nothing is owed.</li>
    </ul>
  </div>
</section>

{close_cta("See a week of issues for your business, free.",
           "One email link, then a week of real issues under your name before anyone else sees them.")}'''

# --------------------------------------------------------------------------------------------
# How it works
# --------------------------------------------------------------------------------------------

HOW = f'''<section class="hero">
  <div class="wrap">
    <span class="eyebrow">How it works</span>
    <h1>One email link. Then your newsletter lands every week, or every morning, under your name.</h1>
    <p class="lede">No software to learn and no password to remember. Answer three short questions and LongLens is set up. From then on, change any line right on the issue, or reply to it in plain words.</p>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Getting started</span><h2>From one email link to your first issue</h2></div>
    <ol class="steps two">
      <li><h3>Ask for a free week</h3>
        <p>Tell Geoff who your readers are and what they should hear from you first. LongLens emails you a one-time start link at once, and Geoff still reads every message himself.</p>
        <p><a href="/contact/">{CTA_TEXT}</a></p></li>
      <li><h3>Your start link arrives at once</h3>
        <p>The link works once, for 24 hours, and your free week starts there. Already have an account? The email holds your sign-in link instead. You see a week of real issues before anyone else does.</p></li>
      <li><h3>Open the link LongLens emails you</h3>
        <p>Open it and press Get started. There is no password. Three short questions follow, no call needed:</p>
        <ul><li>What should LongLens follow, said the way you would tell a friend?</li>
          <li>Where and when: by email and on a web page, or the web page only, how often, what time, your time zone.</li>
          <li>Where should LongLens start looking: websites, feeds or keywords, or a starter set.</li></ul></li>
      <li><h3>Your first issue arrives on the schedule you pick</h3>
        <p>Press Make my newsletter, and your first issue reaches your inbox on the schedule you picked. Sooner? Open Issues and press Make an issue now: LongLens starts on it within ten minutes and emails it to you.</p></li>
    </ol>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Every issue</span><h2>What lands in your inbox, and why you can trust it</h2>
      <p>At the time you picked, LongLens turns the news in your field into one issue with your newsletter's name on it.</p></div>
    <ol class="steps three">
      <li><h3>LongLens catches anything new</h3><p>From every website, feed, forum and channel you follow.</p></li>
      <li><h3>LongLens keeps what matters to your readers</h3><p>A story you have already had stays out, unless something changed. Then it comes back marked as an update.</p></li>
      <li><h3>Every story says what it means for them</h3><p>Most stories carry a short line on why they matter to your readers, and every story links to the original.</p></li>
      <li><h3>Links are checked first</h3><p>A story whose only link is dead is left out, and a line at the foot of the issue says how many links were checked.</p></li>
      <li><h3>Your copy arrives by email</h3><p>Nothing to press. Every issue is also kept on the Issues page when you sign in.</p></li>
      <li><h3>The other formats follow</h3><p>Audio, the picture and the videos appear on the issue's page once they pass their check, not on every issue.</p></li>
    </ol>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Day to day</span><h2>Five things cover most days</h2></div>
    <ul class="list">
      <li><strong>Change a line</strong>: open the issue, press Edit in place, click any line and type (daily newsletters; a weekly newsletter has its own editor).</li>
      <li><strong>Change the next issue</strong>: reply in plain words, for example "shorter please". The next issue follows it.</li>
      <li><strong>Undo a change</strong>: reply UNDO.</li>
      <li><strong>Pause it</strong>: press Pause this newsletter at the bottom of any issue. The same page starts it again.</li>
      <li><strong>Sign in</strong>: type your email on the <a href="/sign-in/">sign-in page</a> and a fresh link arrives by email, usually within a minute. Each link works once, and keeps you signed in for 30 days on that device.</li>
    </ul>
    <p class="k">Every issue comes to you first. Today you send it through the email tool you already use, or forward it. {coming("Email straight to your readers from your own address.")}</p>
  </div>
</section>

{close_cta("See a week of issues for your business, free.",
           "You read a week of real issues before anyone else does.")}'''

# --------------------------------------------------------------------------------------------
# FAQ
# --------------------------------------------------------------------------------------------

def qa(q, a):
    return f"<details><summary>{q}</summary>{a}</details>"


FAQ_ITEMS = [
    ("Getting started", [
        ("How do we start, and how does LongLens reach my readers?",
         "<p>Send the form and LongLens emails you a one-time start link at once. Click it, answer three short questions (what LongLens should follow, where and when it arrives, and where it starts looking), and your first issue arrives on the schedule you pick. On a very busy day the form thanks you instead, and Geoff replies to you himself. You see a week of real issues before anyone else does. Today each issue comes to you first, and you send it through the email tool you already use, or forward it. Email straight to your readers from your own address is coming.</p>"),
        ("Can I sign up on my own?",
         "<p>Yes, from the form. <a href=\"/contact/\">Start your free week</a>. Send the form and LongLens emails you a one-time start link at once. On a very busy day the form thanks you instead, and Geoff replies to you himself. He reads every message.</p>"),
        ("How do I sign in?",
         "<p>With a link by email. There is no password. Type your email on the <a href=\"/sign-in/\">sign-in page</a> and a fresh link arrives, usually within a minute. Each link works once and keeps you signed in for 30 days on that device.</p>"),
    ]),
    ("Trust and control", [
        ("Does anything reach my clients before I see it?",
         "<p>No. Nothing goes to your clients until you approve it. Every issue comes to you by email first: you read it, change any line, and decide what to send and to whom. If your issues also go up on a public page on your own website, each one waits for your OK there too, unless you choose a setting that puts it up for you: Automatic, or Publish at noon without my take (if you have not added your own comment by 12:00, it goes up without it). Both are off until you choose them, you are emailed when an issue goes up, and what goes up also reaches your Slack or Discord channel and your feed.</p>"),
        ("What if LongLens gets something wrong?",
         "<p>You read every issue before your readers do, and you can change or cut any line. LongLens checks names and figures against the original story and links every story to it, so each fact can be checked in one click. Your name is on it, so the last word is yours.</p>"),
        ("Is AI writing it?",
         "<p>Yes. LongLens writes with AI, checks names and figures against the original story, and checks links before the issue goes out. You change anything on the page or by replying.</p>"),
        ("Can I edit the issue myself?",
         "<p>Yes. Open the issue, press Edit in place, click any line and type, then Save. Every version is kept. This works on daily newsletters; a weekly newsletter has its own editor, section by section.</p>"),
    ]),
    ("Your clients' details", [
        ("Does LongLens need my client list?",
         "<p>Not today. Issues come to you, and you send them from the email tool you already use, so your client list stays where it is.</p>"),
        ("Can LongLens follow news from my country?",
         "<p>Yes. LongLens follows the websites, feeds and forums you name, wherever they are: a tax authority's news page, an industry association, a regulator.</p>"),
    ]),
    ("What you get", [
        ("Is LongLens only for one kind of business?",
         "<p>No. LongLens works for any business whose readers need to know what is changing: an accountancy, a vet practice, a law firm, a recruiter, a consultancy, a school or a members' association. Geoff built it first for his own field, visual effects, and that is the example on this site. Yours follows the websites, forums and newsletters of your field.</p>"),
        ("What if the audio or videos are missing?",
         "<p>Not every issue gets every format. During the pilot, up to two of the bigger formats come each week: the two-voice audio, the explainer video or the one picture. The letter always goes out, and the spoken version and the one-minute video come with most issues. If the format that leads your email is missing, you get the full letter with one line saying so.</p>"),
        ("Can LongLens write my own company news?",
         "<p>No. LongLens works from what the press, the forums and the videos in your field say. Your own announcements are still yours to write, and you can add them as a note in an issue.</p>"),
    ]),
    ("Day to day", [
        ("How do I change what I get?",
         "<p>Reply to any issue in plain words: shorter, more on one topic, drop a website. LongLens confirms what it understood in the same thread, and the next issue follows it. Reply UNDO to take it back. The days and the time are changed on your settings page after you sign in.</p>"),
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
    <p class="lede">Getting started, trust and control, what you get, day to day, price and ownership.</p>
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
      <li><strong>Email straight to your readers</strong> {coming()}<br>Issues sent from your own address (for example news@yourbusiness.com), each reader in the format they picked, with a dated record of each reader's yes and one-click unsubscribe.</li>
      <li><strong>Each reader picks their format</strong> {coming()}<br>{F_READ}, {F_SKIM}, {F_HEAR}, {F_WATCH}, {F_PIC} or {F_SHORT}, from a link at the bottom of every issue they get.</li>
      <li><strong>Podcast apps, Instagram and LinkedIn, Telegram, your website</strong> {coming()}<br>Today each issue goes by email, on the web, to your Slack or Discord channel and to an RSS feed.</li>
    </ul>
  </div>
</section>

{close_cta("Ask the person who built LongLens.",
           "Geoff reads every message himself and replies personally.")}'''

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
    return f'''<form class="contact-card" method="post" action="{INQUIRY_ENDPOINT}" accept-charset="utf-8">
  <p><label for="f-name">Your name</label><br><input id="f-name" name="name" required maxlength="200" autocomplete="name"></p>
  <p><label for="f-email">Email</label><br><input id="f-email" type="email" name="email" required maxlength="320" autocomplete="email"></p>
  <p><label for="f-company">Your business (optional)</label><br><input id="f-company" name="company" maxlength="200" autocomplete="organization"></p>
  <input type="hidden" name="offer" value="brief"><input type="hidden" name="source" value="longlens">
  <p><label for="f-message">Who reads your newsletter (or should), and what should they hear from you first?</label><br><textarea id="f-message" name="message" required maxlength="5000"></textarea></p>
  <p style="position:absolute;left:-9999px" aria-hidden="true"><label for="f-website">Leave this empty</label><input id="f-website" name="website" tabindex="-1" autocomplete="off"></p>
  <p><label><input type="checkbox" name="consent" value="yes" required> {INQUIRY_CONSENT}</label></p>{turnstile_widget()}
  <button class="btn btn-a" type="submit">Start my free week</button>
  <p class="email-line">{CONTROL_LINE}</p>
  <p class="email-line">Rather email? Write to <a href="{html.escape(CALL_MAIL)}">{EMAIL}</a> and Geoff replies personally. Writing does not add you to any list.</p>
</form>'''


CONTACT_BODY = inquiry_form() if FORM_LIVE else f'''<div class="contact-card">
  <h2 style="font-size:22px">Email Geoff. Three lines are enough.</h2>
  <ol>
    <li>Who your readers are.</li>
    <li>What they should hear from you first.</li>
    <li>Your name and your business.</li>
  </ol>
  <a class="btn btn-a" href="{html.escape(CALL_MAIL)}">Email Geoff for a free week</a>
  <p class="email-line">Or write to <a href="mailto:{EMAIL}">{EMAIL}</a></p>
  <p class="tiny">Writing does not add you to any list. Geoff replies personally.</p>
</div>'''

CONTACT = f'''<section class="hero">
  <div class="wrap">
    <span class="eyebrow">Free pilot</span>
    <h1>Read a week of your own newsletter, free.</h1>
    <p class="lede">Tell Geoff about your business and who you would send it to. LongLens emails you a one-time start link at once: click it, answer three short questions (what LongLens should follow, where and when it arrives, and where it starts looking), and your first issue arrives on the schedule you pick. Geoff still reads every message himself. The pilot is free.</p>
    {CONTACT_BODY}
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">What happens next</span><h2>From your message to your first week of issues</h2></div>
    <ol class="steps three">
      <li><h3>Your start link arrives</h3><p>By email, straight away. The link works once, for 24 hours. Geoff still reads every message himself.</p></li>
      <li><h3>Three short questions</h3><p>What LongLens should follow, where and when it arrives, and where it starts looking. No call needed.</p></li>
      <li><h3>Your first week</h3><p>Your first issue arrives on the schedule you pick, and your free week starts there. You read a week of real issues before anyone else does.</p></li>
    </ol>
    <p class="k">Before you start, read a real one: <a href="{DAILY}">The VFX Supervisor Daily</a>, Geoff's own newsletter about his own field. Yours covers your field, for your readers.</p>
  </div>
</section>'''

THANKS = f'''<section class="hero">
  <div class="wrap prose">
    <span class="eyebrow">Message sent</span>
    <h1>Thanks. Check your inbox for your start link.</h1>
    <p>LongLens has emailed you a one-time link. Click it and answer three short questions: what LongLens should follow, where and when it arrives, and where it starts looking. Your first issue arrives on the schedule you pick, and your free week starts there. The link works once, for 24 hours.</p>
    <p>Already have an account? The email holds your sign-in link instead. Geoff reads every message himself. Nothing else is sent to you, and you are not added to any list.</p>
    <p>Before you start, read <a href="{DAILY}">Geoff's own newsletter</a>, or go back to the <a href="/">LongLens home page</a>.</p>
  </div>
</section>'''

THANKS_PERSONAL = f'''<section class="hero">
  <div class="wrap prose">
    <span class="eyebrow">Message sent</span>
    <h1>Thanks. Geoff will reply to you personally.</h1>
    <p>LongLens could not send you a start link straight away, so Geoff will email you himself. He reads every message. You may also get a short thank-you email from LongLens. You are not added to any list.</p>
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
    <p class="k">Not set up yet? <a href="/contact/">Start your free week</a> and a start link arrives by email at once.</p>
  </div>
</section>'''

PRIVACY = f'''<section class="hero">
  <div class="wrap prose">
    <span class="eyebrow">Privacy</span>
    <h1>No tracking. No cookies. Your email reaches one person.</h1>
    <p>This website, getlonglens.com, runs no analytics or tracking scripts and sets no cookies. It is a set of plain pages hosted on GitHub Pages.</p>
    <h2>When you write to Geoff</h2>
    <p>Your email goes to Geoffrey Hancock at {EMAIL}. LongLens uses it to email you your start link, and Geoff uses it only to reply to you. Writing does not add you to any list.</p>
    <h2>Once you use LongLens</h2>
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

PAGES = [
    # slug, title, description, body, nav-current
    ("", "LongLens: a newsletter for your clients, written for you",
     "LongLens writes a newsletter under your name on what changed in your field and what it means for your clients, as a letter, audio, a picture and video. Free during the pilot, then from $19 a month.",
     HOME, ""),
    ("features", "Features | LongLens",
     "Every format (letter, audio, one picture, explainer and one-minute video), every place an issue goes, editing any line on the page, and what is coming.",
     FEATURES, "/features/"),
    ("pricing", "Pricing | LongLens",
     "Free during the invite-only pilot. After it, Solo at $19 a month or Business at $95 a month, and what each includes today.",
     PRICING, "/pricing/"),
    ("how-it-works", "How it works | LongLens",
     "One link by email, three short questions, and your first issue on the schedule you pick. Then weekly or daily, and you change any line on the page or by replying.",
     HOW, "/how-it-works/"),
    ("faq", "FAQ | LongLens",
     "Straight answers about LongLens: getting started, what reaches your clients and when, editing, formats, price and ownership.",
     FAQ, "/faq/"),
    ("contact", "Free week | LongLens",
     "Start a free week of LongLens: a one-time link by email at once, three short questions, then a week of your own newsletter before anyone else sees it.",
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
