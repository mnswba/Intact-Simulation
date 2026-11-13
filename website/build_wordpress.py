"""Build local previews and reviewable WordPress payloads; never authenticates."""
from pathlib import Path
import base64
import html
import json
import re
import runpy

ROOT = Path(__file__).parent
SITE = ROOT / 'site'
OUT = ROOT / 'wordpress'
OUT.mkdir(exist_ok=True)
SITE.mkdir(exist_ok=True)
ORIGIN = 'https://www.intactsimulation.com'
CHATGPT = 'https://chatgpt.com/'
ASSET_BASE = ORIGIN + '/wp-content/uploads/2026/11/'
ASSETS = json.loads((ROOT / 'public-assets.json').read_text(encoding='utf-8'))
ARTICLES = json.loads((ROOT / 'content/articles.json').read_text(encoding='utf-8'))
VERSION = (ROOT.parent / 'VERSION').read_text().strip()
DOWNLOADS = json.loads((ROOT / 'downloads.json').read_text(encoding='utf-8'))
DOWNLOAD_URL = DOWNLOADS['url']
LOGO = ASSET_BASE + 'logo.png'
CSS = '\n'.join((ROOT / path).read_text(encoding='utf-8') for path in ('site/site.css', 'showcase.css', 'content.css'))
RESET = 'html,body{margin:0!important;padding:0!important}body{background:#fff!important}.wp-site-blocks{padding:0!important}.wp-block-post-content{max-width:none!important;margin:0!important;padding:0!important}.wp-block-post-content>*{max-width:none!important}.wp-site-blocks>header,.wp-site-blocks>footer{display:none!important}'


def image(name):
    return ASSETS.get(name + '.png', ASSET_BASE + name + '.png')


def header():
    return f'''<header class="wrap nav"><a class="brand" href="/" aria-label="Intact Simulation home"><img src="{LOGO}" width="35" height="35" alt=""><span>Intact Simulation</span></a><nav class="nav-links" aria-label="Main navigation"><a href="/architecture/">Architecture</a><a href="/finished-work/">Finished Work</a><a href="/how-to-use/">How to Use</a><a href="/articles/">Articles</a><a href="/contact/">Contact</a></nav><a class="button small" href="/getting-started/">Get Started <span class="arrow">→</span></a></header>'''


def footer():
    return f'''<footer class="wrap footer"><div class="footer-top"><div class="footer-brand"><a class="brand" href="/"><img src="{LOGO}" width="35" height="35" alt=""><span>Intact Simulation</span></a><p>Design through a conversation in ChatGPT.<br>Build locally. Inspect the geometry.<br>Verify with measured evidence.</p></div><div><h3>Learn &amp; explore</h3><ul><li><a href="/architecture/">Architecture</a></li><li><a href="/how-to-use/">How to Use</a></li><li><a href="/finished-work/">Finished Work</a></li><li><a href="/articles/">Engineering articles</a></li></ul></div><div><h3>Use Intact</h3><ul><li><a href="{CHATGPT}">Open ChatGPT ↗</a></li><li><a href="{DOWNLOAD_URL}">Download Windows v{VERSION} ↓</a></li><li><a href="/getting-started/">Install &amp; enable the plugin</a></li><li><a href="/contact/#who-we-are">Who we are</a></li><li><a href="/privacy-data/">Privacy &amp; data</a></li><li><a href="/contact/">Contact &amp; support</a></li></ul></div></div><div class="footer-bottom"><span>© 2026 Intact Simulation</span><span>DESIGN WITH INTENT. VERIFY WITH EVIDENCE.</span><span>Developed by Abdul Samad · URDT</span></div></footer>'''


def cta():
    return f'''<div class="wrap"><section class="cta"><div><h2>Install once.<br>Design through conversation.</h2><p>Download Intact v{VERSION} for Windows. Install privately in Codex with your own account; CAD runs on your computer.</p><a class="text-link" style="color:#d7eee7!important;margin-top:15px" href="/getting-started/">Follow the installation procedure →</a></div><a class="button" href="{DOWNLOAD_URL}">Download Windows ZIP <span class="arrow">↓</span></a></section></div>'''


