const $ = (id) => document.getElementById(id);

const PLANT_TOPICS = ["name", "uses", "lookalikes", "identify"];
const BIRD_TOPICS = ["call", "name", "uses", "lookalikes", "identify"];

function topicsFor(subject) {
  return subject === "birds" ? BIRD_TOPICS : PLANT_TOPICS;
}

function topicChoices(subject) {
  if (subject === "birds") {
    return [
      ["call", "Name from the call"],
      ["name", "Name from the picture"],
      ["uses", "Voice and diet"],
      ["lookalikes", "Look-alikes"],
      ["identify", "How to identify it"],
    ];
  }
  return [
    ["name", "Name from the picture"],
    ["uses", "Uses"],
    ["lookalikes", "Look-alikes"],
    ["identify", "How to identify it"],
  ];
}

function defaultTopic(subject) {
  return subject === "birds" ? "call" : "name";
}
const COPY = {
  plants: {
    eyebrow: "Western North Carolina",
    title: "Plant Flashcards",
    docTitle: "WNC Plant Flashcards",
    noun: "plants",
    countTail: "start with the most common five",
    place: "Where in WNC",
    usesLabel: "Uses",
    topicUses: "Uses",
    question: {
      name: "What plant is this?",
      uses: "what is it used for?",
      lookalikes: "what is a look-alike?",
      identify: "how do you know it?",
    },
    flip: {
      name: ["Show name & uses", "Hide name"],
      uses: ["Show the uses", "Hide the uses"],
      lookalikes: ["Show the look-alikes", "Hide the look-alikes"],
      identify: ["Show how to identify it", "Hide identification"],
    },
    categories: [
      ["all", "All types"],
      ["tree", "Trees"],
      ["shrub", "Shrubs"],
      ["vine", "Vines"],
      ["wildflower", "Wildflowers"],
      ["fern", "Ferns"],
      ["grass", "Grasses"],
    ],
    origins: [
      ["all", "Native + invasive"],
      ["native", "Native / indigenous"],
      ["invasive", "Invasive"],
    ],
    photoAlt: "Plant photo",
    identifyAlt: "Identify this plant",
    noPhoto: "No photo — flip for the name.",
    empty: "No plants match these filters",
    quizEmpty: "Need a couple of unlocked plants to quiz.",
    footerMain: "Photos from Wikipedia / Wikimedia Commons, saved on this computer. On a card with several pictures, swipe or use the arrows for leaves, bark, and branches. Plant facts checked against NC Cooperative Extension, NC Native Plant Society, NC Forest Service, and NC Invasive Plant Council lists.",
    footerFine: "Western NC has 2,000+ vascular plants. This deck is the common, useful, iconic, and invasive species you are most likely to need. Traditional uses are historical — not medical or foraging advice. Never eat a plant unless you are certain of the ID and the part that is actually edible.",
  },
  birds: {
    eyebrow: "North Carolina",
    title: "Bird Flashcards",
    docTitle: "NC Bird Flashcards",
    noun: "birds",
    countTail: "common birds first, including introduced species",
    place: "Where in North Carolina",
    usesLabel: "Voice and diet",
    topicUses: "Voice and diet",
    question: {
      call: "Which bird made this call?",
      name: "What bird is this?",
      uses: "what does it sound like, and what does it eat?",
      lookalikes: "what is a look-alike?",
      identify: "how do you know it?",
    },
    flip: {
      call: ["Show the bird", "Hide the bird"],
      name: ["Show name & voice", "Hide name"],
      uses: ["Show voice and diet", "Hide voice and diet"],
      lookalikes: ["Show the look-alikes", "Hide the look-alikes"],
      identify: ["Show how to identify it", "Hide identification"],
    },
    categories: [
      ["all", "All types"],
      ["songbird", "Songbirds"],
      ["woodpecker", "Woodpeckers"],
      ["raptor", "Raptors"],
      ["waterfowl", "Waterfowl"],
      ["wader", "Waders"],
      ["waterbird", "Water birds"],
      ["shorebird", "Shorebirds"],
      ["seabird", "Seabirds"],
      ["nightbird", "Night birds"],
      ["aerial", "Aerial"],
      ["dove", "Doves"],
      ["gamebird", "Game birds"],
    ],
    origins: [
      ["all", "Native + introduced"],
      ["native", "Native"],
      ["nonnative", "Introduced or invasive"],
    ],
    photoAlt: "Bird photo",
    identifyAlt: "Identify this bird",
    noPhoto: "No photo yet — flip for the name.",
    empty: "No birds match these filters",
    quizEmpty: "Need a couple of unlocked birds to quiz.",
    footerMain: "Photos and calls from Wikipedia / Wikimedia Commons, saved on this computer. Play call on a card to hear that bird. This deck is common North Carolina birds you are likely to meet — natives plus introduced birds — not every rarity on the state list.",
    footerFine: "Native migratory birds are protected. Do not disturb nests. Established introduced birds here include the house sparrow, European starling, Eurasian collared-dove, and rock pigeon. House finch is introduced in the East. Mute swan and muscovy duck are introduced and are not established statewide breeders. Cattle egret colonized on its own and is treated as native.",
  },
};

