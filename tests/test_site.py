import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from telegram import parse_posts
from update_feed import main, save_feed
from build import build, PUBLIC

PAGE = '''<div class="tgme_widget_message_wrap"><div class="tgme_widget_message js-widget_message" data-post="zexokkydev/12"><div class="tgme_widget_message_text js-message_text" dir="auto">Первый <b>пост</b><br>Код &amp; системы <a href="https://example.com">ссылка</a></div><time datetime="2026-11-03T10:00:00+00:00">13:00</time></div></div><div class="tgme_widget_message" data-post="zexokkydev/13"><div class="tgme_widget_message_photo_wrap"></div><time datetime="2026-11-03T11:00:00+00:00"></time></div><div class="tgme_widget_message" data-post="other/99">Other channel</div>'''


class FeedTests(unittest.TestCase):
    def test_public_feed_text_dates_media_and_channel_filter(self):
        posts = parse_posts(PAGE)
        self.assertEqual([post['id'] for post in posts], [12, 13])
        self.assertEqual(posts[0]['text'], 'Первый пост\nКод & системы ссылка')
        self.assertEqual(posts[0]['url'], 'https://t.me/zexokkydev/12')
        self.assertEqual(posts[1]['text'], '')
        self.assertEqual(posts[0]['date'], '2026-11-03T10:00:00+00:00')

    def test_deduplication_and_limit(self):
        html = ''.join(f'<div class="tgme_widget_message" data-post="zexokkydev/{i}"></div>' for i in range(15))
        posts = parse_posts(html + html)
        self.assertEqual(len(posts), 9)
        self.assertEqual([post['id'] for post in posts], list(range(6, 15)))

    def test_save_and_empty_feed_protection(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'feed.json'
            save_feed(parse_posts(PAGE), target)
            saved = target.read_bytes()
            self.assertEqual(len(json.loads(saved)['posts']), 2)
            with self.assertRaises(ValueError):
                save_feed([], target)
            self.assertEqual(target.read_bytes(), saved)
            self.assertEqual([p.name for p in Path(directory).iterdir()], ['feed.json'])

    def test_failed_refresh_keeps_existing_file_and_reports_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'feed.json'
            target.write_text('{"posts": [{"id": 1}]}')
            previous = target.read_bytes()
            with patch('update_feed.ROOT', Path(directory)), patch('update_feed.fetch_posts', side_effect=OSError('offline')):
                self.assertEqual(main(), 1)
            self.assertEqual(target.read_bytes(), previous)

    def test_successful_refresh(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch('update_feed.ROOT', Path(directory)), patch('update_feed.fetch_posts', return_value=parse_posts(PAGE)):
                self.assertEqual(main(), 0)
            payload = json.loads((Path(directory) / 'feed.json').read_text())
            self.assertEqual(len(payload['posts']), 2)
            self.assertTrue(payload['updated_at'])

    def test_build_contains_only_public_files_and_no_runtime_api(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'site'
            build(target)
            self.assertEqual(set(p.name for p in target.iterdir()), set(PUBLIC) | {'assets', '.nojekyll'})
            self.assertTrue((target / 'assets/favicon.svg').exists())
            self.assertNotIn('api/telegram', (target / 'app.js').read_text())
            self.assertIn("fetch('feed.json'", (target / 'app.js').read_text())


if __name__ == '__main__':
    unittest.main()
