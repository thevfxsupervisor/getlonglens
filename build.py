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

NAV = [("Features", "/features/"), ("Pricing", "/pricing/"), ("How it works", "/how-it-works/"),
       ("FAQ", "/faq/")]
CTA_LABEL = "Book a short call"


def mailto(subject: str, body: str = "") -> str:
    from urllib.parse import quote
    q = "subject=" + quote(subject)
    if body:
        q += "&body=" + quote(body)
    return f"mailto:{EMAIL}?{q}"


CALL_MAIL = mailto(
    "LongLens: book my short call",
    "Who are my customers, and what should they hear from me first?\n\n\n"
    "My name:\nMy business:\n",
)


EXTRAS = "up to two extras a week in total: the full audio conversation or slides"
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
    <nav aria-label="Footer">{links}<a href="/contact/">Email Geoff</a><a href="/sign-in/">Sign in</a><a href="/privacy/">Privacy</a></nav>
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


def close_cta(h2: str, text: str) -> str:
    return f'''<section class="close">
  <div class="wrap"><div>
    <h2>{h2}</h2>
    <p class="k">{text}</p>
    <div class="cta-row"><a class="btn btn-a" href="/contact/">Book a short call. Read your first week, under your name.</a></div>
  </div></div>
</section>'''


M = "/assets/media/"

EXAMPLE_LABEL = "Geoff's own issue for his own field, visual effects for film and TV"

FORMAT_STRIP = f'''<p class="eyebrow strip-label">Real examples from Geoff's own issue, each one labelled with its date</p>
<div class="fmt-strip six" role="list" aria-label="One newsletter in six formats, real examples">
  <div class="fmt-card" role="listitem"><div class="fmt-media tall"><a href="{M}read-letter.png"><img src="{M}read-letter.png" width="780" height="1276" loading="lazy" alt="Geoff's own issue of 13 Oct 2026 as an email on a phone: the date, the headline and a short paragraph on what it means for the reader."></a></div>
    <div class="fmt-txt"><b>Read it</b><p>Two minutes with coffee. Only what is new, and what it means for the reader.</p><p class="fmt-date">13 Oct 2026</p></div></div>
  <div class="fmt-card" role="listitem"><div class="fmt-media"><a href="{M}listen-top.png"><img src="{M}listen-top.png" width="780" height="352" loading="lazy" alt="The top of the same email when Listen leads: a Listen to this issue button above the headline."></a></div>
    <div class="fmt-txt"><b>Hear it</b><p>The whole issue as a conversation, for the drive in.</p>
    <audio controls preload="none" src="{M}issue-audio.m4a" aria-label="A short clip of the issue's audio"></audio><p class="fmt-date">13 Oct 2026, a short clip of 19 minutes</p></div></div>
  <div class="fmt-card" role="listitem"><div class="fmt-media"><a href="{M}issue-slide-1.png"><img src="{M}issue-slide-1.png" width="1280" height="714" loading="lazy" alt="The title slide of the same issue."></a></div>
    <div class="fmt-txt"><b>Flip the slides</b><p>A slide deck of the issue, ready for the Monday meeting.</p><p class="fmt-date">13 Oct 2026, the title slide</p></div></div>
  <div class="fmt-card" role="listitem"><div class="fmt-media"><a href="{M}issue-infographic.jpg"><img src="{M}issue-infographic.jpg" width="1280" height="714" loading="lazy" alt="One picture of a whole issue: headed panels on bidding, pipelines and incentives, each with a drawing and a short line."></a></div>
    <div class="fmt-txt"><b>See the picture</b><p>The whole issue on one picture. Tap to open it full size.</p><p class="fmt-date">30 Oct 2026</p></div></div>
  <div class="fmt-card" role="listitem"><div class="fmt-media"><video controls preload="none" playsinline poster="{M}issue-explainer-poster.jpg" src="{M}issue-explainer.mp4" width="640" height="360" aria-label="The first 15 seconds of an explainer video"></video></div>
    <div class="fmt-txt"><b>Watch it</b><p>A narrated explainer video of the issue, with drawings for each point.</p><p class="fmt-date">1 Nov 2026, the first 15 seconds of 7 minutes</p></div></div>
  <div class="fmt-card" role="listitem"><div class="fmt-media tall"><video controls preload="none" playsinline poster="{M}issue-short-poster.jpg" src="{M}issue-short.mp4" width="540" height="960" aria-label="The first 15 seconds of a short vertical video"></video></div>
    <div class="fmt-txt"><b>The short video</b><p>About a minute, upright for a phone, with captions on screen.</p><p class="fmt-date">4 Nov 2026, the first 15 seconds</p></div></div>
</div>
<p class="fmt-hint">All real, from {EXAMPLE_LABEL}. Yours is about your field, under your name.</p>'''