function emptyTopicMap(fill) {
  return { call: fill, name: fill, uses: fill, lookalikes: fill, identify: fill };
}

const state = {
  mode: "study",
  subject: "plants",
  topic: "name",
  plants: [],
  order: [],
  index: 0,
  flipped: false,
  quiz: null,
  quizScore: { plants: emptyTopicMap(0), birds: emptyTopicMap(0) },
  quizTotal: { plants: emptyTopicMap(0), birds: emptyTopicMap(0) },
  path: null,
  scope: "unlocked",
  scopes: { plants: emptyTopicMap("unlocked"), birds: emptyTopicMap("unlocked") },
  galleries: { study: null, quiz: null, detail: null },
};

function copy() {
  return COPY[state.subject] || COPY.plants;
}

function originText(origin) {
  if (origin === "invasive") return "Invasive";
  if (origin === "introduced") return "Introduced";
  return "Native";
}

function originClass(origin) {
  if (origin === "invasive") return "badge invasive";
  if (origin === "introduced") return "badge dim";
  return "badge";
}

function fillSelect(sel, options) {
  const prev = sel.value;
  sel.innerHTML = "";
  for (const [value, label] of options) {
    const opt = document.createElement("option");
    opt.value = value;
    opt.textContent = label;
    sel.appendChild(opt);
  }
  sel.value = [...sel.options].some((opt) => opt.value === prev) ? prev : options[0][0];
}

function applyCopy() {
  const text = copy();
  $("eyebrow").textContent = text.eyebrow;
  $("deck-title").textContent = text.title;
  document.title = text.docTitle;
  fillSelect($("topic"), topicChoices(state.subject));
  if (!topicsFor(state.subject).includes(state.topic)) state.topic = defaultTopic(state.subject);
  $("topic").value = state.topic;
  $("label-wnc").textContent = text.place;
  $("label-uses").textContent = text.usesLabel;
  $("footer-main").textContent = text.footerMain;
  $("footer-fine").textContent = text.footerFine;
  fillSelect($("category"), text.categories);
  fillSelect($("origin"), text.origins);
  const path = state.path;
  if (path && path.subject === state.subject) {
    $("deck-count").innerHTML = `<strong>${path.total}</strong> ${text.noun} in ${path.group_count} groups of ${path.group_size} · ${text.countTail}`;
  }
}

function activeGallery() {
  if ($("detail").open) return state.galleries.detail;
  if (state.mode === "quiz") return state.galleries.quiz;
  return state.galleries.study;
}

function plantPhotos(p) {
  if (!p) return [];
  if (Array.isArray(p.photos) && p.photos.length) return p.photos;
  if (p.image) return [{ file: p.image, label: "", credit: p.image_credit || "" }];
  return [];
}

function scrollToPhoto(scroller, index) {
  const w = scroller.clientWidth || 1;
  scroller.scrollTo({ left: index * w, behavior: "smooth" });
}

function stepGallery(gallery, dir) {
  if (!gallery || gallery.photos.length < 2) return;
  const w = gallery.scroller.clientWidth || 1;
  const n = gallery.photos.length;
  let i = Math.round(gallery.scroller.scrollLeft / w) + dir;
  i = (i + n) % n;
  scrollToPhoto(gallery.scroller, i);
}

