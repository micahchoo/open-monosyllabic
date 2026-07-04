"use strict";
// Open Monosyllabic — seed Explorer. Phases 2-4 on seed data:
// two-level heatmap + Equal-Earth map, honesty-first (tier composition, never a
// bare count, generated never hidden), Form-detail sheet with real audio,
// filters, compare, About + Sources.

const ONSET_ORDER = ["none", "nasal", "stop", "implosive", "affricate", "fricative", "liquid", "glide", "click", "other"];
const ONSET_LABEL = { none: "∅", nasal: "nasal", stop: "stop", implosive: "implos.", affricate: "affric.", fricative: "fric.", liquid: "liquid", glide: "glide", click: "click", other: "other" };
const NUC_ORDER = ["i", "e", "ə", "a", "o", "u", "diphthong", "other"];
const NUC_LABEL = { i: "i", e: "e", "ə": "ə", a: "a", o: "o", u: "u", diphthong: "V͡V", other: "–" };
const TIER = ["curated", "mined", "generated"];
const TIER_GLYPH = ["●", "◐", "○"];

// SK-63 heatmap ramp: color-mix(in oklab, --data N%, --panel) at 15/35/55/78/100%,
// precomputed to literal hexes (no runtime color-mix in a no-build static site).
// Numerals stay dark through step 3; they invert only on the deepest step (.deep).
const RAMP = ["#DDE4E2", "#C0D2D3", "#98B8BD", "#62909D", "#2F5E6C"];
const rampStep = r => r < 0.5 ? 0 : r < 0.9 ? 1 : r < 1.3 ? 2 : r < 1.8 ? 3 : 4;
// Tier composition with glyphs in their tier colors — the text twin of the strip.
const tierGlyphHTML = i => `<b class="g-${TIER[i]}">${TIER_GLYPH[i]}</b>`;
const tierCompHTML = comp => comp.map((c, i) => c ? `${c}${tierGlyphHTML(i)}` : "").filter(Boolean).join(" ");
// Calibration-strip segments: curated/mined solid, generated hollow (unfilled).
// widthPct = this row's share of the list maximum; comp = [curated, mined, generated].
// comp === all zeros → no segments, but the hairline track still draws: absence is drawn.
function stripSegs(comp, widthPct) {
  const total = comp[0] + comp[1] + comp[2];
  if (!total) return "";
  const cls = ["s-cur", "s-min", "s-gen"];
  return comp.map((c, i) => c ? `<i class="${cls[i]}" style="width:${(widthPct * c / total).toFixed(2)}%"></i>` : "").join("");
}

let CORE, FORMS = {}, AUDIO = {}, CONCEPTS = {}, BASE = "", CHUNKED = false;

// DataStore contract (§10): blob build preloads forms.json; chunked build fetches
// per-shape chunks on demand. slugOf matches oms/bake._slug.
function slugOf(shape) { return "u" + [...shape].map(c => c.codePointAt(0).toString(16).padStart(4, "0")).join("-"); }
async function ensureShape(shape) {
  if (!CHUNKED || Object.values(FORMS).some(f => f.shape === shape)) return;
  try { Object.assign(FORMS, await (await fetch(`${BASE}/shape/${slugOf(shape)}.json`)).json()); } catch {}
}
async function loadConcept(ckey) {
  if (CONCEPTS[ckey]) return CONCEPTS[ckey];
  try { CONCEPTS[ckey] = await (await fetch(`${BASE}/concept/${ckey}.json`)).json(); } catch { CONCEPTS[ckey] = null; }
  return CONCEPTS[ckey];
}
const state = {
  onset: null, nuc: null, shape: null, concept: null, language: null, region: null, convMeaning: null,
  onsetOn: new Set(ONSET_ORDER), tierOn: new Set(TIER),
  pins: [], route: "meanings",
};

async function boot() {
  const cur = await (await fetch("../data/current.json")).json();
  BASE = `../data/${cur.dir || cur.version}`;
  CHUNKED = !!cur.chunked;
  CORE = await (await fetch(`${BASE}/core.json`)).json();
  FORMS = CHUNKED ? {} : await (await fetch(`${BASE}/forms.json`)).json();
  try { AUDIO = await (await fetch("audio/manifest.json")).json(); } catch { AUDIO = {}; }
  try { LAND = decodeLand(await (await fetch("land-110m.json")).json()); } catch { LAND = null; }
  document.getElementById("stamp").textContent =
    `data as of ${cur.version} · ${CORE.languages.length} languages · ${CORE.shapes.length} shapes` +
    (CHUNKED ? " (real datasets)" : " (seed)");
  document.getElementById("mstamp").textContent =
    `${(CORE.concepts || []).length} meanings · ${CORE.languages.length} languages`;
  document.getElementById("lstamp").textContent = `${CORE.languages.length} languages`;
  document.getElementById("rstamp").textContent =
    `${regionIndex().length} regions · ${CORE.languages.length} languages`;
  document.getElementById("convStamp").textContent = `${(CORE.concepts || []).length} meanings`;
  // the maker's plate (wide screens; per-view stamps cover the rest): version,
  // languages by best source tier, shapes — even the stamp carries composition
  const plateComp = [0, 0, 0];
  for (const e of langIndex()) if (e.shapes.length) plateComp[Math.min(...e.shapes.map(s => s.tier))]++;
  const plate = document.getElementById("navplate");
  plate.innerHTML = `data ${cur.version} · ${CORE.languages.length} languages (${tierCompHTML(plateComp)}) · ${CORE.shapes.length} shapes → sources`;
  plate.title = "languages counted at their best source tier; the remainder have no open monosyllables";
  plate.onclick = () => navigateTo("sources");
  document.getElementById("srcStamp").textContent =
    `data ${cur.version} · ${CORE.languages.length} languages · ${CORE.shapes.length} shapes · ${(CORE.sources || []).length} sources`;
  wireNav();
  renderMeanings();
  renderLanguages();
  renderRegions();
  renderConvMeanings();
  renderFilters();
  renderHeatmap();
  drawMap();
  renderAbout();
  renderSources();
  document.getElementById("conceptSearch").oninput = e => renderMeanings(e.target.value);
  document.getElementById("langSearch").oninput = e => renderLanguages(e.target.value);
  document.getElementById("convSearch").oninput = e => renderConvMeanings(e.target.value);
  document.getElementById("sheetClose").onclick = () => document.getElementById("sheet").classList.remove("open");
  // keyboard: every clickable row/cell/chip is focusable (tabindex); Enter activates.
  // Activation re-renders the container and destroys the focused node, so focus is
  // restored to the equivalent element (same container, same data-*) afterwards.
  document.addEventListener("keydown", e => {
    if (e.key !== "Enter") return;
    const t = document.activeElement;
    if (!t || !t.matches(".crow,.langrow,td.cell,.shape,.lshape,.chip,.wlink,.dothit")) return;
    e.preventDefault();
    const hostId = t.closest("[id]")?.id, ds = { ...t.dataset };
    t.click();
    setTimeout(() => {
      if (document.contains(t)) return;
      const host = hostId && document.getElementById(hostId);
      const keys = Object.keys(ds);
      if (!host || !keys.length) return;
      const twin = [...host.querySelectorAll("[tabindex]")]
        .find(el => keys.every(k => el.dataset[k] === ds[k]));
      twin?.focus();
    }, 0);
  });
  // deep links (shareable): #c=<meaning> · #l=<language> · #r=<region> · #v=<look-alike meaning>
  // Selections write history entries (writeHash); Back/Forward re-apply any hash
  // we didn't just write ourselves.
  HASH_SELF = location.hash.slice(1);
  window.addEventListener("hashchange", () => {
    if (location.hash.slice(1) === HASH_SELF) return;
    HASH_SELF = location.hash.slice(1);
    applyHash();
  });
  if (!(await applyHash())) {
    // no deep link: open both hero views on the payoff, never an empty pane —
    // the pressed row/cell also teaches the selection grammar (ux-design.md §Landing)
    if ((CORE.concepts || []).length) await selectConcept(CORE.concepts[0].ckey, true);
    const top = CORE.shapes.slice().sort((a, b) =>
      (CORE.postings[b.shape] || []).length - (CORE.postings[a.shape] || []).length)[0];
    if (top) {
      state.onset = top.onset_class; state.nuc = top.nucleus_bucket; state.shape = top.shape;
      renderHeatmap(); await ensureShape(top.shape); renderShapes(); drawMap(); renderLangs();
    }
  }
}

