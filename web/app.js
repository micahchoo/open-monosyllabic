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
// A cell's colour is its EVIDENCE: the number of language families with a shape
// there (roadmap E2). Before 2026-09-29 it was the ratio to chance, so the
// darkest cells held 1–2 languages. Under MIN_FAMILIES a cell is drawn hollow
// and gives no verdict: too few families to compare with chance.
const MIN_FAMILIES = 5;
const FAMILY_STEPS = [5, 10, 20, 30, 40];
const rampStep = f => FAMILY_STEPS.filter(t => f >= t).length - 1;   // -1 = hollow
// The ratio is read, not seen; near 1 its verdict means nothing, so it says so.
const verdict = r => r > 1.25 ? `${r.toFixed(1)}× the usual share` : r < 0.8 ? `${r.toFixed(2)}× — below the usual share` : `about the usual share (${r.toFixed(2)}×)`;
// The heatmap axes in plain words, for row/column titles and screen readers.
const ONSET_HINT = { none: "no consonant: the word starts with the vowel", nasal: "nasal: m, n, ng — air through the nose",
  stop: "stop: p, t, k, b, d, g — air stopped, then released", implosive: "implosive: b or d with the air pulled in",
  affricate: "affricate: ts, ch — a stop that slides into a hiss", fricative: "fricative: f, s, sh, h — a hiss of air",
  liquid: "liquid: l and r sounds", glide: "glide: w and y", click: "click: tsk-like sounds of southern Africa", other: "other consonants" };
const NUC_HINT = { i: "ee-like vowels", e: "e-like vowels (as in café, bed)", "ə": "central vowels (a as in about)",
  a: "a-like vowels (as in father)", o: "o-like vowels (as in go, law)", u: "oo-like vowels", diphthong: "gliding vowels, as in bye or now", other: "other vowels" };
// Tier composition with glyphs in their tier colors — the text twin of the strip.
const tierGlyphHTML = i => `<b class="g-${TIER[i]}">${TIER_GLYPH[i]}</b>`;
// Nearly every form is curated, so a curated badge on every row says nothing.
// A row wears its tier only when it is the exception (mined / generated); the
// legend and the sheet say that unmarked = curated. Guesses stay visible.
const tierMark = t => t ? `<span class="badge b-${TIER[t]}">${TIER_GLYPH[t]} ${TIER[t]}</span>` : "";
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

// Revalidate every data file: a rebake must show on a plain reload. The server
// answers an unchanged file with a 304, so this costs a header, not a download.
const getJSON = async url => (await fetch(url, { cache: "no-cache" })).json();
let CORE, FORMS = {}, AUDIO = {}, CONCEPTS = {}, BASE = "", CHUNKED = false;
// Tiers that occur in this build. A tier with no forms gets no filter and no
// legend entry: offering to hide "generated" when there is none implied there was.
let TIERS_PRESENT = [];

// Families. Languages in one family share history, so a count of languages is
// always read beside its count of families: 129 Austronesian languages agreeing
// on /rua/ was one fact, not 129 (CONTEXT.md "Family").
const familyOf = li => CORE.languages[li].family || "";
function families(lis) { return new Set([...lis].map(familyOf).filter(Boolean)); }
// "N languages · F families", or "N languages, all Austronesian" when F is 1.
function spreadHTML(lis) {
  lis = [...lis];   // callers pass iterators (Map keys); both counts need a pass
  const n = new Set(lis).size, fams = families(lis);
  const langs = `<b>${n}</b> language${n === 1 ? "" : "s"}`;
  if (n > 1 && fams.size === 1) return `${langs}, all ${[...fams][0]}`;
  return fams.size > 1 ? `${langs} · <b>${fams.size}</b> families` : langs;
}

// Counting unit (roadmap 7). Families by default: Austronesian alone is a third
// of the catalog, and a count of its languages mostly measures how many were
// sampled. "languages" switches the meaning list and the region strip back.
const countBy = () => state.countBy;
const reach = lis => countBy() === "families" ? familiesOrSelf(lis) : new Set(lis).size;
// a language with no family given counts alone, as in oms/baseline.py
function familiesOrSelf(lis) { return new Set([...lis].map(li => familyOf(li) || `lang:${li}`)).size; }

// Plain words for IPA (ux-design.md "IPA-as-hero accessibility"). Each symbol
// gets the nearest everyday sound; where English has none, how it is made.
// Screen readers read these instead of the glyphs; sighted readers see them in
// the sheet and on hover. Approximate by design: a hint, not a transcription.
const SOUND_HINT = {
  a: "a as in father", e: "e as in café", i: "ee as in see", o: "o as in go, without the glide", u: "oo as in food",
  "ə": "a as in about", "ɛ": "e as in bed", "ɔ": "aw as in law", "ɪ": "i as in sit", "ʊ": "oo as in book",
  "æ": "a as in cat", "ɑ": "a as in father, further back", "ɒ": "o as in British hot", "ʌ": "u as in cup",
  "ɐ": "a as in comma", "ɨ": "ee with the tongue pulled back", "ʉ": "oo with the tongue pushed forward",
  "ɯ": "oo with the lips spread", y: "ee with rounded lips, as in French tu", "ø": "eu as in French peu",
  "œ": "eu as in French peur", "ɤ": "o with the lips spread", "ɘ": "a mid central vowel", "ɵ": "a rounded mid central vowel",
  "ɜ": "ir as in British bird", "ɞ": "a rounded open-mid central vowel", "ɶ": "a with rounded lips",
  m: "m as in map", n: "n as in no", "ŋ": "ng as in sing", "ɲ": "ny as in canyon", "ɳ": "n with the tongue curled back",
  "ɴ": "n at the back of the throat", "ɱ": "m with lip on teeth, as in comfort",
  p: "p as in spin", b: "b as in bad", t: "t as in stop", d: "d as in day", k: "k as in skin", g: "g as in go", "ɡ": "g as in go",
  q: "k far back in the throat", "ɢ": "g far back in the throat", c: "between t and k, tongue on the palate",
  "ɟ": "between d and g, tongue on the palate", "ʈ": "t with the tongue curled back", "ɖ": "d with the tongue curled back",
  "ʔ": "the catch in uh-oh",
  "ɓ": "b with the air pulled in", "ɗ": "d with the air pulled in", "ʄ": "a palatal sound with the air pulled in",
  "ɠ": "g with the air pulled in", "ʛ": "a back g with the air pulled in",
  f: "f as in fan", v: "v as in van", s: "s as in sun", z: "z as in zoo", h: "h as in hat", "ʃ": "sh as in shoe",
  "ʒ": "s as in measure", "θ": "th as in thin", "ð": "th as in this", x: "ch as in Scottish loch",
  "ɣ": "a voiced loch sound", "χ": "a rasping ch far back", "ʁ": "r as in French rouge", "ħ": "a strong h from the throat",
  "ʕ": "a voiced squeeze in the throat", "ɸ": "f blown with both lips", "β": "b with the lips not quite closed",
  "ç": "h as in huge", "ʝ": "a voiced huge sound", "ɕ": "a soft sh, as in Mandarin x", "ʑ": "a soft zh",
  "ʂ": "sh with the tongue curled back", "ʐ": "zh with the tongue curled back", "ɬ": "ll as in Welsh Llanelli",
  "ɮ": "a voiced Welsh ll", "ɦ": "a breathy h", "ʍ": "wh as in which, in some accents",
  "ʦ": "ts as in cats", "ʣ": "ds as in beds", "ʧ": "ch as in church", "ʤ": "j as in judge", "ʨ": "a soft ch", "ʥ": "a soft j",
  l: "l as in let", r: "a rolled r", "ɾ": "the tt in American butter", "ɹ": "r as in English red", "ɻ": "r with the tongue curled back",
  "ɽ": "a flapped r with the tongue curled back", "ʀ": "a rolled r in the throat", "ɭ": "l with the tongue curled back",
  "ʎ": "lli as in million", "ʟ": "l at the back of the mouth", "ɫ": "the dark l in full", "ɺ": "a flapped l",
  w: "w as in wet", j: "y as in yes", "ɥ": "a rounded y, as in French huit", "ɰ": "w with the lips spread", "ʋ": "between v and w",
  "ǀ": "a tsk-tsk click", "ǁ": "the click used to urge a horse", "ǃ": "a cork-pop click", "ǂ": "a sharp palatal click", "ʘ": "a kissing click",
};
// Marks: what they add to the sound before them (ⁿ ᵐ ᵑ: to the sound after).
const MARK_HINT = {
  "ʰ": "with a puff of air", "ʱ": "breathy", "ʷ": "with rounded lips", "ʲ": "with a y-glide", "ˠ": "with the tongue raised at the back",
  "ː": "held long", "ˑ": "held a little longer", "ʼ": "popped with the throat closed", "ˀ": "with a catch in the throat",
  "̃": "through the nose", "̥": "whispered", "̊": "whispered", "̪": "with the tongue on the teeth",
  "̤": "breathy", "̰": "creaky", "̩": "as a syllable", "̯": "as a glide", "̆": "very short",
  "̟": "further forward", "̠": "further back", "̝": "raised", "̞": "lowered", "̹": "more rounded",
  "ⁿ": "with a short n before it", "ᵐ": "with a short m before it", "ᵑ": "with a short ng before it",
};
const PREFIX_MARKS = new Set(["ⁿ", "ᵐ", "ᵑ"]);
// Split a shape into segments the way oms/canon.graphemes does: a base letter
// plus its combining marks and attached modifier letters.
function soundSegments(shape) {
  const segs = []; let pre = [];
  for (const ch of shape.normalize("NFD")) {
    if (PREFIX_MARKS.has(ch)) { pre.push(ch); continue; }
    if (segs.length && (/\p{M}/u.test(ch) || (MARK_HINT[ch] && !SOUND_HINT[ch]))) { segs.at(-1).marks.push(ch); continue; }
    segs.push({ base: ch, marks: pre }); pre = [];
  }
  return segs.map(s => ({
    text: (s.marks.filter(m => PREFIX_MARKS.has(m)).join("") + s.base + s.marks.filter(m => !PREFIX_MARKS.has(m)).join("")).normalize("NFC"),
    hint: (SOUND_HINT[s.base] || "a sound with no everyday English match")
      + s.marks.map(m => MARK_HINT[m] ? `, ${MARK_HINT[m]}` : "").join(""),
  }));
}
// "m as in map, then a as in father" — for aria-labels and titles
const sayIt = shape => soundSegments(shape).map(s => s.hint).join(", then ");
const attr = s => s.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");

