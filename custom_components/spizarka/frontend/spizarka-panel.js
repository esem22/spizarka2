class SpizarkaPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._hass = null;
    this._tab = 'products';
    this._search = '';
    this._location = '';
    this._category = '';
    this._dialog = null;
    this._message = '';
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  set panel(panel) {
    this._panel = panel;
  }

  get _productsState() {
    if (!this._hass) return null;
    return Object.values(this._hass.states).find(
      (s) => s.entity_id.startsWith('sensor.') && s.attributes?.spizarka_kind === 'products'
    );
  }

  get _stockState() {
    if (!this._hass) return null;
    return Object.values(this._hass.states).find(
      (s) => s.entity_id.startsWith('sensor.') && s.attributes?.spizarka_kind === 'stock'
    );
  }

  get data() {
    const ps = this._productsState;
    const ss = this._stockState;
    const products = ps?.attributes?.products || [];
    const locations = ps?.attributes?.locations || [];
    const batches = ss?.attributes?.batches || [];
    const locMap = Object.fromEntries(locations.map((l) => [l.id, l.name]));

    const enriched = products.map((p) => {
      const pb = batches.filter((b) => b.product_id === p.id && Number(b.quantity) > 0);
      const quantity = pb.reduce((a, b) => a + Number(b.quantity || 0), 0);
      const expiries = pb.map((b) => b.expiry_date).filter(Boolean).sort();
      const productLocations = [...new Set(pb.map((b) => locMap[b.location_id]).filter(Boolean))];
      return {
        ...p,
        quantity,
        nearestExpiry: expiries[0] || '',
        locations: productLocations,
        batches: pb,
      };
    });
    return { products: enriched, locations, batches, locMap };
  }

  esc(v) {
    return String(v ?? '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  fmt(n) {
    const x = Number(n || 0);
    return Number.isInteger(x) ? String(x) : x.toFixed(2).replace(/0+$/, '').replace(/\.$/, '');
  }

  daysUntil(dateStr) {
    if (!dateStr) return null;
    const today = new Date();
    today.setHours(0,0,0,0);
    const target = new Date(`${dateStr}T00:00:00`);
    return Math.round((target - today) / 86400000);
  }

  expiryBadge(dateStr) {
    if (!dateStr) return '<span class="muted">brak</span>';
    const days = this.daysUntil(dateStr);
    let cls = 'ok';
    let suffix = '';
    if (days < 0) { cls = 'bad'; suffix = ` • po terminie ${Math.abs(days)} d.`; }
    else if (days === 0) { cls = 'bad'; suffix = ' • dzisiaj'; }
    else if (days <= 7) { cls = 'warn'; suffix = ` • ${days} d.`; }
    return `<span class="badge ${cls}">${this.esc(dateStr)}${suffix}</span>`;
  }

  filteredProducts() {
    const { products } = this.data;
    const q = this._search.trim().toLocaleLowerCase('pl');
    return products.filter((p) => {
      const matchesSearch = !q || [p.name, p.ean, p.category]
        .some((v) => String(v || '').toLocaleLowerCase('pl').includes(q));
      const matchesLocation = !this._location || p.locations.includes(this._location);
      const matchesCategory = !this._category || (p.category || '') === this._category;
      return matchesSearch && matchesLocation && matchesCategory;
    }).sort((a,b) => a.name.localeCompare(b.name, 'pl'));
  }

  render() {
    if (!this.shadowRoot) return;
    if (!this._hass) {
      this.shadowRoot.innerHTML = '<div>Ładowanie…</div>';
      return;
    }
    const { products, locations } = this.data;
    const categories = [...new Set(products.map(p => p.category).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'pl'));
    const visible = this.filteredProducts();
    const low = products.filter(p => Number(p.quantity) < Number(p.minimum || 0));
    const expiring = products
      .filter(p => p.nearestExpiry && this.daysUntil(p.nearestExpiry) <= 7)
      .sort((a,b) => a.nearestExpiry.localeCompare(b.nearestExpiry));

    const content = this._tab === 'products'
      ? this.productsTable(visible)
      : this._tab === 'expiring'
        ? this.productsTable(expiring, true)
        : this.productsTable(low);

    this.shadowRoot.innerHTML = `
      <style>
        :host{display:block;background:var(--primary-background-color);color:var(--primary-text-color);min-height:100%;font-family:var(--paper-font-body1_-_font-family,Arial,sans-serif)}
        *{box-sizing:border-box}.wrap{padding:18px;max-width:1500px;margin:0 auto}.top{display:flex;gap:12px;align-items:center;justify-content:space-between;flex-wrap:wrap;margin-bottom:14px}
        h1{font-size:26px;margin:0;display:flex;align-items:center;gap:8px}.version{font-size:12px;color:var(--secondary-text-color);font-weight:400}.actions{display:flex;gap:8px;flex-wrap:wrap}
        button,.btn{border:0;border-radius:10px;padding:10px 14px;background:var(--primary-color);color:var(--text-primary-color,#fff);font-weight:600;cursor:pointer}.secondary{background:var(--secondary-background-color);color:var(--primary-text-color);border:1px solid var(--divider-color)}
        .tabs{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}.tab{background:var(--card-background-color);color:var(--primary-text-color);border:1px solid var(--divider-color)}.tab.active{background:var(--primary-color);color:white}
        .filters{display:grid;grid-template-columns:minmax(220px,1fr) 220px 220px;gap:10px;margin:12px 0 16px}.filters input,.filters select,.form input,.form select{width:100%;padding:10px;border-radius:9px;border:1px solid var(--divider-color);background:var(--card-background-color);color:var(--primary-text-color)}
        .card{background:var(--card-background-color);border-radius:14px;box-shadow:var(--ha-card-box-shadow);overflow:hidden;border:1px solid var(--divider-color)}table{width:100%;border-collapse:collapse}th,td{padding:11px 12px;text-align:left;border-bottom:1px solid var(--divider-color);vertical-align:middle}th{font-size:12px;text-transform:uppercase;color:var(--secondary-text-color);letter-spacing:.04em}.name{font-weight:700}.sub{font-size:12px;color:var(--secondary-text-color);margin-top:3px}.qty{font-weight:700;white-space:nowrap}.row-actions{display:flex;gap:6px;flex-wrap:wrap}.row-actions button{padding:7px 9px;font-size:12px}.badge{display:inline-block;border-radius:999px;padding:4px 8px;font-size:12px}.badge.ok{background:rgba(76,175,80,.16)}.badge.warn{background:rgba(255,152,0,.18)}.badge.bad{background:rgba(244,67,54,.18)}.muted{color:var(--secondary-text-color)}
        .empty{padding:30px;text-align:center;color:var(--secondary-text-color)}.message{padding:10px 12px;border-radius:10px;margin-bottom:12px;background:rgba(76,175,80,.15)}
        .overlay{position:fixed;inset:0;background:rgba(0,0,0,.45);display:flex;align-items:center;justify-content:center;padding:20px;z-index:9999}.dialog{width:min(560px,100%);max-height:90vh;overflow:auto;background:var(--card-background-color);border-radius:16px;padding:18px;box-shadow:0 18px 50px rgba(0,0,0,.35)}.dialog h2{margin:0 0 14px}.form{display:grid;gap:11px}.form label{display:grid;gap:5px;font-size:13px}.dialog-actions{display:flex;justify-content:flex-end;gap:8px;margin-top:16px}.hint{font-size:12px;color:var(--secondary-text-color)}
        @media(max-width:800px){.filters{grid-template-columns:1fr}.card{overflow:auto}table{min-width:850px}.wrap{padding:12px}}
      </style>
      <div class="wrap">
        <div class="top"><h1>🥫 Spiżarka <span class="version">v${this.esc(this._panel?.config?.version || '0.2.0')}</span></h1><div class="actions"><button id="addProduct">+ Produkt</button><button class="secondary" id="addStock">+ Dodaj stan</button></div></div>
        ${this._message ? `<div class="message">${this.esc(this._message)}</div>` : ''}
        <div class="tabs">
          <button class="tab ${this._tab==='products'?'active':''}" data-tab="products">Produkty (${products.length})</button>
          <button class="tab ${this._tab==='expiring'?'active':''}" data-tab="expiring">Kończy się termin (${expiring.length})</button>
          <button class="tab ${this._tab==='low'?'active':''}" data-tab="low">Niski stan (${low.length})</button>
        </div>
        <div class="filters">
          <input id="search" placeholder="Szukaj: nazwa, EAN, kategoria…" value="${this.esc(this._search)}">
          <select id="location"><option value="">Wszystkie lokalizacje</option>${locations.map(l=>`<option ${this._location===l.name?'selected':''}>${this.esc(l.name)}</option>`).join('')}</select>
          <select id="category"><option value="">Wszystkie kategorie</option>${categories.map(c=>`<option ${this._category===c?'selected':''}>${this.esc(c)}</option>`).join('')}</select>
        </div>
        <div class="card">${content}</div>
      </div>
      ${this.dialogHtml()}
    `;
    this.bindEvents();
  }

  productsTable(products, expiryView=false) {
    if (!products.length) return '<div class="empty">Brak produktów spełniających warunki.</div>';
    return `<table><thead><tr><th>Produkt</th><th>Kategoria</th><th>Lokalizacja</th><th>Ilość</th><th>${expiryView?'Termin':'Najbliższy termin'}</th><th>Akcje</th></tr></thead><tbody>${products.map(p=>`
      <tr>
        <td><div class="name">${this.esc(p.name)}</div><div class="sub">${p.ean ? `EAN: ${this.esc(p.ean)}` : 'bez EAN'}</div></td>
        <td>${this.esc(p.category || '—')}</td>
        <td>${p.locations.length ? p.locations.map(x=>this.esc(x)).join(', ') : '<span class="muted">brak stanu</span>'}</td>
        <td class="qty">${this.fmt(p.quantity)} ${this.esc(p.unit || '')}<div class="sub">min. ${this.fmt(p.minimum || 0)}</div></td>
        <td>${this.expiryBadge(p.nearestExpiry)}</td>
        <td><div class="row-actions"><button data-action="add" data-id="${this.esc(p.id)}">+ Dodaj</button><button class="secondary" data-action="consume" data-id="${this.esc(p.id)}">− Zużyj</button><button class="secondary" data-action="move" data-id="${this.esc(p.id)}">↔ Przenieś</button></div></td>
      </tr>`).join('')}</tbody></table>`;
  }

  dialogHtml() {
    if (!this._dialog) return '';
    const { products, locations } = this.data;
    const product = products.find(p => p.id === this._dialog.productId);
    const locOptions = locations.map(l=>`<option value="${this.esc(l.name)}">${this.esc(l.name)}</option>`).join('');
    if (this._dialog.type === 'product') return `<div class="overlay"><div class="dialog"><h2>Dodaj produkt</h2><div class="form">
      <label>Nazwa<input id="f_name" autofocus></label><label>EAN<input id="f_ean" inputmode="numeric"></label><label>Kategoria<input id="f_category"></label><label>Jednostka<input id="f_unit" value="szt."></label><label>Stan minimalny<input id="f_minimum" type="number" min="0" step="0.1" value="0"></label>
      </div><div class="dialog-actions"><button class="secondary" data-close>Anuluj</button><button data-submit="product">Dodaj</button></div></div></div>`;
    if (this._dialog.type === 'stock') return `<div class="overlay"><div class="dialog"><h2>Dodaj stan</h2><div class="form">
      <label>Produkt<select id="f_product">${products.map(p=>`<option value="${this.esc(p.id)}" ${product?.id===p.id?'selected':''}>${this.esc(p.name)}</option>`).join('')}</select></label><label>Ilość<input id="f_quantity" type="number" min="0.001" step="0.1" value="1"></label><label>Lokalizacja<select id="f_location">${locOptions}</select></label><label>Data ważności<input id="f_expiry" type="date"></label>
      </div><div class="dialog-actions"><button class="secondary" data-close>Anuluj</button><button data-submit="stock">Dodaj</button></div></div></div>`;
    if (this._dialog.type === 'consume') return `<div class="overlay"><div class="dialog"><h2>Zużyj: ${this.esc(product?.name || '')}</h2><div class="form">
      <label>Ilość<input id="f_quantity" type="number" min="0.001" step="0.1" value="1"></label><label>Lokalizacja <span class="hint">(opcjonalnie)</span><select id="f_location"><option value="">Dowolna — FEFO</option>${locOptions}</select></label>
      </div><div class="dialog-actions"><button class="secondary" data-close>Anuluj</button><button data-submit="consume">Zużyj</button></div></div></div>`;
    if (this._dialog.type === 'move') return `<div class="overlay"><div class="dialog"><h2>Przenieś: ${this.esc(product?.name || '')}</h2><div class="form">
      <label>Ilość<input id="f_quantity" type="number" min="0.001" step="0.1" value="1"></label><label>Z lokalizacji<select id="f_from">${locOptions}</select></label><label>Do lokalizacji<select id="f_to">${locOptions}</select></label>
      </div><div class="dialog-actions"><button class="secondary" data-close>Anuluj</button><button data-submit="move">Przenieś</button></div></div></div>`;
    return '';
  }

  bindEvents() {
    this.shadowRoot.querySelectorAll('[data-tab]').forEach(b => b.addEventListener('click', () => { this._tab = b.dataset.tab; this.render(); }));
    this.shadowRoot.getElementById('search')?.addEventListener('input', e => { this._search = e.target.value; this.render(); });
    this.shadowRoot.getElementById('location')?.addEventListener('change', e => { this._location = e.target.value; this.render(); });
    this.shadowRoot.getElementById('category')?.addEventListener('change', e => { this._category = e.target.value; this.render(); });
    this.shadowRoot.getElementById('addProduct')?.addEventListener('click', () => { this._dialog={type:'product'}; this.render(); });
    this.shadowRoot.getElementById('addStock')?.addEventListener('click', () => { this._dialog={type:'stock'}; this.render(); });
    this.shadowRoot.querySelectorAll('[data-action]').forEach(b => b.addEventListener('click', () => {
      this._dialog = { type: b.dataset.action === 'add' ? 'stock' : b.dataset.action, productId: b.dataset.id };
      this.render();
    }));
    this.shadowRoot.querySelector('[data-close]')?.addEventListener('click', () => { this._dialog=null; this.render(); });
    this.shadowRoot.querySelector('[data-submit]')?.addEventListener('click', async (e) => {
      const kind = e.currentTarget.dataset.submit;
      e.currentTarget.disabled = true;
      try { await this.submit(kind); this._dialog=null; this._message='Operacja wykonana.'; this.render(); setTimeout(()=>{this._message='';this.render();},2500); }
      catch(err) { alert(`Błąd: ${err?.message || err}`); e.currentTarget.disabled=false; }
    });
  }

  val(id) { return this.shadowRoot.getElementById(id)?.value ?? ''; }

  async submit(kind) {
    if (kind === 'product') {
      const name=this.val('f_name').trim(); if(!name) throw new Error('Podaj nazwę produktu.');
      await this._hass.callService('spizarka','add_product',{name,ean:this.val('f_ean').trim()||undefined,category:this.val('f_category').trim()||undefined,unit:this.val('f_unit').trim()||'szt.',minimum:Number(this.val('f_minimum')||0)}); return;
    }
    if (kind === 'stock') {
      await this._hass.callService('spizarka','add_stock',{product_id:this.val('f_product'),quantity:Number(this.val('f_quantity')),location:this.val('f_location'),expiry_date:this.val('f_expiry')||undefined}); return;
    }
    if (kind === 'consume') {
      const data={product_id:this._dialog.productId,quantity:Number(this.val('f_quantity'))}; const loc=this.val('f_location'); if(loc) data.location=loc;
      await this._hass.callService('spizarka','consume_stock',data); return;
    }
    if (kind === 'move') {
      const from=this.val('f_from'), to=this.val('f_to'); if(from===to) throw new Error('Wybierz dwie różne lokalizacje.');
      await this._hass.callService('spizarka','move_stock',{product_id:this._dialog.productId,quantity:Number(this.val('f_quantity')),from_location:from,to_location:to});
    }
  }
}

customElements.define('spizarka-panel', SpizarkaPanel);