let HASH_SELF = "";
function writeHash(s) { HASH_SELF = s; location.hash = s; }
async function applyHash() {
  const h = new URLSearchParams(location.hash.slice(1));
  if (h.get("c")) { navigateTo("meanings"); await selectConcept(h.get("c"), true); }
  else if (h.get("l")) { navigateTo("languages"); await selectLanguage(h.get("l"), true); }
  else if (h.has("r")) { navigateTo("regions"); selectRegion(h.get("r"), true); } // has(): "" is the Unlisted region
  else if (h.get("v")) { navigateTo("convergence"); await selectConvMeaning(h.get("v"), true); }
  else return false;
  return true;
}

/* ---------- filters ---------- */
function activeShape(s) { return state.onsetOn.has(s.onset_class); }
function activePostings(shape) {
  return (CORE.postings[shape] || []).filter(p => state.tierOn.has(TIER[p[1]]));
}
function renderFilters() {
  const onsets = ONSET_ORDER.filter(o => CORE.shapes.some(s => s.onset_class === o));
  const removedByGen = state.tierOn.has("generated") ? 0
    : new Set(CORE.shapes.flatMap(s => (CORE.postings[s.shape] || []).filter(p => p[1] === 2).map(p => p[0]))).size;
  const chip = (on, cls, label, extra = "") =>
    `<span class="chip ${cls} ${on ? "" : "off"}" tabindex="0" role="button" aria-pressed="${on}" ${extra}>${label}</span>`;
  const onsetChips = onsets.map(o =>
    chip(state.onsetOn.has(o), "onset", ONSET_LABEL[o], `data-onset="${o}"`)).join("");
  const tierChips = TIER.map((t, i) =>
    chip(state.tierOn.has(t), "tier-" + t, `${tierGlyphHTML(i)} ${t}`, `data-tier="${t}"`)).join("");
  document.getElementById("filters").innerHTML =
    `<div class="grp"><span class="lbl">onset</span>${onsetChips}</div>
     <div class="grp"><span class="lbl">tier</span>${tierChips}
       ${removedByGen ? `<span class="removed">hiding generated would remove ${removedByGen} language(s)</span>` : ""}</div>`;
  document.querySelectorAll(".chip.onset").forEach(c => c.onclick = () => toggle(state.onsetOn, c.dataset.onset));
  document.querySelectorAll("[data-tier]").forEach(c => c.onclick = () => toggle(state.tierOn, c.dataset.tier));
}
function toggle(set, key) {
  set.has(key) ? set.delete(key) : set.add(key);
  renderFilters(); renderHeatmap(); drawMap(); renderLangs();
}

