const canvas = document.getElementById('kd-canvas');
const ctx    = canvas.getContext('2d');

const dark = matchMedia('(prefers-color-scheme: dark)').matches;

// One distinct colour per dimension (up to 20). disc % DISC_COLS.length gives the colour.
const DISC_COLS = [
  '#378ADD', // dim 0  — blue
  '#1D9E75', // dim 1  — teal
  '#D85A30', // dim 2  — coral  (reused as query colour only when k≥3)
  '#BA7517', // dim 3  — amber
  '#9370DB', // dim 4  — purple
  '#E05C8A', // dim 5  — pink
  '#3BAA6E', // dim 6  — green
  '#E0803A', // dim 7  — orange
  '#5BADD4', // dim 8  — sky
  '#C44D4D', // dim 9  — red
  '#7B68EE', // dim 10 — slate-purple
  '#4DBEAA', // dim 11 — mint
  '#D4A017', // dim 12 — gold
  '#A05C8A', // dim 13 — mauve
  '#5D8AA8', // dim 14 — air-force blue
  '#7EA87E', // dim 15 — sage
  '#C07858', // dim 16 — copper
  '#6699CC', // dim 17 — cornflower
  '#CC6688', // dim 18 — rose
  '#88AA44', // dim 19 — olive
];

const COL = {
  bg:      dark ? '#1a1a18'                : '#fafaf8',
  grid:    dark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)',
  point:   '#378ADD',
  query:   '#D85A30',
  pruned:  dark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)',
  visited: 'rgba(186,117,23,0.08)',
  region:  'rgba(186,117,23,0.15)',
  regionB: '#BA7517',
  text:    dark ? '#c2c0b6' : '#3d3d3a',
};

// ════════════════════════════════════════════════════════════════════════
//  KDNode — mirrors Python's `node` class
// ════════════════════════════════════════════════════════════════════════
class KDNode {
  constructor(key) {
    this.key   = key;   // Float array, length = k
    this.loson = null;
    this.hison = null;
    this.disc  = 0;
  }
}

// ════════════════════════════════════════════════════════════════════════
//  KDTree — mirrors Python's KDtree class, method for method
// ════════════════════════════════════════════════════════════════════════
class KDTree {
  constructor(k) {
    this.root = null;
    this.k    = k;
  }

  successor(node, Q) {
    for (let i = 0; i < this.k; i++) {
      const sdisc = (Q.disc + i) % this.k;
      if (node.key[sdisc] < Q.key[sdisc]) return 'LOWER';
      if (node.key[sdisc] > Q.key[sdisc]) return 'HIGHER';
    }
    return 'EQUAL';
  }

  insert(node) {
    if (this.root === null) { this.root = node; node.disc = 0; return; }
    let Q = this.root;
    while (true) {
      const r = this.successor(node, Q);
      if (r === 'HIGHER') {
        node.disc = (Q.disc + 1) % this.k;
        if (Q.hison === null) { Q.hison = node; return; }
        Q = Q.hison;
      } else if (r === 'LOWER') {
        node.disc = (Q.disc + 1) % this.k;
        if (Q.loson === null) { Q.loson = node; return; }
        Q = Q.loson;
      } else { return; }
    }
  }

  exactSearch(target) {
    let Q = this.root;
    while (Q !== null) {
      const r = this.successor(target, Q);
      if (r === 'EQUAL')  return Q;
      if (r === 'HIGHER') Q = Q.hison;
      else                Q = Q.loson;
    }
    return null;
  }

  partialSearch(constraints, Q = null, result = []) {
    if (Q === null) { Q = this.root; if (Q === null) return []; }
    let match = true;
    for (const [dim, val] of Object.entries(constraints))
      if (Q.key[dim] != val) { match = false; break; }
    if (match) result.push(Q);
    const disc = Q.disc;
    if (disc in constraints) {
      if      (Q.key[disc] < constraints[disc]) { if (Q.hison) this.partialSearch(constraints, Q.hison, result); }
      else if (Q.key[disc] > constraints[disc]) { if (Q.loson) this.partialSearch(constraints, Q.loson, result); }
      else {
        if (Q.hison) this.partialSearch(constraints, Q.hison, result);
        if (Q.loson) this.partialSearch(constraints, Q.loson, result);
      }
    } else {
      if (Q.hison) this.partialSearch(constraints, Q.hison, result);
      if (Q.loson) this.partialSearch(constraints, Q.loson, result);
    }
    return result;
  }