def wrap(body):
    return '<!-- wp:html --><style>' + RESET + CSS + '</style><div class="intact-site">' + header() + body + footer() + '</div><!-- /wp:html -->'


def pagehero(eyebrow, title, sub):
    return f'<section class="wrap page-hero"><span class="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{sub}</p></section>'


def articlecard(article):
    return f'''<article class="article-card"><div class="article-meta"><span>{html.escape(article['eyebrow']).upper()}</span><span>· {article['reading_minutes']} MIN READ</span></div><h3><a href="/articles/{article['slug']}/">{html.escape(article['title'])}</a></h3><p>{html.escape(article['summary'])}</p><a class="text-link" href="/articles/{article['slug']}/">Read the guide <span>↗</span></a></article>'''


def content(name):
    result = (ROOT / 'content' / (name + '.html')).read_text(encoding='utf-8')
    replacements = {'VERSION': DOWNLOADS['version'], 'DOWNLOAD_URL': DOWNLOAD_URL, 'GITHUB_URL': DOWNLOADS['github_url'], 'RELEASE_URL': DOWNLOADS['release_url'], 'PROCEDURE_URL': DOWNLOADS['procedure_url'], 'FILENAME': DOWNLOADS['filename'], 'SIZE': DOWNLOADS['size_label'], 'PLATFORM': DOWNLOADS['platform'], 'SHA256': DOWNLOADS['sha256']}
    for key, value in replacements.items():
        result = result.replace('{{WINDOWS_' + key + '}}', html.escape(value, quote=True))
    return result


def guide(body, label='INTACT SIMULATION', extra=''):
    return f'<main class="wrap article-layout"><aside class="article-sidebar"><strong>{label}</strong><span>v{VERSION}<br>CHATGPT + LOCAL CAD</span><a href="{CHATGPT}">Open ChatGPT ↗</a><a href="/getting-started/">Plugin setup →</a>{extra}</aside><article class="prose">{body}</article></main>'


