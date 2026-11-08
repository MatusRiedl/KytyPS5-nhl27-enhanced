'use strict';
/* Faceoff page. Talks to Python through window.pywebview.api (faceoff/api.py). Opened in a plain browser it runs on
   a demo stand-in so the look can be checked without the app. */

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
let api = null;
let state = null;
let pollTimer = null;

/* ---------- helpers ---------- */
function mb(bytes) {
  if (!bytes) return '0 MB';
  const m = bytes / (1024 * 1024);
  return m >= 1024 ? (m / 1024).toFixed(2) + ' GB' : Math.round(m) + ' MB';
}
function clock(s) {
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60;
  const pad = n => String(n).padStart(2, '0');
  return (h ? h + ':' + pad(m) : m) + ':' + pad(sec);
}
let toastTimer = null;
function toast(text, bad = false) {
  const t = $('#toast');
  t.textContent = text;
  t.classList.toggle('bad', bad);
  t.classList.add('on');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove('on'), 3200);
}
let savedTimer = null;
function flashSaved() {
  const s = $('#saved');
  s.classList.add('on');
  clearTimeout(savedTimer);
  savedTimer = setTimeout(() => s.classList.remove('on'), 1400);
}

/* ---------- tabs ---------- */
function moveTabBar() {
  const active = $('.tab.active'), bar = $('.tab-bar');
  bar.style.left = active.offsetLeft + 'px';
  bar.style.width = active.offsetWidth + 'px';
}
function showTab(name) {
  $$('.tab').forEach(t => {
    const on = t.dataset.tab === name;
    t.classList.toggle('active', on);
    t.setAttribute('aria-selected', on);
  });
  $$('.page').forEach(p => p.classList.toggle('active', p.id === 'page-' + name));
  moveTabBar();
  requestAnimationFrame(() => $$('.seg').forEach(placeThumb));
}

/* ---------- segmented controls ---------- */
function placeThumb(seg) {
  const on = $('button.on', seg), thumb = $('.seg-thumb', seg);
  if (!on || !seg.offsetWidth) return;
  thumb.style.left = on.offsetLeft + 'px';
  thumb.style.width = on.offsetWidth + 'px';
}
function setSeg(seg, value) {
  const buttons = $$('button', seg);
  let match = buttons.find(b => b.dataset.v === String(value));
  if (!match && seg.dataset.setting === 'scale') {           // a hand-edited scale: show the nearest step
    match = buttons.reduce((a, b) => Math.abs(b.dataset.v - value) < Math.abs(a.dataset.v - value) ? b : a);
  }
  buttons.forEach(b => b.classList.toggle('on', b === match));
  placeThumb(seg);
}
function renderSettings(s) {
  setSeg($('[data-setting="resolution"]'), s.resolution);
  setSeg($('[data-setting="fullscreen"]'), s.fullscreen);
  setSeg($('[data-setting="scale"]'), s.scale);
  $('#trophies').setAttribute('aria-checked', s.trophies);
}
async function save(name, value) {
  const r = await api.save_setting(name, value);
  if (r.settings) { state.settings = r.settings; renderSettings(r.settings); }
  if (r.ok) flashSaved(); else toast(r.error || 'Could not save', true);
}

/* ---------- render ---------- */
function renderGame(g) {
  $('#title').textContent = g.title || 'NHL 27';
  const pill = $('#status');
  pill.className = 'pill ' + (g.ok ? 'ok' : 'bad');
  $('span', pill).textContent = g.status;
  const v = $('#version'), id = $('#titleid');
  v.hidden = !g.version; v.textContent = g.version ? 'v' + g.version : '';
  id.hidden = !g.title_id; id.textContent = g.title_id || '';
  const path = $('#path');
  path.textContent = g.path ? '\u200e' + g.path : 'Not chosen yet';
  path.title = g.path || '';
  const art = $('#art');
  if (g.icon) { art.style.backgroundImage = `url("${g.icon}")`; art.classList.add('on'); }
  else art.classList.remove('on');
}
function renderCache(c) {
  $('#cachesize').textContent = mb(c.bytes);
  const tag = $('#cachetag');
  tag.textContent = c.bytes === 0 ? 'Empty' : c.stale ? 'Rebuild' : c.warm ? 'Warm' : 'Building';
  tag.className = 'tag ' + (c.warm ? 'warm' : 'cold');
  $('#cachebar').style.width = (c.stale ? 0 : Math.min(100, c.bytes / (150 * 1024 * 1024) * 100)) + '%';
  $('#cachehint').textContent = c.stale
    ? 'From an older build: it is rebuilt on the next start, so expect stutter once.'
    : c.warm ? 'Shaders are compiled. It keeps growing as you see new scenes.'
    : 'First arena load will stutter while shaders compile.';
}
function renderSaves(list) {
  $('#savecount').textContent = list.length ? list.length : 'None';
  $('#savelist').textContent = list.length ? list.join(', ') : 'Saves appear here after you play.';
}
function renderRun(run) {
  const play = $('#play'), label = $('#playlabel'), sub = $('#playsub'), pill = $('#status');
  const gameOk = state.game.ok && state.emulator;
  play.classList.toggle('running', run.running);
  play.classList.toggle('ready', gameOk && !run.running);
  play.disabled = run.running || !gameOk;
  if (run.running) {
    label.textContent = 'In game · ' + clock(run.elapsed);
    sub.textContent = 'Close the game window to come back here.';
    pill.className = 'pill live';
    $('span', pill).textContent = 'Playing';
  } else {
    label.textContent = 'Play';
    sub.textContent = !state.emulator ? 'kyty_emulator.exe is not next to Faceoff.'
      : !state.game.ok ? 'Choose your game folder first.'
      : state.cache.warm ? 'Ready when you are.' : 'First start: the first arena load stutters while shaders compile.';
    renderGame(state.game);
  }
  const crashed = !run.running && run.last_exit !== null && run.last_exit !== 0;
  $('#banner').hidden = !crashed;
  if (crashed) $('#bannertext').textContent = `The game stopped with code ${run.last_exit}. Keep play_log.txt for a bug report.`;
}
function render() {
  $('#ver').textContent = 'v' + state.version;
  renderGame(state.game);
  renderSettings(state.settings);
  renderCache(state.cache);
  renderSaves(state.saves);
  renderRun(state.run);
}