  regionQuery(upper, lower) {
    if (this.root === null) return [];
    const lowerB = Array(this.k).fill(-Infinity);
    const upperB = Array(this.k).fill( Infinity);
    const result = [];
    this.regionSearch(this.root, lower, upper, lowerB, upperB, result);
    return result;
  }

  regionSearch(P, lowerR, upperR, lowerB, upperB, result) {
    if (P === null) return;
    if (this.inRegion(P, lowerR, upperR)) result.push(P);
    const J = P.disc;
    if (P.loson !== null) {
      const ll = [...lowerB], lu = [...upperB]; lu[J] = P.key[J];
      if (this.boundsInterRegion(ll, lu, lowerR, upperR))
        this.regionSearch(P.loson, lowerR, upperR, ll, lu, result);
    }
    if (P.hison !== null) {
      const rl = [...lowerB], ru = [...upperB]; rl[J] = P.key[J];
      if (this.boundsInterRegion(rl, ru, lowerR, upperR))
        this.regionSearch(P.hison, lowerR, upperR, rl, ru, result);
    }
  }

  inRegion(P, lower, upper) {
    for (let i = 0; i < P.key.length; i++)
      if (P.key[i] < lower[i] || P.key[i] > upper[i]) return false;
    return true;
  }

  boundsInterRegion(lowerB, upperB, lowerR, upperR) {
    for (let i = 0; i < lowerB.length; i++) {
      if (lowerB[i] > upperR[i]) return false;
      if (upperB[i] < lowerR[i]) return false;
    }
    return true;
  }

  distance(node, P) {
    let r = 0;
    for (let i = 0; i < this.k; i++) r += (node.key[i] - P[i]) ** 2;
    return r;
  }

  nearestNeighbour1(T) {
    if (this.root === null) return { node: null, visited: [], pruned: [] };
    let Bnode = this.root, Bdist = Infinity;
    const visited = [], pruned = [];
    [Bnode, Bdist] = this._nn1(this.root, T, Bnode, Bdist, visited, pruned);
    return { node: Bnode, visited, pruned };
  }

  _nn1(P, T, Bnode, Bdist, visited, pruned) {
    if (P === null) return [Bnode, Bdist];
    const d = this.distance(P, T);
    if (d < Bdist) { Bnode = P; Bdist = d; }
    visited.push(P);
    const J = P.disc;
    const [prim, sec] = T[J] < P.key[J] ? [P.loson, P.hison] : [P.hison, P.loson];
    if (prim) [Bnode, Bdist] = this._nn1(prim, T, Bnode, Bdist, visited, pruned);
    if ((T[J] - P.key[J]) ** 2 < Bdist) {
      [Bnode, Bdist] = this._nn1(sec, T, Bnode, Bdist, visited, pruned);
    } else {
      this._leaves(sec, pruned);
    }
    return [Bnode, Bdist];
  }

  nearestNeighbour2(T) {
    if (this.root === null) return { node: null, visited: [], pruned: [] };
    const lowerB = Array(this.k).fill(-Infinity);
    const upperB = Array(this.k).fill( Infinity);
    let Bnode = this.root, Bdist = Infinity;
    const visited = [], pruned = [];
    [Bnode, Bdist] = this._nn2(this.root, T, Bnode, Bdist, lowerB, upperB, visited, pruned);
    return { node: Bnode, visited, pruned };
  }

  _nn2(P, T, Bnode, Bdist, lowerB, upperB, visited, pruned) {
    if (P === null) return [Bnode, Bdist];
    const d = this.distance(P, T);
    if (d < Bdist) { Bnode = P; Bdist = d; }
    visited.push(P);
    const J = P.disc;
    let prim, sec, pl, pu, sl, su;
    if (T[J] < P.key[J]) {
      prim = P.loson; sec = P.hison;
      pl = [...lowerB]; pu = [...upperB]; pu[J] = P.key[J];
      sl = [...lowerB]; su = [...upperB]; sl[J] = P.key[J];
    } else {
      prim = P.hison; sec = P.loson;
      pl = [...lowerB]; pu = [...upperB]; pl[J] = P.key[J];
      sl = [...lowerB]; su = [...upperB]; su[J] = P.key[J];
    }
    if (prim) [Bnode, Bdist] = this._nn2(prim, T, Bnode, Bdist, pl, pu, visited, pruned);
    if (sec) {
      if (this.distanceToBox(T, sl, su) < Bdist) {
        [Bnode, Bdist] = this._nn2(sec, T, Bnode, Bdist, sl, su, visited, pruned);
      } else {
        this._leaves(sec, pruned);
      }
    }
    return [Bnode, Bdist];
  }

