#!/usr/bin/env python3
"""Build articles from markdown drafts to HTML."""
import re
import os
import sys
from pathlib import Path

ROOT = Path("/home/user/workspace/menopausereviewed")
DRAFTS = ROOT / "_drafts"
OUT = ROOT / "articles"

HEADER = '''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title} — Menopause Reviewed</title>
    <meta name="description" content="{dek}" />
    <link rel="canonical" href="https://menopausereviewed.com/articles/{slug}.html" />
    <meta property="og:title" content="{title}" />
    <meta property="og:description" content="{dek}" />
    <meta property="og:type" content="article" />
    <meta property="og:url" content="https://menopausereviewed.com/articles/{slug}.html" />
    <meta name="twitter:card" content="summary_large_image" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,500;0,8..60,600;1,8..60,400;1,8..60,500&family=Inter:wght@400;500;600&display=swap" rel="stylesheet" />
    <link rel="stylesheet" href="/css/style.css" />
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-2ZPQBQXFKR"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', 'G-2ZPQBQXFKR');
    </script>
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "Article",
      "headline": "{title}",
      "description": "{dek}",
      "datePublished": "2026-05-09",
      "dateModified": "2026-05-09",
      "author": {{"@type": "Organization", "name": "Menopause Reviewed Editorial Team"}},
      "publisher": {{"@type": "Organization", "name": "Menopause Reviewed", "url": "https://menopausereviewed.com"}}
    }}
    </script>
  </head>
  <body>
    <header class="site-header">
      <div class="container">
        <div class="site-header__inner">
          <a href="/" class="brand">
            <svg class="brand__mark" viewBox="0 0 32 32" fill="none" aria-hidden="true">
              <circle cx="16" cy="16" r="14" stroke="currentColor" stroke-width="1.5" />
              <path d="M9 18 C9 13, 13 11, 16 14 C19 11, 23 13, 23 18 C23 22, 19 24, 16 21 C13 24, 9 22, 9 18 Z" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linejoin="round" />
            </svg>
            <span class="brand__name"><strong>Menopause</strong> <em>Reviewed</em></span>
          </a>
          <nav class="nav" aria-label="Primary">
            <a href="/symptoms.html">Symptoms</a>
            <a href="/treatments.html">Treatments</a>
            <a href="/library.html">Library</a>
            <a href="/about.html">About</a>
          </nav>
          <div class="header__actions">
            <button class="theme-toggle" data-theme-toggle aria-label="Switch to dark mode" type="button"></button>
            <button class="menu-toggle" id="menu-toggle" aria-label="Open menu" type="button">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
            </button>
          </div>
        </div>
        <nav class="mobile-nav" id="mobile-nav"><ul role="list"><li><a href="/symptoms.html">Symptoms</a></li><li><a href="/treatments.html">Treatments</a></li><li><a href="/library.html">Library</a></li><li><a href="/about.html">About</a></li></ul></nav>
      </div>
    </header>

    <main>
      <section class="article-hero">
        <div class="container container--prose">
          <p class="article-hero__category">{category}</p>
          <h1 class="article-hero__title">{title}</h1>
          <p class="article-hero__dek">{dek}</p>
          <div class="article-hero__meta">
            <span><strong>Menopause Reviewed Editorial Team</strong></span>
            <span>{read_time} min read</span>
            <span>Last reviewed {last_reviewed}</span>
          </div>
        </div>
      </section>

      <article class="prose">
'''

FOOTER = '''      </article>
    </main>
    <footer class="site-footer">
      <div class="container">
        <div class="site-footer__grid">
          <div class="footer-col"><p class="footer-col__title">Menopause Reviewed</p><p class="footer__about">An independent research hub for women navigating perimenopause and menopause. No products to sell. No agenda but the evidence.</p></div>
          <div class="footer-col"><p class="footer-col__title">Topics</p><ul role="list"><li><a href="/symptoms.html">Symptoms</a></li><li><a href="/treatments.html">Treatments</a></li><li><a href="/library.html">Library</a></li></ul></div>
          <div class="footer-col"><p class="footer-col__title">About</p><ul role="list"><li><a href="/about.html">Our methodology</a></li><li><a href="/about.html#contact">Contact</a></li><li><a href="/about.html#disclosure">Disclosures</a></li></ul></div>
          <div class="footer-col"><p class="footer-col__title">Legal</p><ul role="list"><li><a href="/privacy.html">Privacy</a></li><li><a href="/terms.html">Terms</a></li><li><a href="/about.html#medical-disclaimer">Medical disclaimer</a></li></ul></div>
        </div>
        <div class="footer__bottom"><span>© 2026 Menopause Reviewed</span><span>This site is for informational purposes only and does not constitute medical advice.</span></div>
      </div>
    </footer>
    <script src="/js/main.js" defer></script>
  </body>
</html>
'''


