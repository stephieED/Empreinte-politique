// Imports from config
import { CANDIDATS_URL, PROFILE_URL, PIVOT_PROFILE_URL, REAL_GROUP_PROFILE_URL, REAL_GROUP_PROFILES, MAX_COMPARE_CANDIDATES, PANEL_ORDER } from './config.js';

// Imports from utils
import { setDocumentTitle, escapeHtml, shortName, candidateLastName, withTheme, formatIsoDate } from './utils.js';

// Imports from render
import { renderHome, renderRealGroupHome, renderRealGroupPage, renderPage, openExpressSummary, closeExpressSummary, setExpressScene, toggleKpiFlip, setActivePanel, scrollToPanel } from './render.js';

const state = {
  candidats: [],
  currentSlug: "",
  currentMeta: null,
  currentProfile: null,
  selectedTheme: "all",
  interventionsMode: "all",
  interventionsVisible: 6,
  compareTheme: "sante",
  compareSlugs: ["", ""],
  compareProfiles: {},
  availableCompareCandidates: [],
  activePanelIndex: 0,
  apercuView: "synthese",
  apercuFilter: "all",
  flippedKpis: new Set(),
  expandedTextThemes: new Set(),
  expandedVoteThemes: new Set(),
  showUnpublishedTextes: false,
  textesScopeFilter: "all",
  amendementsOutcomeFilter: "all",
  textesKpiView: "par_statut",
  mandateView: "timeline",
  mandateFilter: "all",
  expressIndex: 0,
  profileMode: "candidates",
  currentRealGroupId: "",
  currentRealGroupProfile: null,
  realGroupCohesionVisible: 20,
};

async function loadProfile(slug) {
  if (!slug) return null;
  const [rawResponse, pivotResponse] = await Promise.all([
    fetch(PROFILE_URL(slug), { cache: "no-store" }),
    fetch(PIVOT_PROFILE_URL(slug), { cache: "no-store" }).catch(() => null),
  ]);
  if (!rawResponse.ok) throw new Error(`HTTP ${rawResponse.status}`);
  const raw = await rawResponse.json();
  const pivot = pivotResponse?.ok ? await pivotResponse.json() : null;
  const pivotVotes = new Map((pivot?.votes || []).map((vote) => [String(vote.numero_scrutin || ""), vote]));
  const votes = (raw.votes || []).map((vote) => {
    const fact = pivotVotes.get(String(vote.numero_scrutin || ""));
    return fact ? { ...vote, type_scrutin: fact.type_scrutin, type_vote: fact.type_vote, texte_lie_id: fact.texte_lie_id, sort: fact.sort ?? vote.sort } : vote;
  });
  return withTheme({
    ...raw,
    votes,
    textes_portes: pivot?.textes_portes || [],
    amendements: pivot?.amendements || [],
    pivot_mandats: pivot?.mandats || [],
  });
}

async function ensureCompareProfile(slug) {
  if (!slug) return null;
  if (state.compareProfiles[slug]) return state.compareProfiles[slug];
  try {
    state.compareProfiles[slug] = await loadProfile(slug);
  } catch {
    state.compareProfiles[slug] = null;
  }
  return state.compareProfiles[slug];
}