  distanceToBox(T, lowerB, upperB) {
    let minD = 0;
    for (let i = 0; i < lowerB.length; i++) {
      if      (T[i] < lowerB[i]) minD += (T[i] - lowerB[i]) ** 2;
      else if (T[i] > upperB[i]) minD += (T[i] - upperB[i]) ** 2;
    }
    return minD;
  }

  deleteNode(target, Q = null, parent = null, side = null) {
    if (Q === null) { Q = this.root; if (Q === null) return; }
    const r = this.successor(target, Q);
    if (r === 'HIGHER') { if (Q.hison) this.deleteNode(target, Q.hison, Q, 'hison'); return; }
    if (r === 'LOWER')  { if (Q.loson) this.deleteNode(target, Q.loson, Q, 'loson'); return; }
    if (!Q.loson && !Q.hison) {
      if (!parent) this.root = null;
      else if (side === 'hison') parent.hison = null;
      else parent.loson = null;
      return;
    }
    if (Q.hison) {
      const rep = this.findMin(Q.hison, Q.disc);
      Q.key = [...rep.key];
      this.deleteNode(rep, Q.hison, Q, 'hison');
    } else {
      const rep = this.findMax(Q.loson, Q.disc);
      Q.key = [...rep.key];
      this.deleteNode(rep, Q.loson, Q, 'loson');
      Q.hison = Q.loson; Q.loson = null;
    }
  }

  findMin(Q, disc) {
    if (!Q) return null;
    if (Q.disc === disc) { if (!Q.loson) return Q; return this.findMin(Q.loson, disc); }
    const c = [Q];
    const l = this.findMin(Q.loson, disc), r = this.findMin(Q.hison, disc);
    if (l) c.push(l); if (r) c.push(r);
    return c.reduce((a, b) => a.key[disc] <= b.key[disc] ? a : b);
  }

  findMax(Q, disc) {
    if (!Q) return null;
    if (Q.disc === disc) { if (!Q.hison) return Q; return this.findMax(Q.hison, disc); }
    const c = [Q];
    const l = this.findMax(Q.loson, disc), r = this.findMax(Q.hison, disc);
    if (l) c.push(l); if (r) c.push(r);
    return c.reduce((a, b) => a.key[disc] >= b.key[disc] ? a : b);
  }

  optimise() {
    if (!this.root) return;
    const all = [];
    this._flatten(this.root, all);
    for (const n of all) { n.loson = null; n.hison = null; n.disc = 0; }
    this.root = this._buildBalanced(all, 0, 0, all.length);
  }

  _flatten(Q, arr) {
    const stack = [Q];
    while (stack.length) {
      const n = stack.pop();
      if (!n) continue;
      arr.push(n);
      stack.push(n.loson);
      stack.push(n.hison);
    }
  }

  _buildBalanced(nodes, depth, lo, hi) {
    if (lo >= hi) return null;
    const disc = depth % this.k;
    nodes.slice(lo, hi).sort((a, b) => a.key[disc] - b.key[disc])
         .forEach((n, i) => { nodes[lo + i] = n; });
    const mid = Math.floor((lo + hi) / 2);
    const med = nodes[mid];
    med.disc  = disc;
    med.loson = this._buildBalanced(nodes, depth + 1, lo, mid);
    med.hison = this._buildBalanced(nodes, depth + 1, mid + 1, hi);
    return med;
  }

  _leaves(node, arr) {
    if (!node) return;
    arr.push(node);
    this._leaves(node.loson, arr);
    this._leaves(node.hison, arr);
  }

  allNodes() {
    const pts = [];
    this._flatten(this.root, pts);   // reuses iterative flatten
    return pts;
  }

