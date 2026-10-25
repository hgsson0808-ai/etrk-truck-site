(function () {
  // 홈: 정렬 · 톤수 · 검색 (처음엔 최근 매물만, 조건을 고르면 전체 매물 목록 cars.json을 불러와 찾음)
  var grid = document.querySelector('[data-grid]');
  if (grid) {
    var tpl = grid.firstElementChild && grid.firstElementChild.cloneNode(true);
    var st = { sort: 'i-asc', ton: '', q: '' }, idx = null, loading = null, LIMIT = 120;
    var countEl = document.querySelector('[data-count]'), emptyEl = document.querySelector('[data-empty]');
    var moreEl = document.querySelector('[data-more]');
    var qState = document.querySelector('[data-q-state]'), qText = document.querySelector('[data-q-text]');
    function load() {
      if (idx) return Promise.resolve(idx);
      if (!loading) loading = fetch('cars.json').then(function (r) { return r.json(); }).then(function (d) { idx = d; return d; });
      return loading;
    }
    function make(c) {
      var el = tpl.cloneNode(true), img = el.querySelector('img');
      el.dataset.ton = c.tb; el.dataset.type = c.ty;
      el.querySelector('.card-link').href = c.f;
      img.src = c.t; img.alt = c.h + ' ' + c.y + '년식'; img.loading = 'lazy';
      el.querySelector('.card-type').textContent = c.ty;
      var pics = el.querySelector('.card-pics'); pics.lastChild.textContent = c.n;
      el.querySelector('.card-title').textContent = c.h;
      var li = el.querySelectorAll('.card-specs li'); li[0].textContent = c.y + '년식'; li[1].textContent = c.kt; li[2].textContent = c.tm;
      el.querySelector('.price strong').textContent = c.p.toLocaleString('ko-KR');
      return el;
    }
    function apply() {
      load().then(function (all) {
        var p = st.sort.split('-'), key = { i: 'i', price: 'p', km: 'k', year: 'y' }[p[0]], dir = p[1] === 'asc' ? 1 : -1;
        var toks = st.q.toLowerCase().split(/\s+/).filter(Boolean);
        var hit = all.filter(function (c) {
          return (!st.ton || c.tb === st.ton) && toks.every(function (t) { return c.q.indexOf(t) > -1; });
        }).sort(function (a, b) { return (a[key] - b[key]) * dir || (a.i - b.i); });
        grid.textContent = '';
        hit.slice(0, LIMIT).forEach(function (c) { grid.appendChild(make(c)); });
        countEl.textContent = hit.length; emptyEl.hidden = hit.length > 0;
        if (moreEl) moreEl.hidden = hit.length <= LIMIT && (st.q || st.ton || st.sort !== 'i-asc');
        qState.hidden = !st.q; qText.textContent = st.q;
      }).catch(function () { location.href = grid.dataset.list || location.href; });
    }
    function pick(sel, attr) {
      var bs = document.querySelectorAll(sel);
      Array.prototype.forEach.call(bs, function (b) {
        b.addEventListener('click', function () {
          st[attr] = b.dataset[attr];
          Array.prototype.forEach.call(bs, function (o) { o.classList.toggle('on', o === b); o.setAttribute('aria-pressed', o === b); });
          apply();
        });
      });
    }
    pick('.stock [data-sort]', 'sort'); pick('.stock [data-ton]', 'ton');
    var qform = document.getElementById('search');
    qform.elements.q.addEventListener('focus', load, { once: true });
    function go() { document.getElementById('stock').scrollIntoView({ behavior: 'smooth', block: 'start' }); }
    qform.addEventListener('submit', function (e) { e.preventDefault(); st.q = qform.elements.q.value.trim(); apply(); go(); });
    document.querySelector('[data-q-clear]').addEventListener('click', function () { qform.elements.q.value = ''; st.q = ''; apply(); });
  }

  // 홈: 배너 슬라이드
  var bn = document.querySelector('[data-banner]');
  if (bn) {
    var tr = bn.querySelector('[data-bn-track]'), dots = bn.querySelectorAll('[data-bn-go]'), n = dots.length, cur = 0, timer;
    function show(i) { cur = (i + n) % n; tr.scrollTo({ left: tr.clientWidth * cur, behavior: 'smooth' }); }
    function mark() {
      var i = Math.round(tr.scrollLeft / tr.clientWidth); cur = i;
      Array.prototype.forEach.call(dots, function (d, k) { d.classList.toggle('on', k === i); d.setAttribute('aria-selected', k === i); });
    }
    tr.addEventListener('scroll', function () { window.requestAnimationFrame(mark); }, { passive: true });
    Array.prototype.forEach.call(dots, function (d) { d.addEventListener('click', function () { show(Number(d.dataset.bnGo)); restart(); }); });
    var still = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    function restart() { clearInterval(timer); if (!still) timer = setInterval(function () { show(cur + 1); }, 5000); }
    bn.addEventListener('pointerdown', restart); restart();
  }

  // 차종·전체 매물: 정렬 버튼
  var bar = document.querySelector('[data-sortbar]');
  if (bar) {
    var grids = document.querySelectorAll('[data-sortable]');
    var btns = bar.querySelectorAll('[data-sort]');
    Array.prototype.forEach.call(btns, function (b) {
      b.addEventListener('click', function () {
        var p = b.dataset.sort.split('-'), key = p[0], dir = p[1] === 'asc' ? 1 : -1;
        Array.prototype.forEach.call(grids, function (g) {
          Array.prototype.slice.call(g.children)
            .sort(function (x, y) { return (Number(x.dataset[key]) - Number(y.dataset[key])) * dir || (x.dataset.i - y.dataset.i); })
            .forEach(function (c) { g.appendChild(c); });
        });
        Array.prototype.forEach.call(btns, function (o) { o.classList.toggle('on', o === b); o.setAttribute('aria-pressed', o === b); });
      });
    });
  }

  // 차종·톤수 페이지: 변속기·가격·연식·제조사·주행거리 필터 (주소 #tm=오토&price=2000-3999 로도 열림)
  var fbox = document.querySelector('[data-filters]');
  if (fbox) {
    var fcards = Array.prototype.slice.call(document.querySelectorAll('[data-sortable] .card'));
    var rows = Array.prototype.slice.call(fbox.querySelectorAll('[data-fg]'));
    var attr = { tm: 'tm', year: 'year', mk: 'mk', km: 'km' };
    var sel = {};
    var fyFrom = fbox.querySelector('[data-fy-from]'), fyTo = fbox.querySelector('[data-fy-to]'), fyN = fbox.querySelector('.f-yn');
    function hit(card, g, v) {
      if (!v) return true;
      var x = card.dataset[attr[g]];
      if (g === 'tm' || g === 'mk') return x === v;
      var r = v.split('-'), n = Number(x);
      return (r[0] === '' || n >= Number(r[0])) && (r[1] === '' || n <= Number(r[1]));
    }
    function ok(card, skip) {
      for (var g in sel) if (g !== skip && !hit(card, g, sel[g])) return false;
      return true;
    }
    var nOut2 = document.querySelector('.sortbar-n b'), hCount2 = document.querySelector('.page-h .count');
    var reset = fbox.querySelector('.f-reset'), empty = document.querySelector('.f-empty'), grid = document.querySelector('[data-sortable]');
    function apply(first) {
      var n = 0;
      fcards.forEach(function (c) { var s = ok(c); c.hidden = !s; if (s) n++; });
      rows.forEach(function (row) {
        var g = row.dataset.fg, live = 0;
        Array.prototype.forEach.call(row.querySelectorAll('[data-v]'), function (b) {
          var v = b.dataset.v, on = (sel[g] || '') === v;
          b.classList.toggle('on', on); b.setAttribute('aria-pressed', on);
          if (!v) return;
          var k = fcards.filter(function (c) { return ok(c, g) && hit(c, g, v); }).length;
          b.querySelector('.f-n').textContent = k;
          b.disabled = !k && !on;
          if (first) b.hidden = !fcards.some(function (c) { return hit(c, g, v); });
          if (!b.hidden) live++;
        });
        if (first) row.hidden = live < 2;
      });
      if (fyN) fyN.textContent = fcards.filter(function (c) { return ok(c); }).length + '대';
      if (fyFrom) fyFrom.value = (sel.year || '-').split('-')[0];
      if (fyTo) fyTo.value = (sel.year || '-').split('-')[1] || '';
      if (nOut2) nOut2.textContent = n;
      if (hCount2) hCount2.textContent = n + '대';
      if (reset) reset.hidden = !Object.keys(sel).some(function (g) { return sel[g]; });
      if (empty) { empty.hidden = n > 0; if (grid) grid.hidden = n === 0; }
      var h = Object.keys(sel).filter(function (g) { return sel[g]; }).map(function (g) { return g + '=' + sel[g]; }).join('&');
      try { history.replaceState(null, '', h ? '#' + h : location.pathname + location.search); } catch (e) {}
      Array.prototype.forEach.call(document.querySelectorAll('ul.chips-row a.chip'), function (a) { a.href = a.href.split('#')[0] + (h ? '#' + h : ''); });
    }
    rows.forEach(function (row) {
      row.addEventListener('click', function (e) {
        var b = e.target.closest('[data-v]'); if (!b || b.disabled) return;
        sel[row.dataset.fg] = b.dataset.v; apply();
      });
    });
    if (reset) reset.addEventListener('click', function () { sel = {}; apply(); });
    function yearPick() {
      var a = fyFrom.value, b = fyTo.value;
      if (a && b && Number(a) > Number(b)) { var t = a; a = b; b = t; }
      sel.year = (a || b) ? a + '-' + b : ''; apply();
    }
    if (fyFrom) { fyFrom.addEventListener('change', yearPick); fyTo.addEventListener('change', yearPick); }
    var hs = decodeURIComponent(location.hash.slice(1));
    if (hs === '오토' || hs === '수동') sel.tm = hs;
    else hs.split('&').forEach(function (kv) { var p = kv.split('='); if (attr[p[0]] && p[1]) sel[p[0]] = p[1]; });
    apply(true);
    if (fbox.querySelectorAll('[data-fg]:not([hidden]), [data-fy]').length === 0) fbox.hidden = true;
  }

  // 상세: 판매 방식 ? 툴팁 (PC는 마우스 올리면, 모바일은 터치하면 판매상사 표시)
  Array.prototype.forEach.call(document.querySelectorAll('[data-tip]'), function (t) {
    var q = t.querySelector('.tip-q');
    q.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = !t.classList.contains('open');
      t.classList.toggle('open', open); q.setAttribute('aria-expanded', open);
    });
    document.addEventListener('click', function () { t.classList.remove('open'); q.setAttribute('aria-expanded', false); });
    q.addEventListener('keydown', function (e) { if (e.key === 'Escape') { t.classList.remove('open'); q.setAttribute('aria-expanded', false); } });
  });

  // 상세: 사진 슬라이드
  var gal = document.querySelector('[data-gallery]');
  if (gal) {
    var track = gal.querySelector('.g-track');
    var now = gal.querySelector('[data-g-now]');
    var thumbs = gal.querySelectorAll('[data-g-go]');
    function mark(i) {
      now.textContent = i + 1;
      thumbs.forEach(function (t, k) { t.setAttribute('aria-current', k === i ? 'true' : 'false'); });
    }
    track.addEventListener('scroll', function () {
      mark(Math.round(track.scrollLeft / track.clientWidth));
    }, { passive: true });
    thumbs.forEach(function (t) {
      t.addEventListener('click', function () {
        track.scrollTo({ left: track.clientWidth * Number(t.dataset.gGo), behavior: 'smooth' });
      });
    });
    track.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
        e.preventDefault();
        track.scrollBy({ left: (e.key === 'ArrowRight' ? 1 : -1) * track.clientWidth, behavior: 'smooth' });
      }
    });
    gal.querySelectorAll('[data-g-step]').forEach(function (b) {
      b.addEventListener('click', function () {
        track.scrollBy({ left: Number(b.dataset.gStep) * track.clientWidth, behavior: 'smooth' });
      });
    });
    mark(0);
  }

  // 상세: 매물 영상 — 유튜브는 눌렀을 때만 불러오고, 없으면 사진을 3초씩 넘기는 자동 영상
  var yt = document.querySelector('[data-yt]');
  if (yt) yt.addEventListener('click', function () {
    yt.innerHTML = '<iframe src="https://www.youtube-nocookie.com/embed/' + encodeURIComponent(yt.dataset.yt) + '?autoplay=1&rel=0" title="매물 영상" allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen></iframe>';
  });
  var show = document.querySelector('[data-show]');
  if (show && window.matchMedia('(min-width: 861px)').matches) {
    var fs = show.querySelectorAll('.vs-f'), bars = show.querySelectorAll('.vs-bar span'), k = 0, t = null, seen = false;
    var still = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    function img(i) { var m = fs[i] && fs[i].querySelector('img[data-src]'); if (m) { m.src = m.dataset.src; m.removeAttribute('data-src'); } }
    function go(i) {
      fs[k].classList.remove('on'); k = (i + fs.length) % fs.length; fs[k].classList.add('on');
      img(k); img(k + 1);
      Array.prototype.forEach.call(bars, function (b, j) {
        b.classList.toggle('done', j < k); var bar = b.firstChild;
        bar.style.transition = 'none'; bar.style.width = j < k ? '100%' : '0';
      });
      if (!show.classList.contains('paused')) {
        var cur = bars[k].firstChild, ms = k === fs.length - 1 ? 4000 : 3000;
        requestAnimationFrame(function () { requestAnimationFrame(function () { cur.style.transition = 'width ' + ms + 'ms linear'; cur.style.width = '100%'; }); });
        clearTimeout(t); t = setTimeout(function () { go(k + 1); }, ms);
      }
    }
    function pause(p) {
      show.classList.toggle('paused', p); clearTimeout(t);
      show.querySelector('[data-vs-toggle]').setAttribute('aria-label', p ? '재생' : '일시정지');
      if (!p) go(k);
    }
    show.querySelector('[data-vs-toggle]').addEventListener('click', function () { show.classList.add('user'); pause(!show.classList.contains('paused')); });
    Array.prototype.forEach.call(bars, function (b, j) { b.addEventListener('click', function () { go(j); }); });
    img(0); img(1);
    if (still) { show.classList.add('paused'); go(0); }
    else if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (es) {
        es.forEach(function (e) {
          if (e.isIntersecting && !seen) { seen = true; go(0); }
          else if (seen && !show.classList.contains('user')) { if (e.isIntersecting) pause(false); else pause(true); }
        });
      }, { threshold: 0.4 }).observe(show);
    } else go(0);
  }

  // 내차팔기: 입력한 내용이 채워진 문자창 열기 (손님 폰 → 담당자 폰)
  var form = document.getElementById('sell');
  if (form) {
    var err = document.querySelector('[data-form-err]'), sms = document.querySelector('[data-sms]');
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var f = form.elements; err.hidden = true; f.car.removeAttribute('aria-invalid');
      if (!f.car.value.trim()) { f.car.setAttribute('aria-invalid', 'true'); f.car.focus(); err.textContent = '차종·톤수를 적어 주세요.'; err.hidden = false; return; }
      var lines = ['[__BRAND__ 시세 문의]', '차종·톤수: ' + f.car.value.trim()];
      if (f.plate.value.trim()) lines.push('차량번호: ' + f.plate.value.trim());
      if (f.km.value.trim()) lines.push('주행거리: ' + f.km.value.trim());
      if (f.area.value.trim()) lines.push('차량 위치: ' + f.area.value.trim());
      if (f.memo.value.trim()) lines.push('특이사항: ' + f.memo.value.trim());
      var enc = encodeURIComponent(lines.join('\n'));
      location.href = sms.getAttribute('href').split('?')[0] + '?body=' + enc + '&body=' + enc;
    });
  }


})();