// DataStore contract (§10): blob build preloads forms.json; chunked build fetches
// per-shape chunks on demand. slugOf matches oms/bake._slug.
function slugOf(shape) { return "u" + [...shape].map(c => c.codePointAt(0).toString(16).padStart(4, "0")).join("-"); }
async function ensureShape(shape) {
  if (!CHUNKED || Object.values(FORMS).some(f => f.shape === shape)) return;
  try { Object.assign(FORMS, await getJSON(`${BASE}/shape/${slugOf(shape)}.json`)); } catch {}
}
async function loadConcept(ckey) {
  if (CONCEPTS[ckey]) return CONCEPTS[ckey];
  try { CONCEPTS[ckey] = await getJSON(`${BASE}/concept/${ckey}.json`); } catch { CONCEPTS[ckey] = null; }
  return CONCEPTS[ckey];
}
const state = {
  onset: null, nuc: null, shape: null, concept: null, language: null,
  onsetOn: new Set(ONSET_ORDER), tierOn: new Set(TIER),
  pins: [], route: "meanings",
  langRegion: null, langFamily: null, langSample: null,   // null = all; "" is a real value (Unlisted)
  langSyll: null, langTone: null,
  countBy: "families",
};

async function boot() {
  const cur = await getJSON("../data/current.json");
  BASE = `../data/${cur.dir || cur.version}`;
  CHUNKED = !!cur.chunked;
  CORE = await getJSON(`${BASE}/core.json`);
  // A Glottolog name can cover two glottocodes (Tuki ×3): the code tells them apart.
  const nameCount = new Map();
  for (const L of CORE.languages) nameCount.set(L.name, (nameCount.get(L.name) || 0) + 1);
  for (const L of CORE.languages) if (nameCount.get(L.name) > 1) L.name = `${L.name} (${L.glottocode})`;
  const seen = new Set(Object.values(CORE.postings).flatMap(ps => ps.map(p => p[1])));
  TIERS_PRESENT = TIER.map((_, i) => i).filter(i => seen.has(i));
  document.getElementById("tierLegend").innerHTML = "tier: " +
    TIERS_PRESENT.map(i => `${tierGlyphHTML(i)} ${TIER[i]}`).join(" ") + " &middot; a row with no mark is curated";
  FORMS = CHUNKED ? {} : await getJSON(`${BASE}/forms.json`);
  try { AUDIO = await getJSON("audio/manifest.json"); } catch { AUDIO = {}; }
  try { LAND = decodeLand(await getJSON("land-110m.json")); } catch { LAND = null; }
  document.getElementById("stamp").textContent =
    `data as of ${cur.version} · ${CORE.languages.length} languages · ${CORE.shapes.length} shapes` +
    (CHUNKED ? " (real datasets)" : " (seed)");
  document.getElementById("mstamp").textContent =
    `${(CORE.concepts || []).length} meanings · ${CORE.languages.length} languages`;
  document.getElementById("lstamp").textContent =
    `${CORE.languages.length} languages · ${families(CORE.languages.keys()).size} families`;
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
  wireCount();
  renderIntro();
  renderMeanings();
  renderLangFilters();
  renderLanguages();
  renderFilters();
  renderHeatmap();
  drawMap();
  renderAbout();
  renderSources();
  document.getElementById("conceptSearch").oninput = e => renderMeanings(e.target.value);
  document.getElementById("conceptSort").onchange = e => {
    state.conceptSort = e.target.value; renderMeanings(document.getElementById("conceptSearch").value);
  };
  document.getElementById("langSearch").oninput = e => renderLanguages(e.target.value);
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
  // deep links (shareable): #c=<meaning> · #l=<language> · #r=<region filter>
  // (#v= was the retired Look-alikes view; it now opens the same meaning)
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
    // Both branches below await a fetch (loadConcept / ensureShape), so a user can
    // click a meaning or a heatmap cell while this default selection is still in
    // flight. Re-check state right before committing so a real click always wins
    // over this fallback, instead of the fallback silently clobbering it on resolve.
    if ((CORE.concepts || []).length && !state.concept) await selectConcept(CORE.concepts[0].ckey, true);
    const top = CORE.shapes.slice().sort((a, b) =>
      (CORE.postings[b.shape] || []).length - (CORE.postings[a.shape] || []).length)[0];
    if (top && !state.onset) {
      state.onset = top.onset_class; state.nuc = top.nucleus_bucket; state.shape = top.shape;
      renderHeatmap(); await ensureShape(top.shape); renderShapes(); drawMap(); renderLangs();
    }
  }
}

