"""Regenerate the checked-in PDF with Python and weasyprint==66.0."""
from pathlib import Path
import shutil
from weasyprint import HTML

root = Path(__file__).resolve().parent.parent
source = root / '_build' / 'media-kit'
# Resolve local images for offline rendering, while keeping PDF links public.
markup = (source / 'index.html').read_text().replace(
    'src="/img/', 'src="' + root.as_uri() + '/img/')
HTML(string=markup, base_url='https://vanpaugam.com/').write_pdf(
    source / 'van-paugam-media-kit.pdf')
public = root / 'media-kit'
public.mkdir(exist_ok=True)
for name in ('index.html', 'van-paugam-media-kit.pdf'):
    shutil.copy(source / name, public / name)