EDITOR_SHOT = f'''<figure class="shot"><a href="{M}edit-in-place.png"><img src="{M}edit-in-place.png" width="1100" height="770" loading="lazy" alt="The LongLens editor open on a real issue: a bar with Save, Discard and the inbox preview line on top, and every line of the issue below outlined, ready to click and change."></a><figcaption>The real editor, on {EXAMPLE_LABEL}, 13 Oct 2026.</figcaption></figure>'''

PROOF = f'''<div class="proof">
  <b>Who built it</b>
  <p>Geoffrey Hancock built LongLens first for his own field, visual effects for film and TV, and publishes his own issue with it most mornings: The VFX Supervisor Daily. He won a VES Award for Changeling and was nominated for another for Invictus. Now he sets LongLens up for owners and experts in any field, one call at a time.</p>
  <p class="links"><a href="{DAILY}">Read Geoff's own issue for his field</a></p>
</div>'''

# --------------------------------------------------------------------------------------------
# Home
# --------------------------------------------------------------------------------------------

HOME = f'''<section class="hero">
  <div class="wrap">
    <span class="eyebrow"><img src="/assets/mark-e1.svg" alt="" width="40" height="40">LongLens</span>
    <h1>Your customers will hear what's changing from someone. Make it you.</h1>
    <p class="lede">Every morning you pick, LongLens turns what changed in your industry into a short briefing your customers open, under your name, with what it means for them. You become the one they hear from and trust, without writing a word of it yourself. Two minutes to read, and often audio for the drive in.</p>
    <p class="price-line">{AI_LINE}</p>
    <div class="cta-row">
      <a class="btn btn-a" href="/contact/">Book a short call. Read your first week, under your name.</a>
    </div>
    <p class="price-line">Free during the pilot. Invite only: Geoff sets up every account himself. <a href="/pricing/">See what the pilot includes</a>.</p>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Far more than a newsletter</span>
      <h2>One issue your customers can read, hear, watch or flip through</h2>
      <p>Your customers do not all take in news the same way. One reads with coffee, one listens on the drive in, one wants the picture before the Monday meeting. LongLens turns each issue into all of them, so every customer gets the same news in the way they like it.</p></div>
    {FORMAT_STRIP}
    <div class="cards two">
      <div class="card"><h3>Where your customers get it today</h3><ul class="list">
        <li><strong>In their inbox</strong>: send the letter through the email tool you already use, or simply forward it.</li>
        <li><strong>On the web</strong>: each issue you publish gets a page of its own that anyone can open from a link, with no sign-in.</li>
        <li><strong>On a public page of all your issues</strong>, with the audio, the videos, the slides and the picture that passed their check. Geoff sets it up with you.</li>
        <li><strong>In a Slack or Discord channel</strong>: a short post with a link to each issue you publish, if you add a channel.</li>
        <li><strong>In a feed reader</strong>: a private RSS link to your published issues.</li>
      </ul></div>
      <div class="card"><h3>Where it goes next</h3><ul class="list">
        <li>{coming("<strong>Straight to each customer</strong> from your own address, for example news@yourbusiness.com, in the format each one picked, every issue.")}</li>
        <li>{coming("<strong>In podcast apps</strong>: the audio of every issue as a podcast your customers can follow.")}</li>
        <li>{coming("<strong>On Instagram and LinkedIn</strong>: posts made from each issue, ready for you to put up.")}</li>
        <li>{coming("<strong>On your own website</strong>: a block that shows your latest issue.")}</li>
        <li>{coming("<strong>On Telegram</strong>: each issue in a Telegram channel.")}</li>
      </ul></div>
    </div>
    <p class="k">Today the public page of your issues carries every format side by side, so each customer picks the one they like. {coming("Each customer picks once, and LongLens sends it to them that way every time.")} <a href="/features/">See every format and every place it goes</a>.</p>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Who it is for</span>
      <h2>Whoever your people are, be the name they hear from first</h2></div>
    <div class="cards">
      <div class="card"><h3>Owners who should be seen as the expert</h3><p>An accountant for small firms, a vet clinic, a builder's merchant, a law firm. A new rule, a recall, a price rise lands. Your customers read what it means for them from you that morning, not from a penalty letter next quarter.</p></div>
      <div class="card"><h3>Experts starting a business</h3><p>A consultant, a coach, a specialist going out alone. Before your first big client, show what you know every morning, under your name, to the people you want to work with.</p></div>
      <div class="card"><h3>Anyone building an audience they own</h3><p>A mentoring programme, an agency, a membership body, a school. Keep your whole community informed through your own email list, not followers a platform can take away.</p></div>
    </div>
    <p class="k">Daily for a fast-moving field, weekly for everyone else. You choose what LongLens follows and who it is written for.</p>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">What you get</span>
      <h2>Your customers get the news with the meaning attached. You get the credit.</h2></div>
    <div class="cards">
      <div class="card"><h3>What changed, and what it means for them</h3>
        <p>Every issue says what changed in your industry and what it means for your customers, with the original link, checked before the issue goes out.</p></div>
      <div class="card"><h3>Your name in front of them, morning after morning</h3>
        <p>Send each issue on through the email tool you already use, or forward it. Week after week they see who knew first. Issue #41 is the proof you were right in issue #12.</p></div>
      <div class="card"><h3>Sounds like you, because you taught LongLens</h3>
        <p>"Shorter." "More on the new rules, less on conferences." Reply in your own words and the next issue changes. Reply UNDO to take it back.</p></div>
    </div>
    <p class="k"><a href="/features/">See every feature</a></p>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Make it yours, on the page</span>
      <h2>Change any line right on your issue, exactly as your readers will see it.</h2></div>
    <div class="feat">
      <div class="txt">
        <p>No forms and no code. Open your issue, click the words you want to change, type, and press Save. LongLens rewrites the whole issue with your words in it and keeps every earlier version, so nothing you save is ever lost.</p>
        <ul>
          <li><strong>Your words on top</strong>: the headline, the opening, the line people see in their inbox before they open it.</li>
          <li><strong>Your say on every story</strong>: the line on what it means for them, and each short summary.</li>
          <li><strong>The facts stay put</strong>: story titles and links stay as the original publisher wrote them, so every story still points to its source.</li>
          <li><strong>Your sections, your order</strong>: drag the sections of a daily newsletter into the order you like, hide the ones you do not need, rename the headings and add a note from you. A preview shows your latest issue as you go.</li>
        </ul>
      </div>
      {EDITOR_SHOT}
    </div>
    <p class="k"><a href="/features/">See everything you can change</a></p>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">{PROOF}</div>
</section>

{close_cta("Your customers hear the news from someone. Make it you.",
           "One short call. Geoff points LongLens at the websites, forums, videos and newsletters you trust, and you see a week of real issues before anyone else does.")}'''

