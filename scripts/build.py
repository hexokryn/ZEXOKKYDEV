"""Stage only public files for GitHub Pages; no application source or tests."""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ['index.html', 'styles.css', 'app.js', 'content.json', 'feed.json']


def build(destination=ROOT / '_site'):
    destination.mkdir(parents=True, exist_ok=True)
    for filename in PUBLIC:
        shutil.copyfile(ROOT / filename, destination / filename)
    shutil.copytree(ROOT / 'assets', destination / 'assets', dirs_exist_ok=True)
    (destination / '.nojekyll').touch()


if __name__ == '__main__':
    build()