function mountGallery(parts, photos, onIndex) {
  const { scroller, dots, label, prev, next } = parts;
  const gallery = { scroller, photos, onIndex, index: 0 };
  scroller.innerHTML = "";
  dots.innerHTML = "";
  const many = photos.length > 1;
  prev.hidden = !many;
  next.hidden = !many;
  dots.hidden = !many;
  label.hidden = !many;
  photos.forEach((ph, i) => {
    const img = document.createElement("img");
    img.src = "/images/" + ph.file;
    img.alt = ph.label || copy().photoAlt;
    img.draggable = false;
    scroller.appendChild(img);
    const dot = document.createElement("button");
    dot.type = "button";
    dot.setAttribute("aria-label", ph.label || `Picture ${i + 1}`);
    dot.addEventListener("click", (e) => {
      e.stopPropagation();
      scrollToPhoto(scroller, i);
    });
    dots.appendChild(dot);
  });
  function sync() {
    if (!photos.length) {
      label.textContent = "";
      return;
    }
    const w = scroller.clientWidth || 1;
    const idx = Math.max(0, Math.min(photos.length - 1, Math.round(scroller.scrollLeft / w)));
    gallery.index = idx;
    if (many) label.textContent = `${photos[idx].label || "Photo"} · ${idx + 1}/${photos.length}`;
    [...dots.children].forEach((d, n) => d.classList.toggle("on", n === idx));
    if (onIndex) onIndex(idx, photos[idx]);
  }
  scroller.onscroll = sync;
  prev.onclick = (e) => {
    e.stopPropagation();
    stepGallery(gallery, -1);
  };
  next.onclick = (e) => {
    e.stopPropagation();
    stepGallery(gallery, 1);
  };
  scroller.scrollLeft = 0;
  sync();
  return gallery;
}

function pathParams() {
  const params = new URLSearchParams({
    subject: state.subject,
    category: $("category").value,
    origin: $("origin").value,
    q: $("search").value.trim(),
    topic: state.topic,
  });
  if (state.scope !== "unlocked") {
    params.set("group", String(state.scope));
  }
  return params;
}

async function loadPath() {
  const subjectAtRequest = state.subject;
  const res = await fetch("/api/path?" + new URLSearchParams({
    topic: state.topic,
    subject: subjectAtRequest,
  }));
  const payload = await res.json();
  if (subjectAtRequest !== state.subject) return;
  state.path = payload;
  applyCopy();
  renderPathBar();
  renderScope();
  renderGroups();
}

async function loadPlants() {
  const subjectAtRequest = state.subject;
  const res = await fetch("/api/plants?" + pathParams().toString());
  const rows = await res.json();
  if (subjectAtRequest !== state.subject) return;
  state.plants = rows;
  state.order = state.plants.map((_, i) => i).filter((i) => {
    if (state.subject === "birds" && state.topic === "call") return !!state.plants[i].audio;
    return true;
  });
  if (state.mode === "study") shuffleStudy(false);
  if (state.mode === "browse") renderBrowse();
  if (state.mode === "quiz") loadQuiz();
  updateMeta();
}

function renderPathBar() {
  const p = state.path;
  if (!p) return;
  const last = p.groups[p.unlocked_groups - 1];
  const label = p.topic_label || "This topic";
  const groups = p.unlocked_groups === 1
    ? "group <strong>1</strong> unlocked"
    : `groups <strong>1–${p.unlocked_groups}</strong> unlocked`;
  $("path-status").innerHTML = `<strong>${escapeHtml(label)}</strong> · ${groups} · ${p.unlocked_count} of ${p.total} ${copy().noun}` +
    (last ? ` · latest: ${escapeHtml(last.title)}` : "");
  $("add-five").disabled = p.unlocked_groups >= p.group_count;
  $("add-five").textContent = p.unlocked_groups >= p.group_count
    ? "All groups unlocked"
    : `Add next 5 (group ${p.unlocked_groups + 1})`;
}

function renderScope() {
  const sel = $("scope");
  const current = state.scope;
  sel.innerHTML = `<option value="unlocked">All unlocked ${copy().noun}</option>`;
  if (!state.path) return;
  for (const g of state.path.groups) {
    if (!g.unlocked) continue;
    const opt = document.createElement("option");
    opt.value = String(g.number);
    opt.textContent = `Group ${g.number} only · ${g.title}`;
    sel.appendChild(opt);
  }
  const ok = [...sel.options].some((o) => o.value === String(current));
  sel.value = ok ? String(current) : "unlocked";
  state.scope = sel.value;
}