# The browser examples remain available inside Finished Work and existing links.
models = [
    ('flange', '01 · NATIVE SOLID', 'Six-hole flange', 'A dimensioned part with a concentric bore and a circular hole pattern.', '80 × 80 × 8 mm'),
    ('enclosure', '02 · NATIVE ASSEMBLY', 'Electronics enclosure', 'Separate base and lid. Inspect their interfaces and assembled placement.', '2 COMPONENTS'),
    ('gyroid', '03 · SAMPLED TPMS', 'A gyroid, made tangible', 'Section a periodic structure and understand its mesh representation.', '24 mm ENVELOPE'),
]
modelcards = ''.join(f'''<a class="model-card" href="/demo/?model={name}"><div class="model-image"><img src="{image(name)}" alt="{title} rendered from actual Intact geometry" loading="lazy"><span class="tag">{tag}</span></div><div class="model-copy"><h3>{title}</h3><p>{desc}</p><div class="model-bottom"><span>{dim}</span><strong>Inspect model ↗</strong></div></div></a>''' for name, tag, title, desc, dim in models)
workflow = ''.join(f'<div class="step"><span class="number">0{i}</span><h3>{title}</h3><p>{text}</p></div>' for i, (title, text) in enumerate([
    ('Describe with intent', 'Tell ChatGPT the purpose, dimensions, interfaces and acceptance criteria. Resolve critical missing inputs.'),
    ('Build real geometry', 'Intact constructs native CAD or supported sampled structures in the isolated local runtime.'),
    ('Audit and inspect', 'Check the geometry, native exports and saved requirements. Read failed and unverified criteria.'),
    ('Refine with evidence', 'Select geometry, compare parameter previews and run supported studies with defined physical assumptions.'),
], 1))
home = f'''<main><section class="wrap hero"><div><span class="eyebrow">INTACT SIMULATION · CAD THROUGH CHATGPT</span><h1>Your next idea,<br>in <em>three dimensions.</em></h1><p class="intro">Describe what you need in ChatGPT. Intact builds editable geometry on your computer, helps you inspect it and checks the result against measurable design intent.</p><div class="hero-actions"><a class="button primary" href="{DOWNLOAD_URL}">Download for Windows <span class="arrow">↓</span></a><a class="button" href="/getting-started/">Install the plugin <span>→</span></a></div><p class="hero-note"><span class="dot"></span>v{VERSION} · Windows x86-64 · Private local installation</p></div><div class="hero-stage"><div class="stage-heading"><span>INTACT / EXAMPLE 001</span><span>NATIVE CAD PREVIEW</span></div><iframe src="/demo/?mini=1" title="Interactive prebuilt flange example" loading="eager" allow="fullscreen"></iframe><div class="stamp"><span>FLANGE ENVELOPE</span><strong>Ø80 × 8 mm</strong><span>6 × Ø6 · PCD Ø60</span></div><div class="stage-footer"><span>DRAG TO ORBIT · SCROLL TO ZOOM</span><a href="/finished-work/">FINISHED WORK ↗</a></div></div></section><div class="wrap capability-line"><span>FROM DESIGN INTENT TO INSPECTABLE OUTPUT</span><span>PARAMETRIC CAD</span><span>GEOMETRY-AWARE EDITS</span><span>GEOMETRY AUDITS</span><span>SUPPORTED 3D ANALYSIS</span></div><section class="soft"><div class="wrap section"><div class="section-head"><div><span class="eyebrow">THE DESIGN LOOP</span><h2>A conversation starts it.<br>Evidence moves it forward.</h2></div><a class="text-link" href="/architecture/">Explore the architecture ↗</a></div><div class="workflow">{workflow}</div></div></section><section class="wrap section"><div class="section-head"><div><span class="eyebrow">ACTUAL GEOMETRY · ORIGINAL CONCEPTS</span><h2>Look closer.<br>There is a model behind it.</h2></div><p>Inspect prebuilt examples in your browser, then use the plugin for your own geometry. Explore 50 original concepts in Finished Work.</p></div><div class="model-grid">{modelcards}</div><p style="margin-top:28px"><a class="text-link" href="/finished-work/">Explore all Finished Work ↗</a></p></section><section class="soft"><div class="wrap section benchmark"><div><span class="eyebrow">AUDITOR · VERIFICATION · VALIDATION</span><h2>Check the geometry.<br>Question the assumptions.</h2><p>The audit inspects native solids, sampled meshes and exported files. Saved requirements check supported dimensions, holes, placements and clearances. Missing evidence remains unverified.</p><p>For analysis, inspect material, boundary conditions, mesh, residuals, conservation and refinement. The recorded compression benchmark offers a bounded reference.</p><a class="text-link" href="/architecture/#verification">Inside the verification chain ↗</a></div><div class="formula"><span class="eyebrow">RECORDED COMPRESSION BENCHMARK</span><div class="equation">u = FL / EA = 0.020 mm</div><dl><dt>Block dimensions</dt><dd>10 × 10 × 20 mm</dd><dt>Applied top load</dt><dd>−1000 N · Z</dd><dt>Elastic modulus / Poisson ratio</dt><dd>10 GPa / 0</dd><dt>Bottom support reaction</dt><dd>+1000 N · Z</dd></dl><p style="font-size:11px;margin:20px 0 0">One verified numerical benchmark; not certification of an arbitrary design.</p><a class="text-link" href="/articles/reproducible-1000-newton-compression-benchmark/">Read the worked example ↗</a></div></div></section><section class="wrap section"><div class="section-head"><div><span class="eyebrow">ENGINEERING KNOWLEDGE</span><h2>Build understanding,<br>alongside the model.</h2></div><a class="text-link" href="/articles/">All engineering articles ↗</a></div><div class="article-grid">{''.join(articlecard(a) for a in ARTICLES[-4:-1])}</div></section><section class="section">{cta()}</section></main>'''

pages = {'home': {'title': 'Intact Simulation — CAD through ChatGPT', 'body': wrap(home)}}
pages['architecture'] = {'title': 'Architecture — Intact Simulation', 'body': wrap(pagehero('HOW INTACT WORKS', 'A conversation.<br>A complete engineering pipeline.', 'Explore the local CAD architecture, open-source engines, modeling flow and evidence behind every accepted revision.') + guide(content('architecture'), 'SYSTEM ARCHITECTURE') + cta())}
pages['terms-of-service'] = {'title': 'Terms of Service', 'body': wrap(pagehero('PRODUCT TERMS', 'Terms of Service', 'Effective 13 November 2026 · Service provider: Abdul Samad') + guide(content('terms-of-service'), 'TERMS OF SERVICE', '<a href="/privacy-data/">Privacy &amp; data →</a>'))}

