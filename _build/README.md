# Build

Static site generated from the Squarespace export.

    python3 _build/build.py _build/export.xml . _build/style.css

`_build/style.css` is the source of the deployed `/style.css`.
Every published URL matches the old Squarespace URL; `_redirects` covers
retired tag and category paths.