let HASH_SELF = "";
function writeHash(s) { HASH_SELF = s; location.hash = s; }
async function applyHash() {
  const h = new URLSearchParams(location.hash.slice(1));
  if (h.get("c") || h.get("v")) { navigateTo("meanings"); await selectConcept(h.get("c") || h.get("v"), true); }
  else if (h.get("l")) { navigateTo("languages"); await selectLanguage(h.get("l"), true); }
  else if (h.has("r")) { navigateTo("languages"); setLangFilter("langRegion", h.get("r")); }
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
  const tierChips = TIERS_PRESENT.map(i => TIER[i]).map((t, k) =>
    chip(state.tierOn.has(t), "tier-" + t, `${tierGlyphHTML(TIERS_PRESENT[k])} ${t}`, `data-tier="${t}"`)).join("");
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
  return { langCount: best.size, famCount: families(best.keys()).size, comp, lis: [...best.keys()] };
}
// Could this language fill the cell? Only its PHOIBLE inventory can say: it
// must have a consonant of the onset class (none: no consonant needed) and a
// vowel of the bucket. null = no inventory, so the language sits out the
// comparison (roadmap 6; oms/typology.py). Diphthongs count only where the
// inventory lists one — many descriptions file them as vowel sequences.
function couldFill(L, o, n) {
  const inv = L.inventory;
  if (!inv) return null;
  return (o === "none" || inv.onsets.includes(o)) && inv.nuclei.includes(n);
}
function renderHeatmap() {
  const onsets = ONSET_ORDER.filter(o => CORE.shapes.some(s => s.onset_class === o));
  const nucs = NUC_ORDER.filter(n => CORE.shapes.some(s => s.nucleus_bucket === n));
  // Chance, counted by FAMILIES, among the families that COULD fill the cell
  // (roadmap 6). A cell's share = families using the onset and vowel together
  // in an open monosyllable ÷ families whose PHOIBLE inventories have both.
  // Its ratio = that share ÷ the share over all cells. Until 2026-10-01 the
  // expectation was row × column ÷ total over every language, which asked how
  // common the sounds are, not how often languages that have them combine them.
  const invLangs = CORE.languages.map((L, i) => i).filter(i => CORE.languages[i].inventory && CORE.languages[i].examined);
  const grid = {};
  let sumUse = 0, sumCould = 0;
  for (const o of onsets) {
    grid[o] = {};
    for (const n of nucs) {
      const st = cellStats(o, n);
      const could = invLangs.filter(i => couldFill(CORE.languages[i], o, n));
      const couldSet = new Set(could);
      st.could = familiesOrSelf(could);
      st.use = familiesOrSelf(st.lis.filter(i => couldSet.has(i)));
      sumUse += st.use; sumCould += st.could;
      grid[o][n] = st;
    }
  }
  const usual = sumCould ? sumUse / sumCould : 0;
  const ratioOf = (o, n) => grid[o][n].could && usual ? (grid[o][n].use / grid[o][n].could) / usual : 0;
  // The dial window: a fixed readout above the grid for the hovered/focused
  // cell — families, languages, tier composition, and the ratio when it is fair.
  const dialLine = (o, n) => {
    const { langCount, famCount, comp, use, could } = grid[o][n];
    const judged = could < MIN_FAMILIES
      ? `too few families with both sounds on record to compare`
      : `${use} of the ${could} families whose sound inventories have both use them together — ${verdict(ratioOf(o, n))}`;
    return `${ONSET_LABEL[o]} × <span class="ipa">${NUC_LABEL[n]}</span> — <b>${famCount}</b> famil${famCount === 1 ? "y" : "ies"} · ${langCount} language${langCount > 1 ? "s" : ""} · ${tierCompHTML(comp)} · ${judged}`;
  };
  const dialDefault = state.onset && grid[state.onset]?.[state.nuc]?.langCount
    ? dialLine(state.onset, state.nuc)
    : `<span class="note">click a cell to choose an onset × vowel — then pick a shape below</span>`;
  let h = `<div class="dial" id="dial" aria-live="polite">${dialDefault}</div>`;
  h += "<table class='heat'><thead><tr><th></th>";
  for (const n of nucs) h += `<th title="${NUC_HINT[n]}" aria-label="${NUC_HINT[n]}">${NUC_LABEL[n]}</th>`;
  h += "</tr></thead><tbody>";
  for (const o of onsets) {
    const dim = state.onsetOn.has(o) ? "" : " dim";
    h += `<tr><th class='row${dim}' title="${ONSET_HINT[o]}">${ONSET_LABEL[o]}</th>`;
    for (const n of nucs) {
      const { langCount, famCount } = grid[o][n];
      if (!langCount) { h += "<td class='empty'></td>"; continue; }
      const step = rampStep(famCount), thin = step < 0;
      const on = (state.onset === o && state.nuc === n) ? " on" : "";
      const label = `${famCount} famil${famCount === 1 ? "y" : "ies"}, ${langCount} language${langCount > 1 ? "s" : ""}`;
      h += `<td class="cell${on}${dim}${thin ? " thin" : ""}${step === 4 ? " deep" : ""}"${dim ? ' aria-disabled="true"' : ' tabindex="0"'}${thin ? "" : ` style="background:${RAMP[step]}"`} data-o="${o}" data-n="${n}"
              aria-label="${ONSET_HINT[o]}, plus ${NUC_HINT[n]}: ${label}"
              title="${label}"><div class="n">${famCount}</div></td>`;
    }
    h += "</tr>";
  }
  h += "</tbody></table><div class='shapes' id='shapes'></div>";
  const host = document.getElementById("heat"); host.innerHTML = h;
  const dial = document.getElementById("dial");
  host.querySelectorAll("td.cell").forEach(td => {
    if (td.classList.contains("dim")) return; // excluded by the user's own filter: inert
    td.onclick = () => {
      state.onset = td.dataset.o; state.nuc = td.dataset.n; state.shape = null; state.showRare = false;
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
// Chips are ordered by how widely a shape is shared — families, then languages —
// and carry that count (roadmap E4). One-language shapes fold behind "+N rare":
// a cell listed 100+ chips alphabetically, and /ma/ (366) looked like /m:ɑ/ (1).
function renderShapes() {
  const el = document.getElementById("shapes"); if (!el) return;
  const drill = document.getElementById("drill");
  if (!state.onset) { el.innerHTML = ""; drill.textContent = ""; return; }
  drill.innerHTML = `— ${ONSET_LABEL[state.onset]} × <span class="ipa">${NUC_LABEL[state.nuc]}</span>: pick a shape`;
  const ranked = cellShapes(state.onset, state.nuc).map(s => {
    const lis = activePostings(s.shape).map(p => p[0]);
    return { shape: s.shape, nl: new Set(lis).size, nf: families(lis).size };
  }).filter(x => x.nl).sort((a, b) => b.nf - a.nf || b.nl - a.nl || a.shape.localeCompare(b.shape));
  const rare = ranked.filter(x => x.nl === 1 && x.shape !== state.shape);
  const shown = state.showRare ? ranked : ranked.filter(x => !rare.includes(x));
  const chip = x => `<span class="shape ${state.shape === x.shape ? "sel" : ""}" tabindex="0" role="button" data-s="${x.shape}"
      aria-label="${attr(sayIt(x.shape))}: ${x.nl} language${x.nl > 1 ? "s" : ""}, ${x.nf} famil${x.nf === 1 ? "y" : "ies"}"
      title="${attr(sayIt(x.shape))}\n${x.nl} language${x.nl > 1 ? "s" : ""} in ${x.nf} famil${x.nf === 1 ? "y" : "ies"}">/${x.shape}/<span class="sc">${countBy() === "families" ? x.nf : x.nl}</span></span>`;
  el.innerHTML = shown.map(chip).join("") + (rare.length
    ? `<button class="go rare" type="button">${state.showRare ? "hide" : `+${rare.length}`} rare (one language each)</button>` : "");
  el.querySelectorAll(".shape").forEach(sp => sp.onclick = async () => {
    state.shape = sp.dataset.s; await ensureShape(state.shape); renderShapes(); drawMap(); renderLangs();
  });
  el.querySelector(".rare")?.addEventListener("click", () => { state.showRare = !state.showRare; renderShapes(); });
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
    const L = CORE.languages[p[0]];
    const d = FORMS[`${L.glottocode}|${state.shape}`] || {};
    const glosses = (d.words || []).flatMap(w => w.gloss_set.map(g => g.gloss));
    const words = glosses.slice(0, 3).join(", ") + (glosses.length > 3 ? ` +${glosses.length - 3}` : "");
    const tone = (d.words || [])[0]?.tone || "";
    const review = p[3] ? `<span class="review">* review</span>` : "";
    return `<div class="langrow" tabindex="0" role="button" data-key="${L.glottocode}|${state.shape}">
      <span class="ipa17">/${state.shape}${tone}/</span>
      <span class="gloss14">${words}</span>
      <span class="lname">${L.name}</span>
      ${toneNote(p[4])}${review}${tierMark(p[1])}</div>`;
  }).join("");
  // Tone: one shape, several words. The shape ignores pitch; these languages don't.
  const multi = posts.filter(p => p[4] > 1);
  const toneLine = multi.length
    ? `<p class="note">In ${multi.length} of these languages /${state.shape}/ is several words told apart by tone
        (pitch) — ${multi.reduce((a, p) => a + p[4], 0)} words in all. The shape ignores tone; the count beside a row says how many.</p>` : "";
  el.innerHTML = `<p class="conv">${playBtn(state.shape)} <span class="ipa22">/${state.shape}/</span> —
      ${spreadHTML(posts.map(p => p[0]))} · ${tierCompHTML(postComp)}
      <span class="note">(unmarked rows are curated; guesses never hidden)</span></p>
      <p class="note sayit">say it: ${sayIt(state.shape)}</p>${toneLine}${rows}`;
  el.querySelectorAll(".langrow").forEach(r => r.onclick = () => openSheet(r.dataset.key));
}

// "3 tones": the source gives this shape with three pitches in this language,
// so it is three words. 0 or 1 says nothing and shows nothing.
const toneNote = n => n > 1 ? `<span class="note" title="${n} words that differ only in tone (pitch)">${n} tones</span>` : "";

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
          ? `<a href="#c=${g.concepticon_id}" title="Concepticon ${g.concepticon_id}${g.linked_by ? ", matched by its English gloss" : ""} — jump to this concept" onclick="jumpConcept(${g.concepticon_id});return false">${g.gloss}</a>`
          : g.gloss).join(", ")}</span></div>`).join("")
    : `<p class="note">The source gives how this word is pronounced, not what it means. The sound stands on
        its own: many sources, especially dictionaries mined from Wiktionary, list pronunciations without meanings.</p>`;
  // the plain-word reading, one segment at a time (ux-design.md: IPA-as-hero accessibility)
  const say = `<p class="sayit">${soundSegments(f.shape).map(sg =>
      `<span class="seg"><span class="ipa17">${sg.text}</span> <span class="note">${sg.hint}</span></span>`).join(" ")}</p>`;
  document.getElementById("sheetBody").innerHTML = `
    <div class="sheet-hd">${playBtn(f.shape)} <span class="ipa" aria-label="${attr(sayIt(f.shape))}">/${f.shape}/</span> · ${L.name}
      <span class="badge b-${f.tier}">${TIER_GLYPH[TIER.indexOf(f.tier)]} ${f.tier}</span>
      ${ccBadge(f.classification_confidence, f.under_review)} ${audioLine}
      ${state.pins.includes(key)
        ? `<button class="pin" onclick="unpin('${key}');openSheet('${key}')">in compare ×</button>`
        : `<button class="pin" onclick="pin('${key}');openSheet('${key}')">+ compare</button>`}</div>
    ${say}
    <p class="note">${L.family || "family not given"} · ${yieldText(L)} examined are open monosyllables</p>
    <p class="note">source: ${f.preferred_source} (preferred of ${f.sources.join(", ")}) ·
       tones: ${f.tones.length ? `<span class="ipa">${f.tones.join(" ")}</span>${f.tones.length > 1 ? ` — ${f.tones.length} words told apart by pitch` : ""}` : L.tone_marked ? "none marked" : "not marked by this source"} · nucleus: ${f.nucleus_type}</p>
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
  // "beyond": only meanings with a shape more families share than any shuffle
  // gave, largest excess first (roadmap B1); otherwise broadest reach first
  const beyond = state.conceptSort === "beyond";
  // reach = families (default) or languages (the count toggle); builds before
  // 2026-10-01 have no fam_count and fall back to languages
  const fams = countBy() === "families" && (CORE.concepts || [])[0]?.fam_count != null;
  const reachOf = c => fams ? c.fam_count : c.lang_count;
  const list = (CORE.concepts || []).filter(c => (!q || c.gloss.toLowerCase().includes(q)) && (!beyond || c.beyond))
    .sort(beyond ? (a, b) => b.gap - a.gap || reachOf(b) - reachOf(a) : (a, b) => reachOf(b) - reachOf(a) || a.shape_count - b.shape_count);
  const max = Math.max(1, ...list.map(reachOf));
  el.innerHTML = list.slice(0, 300).map(c => {
    const conv = c.shape_count === 1 ? "1 shape" : `${c.shape_count} shapes`;
    const n = fams ? `${c.fam_count} famil${c.fam_count === 1 ? "y" : "ies"}` : `${c.lang_count} langs`;
    return `<div class="crow ${state.concept === c.ckey ? "sel" : ""}" tabindex="0" role="button" data-c="${c.ckey}"
        title="${c.lang_count} languages in ${c.fam_count ?? "?"} families">
      <span class="gloss">${c.gloss}</span>
      <span class="bar"><i class="s-data" style="width:${Math.round(100 * reachOf(c) / max)}%"></i></span>
      <span class="cnt">${n} · ${conv}${c.beyond ? ` · ${c.beyond} beyond chance` : ""}</span></div>`;
  }).join("") + (list.length > 300 ? `<p class="note">…${list.length - 300} more — search to narrow</p>` : "");
  el.querySelectorAll(".crow").forEach(r => r.onclick = () => selectConcept(r.dataset.c));
}

