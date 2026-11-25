/* Τέταρτος Τοίχος: συμπεριφορά σελίδων. Το περιεχόμενο είναι ήδη στο HTML. */
(() => {
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  };
  const root = document.documentElement;

  /* Παλιοί σύνδεσμοι με # οδηγούν στη νέα σελίδα */
  const routes = (document.body.dataset.routes || '').split(' ').filter(Boolean);
  if (routes.length && location.hash.length > 1) {
    const h = decodeURIComponent(location.hash.slice(1));
    if (routes.includes(h)) { location.replace(h + '/'); return; }
  }

  /* Φώτα πλατείας */
  const lights = document.getElementById('lights');
  const setLights = on => {
    if (on) root.setAttribute('data-lights', 'on'); else root.removeAttribute('data-lights');
    lights.setAttribute('aria-pressed', on);
  };
  setLights(store.get('tt-lights') === 'on');
  lights.addEventListener('click', () => {
    const on = lights.getAttribute('aria-pressed') !== 'true';
    setLights(on); store.set('tt-lights', on ? 'on' : 'off');
  });

  /* Μέγεθος γραμμάτων και γραμμή προόδου στις κριτικές */
  const prose = document.getElementById('prose');
  if (prose) {
    const SIZES = [18, 20, 22, 24];
    let idx = Math.min(SIZES.length - 1, Math.max(0, parseInt(store.get('tt-size') ?? '1', 10) || 0));
    const minus = document.getElementById('minus'), plus = document.getElementById('plus');
    const apply = () => {
      root.style.setProperty('--read', SIZES[idx] + 'px');
      minus.disabled = idx === 0; plus.disabled = idx === SIZES.length - 1;
    };
    minus.addEventListener('click', () => { idx--; store.set('tt-size', idx); apply(); });
    plus.addEventListener('click', () => { idx++; store.set('tt-size', idx); apply(); });
    apply();

    const progress = document.getElementById('progress');
    const onScroll = () => {
      const rect = prose.getBoundingClientRect();
      const total = rect.height - window.innerHeight * 0.6;
      const done = Math.min(1, Math.max(0, (-rect.top + window.innerHeight * 0.4) / Math.max(1, total)));
      progress.style.width = (done * 100) + '%';
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);
    onScroll();
  }

  /* Αρχείο: αναζήτηση, φίλτρα, ταξινόμηση */
  const list = document.getElementById('rows');
  if (list) {
    const norm = s => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/ς/g, 'σ');
    const index = JSON.parse(document.getElementById('idx').textContent);
    const rows = [...list.children];
    const q = document.getElementById('q'), sort = document.getElementById('sort');
    const count = document.getElementById('count'), empty = document.getElementById('empty');
    const chips = [...document.querySelectorAll('.chip')];
    const filter = { tag: new URLSearchParams(location.search).get('tag'), venue: null };

    const update = () => {
      const needle = norm(q.value.trim());
      chips.forEach(c => c.setAttribute('aria-pressed', filter[c.dataset.key] === c.dataset.val));
      let shown = 0;
      rows.forEach(r => {
        const ok = (!filter.tag || r.dataset.tags.split('|').includes(filter.tag)) &&
                   (!filter.venue || r.dataset.venue === filter.venue) &&
                   (!needle || index[r.dataset.slug].includes(needle));
        r.hidden = !ok; if (ok) shown++;
      });
      const by = sort.value;
      const order = [...rows].sort((a, b) =>
        by === 'old' ? a.dataset.no - b.dataset.no :
        by === 'rating' ? (b.dataset.rating - a.dataset.rating) || (b.dataset.no - a.dataset.no) :
        b.dataset.no - a.dataset.no);
      order.forEach(r => list.appendChild(r));
      count.textContent = shown === 1 ? '1 σημείωση' : shown + ' σημειώσεις';
      empty.hidden = shown > 0;
    };
    q.addEventListener('input', update);
    sort.addEventListener('change', update);
    chips.forEach(c => c.addEventListener('click', () => {
      const k = c.dataset.key, v = c.dataset.val;
      filter[k] = filter[k] === v ? null : v; update();
    }));
    document.getElementById('clear').addEventListener('click', () => {
      q.value = ''; filter.tag = null; filter.venue = null; update();
    });
    document.addEventListener('keydown', e => {
      if (e.key === '/' && document.activeElement !== q) { e.preventDefault(); q.focus(); }
    });
    update();
  }
})();
