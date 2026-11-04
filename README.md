# getlonglens.com

The LongLens product website, served by GitHub Pages from the root of `main` (custom domain in
`CNAME`).

Plain HTML and one stylesheet (`assets/site.css`), no external scripts, no tracking. All copy
lives in `build.py`; edit it there, run `python3 build.py`, and commit the generated pages
(`index.html`, `<page>/index.html`, `404.html`). `build.py` also writes `preview.html`, every page
in one self-contained file for review (git-ignored, never published).

The contact page uses email until the app's inquiry endpoint accepts this origin; then set
`FORM_LIVE = True` in `build.py` and rebuild.