# Generate the shortcut reference from the same registry used by the viewer.
shortcut_source = (ROOT.parent / 'scripts/viewer/shortcuts.mjs').read_text(encoding='utf-8')
shortcut_rows = ''.join(f'<tr><td><kbd>{html.escape(label)}</kbd></td><td>{html.escape(name)}</td></tr>' for label, name in re.findall(r"label:'([^']+)',name:'([^']+)'", shortcut_source))
how_to_use = content('how-to-use').replace('{{SHORTCUT_ROWS}}', shortcut_rows)
pages['how-to-use'] = {'title': 'How to Use — Intact Simulation', 'body': wrap(pagehero('THE CHATGPT PLUGIN TUTORIAL', 'From your first prompt<br>to a design you can inspect.', 'Install, create, select, edit, review, simulate and export. A practical guide to Intact’s tools and keyboard shortcuts.') + guide(how_to_use, 'USER TUTORIAL') + cta())}
# Keep the existing URL and page identity useful for bookmarks and search engines.
pages['how-it-works'] = dict(pages['how-to-use'])

pages['articles'] = {'title': 'Engineering Articles — Intact Simulation', 'body': wrap(pagehero('KNOWLEDGE FOR THE NEXT ITERATION', 'Better briefs.<br>Stronger engineering judgement.', 'Practical guides to ChatGPT-assisted CAD, geometry verification, design alternatives, sampled structures and numerical evidence.') + '<main class="wrap section"><div class="article-grid">' + ''.join(articlecard(a) for a in ARTICLES) + '</div></main>' + cta())}
for article in ARTICLES:
    body = pagehero(html.escape(article['eyebrow']), html.escape(article['title']), html.escape(article['summary']))
    body += guide(article['content_html'], 'ENGINEERING GUIDE', f'<span>{article["reading_minutes"]} MIN READ</span><a href="/articles/">← All articles</a>')
    pages['article-' + article['slug']] = {'title': article['title'], 'slug': article['slug'], 'parent_slug': 'articles', 'body': wrap(body + cta())}

pages['getting-started'] = {'title': 'Download & Install Intact Simulation for Windows', 'body': wrap(pagehero('WINDOWS LOCAL EDITION · v' + VERSION, 'Your computer.<br>Your CAD tools.', 'Download the current Windows plugin and install it privately in Codex. Use your own ChatGPT account; no publisher-hosted CAD backend is required.') + content('browser-cad-banner') + guide(content('getting-started'), 'PLUGIN SETUP') + cta())}
pages['contact'] = {'title': 'Who We Are & Contact — Intact Simulation', 'body': wrap(pagehero('URDT · DESIGN & ENGINEERING', 'Meet the people<br>behind Intact Simulation.', 'Company background, the developer and a direct route to technical help and collaboration.') + content('contact') + cta())}
privacy = '''<h2>The public website and model viewer</h2><p>Finished Work and the embedded browser examples load prebuilt public geometry and recorded solver data. Orbiting, sectioning, recoloring and visual deformation happen in your browser. The example viewer does not perform new custom AI CAD generation or a new analysis of your design.</p><h2>WordPress hosting</h2><p>WordPress and the hosting provider may process operational data such as IP addresses, requested URLs, browser details and security logs. Retention depends on the hosting configuration. This description is not a complete audit of the provider or every WordPress plugin.</p><h2>ChatGPT and the local plugin</h2><p>Use your own account. Local projects and revisions are stored in the configured Intact state directory. The selected request and relevant model context are sent to the AI client/provider; this may include geometry facts, CAD programs and reference attachments. Provider account, availability, usage and privacy terms apply. Local CAD execution does not make the AI conversation offline.</p><h2>External links and downloads</h2><p>ChatGPT sign-in is handled by OpenAI. The Windows plugin download is delivered through the project’s versioned GitHub release; the website links to that same file. Dependency setup downloads runtimes from their upstream services. Those services have their own privacy practices. Example design packages are public files. Display changes do not alter native downloads.</p><h2>Contact</h2><p>Enquiries go to the listed Intact or URDT email address. Do not include credentials or confidential project material without an agreed channel. For information you have sent directly, <a href="/contact/">contact the recipient</a>.</p>'''
pages['privacy-data'] = {'title': 'Privacy & Data — Intact Simulation', 'body': wrap(pagehero('CLEAR DATA BOUNDARIES', 'Know where your<br>information goes.', 'The public examples, local CAD runtime, your ChatGPT conversation and external services each have a distinct role.') + guide(privacy, 'DATA FLOW'))}