function renderGroups() {
  const box = $("group-list");
  if (!box || !state.path) return;
  const intro = document.querySelector(".path-intro");
  if (intro) {
    const label = state.path.topic_label || "This topic";
    const unlocked = state.path.unlocked_groups === 1
      ? "group 1"
      : `groups 1–${state.path.unlocked_groups}`;
    intro.textContent = `${label} has its own groups (${unlocked} unlocked). The other topics stay where you left them.`;
  }
  box.innerHTML = "";
  for (const g of state.path.groups) {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "group-card" + (g.unlocked ? "" : " locked") +
      (String(state.scope) === String(g.number) ? " on" : "");
    const names = (g.members || []).map((pl) => {
      const klass = (pl.origin === "invasive" || pl.origin === "introduced") ? " class=\"invasive-name\"" : "";
      return `<li${klass}>${escapeHtml(pl.common_name)}</li>`;
    }).join("");
    const status = g.unlocked
      ? `${g.known}/${g.size} marked known`
      : "Locked — add groups in order";
    card.innerHTML = `
      <header>
        <span class="num">Group ${g.number}</span>
        <span class="num">${status}</span>
      </header>
      <h3>${escapeHtml(g.title)}</h3>
      <ul>${names}</ul>`;
    if (g.unlocked) {
      card.addEventListener("click", () => {
        state.scope = String(g.number);
        $("scope").value = String(g.number);
        setMode("study");
        loadPlants();
        renderGroups();
      });
    }
    box.appendChild(card);
  }
}

async function changePath(action, extra = {}) {
  await fetch("/api/path", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, topic: state.topic, subject: state.subject, ...extra }),
  });
  if (action === "reset") {
    state.scope = "unlocked";
    state.scopes[state.subject][state.topic] = "unlocked";
  }
  await loadPath();
  await loadPlants();
}

function shuffleStudy(reshuffle = true) {
  if (reshuffle) {
    for (let i = state.order.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [state.order[i], state.order[j]] = [state.order[j], state.order[i]];
    }
  }
  state.index = 0;
  state.flipped = false;
  showCard();
}

function currentPlant() {
  if (!state.order.length) return null;
  return state.plants[state.order[state.index]];
}

function updateMeta() {
  const hearing = state.subject === "birds" && state.topic === "call" && state.mode === "study";
  const n = hearing ? state.order.length : state.plants.length;
  const shown = Math.min(state.index + 1, n);
  $("study-meta").textContent = n
    ? (hearing ? `Card ${shown} of ${n} with a call` : `Card ${shown} of ${n}`)
    : (hearing ? "No saved calls in this group yet." : copy().empty);
}

function syncHearCall(revealed) {
  const hearing = state.subject === "birds" && state.topic === "call";
  $("card").classList.toggle("hear-call", hearing && !state.flipped);
  const quizCard = document.querySelector("#quiz-view .quiz-card");
  if (quizCard) quizCard.classList.toggle("hear-call", hearing && !revealed);
}

function startCall(file) {
  if (!file) return;
  stopCall();
  callPlayer.src = "/sounds/" + file;
  callPlayer.dataset.file = file;
  const played = callPlayer.play();
  if (played && played.catch) played.catch(() => syncCallButtons());
  else syncCallButtons();
}

const callPlayer = new Audio();
callPlayer.preload = "none";

function syncCallButtons() {
  const playing = !callPlayer.paused && !callPlayer.ended;
  const file = callPlayer.dataset.file || "";
  document.querySelectorAll(".call-btn").forEach((button) => {
    const mine = playing && button.dataset.file === file;
    button.textContent = mine ? "Stop" : "Play call";
    button.setAttribute("aria-pressed", mine ? "true" : "false");
  });
}

function stopCall() {
  callPlayer.pause();
  try { callPlayer.currentTime = 0; } catch (err) { /* not loaded yet */ }
  syncCallButtons();
}

function setCallButton(button, card) {
  if (!button) return;
  const file = (card && card.audio) || "";
  button.hidden = !file;
  button.dataset.file = file;
  if (!button.dataset.bound) {
    button.dataset.bound = "1";
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      const next = button.dataset.file;
      if (!next) return;
      if (!callPlayer.paused && callPlayer.dataset.file === next) {
        stopCall();
        return;
      }
      stopCall();
      callPlayer.src = "/sounds/" + next;
      callPlayer.dataset.file = next;
      const played = callPlayer.play();
      if (played && played.catch) played.catch(() => syncCallButtons());
      syncCallButtons();
    });
  }
  syncCallButtons();
}

function setCallCredit(node, card, hold) {
  if (!node) return;
  const credit = (card && card.audio && card.audio_credit) || "";
  node.hidden = !credit || !!hold;
  node.textContent = credit;
}

callPlayer.addEventListener("ended", stopCall);
callPlayer.addEventListener("play", syncCallButtons);

