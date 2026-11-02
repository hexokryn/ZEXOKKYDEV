"""Refresh the static feed; retain the last valid file if Telegram is unavailable."""
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from telegram import fetch_posts

ROOT = Path(__file__).resolve().parent.parent


def save_feed(posts, destination):
    if not posts:
        raise ValueError('No Telegram posts received')
    payload = {'updated_at': datetime.now(timezone.utc).isoformat(), 'posts': posts}
    temporary = None
    try:
        with tempfile.NamedTemporaryFile('w', dir=destination.parent, encoding='utf-8', delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        os.replace(temporary, destination)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def main():
    try:
        posts = fetch_posts()
        save_feed(posts, ROOT / 'feed.json')
    except (OSError, ValueError, UnicodeError):
        print('Telegram could not be refreshed. Keeping the previous feed.json.', file=sys.stderr)
        return 1
    print(f'Updated feed: {len(posts)} posts.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