# --------------------------------------------------------------------------------------------
# Features
# --------------------------------------------------------------------------------------------

FEATURES = f'''<section class="hero">
  <div class="wrap">
    <span class="eyebrow">Features</span>
    <h1>What changed in your industry, and what it means for your customers. To read, hear, watch and flip through.</h1>
    <p class="lede">Far more than a newsletter. LongLens writes each issue as a short letter under your name, then turns the same issue into audio, slides, one picture, an explainer video and a short video, so each customer gets the news the way they like it. Change any line right on the page, exactly as your readers will see it.</p>
    <p class="price-line">{AI_LINE}</p>
    {FORMAT_STRIP}
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Every format</span>
      <h2>The same news, in the way each customer likes it</h2>
      <p>Every format is switched on for a new account. Each one is made once per issue, from the same stories, so whichever a customer picks, they get the same news.</p></div>
    <div class="cards">
      <div class="card"><h3>Read it</h3><p>The letter: what changed and what it means for them, with a link to every original story. By email, and on the web once you publish the issue.</p></div>
      <div class="card"><h3>Skim it</h3><p>A short email with the one line that matters most and a button to read the whole issue on the web.</p></div>
      <div class="card"><h3>Hear it</h3><p>The issue as a conversation between two voices, for the drive in. On a day that service is down, LongLens makes the audio itself instead.</p></div>
      <div class="card"><h3>Flip the slides</h3><p>A slide deck of the issue, ready to put on screen in a meeting.</p></div>
      <div class="card"><h3>See the picture</h3><p>The whole issue on one picture, with a drawing and a short line for each point.</p></div>
      <div class="card"><h3>Watch it</h3><p>A narrated explainer video of the issue, a few minutes long.</p></div>
      <div class="card"><h3>The short video</h3><p>About a minute, upright for a phone, with captions on screen.</p></div>
      <div class="card"><h3>Story pictures</h3><p>Turn them on and your top stories each get a small picture in your colours. Off until you turn them on. {coming("A picture generated for each story, in your own style.")}</p></div>
    </div>
    <ul class="list">
      <li><strong>When the audio, slides, picture and videos come</strong>: with any issue that includes stories from public websites. An issue with no stories from public websites goes out as the letter alone.</li>
      <li><strong>Checked before anyone sees them</strong>: LongLens checks every audio, slide deck, picture and video against the stories. A piece that fails is held back, and the letter goes out without it.</li>
      <li><strong>Slides, the picture and the videos</strong> come from one outside service. On a day it is down, the issue goes out without them.</li>
      <li><strong>You pick what leads your own email</strong>: Read it, Skim it, Listen, Watch, See it, Slides or the short video. The letter always follows.</li>
      <li><strong>Each customer, their own way</strong>: today the public page of your issues carries every format side by side, so each customer picks the one they like. {coming("Each customer picks once at the bottom of their email, and LongLens sends every issue that way: the audio first, the video first, or just the top stories.")}</li>
    </ul>

    <div class="sec-head"><span class="eyebrow">Where it goes</span>
      <h2>Every place your customers can get each issue</h2>
      <p>Your newsletter's name and issue number are on every one, wherever it lands.</p></div>
    <div class="cards two">
      <div class="card"><h3>Today</h3><ul class="list">
        <li><strong>In their inbox</strong>: send the letter through the email tool you already use, or simply forward it.</li>
        <li><strong>On the web</strong>: each issue you publish gets a page of its own that anyone can open from a link, with no sign-in.</li>
        <li><strong>On a public page of all your issues</strong>, with the audio, the videos, the slides and the picture that passed their check. Geoff sets it up with you.</li>
        <li><strong>In a Slack or Discord channel</strong>: a short post with a link to each issue you publish, if you add a channel.</li>
        <li><strong>In a feed reader</strong>: a private RSS link to your published issues.</li>
        <li><strong>In your own inbox first</strong>: every issue lands with you, with every format on its page in your account.</li>
      </ul></div>
      <div class="card"><h3>Coming</h3><ul class="list">
        <li>{coming("<strong>Straight to each customer</strong> from your own address, for example news@yourbusiness.com, in the format each one picked, every issue.")}</li>
        <li>{coming("<strong>In podcast apps</strong>: the audio of every issue as a podcast your customers can follow.")}</li>
        <li>{coming("<strong>On Instagram and LinkedIn</strong>: posts made from each issue, ready for you to put up.")}</li>
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
          <li><strong>Plain words in, the full issue out</strong>: type as you would in an email. On Save, LongLens rewrites the whole issue with your words in it, in every copy it keeps.</li>
          <li><strong>Every version kept</strong>: the issue as LongLens first wrote it, and every save after that, so any change can be traced and copied back.</li>
          <li><strong>Locked once it goes out</strong>: once an issue is approved or sent, it stays exactly as it went.</li>
        </ul>
      </div>
      {EDITOR_SHOT}
    </div>

    <div class="feat">
      <div class="txt">
        <h2>Arrange your issue the way you would lay out a page</h2>
        <p>The Sections page puts every part of a daily newsletter in a list you can rearrange, with a live preview of your latest issue beside it.</p>
        <ul>
          <li><strong>Your order</strong>: drag a section, or use the arrows, to move it.</li>
          <li><strong>Only what you need</strong>: hide a section with one tick, or show at most a set number of stories in it.</li>
          <li><strong>Your headings</strong>: rename any section in your own words.</li>
          <li><strong>A note from you</strong>: add your own note, with its own heading, or a divider, anywhere in the issue.</li>
          <li><strong>Back to the usual</strong>: one button puts the usual sections back.</li>
        </ul>
        <p>Your next issue uses the new layout in the email. Issues already written stay as they were.</p>
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
        <h2>Hit reply. The next issue listens.</h2>
        <p>Teach LongLens the way you would teach a new hire: reply to any issue in your own words. LongLens answers in the same thread with what it understood, and the next issue follows it.</p>
        <ul>
          <li><strong>Length</strong>: shorter, longer, or how many stories.</li>
          <li><strong>Topics</strong>: more of one thing, less of another.</li>
          <li><strong>Your customers</strong>: a new sentence about who they are and what matters to them.</li>
          <li><strong>Websites</strong>: paste a link to add one, name one to drop it.</li>
          <li><strong>Tone and layout</strong>: how it sounds, how each story is laid out.</li>
          <li><strong>Extras</strong>: add or drop the full audio or the slides.</li>
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
        <h2>Built from the websites, forums and videos you already trust</h2>
        <p>Every issue covers what is new on the websites, forums, YouTube channels and topics your industry follows. Name them to Geoff on your call, or paste a link into a reply any time.</p>
        <ul>
          <li><strong>Forward the newsletters you never open</strong>, or save a page from your phone or browser. What matters lands in your next issue under "You sent".</li>
          <li><strong>One tap to turn a website off</strong>, one more to turn it back on. LongLens never adds a website you turned off back by itself.</li>
          <li><strong>New websites, found for you</strong>: LongLens lists the ones your stories came from under "New sources for you", each with a way to remove it.</li>
        </ul>
      </div>
      <div class="txt">
        <h2>LongLens checks every story before your customers read it</h2>
        <ul>
          <li><strong>What it means for them</strong>: most stories carry one line on why they matter to your customers, so the issue is never a link dump.</li>
          <li><strong>No repeats</strong>: a story they have already seen stays out until something changes, then comes back marked as an update.</li>
          <li><strong>Names and figures</strong> are checked against the original story.</li>
          <li><strong>Every link is tried</strong> before the issue goes out. A story whose only link is dead is left out, and the last line says how many links were checked and how many were dead.</li>
        </ul>
      </div>
    </div>

    <div class="feat">
      <div class="txt">
        <h2>On your desk when you sit down</h2>
        <p>LongLens arrives on the days and at the time you pick, in your time zone. Daily for a fast-moving field, weekly for everyone else.</p>
        <p>Away for a week? Press Pause this newsletter at the bottom of any issue. The same page starts it again.</p>
      </div>
      <div class="txt">
        <h2>Yours to keep</h2>
        <p>You own what LongLens makes: every issue, every website you chose, every lesson you taught LongLens.</p>
      </div>
    </div>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">An honest comparison</span>
      <h2>Three other ways to be the expert, and what each one costs you</h2></div>
    <div class="cards">
      <div class="card"><h3>By hand</h3><p>Read the industry press every morning and write it up yourself. Full control. It costs the hours you do not have, and it dies the first busy week.</p></div>
      <div class="card"><h3>A newsletter platform</h3><p>Great at sending and at growing a list. No idea what to say. You still find the news and write every word.</p></div>
      <div class="card"><h3>A personal AI summary</h3><p>Fast, often free, and fine for keeping yourself informed. Written for you alone. Nobody else reads it, nobody learns what you know, and your name is nowhere on it.</p></div>
    </div>
    <p class="k">LongLens tells your customers what today's news means for them, ready to send as text and often as audio. You keep the name, the last word and the customers.</p>
    <div class="notfor"><h3>What LongLens does not do</h3><ul>
      <li><strong>Write your own company news.</strong> LongLens works from what the industry press, the forums and the videos say about your field. Your own announcements are still yours to write.</li>
      <li><strong>Run ads or paid subscriptions.</strong> Use a newsletter platform built for that.</li>
      <li><strong>Replace you.</strong> Your judgment is the point. LongLens makes it reach further, issue after issue.</li>
    </ul></div>
  </div>
</section>

{close_cta("Put the news in your customers' hands before anyone else does.",
           "Tell Geoff who your customers are and what they should hear from you first. He sets LongLens up with you on one short call.")}'''