/* ---------- heatmap ---------- */
function cellShapes(o, n) { return CORE.shapes.filter(s => s.onset_class === o && s.nucleus_bucket === n && activeShape(s)); }
function cellStats(o, n) {
  // Composition is over *languages*, not postings: a language that has many
  // shapes in this cell counts once, at its most-trustworthy (lowest-index) tier.
  // Without this, comp double-counts and its glyph string grows unbounded.
  const best = new Map();
  for (const s of cellShapes(o, n)) for (const p of activePostings(s.shape)) {
    const cur = best.get(p[0]);
    if (cur === undefined || p[1] < cur) best.set(p[0], p[1]);
  }
  const comp = [0, 0, 0];
  for (const t of best.values()) comp[t]++;
  return { langCount: best.size, comp };
}
function renderHeatmap() {
  const onsets = ONSET_ORDER.filter(o => CORE.shapes.some(s => s.onset_class === o));
  const nucs = NUC_ORDER.filter(n => CORE.shapes.some(s => s.nucleus_bucket === n));
  // Observed-vs-expected intensity (honesty: a raw count just rewards common cells /
  // data-dense languages). expected = row×col marginal ÷ grand total (independence);
  // ratio > 1 = this onset+vowel COMBINATION is commoner than chance. A PHOIBLE-
  // inventory denominator would be stricter — this marginal proxy is fully client-side.
  const grid = {}, rowT = {}, colT = {}; let grand = 0;
  for (const o of onsets) {
    grid[o] = {};
    for (const n of nucs) {
      const st = cellStats(o, n); grid[o][n] = st;
      rowT[o] = (rowT[o] || 0) + st.langCount;
      colT[n] = (colT[n] || 0) + st.langCount;
      grand += st.langCount;
    }
  }
  const ratioOf = (o, n) => {
    const exp = grand ? rowT[o] * colT[n] / grand : 0;
    return exp ? grid[o][n].langCount / exp : 0;
  };
  // The dial window (grafted from the panel's Typenschild proposal): a fixed
  // readout above the grid carrying the hovered/focused cell's tier composition —
  // cells keep only the count numeral, the dial keeps "never a bare count" whole.
  const dialLine = (o, n) => {
    const { langCount, comp } = grid[o][n];
    const ratio = ratioOf(o, n);
    const rtxt = ratio >= 1 ? `${ratio.toFixed(1)}× commoner than chance` : `${ratio.toFixed(2)}× — rarer than chance`;
    return `${ONSET_LABEL[o]} × <span class="ipa">${NUC_LABEL[n]}</span> — ${langCount} language${langCount > 1 ? "s" : ""} · ${tierCompHTML(comp)} · ${rtxt}`;
  };
  const dialDefault = state.onset && grid[state.onset]?.[state.nuc]?.langCount
    ? dialLine(state.onset, state.nuc)
    : `<span class="note">click a cell to choose an onset × vowel — then pick a shape below</span>`;
  let h = `<div class="dial" id="dial" aria-live="polite">${dialDefault}</div>`;
  h += "<table class='heat'><thead><tr><th></th>";
  for (const n of nucs) h += `<th>${NUC_LABEL[n]}</th>`;
  h += "</tr></thead><tbody>";
  for (const o of onsets) {
    const dim = state.onsetOn.has(o) ? "" : " dim";
    h += `<tr><th class='row${dim}'>${ONSET_LABEL[o]}</th>`;
    for (const n of nucs) {
      const { langCount, comp } = grid[o][n];
      if (!langCount) { h += "<td class='empty'></td>"; continue; }
      const ratio = ratioOf(o, n);
      const step = rampStep(ratio);
      const dots = comp.map((c, i) => c ? `${c}${TIER_GLYPH[i]}` : "").filter(Boolean).join(" ");
      const on = (state.onset === o && state.nuc === n) ? " on" : "";
      const rtxt = ratio >= 1 ? `${ratio.toFixed(1)}× commoner than chance` : `${ratio.toFixed(2)}× — rarer than chance`;
      h += `<td class="cell${on}${dim}${step === 4 ? " deep" : ""}"${dim ? ' aria-disabled="true"' : ' tabindex="0"'} style="background:${RAMP[step]}" data-o="${o}" data-n="${n}"
              aria-label="${ONSET_LABEL[o]} plus ${NUC_LABEL[n]}: ${langCount} language(s), ${rtxt} — ${dots}"
              title="${langCount} language(s), ${rtxt} — ${dots}"><div class="n">${langCount}</div></td>`;
    }
    h += "</tr>";
  }
  h += "</tbody></table><div class='shapes' id='shapes'></div>";
  const host = document.getElementById("heat"); host.innerHTML = h;
  const dial = document.getElementById("dial");
  host.querySelectorAll("td.cell").forEach(td => {
    if (td.classList.contains("dim")) return; // excluded by the user's own filter: inert
    td.onclick = () => {
      state.onset = td.dataset.o; state.nuc = td.dataset.n; state.shape = null;
      renderHeatmap(); renderShapes(); drawMap(); renderLangs();
    };
    // hover/keyboard-focus reads the cell into the dial; leaving reverts to the selection
    const read = () => { dial.innerHTML = dialLine(td.dataset.o, td.dataset.n); };
    td.onmouseenter = read; td.onfocus = read;
  });
  const grid_el = host.querySelector("table.heat");
  grid_el.onmouseleave = () => { dial.innerHTML = dialDefault; };
  // keyboard parity: tabbing out of the grid also reverts the dial to the selection
  grid_el.addEventListener("focusout", e => {
    if (!e.currentTarget.contains(e.relatedTarget)) dial.innerHTML = dialDefault;
  });
  renderShapes();
}
function renderShapes() {
  const el = document.getElementById("shapes"); if (!el) return;
  const drill = document.getElementById("drill");
  if (!state.onset) { el.innerHTML = ""; drill.textContent = ""; return; }
  drill.innerHTML = `— ${ONSET_LABEL[state.onset]} × <span class="ipa">${NUC_LABEL[state.nuc]}</span>: pick a shape`;
  el.innerHTML = cellShapes(state.onset, state.nuc).map(s =>
    `<span class="shape ${state.shape === s.shape ? "sel" : ""}" tabindex="0" role="button" data-s="${s.shape}">/${s.shape}/</span>`).join("");
  el.querySelectorAll(".shape").forEach(sp => sp.onclick = async () => {
    state.shape = sp.dataset.s; await ensureShape(state.shape); renderShapes(); drawMap(); renderLangs();
  });
}
function renderLangs() {
  const el = document.getElementById("langs"), head = document.getElementById("selshape");
  if (!state.shape) { el.innerHTML = ""; head.textContent = ""; return; }
  head.textContent = "";
  const posts = activePostings(state.shape);
  const postComp = [0, 0, 0];
  posts.forEach(p => { postComp[p[1]]++; });
  // each row leads with the word (attested tone form), then meaning, then language
  const rows = posts.map(p => {
    const L = CORE.languages[p[0]], tier = TIER[p[1]];
    const d = FORMS[`${L.glottocode}|${state.shape}`] || {};
    const glosses = (d.words || []).flatMap(w => w.gloss_set.map(g => g.gloss));
    const words = glosses.slice(0, 3).join(", ") + (glosses.length > 3 ? ` +${glosses.length - 3}` : "");
    const tone = (d.words || [])[0]?.tone || "";
    const review = p[3] ? `<span class="review">* review</span>` : "";
    return `<div class="langrow" tabindex="0" role="button" data-key="${L.glottocode}|${state.shape}">
      <span class="ipa17">/${state.shape}${tone}/</span>
      <span class="gloss14">${words}</span>
      <span class="lname">${L.name}</span>
      ${review}<span class="badge b-${tier}">${TIER_GLYPH[p[1]]} ${tier}</span></div>`;
  }).join("");
  el.innerHTML = `<p class="conv">${playBtn(state.shape)} <span class="ipa22">/${state.shape}/</span> —
      <b>${posts.length}</b> language${posts.length > 1 ? "s" : ""} · ${tierCompHTML(postComp)}
      <span class="note">(guesses never hidden)</span></p>${rows}`;
  el.querySelectorAll(".langrow").forEach(r => r.onclick = () => openSheet(r.dataset.key));
}

/* ---------- form-detail bottom sheet (Phase 3) ---------- */
function ccBadge(cc, under) {
  // confidence is plain engraved text — only "pending review" earns the alarm hue
  return `<span class="conf">openness: ${cc}</span>${under ? ` <span class="review">* pending review</span>` : ""}`;
}
function playBtn(shape) {
  return AUDIO[shape] ? `<button class="play" onclick="playShape('${shape}')" title="hear" aria-label="hear">▶</button>` : "";
}
function openSheet(key) {
  const f = FORMS[key]; if (!f) return;
  const L = CORE.languages.find(l => l.glottocode === f.glottocode);
  const synth = AUDIO[f.shape];
  const audioLine = synth
    ? `<span class="badge">audio: ${synth.provenance}${synth.lossy ? " (approx.)" : ""} · tone not rendered</span>`
    : `<span class="note">no audio available for this shape (honest gap)</span>`;
  const words = f.words.length ? f.words.map(w => `
      <div class="wordrow"><span class="badge b-${w.tier}">${TIER_GLYPH[TIER.indexOf(w.tier)]}</span>
        <span class="ipa17">${f.shape}${w.tone}</span>
        <span>${w.gloss_set.map(g => g.concepticon_id
          ? `<a href="#c=${g.concepticon_id}" title="Concepticon ${g.concepticon_id} — jump to this concept" onclick="jumpConcept(${g.concepticon_id});return false">${g.gloss}</a>`
          : g.gloss).join(", ")}</span></div>`).join("")
    : `<p class="note">No example words in the seed for this language — the Form still stands on its own
        (this is common for under-documented languages; not an error).</p>`;
  document.getElementById("sheetBody").innerHTML = `
    <div class="sheet-hd">${playBtn(f.shape)} <span class="ipa">/${f.shape}/</span> · ${L.name}
      <span class="badge b-${f.tier}">${TIER_GLYPH[TIER.indexOf(f.tier)]} ${f.tier}</span>
      ${ccBadge(f.classification_confidence, f.under_review)} ${audioLine}
      ${state.pins.includes(key)
        ? `<button class="pin" onclick="unpin('${key}');openSheet('${key}')">in compare ×</button>`
        : `<button class="pin" onclick="pin('${key}');openSheet('${key}')">+ compare</button>`}</div>
    <p class="note">source: ${f.preferred_source} (preferred of ${f.sources.join(", ")}) ·
       tones: ${f.tones.length ? `<span class="ipa">${f.tones.join(" ")}</span>` : "—"} · nucleus: ${f.nucleus_type}</p>
    <h2>Example words</h2>${words}`;
  document.getElementById("sheet").classList.add("open");
}
function jumpConcept(cid) {
  // "same meaning elsewhere" → open the meaning as hero across all languages.
  navigateTo("meanings");
  selectConcept(String(cid));
}

/* ---------- audio ---------- */
function playShape(shape) {
  const clip = AUDIO[shape]; if (!clip) return;
  const p = document.getElementById("player"); p.src = "audio/" + clip.file; p.play();
}
window.playShape = playShape; window.jumpConcept = jumpConcept; window.pin = pin; window.ensureShape = ensureShape;