def parse_frontmatter(text):
    m = re.match(r'^---\n(.*?)\n---\n(.*)$', text, re.DOTALL)
    if not m:
        return {}, text
    fm_block, body = m.group(1), m.group(2)
    fm = {}
    for line in fm_block.split('\n'):
        if ':' in line:
            k, v = line.split(':', 1)
            v = v.strip()
            if v.startswith('"') and v.endswith('"'):
                v = v[1:-1]
            fm[k.strip()] = v
    return fm, body


def md_to_html(md):
    """Lightweight markdown to HTML for our specific article structure."""
    lines = md.split('\n')
    out = []
    i = 0
    in_list = None  # 'ul' or 'ol' or None
    in_blockquote = False

    def close_list():
        nonlocal in_list
        if in_list:
            out.append(f'</{in_list}>')
            in_list = None

    def close_bq():
        nonlocal in_blockquote
        if in_blockquote:
            out.append('</blockquote>')
            in_blockquote = False

    def inline(text):
        # Links [text](url)
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
        # Bold **text**
        text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
        # Italic *text* (only when not at start of line where already eaten)
        text = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'<em>\1</em>', text)
        return text

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip the H1 title (already in hero)
        if stripped.startswith('# ') and i < 3:
            i += 1
            continue

        if not stripped:
            close_list()
            close_bq()
            i += 1
            continue

        # Headings
        if stripped.startswith('### '):
            close_list(); close_bq()
            out.append(f'<h3>{inline(stripped[4:])}</h3>')
        elif stripped.startswith('## '):
            close_list(); close_bq()
            heading_text = stripped[3:]
            slug = re.sub(r'[^a-z0-9]+', '-', heading_text.lower()).strip('-')
            out.append(f'<h2 id="{slug}">{inline(heading_text)}</h2>')
        elif stripped.startswith('# '):
            close_list(); close_bq()
            out.append(f'<h1>{inline(stripped[2:])}</h1>')
        # HR
        elif stripped == '---':
            close_list(); close_bq()
            out.append('<hr />')
        # Blockquote (callout)
        elif stripped.startswith('>'):
            close_list()
            content = stripped.lstrip('>').strip()
            if not in_blockquote:
                # Detect if it starts with **Important:** or similar -> callout
                m = re.match(r'^\*\*([^*]+):\*\*\s*(.*)', content)
                if m:
                    label, rest = m.group(1), m.group(2)
                    out.append(f'<aside class="callout"><div class="callout__label">{label}</div><p>{inline(rest)}</p>')
                    in_blockquote = 'callout'
                else:
                    out.append('<blockquote>')
                    out.append(f'<p>{inline(content)}</p>')
                    in_blockquote = 'quote'
            else:
                if content:
                    out.append(f'<p>{inline(content)}</p>')
        # Unordered list
        elif re.match(r'^[-*]\s+', stripped):
            close_bq()
            if in_list != 'ul':
                close_list()
                out.append('<ul>')
                in_list = 'ul'
            content = re.sub(r'^[-*]\s+', '', stripped)
            out.append(f'<li>{inline(content)}</li>')
        # Ordered list
        elif re.match(r'^\d+\.\s+', stripped):
            close_bq()
            if in_list != 'ol':
                close_list()
                out.append('<ol>')
                in_list = 'ol'
            content = re.sub(r'^\d+\.\s+', '', stripped)
            out.append(f'<li>{inline(content)}</li>')
        else:
            # Close blockquote when leaving
            if in_blockquote == 'callout':
                # multi-paragraph in callout?  add as additional <p>
                out.append(f'<p>{inline(stripped)}</p>')
            elif in_blockquote == 'quote':
                out.append(f'<p>{inline(stripped)}</p>')
            else:
                close_list()
                # Paragraph
                # collect continuation lines
                para = [stripped]
                while i + 1 < len(lines) and lines[i+1].strip() and not re.match(r'^(#|>|\d+\.|[-*]\s|---)', lines[i+1].strip()):
                    i += 1
                    para.append(lines[i].strip())
                out.append(f'<p>{inline(" ".join(para))}</p>')
        i += 1

    close_list()
    if in_blockquote == 'callout':
        out.append('</aside>')
    elif in_blockquote == 'quote':
        out.append('</blockquote>')
    return '\n        '.join(out)


def build_article(md_path):
    text = md_path.read_text()
    fm, body = parse_frontmatter(text)
    body_html = md_to_html(body)

    # Replace the PeptidesRated funnel callout (in article 3) with a richer styled component
    # Find any blockquote-style callout that mentions peptidesrated.com and upgrade it visually.

    html = HEADER.format(
        title=fm.get('title', ''),
        dek=fm.get('dek', ''),
        slug=fm.get('slug', ''),
        category=fm.get('category', ''),
        read_time=fm.get('read_time', ''),
        last_reviewed=fm.get('last_reviewed', ''),
    ) + body_html + FOOTER

    out_path = OUT / f"{fm.get('slug')}.html"
    out_path.write_text(html)
    print(f"Built {out_path.name} ({len(body_html)} bytes body)")


def main():
    OUT.mkdir(exist_ok=True)
    for md in sorted(DRAFTS.glob('*.md')):
        build_article(md)


if __name__ == '__main__':
    main()
