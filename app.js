(function () {
  let allData = [];
  let curSort = 'mult';
  let curTier = 'all';
  let curRegion = 'all';
  let isZH = false;
  let watchlist = JSON.parse(localStorage.getItem('pmr_wl') || '[]');

  function loadData() {
    fetch('pmr-data-latest.json?t=' + Date.now())
      .then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(data => {
        allData = Array.isArray(data) ? data : (data.listings || data.data || []);
        const dt = document.getElementById('dt');
        if (dt) dt.textContent = new Date().toLocaleDateString('en-AU');
        const fr = document.getElementById('freshness');
        if (fr) fr.textContent = allData.length + ' listings';
        buildRegions();
        bindPills();
        render();
      })
      .catch(e => {
        const ta = document.getElementById('ta');
        if (ta) ta.innerHTML = '<div style="padding:60px;text-align:center;color:#dc4646">Cannot load pmr-data-latest.json<br><small>' + e.message + '</small></div>';
      });
  }

  function buildRegions() {
    const bar = document.getElementById('rf-bar');
    if (!bar) return;
    const regions = ['all'];
    allData.forEach(p => {
      const r = (p.location || '').split(',')[0].trim();
      if (r && !regions.includes(r)) regions.push(r);
    });
    let html = '<span class="fbar-label en">Location</span><span class="fbar-label zh">地区</span>';
    regions.forEach((r, i) => {
      html += '<button class="pill' + (i === 0 ? ' ac' : '') + '" data-region="' + r + '">' + (r === 'all' ? '<span class="en">All</span><span class="zh">全部</span>' : r) + '</button>';
    });
    bar.innerHTML = html;
    bar.querySelectorAll('[data-region]').forEach(b => {
      b.addEventListener('click', function () {
        curRegion = this.dataset.region;
        bar.querySelectorAll('[data-region]').forEach(x => x.classList.remove('ac'));
        this.classList.add('ac');
        render();
      });
    });
  }

  function bindPills() {
    document.querySelectorAll('[data-sort]').forEach(b => {
      b.addEventListener('click', function () {
        curSort = this.dataset.sort;
        document.querySelectorAll('[data-sort]').forEach(x => x.classList.remove('ac'));
        this.classList.add('ac');
        render();
      });
    });
    document.querySelectorAll('[data-tier]').forEach(b => {
      b.addEventListener('click', function () {
        curTier = this.dataset.tier;
        document.querySelectorAll('[data-tier]').forEach(x => x.classList.remove('ac'));
        this.classList.add('ac');
        render();
      });
    });
  }

  function getF() {
    let d = allData.slice();
    if (curRegion !== 'all') d = d.filter(p => (p.location || '').includes(curRegion));
    if (curTier !== 'all') d = d.filter(p => {
      const pr = p.price || 0;
      if (curTier === 't1') return pr > 0 && pr < 1e6;
      if (curTier === 't2') return pr >= 1e6 && pr < 1.5e6;
      return pr >= 1.5e6;
    });
    return d.sort((a, b) => {
      if (curSort === 'mult') return (a.multiplier || 999) - (b.multiplier || 999);
      if (curSort === 'ni') return (b.net_income || 0) - (a.net_income || 0);
      if (curSort === 'roi') return roi(b) - roi(a);
      return (a.price || 0) - (b.price || 0);
    });
  }

  function roi(p) { return p.price && p.net_income ? (p.net_income / p.price) * 100 : 0; }

  function cl(k, v) {
    if (!v) return '';
    if (k === 'bc') return v <= 70 ? 'g' : v <= 80 ? 'y' : 'r';
    if (k === 'mult') return v <= 5 ? 'g' : v <= 7 ? 'y' : 'r';
    if (k === 'cont') return v >= 20 ? 'g' : v >= 10 ? 'y' : 'r';
    if (k === 'ni') return v >= 150000 ? 'g' : v >= 80000 ? 'y' : 'r';
    if (k === 'pool') return v >= 30 ? 'g' : v >= 15 ? 'y' : 'r';
    return '';
  }

  function fm(k, v) {
    if (v == null) return '—';
    if (k === 'price' || k === 'ni') return v ? '$' + Number(v).toLocaleString('en-AU') : '—';
    if (k === 'bc') return Number(v).toFixed(1) + '%';
    if (k === 'mult') return Number(v).toFixed(2) + 'x';
    if (k === 'cont') return v + 'yr';
    return String(v);
  }

  function esc(s) { return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

  function mc(l, v, c) { return '<div class="mc' + (c ? ' ' + c : '') + '"><div class="v ' + (c || '') + '">' + v + '</div><div class="l">' + l + '</div></div>'; }

  function render() { renderCards(); renderWL(); }

  function renderCards() {
    const ta = document.getElementById('ta');
    if (!ta) return;
    const list = getF();
    if (!list.length) {
      ta.innerHTML = '<div style="padding:60px;text-align:center;color:var(--t2)">No listings match filters.</div>';
      return;
    }

    let cards = '';
    list.forEach((p, i) => {
      const idx = allData.indexOf(p);
      const url = p.url || p.link || '';
      const inWL = watchlist.includes(idx);
      const rk = i < 2 ? 'g' : i < 4 ? 'y' : 'd';
      cards += '<div class="card"><div class="card-h"><span class="rk ' + rk + '">' + (i + 1) + '</span><span class="nm">' + esc(p.title || p.name || 'PMR') + (p.location ? ' <span style="font-size:11px;font-weight:400;color:var(--t2)">· ' + esc(p.location) + '</span>' : '') + '</span><button class="star' + (inWL ? ' on' : '') + '" onclick="toggleWL(' + idx + ',this)">★</button></div><div class="mg">' + mc('PRICE', fm('price', p.price), cl('price', p.price)) + mc('NI', fm('ni', p.net_income), cl('ni', p.net_income)) + mc('BC%', fm('bc', p.bc_percent), cl('bc', p.bc_percent)) + mc('MULT', fm('mult', p.multiplier), cl('mult', p.multiplier)) + mc('CONT', fm('cont', p.contract_years), cl('cont', p.contract_years)) + mc('POOL', fm('pool', p.pool_units), cl('pool', p.pool_units)) + '</div>' + (p.notes ? '<div class="cn-notes">' + esc(p.notes) + '</div>' : '') + (url ? '<div style="margin-top:8px"><a href="' + esc(url) + '" target="_blank" class="lk" style="font-size:12px;color:var(--ac)">View listing →</a></div>' : '') + '</div>';
    });

    let tbl = '<div class="tw mobile-hide"><table class="t"><thead><tr><th style="text-align:left">#</th><th style="text-align:left">Name</th><th>Price</th><th>NI</th><th>BC%</th><th>Mult</th><th>Cont</th><th>Pool</th><th>ROI</th></tr></thead><tbody>';
    list.forEach((p, i) => {
      const r = roi(p);
      const url = p.url || p.link || '';
      tbl += '<tr ' + (url ? 'onclick="window.open(\'' + esc(url) + '\',\'_blank\')"' : '') + ' style="cursor:pointer"><td style="text-align:left;color:var(--t2)">' + (i + 1) + '</td><td style="text-align:left">' + esc(p.title || p.name || 'PMR') + '</td><td class="' + cl('price', p.price) + '">' + fm('price', p.price) + '</td><td class="' + cl('ni', p.net_income) + '">' + fm('ni', p.net_income) + '</td><td class="' + cl('bc', p.bc_percent) + '">' + fm('bc', p.bc_percent) + '</td><td class="' + cl('mult', p.multiplier) + '">' + fm('mult', p.multiplier) + '</td><td class="cont-' + cl('cont', p.contract_years) + '">' + fm('cont', p.contract_years) + '</td><td class="' + cl('pool', p.pool_units) + '">' + fm('pool', p.pool_units) + '</td><td>' + (r ? r.toFixed(1) + '%' : '—') + '</td></tr>';
    });
    tbl += '</tbody></table></div>';

    ta.innerHTML = tbl + '<div class="mobile-cards">' + cards + '</div>';
  }

  function renderWL() {
    const tw = document.getElementById('tw');
    const cnt = document.getElementById('wl-cnt');
    if (cnt) { cnt.textContent = watchlist.length; cnt.style.display = watchlist.length ? 'inline-block' : 'none'; }
    if (!tw) return;
    if (!watchlist.length) { tw.innerHTML = '<div style="padding:60px;text-align:center;color:var(--t2)">No saved listings. Click ★ to save.</div>'; return; }
    let html = '<div>';
    watchlist.forEach(idx => {
      const p = allData[idx];
      if (!p) return;
      const url = p.url || p.link || '';
      html += '<div class="card"><div class="card-h"><span class="nm">' + esc(p.title || p.name || 'PMR') + '</span><button class="star on" onclick="toggleWL(' + idx + ',this)">★</button></div><div class="mg">' + mc('PRICE', fm('price', p.price), cl('price', p.price)) + mc('NI', fm('ni', p.net_income), cl('ni', p.net_income)) + mc('BC%', fm('bc', p.bc_percent), cl('bc', p.bc_percent)) + mc('MULT', fm('mult', p.multiplier), cl('mult', p.multiplier)) + mc('CONT', fm('cont', p.contract_years), cl('cont', p.contract_years)) + mc('POOL', fm('pool', p.pool_units), cl('pool', p.pool_units)) + '</div>' + (url ? '<div style="margin-top:8px"><a href="' + esc(url) + '" target="_blank" class="lk" style="font-size:12px;color:var(--ac)">View listing →</a></div>' : '') + '</div>';
    });
    tw.innerHTML = html + '</div>';
  }

  window.sw = function (id) {
    document.querySelectorAll('.tp').forEach(e => e.classList.remove('ac'));
    document.querySelectorAll('.ti').forEach(e => e.classList.remove('ac'));
    const p = document.getElementById(id);
    if (p) p.classList.add('ac');
    const map = { ta: 0, t4: 1, tw: 2 };
    const tabs = document.querySelectorAll('.ti');
    if (map[id] != null && tabs[map[id]]) tabs[map[id]].classList.add('ac');
  };

  window.tog = function () {
    isZH = !isZH;
    document.body.classList.toggle('cn', isZH);
    const b = document.querySelector('.lb');
    if (b) b.textContent = isZH ? 'EN' : '中文';
  };

  window.toggleWL = function (idx, btn) {
    const i = watchlist.indexOf(idx);
    if (i === -1) watchlist.push(idx); else watchlist.splice(i, 1);
    localStorage.setItem('pmr_wl', JSON.stringify(watchlist));
    if (btn) btn.classList.toggle('on', watchlist.includes(idx));
    renderWL();
  };

  document.addEventListener('DOMContentLoaded', loadData);
})();