/* ---------- compare (Phase 3) ---------- */
function pin(key) {
  if (!state.pins.includes(key)) state.pins.push(key);
  const b = document.getElementById("pinBadge");
  b.textContent = state.pins.length; b.classList.toggle("hidden", !state.pins.length);
  renderCompare();
}
function renderCompare() {
  const el = document.getElementById("compare");
  if (!state.pins.length) {
    el.innerHTML = `<p class="note">Nothing pinned yet. Pick a meaning in
        <a onclick="navigateTo('meanings')">Meanings</a> or a shape in
        <a onclick="navigateTo('explore')">Sounds</a>, click a language to raise its
        detail sheet, then press &ldquo;+ compare&rdquo;.</p>
      <p class="note">Juxtaposition only — no similarity score: for words this short,
        look-alikes are overwhelmingly chance.</p>`;
    return;
  }
  const pins = state.pins.map(k => {
    const f = FORMS[k], li = CORE.languages.findIndex(l => l.glottocode === f.glottocode);
    return { k, f, L: CORE.languages[li], e: li >= 0 ? langIndex()[li] : null };
  });
  // One grid with shared row tracks (not per-column stacks): forms stay aligned
  // no matter what wraps. A fixed ledger column carries each field label once.
  // Hierarchy per column: word (serif, largest) → meanings → language attribution.
  let cells = "";
  const row = (lbl, cell, cls = "") => {
    cells += `<div class="clabel ${cls}">${lbl}</div>`
      + pins.map(p => `<div class="ccell ${cls}">${cell(p)}</div>`).join("");
  };
  row("", p => `${playBtn(p.f.shape)} <span class="ipa22">/${p.f.shape}/</span>`);
  row("words", p => p.f.words.flatMap(w => w.gloss_set.map(g =>
      `<span class="ipa17">${p.f.shape}${w.tone}</span> ${g.concepticon_id
        ? `<a href="#c=${g.concepticon_id}" onclick="jumpConcept(${g.concepticon_id});return false">‘${g.gloss}’</a>`
        : `‘${g.gloss}’`}`)).join("<br>") || "—");
  row("tones", p => p.f.tones.length ? `<span class="ipa17">${p.f.tones.join(" ")}</span>` : "—");
  row("language", p => `<span class="wlink" tabindex="0" role="button" data-l="${p.f.glottocode}"><span class="wname">${p.L.name}</span></span>
      <button class="go" onclick="gotoShape('${p.f.shape}')">see in Sounds →</button>`);
  row("tier", p => `<span class="badge b-${p.f.tier}">${TIER_GLYPH[TIER.indexOf(p.f.tier)]} ${p.f.tier}</span>${p.f.under_review ? ` <span class="review">* review</span>` : ""}`);
  row("openness", p => `<span class="conf">${p.f.classification_confidence}</span>`);
  row("evidence", p => p.e
    ? `<span class="bar mini">${stripSegs(p.e.comp, 100)}</span><span class="note">${tierCompHTML(p.e.comp)} — whole catalog</span>`
    : "—");
  row("", p => `<button class="unpin" onclick="unpin('${p.k}')">× remove</button>`, "last");
  el.innerHTML = `<div class="cols" style="grid-template-columns:auto repeat(${pins.length},minmax(11rem,max-content))">${cells}</div>`;
  el.querySelectorAll(".wlink").forEach(sp =>
    sp.onclick = () => { navigateTo("languages"); selectLanguage(sp.dataset.l); });
}
function unpin(k) {
  state.pins = state.pins.filter(x => x !== k);
  const b = document.getElementById("pinBadge");
  b.textContent = state.pins.length; b.classList.toggle("hidden", !state.pins.length);
  renderCompare();
}
window.unpin = unpin;

/* ---------- meanings (the hero axis) ---------- */
function renderMeanings(filter = "") {
  const el = document.getElementById("conceptList");
  const q = filter.trim().toLowerCase();
  const list = (CORE.concepts || []).filter(c => !q || c.gloss.toLowerCase().includes(q));
  const max = Math.max(1, ...list.map(c => c.lang_count));
  el.innerHTML = list.slice(0, 300).map(c => {
    const conv = c.shape_count === 1 ? "1 shape" : `${c.shape_count} shapes`;
    return `<div class="crow ${state.concept === c.ckey ? "sel" : ""}" tabindex="0" role="button" data-c="${c.ckey}">
      <span class="gloss">${c.gloss}</span>
      <span class="bar"><i class="s-data" style="width:${Math.round(100 * c.lang_count / max)}%"></i></span>
      <span class="cnt">${c.lang_count} langs · ${conv}</span></div>`;
  }).join("") + (list.length > 300 ? `<p class="note">…${list.length - 300} more — search to narrow</p>` : "");
  el.querySelectorAll(".crow").forEach(r => r.onclick = () => selectConcept(r.dataset.c));
}

async function selectConcept(ckey, skipHash) {
  state.concept = ckey;
  if (!skipHash) writeHash("c=" + ckey);   // shareable deep link
  renderMeanings(document.getElementById("conceptSearch").value);
  const box = document.getElementById("conceptDetail"), head = document.getElementById("conceptSel");
  const d = await loadConcept(ckey);
  if (!d) { box.innerHTML = `<p class="note">no data for this meaning</p>`; return; }
  head.textContent = `— ‘${d.gloss}’`;
  const byShape = new Map();
  for (const [li, shape, tone, tr, cr, ur] of d.entries) {
    if (!byShape.has(shape)) byShape.set(shape, []);
    byShape.get(shape).push({ li, tone, tr, ur });
  }
  const langs = new Set(d.entries.map(e => e[0]));
  const shapes = [...byShape.entries()].sort((a, b) => b[1].length - a[1].length);
  // lede composition: each language once, at its most-trustworthy tier
  const best = new Map();
  for (const [li, , , tr] of d.entries) {
    const cur = best.get(li);
    if (cur === undefined || tr < cur) best.set(li, tr);
  }
  const ledeComp = [0, 0, 0];
  for (const t of best.values()) ledeComp[t]++;
  const conv = `<p class="conv"><b>${langs.size}</b> language${langs.size > 1 ? "s" : ""} express
    <b>‘${d.gloss}’</b> as an open monosyllable, using just <b>${byShape.size}</b> sound-shape${byShape.size > 1 ? "s" : ""}
    <span class="note">(${tierCompHTML(ledeComp)})</span>.</p>`;
  // card bodies lead with the word (attested tone form); the language name is
  // attribution — and a live link to the form sheet, not a dead end
  const blocks = shapes.map(([shape, rows]) => {
    const comp = [0, 0, 0];
    rows.forEach(r => { comp[r.tr]++; });
    const names = rows.map(r => {
      const L = CORE.languages[r.li];
      return `<span class="wlink" tabindex="0" role="button" title="${TIER[r.tr]} tier — open this form" data-key="${L.glottocode}|${shape}" data-shape="${shape}">${r.tone ? `<span class="ipa">${shape}${r.tone}</span> ` : ""}<span class="wname">${L.name}</span></span>${r.ur ? ` <span class="review">* review</span>` : ""}`;
    }).join(" · ");
    return `<div class="cshape"><div class="hd">
        ${AUDIO[shape] ? `<button class="play inline" onclick="playShape('${shape}')" aria-label="hear">▶</button>` : ""}
        <span class="ipa17">/${shape}/</span> <span class="note">${rows.length} language${rows.length > 1 ? "s" : ""} · ${tierCompHTML(comp)}</span>
        <button class="go" onclick="gotoShape('${shape}')">see in Sounds →</button></div>
      <div class="langs">${names}</div></div>`;
  }).join("");
  box.innerHTML = `<p class="convhd">‘${d.gloss}’</p>` + conv + blocks;
  box.querySelectorAll(".wlink").forEach(sp => sp.onclick = async () => {
    await ensureShape(sp.dataset.shape); openSheet(sp.dataset.key);
  });
}

