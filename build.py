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
EMAIL = "geoff@thevfxsupervisor.com"

# The inquiry form. The app's endpoint (POST /hooks/inquiry) refuses any Origin but
# https://thevfxsupervisor.com today (NL_INQUIRY_ORIGINS), so the contact page uses email until
# the app accepts https://getlonglens.com. Flip FORM_LIVE to True once it does, then rebuild.
FORM_LIVE = False
INQUIRY_ENDPOINT = APP + "/hooks/inquiry"
INQUIRY_CONSENT = "I agree to be contacted about this message at the email address I gave."

NAV = [("Features", "/features/"), ("Pricing", "/pricing/"), ("How it works", "/how-it-works/"),
       ("FAQ", "/faq/")]
CTA_LABEL = "Email Geoff to book a call"


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


EXTRAS = "up to two extras a week in total: the full audio conversation, a short video or slides"
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
<meta property="og:image" content="{SITE}/assets/media/issue-video-poster.jpg">
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
    <div class="cta-row"><a class="btn btn-a" href="/contact/">Email Geoff to book a call. See a week of your news, under your name.</a></div>
  </div></div>
</section>'''


M = "/assets/media/"

FORMAT_STRIP = f'''<p class="eyebrow strip-label">One morning, every format</p>
<div class="fmt-strip" role="list" aria-label="The same issue, every way it comes today">
  <div class="fmt-card" role="listitem"><div class="fmt-media tall"><a href="{M}read-letter.png"><img src="{M}read-letter.png" width="780" height="1276" loading="lazy" alt="The 13 Oct 2026 issue as an email on a phone: the date, the headline and a short paragraph on why it matters."></a></div>
    <div class="fmt-txt"><b>Read it</b><p>Two minutes with coffee. Only what is new, and why it matters to your customers.</p></div></div>
  <div class="fmt-card" role="listitem"><div class="fmt-media"><a href="{M}listen-top.png"><img src="{M}listen-top.png" width="780" height="352" loading="lazy" alt="The top of the same email when Listen leads: a Listen to this issue button above the headline."></a></div>
    <div class="fmt-txt"><b>Hear it</b><p>The whole issue as a conversation, for the van.</p>
    <audio controls preload="none" src="{M}issue-audio.m4a" aria-label="A short clip of the issue's audio overview"></audio></div></div>
  <div class="fmt-card" role="listitem"><div class="fmt-media"><video controls playsinline preload="none" poster="{M}issue-video-poster.jpg" width="1280" height="720" aria-label="A short silent clip of the issue's explainer video"><source src="{M}issue-video.mp4" type="video/mp4"></video></div>
    <div class="fmt-txt"><b>Watch it</b><p>A short explainer, crafted from the same words.</p></div></div>
  <div class="fmt-card" role="listitem"><div class="fmt-media"><a href="{M}issue-slide-1.png"><img src="{M}issue-slide-1.png" width="1280" height="714" loading="lazy" alt="The title slide of the same issue: Defending margins in an AI-augmented production reality."></a></div>
    <div class="fmt-txt"><b>Flip the slides</b><p>For the Monday meeting, one story a slide.</p></div></div>
  <div class="fmt-card fmt-coming" role="listitem"><div class="fmt-txt"><b>The one picture</b> {coming()}<p>The whole issue on one screen, for the person who will not read.</p></div></div>
</div>
<p class="fmt-hint">All from one real issue of Geoff's own VFX briefing, 13 Oct 2026. The audio and video here are short clips of the full 19 and 7 minutes.</p>'''

PROOF = f'''<div class="proof">
  <b>The proof, every morning</b>
  <p>The VFX Supervisor Daily is Geoffrey Hancock's own morning VFX briefing, crafted with LongLens. Read it, hear it, watch it. That is how he shows producers what he knows before they hire him.</p>
  <p class="links"><a href="{DAILY}">Read this morning's Daily</a></p>
</div>'''

# --------------------------------------------------------------------------------------------
# Home
# --------------------------------------------------------------------------------------------