async function selectConcept(ckey, skipHash) {
  state.concept = ckey;
  if (!skipHash) writeHash("c=" + ckey);   // shareable deep link
  renderMeanings(document.getElementById("conceptSearch").value);
  const box = document.getElementById("conceptDetail"), head = document.getElementById("conceptSel");
  const d = await loadConcept(ckey);
  if (state.concept !== ckey) return; // a newer selection won the race while this one awaited
  if (!d) { box.innerHTML = `<p class="note">no data for this meaning</p>`; return; }
  head.textContent = `— ‘${d.gloss}’`;
  const byShape = new Map();
  for (const [li, shape, tone, tr, cr, ur] of d.entries) {
    if (!byShape.has(shape)) byShape.set(shape, []);
    byShape.get(shape).push({ li, tone, tr, ur });
  }
  // Rank shapes by how many FAMILIES use them, then languages: a shape shared
  // across families is the question worth asking; one shared inside a single
  // family is most likely one inherited word, however many languages carry it.
  const shapes = [...byShape.entries()]
    .map(([shape, rows]) => ({ shape, rows, lis: rows.map(r => r.li) }))
    .map(x => ({ ...x, nl: new Set(x.lis).size, nf: families(x.lis).size }))
    .sort((a, b) => b.nf - a.nf || b.nl - a.nl);
  // lede composition: each language once, at its most-trustworthy tier
  const best = new Map();
  for (const [li, , , tr] of d.entries) {
    const cur = best.get(li);
    if (cur === undefined || tr < cur) best.set(li, tr);
  }
  const ledeComp = [0, 0, 0];
  for (const t of best.values()) ledeComp[t]++;
  const B = CORE.meta.baseline, band = d.baseline || {};   // absent in builds before B1
  const conv = `<p class="conv">${spreadHTML(best.keys())} express <b>‘${d.gloss}’</b> as an open
    monosyllable, using <b>${byShape.size}</b> sound-shape${byShape.size > 1 ? "s" : ""}
    <span class="note">(${tierCompHTML(ledeComp)})</span>.</p>
    ${B ? `<p class="caveat">Beside each shape is what chance gives: how many families would share it if every
    language’s words were shuffled among its own meanings. <b>Beyond chance</b> means more families share it
    than that allows, even after counting every one of the ${(B.hypotheses ?? B.tested).toLocaleString()} sound–meaning
    pairs that could have come up — ${B.fdr ? `about 1 in ${Math.round(1 / B.fdr)} of the marked pairs may still be chance` : "a few may still be chance"}.
    A loanword (<i>tea</i>), a nursery word (<i>mama</i>) or an inherited word can all pass; it is not a claim
    of relatedness. ${B.beyond} pairs pass across the whole catalog.</p>` : ""}`;
  // card bodies lead with the word (attested tone form); the language name is
  // attribution — and a live link to the form sheet, not a dead end
  const blocks = shapes.map(({ shape, rows, lis, nl, nf }) => {
    // composition counts each language once, at its best tier, like the lede
    const bestOf = new Map();
    rows.forEach(r => bestOf.set(r.li, Math.min(r.tr, bestOf.get(r.li) ?? 9)));
    const comp = [0, 0, 0];
    for (const t of bestOf.values()) comp[t]++;
    const names = rows.map(r => {
      const L = CORE.languages[r.li];
      return `<span class="wlink" tabindex="0" role="button" title="${L.family || "family not given"} · ${TIER[r.tr]} tier — open this form" data-key="${L.glottocode}|${shape}" data-shape="${shape}">${r.tr ? tierGlyphHTML(r.tr) + " " : ""}${r.tone ? `<span class="ipa">${shape}${r.tone}</span> ` : ""}<span class="wname">${L.name}</span></span>${r.ur ? ` <span class="review">* review</span>` : ""}`;
    }).join(" · ");
    return `<div class="cshape"><div class="hd">
        ${AUDIO[shape] ? `<button class="play inline" onclick="playShape('${shape}')" aria-label="hear">▶</button>` : ""}
        <span class="ipa17">/${shape}/</span> <span class="note">${spreadHTML(lis)} · ${tierCompHTML(comp)}${bandHTML(band[shape])}</span>
        <button class="go" onclick="gotoShape('${shape}')">see in Sounds →</button></div>
      <div class="langs">${names}</div></div>`;
  }).join("");
  box.innerHTML = `<p class="convhd">‘${d.gloss}’</p>` + conv + blocks;
  box.querySelectorAll(".wlink").forEach(sp => sp.onclick = async () => {
    await ensureShape(sp.dataset.shape); openSheet(sp.dataset.key);
  });
}

// chance band for one shape card: "chance 0–2 families", and the verdict only
// when the observed count beats every shuffle (see oms/baseline.py)
// b = [observed, lo, hi, q]: q is the false-discovery-adjusted p-value (builds
// from 2026-10-01); older builds carried the largest shuffle in its place.
function bandHTML(b) {
  if (!b) return "";
  const [obs, lo, hi, q] = b;
  const fdr = CORE.meta.baseline?.fdr;
  const isBeyond = fdr ? q <= fdr : obs > q;
  return ` · chance ${lo}–${hi} famil${hi === 1 ? "y" : "ies"}${isBeyond ? ` · <b class="beyond">beyond chance</b>` : ""}`;
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
    for (const p of posts) idx[p[0]].shapes.push({ shape, tier: p[1], review: !!p[3], tones: p[4] || 0 });
  for (const e of idx) for (const s of e.shapes) e.comp[s.tier]++;
  return (LANG_INDEX = idx);
}