/* ---------- polling while the game runs ---------- */
function startPolling() {
  clearInterval(pollTimer);
  pollTimer = setInterval(async () => {
    const run = await api.run_state();
    state.run = run;
    if (!run.running) {
      clearInterval(pollTimer);
      state = await api.state();
      render();
      return;
    }
    renderRun(run);
  }, 1000);
}

/* ---------- wiring ---------- */
function wire() {
  $$('.tab').forEach(t => t.addEventListener('click', () => showTab(t.dataset.tab)));
  $$('.seg').forEach(seg => $$('button', seg).forEach(b => b.addEventListener('click', () => {
    if (b.classList.contains('on')) return;
    const name = seg.dataset.setting;
    let v = b.dataset.v;
    if (name === 'fullscreen') v = v === 'true';
    if (name === 'scale') v = parseFloat(v);
    setSeg(seg, b.dataset.v);
    save(name, v);
  })));
  $('#trophies').addEventListener('click', e => {
    const on = e.currentTarget.getAttribute('aria-checked') !== 'true';
    e.currentTarget.setAttribute('aria-checked', on);
    save('trophies', on);
  });
  $('#browse').addEventListener('click', async () => {
    const info = await api.pick_folder();
    if (!info) return;
    if (!info.ok) { toast(info.status + '. Pick the folder that holds eboot.bin.', true); return; }
    state = await api.state();
    render();
    toast('Game found: ' + info.title + (info.version ? ' v' + info.version : ''));
  });
  $('#play').addEventListener('click', async () => {
    const r = await api.play();
    if (!r.ok) { toast(r.error, true); return; }
    state.run = await api.run_state();
    renderRun(state.run);
    startPolling();
  });
  $$('[data-open]').forEach(b => b.addEventListener('click', async () => {
    if (!(await api.open(b.dataset.open))) toast('Nothing there yet.', true);
  }));
  $('#clearcache').addEventListener('click', () => { $('#modal').hidden = false; });
  $('#modalno').addEventListener('click', () => { $('#modal').hidden = true; });
  $('#modalyes').addEventListener('click', async () => {
    $('#modal').hidden = true;
    const r = await api.clear_cache();
    if (r.ok) { state.cache = r.cache; renderCache(r.cache); renderRun(state.run); toast('Shader cache cleared'); }
    else toast(r.error, true);
  });
  window.addEventListener('resize', () => { moveTabBar(); $$('.seg').forEach(placeThumb); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') $('#modal').hidden = true; });
}

async function boot(bridge) {
  api = bridge;
  state = await api.state();
  render();
  await document.fonts.ready;
  moveTabBar();
  $$('.seg').forEach(placeThumb);
  if (state.run.running) startPolling();
}

/* ---------- demo stand-in (plain browser only) ---------- */
function demoApi() {
  const s = {
    version: '1.0.0', folder: 'D:\\Games\\KytyPS5-nhl27-enhanced-rc4', emulator: true,
    game: { ok: true, status: 'Ready', path: 'D:\\PS5\\NHL27\\PPSA34063-app0', title: 'NHL 27', version: '01.003.001', title_id: 'PPSA34063', icon: null },
    settings: { resolution: 'R2560X1440', fullscreen: false, scale: 0.6667, trophies: true },
    cache: { bytes: 113 * 1024 * 1024, files: 3, warm: true }, saves: ['Profile0', 'ThreeOnThree0'],
    run: { running: false, elapsed: 0, last_exit: null, error: null },
  };
  let start = 0;
  return {
    state: async () => JSON.parse(JSON.stringify(s)),
    run_state: async () => ({ ...s.run, elapsed: s.run.running ? Math.floor((Date.now() - start) / 1000) : 0 }),
    save_setting: async (n, v) => { s.settings[n] = v; return { ok: true, settings: { ...s.settings } }; },
    pick_folder: async () => s.game,
    play: async () => { s.run.running = true; start = Date.now(); setTimeout(() => { s.run.running = false; s.run.last_exit = 0; }, 8000); return { ok: true }; },
    clear_cache: async () => { s.cache = { bytes: 0, files: 0, warm: false }; return { ok: true, cache: s.cache }; },
    open: async () => true,
  };
}

wire();
if (window.pywebview && window.pywebview.api && window.pywebview.api.state) boot(window.pywebview.api);
else {
  let booted = false;
  window.addEventListener('pywebviewready', () => { if (!booted) { booted = true; boot(window.pywebview.api); } });
  setTimeout(() => { if (!booted && !window.pywebview) { booted = true; boot(demoApi()); } }, 1500);
}