HOME = f'''<section class="hero">
  <div class="wrap">
    <span class="eyebrow"><img src="/assets/mark-e1.svg" alt="" width="40" height="40">LongLens</span>
    <h1>Stop being quietly brilliant. Be the expert your customers hear from first.</h1>
    <p class="lede">Daily or weekly, LongLens turns your trade's news into a letter under your name: what changed, and why it matters to your customers. Read it or hear it, with up to two extras a week in total: the full audio conversation, a short video or slides, and change anything by replying in plain words.</p>
    <p class="price-line">LongLens uses AI to write each issue, then checks names and figures against the original story before you see it.</p>
    <div class="cta-row">
      <a class="btn btn-a" href="/contact/">Email Geoff to book a call. See a week of your news, under your name.</a>
      <a class="btn btn-b" href="{DAILY}">Read this morning's Daily</a>
    </div>
    <p class="price-line">Free, Solo at $19 a month, or Business at $95 a month. <a href="/pricing/">Compare the three plans</a>.</p>
    {FORMAT_STRIP}
    <p class="coming-line">{coming("LongLens sends straight to each customer, in the format each one picks. Today every format lands with you first, ready to send through the email tool you already use, or to forward.")}</p>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">{PROOF}</div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">What you get</span>
      <h2>Your customers get the news with the meaning attached. You get the credit.</h2></div>
    <div class="cards">
      <div class="card"><h3>The news, and why it matters to them</h3>
        <p>Every issue says what changed in your trade and why it matters to your customers, with the original link, checked before the issue goes out.</p></div>
      <div class="card"><h3>Your name in front of them, issue after issue</h3>
        <p>Send each issue on through the email tool you already use, or forward it. Week after week they see who knew first. Issue #41 is the proof you were right in issue #12.</p></div>
      <div class="card"><h3>Sounds like you, because you taught LongLens</h3>
        <p>"Shorter." "More on the new rules, less on trade shows." Reply in your own words and the next issue changes. Reply UNDO to take it back.</p></div>
    </div>
    <p class="k"><a href="/features/">See every feature</a></p>
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Who it is for</span>
      <h2>The plumber, the adviser, the trade body: the one customers should hear the news from first</h2></div>
    <div class="cards">
      <div class="card"><h3>A local trade</h3><p>A plumber, an electrician, a builder. New rules, prices and kit, explained by the person who will fit it. Your customers hear it from you first, and remember who told them.</p></div>
      <div class="card"><h3>Advisers and consultancies</h3><p>You are paid for knowing. Send your issue on and your clients get a taste of it every week, under your name, and a reply turns into a conversation.</p></div>
      <div class="card"><h3>Trade bodies and brands</h3><p>Send one issue to the whole field, and everyone hears what changed from one source it trusts, with a person's name on every issue.</p></div>
    </div>
    <p class="k">Daily for a fast-moving trade, weekly for everyone else.</p>
  </div>
</section>

{close_cta("Your customers hear the news from someone. Make it you.",
           "One short call. Geoff points LongLens at the websites, forums, videos and newsletters you trust, and you see a week of real issues before anyone else does.")}'''

# --------------------------------------------------------------------------------------------
# Features
# --------------------------------------------------------------------------------------------