function showCard() {
  const p = currentPlant();
  const back = $("card-back");
  const hint = $("front-hint");
  $("learning").hidden = true;
  $("know").hidden = true;
  $("next").hidden = true;
  $("flip").hidden = false;
  const flipLabels = copy().flip[state.topic] || copy().flip.name;
  $("flip").textContent = flipLabels[0];
  if (!p) {
    state.galleries.study = mountGallery({
      scroller: $("card-scroller"),
      dots: $("card-dots"),
      label: $("card-photo-label"),
      prev: $("card-prev"),
      next: $("card-next"),
    }, [], null);
    hint.textContent = copy().empty + ".";
    back.hidden = true;
    $("flip").hidden = true;
    $("credit").textContent = "";
    setCallButton($("card-call"), null);
    setCallCredit($("call-credit"), null);
    stopCall();
    syncHearCall(false);
    updateMeta();
    return;
  }
  state.flipped = false;
  back.hidden = true;
  hint.hidden = false;
  const photos = plantPhotos(p);
  const hearing = state.subject === "birds" && state.topic === "call";
  syncHearCall(false);
  if (hearing) {
    hint.textContent = copy().question.call;
  } else if (state.topic === "name") {
    hint.textContent = photos.length ? copy().question.name : copy().noPhoto;
  } else {
    hint.textContent = `${p.common_name} — ${copy().question[state.topic]}`;
  }
  focusFact();
  state.galleries.study = mountGallery({
    scroller: $("card-scroller"),
    dots: $("card-dots"),
    label: $("card-photo-label"),
    prev: $("card-prev"),
    next: $("card-next"),
  }, photos, (_i, ph) => {
    $("credit").textContent = (ph && ph.credit) || "";
  });
  const origin = $("badge-origin");
  origin.textContent = originText(p.origin);
  origin.className = originClass(p.origin);
  origin.hidden = true;
  $("badge-cat").textContent = p.category;
  $("badge-cat").hidden = true;
  $("badge-group").textContent = `Group ${p.group}`;
  $("common").textContent = p.common_name;
  $("scientific").textContent = `${p.scientific_name} · ${p.family}`;
  $("aka").textContent = p.also_known_as.length
    ? "Also called: " + p.also_known_as.join(", ")
    : "";
  $("id-tips").textContent = p.id_tips;
  $("wnc").textContent = p.wnc;
  $("habitat").textContent = p.habitat;
  $("uses").textContent = p.uses;
  $("caution").textContent = p.caution;
  $("lookalikes").textContent = p.lookalikes;
  setCallButton($("card-call"), p);
  setCallCredit($("call-credit"), p);
  syncHearCall(false);
  if (hearing && p.audio) startCall(p.audio);
  else if (callPlayer.dataset.file && callPlayer.dataset.file !== p.audio) stopCall();
  updateMeta();
}

function focusFact() {
  document.querySelectorAll("#card-back dl div").forEach((d) => d.classList.remove("focus"));
  const field = { uses: "uses", lookalikes: "lookalikes", identify: "id-tips" }[state.topic];
  if (!field) return;
  const node = $(field);
  if (node && node.parentElement) node.parentElement.classList.add("focus");
}

function flipCard() {
  const p = currentPlant();
  if (!p) return;
  state.flipped = !state.flipped;
  $("card-back").hidden = !state.flipped;
  $("front-hint").hidden = state.flipped;
  const labels = copy().flip[state.topic] || copy().flip.name;
  $("flip").textContent = state.flipped ? labels[1] : labels[0];
  $("learning").hidden = !state.flipped;
  $("know").hidden = !state.flipped;
  $("next").hidden = !state.flipped;
  $("badge-origin").hidden = !state.flipped;
  $("badge-cat").hidden = !state.flipped;
  syncHearCall(false);
  if (state.flipped) {
    $("card-scroller").querySelectorAll("img").forEach((img) => {
      img.alt = p.common_name;
    });
  }
}

async function mark(result) {
  const p = currentPlant();
  if (!p) return;
  await fetch("/api/progress", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: p.id, result, topic: state.topic, subject: state.subject }),
  });
  await loadPath();
  nextCard();
}

function nextCard() {
  if (!state.order.length) return;
  state.index = (state.index + 1) % state.order.length;
  showCard();
}

function setMode(mode) {
  stopCall();
  state.mode = mode;
  document.querySelectorAll(".tab").forEach((t) => {
    t.classList.toggle("on", t.dataset.mode === mode);
  });
  $("study-view").classList.toggle("on", mode === "study");
  $("quiz-view").classList.toggle("on", mode === "quiz");
  $("browse-view").classList.toggle("on", mode === "browse");
  $("path-view").classList.toggle("on", mode === "path");
  if (mode === "study") showCard();
  if (mode === "browse") renderBrowse();
  if (mode === "quiz") loadQuiz();
  if (mode === "path") renderGroups();
}