  depth() {
    const d = n => !n ? 0 : 1 + Math.max(d(n.loson), d(n.hison));
    return d(this.root);
  }
}

// ════════════════════════════════════════════════════════════════════════
//  Visualiser state
// ════════════════════════════════════════════════════════════════════════
let currentK       = 2;
let tree           = new KDTree(2);
let mode           = 'insert';
let nnMode         = 'nn2';
let nnQuery        = null;
let nnResult       = null;
let nnVisited      = [];
let nnPruned       = [];
let regionStart    = null;
let regionEnd      = null;
let regionDragging = false;
let regionResults  = [];

// ── k slider ─────────────────────────────────────────────────────────
function onKSlider(v) {
  document.getElementById('k-label').textContent = `k = ${v}`;
}

function applyK() {
  const newK = parseInt(document.getElementById('k-slider').value, 10);
  currentK = newK;
  tree = new KDTree(newK);
  nnQuery = null; nnResult = null; nnVisited = []; nnPruned = [];
  regionStart = null; regionEnd = null; regionResults = [];
  document.getElementById('stat-k').textContent = newK;
  updateLegend();
  updateCanvasVisibility();
  updateStats();
  draw();
  document.getElementById('info-text').textContent =
    `Tree rebuilt with k = ${newK}. ${newK > 2 ? 'Canvas hidden — bulk insert and run queries to see timing.' : 'Click to add points.'}`;
}

function updateCanvasVisibility() {
  const is2D = currentK === 2;
  canvas.style.display        = is2D ? 'block' : 'none';
  document.getElementById('hd-panel').style.display = is2D ? 'none'  : 'block';
  document.getElementById('hd-k').textContent  = currentK;
  document.getElementById('hd-k2').textContent = currentK;
  // insert mode only meaningful in 2D
  if (!is2D && mode === 'insert') setMode('nn');
  document.getElementById('btn-insert').style.display = is2D ? '' : 'none';
}

function updateLegend() {
  const box = document.getElementById('legend-lines');
  box.innerHTML = '';
  const show = Math.min(currentK, 6); // cap legend at 6 entries
  for (let d = 0; d < show; d++) {
    const col = DISC_COLS[d % DISC_COLS.length];
    const row = document.createElement('div');
    row.className = 'legend-row';
    row.innerHTML =
      `<div class="legend-line" style="background:${col}"></div> dim ${d} split`;
    box.appendChild(row);
  }
  if (currentK > 6) {
    const more = document.createElement('div');
    more.className = 'legend-row';
    more.style.color = '#888';
    more.textContent = `+ ${currentK - 6} more dimensions…`;
    box.appendChild(more);
  }
}

// ── Mode switching ────────────────────────────────────────────────────
function setMode(m) {
  mode = m;
  nnQuery = null; nnResult = null; nnVisited = []; nnPruned = [];
  regionStart = null; regionEnd = null; regionResults = [];
  document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
  const btn = document.getElementById('btn-' + m);
  if (btn) btn.classList.add('active');
  const texts = {
    insert: 'Click the canvas to add points. Uses insert() with successor() routing.',
    nn:     'Click the canvas (2D) or use bulk insert then click, to run nearest neighbour. Toggle NN1 vs NN2.',
    region: 'Click and drag a region on the canvas (2D), or just bulk insert to see timing stats.',
  };
  document.getElementById('info-text').textContent = texts[m] || '';
  updateNNToggle();
  draw();
}

function setNNMode(m) {
  nnMode  = m;
  nnQuery = null; nnResult = null; nnVisited = []; nnPruned = [];
  updateNNToggle();
  draw();
}

function updateNNToggle() {
  const wrap = document.getElementById('nn-toggle-wrap');
  if (wrap) wrap.style.display = mode === 'nn' ? 'flex' : 'none';
  document.querySelectorAll('.nn-btn').forEach(b => b.classList.remove('active'));
  const btn = document.getElementById('btn-' + nnMode);
  if (btn) btn.classList.add('active');
}

function clearTree() {
  tree = new KDTree(currentK);
  nnQuery = null; nnResult = null; nnVisited = []; nnPruned = [];
  regionStart = null; regionEnd = null; regionResults = [];
  hideTimingBar();
  updateStats();
  draw();
  document.getElementById('info-text').textContent = 'Tree cleared.';
}