FEATURES = f'''<section class="hero">
  <div class="wrap">
    <span class="eyebrow">Features</span>
    <h1>One morning of news. Every way your customers take it in.</h1>
    <p class="lede">LongLens crafts each issue once as a letter, then turns the same issue into audio, a short explainer video and slides. More for your customers than you could make by hand.</p>
    <p class="price-line">LongLens uses AI to write each issue, then checks names and figures against the original story before you see it.</p>
    {FORMAT_STRIP}
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="feat">
      <div class="txt">
        <h2>Read it, skim it, hear it, watch it, flip it</h2>
        <p>Pick the one that leads your own email. The extras you turn on play on the issue's page in your account.</p>
        <ul>
          <li><strong>Read it</strong>: the whole letter in your email.</li>
          <li><strong>Skim it</strong>: a short email with a link to read it on the web.</li>
          <li><strong>Listen</strong>: the audio overview on top, then the letter. Or a shorter plain read.</li>
          <li><strong>Watch</strong>: the short explainer video on top, then the letter.</li>
          <li><strong>Slides</strong>: the slide deck on top, then the letter.</li>
          <li>{coming("<strong>See it</strong>: the whole issue on one screen, as a format of its own.")}</li>
        </ul>
        <p>Every plan gets a plain-voice audio read with each issue, and up to two extras a week in total: the full audio conversation, a short video or slides. Audio, video and slides come when the issue includes stories from public websites. LongLens checks every audio, slide and video against the stories before you see it.</p>
      </div>
      <figure class="shot"><img src="/assets/formats-video.png" width="1280" height="720" loading="lazy" alt="The explainer video of one real issue, paused on a frame that reads: A human touch is absolutely essential."><figcaption>Real explainer video from one issue of Geoff's own VFX briefing.</figcaption></figure>
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
          <li><strong>Extras</strong>: add or drop the audio, the slides or the video.</li>
        </ul>
        <p>Reply UNDO to take back the last change. LongLens acts only on replies from you: a forward to a colleague changes nothing.</p>
      </div>
      <div class="exchange" aria-label="An example reply and the answer">
        <span class="who">You</span>
        <p class="you">Longer please. More on the new rules, less on trade shows.</p>
        <span class="who">LongLens, in the same thread</span>
        <div class="ll">
          <p>Got it. Your issues will be the usual length from the next one.</p>
          <p>You'll see more on the new rules from the next issue.</p>
          <p>You'll see less on trade shows from the next issue.</p>
          <p>Changed your mind? Just reply UNDO.</p>
        </div>
      </div>
    </div>

    <div class="feat">
      <div class="txt">
        <h2>Your name on every issue. Your customers remember who told them.</h2>
        <p>Every issue carries your newsletter's name and its issue number. Send it on through the email tool you already use, or simply forward it.</p>
        <ul>
          <li>Each issue posted to your Slack or Discord channel, if you add one.</li>
          <li>Your own blog page, set up by Geoff, and you choose which issues go up.</li>
          <li>{coming("LongLens sends straight to your customers from your own address, for example news@yourbusiness.com, each one in the format they picked, with a dated record of each yes and one-click unsubscribe.")}</li>
          <li>{coming("Social posts for every issue, and your issue on Telegram.")}</li>
        </ul>
      </div>
      <figure class="shot"><img src="/assets/links.png" width="600" height="385" loading="lazy" alt="The end of a real web issue, finishing with: 2 links checked when this went out, 0 dead."><figcaption>Real web issue, last lines.</figcaption></figure>
    </div>

    <div class="feat">
      <div class="txt">
        <h2>You decide where LongLens looks</h2>
        <p>Name the websites, feeds, forums, YouTube channels and keywords your trade lives on. LongLens catches anything new from every one of them before each issue.</p>
        <ul>
          <li><strong>Forward the newsletters you never open</strong>, or save a page from your phone or browser. What matters lands in your next issue under "You sent".</li>
          <li><strong>One tap to turn a website off</strong>, one more to turn it back on. LongLens never adds a website you turned off back by itself.</li>
          <li><strong>New websites, found for you</strong>: LongLens lists the ones your stories came from under "New sources for you", each with a way to remove it.</li>
        </ul>
      </div>
      <div class="txt">
        <h2>LongLens checks every story before your customers read it</h2>
        <ul>
          <li><strong>Why it matters</strong>: most stories carry one line on why they matter to your customers, so the issue is never a link dump.</li>
          <li><strong>No repeats</strong>: a story they have already seen stays out until something changes, then comes back marked as an update.</li>
          <li><strong>Names and figures</strong> are checked against the original story.</li>
          <li><strong>Every link is tried</strong> before the issue goes out. A story whose only link is dead is left out, and the last line says how many links were checked and how many were dead.</li>
        </ul>
      </div>
    </div>

    <div class="feat">
      <div class="txt">
        <h2>On your desk when you sit down</h2>
        <p>LongLens arrives on the days and at the time you pick, in your time zone. Daily for a fast-moving trade, weekly for everyone else.</p>
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
      <div class="card"><h3>By hand</h3><p>Read the trade press every morning and write it up yourself. Full control. It costs the hours you do not have, and it dies the first busy week.</p></div>
      <div class="card"><h3>A newsletter platform</h3><p>Great at sending and at growing a list. No idea what to say. You still find the news and write every word.</p></div>
      <div class="card"><h3>A personal AI summary</h3><p>Fast, often free, and fine for keeping yourself informed. Written for you alone. Nobody else reads it, nobody learns what you know, and your name is nowhere on it.</p></div>
    </div>
    <p class="k">LongLens tells you why today's news matters to your customers, ready to send as text, audio, video or slides. You keep the name, the last word and the customers.</p>
    <div class="notfor"><h3>What LongLens does not do</h3><ul>
      <li><strong>Write your own company news.</strong> LongLens works from what the trade press, the forums and the videos say about your trade. Your own announcements are still yours to write.</li>
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

def plan(name, price, per, outcome, items, cta_label, cta_href, lead=False):
    lis = "".join(
        f'<li class="plan-coming">{coming(i[7:].strip())}</li>' if i.startswith("Coming:") else f"<li>{i}</li>"
        for i in items
    )
    cls = "btn btn-a" if lead else "btn btn-b"
    per_html = f" <small>{per}</small>" if per else ""
    return (f'<div class="plan{" lead" if lead else ""}"><h2>{name}</h2>'
            f'<p class="plan-price">{price}{per_html}</p><p class="plan-outcome">{outcome}</p>'
            f'<ul>{lis}</ul><a class="{cls}" href="{html.escape(cta_href)}">{cta_label}</a></div>')


PLANS = "".join([
    plan("Free", "$0", "", "Know what changed in your trade before your first coffee.",
         ["Everything under Every plan today",
          "Coming: a weekly summary as a letter, audio and video"],
         "Get my free invite", mailto("LongLens Free invite")),
    plan("Solo", "$19", "a month",
         "Built for the reader who takes every format, with every issue.",
         ["Everything under Every plan today",
          "Coming: the full audio conversation, video and slides with every issue",
          "Coming: the whole issue as one picture"],
         "Get my Solo invite", mailto("LongLens Solo invite")),
    plan("Business", "$95", "a month", "Be the expert your customers hear from first.",
         ["Everything under Every plan today",
          "Set up with you by Geoff, on one short call",
          "Coming: LongLens sends straight to your audience from your own address",
          "Coming: social posts for every issue",
          "Coming: your issue on Telegram"],
         "Put my name in front of my customers", "/contact/", lead=True),
])

EVERY_PLAN = f'''<div class="card" style="margin-top:14px"><h2 style="font-size:18px">Every plan today</h2>
  <ul class="list" style="margin-top:8px">
    <li>Your letter with each issue, daily or weekly, under your newsletter's name</li>
    <li>A plain-voice audio read with each issue</li>
    <li>{EXTRAS[0].upper() + EXTRAS[1:]}</li>
    <li>Change anything by replying in plain words</li>
    <li>Send each issue through the email tool you already use, or forward it</li>
    <li>Each issue posted to your Slack or Discord channel, if you add one</li>
  </ul>
  <p class="tiny">Today Free and Solo include the same. What Solo adds is tagged coming.</p>