// A yield is read against its sample (CONTEXT.md "Examined"), with its 95%
// Wilson interval (roadmap B3). Languages rank by the interval's LOWER bound, so
// 1 of 1 words (20–100%) never outranks 180 of 185 (94–99%). This replaced a
// fixed 30-word cutoff: the interval says how sure, instead of a line saying who.
const rateOf = L => L.examined ? L.form_count / L.examined : 0;
const SAMPLE_ORDER = ["word list", "mixed", "dictionary", ""];
function wilson(k, n) {
  if (!n) return [0, 1];
  const z = 1.96, p = k / n, d = 1 + z * z / n, c = p + z * z / (2 * n);
  const h = z * Math.sqrt(p * (1 - p) / n + z * z / (4 * n * n));
  return [Math.max(0, (c - h) / d), Math.min(1, (c + h) / d)];
}
// one decimal under 10%, or Hindi's 0.4–0.6% reads "1% (0%–1%)"
const pct = x => `${x < 0.1 ? (100 * x).toFixed(1) : Math.round(100 * x)}%`;
function yieldText(L) {
  return `${L.form_count} of ${L.examined} word${L.examined === 1 ? "" : "s"}`;
}
function rangeText(L) {
  const [lo, hi] = wilson(L.form_count, L.examined);
  return `${pct(rateOf(L))} (${pct(lo)}–${pct(hi)})`;
}
// the interval drawn over the rate bar: a bracket from lower to upper bound
function ciHTML(L) {
  const [lo, hi] = wilson(L.form_count, L.examined);
  return `<b class="ci" style="left:${(100 * lo).toFixed(1)}%;width:${(100 * (hi - lo)).toFixed(1)}%"></b>`;
}
// Funnel plot (roadmap B3): each language's rate against the words examined,
// with 95% limits around the rate of every plotted language. Inside the funnel
// a language is within chance of that common rate; outside it stands out. One
// kind of sample at a time (B2): word lists unless the filter picks another.
function drawFunnel(langs) {
  const host = document.getElementById("langFunnel"); if (!host) return;
  const kind = state.langSample ?? "word list";
  const pts = langs.filter(L => L.examined > 0 && L.sample === kind);
  if (pts.length < 10) { host.innerHTML = ""; return; }
  const k = pts.reduce((a, L) => a + L.form_count, 0), n = pts.reduce((a, L) => a + L.examined, 0), p0 = k / n;
  const W = 520, H = 210, m = { l: 34, r: 8, t: 8, b: 30 };
  const lx = Math.log10, nMin = Math.min(...pts.map(L => L.examined)), nMax = Math.max(...pts.map(L => L.examined));
  const X = v => m.l + (lx(v) - lx(nMin)) / Math.max(1e-9, lx(nMax) - lx(nMin)) * (W - m.l - m.r);
  const Y = v => H - m.b - v * (H - m.t - m.b);
  const lim = (s, v) => Math.min(1, Math.max(0, p0 + s * 1.96 * Math.sqrt(p0 * (1 - p0) / v)));
  const steps = Array.from({ length: 60 }, (_, i) => nMin * (nMax / nMin) ** (i / 59));
  const line = s => "M" + steps.map(v => `${X(v).toFixed(1)},${Y(lim(s, v)).toFixed(1)}`).join(" L");
  let svg = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="funnel plot: share of open monosyllables against words examined, ${kind} samples">`;
  for (const t of [0, 0.25, 0.5, 0.75, 1]) svg += `<line x1="${m.l}" x2="${W - m.r}" y1="${Y(t)}" y2="${Y(t)}" stroke="#C9C6BF" stroke-width=".5"/><text x="${m.l - 4}" y="${Y(t) + 3}" font-size="8" text-anchor="end" fill="#64615A">${t * 100}%</text>`;
  for (const t of [10, 30, 100, 300, 1000, 3000, 10000, 30000].filter(t => t >= nMin && t <= nMax))
    svg += `<text x="${X(t)}" y="${H - m.b + 12}" font-size="8" text-anchor="middle" fill="#64615A">${t.toLocaleString()}</text>`;
  svg += `<text x="${(m.l + W - m.r) / 2}" y="${H - 4}" font-size="8" text-anchor="middle" fill="#64615A">words examined (log scale)</text>`;
  svg += `<path d="${line(1)}" fill="none" stroke="#A39F96" stroke-dasharray="3 2"/><path d="${line(-1)}" fill="none" stroke="#A39F96" stroke-dasharray="3 2"/>`;
  svg += `<line x1="${m.l}" x2="${W - m.r}" y1="${Y(p0)}" y2="${Y(p0)}" stroke="#4A4841" stroke-width=".8"/>`;
  let out = 0, selDot = "";
  const dots = pts.map(L => {
    const r = rateOf(L), above = r > lim(1, L.examined), below = r < lim(-1, L.examined);
    if (above || below) out++;
    const sel = state.language === L.glottocode;
    const fill = above ? "#2F5E6C" : below ? "#F2F1ED" : "#8B877E";
    const stroke = above || below ? "#2F5E6C" : "none";
    const dot = `<circle class="fdot" data-l="${L.glottocode}" cx="${X(L.examined).toFixed(1)}" cy="${Y(r).toFixed(1)}" r="${sel ? 4 : 2.2}" fill="${fill}" stroke="${sel ? "#21201C" : stroke}" stroke-width="${sel ? 1.5 : .8}"><title>${L.name} · ${yieldText(L)} · ${rangeText(L)}${above ? " · above the funnel" : below ? " · below the funnel" : ""}</title></circle>`;
    if (sel) { selDot = dot; return ""; }   // drawn last, so it is never covered
    return dot;
  });
  // If all languages shared one rate, about 5% would fall outside by chance.
  // Far more means they genuinely differ: the rate describes the language.
  const share = out / pts.length;
  // "the language, not the list" was too strong (2026-10-01 audit): sources
  // that segment diphthongs differently move a rate as much as languages do
  const reading = share > 0.1
    ? `rates differ far more than sample size explains — through the languages, but also through how each source writes and which words it lists`
    : `about what sample size alone gives`;
  host.innerHTML = svg + dots.join("") + selDot + `</svg><p class="note">${pts.length} ${kind} samples · solid line = their common rate, ${pct(p0)} ·
    dashed = where 95% would fall if all shared that rate · <b>${out}</b> (${pct(share)}) fall outside
    (<span style="color:#2F5E6C">●</span> above, <span style="color:#2F5E6C">○</span> below): ${reading}.</p>`;
  host.querySelectorAll(".fdot").forEach(c => c.onclick = () => selectLanguage(c.dataset.l));
}

