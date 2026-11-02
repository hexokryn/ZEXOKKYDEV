const posts = document.getElementById('posts');
const feedStatus = document.getElementById('feed-status');

function element(tag, text) {
  const el = document.createElement(tag);
  el.textContent = text;
  return el;
}

function renderPost(post) {
  if (!post || typeof post !== 'object') return null;
  let url;
  try { url = new URL(post.url); } catch { return null; }
  if (url.protocol !== 'https:' || url.hostname !== 't.me' || url.username || url.password || !/^\/zexokkydev\/\d+$/.test(url.pathname)) return null;
  const card = document.createElement('article');
  card.className = 'post';
  const date = new Date(post.date);
  if (!Number.isNaN(date.getTime())) {
    const time = element('time', new Intl.DateTimeFormat('ru', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'Europe/Moscow' }).format(date));
    time.dateTime = post.date;
    card.append(time);
  }
  const text = typeof post.text === 'string' ? post.text : '';
  card.append(element('p', text ? (text.length > 900 ? `${text.slice(0, 900)}…` : text) : 'Медиа-публикация'));
  const link = element('a', 'Читать в Telegram');
  const arrow = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  arrow.setAttribute('class', 'arrow');
  arrow.setAttribute('viewBox', '0 0 24 24');
  arrow.setAttribute('aria-hidden', 'true');
  const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  path.setAttribute('d', 'M5 19 19 5M5 5h14v14');
  arrow.append(path);
  link.append(' ', arrow);
  link.href = url.href;
  link.target = '_blank';
  link.rel = 'noopener noreferrer';
  card.append(link);
  return card;
}

async function loadPosts() {
  try {
    const response = await fetch('feed.json', { cache: 'no-cache', signal: AbortSignal.timeout(12000) });
    if (!response.ok) throw new Error('Feed unavailable');
    const feed = await response.json();
    if (!Array.isArray(feed.posts)) throw new Error('Invalid feed');
    const cards = feed.posts.slice(0, 9).map(renderPost).filter(Boolean);
    if (!cards.length) throw new Error('No posts');
    posts.replaceChildren(...cards);
    document.getElementById('feed-empty').hidden = true;
    const updated = new Date(feed.updated_at);
    const stale = Number.isNaN(updated.getTime()) || Date.now() - updated.getTime() > 2 * 3600000;
    feedStatus.textContent = stale ? 'Архив публикаций · свежие записи в канале' : '';
  } catch {
    if (!posts.children.length) {
      document.getElementById('feed-empty').hidden = false;
      feedStatus.textContent = '';
    }
  } finally {
    posts.setAttribute('aria-busy', 'false');
  }
}

async function loadProfile() {
  try {
    const response = await fetch('content.json');
    if (!response.ok) return;
    const profile = await response.json();
    for (const [key, id] of [['name', 'name'], ['alias', 'alias'], ['intro', 'intro-text'], ['about', 'about-text']]) {
      if (typeof profile[key] === 'string') document.getElementById(id).textContent = profile[key] + (key === 'name' ? '.' : '');
    }
    if (Array.isArray(profile.topics)) {
      document.getElementById('topics').replaceChildren(...profile.topics.filter(topic => typeof topic === 'string').map(topic => element('li', topic)));
    }
  } catch { /* Keep the built-in profile. */ }
}

document.getElementById('copy-handle').addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText('@zexokkydev');
    document.getElementById('copy-status').textContent = 'Скопировано';
  } catch {
    document.getElementById('copy-status').textContent = '@zexokkydev';
  }
});
document.getElementById('year').textContent = new Date().getFullYear();
loadProfile();
loadPosts();
setInterval(() => { if (!document.hidden) loadPosts(); }, 300000);