function optimiseTree() {
  const t0 = performance.now();
  tree.optimise();
  const ms = performance.now() - t0;
  draw();
  showTimingBar([{ label: 'optimise()', ms }]);
  document.getElementById('info-text').textContent =
    `Tree rebalanced with optimise(). Took ${ms.toFixed(3)} ms.`;
}

// ── Timing bar ────────────────────────────────────────────────────────
function showTimingBar(items) {
  // items: [{ label, ms }, ...]
  const bar = document.getElementById('timing-bar');
  bar.style.display = 'flex';
  bar.innerHTML = items.map(it => {
    const ms = typeof it.ms === 'number' ? it.ms : 0;
    const disp = ms < 0.001 ? '<0.001 ms' : ms < 1 ? `${ms.toFixed(3)} ms` : `${ms.toFixed(2)} ms`;
    return `<div class="timing-item">
      <span class="timing-label">${it.label}</span>
      <span class="timing-value">${disp}</span>
    </div>`;
  }).join('');
}

function hideTimingBar() {
  document.getElementById('timing-bar').style.display = 'none';
}

// ── Canvas coordinate helpers ─────────────────────────────────────────
function canvasXY(e) {
  const r  = canvas.getBoundingClientRect();
  const sx = canvas.width  / r.width;
  const sy = canvas.height / r.height;
  const cx = e.clientX ?? e.touches?.[0].clientX;
  const cy = e.clientY ?? e.touches?.[0].clientY;
  return [(cx - r.left) * sx, (cy - r.top) * sy];
}

// Make a full k-dimensional key, using x/y for dims 0/1 and random for the rest
function makeKey(x, y) {
  const key = [x, y];
  for (let i = 2; i < currentK; i++) key.push(Math.random() * 1000);
  return key;
}

// ── Mouse events ──────────────────────────────────────────────────────
canvas.addEventListener('mousedown', e => {
  const [x, y] = canvasXY(e);
  if (mode === 'insert') {
    const t0 = performance.now();
    tree.insert(new KDNode(makeKey(x, y)));
    const ms = performance.now() - t0;
    updateStats();
    draw();
    showTimingBar([{ label: 'insert()', ms }]);
  } else if (mode === 'nn') {
    nnQuery = makeKey(x, y);
    runNN();
    draw();
  } else if (mode === 'region') {
    regionStart = [x, y]; regionEnd = [x, y];
    regionDragging = true; regionResults = [];
    draw();
  }
});

canvas.addEventListener('mousemove', e => {
  if (mode === 'region' && regionDragging) { regionEnd = canvasXY(e); draw(); }
});

canvas.addEventListener('mouseup', () => {
  if (mode === 'region' && regionDragging) { regionDragging = false; runRegion(); draw(); }
});

canvas.addEventListener('mouseleave', () => {
  if (mode === 'region' && regionDragging) { regionDragging = false; runRegion(); draw(); }
});

// ── Queries ───────────────────────────────────────────────────────────
function runNN() {
  if (!tree.root || !nnQuery) return;
  const t0  = performance.now();
  const res = nnMode === 'nn1' ? tree.nearestNeighbour1(nnQuery) : tree.nearestNeighbour2(nnQuery);
  const ms  = performance.now() - t0;
  nnResult  = res.node;
  nnVisited = res.visited;
  nnPruned  = res.pruned;
  const total  = nnVisited.length + nnPruned.length;
  const method = nnMode === 'nn1' ? 'NN1 (split-plane)' : 'NN2 (bounding-box)';
  showTimingBar([
    { label: method,    ms },
    { label: 'Visited', ms: nnVisited.length + ' nodes' },
    { label: 'Pruned',  ms: nnPruned.length  + ' nodes' },
    { label: '% explored', ms: Math.round((1 - nnPruned.length / Math.max(total, 1)) * 100) + '%' },
  ].map(it => typeof it.ms === 'string' ? { label: it.label, ms: null, disp: it.ms } : it));

  // Custom render for mixed timing/count bar
  const bar = document.getElementById('timing-bar');
  bar.style.display = 'flex';
  bar.innerHTML = [
    { label: method,       val: ms < 0.001 ? '<0.001 ms' : ms < 1 ? ms.toFixed(3) + ' ms' : ms.toFixed(2) + ' ms' },
    { label: 'Visited',    val: nnVisited.length + ' nodes' },
    { label: 'Pruned',     val: nnPruned.length  + ' nodes' },
    { label: '% explored', val: Math.round((1 - nnPruned.length / Math.max(total, 1)) * 100) + '%' },
  ].map(it => `<div class="timing-item">
    <span class="timing-label">${it.label}</span>
    <span class="timing-value">${it.val}</span>
  </div>`).join('');

  document.getElementById('info-text').textContent =
    `${method}: ${nnVisited.length} visited, ${nnPruned.length} pruned.`;
}

