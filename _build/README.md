# Build

Static site generated from the Squarespace export.

    python3 _build/build.py _build/export.xml . _build/style.css

`netlify.toml` runs this generator during deployment and publishes the repository
root. `_build/style.css` is the source of the deployed `/style.css`.

Each published blog post is generated at `blog/<slug>/index.html`, including
date-based nested slugs. The canonical URLs in the pages and sitemap omit the
trailing slash. Pretty URLs processing is disabled, and the final `_redirects`
rules rewrite `/blog` and `/blog/*` to their generated HTML files with status
`200!`, avoiding an automatic directory-slash redirect. Both trailing-slash
variants resolve to the same content without redirecting between them.

Retired category, tag, and article URLs use 301 redirects before the general
blog rewrites. `/blog/rare-city-pop-vinyl-repress` redirects to
`/blog/tatsuro-yamashita-vinyl-repress-pre-order`. Missing articles still return
404; this static site does not use a homepage or single-page-app fallback.
The generator preserves the deployment configuration and regenerates the routing
rules, so subsequent deployments retain these fixes. `/api/reissues` is served
by `netlify/functions/reissues.mjs`.