function renderBrowse() {
  const grid = $("grid");
  grid.innerHTML = "";
  if (!state.plants.length) {
    grid.textContent = copy().empty + ".";
    return;
  }
  for (const p of state.plants) {
    const btn = document.createElement("button");
    btn.className = "tile";
    btn.innerHTML = `
      ${p.image ? `<img src="/images/${p.image}" alt="${escapeHtml(p.common_name)}">` : `<img alt="">`}
      <div>
        <h3>${escapeHtml(p.common_name)}</h3>
        <p>Group ${p.group} · ${escapeHtml(p.scientific_name)}</p>
      </div>`;
    btn.addEventListener("click", () => openDetail(p));
    grid.appendChild(btn);
  }
}

function openDetail(p) {
  const dlg = $("detail");
  const photos = plantPhotos(p);
  $("detail-body").innerHTML = `
    <div class="photo-wrap">
      <div class="photo-scroller" id="detail-scroller" tabindex="0"></div>
      <button type="button" class="photo-nav prev" id="detail-prev" aria-label="Previous picture" hidden>‹</button>
      <button type="button" class="photo-nav next" id="detail-next" aria-label="Next picture" hidden>›</button>
      <p class="photo-label" id="detail-photo-label" hidden></p>
      <div class="photo-dots" id="detail-dots"></div>
      <button type="button" class="call-btn" id="detail-call" hidden>Play call</button>
    </div>
    <div class="pad">
      <h2>${escapeHtml(p.common_name)}</h2>
      <p class="sci">${escapeHtml(p.scientific_name)} · ${escapeHtml(p.family)}</p>
      <p><strong>${originText(p.origin)}</strong> · ${escapeHtml(p.category)} · Group ${p.group} · ${escapeHtml(p.group_title || "")}</p>
      <dl>
        <div><dt>How to know it</dt><dd>${escapeHtml(p.id_tips)}</dd></div>
        <div><dt>${escapeHtml(copy().place)}</dt><dd>${escapeHtml(p.wnc)}</dd></div>
        <div><dt>Habitat</dt><dd>${escapeHtml(p.habitat)}</dd></div>
        <div><dt>${escapeHtml(copy().usesLabel)}</dt><dd>${escapeHtml(p.uses)}</dd></div>
        <div><dt>Caution</dt><dd>${escapeHtml(p.caution)}</dd></div>
        <div><dt>Lookalikes</dt><dd>${escapeHtml(p.lookalikes)}</dd></div>
      </dl>
      <p class="credit" id="detail-credit">${escapeHtml((photos[0] && photos[0].credit) || p.image_credit || "")}</p>
      <p class="credit" id="detail-call-credit"></p>
    </div>`;
  state.galleries.detail = mountGallery({
    scroller: $("detail-scroller"),
    dots: $("detail-dots"),
    label: $("detail-photo-label"),
    prev: $("detail-prev"),
    next: $("detail-next"),
  }, photos, (_i, ph) => {
    const credit = $("detail-credit");
    if (credit) credit.textContent = (ph && ph.credit) || "";
  });
  setCallButton($("detail-call"), p);
  setCallCredit($("detail-call-credit"), p);
  dlg.showModal();
}

function quizScoreLine() {
  const score = state.quizScore[state.subject][state.topic] || 0;
  const total = state.quizTotal[state.subject][state.topic] || 0;
  return `Score ${score} / ${total}`;
}