# --------------------------------------------------------------------------------------------
# Pricing
# --------------------------------------------------------------------------------------------

PRICING = f'''<section class="hero">
  <div class="wrap">
    <span class="eyebrow">Pricing</span>
    <h1>Free during the pilot. Put your name in front of your customers at no cost.</h1>
    <p class="lede">LongLens is in its pilot, and the pilot is free. Paid plans are coming.</p>
    <div class="card" style="margin-top:28px;max-width:780px"><h2 style="font-size:20px">What the pilot includes today</h2>
      <ul class="list" style="margin-top:8px">
        <li>Your letter with each issue, daily or weekly, under your newsletter's name</li>
        <li>A plain-voice audio read with most issues</li>
        <li>{EXTRAS[0].upper() + EXTRAS[1:]}</li>
        <li>Change anything by replying in plain words</li>
        <li>Send each issue through the email tool you already use, or forward it</li>
        <li>Each issue posted to your Slack or Discord channel, if you add one</li>
        <li>Set up with you by Geoff, on one short call</li>
      </ul>
      <div class="cta-row"><a class="btn btn-a" href="/contact/">Join the free pilot. Book a short call.</a></div>
    </div>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">How the pilot works</span>
      <h2>No card form. Geoff sets you up himself.</h2></div>
    <ul class="list">
      <li><strong>Invite only, for now.</strong> Geoff sets up every account himself. {coming("Sign up on your own.")}</li>
      <li><strong>It starts with a short call.</strong> You and Geoff pin down who your customers are and what they should hear from you first.</li>
      <li><strong>A set amount of writing each month.</strong> The pilot covers a set amount of writing a month. If you reach it, LongLens says so on your pages and picks up again next month.</li>
      <li><strong>Up to two extras a week in total</strong>: the full audio conversation or slides. Once those two are used, the plain-voice audio can still come, and the rest waits until next week.</li>
      <li><strong>Paid plans</strong> {coming()}</li>
    </ul>
  </div>
</section>

{close_cta("Be the name on your customers' morning news.",
           "One short call, then a week of real issues under your name before anyone else sees them.")}'''