export function bindRenderedEvents() {
  document.querySelector(".express-launch")?.addEventListener("click", () => openExpressSummary(state));
  document.querySelector(".express-summary-close")?.addEventListener("click", closeExpressSummary);
  document.querySelectorAll("[data-express-dir]").forEach((button) => {
    button.addEventListener("click", () => setExpressScene(state.expressIndex + Number(button.dataset.expressDir), state));
  });

  document.querySelectorAll("[data-apercu-view]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.apercuView = btn.dataset.apercuView;
      renderPage(state);
    });
  });

  document.querySelectorAll("[data-apercu-filter]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.apercuFilter = btn.dataset.apercuFilter;
      renderPage(state);
    });
  });

  document.querySelectorAll("[data-expand-vote-theme]").forEach((button) => {
    button.addEventListener("click", () => {
      const theme = button.dataset.expandVoteTheme;
      if (state.expandedVoteThemes.has(theme)) state.expandedVoteThemes.delete(theme);
      else state.expandedVoteThemes.add(theme);
      renderPage(state);
    });
  });

  document.querySelectorAll("[data-expand-text-theme]").forEach((button) => {
    button.addEventListener("click", () => {
      const theme = button.dataset.expandTextTheme;
      if (state.expandedTextThemes.has(theme)) state.expandedTextThemes.delete(theme);
      else state.expandedTextThemes.add(theme);
      renderPage(state);
    });
  });

  document.querySelector("[data-toggle-unpublished-textes]")?.addEventListener("click", () => {
    state.showUnpublishedTextes = !state.showUnpublishedTextes;
    renderPage(state);
  });

  document.querySelectorAll("[data-legislative-reading]").forEach((button) => {
    button.addEventListener("click", () => {
      state.textesScopeFilter = button.dataset.legislativeReading === "auto" ? "all" : button.dataset.legislativeReading;
      renderPage(state);
    });
  });

  document.querySelectorAll("[data-textes-kpi-view]").forEach((button) => {
    button.addEventListener("click", () => {
      state.textesKpiView = button.dataset.textesKpiView;
      renderPage(state);
    });
  });

  document.querySelectorAll("[data-textes-scope]").forEach((el) => {
    el.addEventListener("click", () => {
      const scope = el.dataset.textesScope;
      if (state.textesScopeFilter === scope && state.amendementsOutcomeFilter === "all") {
        state.textesScopeFilter = "all";
      } else {
        state.textesScopeFilter = scope;
        state.amendementsOutcomeFilter = "all";
      }
      renderPage(state);
    });
    el.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); el.click(); }
    });
  });

  document.querySelectorAll("[data-amend-outcome]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const outcome = btn.dataset.amendOutcome;
      const scope = btn.dataset.scope;
      if (state.amendementsOutcomeFilter === outcome && state.textesScopeFilter === scope) {
        state.amendementsOutcomeFilter = "all";
        state.textesScopeFilter = "all";
      } else {
        state.amendementsOutcomeFilter = outcome;
        state.textesScopeFilter = scope;
      }
      renderPage(state);
    });
  });

  document.querySelectorAll(".outcome-segment[data-outcome]").forEach((seg) => {
    seg.addEventListener("click", (e) => {
      e.stopPropagation();
      const outcome = seg.dataset.outcome;
      const scope = seg.dataset.scope;
      if (state.amendementsOutcomeFilter === outcome && state.textesScopeFilter === scope) {
        state.amendementsOutcomeFilter = "all";
        state.textesScopeFilter = "all";
      } else {
        state.amendementsOutcomeFilter = outcome;
        state.textesScopeFilter = scope;
      }
      renderPage(state);
    });
    seg.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); seg.click(); }
    });
  });

  document.querySelector("[data-reset-textes-filters]")?.addEventListener("click", () => {
    state.textesScopeFilter = "all";
    state.amendementsOutcomeFilter = "all";
    renderPage(state);
  });

  document.querySelectorAll(".orbit-node").forEach((node) => {
    node.addEventListener("click", () => {
      const expanded = node.classList.toggle("expanded");
      node.setAttribute("aria-expanded", String(expanded));
    });
  });

  document.querySelectorAll("[data-mandate-view]").forEach((button) => {
    button.addEventListener("click", () => {
      state.mandateView = button.dataset.mandateView;
      renderPage(state);
    });
  });

  document.querySelectorAll("[data-mandate-filter]").forEach((button) => {
    button.addEventListener("click", () => {
      state.mandateFilter = button.dataset.mandateFilter;
      renderPage(state);
    });
  });

  document.querySelectorAll("[data-theme]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.selectedTheme = btn.dataset.theme;
      if (state.selectedTheme !== "all") state.compareTheme = state.selectedTheme;
      renderPage(state);
    });
  });

  document.querySelectorAll("[data-compare-theme]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.compareTheme = btn.dataset.compareTheme;
      renderPage(state);
    });
  });

  document.querySelectorAll("[data-inter-mode]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.interventionsMode = btn.dataset.interMode;
      state.interventionsVisible = 6;
      renderPage(state);
    });
  });

  const moreBtn = document.getElementById("see-more-interventions");
  if (moreBtn) {
    moreBtn.addEventListener("click", () => {
      state.interventionsVisible += 6;
      renderPage(state);
    });
  }

  document.querySelectorAll("[data-compare-toggle]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const slug = btn.dataset.compareToggle;
      const idx = state.compareSlugs.indexOf(slug);
      if (idx !== -1) {
        state.compareSlugs[idx] = "";
      } else {
        const emptyIdx = state.compareSlugs.indexOf("");
        state.compareSlugs[emptyIdx !== -1 ? emptyIdx : 0] = slug;
      }
      await refreshCompareProfiles();
      renderPage(state);
    });
  });

  // Cartes KPI en flip 3D : clic/tap pour basculer (le survol suffit sur desktop)
  document.querySelectorAll(".kpi-flip").forEach((el) => {
    el.addEventListener("click", (e) => {
      if (e.target.closest(".kpi-back-link")) return;
      toggleKpiFlip(el, state);
    });
    el.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        toggleKpiFlip(el, state);
      }
    });
  });
  document.querySelectorAll(".kpi-back-link").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      scrollToPanel(btn.dataset.gotoPanel, state);
    });
  });

  // Barre d'onglets : un seul panneau visible, sans défilement horizontal forcé.
  document.querySelectorAll(".panel-dot").forEach((dot) => {
    dot.addEventListener("click", () => {
      setActivePanel(Number(dot.dataset.panelIndex), { scroll: true }, state);
    });
  });
}