async function gotoShape(shape) {
  const s = CORE.shapes.find(x => x.shape === shape); if (!s) return;
  navigateTo("explore");
  state.onset = s.onset_class; state.nuc = s.nucleus_bucket; state.shape = shape;
  renderHeatmap(); await ensureShape(shape); renderShapes(); drawMap(); renderLangs();
}
window.selectConcept = selectConcept; window.gotoShape = gotoShape;

/* ---------- languages & regions (filter by language / by region) ---------- */
// Inverted index: language index → its open-monosyllable shapes (with tier).
// Built once from postings; the same source of truth as the heatmap.
let LANG_INDEX = null, SHAPE_META = null;
function shapeMeta() { return (SHAPE_META ||= Object.fromEntries(CORE.shapes.map(s => [s.shape, s]))); }
function langIndex() {
  if (LANG_INDEX) return LANG_INDEX;
  const idx = CORE.languages.map(L => ({ L, shapes: [], comp: [0, 0, 0] }));
  for (const [shape, posts] of Object.entries(CORE.postings))
    for (const p of posts) idx[p[0]].shapes.push({ shape, tier: p[1], review: !!p[3] });
  for (const e of idx) for (const s of e.shapes) e.comp[s.tier]++;
  return (LANG_INDEX = idx);
}

function renderLanguages(filter = "") {
  const el = document.getElementById("langList");
  const q = filter.trim().toLowerCase();
  const idx = langIndex()
    .map((e, li) => ({ e, li }))
    .filter(({ e }) => e.shapes.length &&
      (!q || e.L.name.toLowerCase().includes(q) || (e.L.macroarea || "").toLowerCase().includes(q)))
    .sort((a, b) => b.e.shapes.length - a.e.shapes.length);
  const max = Math.max(1, ...idx.map(({ e }) => e.shapes.length));
  el.innerHTML = idx.slice(0, 300).map(({ e }) => {
    const sc = e.shapes.length;
    return `<div class="crow ${state.language === e.L.glottocode ? "sel" : ""}" tabindex="0" role="button" data-l="${e.L.glottocode}">
      <span class="gloss">${e.L.name}</span>
      <span class="bar">${stripSegs(e.comp, 100 * sc / max)}</span>
      <span class="cnt">${sc} shape${sc > 1 ? "s" : ""} (${tierCompHTML(e.comp)})${e.L.macroarea ? " · " + e.L.macroarea : ""}</span></div>`;
  }).join("") + (idx.length > 300 ? `<p class="note">…${idx.length - 300} more — search to narrow</p>` : "");
  el.querySelectorAll(".crow").forEach(r => r.onclick = () => selectLanguage(r.dataset.l));
}
async function selectLanguage(gc, skipHash) {
  state.language = gc;
  if (!skipHash) writeHash("l=" + gc);
  renderLanguages(document.getElementById("langSearch").value);
  document.querySelector("#langList .crow.sel")?.scrollIntoView({ block: "nearest" });
  const box = document.getElementById("langDetail"), head = document.getElementById("langSel");
  const li = CORE.languages.findIndex(l => l.glottocode === gc);
  if (li < 0) { box.innerHTML = `<p class="note">unknown language</p>`; return; }
  const L = CORE.languages[li], e = langIndex()[li], meta = shapeMeta();
  head.textContent = `— ${L.name}`;
  const shapes = e.shapes.slice().sort((a, b) =>
    (ONSET_ORDER.indexOf(meta[a.shape]?.onset_class) - ONSET_ORDER.indexOf(meta[b.shape]?.onset_class))
    || a.shape.localeCompare(b.shape));
  const loc = (L.longitude == null || L.latitude == null)
    ? `<span class="review">no coordinates — listed but unmapped</span>`
    : `${L.latitude.toFixed(1)}, ${L.longitude.toFixed(1)}`;
  const conv = `<p class="conv"><b>${L.name}</b> has <b>${e.shapes.length}</b> open-monosyllable
      shape${e.shapes.length > 1 ? "s" : ""} <span class="note">(${tierCompHTML(e.comp)})</span>.</p>
    <p class="note">region: ${L.macroarea || "unlisted"} · location: ${loc} ·
      documentation: ${L.doc_status || "—"} · prosody: ${L.prosodic_type || "—"} ·
      ${L.form_count} example word${L.form_count === 1 ? "" : "s"} in the catalog</p>`;
  const blocks = shapes.slice(0, 400).map(s => {
    // meanings belong beside the word (blob build has them all; the chunked
    // build only for already-fetched shapes — top-glosses-in-postings is a
    // recorded bake debt in .interface-design/system.md)
    const w = (FORMS[`${gc}|${s.shape}`]?.words || []).flatMap(x => x.gloss_set.map(g => g.gloss));
    const gl = w.slice(0, 3).join(", ") + (w.length > 3 ? ` +${w.length - 3}` : "");
    // portal card: names ONE form, so its whole surface opens the sheet
    return `<div class="cshape portal" data-key="${gc}|${s.shape}" data-shape="${s.shape}"><div class="hd">
      ${AUDIO[s.shape] ? `<button class="play inline" onclick="playShape('${s.shape}')" aria-label="hear">▶</button>` : ""}
      <span class="lshape" tabindex="0" role="button" data-key="${gc}|${s.shape}" data-shape="${s.shape}"><span class="ipa17">/${s.shape}/</span></span>
      ${gl ? `<span class="gloss14">${gl}</span>` : ""}
      <span class="badge b-${TIER[s.tier]}">${TIER_GLYPH[s.tier]} ${TIER[s.tier]}</span>
      ${s.review ? `<span class="review">* review</span>` : ""}
      <button class="go" onclick="gotoShape('${s.shape}')">see in Sounds →</button></div></div>`;
  }).join("")
    + (shapes.length > 400 ? `<p class="note">…${shapes.length - 400} more shapes</p>` : "");
  box.innerHTML = conv + blocks;
  // the whole portal card opens the form sheet; inner keys win over the container
  box.querySelectorAll(".cshape.portal").forEach(c => c.onclick = async e => {
    if (e.target.closest("button,a,.lshape")) return;
    await ensureShape(c.dataset.shape); openSheet(c.dataset.key);
  });
  box.querySelectorAll(".lshape").forEach(sp => sp.onclick = async () => {
    await ensureShape(sp.dataset.shape); openSheet(sp.dataset.key);
  });
}