async function loadQuiz() {
  const params = pathParams();
  params.delete("q");
  const subjectAtRequest = state.subject;
  const res = await fetch("/api/quiz?" + params.toString());
  if (subjectAtRequest !== state.subject) return;
  if (!res.ok) {
    let message = copy().quizEmpty;
    try {
      const err = await res.json();
      if (err && err.error) message = err.error;
    } catch (err) { /* keep the short fallback */ }
    $("quiz-feedback").textContent = message;
    $("quiz-ask").textContent = "";
    $("choices").innerHTML = "";
    setCallButton($("quiz-call"), null);
    setCallCredit($("quiz-call-credit"), null);
    syncHearCall(false);
    state.galleries.quiz = mountGallery({
      scroller: $("quiz-scroller"),
      dots: $("quiz-dots"),
      label: $("quiz-photo-label"),
      prev: $("quiz-prev"),
      next: $("quiz-next-photo"),
    }, [], null);
    return;
  }
  state.quiz = await res.json();
  if (subjectAtRequest !== state.subject || state.quiz.subject !== state.subject) return;
  syncHearCall(false);
  $("quiz-feedback").textContent = "";
  const ask = state.quiz.prompt || copy().question.name;
  $("quiz-ask").textContent = state.quiz.show_name && state.quiz.common_name
    ? `${state.quiz.common_name} — ${ask.charAt(0).toLowerCase()}${ask.slice(1)}`
    : ask;
  const quizPhotos = state.quiz.topic === "call" ? [] : plantPhotos(state.quiz);
  state.galleries.quiz = mountGallery({
    scroller: $("quiz-scroller"),
    dots: $("quiz-dots"),
    label: $("quiz-photo-label"),
    prev: $("quiz-prev"),
    next: $("quiz-next-photo"),
  }, quizPhotos, null);
  $("quiz-scroller").querySelectorAll("img").forEach((img) => {
    img.alt = copy().identifyAlt;
  });
  setCallButton($("quiz-call"), state.quiz);
  setCallCredit($("quiz-call-credit"), state.quiz, true);
  syncHearCall(false);
  if (state.quiz.topic === "call" && state.quiz.audio) startCall(state.quiz.audio);
  else if (callPlayer.dataset.file && callPlayer.dataset.file !== state.quiz.audio) stopCall();
  const box = $("choices");
  box.innerHTML = "";
  delete box.dataset.locked;
  const factQuiz = state.quiz.topic && state.quiz.topic !== "name" && state.quiz.topic !== "call";
  const callQuiz = state.quiz.topic === "call";
  state.quiz.choices.forEach((c, i) => {
    const b = document.createElement("button");
    b.type = "button";
    const key = document.createElement("span");
    key.className = "choice-key";
    key.textContent = String(i + 1);
    b.appendChild(key);
    if (callQuiz && c.image) {
      const img = document.createElement("img");
      img.className = "choice-photo";
      img.alt = "";
      img.src = "/images/" + c.image;
      b.appendChild(img);
      b.classList.add("with-photo");
    }
    const label = document.createElement("span");
    if (factQuiz) {
      b.classList.add("fact");
      label.textContent = c.text || "";
    } else {
      label.innerHTML = `${escapeHtml(c.common_name)}<small>${escapeHtml(c.scientific_name)}</small>`;
    }
    b.appendChild(label);
    b.addEventListener("click", () => answerQuiz(c.id, b));
    box.appendChild(b);
  });
  $("quiz-score").textContent = quizScoreLine();
}

function answerQuiz(id, btn) {
  if (!state.quiz || $("choices").dataset.locked) return;
  $("choices").dataset.locked = "1";
  const scoreSubject = state.quiz.subject || state.subject;
  state.quizTotal[scoreSubject][state.topic] = (state.quizTotal[scoreSubject][state.topic] || 0) + 1;
  const correct = id === state.quiz.answer.id;
  if (correct) state.quizScore[scoreSubject][state.topic] = (state.quizScore[scoreSubject][state.topic] || 0) + 1;
  document.querySelectorAll("#choices button").forEach((b, i) => {
    const cid = state.quiz.choices[i].id;
    if (cid === state.quiz.answer.id) b.classList.add("right");
    if (b === btn && !correct) b.classList.add("wrong");
  });
  const detail = state.quiz.answer.detail || state.quiz.answer.id_tips || "";
  $("quiz-feedback").textContent = correct
    ? `Yes — ${state.quiz.answer.common_name}. ${detail}`
    : `It's ${state.quiz.answer.common_name} (${state.quiz.answer.scientific_name}). ${detail}`;
  $("quiz-score").textContent = quizScoreLine();
  setCallCredit($("quiz-call-credit"), state.quiz);
  if (state.quiz.topic === "call") {
    state.galleries.quiz = mountGallery({
      scroller: $("quiz-scroller"),
      dots: $("quiz-dots"),
      label: $("quiz-photo-label"),
      prev: $("quiz-prev"),
      next: $("quiz-next-photo"),
    }, plantPhotos(state.quiz), null);
    $("quiz-scroller").querySelectorAll("img").forEach((img) => {
      img.alt = state.quiz.answer.common_name;
    });
    syncHearCall(true);
  }
}