# --------------------------------------------------------------------------------------------
# How it works
# --------------------------------------------------------------------------------------------

HOW = f'''<section class="hero">
  <div class="wrap">
    <span class="eyebrow">How it works</span>
    <h1>One short call. Then what's changing for your customers lands daily or weekly, under your name.</h1>
    <p class="lede">No software to learn and no password to remember. Geoff sets LongLens up with you, and from then on you change anything by replying to an issue.</p>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Getting started</span><h2>From a short call to your first issue</h2></div>
    <ol class="steps two">
      <li><h3>Book a short call</h3>
        <p>Tell Geoff who your customers are and what they should hear from you first. He reads every message himself and replies from {EMAIL}.</p>
        <p><a href="/contact/">Book a short call</a></p></li>
      <li><h3>Geoff sets LongLens up with you</h3>
        <p>He points LongLens at the websites, forums, videos and newsletters you trust, and you describe your customers in your own words. You see a week of real issues before anyone else does.</p></li>
      <li><h3>Sign in with the link Geoff emails you</h3>
        <p>Open it and press Get started. There is no password. Three short questions follow, on your own or with Geoff:</p>
        <ul><li>What should LongLens follow, said the way you would tell a friend?</li>
          <li>Where and when: by email and on a web page, or the web page only, how often, what time, your time zone.</li>
          <li>Where should LongLens start looking: websites, feeds or keywords, or a starter set.</li></ul></li>
      <li><h3>Your first issue can land today</h3>
        <p>Press Make my newsletter. Then open Issues and press Make an issue now: LongLens starts on it within ten minutes and emails it to you.</p></li>
    </ol>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Every morning</span><h2>What lands in your inbox, and why you can trust it</h2>
      <p>At the time you picked, LongLens turns the day's news in your industry into one issue with your newsletter's name on it.</p></div>
    <ol class="steps three">
      <li><h3>LongLens catches anything new</h3><p>From every website, feed, forum and channel you follow.</p></li>
      <li><h3>LongLens keeps what matters to your customers</h3><p>A story you have already had stays out, unless something changed. Then it comes back marked as an update.</p></li>
      <li><h3>Every story says what it means for them</h3><p>Most stories carry a short line on why they matter to your customers, and every story links to the original.</p></li>
      <li><h3>Every link is tried first</h3><p>A story whose only link is dead is left out, and a line at the foot of the issue says how many links were checked and how many were dead.</p></li>
      <li><h3>Your copy arrives by email</h3><p>Nothing to press. Every issue is also kept on the Issues page when you sign in.</p></li>
      <li><h3>Audio and slides follow</h3><p>Often, on the issue's page, once they pass their check. On extras days your copy can arrive up to a few hours later.</p></li>
    </ol>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Your daily routine</span><h2>Four answers cover most mornings</h2></div>
    <ul class="list">
      <li><strong>Change your issue</strong>: reply to any issue in plain words, for example "shorter please". The next issue follows it.</li>
      <li><strong>Undo a change</strong>: reply UNDO.</li>
      <li><strong>Pause it</strong>: press Pause this newsletter at the bottom of any issue. The same page starts it again.</li>
      <li><strong>Sign in</strong>: type your email on the <a href="/sign-in/">sign-in page</a> and a fresh link arrives by email, usually within a minute. Each link works once, and keeps you signed in for 30 days on that device.</li>
    </ul>
    <p class="k">Sending to your customers: today each issue comes to you first, and you send it through the email tool you already use, or forward it. {coming("Email straight to your customers from your own address.")}</p>
  </div>
</section>

{close_cta("Book the call. Read your first week.",
           "You see a week of real issues before anyone else does.")}'''