function renderLangFilters() {
  const count = key => {
    const m = new Map();
    for (const L of CORE.languages) m.set(L[key] || "", (m.get(L[key] || "") || 0) + 1);
    return [...m.entries()].sort((a, b) => b[1] - a[1]);
  };
  const opts = (all, rows, none) => `<option value="*">${all}</option>` + rows.map(([k, n]) =>
    `<option value="${k}">${k || none} (${n})</option>`).join("");
  const reg = document.getElementById("langRegion"), fam = document.getElementById("langFamily");
  reg.innerHTML = opts("all regions", count("macroarea"), "Unlisted");
  fam.innerHTML = opts("all families", count("family"), "family not given");
  const smp = document.getElementById("langSample");
  smp.innerHTML = opts("all samples", count("sample").filter(([k]) => k), "");
  const syl = document.getElementById("langSyll"), ton = document.getElementById("langTone");
  const sylCount = new Map(count("syllable_structure"));
  syl.innerHTML = `<option value="*">any syllable structure</option>` + SYLL_ORDER.map(k =>
    `<option value="${k}">${SYLL_LABEL[k]} (${sylCount.get(k) || 0})</option>`).join("");
  const toned = CORE.languages.filter(L => L.tone_marked).length;
  ton.innerHTML = `<option value="*">tone marked or not</option><option value="yes">tone marked (${toned})</option>
    <option value="no">tone not marked (${CORE.languages.length - toned})</option>`;
  reg.onchange = () => setLangFilter("langRegion", reg.value);
  fam.onchange = () => setLangFilter("langFamily", fam.value);
  smp.onchange = () => setLangFilter("langSample", smp.value);
  syl.onchange = () => setLangFilter("langSyll", syl.value);
  ton.onchange = () => setLangFilter("langTone", ton.value);
}
// WALS 12A (Maddieson 2013), joined in oms/typology.py. "" = not in WALS.
const SYLL_ORDER = ["simple", "moderate", "complex", ""];
const SYLL_LABEL = { simple: "simple — CV only", moderate: "moderately complex", complex: "complex", "": "not classified by WALS" };
// Why some languages have more (roadmap 5): the median share of open
// monosyllables per WALS class, among the same kind of sample the funnel shows.
// research.md predicts simple > moderate > complex; the panel says whether the
// catalog agrees, and says so plainly when a class is too thin to tell.
function syllablePanel(langs) {
  const host = document.getElementById("langWhy"); if (!host) return;
  const kind = state.langSample ?? "word list";
  const rows = SYLL_ORDER.map(k => {
    const rs = langs.filter(L => (L.syllable_structure || "") === k && L.sample === kind && L.examined >= 20).map(rateOf).sort((a, b) => a - b);
    const q = f => rs.length ? rs[Math.min(rs.length - 1, Math.floor(f * rs.length))] : 0;
    return { k, n: rs.length, med: q(0.5), lo: q(0.25), hi: q(0.75) };
  });
  const known = rows.filter(r => r.k && r.n >= 5);
  if (!known.length) { host.innerHTML = ""; return; }
  const order = known.slice().sort((a, b) => b.med - a.med).map(r => r.k).join(" > ");
  // rates are small; scale the bars to the widest middle half, not to 100%
  const top = Math.max(...rows.filter(r => r.n).map(r => r.hi)) * 1.15 || 1;
  const X = v => (100 * v / top).toFixed(1);
  const agrees = known.length === 3 && order === "simple > moderate > complex";
  host.innerHTML = `<h2>Why some languages have more</h2>
    <p class="note">A language that only allows consonant + vowel syllables (WALS “simple”) builds most of its short
      words as open syllables; one that allows clusters and final consonants has other options. Median share of open
      monosyllables in ${kind}s of 20+ words, by the language’s syllable structure in WALS
      (the bar spans the middle half of languages):</p>
    <div class="regshare" role="table" aria-label="share of open monosyllables by syllable structure">` + rows.filter(r => r.n).map(r =>
      `<div class="rs" role="row"><span class="rsk" role="cell">${SYLL_LABEL[r.k]}</span>
        <span class="bar" role="cell"><i class="s-data" style="margin-left:${X(r.lo)}%;width:${X(Math.max(top / 200, r.hi - r.lo))}%;opacity:.45"></i><b class="ci" style="left:${X(r.med)}%;width:0"></b></span>
        <span class="rsn" role="cell">${pct(r.med)} median · ${r.n} language${r.n === 1 ? "" : "s"}${r.n < 5 ? " — too few to read" : ""}</span></div>`).join("") +
    `</div><p class="note">Bars run from 0 to ${pct(top)}; the tick is the median. ${agrees
      ? "The catalog agrees with the typology: the simpler the syllables a language allows, the more of its words are open monosyllables."
      : `In this selection the order is ${order}, not the simple > moderate > complex the typology predicts — read it with the small numbers in mind.`}
      WALS classifies only a few hundred languages, so most of the catalog sits in the last row.</p>`;
}
function setLangFilter(id, value) {
  const all = value == null || value === "*";
  state[id] = all ? null : value;
  document.getElementById(id).value = all ? "*" : value;
  if (id === "langRegion") writeHash(all ? "" : "r=" + encodeURIComponent(value));
  renderLanguages(document.getElementById("langSearch").value);
}
function renderLanguages(filter = "") {
  const el = document.getElementById("langList");
  const q = filter.trim().toLowerCase();
  const reg = state.langRegion, fam = state.langFamily, smp = state.langSample, syl = state.langSyll, ton = state.langTone;
  const idx = langIndex()
    .map((e, li) => ({ e, li }))
    .filter(({ e }) => (!q || e.L.name.toLowerCase().includes(q) || (e.L.alias || "").toLowerCase().includes(q))
      && (reg == null || (e.L.macroarea || "") === reg)
      && (fam == null || (e.L.family || "") === fam)
      && (smp == null || e.L.sample === smp)
      && (syl == null || (e.L.syllable_structure || "") === syl)
      && (ton == null || (ton === "yes") === !!e.L.tone_marked))
    .map(x => ({ ...x, lo: wilson(x.e.L.form_count, x.e.L.examined)[0] }))
    // a rate from a word list and one from a dictionary are not ranked together
    // (roadmap B2): group by kind of sample, then rank within it
    .sort((a, b) => SAMPLE_ORDER.indexOf(a.e.L.sample) - SAMPLE_ORDER.indexOf(b.e.L.sample)
      || b.lo - a.lo || b.e.L.examined - a.e.L.examined);
  const lis = idx.map(x => x.li);
  drawFunnel(idx.map(x => x.e.L));
  syllablePanel(idx.map(x => x.e.L));
  const head = `<p class="note">${spreadHTML(lis)} · ${idx.filter(x => x.e.shapes.length).length} with open monosyllables</p>`;
  el.innerHTML = head + idx.slice(0, 300).map(({ e }) => {
    const L = e.L;
    return `<div class="crow ${state.language === L.glottocode ? "sel" : ""}" tabindex="0" role="button" data-l="${L.glottocode}">
      <span class="gloss">${L.name}</span>
      <span class="bar">${stripSegs(e.comp, 100 * rateOf(L))}${ciHTML(L)}</span>
      <span class="cnt">${yieldText(L)} · ${rangeText(L)}${L.sample && L.sample !== "word list" ? ` · ${L.sample}` : ""} · ${L.family || "family not given"}</span></div>`;
  }).join("") + (idx.length > 300 ? `<p class="note">…${idx.length - 300} more — search or filter to narrow</p>` : "");
  el.querySelectorAll(".crow").forEach(r => r.onclick = () => selectLanguage(r.dataset.l));
}
const LANG_GLOSS = {};
async function langGlosses(gc) {
  if (!(gc in LANG_GLOSS)) {
    try { LANG_GLOSS[gc] = CHUNKED ? await getJSON(`${BASE}/lang/${gc}.json`) : null; } catch { LANG_GLOSS[gc] = null; }
  }
  return LANG_GLOSS[gc];
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
  const glosses = await langGlosses(gc);
  if (state.language !== gc) return;   // a newer selection won while this one loaded
  head.textContent = `— ${L.name}`;
  // How widely each shape is shared beyond this language: the one question a
  // shape answers even when the source gives no meanings (roadmap 4).
  const spread = sh => {
    const others = (CORE.postings[sh] || []).map(p => p[0]).filter(i => i !== li);
    const ownFam = L.family;
    return { langs: new Set(others).size, fams: new Set(others.map(i => familyOf(i) || `lang:${i}`).filter(f => f !== ownFam)).size };
  };
  const hasWords = e.shapes.some(s => (glosses?.[s.shape] || []).length
    || (FORMS[`${gc}|${s.shape}`]?.words || []).length);
  const byOnset = (a, b) => (ONSET_ORDER.indexOf(meta[a.shape]?.onset_class) - ONSET_ORDER.indexOf(meta[b.shape]?.onset_class))
    || a.shape.localeCompare(b.shape);
  // with meanings: the sound system's order; sounds only: the widest-shared first
  const shapes = e.shapes.map(s => ({ ...s, sp: spread(s.shape) }))
    .sort(hasWords ? byOnset : (a, b) => b.sp.fams - a.sp.fams || b.sp.langs - a.sp.langs || byOnset(a, b));
  const loc = (L.longitude == null || L.latitude == null)
    ? `<span class="review">no coordinates — listed but unmapped</span>`
    : `${L.latitude.toFixed(1)}, ${L.longitude.toFixed(1)}`;
  const share = L.examined ? ` — ${rangeText(L)}` : "";
  const words = e.shapes.reduce((a, s) => a + Math.max(1, s.tones), 0);
  const toneLine = words > e.shapes.length
    ? ` Counting tone, they are <b>${words}</b> different words: ${e.shapes.filter(s => s.tones > 1).length} of the shapes carry more than one pitch.` : "";
  const conv = e.shapes.length
    ? `<p class="conv"><b>${L.name}</b> has <b>${e.shapes.length}</b> open monosyllable${e.shapes.length > 1 ? "s" : ""}
      among the <b>${L.examined}</b> words examined${share} <span class="note">(${tierCompHTML(e.comp)})</span>.${toneLine}</p>`
    : `<p class="conv">No open monosyllables among the <b>${L.examined}</b> words examined for <b>${L.name}</b>.</p>
      <p class="note">That describes the sample, not the language: a longer word list may hold some.</p>`;
  const soundsOnly = e.shapes.length && !hasWords
    ? `<p class="caveat"><b>Sounds only.</b> The source for ${L.name} lists how words are pronounced but not what they
        mean, so this page is about the sounds: where they fall in the language’s sound system, and how many other
        languages share each one. Shapes found in the most other families come first.</p>` : "";
  const facts = `<p class="note">${L.alias ? `source name: ${L.alias} · ` : ""}family: ${L.family || "not given"} · region: ${L.macroarea || "unlisted"} ·
      location: ${loc} · sample: ${L.sample || "none"} · syllable structure (WALS): ${L.syllable_structure ? SYLL_LABEL[L.syllable_structure] : "not classified"} ·
      tone: ${L.tone_marked ? "marked by the source" : "not marked by the source"} · the range is a 95% interval for sampling noise in ${L.examined} words; a different word list could move the share further</p>`;
  const blocks = shapes.slice(0, 400).map(s => {
    // meanings belong beside the word: the build's per-language gloss file
    // (lang/<glottocode>.json) has them all, one request per language
    const w = glosses?.[s.shape] || (FORMS[`${gc}|${s.shape}`]?.words || []).flatMap(x => x.gloss_set.map(g => g.gloss));
    const gl = w.slice(0, 3).join(", ") + (w.length > 3 ? ` +${w.length - 3}` : "");
    const shared = s.sp.langs
      ? `also in ${s.sp.langs} language${s.sp.langs === 1 ? "" : "s"}${s.sp.fams ? `, ${s.sp.fams} other famil${s.sp.fams === 1 ? "y" : "ies"}` : ", all in its family"}`
      : "found only here";
    // portal card: names ONE form, so its whole surface opens the sheet
    return `<div class="cshape portal" data-key="${gc}|${s.shape}" data-shape="${s.shape}"><div class="hd">
      ${AUDIO[s.shape] ? `<button class="play inline" onclick="playShape('${s.shape}')" aria-label="hear">▶</button>` : ""}
      <span class="lshape" tabindex="0" role="button" data-key="${gc}|${s.shape}" data-shape="${s.shape}" aria-label="${attr(sayIt(s.shape))}" title="${attr(sayIt(s.shape))}"><span class="ipa17">/${s.shape}/</span></span>
      ${gl ? `<span class="gloss14">${gl}</span>` : `<span class="note">${shared}</span>`}
      ${toneNote(s.tones)}
      ${tierMark(s.tier)}
      ${s.review ? `<span class="review">* review</span>` : ""}
      <button class="go" onclick="gotoShape('${s.shape}')">see in Sounds →</button></div>
      ${gl ? `<div class="langs note">${shared}</div>` : ""}</div>`;
  }).join("")
    + (shapes.length > 400 ? `<p class="note">…${shapes.length - 400} more shapes</p>` : "");
  box.innerHTML = conv + soundsOnly + facts + langGridHTML(e.shapes, meta) + blocks;
  // the whole portal card opens the form sheet; inner keys win over the container
  box.querySelectorAll(".cshape.portal").forEach(c => c.onclick = async e => {
    if (e.target.closest("button,a,.lshape")) return;
    await ensureShape(c.dataset.shape); openSheet(c.dataset.key);
  });
  box.querySelectorAll(".lshape").forEach(sp => sp.onclick = async () => {
    await ensureShape(sp.dataset.shape); openSheet(sp.dataset.key);
  });
}

