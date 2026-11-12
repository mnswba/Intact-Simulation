/* Finished Work: local, progressively enhanced category and text filters. */
(() => {
  'use strict';
  const initialize = () => {
    document.querySelectorAll('[data-showcase]').forEach((root) => {
      if (root.dataset.showcaseReady) return;
      root.dataset.showcaseReady = 'true';
      const cards = Array.from(root.querySelectorAll('[data-showcase-item]'));
      const filters = Array.from(root.querySelectorAll('[data-showcase-category]'));
      const search = root.querySelector('[data-showcase-search]');
      const results = root.querySelector('[data-showcase-results]');
      const empty = root.querySelector('[data-showcase-empty]');
      let category = 'all';
      const normalize = (text) => text.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase();
      const searchable = new Map(cards.map((card) => [card, normalize(card.dataset.search || '')]));
      const update = () => {
        const terms = normalize(search ? search.value.trim() : '').split(/\s+/).filter(Boolean);
        let visible = 0;
        cards.forEach((card) => {
          const matches = (category === 'all' || card.dataset.category === category)
            && terms.every((term) => searchable.get(card).includes(term));
          card.hidden = !matches;
          if (matches) visible += 1;
        });
        filters.forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.showcaseCategory === category)));
        if (results) results.textContent = `Showing ${visible} of ${cards.length} models${category === 'all' ? '' : ` · ${category}`}`;
        if (empty) empty.hidden = visible !== 0;
      };
      filters.forEach((button) => button.addEventListener('click', () => {
        category = button.dataset.showcaseCategory;
        update();
      }));
      if (search) search.addEventListener('input', update);
      root.querySelectorAll('[data-showcase-reset]').forEach((button) => button.addEventListener('click', () => {
        category = 'all';
        if (search) search.value = '';
        update();
        if (search) search.focus();
      }));
      root.querySelectorAll('[data-copy-prompt]').forEach(button=>button.addEventListener('click',async()=>{const text=button.closest('.showcase-prompt').querySelector('[data-design-prompt]').textContent;try{await navigator.clipboard.writeText(text);button.textContent='Copied';}catch{button.textContent='Select the prompt text to copy';}}));
      update();
    });
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialize, { once: true });
  else initialize();
})();