function escapeHtml(s) {
  return String(s || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

document.querySelectorAll(".tab").forEach((t) => {
  t.addEventListener("click", () => setMode(t.dataset.mode));
});
["category", "origin"].forEach((id) => {
  $(id).addEventListener("change", loadPlants);
});
$("search").addEventListener("input", () => {
  clearTimeout(window.__q);
  window.__q = setTimeout(loadPlants, 200);
});
$("scope").addEventListener("change", () => {
  state.scope = $("scope").value;
  loadPlants();
  renderGroups();
});
$("shuffle").addEventListener("click", () => shuffleStudy(true));
$("flip").addEventListener("click", flipCard);
$("next").addEventListener("click", nextCard);
$("know").addEventListener("click", () => mark("know"));
$("learning").addEventListener("click", () => mark("learning"));
$("add-five").addEventListener("click", () => changePath("add"));
$("topic").addEventListener("change", async () => {
  const next = $("topic").value;
  if (!topicsFor(state.subject).includes(next) || next === state.topic) return;
  state.scopes[state.subject][state.topic] = state.scope;
  state.topic = next;
  try { localStorage.setItem("wnc-learn-topic-" + state.subject, next); } catch (err) { /* private mode */ }
  state.scope = state.scopes[state.subject][next] || "unlocked";
  await loadPath();
  await loadPlants();
});
$("subject").addEventListener("change", async () => {
  const next = $("subject").value;
  if (next !== "plants" && next !== "birds") return;
  if (next === state.subject) return;
  state.scopes[state.subject][state.topic] = state.scope;
  try { localStorage.setItem("wnc-learn-topic-" + state.subject, state.topic); } catch (err) { /* private mode */ }
  state.subject = next;
  state.topic = loadSavedTopic(next);
  state.scope = state.scopes[next][state.topic] || "unlocked";
  $("topic").value = state.topic;
  try { localStorage.setItem("wnc-subject", next); } catch (err) { /* private mode */ }
  $("category").value = "all";
  $("origin").value = "all";
  $("search").value = "";
  applyCopy();
  await loadPath();
  await loadPlants();
});
$("reset-path").addEventListener("click", () => {
  const label = $("topic").selectedOptions[0] ? $("topic").selectedOptions[0].textContent : "this topic";
  if (confirm(`Start ${label} over with only the first 5 ${copy().noun}? The other topics keep their own groups.`)) {
    changePath("reset");
  }
});
$("quiz-next").addEventListener("click", () => {
  delete $("choices").dataset.locked;
  loadQuiz();
});
$("close-detail").addEventListener("click", () => {
  stopCall();
  $("detail").close();
});
$("detail").addEventListener("close", stopCall);
function quizChoiceIndex(e) {
  if (/^[1-4]$/.test(e.key)) return Number(e.key) - 1;
  const pad = /^Numpad([1-4])$/.exec(e.code || "");
  return pad ? Number(pad[1]) - 1 : -1;
}

document.addEventListener("keydown", (e) => {
  if (e.target.matches && e.target.matches("input, textarea, select")) return;
  const dialogOpen = $("detail").open;
  if (!dialogOpen && state.mode === "quiz") {
    const index = quizChoiceIndex(e);
    if (index >= 0) {
      const buttons = [...$("choices").querySelectorAll("button")];
      if (buttons[index] && !$("choices").dataset.locked) {
        e.preventDefault();
        buttons[index].click();
      }
      return;
    }
    if ((e.key === "Enter" || e.code === "NumpadEnter") && $("choices").dataset.locked) {
      if (e.target === $("quiz-next") || (e.target.closest && e.target.closest(".call-btn"))) return;
      e.preventDefault();
      $("quiz-next").click();
      return;
    }
  }
  if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
  if (!dialogOpen && state.mode !== "study" && state.mode !== "quiz") return;
  e.preventDefault();
  stepGallery(activeGallery(), e.key === "ArrowRight" ? 1 : -1);
});

function loadSavedTopic(subject) {
  let saved = null;
  try { saved = localStorage.getItem("wnc-learn-topic-" + subject); } catch (err) { saved = null; }
  return topicsFor(subject).includes(saved) ? saved : defaultTopic(subject);
}

const savedSubject = (() => {
  try { return localStorage.getItem("wnc-subject"); } catch (err) { return null; }
})();
if (savedSubject === "plants" || savedSubject === "birds") {
  state.subject = savedSubject;
  $("subject").value = savedSubject;
}
state.topic = loadSavedTopic(state.subject);
$("topic").value = state.topic;
applyCopy();
loadPath().then(loadPlants);