function runRegion() {
  if (!regionStart || !regionEnd || !tree.root) return;
  const x0 = Math.min(regionStart[0], regionEnd[0]);
  const x1 = Math.max(regionStart[0], regionEnd[0]);
  const y0 = Math.min(regionStart[1], regionEnd[1]);
  const y1 = Math.max(regionStart[1], regionEnd[1]);
  // For k>2 dims beyond x/y are unconstrained: use ±Infinity
  const lower = makeKey(x0, y0).map((v, i) => i < 2 ? v : -Infinity);
  const upper = makeKey(x1, y1).map((v, i) => i < 2 ? v :  Infinity);
  const t0 = performance.now();
  regionResults = tree.regionQuery(upper, lower);
  const ms = performance.now() - t0;
  const all = tree.allNodes().length;

  const bar = document.getElementById('timing-bar');
  bar.style.display = 'flex';
  bar.innerHTML = [
    { label: 'regionQuery()', val: ms < 0.001 ? '<0.001 ms' : ms < 1 ? ms.toFixed(3) + ' ms' : ms.toFixed(2) + ' ms' },
    { label: 'Found',         val: regionResults.length + ' points' },
    { label: 'Total',         val: all + ' points' },
  ].map(it => `<div class="timing-item">
    <span class="timing-label">${it.label}</span>
    <span class="timing-value">${it.val}</span>
  </div>`).join('');

  document.getElementById('info-text').textContent =
    `Found ${regionResults.length} / ${all} points in region.`;
}

// ── Bulk insert ───────────────────────────────────────────────────────
function bulkInsert() {
  const n = parseInt(document.getElementById('bulk-n').value, 10);
  if (!n || n < 1) return;
  if (canvas.width === 0) canvas.width = canvas.offsetWidth;
  const W = canvas.width  || 800;
  const H = canvas.height || 460;
  const CHUNK = 2000;
  let inserted = 0;
  const t0 = performance.now();

  function insertChunk() {
    const end = Math.min(inserted + CHUNK, n);
    for (let i = inserted; i < end; i++)
      tree.insert(new KDNode(makeKey(Math.random() * W, Math.random() * H)));
    inserted = end;
    updateStats();
    if (inserted < n) {
      document.getElementById('info-text').textContent = `Inserting… ${inserted} / ${n}`;
      requestAnimationFrame(insertChunk);
    } else {
      const ms = performance.now() - t0;
      draw();
      showTimingBar([
        { label: `insert() ×${n}`, ms },
        { label: 'Per insert',     ms: ms / n },
      ]);
      document.getElementById('info-text').textContent =
        `Inserted ${n} points in ${ms < 1 ? ms.toFixed(3) : ms.toFixed(2)} ms ` +
        `(${(ms / n).toFixed(4)} ms each).`;
    }
  }
  insertChunk();
}

// ── Drawing ───────────────────────────────────────────────────────────
function drawSplits(node, x0, y0, x1, y1) {
  if (!node) return;
  // Only draw splits for dimensions 0 (x) and 1 (y) — those map to the canvas axes
  const disc = node.disc;
  const col  = DISC_COLS[disc % DISC_COLS.length];

  if (disc === 0) {
    const px = node.key[0];
    ctx.strokeStyle = col; ctx.lineWidth = 1; ctx.setLineDash([]);
    ctx.beginPath(); ctx.moveTo(px, y0); ctx.lineTo(px, y1); ctx.stroke();
    drawSplits(node.loson, x0, y0, px, y1);
    drawSplits(node.hison, px, y0, x1, y1);
  } else if (disc === 1) {
    const py = node.key[1];
    ctx.strokeStyle = col; ctx.lineWidth = 1; ctx.setLineDash([]);
    ctx.beginPath(); ctx.moveTo(x0, py); ctx.lineTo(x1, py); ctx.stroke();
    drawSplits(node.loson, x0, y0, x1, py);
    drawSplits(node.hison, x0, py, x1, y1);
  } else {
    // Higher dimensions: pass bounds through unchanged (split not visible in 2D)
    drawSplits(node.loson, x0, y0, x1, y1);
    drawSplits(node.hison, x0, y0, x1, y1);
  }
}