async function refreshCompareProfiles() {
  // Dédoublonnage utile si la même personne est choisie deux fois pour la comparaison.
  const slugs = [...new Set(state.compareSlugs.filter(Boolean))].slice(0, MAX_COMPARE_CANDIDATES);
  state.compareSlugs = [slugs[0] || "", slugs[1] || ""];
  await Promise.all(slugs.map((slug) => ensureCompareProfile(slug)));
}

export function updateActiveAvatarChip() {
  const carousel = document.getElementById("candidat-carousel");
  if (!carousel) return;
  document.querySelectorAll("#candidat-carousel .avatar-chip").forEach((chip) => {
    let isActive;
    if (state.profileMode === "groups") isActive = chip.dataset.realGroupId === state.currentRealGroupId;
    else isActive = chip.dataset.slug === state.currentSlug;
    chip.classList.toggle("active", isActive);
    chip.setAttribute("aria-selected", String(isActive));
  });
}

export function updateStickyLayoutVars() {
  const dock = document.querySelector(".candidate-dock");
  const themeDock = document.querySelector(".theme-dock");
  const measuredDockHeight = dock ? dock.offsetHeight : 0;
  document.body.style.setProperty("--candidate-dock-height", `${measuredDockHeight}px`);
  document.body.style.setProperty("--theme-dock-height", `${themeDock ? themeDock.offsetHeight : 0}px`);
}

export function updateProfileRailVisibility() {
  const carousel = document.getElementById("candidat-carousel");
  const dock = document.querySelector(".candidate-dock");
  const button = document.getElementById("rail-scroll-btn");
  let hasSelection;
  if (state.profileMode === "groups") hasSelection = Boolean(state.currentRealGroupId);
  else hasSelection = Boolean(state.currentSlug);
  carousel.hidden = !hasSelection;
  button.hidden = !hasSelection;
  dock.classList.toggle("has-profile-rail", hasSelection);
  document.body.classList.toggle("profile-selected", hasSelection);
  updateStickyLayoutVars();
  if (!hasSelection) return;
  const needsScroll = carousel.scrollWidth > carousel.clientWidth + 1;
  button.hidden = !needsScroll;
  updateStickyLayoutVars();
}

function scrollProfileRail() {
  const carousel = document.getElementById("candidat-carousel");
  if (!carousel) return;
  const step = Math.max(160, carousel.clientWidth * 0.8);
  carousel.scrollBy({ left: step, behavior: "smooth" });
}

function renderProfileRail() {
  const carousel = document.getElementById("candidat-carousel");
  if (!carousel) return;
  if (state.profileMode === "groups") {
    carousel.setAttribute("aria-label", "Choisir un groupe parlementaire");
    carousel.innerHTML = REAL_GROUP_PROFILES.map((group) => `
      <button type="button" class="avatar-chip" data-real-group-id="${escapeHtml(group.id)}" role="tab" aria-selected="false" title="${escapeHtml(group.label)} (${escapeHtml(group.chambre)})">
        <span class="avatar-chip-circle">${escapeHtml(shortName(group.label))}</span>
        <span class="avatar-chip-name">${escapeHtml(group.label)}</span>
      </button>
    `).join("");
    carousel.querySelectorAll("[data-real-group-id]").forEach((chip) => {
      chip.addEventListener("click", () => selectRealGroup(chip.dataset.realGroupId));
    });
  } else {
    carousel.setAttribute("aria-label", "Choisir un candidat");
    carousel.innerHTML = state.candidats.map((candidate) => `
      <button type="button" class="avatar-chip" data-slug="${escapeHtml(candidate.slug || "")}" role="tab" aria-selected="false" ${candidate.slug ? "" : "disabled"} title="${candidate.slug ? escapeHtml(candidate.nom) : `${escapeHtml(candidate.nom)} (pas de données parlementaires)`}">
        <span class="avatar-chip-circle">${escapeHtml(shortName(candidate.nom))}</span>
        <span class="avatar-chip-name">${escapeHtml(candidateLastName(candidate.nom))}</span>
      </button>
    `).join("");
    carousel.querySelectorAll(".avatar-chip[data-slug]:not(:disabled)").forEach((chip) => {
      chip.addEventListener("click", () => selectCandidate(chip.dataset.slug));
    });
  }
  updateActiveAvatarChip();
  updateProfileRailVisibility();
}

