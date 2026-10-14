# Build

Static site generated from the Squarespace export.

    python3 _build/build.py _build/export.xml . _build/style.css
    python3 _build/favicon.py .

`_build/style.css` is the source of the deployed `/style.css`.
Every published URL matches the old Squarespace URL; `_redirects` covers
retired tag and category paths and proxies `/api/reissues` to City Pop Wiki.

Retired Squarespace URLs live in `DEAD` (old links, rewritten in post bodies
and 301'd) and `RETIRED` (duplicate pages, never built, force-301'd) in
`build.py`. `netlify/edge-functions/archive-paths.ts` 301s mixed-case
category/tag URLs, which `_redirects` can't match.