let REGION_INDEX = null;
function regionIndex() {
  if (REGION_INDEX) return REGION_INDEX;
  const byRegion = new Map();
  langIndex().forEach((e, li) => {
    if (!e.shapes.length) return;
    const key = e.L.macroarea || "";
    if (!byRegion.has(key)) byRegion.set(key, { region: key, langs: [], shapeSet: new Set(), comp: [0, 0, 0] });
    const r = byRegion.get(key);
    r.langs.push({ li, name: e.L.name, sc: e.shapes.length });
    for (const s of e.shapes) r.shapeSet.add(s.shape);
    r.comp[Math.min(...e.shapes.map(s => s.tier))]++; // each language once, at its best tier
  });
  return (REGION_INDEX = [...byRegion.values()].sort((a, b) => b.langs.length - a.langs.length));
}
function renderRegions() {
  const el = document.getElementById("regionList");
  const regs = regionIndex();
  const max = Math.max(1, ...regs.map(r => r.langs.length));
  el.innerHTML = regs.map(r => `<div class="crow ${state.region === r.region ? "sel" : ""}" tabindex="0" role="button" data-r="${encodeURIComponent(r.region)}">
      <span class="gloss">${r.region || "Unlisted"}</span>
      <span class="bar">${stripSegs(r.comp, 100 * r.langs.length / max)}</span>
      <span class="cnt">${r.langs.length} langs (${tierCompHTML(r.comp)}) · ${r.shapeSet.size} shapes</span></div>`).join("");
  el.querySelectorAll(".crow").forEach(row => row.onclick = () => selectRegion(decodeURIComponent(row.dataset.r)));
}
function selectRegion(region, skipHash) {
  state.region = region;
  if (!skipHash) writeHash("r=" + encodeURIComponent(region));
  renderRegions();
  const box = document.getElementById("regionDetail"), head = document.getElementById("regionSel");
  const r = regionIndex().find(x => x.region === region);
  if (!r) { box.innerHTML = `<p class="note">no data</p>`; return; }
  const lbl = r.region || "Unlisted";
  head.textContent = `— ${lbl}`;
  const conv = `<p class="conv"><b>${r.langs.length}</b> language${r.langs.length > 1 ? "s" : ""} in
      <b>${lbl}</b> use <b>${r.shapeSet.size}</b> distinct open-monosyllable shape${r.shapeSet.size > 1 ? "s" : ""}
      <span class="note">(${tierCompHTML(r.comp)})</span>.</p>`;
  const langs = r.langs.slice().sort((a, b) => b.sc - a.sc);
  // the specimen is present even here: a serif preview of each language's shapes
  const rows = langs.slice(0, 400).map(l => {
    const shp = langIndex()[l.li].shapes;
    const prev = shp.slice(0, 3).map(s => `/${s.shape}/`).join(" ") + (shp.length > 3 ? ` +${shp.length - 3}` : "");
    return `<div class="langrow" tabindex="0" role="button" data-l="${CORE.languages[l.li].glottocode}">
      <span class="name">${l.name} <span class="note ipa">${prev}</span></span>
      <span class="badge">${l.sc} shape${l.sc > 1 ? "s" : ""}</span></div>`;
  }).join("")
    + (langs.length > 400 ? `<p class="note">…${langs.length - 400} more</p>` : "");
  box.innerHTML = conv + rows;
  box.querySelectorAll(".langrow").forEach(row => row.onclick = () => pickLang(row.dataset.l));
}
function pickLang(gc) {
  // arrive with the Languages list pre-filtered to the region we came from —
  // visible, reversible context instead of an unmarked teleport
  navigateTo("languages");
  document.getElementById("langSearch").value = state.region || "";
  selectLanguage(gc);
}
window.selectLanguage = selectLanguage; window.selectRegion = selectRegion; window.pickLang = pickLang;

/* ---------- look-alikes: same sound + same meaning across languages ----------
   HONESTY BOUNDARY (ux-design.md "Why no similarity score", load-bearing): this
   surfaces raw co-occurrences only — a count of how many languages share a shape
   for a meaning, the same class of fact as a heatmap cell. It computes NO
   similarity / relatedness score, and every view leads with the chance caveat. */
const CONV_BANNER = `<p class="convbanner"><span class="lbl">chance vs. cognate — read first</span><br>These are <b>raw co-occurrences, not a relatedness claim.</b> Two
  languages sharing a shape for a meaning may be coincidence <i>or</i> shared history — and for short open
  monosyllables the two are notoriously hard to tell apart without an explicit chance baseline (Ringe 1992).
  This view computes <b>no similarity or relatedness score</b> and takes no side; your eye does the judging.</p>`;
function renderConvMeanings(filter = "") {
  const el = document.getElementById("convList");
  const q = filter.trim().toLowerCase();
  const list = (CORE.concepts || []).filter(c => c.lang_count >= 2 && (!q || c.gloss.toLowerCase().includes(q)))
    .sort((a, b) => b.lang_count - a.lang_count);
  const max = Math.max(1, ...list.map(c => c.lang_count));
  el.innerHTML = list.slice(0, 300).map(c =>
    `<div class="crow ${state.convMeaning === c.ckey ? "sel" : ""}" tabindex="0" role="button" data-c="${c.ckey}">
      <span class="gloss">${c.gloss}</span>
      <span class="bar"><i class="s-data" style="width:${Math.round(100 * c.lang_count / max)}%"></i></span>
      <span class="cnt">${c.lang_count} langs · ${c.shape_count} shapes</span></div>`).join("")
    + (list.length > 300 ? `<p class="note">…${list.length - 300} more — search to narrow</p>` : "");
  el.querySelectorAll(".crow").forEach(r => r.onclick = () => selectConvMeaning(r.dataset.c));
}
async function selectConvMeaning(ckey, skipHash) {
  state.convMeaning = ckey;
  if (!skipHash) writeHash("v=" + ckey);
  renderConvMeanings(document.getElementById("convSearch").value);
  const box = document.getElementById("convDetail"), head = document.getElementById("convSel");
  const d = await loadConcept(ckey);
  if (!d) { box.innerHTML = CONV_BANNER + `<p class="note">no data for this meaning</p>`; return; }
  head.textContent = `— ‘${d.gloss}’`;
  const byShape = new Map();
  for (const [li, shape, tone, tr, cr, ur] of d.entries) {
    if (!byShape.has(shape)) byShape.set(shape, []);
    byShape.get(shape).push({ li, tone, tr, ur });
  }
  // A "look-alike" = a single shape that ≥2 distinct languages use for this meaning.
  const shared = [...byShape.entries()]
    .map(([shape, rows]) => [shape, rows, new Set(rows.map(r => r.li)).size])
    .filter(([, , nl]) => nl >= 2)
    .sort((a, b) => b[2] - a[2]);
  if (!shared.length) {
    box.innerHTML = `<p class="convhd">‘${d.gloss}’</p>` + CONV_BANNER + `<p class="note">No single shape is shared by two or more languages for
      ‘${d.gloss}’ — here every language reaches for a different sound. (That is the common case; convergence
      is rarer than intuition suggests.)</p>`;
    return;
  }
  const [topShape, , topN] = shared[0];
  const lede = `<p class="conv">For <b>‘${d.gloss}’</b>, <b>${shared.length}</b>
    sound-shape${shared.length > 1 ? "s are" : " is"} independently used by two or more languages;
    the widest is <span class="ipa17">/${topShape}/</span> (<b>${topN}</b> languages).</p>`;
  // Evidence quality legible at rest in the judgment view: per-shape tier
  // composition in the head, per-language tier glyph and review flag inline.
  const blocks = shared.map(([shape, rows, nl]) => {
    const comp = [0, 0, 0];
    rows.forEach(r => { comp[r.tr]++; });
    const names = rows.map(r => {
      const L = CORE.languages[r.li];
      return `<span class="wlink" tabindex="0" role="button" title="${TIER[r.tr]} tier — open this form" data-key="${L.glottocode}|${shape}" data-shape="${shape}">${tierGlyphHTML(r.tr)} ${r.tone ? `<span class="ipa">${shape}${r.tone}</span> ` : ""}<span class="wname">${L.name}</span></span>${r.ur ? ` <span class="review">* review</span>` : ""}`;
    }).join(" · ");
    return `<div class="cshape"><div class="hd">
        ${AUDIO[shape] ? `<button class="play inline" onclick="playShape('${shape}')" aria-label="hear">▶</button>` : ""}
        <span class="ipa17">/${shape}/</span> <span class="note">${nl} languages · ${tierCompHTML(comp)}</span>
        <button class="go" onclick="gotoShape('${shape}')">see in Sounds →</button></div>
      <div class="langs">${names}</div></div>`;
  }).join("");
  box.innerHTML = `<p class="convhd">‘${d.gloss}’</p>` + CONV_BANNER + lede + blocks;
  box.querySelectorAll(".wlink").forEach(sp => sp.onclick = async () => {
    await ensureShape(sp.dataset.shape); openSheet(sp.dataset.key);
  });
}
window.selectConvMeaning = selectConvMeaning;