# --------------------------------------------------------------------------------------------
# FAQ
# --------------------------------------------------------------------------------------------

def qa(q, a):
    return f"<details><summary>{q}</summary>{a}</details>"


FAQ_ITEMS = [
    ("Getting started", [
        ("How do we start, and how does LongLens reach my customers?",
         "<p>A short call, then Geoff points LongLens at the websites, forums, videos and newsletters you trust, and you describe your customers in your own words. You see a week of real issues before anyone else does. Today each issue comes to you first, and you send it through the email tool you already use, or forward it. Email straight to your customers from your own address is coming.</p>"),
        ("Can I sign up on my own?",
         f"<p>Not yet. LongLens is invite only for now, and Geoff sets up every account himself. <a href=\"/contact/\">Book a short call with Geoff</a>.</p>"),
        ("How do I sign in?",
         f"<p>With a link by email. There is no password. Type your email on the <a href=\"/sign-in/\">sign-in page</a> and a fresh link arrives, usually within a minute. Each link works once and keeps you signed in for 30 days on that device.</p>"),
    ]),
    ("What you get", [
        ("Is AI writing it?",
         "<p>Yes. LongLens writes with AI, checks names and figures against the original story, tries every link before the issue goes out, and you change anything by replying. Your name is on it, so the last word is yours.</p>"),
        ("Is LongLens only for one kind of business?",
         "<p>No. LongLens works for any business whose customers need to know what is changing: an accountant, a vet clinic, a builder's merchant, a law firm, a recruiter, a school, a mentoring programme or a consultancy. Geoff built it first for his own field, visual effects, and that is the example you can read on this site. Yours follows the websites, forums and newsletters of your industry.</p>"),
        ("What if the audio or slides are missing?",
         "<p>Each week you get up to two extras: the full audio or the slides. Once those two are used, audio still comes as the plainer spoken version. If the piece that leads your email is missing, you get the full letter with one line saying so.</p>"),
        ("Can LongLens write my own company news?",
         "<p>No. LongLens works from what the industry press, the forums and the videos say about your field. Your own announcements are still yours to write.</p>"),
    ]),
    ("Day to day", [
        ("How do I change what I get?",
         "<p>Reply to any issue in plain words: shorter, more on one topic, drop a website, add the slides. LongLens confirms what it understood in the same thread, and the next issue follows it. Reply UNDO to take it back. The days and the time are changed on your settings page after you sign in.</p>"),
        ("Can I stop it for a while?",
         "<p>Yes. Press Pause this newsletter at the bottom of any issue. The same page starts it again.</p>"),
        ("Can a colleague change my issue by replying?",
         "<p>No. LongLens acts only on replies from the address your issue goes to. A forward to a colleague changes nothing.</p>"),
    ]),
    ("Money and ownership", [
        ("What does LongLens cost?",
         "<p>Nothing during the pilot: LongLens is free while it runs. Paid plans are coming. <a href=\"/pricing/\">See what the pilot includes</a>.</p>"),
        ("Who owns what LongLens makes?",
         "<p>You do. Every issue, every website you chose, every lesson you taught LongLens.</p>"),
        ("Who is behind LongLens?",
         f"<p>Geoffrey Hancock. He built LongLens first for his own field, visual effects for film and TV, and publishes his own issue with it most mornings: <a href=\"{DAILY}\">The VFX Supervisor Daily</a>. He won a VES Award for Changeling and was nominated for another for Invictus.</p>"),
    ]),
]