</div>'''

PRICING = f'''<section class="hero">
  <div class="wrap">
    <span class="eyebrow">Pricing</span>
    <h1>Start free. Put your name in front of your customers for $95.</h1>
    <p class="lede">Free, Solo at $19 a month, or Business at $95 a month. Anything tagged coming is not built yet.</p>
    <div class="plans">{PLANS}</div>
    {EVERY_PLAN}
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">How paying works today</span>
      <h2>No card form. Geoff sets you up himself.</h2></div>
    <ul class="list">
      <li><strong>Invite only, for now.</strong> Geoff sets up every account himself. The invite buttons above open an email to him. {coming("Sign up on your own.")}</li>
      <li><strong>Business starts with a short call.</strong> You and Geoff pin down who your customers are and what they should hear from you first. Then he quotes the setup, before anything starts.</li>
      <li><strong>A set amount of writing each month.</strong> Every plan covers a set amount of writing a month. If you reach it, LongLens says so on your pages and picks up again next month.</li>
      <li><strong>Up to two extras a week in total</strong> on every plan: the full audio conversation, a short video or slides. Once those two are used, the plain-voice audio still comes, and the rest waits until next week.</li>
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
    <h1>One short call. Then your trade's news lands daily or weekly, under your name.</h1>
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
        <p><a href="/contact/">Email Geoff to book a call</a></p></li>
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
      <p>At the time you picked, LongLens turns the day's news in your trade into one issue with your newsletter's name on it.</p></div>
    <ol class="steps three">
      <li><h3>LongLens catches anything new</h3><p>From every website, feed, forum and channel you follow.</p></li>
      <li><h3>LongLens keeps what matters to your customers</h3><p>A story you have already had stays out, unless something changed. Then it comes back marked as an update.</p></li>
      <li><h3>Every story says why it matters</h3><p>Most stories carry a short line on why they matter to your customers, and every story links to the original.</p></li>
      <li><h3>Every link is tried first</h3><p>A story whose only link is dead is left out, and a line at the foot of the issue says how many links were checked and how many were dead.</p></li>
      <li><h3>Your copy arrives by email</h3><p>Nothing to press. Every issue is also kept on the Issues page when you sign in.</p></li>
      <li><h3>Audio, video and slides follow</h3><p>On the issue's page, once they pass their check. On extras days your copy can arrive up to a few hours later.</p></li>
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
         f"<p>Not yet. LongLens is invite only for now, and Geoff sets up every account himself. <a href=\"/contact/\">Email Geoff to book a short call</a>, or ask for a Free or Solo invite on the <a href=\"/pricing/\">pricing page</a>.</p>"),
        ("How do I sign in?",
         f"<p>With a link by email. There is no password. Type your email on the <a href=\"/sign-in/\">sign-in page</a> and a fresh link arrives, usually within a minute. Each link works once and keeps you signed in for 30 days on that device.</p>"),
    ]),
    ("What you get", [
        ("Is AI writing it?",
         "<p>Yes. LongLens writes with AI, checks names and figures against the original story, tries every link before the issue goes out, and you change anything by replying. Your name is on it, so the last word is yours.</p>"),
        ("Does LongLens make a separate video for every customer?",
         "<p>No. LongLens crafts each piece once per issue, whether ten people read it or ten thousand. So when each customer picks their own format (coming), the cost still does not grow with your list.</p>"),
        ("What if an audio, video or slides piece is missing?",
         "<p>Each week you get up to two of the full audio, the video and the slides. Once those two are used, audio still comes as the plainer spoken version. If the piece that leads your email is missing, you get the full letter with one line saying so.</p>"),
        ("Can LongLens write my own company news?",
         "<p>No. LongLens works from what the trade press, the forums and the videos say about your trade. Your own announcements are still yours to write.</p>"),
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
         "<p>Free, Solo at $19 a month, or Business at $95 a month. For Business, Geoff quotes the setup after your call, before anything starts. <a href=\"/pricing/\">Compare the plans</a>.</p>"),
        ("Who owns what LongLens makes?",
         "<p>You do. Every issue, every website you chose, every lesson you taught LongLens.</p>"),
        ("Who is behind LongLens?",
         f"<p>Geoffrey Hancock, a VFX supervisor and producer who won a VES Award for Changeling. His own morning VFX briefing, <a href=\"{DAILY}\">The VFX Supervisor Daily</a>, is crafted with LongLens.</p>"),
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
      <li><strong>Each customer picks their format</strong> {coming()}<br>Read it, Skim it, Listen, Watch, Slides or See it, from a link at the bottom of every issue they get.</li>
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
    <h1>Email Geoff for a short call. See a week of your news, under your name.</h1>
    <p class="lede">Tell Geoff who your customers are and what they should hear from you first. He reads every message himself and replies from {EMAIL} to set up a short call.</p>
    {CONTACT_BODY}
  </div>
</section>

<hr class="rule">
<section>
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">What happens next</span><h2>From your message to your first week of issues</h2></div>
    <ol class="steps three">
      <li><h3>Geoff replies</h3><p>Personally, to set up a short call. Nothing is sent to you automatically.</p></li>
      <li><h3>The call</h3><p>You pin down who your customers are and what they should hear from you first. Then Geoff quotes the setup.</p></li>
      <li><h3>Your first week</h3><p>Geoff sets LongLens up with you, and you see a week of real issues before anyone else does.</p></li>
    </ol>
    <p class="k">Before the call: <a href="{DAILY}">read this morning's VFX Supervisor Daily</a>, crafted with LongLens. That is what LongLens crafts for your trade, under your name.</p>
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
    <p class="k">Not set up yet? LongLens is invite only for now. <a href="/contact/">Email Geoff to book a short call</a>.</p>
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
    <p><a href="/">Go to the LongLens home page</a>, or <a href="/contact/">email Geoff to book a short call</a>.</p>
  </div>
</section>'''

# --------------------------------------------------------------------------------------------

PAGES = [
    # slug, title, description, body, nav-current
    ("", "LongLens: be the expert your customers hear from first",
     "Daily or weekly, LongLens turns your trade's news into a letter under your name, to read or hear, with up to two extras a week. Free, or from $19 a month.",
     HOME, ""),
    ("features", "Features | LongLens",
     "One morning of news, every way your customers take it in: read, skim, listen, watch or flip the slides, and change anything by replying in plain words.",
     FEATURES, "/features/"),
    ("pricing", "Pricing | LongLens",
     "Free, Solo at $19 a month, or Business at $95 a month. What each plan includes today, and what is coming.",
     PRICING, "/pricing/"),
    ("how-it-works", "How it works | LongLens",
     "One short call, a sign-in link by email, and your first issue the same day. Then daily or weekly, and you change anything by replying.",
     HOW, "/how-it-works/"),
    ("faq", "FAQ | LongLens",
     "Straight answers about LongLens: getting started, signing in, what you get, changing it by replying, price and ownership.",
     FAQ, "/faq/"),
    ("contact", "Book a call | LongLens",
     "Email Geoffrey Hancock for a short call and see a week of your trade's news, under your name.",
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