/* ---------- about + sources (honesty destinations) ---------- */
function renderAbout() {
  const g = tierGlyphHTML; // same rendering as everywhere: never bold, class-colored
  document.getElementById("about").innerHTML = `
    <p>Nearly every language on Earth builds some of its words from the simplest mouthful there is:
    a sound, a vowel, and nothing to close it off — <span class="ipa17">/ma/</span>, <span class="ipa17">/tu/</span>,
    <span class="ipa17">/ko/</span>. This is a
    field guide to those little words, called <b>open monosyllables</b>, and to the languages that lean on them.</p>

    <h3>What counts</h3>
    <p>One syllable, ending on a vowel — including the gliding vowels in “bye” and “now”. Words that end
    in a consonant (“cat”) or have no vowel at all (“mm”) are left out. It’s a deliberately narrow rule, so
    that every language is measured the same way.</p>

    <h3>How much to trust each sound</h3>
    <p>Every pronunciation carries a small mark for how it was sourced: ${g(0)} <b>curated</b> comes from a
    <a onclick="navigateTo('sources')">checked linguistic database</a>, ${g(1)} <b>mined</b> is drawn from dictionaries, and ${g(2)} <b>generated</b>
    is a careful guess from spelling. We never hide the guesses — for many under-documented languages they are
    all that exists — and every count of languages is broken down by these marks, so you can
    see at a glance whether you’re standing on solid ground or thin ice.</p>
    <p><span class="bar mini" style="max-width:14rem">${stripSegs([28, 11, 8], 100)}</span>
    <span class="note">28${g(0)} 11${g(1)} 8${g(2)} — the same gauge everywhere: solid segments are sourced;
    the guessed share is left hollow, literally not inked in.</span></p>

    <h3>When “open” is a judgment call</h3>
    <p>Now and then, whether a word even counts as open is a real linguistic question — is that final glide a
    vowel, or a consonant in disguise? Where careful scholars could disagree, we flag the word rather than
    pretend the matter is settled. Flagged entries appear as <span class="review">* pending review</span>
    everywhere — including a small red square beside the map dot — until a human has ruled.</p>

    <h3>Why we never score similarity</h3>
    <p>You won’t find a number here claiming two languages are related because their words sound alike. For
    words this short, matching sounds are almost always coincidence — <span class="ipa">/ma/</span> means “mother” in wildly
    unrelated languages largely because it’s among the first sounds a baby makes. We lay the look-alikes side
    by side and let your eye judge; a genuine claim of kinship takes far more than a rhyme.</p>

    <h3>Why coverage is uneven</h3>
    <p>The gaps are honest. Some languages simply have few open syllables; others are just thinly documented.
    <a onclick="navigateTo('explore')">On the map</a>, an empty spot tells you which — a hollow ring means a
    language has no open monosyllables at all, not that we haven’t looked yet. (Unlike the hollow guess-mark
    ○, the ring is a confident claim.)</p>`;
}
function renderSources() {
  // grouped by license family so the NC block reads as one cluster
  const rows = (CORE.sources || []).slice()
    .sort((a, b) => (a.license || "").localeCompare(b.license || "") || (a.id || "").localeCompare(b.id || ""))
    .map(s =>
    `<tr><td>${s.id}</td><td><span class="badge b-${s.tier}">${TIER_GLYPH[TIER.indexOf(s.tier)]} ${s.tier}</span></td><td>${s.license}</td></tr>`).join("");
  document.getElementById("sources").innerHTML = `
    <p>Every Form cites its Source(s). Because some sources are <b>non-commercial (CC-BY-NC)</b>, the whole
    catalog is released under <b>CC-BY-NC-SA 4.0</b> — free to use, share, and adapt for
    <b>non-commercial</b> purposes. The per-Form <code>source_license</code> lets reusers extract a
    commercial-safe subset (only CC0 / CC-BY / CC-BY-SA sources). No-derivatives (ND) sources are excluded.</p>
    <table class="src"><thead><tr><th>source</th><th>tier</th><th>license</th></tr></thead><tbody>${rows}</tbody></table>`;
}

/* ---------- map (Equal Earth) ---------- */
function equalEarth(lonDeg, latDeg) {
  const A1 = 1.340264, A2 = -0.081106, A3 = 0.000893, A4 = 0.003796;
  const lon = lonDeg * Math.PI / 180, lat = latDeg * Math.PI / 180;
  const th = Math.asin(Math.sqrt(3) / 2 * Math.sin(lat));
  const t2 = th * th, t6 = t2 * t2 * t2, t8 = t6 * t2;
  const x = 2 * Math.sqrt(3) * lon * Math.cos(th) / (3 * (9 * A4 * t8 + 7 * A3 * t6 + 3 * A2 * t2 + A1));
  const y = A4 * th * t8 + A3 * th * t6 + A2 * th * t2 + A1 * th;
  return [x, y];
}
// Fixed Equal-Earth world extent (the projection's own bounds) so the graticule
// frame and the dots always share one coordinate system, independent of the data.
const MAP_W = 520, MAP_H = 300, MAP_PAD = 12;
const MAP_MINX = -2.8, MAP_MAXX = 2.8, MAP_MINY = -1.4, MAP_MAXY = 1.4;
const MAP_S = Math.min((MAP_W - 2 * MAP_PAD) / (MAP_MAXX - MAP_MINX), (MAP_H - 2 * MAP_PAD) / (MAP_MAXY - MAP_MINY));
const mapX = x => MAP_PAD + (x - MAP_MINX) * MAP_S;
const mapY = y => MAP_H - MAP_PAD - (y - MAP_MINY) * MAP_S;

