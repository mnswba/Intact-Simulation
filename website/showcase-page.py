"""Body-only Finished Work gallery. The site builder supplies its shared shell."""
from html import escape
from urllib.parse import quote, urlsplit
import math

CATEGORIES = ('Robotics', 'Engine & powertrain', 'Product concepts', 'TPMS')


def _text(value):
    return escape(str(value), quote=True)


def _url(value):
    value = str(value).strip()
    parsed = urlsplit(value)
    if parsed.scheme in ('https', 'http') or (not parsed.scheme and value.startswith('/') and not value.startswith('//')):
        return _text(value)
    raise ValueError('Showcase links must use HTTP(S) or an absolute site path.')


def _number(value):
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError('Showcase measurements must be finite and nonnegative.')
    return f'{value:,.1f}'.removesuffix('.0')


def render_showcase(items):
    """Render catalog entries without adding a header, footer, style or script."""
    items = list(items)
    count = len(items)
    category_names=tuple(dict.fromkeys(item['category'] for item in items))
    categories = ''.join(
        f'<button class="showcase-filter" type="button" data-showcase-category="{_text(category)}" aria-pressed="false">'
        f'{_text(category)}<span class="showcase-filter-count">{sum(item["category"] == category for item in items)}</span></button>'
        for category in category_names
    )
    cards = []
    for index, item in enumerate(items, 1):
        title = _text(item['title'])
        category = _text(item['category'])
        slug = _text(item['slug'])
        native = item['representation'] == 'native'
        representation = 'Native CAD' if native else 'Sampled mesh'
        dimensions = ' × '.join(_number(v) for v in item['dimensions_mm']) + ' mm'
        parts = int(item['part_count'])
        model_url = '/demo/?model=' + quote(str(item['model_key']), safe='')
        search_text = _text(' '.join(str(item.get(key, '')) for key in ('title', 'category', 'summary', 'design_notes', 'design_prompt')))
        prompt=_text(item.get('design_prompt',''));prompt_note=_text(item.get('prompt_provenance',''));audit=item.get('audit');audit_note=(str(audit['export_checks'])+' export checks passed') if audit else 'Original geometry validation'
        cards.append(f'''<li class="showcase-item" data-showcase-item data-category="{category}" data-search="{search_text}">
<article class="showcase-card" aria-labelledby="showcase-title-{slug}">
<a class="showcase-image" href="{model_url}" aria-label="Inspect {title} in the model viewer">
<img src="{_url(item['thumbnail_url'])}" width="960" height="720" alt="{title}, rendered from its exported CAD geometry" loading="lazy" decoding="async">
<span class="showcase-image-index">{index:02d} / {count:02d}</span><span class="showcase-inspect">Inspect geometry <span aria-hidden="true">↗</span></span></a>
<div class="showcase-card-copy"><div class="showcase-card-meta"><span>{category}</span><span class="showcase-badge{' showcase-badge-mesh' if not native else ''}">{representation}</span></div>
<h2 id="showcase-title-{slug}"><a href="{model_url}">{title}</a></h2><p class="showcase-card-summary">{_text(item['summary'])}</p>
<dl class="showcase-measurements"><div><dt>Components</dt><dd>{parts:,}</dd></div><div><dt>Envelope · X × Y × Z</dt><dd>{dimensions}</dd></div></dl>
<p class="showcase-validation"><span aria-hidden="true"></span>Showcase concept · geometry validated</p>
<div class="showcase-card-actions"><a class="showcase-open" href="{model_url}">Open model <span aria-hidden="true">↗</span><span class="showcase-sr-only">: {title}</span></a><a class="showcase-download" href="{_url(item['package_url'])}" download>Download ZIP <span aria-hidden="true">↓</span><span class="showcase-sr-only">: {title}</span></a></div>
<details class="showcase-prompt"><summary>{"AI design prompt" if item.get("collection")=="industry30" else "Design brief (reconstructed)"}</summary><p class="showcase-prompt-note">{prompt_note}</p><pre data-design-prompt>{prompt}</pre><button type="button" data-copy-prompt>Copy prompt</button></details>
<details class="showcase-details"><summary>Design notes &amp; geometry</summary><div class="showcase-details-content"><p>{_text(item['design_notes'])}</p><dl><div><dt>Representation</dt><dd>{representation}</dd></div><div><dt>Measured volume</dt><dd>{_number(item['volume_mm3'])} mm³</dd></div></dl><p class="showcase-details-note">{audit_note}. Geometry validation covers the exported model. Mechanical function, strength and motion are unverified.</p></div></details>
</div></article></li>''')
    return f'''<main class="showcase-page" data-showcase>
<section class="wrap showcase-hero" aria-labelledby="showcase-heading"><div class="showcase-hero-copy"><span class="showcase-eyebrow">THE INTACT MODEL COLLECTION</span><h1 id="showcase-heading">Finished Work<span class="showcase-title-dot" aria-hidden="true">.</span></h1><p class="showcase-intro">Ideas with shape, detail and something to inspect. Explore original CAD concepts across robotics, aerospace, medicine, energy, manufacturing, transport and more.</p><a class="showcase-hero-link" href="#showcase-collection">Explore the collection <span aria-hidden="true">↓</span></a></div><aside class="showcase-hero-note" aria-label="About this collection"><span class="showcase-collection-number">{count:02d}</span><span class="showcase-eyebrow">ORIGINAL MODELS · {len(category_names)} INDUSTRY GROUPS</span><p>Every form has a file behind it. Orbit the geometry, inspect the components, or download a model package to explore further.</p><span class="showcase-hero-footnote">Showcase concepts. Geometry validated.<br>Engineering performance unverified.</span></aside></section>
<section class="wrap showcase-collection" id="showcase-collection" aria-label="Browse finished work"><div class="showcase-toolbar"><div class="showcase-filter-group" role="group" aria-label="Filter models by category"><button class="showcase-filter" type="button" data-showcase-category="all" aria-pressed="true">All work<span class="showcase-filter-count">{count}</span></button>{categories}</div><div class="showcase-search"><label for="showcase-search">Search the collection</label><input id="showcase-search" type="search" placeholder="Try gripper, turbine, gyroid…" autocomplete="off" data-showcase-search></div></div>
<div class="showcase-results-bar"><p class="showcase-results" data-showcase-results role="status" aria-live="polite" aria-atomic="true">Showing {count} of {count} models</p><span>INSPECT · EXPLORE · DOWNLOAD</span></div>
<ul class="showcase-grid" role="list">{''.join(cards)}</ul><div class="showcase-empty" data-showcase-empty hidden><h2>No models match this view.</h2><p>Try another search or return to the full collection.</p><button type="button" data-showcase-reset>Show all work <span aria-hidden="true">↗</span></button></div>
<noscript><p class="showcase-noscript">All models are shown. Enable JavaScript to filter or search the collection.</p></noscript>
</section><section class="wrap showcase-closing"><span class="showcase-eyebrow">FROM CONCEPT TO YOUR OWN QUESTIONS</span><h2>A closer look is the next step.</h2><p>These original studies show what an inspectable model can contain. Bring your own dimensions and design intent to the desktop plugin.</p><a class="showcase-open" href="/getting-started/">Start designing with Intact <span aria-hidden="true">↗</span></a></section></main>'''