// One language's own onset × vowel grid: how many of its shapes fall in each
// cell. The catalog heatmap in miniature, so a sounds-only page still shows the
// shape of the language's sound system, not just a list.
function langGridHTML(shapes, meta) {
  if (!shapes.length) return "";
  const cell = {};
  for (const s of shapes) {
    const m = meta[s.shape]; if (!m) continue;
    const k = `${m.onset_class}|${m.nucleus_bucket}`;
    cell[k] = (cell[k] || 0) + 1;
  }
  const onsets = ONSET_ORDER.filter(o => NUC_ORDER.some(n => cell[`${o}|${n}`]));
  const nucs = NUC_ORDER.filter(n => onsets.some(o => cell[`${o}|${n}`]));
  const max = Math.max(...Object.values(cell));
  let h = `<table class="heat mini" aria-label="where its open monosyllables fall: how they start and which vowel"><thead><tr><th></th>`
    + nucs.map(n => `<th title="${NUC_HINT[n]}">${NUC_LABEL[n]}</th>`).join("") + "</tr></thead><tbody>";
  for (const o of onsets) {
    h += `<tr><th class="row" title="${ONSET_HINT[o]}">${ONSET_LABEL[o]}</th>`;
    for (const n of nucs) {
      const c = cell[`${o}|${n}`] || 0;
      const step = c ? Math.min(4, Math.floor(4 * c / max)) : -1;
      h += c ? `<td class="cell static${step === 4 ? " deep" : ""}" style="background:${RAMP[step]}" title="${c} shape${c > 1 ? "s" : ""}: ${ONSET_HINT[o]}, ${NUC_HINT[n]}"><div class="n">${c}</div></td>`
        : `<td class="empty"></td>`;
    }
    h += "</tr>";
  }
  return `<h2>Where its open monosyllables fall</h2>${h}</tbody></table>
    <p class="note">rows = how the word starts · columns = its vowel · number = shapes in this language</p>`;
}

window.selectLanguage = selectLanguage;

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
    <p>Syllables are counted the way each source wrote the word. Two vowels written as separate sounds are
    two syllables — Māori <span class="ipa">/ru.a/</span> ‘two’ is not included. Two vowels count as one gliding
    vowel only when the source says so. Sources that give spellings instead of sounds are converted first, and
    their vowel pairs are left out, because a spelling cannot tell the two cases apart.</p>

    <h3>How much to trust each sound</h3>
    <p>Every pronunciation carries a small mark for how it was sourced: ${g(0)} <b>curated</b> comes from a
    <a onclick="navigateTo('sources')">checked linguistic database</a>, ${g(1)} <b>mined</b> is drawn from dictionaries, and ${g(2)} <b>generated</b>
    is a careful guess from spelling. We never hide the guesses — for many under-documented languages they are
    all that exists — and every count of languages is broken down by these marks, so you can
    see at a glance whether you’re standing on solid ground or thin ice.${TIERS_PRESENT.includes(2) ? "" : `
    This build has no generated forms: every sound comes from a curated database or a dictionary.`}</p>
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
    unrelated languages largely because it’s among the first sounds a baby makes. What we do show is how many
    language <i>families</i> share a sound: a hundred related languages agreeing is one inherited word, while
    a handful of unrelated families agreeing is the more curious fact. To tell that from coincidence, each shape
    is set against chance: each language’s words shuffled among its own meanings. A shape more families share than
    that allows — after counting every sound–meaning pair that could have come up, so that about 1 in 20 marks may
    still be luck — is marked <i>beyond chance</i>. Often it is a loanword or a nursery word.</p>

    <h3>Why coverage is uneven</h3>
    <p>Some languages simply have few open syllables; most are just thinly sampled. Every language is shown
    against the words its sources give — <b>12 of 187</b> means 12 open monosyllables among 187 words examined —
    because a 200-word list and a whole dictionary are not the same evidence.
    <a onclick="navigateTo('explore')">On the map</a>, a hollow ring means none turned up among the words
    examined. That is a fact about the sample, not a claim about the language.</p>
    <p>Many languages in the catalog belong to a few large families — Austronesian alone is nearly a third.
    So numbers count families first; the <b>counting</b> switch at the top changes that to single languages.</p>

    <h3>Why some languages have more</h3>
    <p>A language whose syllables are all consonant + vowel (what the World Atlas of Language Structures calls
    “simple” syllable structure) builds most of its short words as open syllables. A language that allows
    clusters like <i>str</i> and final consonants like <i>-nk</i> has other options, and fewer of its words end
    up open. <a onclick="navigateTo('languages')">The Languages page</a> sets each language’s share beside its WALS
    class. Some languages also require every word to be “heavy” — a long vowel or two syllables — which rules
    out short open words almost entirely; no dataset records that rule for most languages yet, so the catalog
    can show its effect but not label it.</p>

    <h3>How the Sounds grid compares cells</h3>
    <p>Each cell of the grid is compared only with the language families that <i>could</i> fill it: families
    whose sound inventories (from PHOIBLE) have both the consonant and the vowel. “1.8× the usual share” means
    those families combine the two into a one-syllable word 1.8 times as often as families combine sounds in an
    average cell. It describes; it is not a test against chance. Languages with no inventory on record are counted
    in the cell’s number but sit out the comparison.</p>

    <h3>Tone</h3>
    <p>In many languages pitch tells words apart: Yoruba <span class="ipa">ba</span> said high, mid or low is three
    words. The sound-shapes here ignore pitch so that the same syllable lines up across languages, but each
    language still shows how many tones its source gives a shape (“3 tones” = three words). Many sources don’t
    write tone at all, so “tone not marked” is a fact about the source, not the language.</p>

    <h3>Words used here</h3>
    <dl class="gloss">
      <dt>open monosyllable</dt><dd>a word of one syllable that ends on a vowel: <i>ma</i>, <i>tea</i>, <i>bye</i>.</dd>
      <dt>shape</dt><dd>the sound of such a word, written between slashes in the phonetic alphabet (<span class="ipa">/ma/</span>), with pitch left out so it can be matched across languages.</dd>
      <dt>language family</dt><dd>languages descended from one ancestor, like Austronesian or Sino-Tibetan.</dd>
      <dt>words examined</dt><dd>how many words the sources gave for a language — every share is read against it.</dd>
      <dt>curated, mined, generated</dt><dd>where a pronunciation came from: a checked linguistic database, a dictionary, or a guess from spelling.</dd>
      <dt>pending review</dt><dd>linguists could reasonably disagree whether this word is one open syllable.</dd>
      <dt>beyond chance</dt><dd>more families share this sound for this meaning than reshuffling each language’s words would give, judged so that about 1 in 20 such marks may still be luck.</dd>
      <dt>sounds only</dt><dd>the source gives pronunciations without meanings; the language page shows its sounds instead.</dd>
    </dl>`;
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
    <table class="src"><thead><tr><th>source</th><th>tier</th><th>license</th></tr></thead><tbody>${rows}</tbody></table>
    <p>Language names are Glottolog’s (<a href="https://glottolog.org" target="_blank" rel="noopener">Glottolog 5.3</a>,
    Hammarström, Forkel, Haspelmath &amp; Bank, CC-BY 4.0); each source’s own name for a language is kept as its alias.
    Coastlines: Natural Earth, via world-atlas (public domain).</p>`;
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
// The map answers one question: where is the selected shape, against where we
// looked? So it has two layers, drawn in that order. Context: every examined
// language, small and quiet — "none found in the sample" is context too, not a
// louder ring. Answer: the languages with the shape, drawn LAST in the data hue
// with a page-coloured ring, so a dense cluster stays countable and nothing hides
// a hit (before 2026-09-29, 216 of 369 /ma/ dots sat under an unselected dot).
// Proportion, which dots cannot show, is the regional strip under the map.
const INK_2 = "#4A4841", INK_3 = "#64615A", DATA = "#2F5E6C", RING = "#F2F1ED", ALARM = "#A63A22";
function drawMap() {
  const posts = state.shape ? activePostings(state.shape) : [];
  const withShape = new Set(posts.map(p => p[0]));
  const review = new Set(posts.filter(p => p[3]).map(p => p[0]));
  let ctx = "", hits = "", unmapped = 0;
  CORE.languages.forEach((L, i) => {
    if (L.longitude == null || L.latitude == null) { unmapped++; return; } // listed but unmapped — never plotted at (0,0)
    const [ex, ey] = equalEarth(L.longitude, L.latitude);
    const x = mapX(ex).toFixed(1), y = mapY(ey).toFixed(1);
    const none = L.form_count === 0;
    const title = `<title>${L.name} · ${L.family || "family not given"} · ${yieldText(L)}${none ? " — none found in this sample" : ""}</title>`;
    if (state.shape && withShape.has(i)) {
      // review is an annotation beside the dot, never a recolor of it
      const flag = review.has(i) ? `<rect x="${(+x + 2.4).toFixed(1)}" y="${(+y - 5.6).toFixed(1)}" width="3" height="3" fill="${ALARM}"/>` : "";
      hits += `<circle class="dothit" tabindex="0" role="button" data-li="${i}" cx="${x}" cy="${y}" r="3.2" fill="${DATA}" stroke="${RING}" stroke-width=".9">${title}</circle>${flag}`;
    } else if (state.shape) {
      ctx += `<circle cx="${x}" cy="${y}" r="1.4" fill="${INK_3}">${title}</circle>`;   // recede by size, not below the 3:1 ink floor
    } else {
      ctx += none
        ? `<circle cx="${x}" cy="${y}" r="1.8" fill="none" stroke="${INK_3}" stroke-width=".7">${title}</circle>`
        : `<circle cx="${x}" cy="${y}" r="1.9" fill="${INK_2}">${title}</circle>`;
    }
  });
  document.getElementById("map").innerHTML =
    `<svg viewBox="0 0 ${MAP_W} ${MAP_H}" role="img" aria-label="${state.shape ? `world map: languages with /${state.shape}/` : "world map of languages"}">`
    + buildBasemap() + `<g>${ctx}</g><g>${hits}</g>` + mapLegend(review.size > 0) + "</svg>" + regionShareHTML(withShape);
  // the advertised loop closes on the map itself: lit dot → form sheet
  document.querySelectorAll("#map .dothit").forEach(c =>
    c.onclick = () => openSheet(`${CORE.languages[+c.dataset.li].glottocode}|${state.shape}`));
  const unmappedNote = unmapped ? `${unmapped} language(s) lack coordinates and are listed but not mapped.` : "";
  document.getElementById("mapnote").innerHTML = (state.shape ? "" : "Pick a shape to light up the languages that have it. ") + unmappedNote;
}
// Legend inside the map, in the empty South Pacific: identity is never colour alone.
function mapLegend(anyReview) {
  const row = (y, mark, text) => `<g transform="translate(26 ${y})">${mark}<text x="9" y="3" font-size="8" fill="${INK_2}" font-family="system-ui,sans-serif">${text}</text></g>`;
  const rows = state.shape
    ? [row(0, `<circle r="3.2" fill="${DATA}" stroke="${RING}" stroke-width=".9"/>`, `has /${state.shape}/`),
       row(11, `<circle r="1.4" fill="${INK_3}"/>`, "examined, does not have it"),
       ...(anyReview ? [row(22, `<rect x="-1.5" y="-1.5" width="3" height="3" fill="${ALARM}"/>`, "pending review")] : [])]
    : [row(0, `<circle r="1.9" fill="${INK_2}"/>`, "has open monosyllables"),
       row(11, `<circle r="1.8" fill="none" stroke="${INK_3}" stroke-width=".7"/>`, "none among the words examined")];
  return `<g aria-hidden="true" transform="translate(0 ${MAP_H - 44})">${rows.join("")}</g>`;
}
// Share of each region's languages that have the shape. Denominator: languages
// with any open monosyllable in their sample — the ones that COULD show it.
function regionShareHTML(withShape) {
  if (!state.shape) return "";
  const reg = new Map();
  CORE.languages.forEach((L, i) => {
    if (!L.form_count) return;
    const k = L.macroarea || "Unlisted";
    const r = reg.get(k) || { k, n: 0, hit: [], all: [] };
    r.n++; r.all.push(i); if (withShape.has(i)) r.hit.push(i);
    reg.set(k, r);
  });
  // by families: of the region's families with any open monosyllable, how many
  // have the shape in at least one language — one big family is one vote
  const byFam = countBy() === "families";
  const num = r => byFam ? familiesOrSelf(r.hit) : r.hit.length, den = r => byFam ? familiesOrSelf(r.all) : r.n;
  // a region needs 5 languages, or 3 families when counting families
  // (Australia is one family, Pama-Nyungan: "1 of 1 · 100%" says nothing)
  const rows = [...reg.values()].filter(r => r.n >= 5 && (!byFam || den(r) >= 3))
    .sort((a, b) => num(b) / den(b) - num(a) / den(a));
  const unit = byFam ? "families" : "languages";
  return `<div class="regshare" role="table" aria-label="share of each region's ${unit} with /${state.shape}/">` + rows.map(r => {
    const pct = 100 * num(r) / den(r);
    return `<div class="rs" role="row"><span class="rsk" role="cell">${r.k}</span>
      <span class="bar" role="cell"><i class="s-data" style="width:${pct.toFixed(1)}%"></i></span>
      <span class="rsn" role="cell">${num(r)} of ${den(r)} ${unit} · ${Math.round(pct)}%</span></div>`;
  }).join("") + `</div>`;
}