showcase = json.loads((ROOT / 'content/showcase.json').read_text(encoding='utf-8'))
render_showcase = runpy.run_path(str(ROOT / 'showcase-page.py'))['render_showcase']
filter_bytes = base64.b64encode((ROOT / 'showcase-filter.js').read_bytes()).decode()
filter_script = '<script>(function(){var s=document.createElement("script");s.textContent=new TextDecoder().decode(Uint8Array.from(atob("' + filter_bytes + '"),function(c){return c.charCodeAt(0)}));document.body.appendChild(s)})();</script>'
pages['finished-work'] = {'title': 'Finished Work — Intact Simulation', 'body': wrap(render_showcase(showcase)).replace('<!-- /wp:html -->', filter_script + '<!-- /wp:html -->')}

for key, page in pages.items():
    slug = page.get('slug', key)
    page['slug'] = slug
    payload = {'title': page['title'], 'slug': slug, 'content': page['body'], 'status': 'draft', 'template': 'blank', 'comment_status': 'closed', 'ping_status': 'closed'}
    (OUT / (key + '.json')).write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
    local = 'articles/' + slug if page.get('parent_slug') else '' if key == 'home' else slug
    folder = SITE / local
    folder.mkdir(parents=True, exist_ok=True)
    preview = page['body'].replace(LOGO, '/assets/intact-logo.png')
    for name in ('flange', 'enclosure', 'gyroid'):
        preview = preview.replace(image(name), '/assets/' + name + '.png')
    canonical = ORIGIN + ('/how-to-use/' if key == 'how-it-works' else '/' + local + '/' if local else '/')
    (folder / 'index.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="canonical" href="' + canonical + '"><title>' + html.escape(page['title']) + '</title></head><body>' + preview + '</body></html>', encoding='utf-8')

# Preserve the interactive example implementation and its existing public URL.
demo = (SITE / 'demo/intact-demo.html').read_text(encoding='utf-8')
demo_body = re.search(r'<body>(.*)</body>', demo, re.S)[1]
demo_body = re.sub(r'<script.*?</script>', '', demo_body, flags=re.S)
zip_urls = {name: ASSETS.get(name, ASSET_BASE + name) for name in ['intact-flange.zip', 'intact-enclosure.zip', 'intact-gyroid.zip', 'intact-benchmark.zip'] + [item['package_filename'] for item in showcase]}
script = base64.b64encode((SITE / 'demo/intact-demo.js').read_bytes()).decode()
bootstrap = '(function(){var a=Uint8Array.from(atob("' + script + '"),function(c){return c.charCodeAt(0)}),s=document.createElement("script");s.textContent=new TextDecoder().decode(a);document.body.appendChild(s)})();'
demo_content = '<!-- wp:html --><style>' + RESET + (SITE / 'demo/intact-demo.css').read_text(encoding='utf-8') + '</style>' + demo_body + '<script>window.INTACT_DEMO_ASSETS=' + json.dumps(zip_urls) + ';</script><script>' + bootstrap + '</script><!-- /wp:html -->'
(OUT / 'demo.json').write_text(json.dumps({'title': 'Interactive CAD Examples — Intact Simulation', 'slug': 'demo', 'content': demo_content, 'status': 'draft', 'template': 'blank', 'comment_status': 'closed', 'ping_status': 'closed'}, ensure_ascii=False), encoding='utf-8')
(SITE / 'demo/index.html').write_text(demo, encoding='utf-8')
(OUT / 'page-index.json').write_text(json.dumps({key: {'title': page['title'], 'slug': page['slug'], 'parent_slug': page.get('parent_slug')} for key, page in pages.items()}, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'Built {len(pages)} content pages plus the preserved interactive examples. No credentials in generated content.')
