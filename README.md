# getlonglens.com

The LongLens product website, served by GitHub Pages from the root of `main` (custom domain in
`CNAME`).

Plain HTML and one stylesheet (`assets/site.css`), no external scripts, no tracking. All copy
lives in `build.py`; edit it there, run `python3 build.py`, and commit the generated pages
(`index.html`, `<page>/index.html`, `404.html`). `build.py` also writes `preview.html`, every page
in one self-contained file for review (git-ignored, never published).

The contact page posts a form to the app's inquiry endpoint (`FORM_LIVE = True` in `build.py`),
with an email link as the fallback. Set it to False to fall back to email only.

## The sample form ("see one for your own business")

Under the sample issues on the home page, a form posts a website address to the app's
`POST /hooks/preview` (self-serve preview, app branch `preview-slices`). It is built ONLY when
`TURNSTILE_SITEKEY` in `build.py` holds the real public site key of the Cloudflare Turnstile
widget (action `preview`, hostname getlonglens.com). While it is empty, the form, the Turnstile
script and the privacy page's sample section are left out entirely, so this can be on `main`
before the app's routes are live.

Before setting the key: the app's edge routes `preview-hook`, `sample`, `sample-fix` and
`sample-pilot` must be published, and the app must have `NL_TURNSTILE_SECRET`,
`NL_PREVIEW_ORIGINS` (including `https://getlonglens.com`) and `NL_TURNSTILE_HOSTNAMES`
(default `thevfxsupervisor.com,getlonglens.com`; an empty value refuses every visitor).

Local test only (never commit its output). The app then needs Cloudflare's test secret in
`NL_TURNSTILE_SECRET`, `NL_TURNSTILE_ALLOW_TEST_KEYS=1`, and the local site's origin (for example
`http://127.0.0.1:8766`) in `NL_PREVIEW_ORIGINS`, all set in the shell for that run only:

    LONGLENS_LOCAL_TEST=1 LONGLENS_OUT=/some/folder/outside/the/repo \
    LONGLENS_APP=http://127.0.0.1:8765 LONGLENS_TURNSTILE_SITEKEY=1x00000000000000000000AA \
    python3 build.py

Cloudflare's test site keys are refused by a normal build, and a local test build refuses to
write inside this repo.