/* ---------- onboarding: a plain first-visit explainer (no tour) ---------- */
// Shown at the top of the landing view on a first visit, and on demand from
// "What is this?". It says what the page is, how to read /ma/, where to start,
// and the two cautions that keep the numbers honest. Dismissal is remembered
// per browser; storage can be blocked, so every access is guarded.
const INTRO_KEY = "oms-intro-dismissed";
function introSeen() { try { return localStorage.getItem(INTRO_KEY) === "1"; } catch { return false; } }
function renderIntro(force) {
  const el = document.getElementById("intro");
  if (!force && introSeen()) { el.classList.add("hidden"); return; }
  const ex = (CORE.concepts || []).find(c => c.gloss === "mother") || (CORE.concepts || [])[0];
  const fams = families(CORE.languages.keys()).size;
  el.innerHTML = `<h2 id="introTitle">New here? This is what you’re looking at.</h2>
    <p>Most languages have short words like <span class="ipa17">ma</span>, <span class="ipa17">tu</span> or
      <span class="ipa17">ko</span>: <b>one syllable that ends on a vowel</b>. Linguists call them <i>open
      monosyllables</i>. This site gathers them from <b>${CORE.languages.length.toLocaleString()} languages</b> in
      ${fams} families, so you can see which sounds and meanings turn up where.</p>
    <p><span class="ex">/ma/</span> — a word between slashes is written by how it <i>sounds</i>, in the
      International Phonetic Alphabet. You don’t need to know it: hover over or tap a shape for a plain reading
      (<span class="ipa">/ma/</span> is “${sayIt("ma")}”), and ▶ plays a computer voice reading it.</p>
    <p>Three ways in:</p>
    <ol>
      <li><b>Meanings</b> (this page): pick a meaning such as ‘${ex ? ex.gloss : "water"}’ and see the short words languages use for it.</li>
      <li><b>Sounds</b>: a grid of how words start (rows) and which vowel they have (columns). Pick a cell, then a shape, and the map shows where on Earth it is said.</li>
      <li><b>Languages</b>: pick one language and see all of its short open words, what they mean, and how common they are in it.</li>
    </ol>
    <p>Two things to keep in mind:</p>
    <ol>
      <li><b>Look-alikes are usually chance.</b> Words this short often match by accident; a match across
        languages is not evidence they are related. Where a match is more than chance, the page says so — and even
        then it is often a borrowed word or a baby-talk word like <i>mama</i>.</li>
      <li><b>Counts are by family.</b> A hundred related languages that share a word inherited it once, so numbers
        count language families first. The <b>counting</b> switch at the top changes this to single languages.</li>
    </ol>
    <p class="note">Small marks: ${tierGlyphHTML(1)} <i>mined</i> means the pronunciation comes from a dictionary
      rather than a checked linguistic database; <span class="review">* review</span> means linguists could disagree
      whether the word counts. Unmarked rows come from checked databases.</p>
    <div class="row">
      ${ex ? `<button class="go" type="button" id="introTry">Start with ‘${ex.gloss}’ →</button>` : ""}
      <button class="pin" type="button" id="introClose">Got it, hide this</button>
      <a onclick="navigateTo('about')">read more about how it works</a>
    </div>`;
  el.classList.remove("hidden");
  document.getElementById("introClose").onclick = () => {
    try { localStorage.setItem(INTRO_KEY, "1"); } catch {}
    el.classList.add("hidden");
  };
  document.getElementById("introTry")?.addEventListener("click", () => {
    selectConcept(ex.ckey);
    document.getElementById("conceptDetail").scrollIntoView({ block: "start", behavior: "smooth" });
  });
}

// The counting switch (roadmap 7): families ⇄ languages, everywhere it applies.
function wireCount() {
  const b = document.getElementById("countBtn");
  const paint = () => {
    b.textContent = `counting: ${state.countBy}`;
    b.setAttribute("aria-pressed", String(state.countBy === "families"));
  };
  paint();
  b.onclick = () => {
    state.countBy = state.countBy === "families" ? "languages" : "families";
    paint();
    renderMeanings(document.getElementById("conceptSearch").value);
    renderShapes(); drawMap();
  };
  document.getElementById("introBtn").onclick = () => { navigateTo("meanings"); renderIntro(true); window.scrollTo(0, 0); };
}

/* ---------- routing ---------- */
const ROUTES = ["meanings", "explore", "languages", "compare", "about", "sources"];
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