// Coastlines: self-hosted 110m TopoJSON (web/land-110m.json, Natural Earth via
// world-atlas). decodeLand inlines the tiny arc-decoding part of topojson-client:
// delta-decode quantized arcs, stitch each ring's arcs (negative index = reversed).
let LAND = null; // array of rings, each [[lon,lat],...] — set in boot(), null if fetch fails
function decodeLand(topo) {
  const [sx, sy] = topo.transform.scale, [tx, ty] = topo.transform.translate;
  const arcs = topo.arcs.map(arc => {
    let x = 0, y = 0;
    return arc.map(([dx, dy]) => { x += dx; y += dy; return [x * sx + tx, y * sy + ty]; });
  });
  const rings = [];
  for (const g of topo.objects.land.geometries)
    for (const poly of (g.type === "MultiPolygon" ? g.arcs : [g.arcs]))
      for (const idxs of poly) {
        const pts = [];
        for (const i of idxs) {
          const a = i < 0 ? arcs[~i].slice().reverse() : arcs[i];
          for (let k = pts.length ? 1 : 0; k < a.length; k++) pts.push(a[k]); // skip duplicated join point
        }
        rings.push(...splitAntimeridian(pts));
      }
  return rings;
}
// Rings that wrap past lon ±180 (Chukotka, Fiji) would otherwise project as a
// chord straight across the map. Cut them at the antimeridian into separate
// rings, each closed along the ±180 boundary at the interpolated latitude.
function splitAntimeridian(pts) {
  if (pts.length > 1 && pts[0][0] === pts.at(-1)[0] && pts[0][1] === pts.at(-1)[1]) pts = pts.slice(0, -1);
  const jump = (a, b) => Math.abs(b[0] - a[0]) > 180;
  const cutLat = (a, b) => { // latitude where segment a→b meets the antimeridian
    const lb = b[0] + (b[0] < a[0] ? 360 : -360);
    return a[1] + (b[1] - a[1]) * (((a[0] >= 0 ? 180 : -180) - a[0]) / ((lb - a[0]) || 1));
  };
  const start = pts.findIndex((p, k) => jump(pts[(k + pts.length - 1) % pts.length], p));
  if (start < 0) return [pts];
  const rot = pts.slice(start).concat(pts.slice(0, start));
  const chains = [[]];
  for (let k = 0; k < rot.length; k++) {
    if (k && jump(rot[k - 1], rot[k])) chains.push([]);
    chains.at(-1).push(rot[k]);
  }
  return chains.map((ch, c) => {
    const before = chains.at(c - 1).at(-1), after = chains[(c + 1) % chains.length][0];
    const side = p => (p[0] >= 0 ? 180 : -180);
    return [[side(ch[0]), cutLat(before, ch[0])], ...ch, [side(ch.at(-1)), cutLat(ch.at(-1), after)]];
  });
}

// Basemap = the Equal-Earth boundary + a 30° graticule + coastlines (when the
// land asset loaded). Pure projection math, computed once after boot().
let MAP_BASE = "";
function buildBasemap() {
  if (MAP_BASE) return MAP_BASE;
  const range = (a, b, st) => { const o = []; for (let v = a; st > 0 ? v <= b : v >= b; v += st) o.push(v); return o; };
  const poly = coords => "M" + coords.map(([lo, la]) => {
    const [x, y] = equalEarth(lo, la); return `${mapX(x).toFixed(1)},${mapY(y).toFixed(1)}`;
  }).join(" L");
  const outline = poly([
    ...range(90, -90, -3).map(la => [-180, la]), ...range(-180, 180, 10).map(lo => [lo, -90]),
    ...range(-90, 90, 3).map(la => [180, la]), ...range(180, -180, -10).map(lo => [lo, 90]),
  ]) + " Z";
  const grat = [];
  for (const lo of range(-180, 180, 30)) grat.push(poly(range(-90, 90, 5).map(la => [lo, la])));
  for (const la of range(-90, 90, 30)) grat.push(poly(range(-180, 180, 5).map(lo => [lo, la])));
  // One evenodd path for all land rings so lake/sea holes punch through.
  const land = LAND
    ? `<path d="${LAND.map(r => poly(r) + " Z").join(" ")}" fill="#CFCCC4" stroke="#A39F96" stroke-width=".5" fill-rule="evenodd"/>`
    : "";
  // Ocean = the page itself: the map is chart-paper for the dots, not scenery.
  MAP_BASE = `<path d="${outline}" fill="none" stroke="#C9C6BF" stroke-width="1"/>` +
    `<g fill="none" stroke="#C9C6BF" stroke-width=".4">${grat.map(d => `<path d="${d}"/>`).join("")}</g>` + land;
  return MAP_BASE;
}
function drawMap() {
  const withShape = new Set(state.shape ? activePostings(state.shape).map(p => p[0]) : []);
  const review = new Set(state.shape ? activePostings(state.shape).filter(p => p[3]).map(p => p[0]) : []);
  let svg = `<svg viewBox="0 0 ${MAP_W} ${MAP_H}" role="img" aria-label="world map of languages">` + buildBasemap();
  let unmapped = 0;
  CORE.languages.forEach((L, i) => {
    if (L.longitude == null || L.latitude == null) { unmapped++; return; } // listed but unmapped — never plotted at (0,0)
    const [ex, ey] = equalEarth(L.longitude, L.latitude);
    const x = mapX(ex), y = mapY(ey);
    const noData = L.form_count === 0;
    let fill = "#4A4841", r = 3, stroke = "", flag = "";
    // hollow ring = a positive structural claim, so it is inked firmly — unlike
    // unsourced languages, which are simply not in the catalog and get no mark
    if (noData) { fill = "none"; stroke = `stroke="#4A4841" stroke-width="1.3"`; r = 4; }
    if (state.shape) {
      if (withShape.has(i)) {
        fill = "#2F5E6C"; r = 4.5;
        // review is an annotation flag beside the dot, never a recolor of it —
        // the data hue keeps meaning "has this shape" even under review
        if (review.has(i)) flag = `<rect x="${(x + 2.6).toFixed(1)}" y="${(y - 6.6).toFixed(1)}" width="4" height="4" fill="#A63A22"/>`;
      } else if (!noData) { fill = "#64615A"; r = 2.5; } // recede by size, not below the 3:1 ink floor
    }
    const hit = state.shape && withShape.has(i) ? ` class="dothit" tabindex="0" role="button" data-li="${i}"` : "";
    svg += `<circle${hit} cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${r}" fill="${fill}" ${stroke}><title>${L.name}${noData ? " (no open monosyllables in seed)" : ""}</title></circle>${flag}`;
  });
  document.getElementById("map").innerHTML = svg + "</svg>";
  // the advertised loop closes on the map itself: lit dot → form sheet
  document.querySelectorAll("#map .dothit").forEach(c =>
    c.onclick = () => openSheet(`${CORE.languages[+c.dataset.li].glottocode}|${state.shape}`));
  const unmappedNote = unmapped ? ` · ${unmapped} language(s) lack coordinates (listed but unmapped)` : "";
  document.getElementById("mapnote").innerHTML = (state.shape
    ? `Filled = has <span class="ipa">/${state.shape}/</span> · <b style="color:var(--review)">▪</b> = pending review · hollow ring = no open monosyllables (a structural claim, not a gap)`
    : `Pick a shape to light up the languages that have it. Hollow rings = no open monosyllables in the seed.`) + unmappedNote;
}

/* ---------- routing ---------- */
const ROUTES = ["meanings", "explore", "languages", "regions", "convergence", "compare", "about", "sources"];
function navigateTo(route) {
  state.route = route;
  document.querySelectorAll("nav [data-route]").forEach(x => x.classList.toggle("active", x.dataset.route === route));
  for (const r of ROUTES) document.getElementById("view-" + r).classList.toggle("hidden", r !== route);
  if (route === "compare") renderCompare();
}
function wireNav() {
  document.querySelectorAll("nav [data-route]").forEach(b => b.onclick = () => navigateTo(b.dataset.route));
}
window.navigateTo = navigateTo;

boot().catch(e => document.body.insertAdjacentHTML("beforeend",
  `<p style="padding:1rem;color:#A63A22">Could not load data (${e}). Serve from the project root: <code>python3 -m http.server</code>, then open <code>/web/</code>.</p>`));