function dist2screen(a, b) {
  return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2;
}

function draw() {
  if (currentK > 2) return; // no canvas in high-D mode
  canvas.width = canvas.offsetWidth;
  ctx.fillStyle = COL.bg;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.strokeStyle = COL.grid; ctx.lineWidth = 0.5;
  for (let x = 0; x < canvas.width;  x += 40) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke(); }
  for (let y = 0; y < canvas.height; y += 40) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y);  ctx.stroke(); }

  const pts = tree.allNodes();
  if (pts.length > 1) drawSplits(tree.root, 0, 0, canvas.width, canvas.height);

  if (mode === 'nn') {
    nnPruned.forEach(n => {
      ctx.fillStyle = COL.pruned;
      ctx.beginPath(); ctx.arc(n.key[0], n.key[1], 14, 0, Math.PI * 2); ctx.fill();
    });
    nnVisited.forEach(n => {
      ctx.fillStyle = COL.visited;
      ctx.beginPath(); ctx.arc(n.key[0], n.key[1], 14, 0, Math.PI * 2); ctx.fill();
    });
    if (nnResult && nnQuery) {
      const r = Math.sqrt(dist2screen(nnQuery, nnResult.key));
      ctx.strokeStyle = COL.query; ctx.lineWidth = 1; ctx.setLineDash([4, 4]);
      ctx.beginPath(); ctx.arc(nnQuery[0], nnQuery[1], r, 0, Math.PI * 2); ctx.stroke();
      ctx.setLineDash([]);
      ctx.strokeStyle = COL.query; ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.moveTo(nnQuery[0], nnQuery[1]); ctx.lineTo(nnResult.key[0], nnResult.key[1]); ctx.stroke();
    }
  }

  if (mode === 'region' && regionStart && regionEnd) {
    const x0 = Math.min(regionStart[0], regionEnd[0]), y0 = Math.min(regionStart[1], regionEnd[1]);
    const w  = Math.abs(regionEnd[0] - regionStart[0]),  h  = Math.abs(regionEnd[1] - regionStart[1]);
    ctx.fillStyle = COL.region; ctx.fillRect(x0, y0, w, h);
    ctx.strokeStyle = COL.regionB; ctx.lineWidth = 1.5; ctx.setLineDash([5, 3]);
    ctx.strokeRect(x0, y0, w, h); ctx.setLineDash([]);
  }

  const regionKeys = new Set(regionResults.map(n => n.key.join(',')));
  pts.forEach(n => {
    const isNN     = nnResult && n === nnResult;
    const inRegion = regionKeys.has(n.key.join(','));
    ctx.fillStyle   = (isNN || inRegion) ? COL.query : COL.point;
    ctx.beginPath(); ctx.arc(n.key[0], n.key[1], isNN || inRegion ? 6 : 5, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.7)'; ctx.lineWidth = 1.5; ctx.stroke();
  });

  if (mode === 'nn' && nnQuery) {
    ctx.fillStyle = COL.query;
    ctx.beginPath(); ctx.arc(nnQuery[0], nnQuery[1], 5, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = '#fff'; ctx.lineWidth = 2; ctx.stroke();
    ctx.fillStyle = COL.text; ctx.font = '11px sans-serif';
    ctx.fillText('query', nnQuery[0] + 8, nnQuery[1] - 6);
  }
}

function updateStats() {
  const pts = tree.allNodes();
  document.getElementById('stat-n').textContent = pts.length;
  document.getElementById('stat-d').textContent = tree.depth();
  document.getElementById('stat-k').textContent = currentK;
}

// ── Init ──────────────────────────────────────────────────────────────
updateLegend();
updateCanvasVisibility();
updateNNToggle();
window.addEventListener('resize', () => draw());
draw();
