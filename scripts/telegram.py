"""Parse the public Telegram channel preview without external dependencies."""
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

CHANNEL = "zexokkydev"
FEED_URL = f"https://t.me/s/{CHANNEL}"
MAX_BYTES = 2_000_000


class Element:
    def __init__(self, tag='', attrs=()):
        self.tag = tag
        self.attrs = dict(attrs)
        self.children = []

    def walk(self):
        yield self
        for child in self.children:
            if isinstance(child, Element):
                yield from child.walk()

    def text(self):
        if self.tag == 'br':
            return '\n'
        if self.tag in ('script', 'style'):
            return ''
        return ''.join(child.text() if isinstance(child, Element) else child for child in self.children)

    def has_class(self, name):
        return name in self.attrs.get('class', '').split()


class PageParser(HTMLParser):
    VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Element()
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        element = Element(tag, attrs)
        self.stack[-1].children.append(element)
        if tag not in self.VOID:
            self.stack.append(element)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def parse_posts(html):
    parser = PageParser()
    parser.feed(html)
    posts = {}
    for message in parser.root.walk():
        if not message.has_class('tgme_widget_message'):
            continue
        post_id = message.attrs.get('data-post', '')
        if not re.fullmatch(rf'{CHANNEL}/[0-9]+', post_id):
            continue
        descendants = list(message.walk())
        text = next((el.text().strip() for el in descendants if el.has_class('tgme_widget_message_text')), '')
        date = next((el.attrs.get('datetime', '') for el in descendants if el.tag == 'time'), '')
        # Media-only messages still link to the original post.
        posts[post_id] = {'id': int(post_id.split('/')[1]), 'url': f'https://t.me/{post_id}', 'text': text, 'date': date}
    return sorted(posts.values(), key=lambda post: post['id'], reverse=True)[:9]


def fetch_posts():
    request = Request(FEED_URL, headers={'User-Agent': 'Mozilla/5.0 (compatible; ZexokkySite/1.0)'})
    with urlopen(request, timeout=12) as response:
        final_url = urlsplit(response.url)
        if final_url.scheme != 'https' or final_url.hostname != 't.me':
            raise ValueError('Unexpected Telegram destination')
        payload = response.read(MAX_BYTES + 1)
        if len(payload) > MAX_BYTES:
            raise ValueError('Telegram response too large')
    posts = parse_posts(payload.decode('utf-8'))
    if not posts:
        raise ValueError('Public channel feed is empty or unavailable')
    return posts