FAQ = f'''<section class="hero">
  <div class="wrap">
    <span class="eyebrow">FAQ</span>
    <h1>Straight answers. Including what LongLens does not do yet.</h1>
    <p class="lede">Getting started, signing in, what you get, day to day, price and ownership.</p>
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
      <li><strong>Email straight to your customers</strong> {coming()}<br>Issues sent from your own address (for example news@yourbusiness.com), each customer in the format they picked, with a dated record of each customer's yes and one-click unsubscribe.</li>
      <li><strong>Each customer picks their format</strong> {coming()}<br>Read it, Skim it, Listen, Slides or See it, from a link at the bottom of every issue they get.</li>
      <li><strong>The one picture</strong> {coming()}<br>The whole issue on one screen, for the person who will not read.</li>
      <li><strong>Your issue on Telegram</strong> {coming()}<br>Today it comes by email, on the web, and in your Slack or Discord channel.</li>
      <li><strong>Sign up on your own</strong> {coming()}<br>Today Geoff sets it up with you.</li>
    </ul>
  </div>
</section>

{close_cta("Ask the person who built LongLens.",
           "Geoff reads every message himself and replies personally.")}'''

# --------------------------------------------------------------------------------------------
# Contact
# --------------------------------------------------------------------------------------------

def inquiry_form() -> str:
    return f'''<form class="contact-card" method="post" action="{INQUIRY_ENDPOINT}" accept-charset="utf-8">
  <p><label for="f-name">Your name</label><br><input id="f-name" name="name" required maxlength="200" autocomplete="name"></p>
  <p><label for="f-email">Email</label><br><input id="f-email" type="email" name="email" required maxlength="320" autocomplete="email"></p>
  <p><label for="f-company">Your business (optional)</label><br><input id="f-company" name="company" maxlength="200" autocomplete="organization"></p>
  <input type="hidden" name="offer" value="brief"><input type="hidden" name="source" value="longlens">
  <p><label for="f-message">Who are your customers, and what should they hear from you first?</label><br><textarea id="f-message" name="message" required maxlength="5000"></textarea></p>
  <p style="position:absolute;left:-9999px" aria-hidden="true"><label for="f-website">Leave this empty</label><input id="f-website" name="website" tabindex="-1" autocomplete="off"></p>
  <p><label><input type="checkbox" name="consent" value="yes" required> {INQUIRY_CONSENT}</label></p>
  <button class="btn btn-a" type="submit">Book my short call</button>
  <p class="email-line">Rather email? Write to <a href="{html.escape(CALL_MAIL)}">{EMAIL}</a>. Writing does not add you to any list.</p>
</form>'''