function setProfileMode(mode) {
  if (!['candidates', 'groups'].includes(mode) || state.profileMode === mode) return;
  state.profileMode = mode;
  state.currentSlug = "";
  state.currentMeta = null;
  state.currentProfile = null;
  state.currentRealGroupId = "";
  state.currentRealGroupProfile = null;
  document.querySelectorAll("[data-profile-mode]").forEach((button) => {
    const active = button.dataset.profileMode === mode;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  renderProfileRail();
  renderHome(state);
}

export async function selectCandidate(slug) {
  state.currentSlug = slug;
  state.currentMeta = state.candidats.find((c) => c.slug === slug) || null;
  state.currentProfile = null;
  state.selectedTheme = "all";
  state.interventionsMode = "all";
  state.interventionsVisible = 6;
  state.compareSlugs = ["", ""];
  state.compareProfiles = {};
  state.activePanelIndex = 0;
  state.apercuView = "synthese";
  state.apercuFilter = "all";
  state.flippedKpis = new Set();
  state.expandedTextThemes = new Set();
  state.expandedVoteThemes = new Set();
  state.showUnpublishedTextes = false;
  state.textesScopeFilter = "all";
  state.amendementsOutcomeFilter = "all";
  state.textesKpiView = "par_statut";
  state.mandateView = "timeline";
  state.mandateFilter = "all";
  state.expressIndex = 0;

  updateActiveAvatarChip();
  updateProfileRailVisibility();

  const root = document.getElementById("candidat-root");
  if (!slug || !state.currentMeta) {
    root.innerHTML = "";
    setDocumentTitle("");
    return;
  }
  state.availableCompareCandidates = state.candidats.filter((c) => c.slug && c.slug !== slug);

  root.innerHTML = `<section class="panel"><p class="empty" role="status" aria-live="polite">Chargement de la fiche de ${escapeHtml(state.currentMeta.nom)}…</p></section>`;
  try {
    state.currentProfile = await loadProfile(slug);
    renderPage(state);
  } catch (err) {
    root.innerHTML = `
      <section class="panel">
        <p class="empty">Données non disponibles pour ce candidat (${escapeHtml(err.message)}).</p>
        <p class="small">Aucune donnée trouvée pour le moment. Cette fiche sera affichée dès que les données seront disponibles.</p>
      </section>
    `;
    setDocumentTitle(state.currentMeta?.nom || "");
  }
}

export async function selectRealGroup(groupId) {
  state.currentRealGroupId = groupId;
  state.currentRealGroupProfile = null;
  state.realGroupCohesionVisible = 20;
  updateActiveAvatarChip();
  updateProfileRailVisibility();
  const root = document.getElementById("candidat-root");
  const groupMeta = REAL_GROUP_PROFILES.find((group) => group.id === groupId);
  if (!groupMeta) {
    renderRealGroupHome(state);
    return;
  }
  root.innerHTML = `<section class="panel"><p class="empty" role="status" aria-live="polite">Chargement du groupe ${escapeHtml(groupMeta.label)}…</p></section>`;
  try {
    const response = await fetch(REAL_GROUP_PROFILE_URL(groupMeta.fichier), { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const profile = await response.json();
    if (profile.type_document !== "profil_groupe") throw new Error("schéma de profil inattendu");
    state.currentRealGroupProfile = profile;
    renderRealGroupPage(state);
  } catch (error) {
    root.innerHTML = `<section class="panel"><p class="empty">Données de groupe indisponibles (${escapeHtml(error.message)}).</p></section>`;
    setDocumentTitle(groupMeta.label);
  }
}

async function init() {
  document.getElementById("home-link").addEventListener("click", () => renderHome(state));
  document.querySelectorAll("[data-profile-mode]").forEach((button) => {
    button.addEventListener("click", () => setProfileMode(button.dataset.profileMode));
  });
  document.getElementById("rail-scroll-btn").addEventListener("click", scrollProfileRail);
  window.addEventListener("resize", updateProfileRailVisibility);

  try {
    const resp = await fetch(CANDIDATS_URL, { cache: "no-store" });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    state.candidats = data.candidats || [];
    renderProfileRail();
    renderHome(state);
  } catch (err) {
    document.getElementById("candidat-root").innerHTML = `
      <section class="panel"><p class="empty">Impossible de charger la liste des candidats (${escapeHtml(err.message)}).</p></section>
    `;
    return;
  }

}

init();
document.addEventListener("keydown", (event) => {
  if (!document.querySelector(".express-summary.open")) return;
  if (event.key === "Escape") closeExpressSummary();
  if (event.key === "ArrowRight") setExpressScene(state.expressIndex + 1, state);
  if (event.key === "ArrowLeft") setExpressScene(state.expressIndex - 1, state);
});