CONTACT_BODY = inquiry_form() if FORM_LIVE else f'''<div class="contact-card">
  <h2 style="font-size:22px">Email Geoff. Three lines are enough.</h2>
  <ol>
    <li>Who your customers are.</li>
    <li>What they should hear from you first.</li>
    <li>Your name and your business.</li>
  </ol>
  <a class="btn btn-a" href="{html.escape(CALL_MAIL)}">Email Geoff to book a call</a>
  <p class="email-line">Or write to <a href="mailto:{EMAIL}">{EMAIL}</a></p>
  <p class="tiny">Writing does not add you to any list. Geoff replies personally to set up the call.</p>
</div>'''

CONTACT = f'''<section class="hero">
  <div class="wrap">
    <span class="eyebrow">Book a call</span>
    <h1>Book a short call. Read your first week, under your name.</h1>
    <p class="lede">Tell Geoff who your customers are and what they should hear from you first. He reads every message himself and replies from {EMAIL} to set up a short call. Free during the pilot, invite only.</p>
    {CONTACT_BODY}
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">What happens next</span><h2>From your message to your first week of issues</h2></div>
    <ol class="steps three">
      <li><h3>Geoff replies</h3><p>Personally, to set up a short call. Nothing is sent to you automatically.</p></li>
      <li><h3>The call</h3><p>You pin down who your customers are and what they should hear from you first.</p></li>
      <li><h3>Your first week</h3><p>Geoff sets LongLens up with you, and you see a week of real issues before anyone else does.</p></li>
    </ol>
    <p class="k">Before the call, see a real one: <a href="{DAILY}">The VFX Supervisor Daily</a>, Geoff's own issue for his own field, written with LongLens. Yours covers your field, under your name.</p>
  </div>
</section>'''

# --------------------------------------------------------------------------------------------
# Sign in, privacy, 404
# --------------------------------------------------------------------------------------------

SIGNIN_PAGE = f'''<section class="hero">
  <div class="wrap">
    <span class="eyebrow">Sign in</span>
    <h1>Sign in with one link. No password.</h1>
    <p class="lede">The LongLens app lives at <strong>newsletter-edge.thevfxsupervisor.workers.dev</strong>. The button below takes you to its sign-in page: type your email and a link arrives by email, usually within a minute. The link keeps you signed in for 30 days on that device.</p>
    <div class="cta-row"><a class="btn btn-a" href="{SIGNIN}">Open the LongLens app and get my sign-in link</a></div>
    <p class="k">Not set up yet? LongLens is invite only for now. <a href="/contact/">Book a short call with Geoff</a>.</p>
  </div>
</section>'''

PRIVACY = f'''<section class="hero">
  <div class="wrap prose">
    <span class="eyebrow">Privacy</span>
    <h1>No tracking. No cookies. Your email reaches one person.</h1>
    <p>This website, getlonglens.com, runs no analytics or tracking scripts and sets no cookies. It is a set of plain pages hosted on GitHub Pages.</p>
    <h2>When you write to Geoff</h2>
    <p>Your email goes to Geoffrey Hancock at {EMAIL}. He uses it only to reply to you. Writing does not add you to any list.</p>
    <h2>Once you use LongLens</h2>
    <p>What the LongLens app keeps about you, where it lives and who else sees anything is set out on the app's own privacy page: <a href="{APP_PRIVACY}">LongLens app privacy</a>.</p>
  </div>
</section>'''

NOT_FOUND = '''<section class="hero">
  <div class="wrap prose">
    <span class="eyebrow">Not found</span>
    <h1>That page is not here.</h1>
    <p><a href="/">Go to the LongLens home page</a>, or <a href="/contact/">book a short call with Geoff</a>.</p>
  </div>
</section>'''

# --------------------------------------------------------------------------------------------

PAGES = [
    # slug, title, description, body, nav-current
    ("", "LongLens: your customers hear what's changing from you",
     "Every morning, LongLens turns what changed in your industry into a short briefing your customers open, under your name, with what it means for them. Free during the pilot.",
     HOME, ""),
    ("features", "Features | LongLens",
     "What changed in your industry and what it means for your customers: to read, often to hear, and changed by replying in plain words.",
     FEATURES, "/features/"),
    ("pricing", "Pricing | LongLens",
     "LongLens is free during the pilot. What the pilot includes today, and paid plans coming.",
     PRICING, "/pricing/"),
    ("how-it-works", "How it works | LongLens",
     "One short call, a sign-in link by email, and your first issue the same day. Then daily or weekly, and you change anything by replying.",
     HOW, "/how-it-works/"),
    ("faq", "FAQ | LongLens",
     "Straight answers about LongLens: getting started, signing in, what you get, changing it by replying, price and ownership.",
     FAQ, "/faq/"),
    ("contact", "Book a call | LongLens",
     "Email Geoffrey Hancock for a short call and read your first week, under your name.",
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
