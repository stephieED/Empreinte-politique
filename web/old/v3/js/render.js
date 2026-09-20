// Imports from config
import { CANDIDATS_URL, PROFILE_URL, PIVOT_PROFILE_URL, REAL_GROUP_PROFILES, REAL_GROUP_PROFILE_URL, UI_ICONS, THEME_OPTIONS, THEME_RULES, DEFAULT_THEME, MAX_COMPARE_CANDIDATES, TITLE_TRUNCATE_LENGTH, TITLE_TRUNCATE_SLICE, INTERVENTION_TEXT_PREVIEW_LENGTH, NON_VOTING_PATTERN, DEBATED_TEXT_STAGES, TEXT_ROLE_LABELS, TEXT_STAGE_LABELS, AMENDMENT_OUTCOMES, TEXT_STAGE_COLORS, TEXT_STAGES_ORDER, THEME_COLORS, PANEL_ORDER, PANEL_ICON_ATTRS, PANEL_META, KPI_ICONS, MS_PER_YEAR, RESPONSIBILITY_CATEGORIES, ROLE_PRIORITY, CATEGORIE_LABELS_FR, MANDATE_FILTERS, ENSEMBLE_VOTE_PATTERN, READING_STAGE_RANK } from './config.js';

// Imports from utils
import { setDocumentTitle, escapeHtml, toDateMs, formatIsoDate, shortName, simplifyTitle, normalizedText, detectThemeFromText, themeLabel, voteLabelAndClass, inTheme, isPublicCarriedText, publicCarriedTexts, textExclusionReasons, sourceLinkHtml, voteSourceUrl, compareFactsForTheme, withTheme, average, formatPercentage, candidateLastName, readingStageRank, parseEnsembleVote } from './utils.js';

// Imports from app (circular — resolved at call time)
import { updateActiveAvatarChip, updateStickyLayoutVars, updateProfileRailVisibility, bindRenderedEvents, selectCandidate, selectRealGroup } from './app.js';

export function computeMandateTenure(profile) {
  const electifs = (profile.mandats || []).filter((m) => m.categorie === "mandat_electif");
  const debuts = electifs.map((m) => toDateMs(m.debut)).filter(Boolean);
  if (!debuts.length) return null;
  const debutMin = Math.min(...debuts);
  const enCours = electifs.some((m) => m.actif);
  const fins = electifs.map((m) => toDateMs(m.fin)).filter(Boolean);
  const refEnd = enCours || !fins.length ? Date.now() : Math.max(...fins);
  const annees = Math.max(0, Math.round(((refEnd - debutMin) / MS_PER_YEAR) * 10) / 10);
  return { debutIso: new Date(debutMin).toISOString().slice(0, 10), annees, enCours };
}

// KPI 2 — Responsabilités institutionnelles : dédupliquées par intitulé pour ne pas
// gonfler le chiffre avec des réaffectations administratives internes (churn de commissions).
export function bestRoleType(types) {
  for (const kw of ROLE_PRIORITY) {
    const match = types.find((t) => (t || "").toLowerCase().includes(kw));
    if (match) return match;
  }
  return types[0] || "membre";
}

export function dedupeResponsibilities(profile) {
  const relevant = (profile.mandats || []).filter((m) => RESPONSIBILITY_CATEGORIES.includes(m.categorie));
  const byLabel = new Map();
  for (const m of relevant) {
    const key = m.label || "Responsabilité non précisée";
    if (!byLabel.has(key)) {
      byLabel.set(key, { label: key, categorie: m.categorie, types: [], debuts: [], fins: [], actif: false });
    }
    const entry = byLabel.get(key);
    entry.types.push(m.type);
    if (m.debut) entry.debuts.push(toDateMs(m.debut));
    if (m.fin) entry.fins.push(toDateMs(m.fin));
    if (m.actif) entry.actif = true;
  }
  return [...byLabel.values()]
    .map((e) => ({
      label: e.label,
      categorie: e.categorie,
      type: bestRoleType(e.types),
      debut: e.debuts.length ? new Date(Math.min(...e.debuts)).toISOString().slice(0, 10) : null,
      fin: e.actif ? null : (e.fins.length ? new Date(Math.max(...e.fins)).toISOString().slice(0, 10) : null),
      actif: e.actif,
    }))
    .sort((a, b) => {
      const notableDiff = Number(isNotableResponsibility(b)) - Number(isNotableResponsibility(a));
      return notableDiff || (b.debut || "").localeCompare(a.debut || "");
    });
}

export function computeResponsibilitiesSummary(profile) {
  const items = dedupeResponsibilities(profile);
  return { distinctCount: items.length };
}

export function isNotableResponsibility(responsibility) {
  return ROLE_PRIORITY.some((keyword) => (responsibility.type || "").toLowerCase().includes(keyword));
}

export function mandateRoleTone(fonction) {
  const role = normalizedText(fonction || "");
  if (/\bvice[- ]president\b/.test(role)) return "vice_presidence";
  if (/\bco[- ]president\b/.test(role) || /\bpresident\b/.test(role)) return "presidence";
  if (/rapporteur|rapporteure|co[- ]rapporteur/.test(role)) return "rapporteur";
  return "membre";
}

export function mandateBorderStyle(categorie) {
  return ["groupe_amitie", "extra_parlementaire"].includes(categorie) ? "is-dashed" : "is-solid";
}

export function sourcedHemicyclePosition(profile) {
  const mandate = (profile.pivot_mandats || []).find((item) => item.position_dans_hemicycle && item.source_url);
  return mandate?.position_dans_hemicycle || null;
}

export function hemicyclePeriods(profile) {
  return (profile.pivot_mandats || [])
    .filter((item) => item.position_dans_hemicycle && item.source_url)
    .map((item) => ({
      position: item.position_dans_hemicycle,
      debutMs: toDateMs(item.debut),
      finMs: item.actif || !item.fin ? Number.POSITIVE_INFINITY : toDateMs(item.fin),
    }))
    .filter((period) => Number.isFinite(period.debutMs));
}

export function classifyDateInHemicycle(dateIso, periods) {
  if (!dateIso || !periods.length) return "indetermine";
  const dateMs = toDateMs(dateIso);
  if (!Number.isFinite(dateMs)) return "indetermine";
  const matching = periods
    .filter((period) => dateMs >= period.debutMs && dateMs <= period.finMs)
    .map((period) => period.position);
  // Une période gouvernementale prime : un ministre n'est, au sens
  // parlementaire, ni majorité ni opposition pendant sa fonction (mandat
  // électif généralement suspendu, voir suspendu_pour_fonction_gouvernementale).
  if (matching.includes("gouvernement")) return "gouvernement";
  const hasMajorite = matching.includes("majorite");
  const hasOpposition = matching.includes("opposition");
  if (hasMajorite && hasOpposition) return "mixte";
  if (hasMajorite) return "majorite";
  if (hasOpposition) return "opposition";
  return "indetermine";
}

export function classifyTexteInHemicycle(texte, periods) {
  if (!periods.length) return "indetermine";
  const anchors = [texte.date_max, texte.date_min].filter(Boolean);
  if (!anchors.length) return "indetermine";
  const labels = anchors.map((dateIso) => classifyDateInHemicycle(dateIso, periods));
  if (labels.includes("gouvernement")) return "gouvernement";
  const hasMajorite = labels.includes("majorite");
  const hasOpposition = labels.includes("opposition");
  if (hasMajorite && hasOpposition) return "mixte";
  if (hasMajorite) return "majorite";
  if (hasOpposition) return "opposition";
  return labels[0] || "indetermine";
}

export function splitLegislativeFactsByHemicycle(profile) {
  const periods = hemicyclePeriods(profile);
  const textesBuckets = {
    majorite: [], opposition: [], gouvernement: [], mixte: [], indetermine: [],
  };
  const amendementsBuckets = {
    majorite: [], opposition: [], gouvernement: [], mixte: [], indetermine: [],
  };
  for (const texte of (profile.textes_portes || [])) {
    const bucket = classifyTexteInHemicycle(texte, periods);
    textesBuckets[bucket]?.push(texte);
  }
  for (const amendement of (profile.amendements || [])) {
    const bucket = classifyDateInHemicycle(amendement.date, periods);
    amendementsBuckets[bucket]?.push(amendement);
  }
  return { periods, textesBuckets, amendementsBuckets };
}

export function filterTextesByScope(profile, scope, state) {
  const themedTextes = (profile.textes_portes || []).filter((d) => inTheme(d, state.selectedTheme));
  if (scope === "all") return themedTextes;
  const split = splitLegislativeFactsByHemicycle(profile);
  if (!split.periods.length) return scope === "non_distingue" ? themedTextes : [];
  const bucket = scope === "non_distingue"
    ? [...(split.textesBuckets.mixte || []), ...(split.textesBuckets.indetermine || [])]
    : (split.textesBuckets[scope] || []);
  return themedTextes.filter((item) => bucket.includes(item));
}

export function filterAmendementsByScope(profile, scope, state = null) {
  const amendements = (profile.amendements || []).filter((a) => (state ? inTheme(a, state.selectedTheme) : true));
  if (scope === "all") return amendements;
  if (scope === "gouvernement") return [];
  const split = splitLegislativeFactsByHemicycle(profile);
  if (!split.periods.length) return scope === "non_distingue" ? amendements : [];
  const bucket = scope === "non_distingue"
    ? [...(split.amendementsBuckets.mixte || []), ...(split.amendementsBuckets.indetermine || [])]
    : (split.amendementsBuckets[scope] || []);
  return amendements.filter((item) => bucket.includes(item));
}

export function buildKpiColumnData(profile, scope, state) {
  const split = splitLegislativeFactsByHemicycle(profile);
  const textesBucket = scope === "all"
    ? (profile.textes_portes || [])
    : (split.textesBuckets[scope] || []);
  const amendsBucket = scope === "all"
    ? (profile.amendements || [])
    : (split.amendementsBuckets[scope] || []);
  const publicTextes = textesBucket.filter((d) => inTheme(d, state.selectedTheme) && isPublicCarriedText(d));
  const amendements = amendsBucket;
  const counts = Object.fromEntries(AMENDMENT_OUTCOMES.map(([o]) => [o, 0]));
  for (const a of amendements) {
    if (Object.hasOwn(counts, a.sort)) counts[a.sort] += 1;
  }
  return { publicTextes, amendements, counts };
}

export function renderOutcomeBar(counts, totalAmends, scope, state) {
  if (totalAmends === 0) return `<div class="outcome-bar"></div>`;
  return `<div class="outcome-bar">${renderOutcomeSegments(counts, totalAmends, scope, state)}</div>`;
}

export function renderOutcomeLegend(counts, totalAmends, scope, state) {
  return `<div class="outcome-legend">${AMENDMENT_OUTCOMES.map(([outcome, label]) => {
    const n = counts[outcome] || 0;
    if (!n && totalAmends > 0) return "";
    const isActive = state.amendementsOutcomeFilter === outcome && state.textesScopeFilter === scope;
    const swatchColor = { "adopté": "var(--vert)", "rejeté": "var(--rouge)", "retiré": "#8B8B00", "tombé": "var(--muted)", "irrecevable": "#9C4D00", "non_soutenu": "#5A6E7F" }[outcome] || "var(--line)";
    return `<button type="button" class="outcome-legend-item${isActive ? " is-active" : ""}" data-amend-outcome="${escapeHtml(outcome)}" data-scope="${escapeHtml(scope)}" aria-pressed="${isActive}"><span class="outcome-legend-swatch" style="background:${swatchColor}"></span>${n} ${escapeHtml(label)}</button>`;
  }).join("")}</div>`;
}

export function renderThemeBar(amendements, scope) {
  const total = amendements.length;
  if (total === 0) return `<div class="outcome-bar"></div>`;
  return `<div class="outcome-bar">${renderThemeSegments(amendements, scope)}</div>`;
}

export function renderThemeLegend(amendements, scope) {
  const themeCounts = {};
  for (const a of amendements) {
    const t = a._theme || DEFAULT_THEME;
    themeCounts[t] = (themeCounts[t] || 0) + 1;
  }
  const items = Object.entries(themeCounts).map(([theme, n]) => {
    const color = THEME_COLORS[theme] || "var(--muted)";
    return `<span class="outcome-legend-item"><span class="outcome-legend-swatch" style="background:${color}"></span>${n} ${escapeHtml(themeLabel(theme))}</span>`;
  }).join("");
  return `<div class="outcome-legend">${items}</div>`;
}

export function renderStageBar(publicTextes) {
  const total = publicTextes.length;
  if (total === 0) return `<div class="outcome-bar"></div>`;
  return `<div class="outcome-bar">${renderStageSegments(publicTextes)}</div>`;
}

export function renderOutcomeSegments(counts, totalAmends, scope, state, interactive = true) {
  return AMENDMENT_OUTCOMES.map(([outcome]) => {
    const n = counts[outcome] || 0;
    if (!n) return "";
    const pct = (n / totalAmends * 100).toFixed(2);
    const isActive = interactive && state.amendementsOutcomeFilter === outcome && state.textesScopeFilter === scope;
    const attrs = interactive
      ? ` data-outcome="${escapeHtml(outcome)}" data-scope="${escapeHtml(scope)}" role="button" tabindex="0" aria-label="${escapeHtml(outcome)}: ${n} sur ${totalAmends}"`
      : "";
    return `<span class="outcome-segment${isActive ? " is-active" : ""}"${attrs} style="flex:${pct}" title="${escapeHtml(outcome)}: ${n}/${totalAmends}"></span>`;
  }).join("");
}

export function renderThemeSegments(items, scope) {
  const total = items.length;
  const themeCounts = {};
  for (const item of items) {
    const t = item._theme || DEFAULT_THEME;
    themeCounts[t] = (themeCounts[t] || 0) + 1;
  }
  return Object.entries(themeCounts).map(([theme, n]) => {
    const pct = (n / total * 100).toFixed(2);
    const color = THEME_COLORS[theme] || "var(--muted)";
    return `<span class="theme-segment" data-theme="${escapeHtml(theme)}" data-scope="${escapeHtml(scope)}" style="flex:${pct};background:${color}" title="${escapeHtml(themeLabel(theme))}: ${n}/${total}"></span>`;
  }).join("");
}

export function renderStageSegments(publicTextes) {
  const total = publicTextes.length;
  const counts = {};
  for (const d of publicTextes) {
    const s = TEXT_STAGES_ORDER.includes(d.stade_procedural) ? d.stade_procedural : "examine_commission";
    counts[s] = (counts[s] || 0) + 1;
  }
  return TEXT_STAGES_ORDER.filter((s) => counts[s]).map((stage) => {
    const n = counts[stage];
    const pct = (n / total * 100).toFixed(2);
    const color = TEXT_STAGE_COLORS[stage] || "var(--muted)";
    return `<span class="theme-segment" data-stage="${escapeHtml(stage)}" style="flex:${pct};background:${color}" title="${escapeHtml(TEXT_STAGE_LABELS[stage] || stage)}: ${n}/${total}"></span>`;
  }).join("");
}

export function renderStageLegend(publicTextes) {
  const counts = {};
  for (const d of publicTextes) {
    const s = TEXT_STAGES_ORDER.includes(d.stade_procedural) ? d.stade_procedural : "examine_commission";
    counts[s] = (counts[s] || 0) + 1;
  }
  const items = TEXT_STAGES_ORDER.filter((s) => counts[s]).map((stage) => {
    const n = counts[stage];
    const color = TEXT_STAGE_COLORS[stage] || "var(--muted)";
    return `<span class="outcome-legend-item"><span class="outcome-legend-swatch" style="background:${color}"></span>${n} ${escapeHtml(TEXT_STAGE_LABELS[stage] || stage)}</span>`;
  }).join("");
  return `<div class="outcome-legend">${items}</div>`;
}

export function renderKpiColumn(profile, scope, label, noPeriods, state) {
  const isActive = state.textesScopeFilter === scope && state.amendementsOutcomeFilter === "all";
  if (noPeriods && scope !== "all") {
    return `<div class="textes-kpi-col${isActive ? " is-active" : ""}" data-textes-scope="${escapeHtml(scope)}" role="button" tabindex="0" aria-label="Filtrer: ${escapeHtml(label)}" aria-pressed="${isActive}">
      <div class="textes-kpi-col-label">${escapeHtml(label)}</div>
      <div class="textes-kpi-empty">Position dans l'hémicycle non sourcée pour cette fiche</div>
    </div>`;
  }
  const { publicTextes, amendements, counts } = buildKpiColumnData(profile, scope, state);
  const total = amendements.length;
  const byTheme = state.textesKpiView === "par_theme";
  const textesBarBlock = publicTextes.length
    ? `<div class="textes-kpi-bar-label">Textes portés</div>
       ${byTheme ? renderThemeBar(publicTextes, scope) : renderStageBar(publicTextes)}
       ${byTheme ? renderThemeLegend(publicTextes, scope) : renderStageLegend(publicTextes)}`
    : "";
  const amendsBar = byTheme ? renderThemeBar(amendements, scope) : renderOutcomeBar(counts, total, scope, state);
  const amendsLegend = total
    ? (byTheme ? renderThemeLegend(amendements, scope) : renderOutcomeLegend(counts, total, scope, state))
    : `<div class="textes-kpi-empty">Aucun amendement</div>`;
  return `<div class="textes-kpi-col${isActive ? " is-active" : ""}" data-textes-scope="${escapeHtml(scope)}" role="button" tabindex="0" aria-label="Filtrer: ${escapeHtml(label)}" aria-pressed="${isActive}">
    <div class="textes-kpi-col-label">${escapeHtml(label)}</div>
    <div class="textes-kpi-col-count">${publicTextes.length}</div>
    <div class="textes-kpi-col-sublabel">texte(s) porté(s)</div>
    ${textesBarBlock}
    <div class="textes-kpi-bar-label">Amendements</div>
    ${amendsBar}
    ${amendsLegend}
  </div>`;
}

export function renderLegislativeScopeBars(profile, counts, total, state, kind, includeMinisterial = false) {
  const rows = [
    { scope: "majorite", label: "Majorité" },
    { scope: "opposition", label: "Opposition" },
    { scope: "non_distingue", label: "Non distingué" },
  ];
  if (includeMinisterial) {
    rows.push({ scope: "gouvernement", label: "Activité ministérielle" });
  }
  const isAnyActive = state.textesScopeFilter !== "all";
  return `<div class="scope-bars">${rows.map((row) => {
    const count = counts[row.scope] || 0;
    const pct = total > 0 ? ((count / total) * 100).toFixed(2) : "0.00";
    const isActive = state.textesScopeFilter === row.scope;
    const isDimmed = isAnyActive && !isActive;
    const items = kind === "textes"
      ? filterTextesByScope(profile, row.scope, state).filter((d) => isPublicCarriedText(d))
      : filterAmendementsByScope(profile, row.scope, state);
    const itemCounts = Object.fromEntries(AMENDMENT_OUTCOMES.map(([o]) => [o, 0]));
    for (const item of items) {
      if (kind === "amendements" && Object.hasOwn(itemCounts, item.sort)) itemCounts[item.sort] += 1;
    }
    const segments = state.textesKpiView === "par_theme"
      ? renderThemeSegments(items, row.scope)
      : (kind === "textes" ? renderStageSegments(items) : renderOutcomeSegments(itemCounts, items.length, row.scope, state, false));
    const note = row.scope === "gouvernement" && count === 0
      ? `<span class="scope-bar-note">aucune activité ministérielle</span>`
      : "";
    return `<button type="button" class="scope-bar-row${isActive ? " is-active" : ""}${isDimmed ? " is-dimmed" : ""}" data-textes-scope="${escapeHtml(row.scope)}" aria-pressed="${isActive}" aria-label="Filtrer : ${escapeHtml(row.label)} (${count})">
      <span class="scope-bar-label">${escapeHtml(row.label)}</span>
      <span class="scope-bar-track"><span class="scope-bar-fill scope-bar-fill--stacked" style="width:${pct}%">${segments}</span></span>
      <span class="scope-bar-count">${count}</span>
      ${note}
    </button>`;
  }).join("")}</div>`;
}

export function renderTextesKpi(profile, state) {
  const split = splitLegislativeFactsByHemicycle(profile);
  const allPublicTextes = (profile.textes_portes || []).filter((d) => inTheme(d, state.selectedTheme) && isPublicCarriedText(d));
  const allAmendements = (profile.amendements || []).filter((a) => inTheme(a, state.selectedTheme));
  const countBuckets = split.periods.length
    ? {
      textes: {
        majorite: split.textesBuckets.majorite.filter((d) => inTheme(d, state.selectedTheme) && isPublicCarriedText(d)).length,
        opposition: split.textesBuckets.opposition.filter((d) => inTheme(d, state.selectedTheme) && isPublicCarriedText(d)).length,
        non_distingue: [...(split.textesBuckets.mixte || []), ...(split.textesBuckets.indetermine || [])]
          .filter((d) => inTheme(d, state.selectedTheme) && isPublicCarriedText(d)).length,
        gouvernement: split.textesBuckets.gouvernement.filter((d) => inTheme(d, state.selectedTheme) && isPublicCarriedText(d)).length,
      },
      amendements: {
        majorite: split.amendementsBuckets.majorite.filter((a) => inTheme(a, state.selectedTheme)).length,
        opposition: split.amendementsBuckets.opposition.filter((a) => inTheme(a, state.selectedTheme)).length,
        non_distingue: [...(split.amendementsBuckets.mixte || []), ...(split.amendementsBuckets.indetermine || [])]
          .filter((a) => inTheme(a, state.selectedTheme)).length,
      },
    }
    : {
      textes: { majorite: 0, opposition: 0, non_distingue: allPublicTextes.length, gouvernement: 0 },
      amendements: { majorite: 0, opposition: 0, non_distingue: allAmendements.length },
    };
  const isFilterActive = state.textesScopeFilter !== "all" || state.amendementsOutcomeFilter !== "all";
  const byTheme = state.textesKpiView === "par_theme";
  const allAmendementCounts = Object.fromEntries(AMENDMENT_OUTCOMES.map(([o]) => [o, 0]));
  for (const a of allAmendements) {
    if (Object.hasOwn(allAmendementCounts, a.sort)) allAmendementCounts[a.sort] += 1;
  }
  const resetBtn = isFilterActive
    ? `<button type="button" class="textes-kpi-reset" data-reset-textes-filters>Réinitialiser les filtres</button>`
    : "";

  return `
    <div class="textes-kpi-controls" role="group" aria-label="Coloration des barres">
      <button type="button" data-textes-kpi-view="par_statut" aria-pressed="${state.textesKpiView === "par_statut"}">Par statut</button>
      <button type="button" data-textes-kpi-view="par_theme" aria-pressed="${state.textesKpiView === "par_theme"}">Par thème</button>
      ${resetBtn}
    </div>
    <div class="textes-kpi-grid">
      <article class="textes-kpi-col">
        <div class="textes-kpi-col-label">Textes portés</div>
        ${renderLegislativeScopeBars(profile, countBuckets.textes, allPublicTextes.length, state, "textes", true)}
        ${allPublicTextes.length
          ? (byTheme ? renderThemeLegend(allPublicTextes, "all") : renderStageLegend(allPublicTextes))
          : `<div class="textes-kpi-empty">Aucun texte porté</div>`}
      </article>
      <article class="textes-kpi-col">
        <div class="textes-kpi-col-label">Amendements</div>
        ${renderLegislativeScopeBars(profile, countBuckets.amendements, allAmendements.length, state, "amendements")}
        ${allAmendements.length
          ? (byTheme ? renderThemeLegend(allAmendements, "all") : renderOutcomeLegend(allAmendementCounts, allAmendements.length, "all", state))
          : `<div class="textes-kpi-empty">Aucun amendement</div>`}
      </article>
    </div>
  `;
}

export function renderMinisterialIncompatibilities(profile) {
  const periods = (profile.pivot_mandats || [])
    .map((mandate) => mandate.suspendu_pour_fonction_gouvernementale)
    .filter(Boolean);
  if (!periods.length) return "";
  return `<div class="party-coverage">INCOMPATIBILITÉ MINISTÉRIELLE : ${periods.map((period) => (
    `mandat suspendu du ${escapeHtml(formatIsoDate(period.debut))} au ${escapeHtml(formatIsoDate(period.fin))}${period.suppleant_id ? ` · suppléant : ${escapeHtml(period.suppleant_id)}` : ""}`
  )).join(" · ")}. Cette période n’est pas interprétée comme une absence parlementaire.</div>`;
}

// KPI 3 — Profil de vote synthétique : une répartition, jamais un score isolé.
// Univers retenu : tous les scrutins publics, ordinaires ou solennels, portant sur
// "l'ensemble" du texte (pas les amendements/articles isolés,
// où un "contre" reflète souvent un désaccord technique ponctuel plutôt qu'une opposition de
// principe), et dédupliqué sur la lecture la plus avancée quand un même texte a été voté à
// plusieurs stades (première lecture, nouvelle lecture, CMP, lecture définitive...).
// Limite qui subsiste : un vote sur l'ensemble agrège quand même des motivations plurielles,
// et le regroupement des lectures d'un même texte repose sur une similarité de titre (fragile
// si le libellé change entre chambres). Une donnée manquante reste distincte d'une position.
export function computeFinalTextVoteProfile(profile) {
  const votes = profile.votes || [];
  const groups = new Map();
  let totalLectures = 0;
  for (const v of votes) {
    if (v.type_vote === "motion_censure" || v.sort === "adopte_sans_vote_49_3") continue;
    const parsed = parseEnsembleVote(v.titre);
    if (!parsed) continue;
    totalLectures += 1;
    const current = groups.get(parsed.key);
    if (
      !current ||
      parsed.rank > current.rank ||
      (parsed.rank === current.rank && toDateMs(v.date) > toDateMs(current.vote.date))
    ) {
      groups.set(parsed.key, { rank: parsed.rank, vote: v });
    }
  }
  const counts = { pour: 0, contre: 0, abstention: 0, absent: 0 };
  for (const { vote } of groups.values()) {
    const cls = voteLabelAndClass(vote.position).cls;
    counts[cls] = (counts[cls] || 0) + 1;
  }
  const totalPositions = counts.pour + counts.contre + counts.abstention;
  return { totalTextes: groups.size, totalPositions, totalLectures, counts };
}

export function renderResponsabilites(profile) {
  const items = dedupeResponsibilities(profile);
  if (!items.length) {
    return `<p class="empty">Aucune responsabilité institutionnelle retrouvée.</p>`;
  }
  return `
    <p class="orbit-legend">Jaune = présidence, vice-présidence ou rapport identifié · survoler / toucher pour détailler</p>
    <div class="orbit" aria-label="Constellation des responsabilités">${items.map((r, index) => `
    <button type="button" class="orbit-node ${isNotableResponsibility(r) ? "is-notable" : ""}" style="--tilt:${((index % 7) - 3) * 1.8}deg" aria-expanded="false">
      <strong>${escapeHtml(r.label)}</strong>
      <small>${escapeHtml(formatIsoDate(r.debut))} → ${r.fin ? escapeHtml(formatIsoDate(r.fin)) : (r.actif ? "aujourd’hui" : "fin non renseignée")}</small>
      <span class="orbit-detail"><span>
        <small>${escapeHtml(r.type || "membre")}</small>
        <small>${escapeHtml(CATEGORIE_LABELS_FR[r.categorie] || r.categorie)}</small>
        ${isNotableResponsibility(r) ? `<small>Rôle signalé comme responsabilité notable.</small>` : `<small>Participation comme membre.</small>`}
      </span></span>
    </button>
  `).join("")}</div>`;
}

export function buildMandateTimeline(profile) {
  const dayMs = 24 * 60 * 60 * 1000;
  const dated = [];
  const undated = [];
  for (const mandate of (profile.pivot_mandats || [])) {
    const item = {
      ...mandate,
      sourceUrls: /^https?:\/\//.test(mandate.source_url || "") ? [mandate.source_url] : [],
    };
    (mandate.debut ? dated : undated).push(item);
  }
  dated.sort((a, b) => a.debut.localeCompare(b.debut) || String(a.fin || "").localeCompare(String(b.fin || "")));

  const merged = [];
  for (const mandate of dated) {
    const previous = merged.at(-1);
    const sameRole = previous
      && previous.label === mandate.label
      && previous.categorie === mandate.categorie
      && previous.fonction === mandate.fonction;
    const gap = sameRole && previous.fin ? toDateMs(mandate.debut) - toDateMs(previous.fin) : Number.POSITIVE_INFINITY;
    if (sameRole && gap >= 0 && gap <= dayMs) {
      previous.fin = mandate.fin;
      previous.actif = mandate.actif;
      previous.sourceUrls = [...new Set([...previous.sourceUrls, ...mandate.sourceUrls])];
    } else {
      merged.push(mandate);
    }
  }
  return merged
    .sort((a, b) => b.debut.localeCompare(a.debut) || String(b.fin || "").localeCompare(String(a.fin || "")))
    .concat(undated);
}

export function renderMandateTimeline(profile, state) {
  const filter = MANDATE_FILTERS[state.mandateFilter] || MANDATE_FILTERS.all;
  const items = buildMandateTimeline(profile).filter(filter);
  if (!items.length) return `<p class="empty">Aucun mandat documenté pour ce filtre.</p>`;
  return `<div class="mandate-timeline">${items.map((mandate) => {
    const period = mandate.debut
      ? `${formatIsoDate(mandate.debut)} → ${mandate.actif ? "aujourd’hui" : (mandate.fin ? formatIsoDate(mandate.fin) : "fin non renseignée")}`
      : "date non renseignée";
    return `<article class="mandate-timeline-item">
      <div class="mandate-period">${escapeHtml(period)}</div>
      <div class="mandate-card ${mandateBorderStyle(mandate.categorie)} mandate-role--${mandateRoleTone(mandate.fonction)} ${mandate.actif ? "is-current" : ""}">
        <strong class="mandate-function">${escapeHtml(mandate.label || "Mandat non précisé")}</strong>
        <div class="mandate-row">
          <span class="mandate-role">${escapeHtml(mandate.fonction || "Fonction non renseignée")}</span>
          <small class="mandate-meta">${escapeHtml(CATEGORIE_LABELS_FR[mandate.categorie] || mandate.categorie || "Catégorie non renseignée")}</small>
          ${mandate.actif ? `<span class="mandate-live-tag">en cours</span>` : ""}
        </div>
        ${mandate.sourceUrls.length ? `<div class="mandate-sources">${mandate.sourceUrls.map((url, index) => `<a href="${escapeHtml(url)}" target="_blank" rel="noopener">Source${mandate.sourceUrls.length > 1 ? ` ${index + 1}` : ""}</a>`).join(" · ")}</div>` : ""}
      </div>
    </article>`;
  }).join("")}</div>`;
}

export function renderMandateLegend() {
  return `<div class="mandate-legend" role="note" aria-label="Légende des mandats">
    <span class="mandate-legend-item"><span class="mandate-legend-swatch mandate-role--presidence"></span>Présidence</span>
    <span class="mandate-legend-item"><span class="mandate-legend-swatch mandate-role--vice_presidence"></span>Vice-présidence</span>
    <span class="mandate-legend-item"><span class="mandate-legend-swatch mandate-role--rapporteur"></span>Rapporteur / rapporteure</span>
    <span class="mandate-legend-item"><span class="mandate-legend-swatch mandate-role--membre"></span>Membre</span>
    <span class="mandate-legend-item"><span class="mandate-legend-line is-solid"></span>Trait plein : rôle institutionnel formel</span>
    <span class="mandate-legend-item"><span class="mandate-legend-line is-dashed"></span>Pointillé : rôle déclaratif (amitié / extra-parlementaire)</span>
    <span class="mandate-legend-item"><span class="mandate-live-tag">en cours</span>Mandat actif</span>
  </div>`;
}

export function renderMandates(profile, state) {
  const viewControls = `<div class="mandate-view-controls" role="group" aria-label="Vue des mandats">
    ${[["timeline", "Chronologie"], ["responsibilities", "Responsabilités"]].map(([value, label]) => (
      `<button type="button" class="${state.mandateView === value ? "active" : ""}" data-mandate-view="${value}" aria-pressed="${state.mandateView === value}">${label}</button>`
    )).join("")}
  </div>`;
  if (state.mandateView === "responsibilities") return `${viewControls}${renderMandateLegend()}${renderResponsabilites(profile)}`;
  const filters = `<div class="mandate-filters" role="group" aria-label="Filtrer les mandats">
    ${[["all", "Tous"], ["elective", "Électifs"], ["responsibilities", "Responsabilités"], ["groups", "Groupes"]].map(([value, label]) => (
      `<button type="button" class="${state.mandateFilter === value ? "active" : ""}" data-mandate-filter="${value}" aria-pressed="${state.mandateFilter === value}">${label}</button>`
    )).join("")}
  </div>`;
  return `${viewControls}${filters}${renderMandateLegend()}${renderMandateTimeline(profile, state)}`;
}

export function renderThemePills(state) {
  return `
    <div class="themes-row" aria-label="Filtre des thèmes">
      ${THEME_OPTIONS.map((t) => `
        <button type="button" class="theme-pill ${state.selectedTheme === t.key ? "active" : ""}" data-theme="${t.key}">
          ${t.icon ? `<span aria-hidden="true">${t.icon}</span>` : ""}<span>${escapeHtml(t.label)}</span>
        </button>
      `).join("")}
    </div>
  `;
}

export function renderHeader(meta, profile, state) {
  const nom = profile?.identite?.nom_complet || meta?.nom || profile?.slug || "Candidat";
  const parti = meta?.parti || profile?.identite?.groupe_nom || profile?.identite?.groupe_sigle || "Affiliation non renseignée";
  const statut = meta?.statut || "statut non renseigné";
  const photo = profile?.mandat_europeen?.photo || "";
  const updatedAt = profile?.meta?.genere_le || null;

  // KPI 1 — Ancienneté et statut du mandat
  const tenure = computeMandateTenure(profile);

  // KPI 2 — Responsabilités institutionnelles occupées (dédupliquées, hors churn administratif)
  const responsibilities = computeResponsibilitiesSummary(profile);

  // KPI 3 — Profil de vote synthétique, restreint aux votes sur l'ensemble du texte (dernière lecture connue)
  const voteProfile = computeFinalTextVoteProfile(profile);
  const voteProfilePct = (key) => (voteProfile.totalPositions > 0 ? Math.round((voteProfile.counts[key] / voteProfile.totalPositions) * 100) : 0);

  // Répartition thématique des votes pour histogramme horizontal (sert aussi de base au KPI 4)
  const themeCountMap = {};
  for (const v of (profile.votes || [])) {
    themeCountMap[v._theme] = (themeCountMap[v._theme] || 0) + 1;
  }
  const sortedThemeDist = Object.entries(themeCountMap)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);
  const maxThemeCount = sortedThemeDist[0]?.[1] || 1;

  const themeDistHtml = sortedThemeDist.length ? `
    <div class="theme-dist">
      <p class="theme-dist-title">Répartition des votes par thème</p>
      ${sortedThemeDist.map(([theme, count]) => `
        <div class="theme-dist-row">
          <span class="theme-dist-label">${escapeHtml(themeLabel(theme))}</span>
          <div class="theme-dist-bar-wrap" title="${escapeHtml(themeLabel(theme))} — ${count} vote(s)">
            <div class="theme-dist-bar" style="width:${Math.round((count / maxThemeCount) * 100)}%"></div>
          </div>
          <span class="theme-dist-count">${count}</span>
        </div>
      `).join("")}
    </div>
  ` : "";

  return `
    <section id="resume" class="panel">
      <div class="hero">
        <div class="avatar">${photo ? `<img src="${escapeHtml(photo)}" alt="Photo de ${escapeHtml(nom)}">` : escapeHtml(shortName(nom))}</div>
        <div>
          <h2>${escapeHtml(nom)}</h2>
          <div class="tags">
            <span class="tag">${escapeHtml(parti)}</span>
            <span class="tag">${escapeHtml(statut)}</span>
          </div>
          <button type="button" class="express-launch">Résumé express ▶</button>
        </div>
      </div>

      <div class="summary-grid">
        <div class="kpi-flip ${state.flippedKpis.has("anciennete") ? "flipped" : ""}" tabindex="0" role="button" aria-pressed="${state.flippedKpis.has("anciennete")}" data-kpi="anciennete" aria-label="Ancienneté du mandat, appuyer pour l'explication">
          <div class="kpi-flip-inner">
            <div class="kpi-face kpi-face--front">
              <div class="kpi-icon">${KPI_ICONS.anciennete}</div>
              <div class="kpi-value">${tenure ? `${tenure.annees}\u00a0${tenure.annees <= 1 ? "an" : "ans"}` : "N/D"}</div>
              <div class="kpi-label">Ancienneté du mandat</div>
            </div>
            <div class="kpi-face kpi-face--back">
              <p class="kpi-back-text">${tenure ? (tenure.enCours ? `En cours depuis le ${escapeHtml(formatIsoDate(tenure.debutIso))}.` : `Terminé, débuté le ${escapeHtml(formatIsoDate(tenure.debutIso))}.`) : "Mandat électif non renseigné."} Mesure la durée, pas l'implication.</p>
            </div>
          </div>
        </div>

        <div class="kpi-flip ${state.flippedKpis.has("responsabilites") ? "flipped" : ""}" tabindex="0" role="button" aria-pressed="${state.flippedKpis.has("responsabilites")}" data-kpi="responsabilites" aria-label="Responsabilités occupées, appuyer pour l'explication">
          <div class="kpi-flip-inner">
            <div class="kpi-face kpi-face--front">
              <div class="kpi-icon">${KPI_ICONS.responsabilites}</div>
              <div class="kpi-value">${responsibilities.distinctCount}</div>
              <div class="kpi-label">Responsabilités occupées</div>
            </div>
            <div class="kpi-face kpi-face--back">
              <p class="kpi-back-text">Commissions et engagements distincts, hors réaffectations internes. Les fonctions ordonnent le détail, mais ne produisent aucun total public de « responsabilités notables ».</p>
              <button type="button" class="kpi-back-link" data-goto-panel="mandats">Voir le détail →</button>
            </div>
          </div>
        </div>

        <div class="kpi-flip ${state.flippedKpis.has("vote") ? "flipped" : ""}" tabindex="0" role="button" aria-pressed="${state.flippedKpis.has("vote")}" data-kpi="vote" aria-label="Profil de vote, appuyer pour l'explication">
          <div class="kpi-flip-inner">
            <div class="kpi-face kpi-face--front">
              <div class="kpi-icon">${KPI_ICONS.vote}</div>
              <div class="kpi-value">${voteProfile.totalPositions > 0 ? `${voteProfilePct("pour")}\u00a0%` : "N/D"}</div>
              <div class="kpi-label">Profil de vote — part de "pour"</div>
            </div>
            <div class="kpi-face kpi-face--back">
              ${voteProfile.totalPositions > 0 ? `
                <div class="vote-profile-bar" role="img" aria-label="Répartition des positions documentées : ${voteProfilePct("pour")}% pour, ${voteProfilePct("contre")}% contre, ${voteProfilePct("abstention")}% abstention">
                  <div class="vote-profile-seg--pour" style="width:${voteProfilePct("pour")}%"></div>
                  <div class="vote-profile-seg--contre" style="width:${voteProfilePct("contre")}%"></div>
                  <div class="vote-profile-seg--abstention" style="width:${voteProfilePct("abstention")}%"></div>
                </div>
                <div class="vote-profile-legend">
                  <span><span class="dot dot--pour"></span>Pour ${voteProfilePct("pour")}%</span>
                  <span><span class="dot dot--contre"></span>Contre ${voteProfilePct("contre")}%</span>
                  <span><span class="dot dot--abstention"></span>Abst. ${voteProfilePct("abstention")}%</span>
                </div>
                <p class="kpi-back-text">${voteProfile.totalPositions} position(s) documentée(s) sur des textes entiers, à leur lecture la plus avancée. Scrutins publics ordinaires et solennels; motions de censure et 49.3 sans vote exclus. Pas un score de performance.</p>
              ` : `<p class="kpi-back-text">Aucun vote sur l'ensemble d'un texte retrouvé dans les données disponibles.</p>`}
              <button type="button" class="kpi-back-link" data-goto-panel="votes">Voir le détail →</button>
            </div>
          </div>
        </div>

        <div class="kpi-flip ${state.flippedKpis.has("theme") ? "flipped" : ""}" tabindex="0" role="button" aria-pressed="${state.flippedKpis.has("theme")}" data-kpi="theme" aria-label="Thème dominant, appuyer pour l'explication">
          <div class="kpi-flip-inner">
            <div class="kpi-face kpi-face--front">
              <div class="kpi-icon">${KPI_ICONS.theme}</div>
              <div class="kpi-value">${sortedThemeDist.length ? escapeHtml(themeLabel(sortedThemeDist[0][0])) : "N/D"}</div>
              <div class="kpi-label">Thème dominant</div>
            </div>
            <div class="kpi-face kpi-face--back">
              <p class="kpi-back-text">${sortedThemeDist.length ? `${sortedThemeDist[0][1]} vote(s) sur ce thème.` : "Thème non déterminé."} Classification par mots-clés : une tendance, pas un classement exhaustif.</p>
              <button type="button" class="kpi-back-link" data-goto-panel="votes">Voir le détail →</button>
            </div>
          </div>
        </div>
      </div>

      <aside class="color-legend" aria-label="Légende des couleurs utilisées">
        <span class="color-legend-item"><span class="color-swatch color-swatch--acid"></span>Jaune — accent actif</span>
        <span class="color-legend-item"><span class="color-swatch color-swatch--pink"></span>Rose — signal éditorial</span>
        <span class="color-legend-item"><span class="color-swatch color-swatch--soft"></span>Bleu — repère secondaire</span>
        <span class="color-legend-item"><span class="color-swatch color-swatch--vert"></span>Vert — vote pour</span>
        <span class="color-legend-item"><span class="color-swatch color-swatch--rouge"></span>Rouge — vote contre</span>
        <span class="color-legend-item"><span class="color-swatch color-swatch--muted"></span>Gris — abstention</span>
      </aside>

      ${themeDistHtml}

      <div class="trust-line">
        Données sourcées • Mise à jour le ${escapeHtml(formatIsoDate(updatedAt))} •
        <a class="link" href="methodologie.html" target="_blank" rel="noopener">Voir la méthode</a>
        <a class="link" href="mentions-legales.html" target="_blank" rel="noopener">Mentions légales</a>
      </div>
    </section>
  `;
}

export function renderTextes(profile, scope = "all", state) {
  const allThemedTextes = (profile.textes_portes || []).filter((d) => inTheme(d, state.selectedTheme));
  let themedTextes;
  if (scope === "non_distingue") {
    const split = splitLegislativeFactsByHemicycle(profile);
    const ndSet = new Set([...(split.textesBuckets.mixte || []), ...(split.textesBuckets.indetermine || [])]);
    themedTextes = allThemedTextes.filter((d) => ndSet.has(d));
  } else {
    themedTextes = filterTextesByScope(profile, scope, state);
  }
  const items = themedTextes.filter((d) => isPublicCarriedText(d));
  const excludedItems = themedTextes.filter((d) => !isPublicCarriedText(d));
  const noSplitData = scope !== "all" && !hemicyclePeriods(profile).length;
  if (!items.length) {
    if (noSplitData) {
      return `<p class="empty">Impossible de distinguer les textes entre majorité et opposition pour cette fiche: aucune période sourcée de position dans l’hémicycle n’est disponible.</p>`;
    }
    if (!excludedItems.length) {
      return `<p class="empty">${state.selectedTheme === "all" ? "Aucun texte avec rôle factuel et débat avéré retrouvé." : "Aucun texte répondant aux critères sur ce thème."} Un simple dépôt ou un rôle inconnu n’est pas publié ici.</p>`;
    }

    const sortedExcluded = [...excludedItems].sort((a, b) => {
      const dateDiff = toDateMs(b.date_max || b.date_min) - toDateMs(a.date_max || a.date_min);
      return dateDiff || simplifyTitle(a.titre).localeCompare(simplifyTitle(b.titre), "fr");
    });
    return `
      <p class="source-ref">Aucun texte publiable avec les criteres actuels. ${sortedExcluded.length} texte(s) existent dans la source mais sont exclus de la publication.</p>
      <div class="text-fallback-grid">
        ${sortedExcluded.map((d) => `
          <article class="text-fallback-item">
            <div class="text-fallback-title">${escapeHtml(simplifyTitle(d.titre) || "Titre non renseigne")}</div>
            <div class="small">${escapeHtml(formatIsoDate(d.date_min))}${d.date_max ? ` → ${escapeHtml(formatIsoDate(d.date_max))}` : ""}</div>
            <div>
              ${textExclusionReasons(d).map((reason) => `<span class="text-fallback-reason">${escapeHtml(reason)}</span>`).join("")}
            </div>
            ${sourceLinkHtml(d.source_url, "↗ source")}
          </article>
        `).join("")}
      </div>
    `;
  }
  const sorted = [...items].sort((a, b) => {
    const dateDiff = toDateMs(b.date_max || b.date_min) - toDateMs(a.date_max || a.date_min);
    return dateDiff || simplifyTitle(a.titre).localeCompare(simplifyTitle(b.titre), "fr");
  });
  const byTheme = new Map();
  for (const item of sorted) {
    if (!byTheme.has(item._theme)) byTheme.set(item._theme, []);
    byTheme.get(item._theme).push(item);
  }
  const shelves = [...byTheme.entries()].sort((a, b) => {
    const countDiff = b[1].length - a[1].length;
    if (countDiff) return countDiff;
    const newestDiff = toDateMs(b[1][0]?.date_max || b[1][0]?.date_min) - toDateMs(a[1][0]?.date_max || a[1][0]?.date_min);
    return newestDiff || themeLabel(a[0]).localeCompare(themeLabel(b[0]), "fr");
  });

  return `<p class="source-ref">Sont retenus les textes dont le rôle est sourcé et qui ont au moins été examinés en commission.</p><div class="text-atlas">${shelves.map(([theme, themeItems]) => {
    const expanded = state.expandedTextThemes.has(theme);
    const visible = expanded ? themeItems : themeItems.slice(0, 6);
    return `
      <section class="text-shelf" aria-labelledby="text-theme-${escapeHtml(theme)}">
        <div class="text-shelf-head">
          <strong id="text-theme-${escapeHtml(theme)}">${escapeHtml(themeLabel(theme))}</strong>
          <span></span>
          <span class="text-shelf-count">${themeItems.length} texte(s)</span>
        </div>
        <div class="text-shelf-track">
          ${visible.map((d) => `
            <article class="text-leaf">
              <div class="text-leaf-title">${escapeHtml(simplifyTitle(d.titre))}</div>
              <div>
                <div class="text-leaf-meta">${escapeHtml(TEXT_ROLE_LABELS[d.role])} / ${escapeHtml(TEXT_STAGE_LABELS[d.stade_procedural])} / ${escapeHtml(formatIsoDate(d.date_min))}${d.date_max ? ` → ${escapeHtml(formatIsoDate(d.date_max))}` : ""}</div>
                ${sourceLinkHtml(d.source_url, "↗ source")}
              </div>
            </article>
          `).join("")}
        </div>
        ${themeItems.length > 6 ? `<button type="button" class="text-shelf-more" data-expand-text-theme="${escapeHtml(theme)}">${expanded ? "Réduire" : `Voir les ${themeItems.length} textes`} ${escapeHtml(themeLabel(theme))}</button>` : ""}
      </section>
    `;
  }).join("")}</div>${excludedItems.length ? `
    <div class="text-unpublished-bar">
      <button type="button" class="text-unpublished-toggle" data-toggle-unpublished-textes aria-expanded="${state.showUnpublishedTextes}">
        ${state.showUnpublishedTextes ? "Masquer" : `Voir les ${excludedItems.length} texte(s) non publiés`} <span class="text-unpublished-reason">(rôle factuel absent ou stade non retenu)</span>
      </button>
    </div>
    ${state.showUnpublishedTextes ? `<div class="text-fallback-grid">${[...excludedItems].sort((a, b) => toDateMs(b.date_max || b.date_min) - toDateMs(a.date_max || a.date_min) || simplifyTitle(a.titre).localeCompare(simplifyTitle(b.titre), "fr")).map((d) => `
      <article class="text-fallback-item">
        <div class="text-fallback-title">${escapeHtml(simplifyTitle(d.titre) || "Titre non renseigné")}</div>
        <div class="small">${escapeHtml(formatIsoDate(d.date_min))}${d.date_max ? ` → ${escapeHtml(formatIsoDate(d.date_max))}` : ""}</div>
        <div>${textExclusionReasons(d).map((reason) => `<span class="text-fallback-reason">${escapeHtml(reason)}</span>`).join("")}</div>
        ${sourceLinkHtml(d.source_url, "↗ source")}
      </article>
    `).join("")}</div>` : ""}
  ` : ""}`;
}

export function renderAmendements(profile, scope = "all", outcomeFilter = "all") {
  let amendements;
  if (scope === "non_distingue") {
    const split = splitLegislativeFactsByHemicycle(profile);
    const ndSet = new Set([...(split.amendementsBuckets.mixte || []), ...(split.amendementsBuckets.indetermine || [])]);
    amendements = (profile.amendements || []).filter((a) => ndSet.has(a));
  } else {
    amendements = filterAmendementsByScope(profile, scope);
  }
  const noSplitData = scope !== "all" && scope !== "non_distingue" && !hemicyclePeriods(profile).length;
  if (noSplitData) {
    return `<p class="empty">Impossible de distinguer les amendements entre majorité et opposition pour cette fiche: aucune période sourcée de position dans l'hémicycle n'est disponible.</p>`;
  }
  if (outcomeFilter !== "all") {
    amendements = amendements.filter((a) => a.sort === outcomeFilter);
  }
  if (!amendements.length) return `<p class="empty">Aucun amendement structuré disponible${outcomeFilter !== "all" ? ` (filtre : ${escapeHtml(outcomeFilter)})` : ""}.</p>`;
  const counts = Object.fromEntries(AMENDMENT_OUTCOMES.map(([outcome]) => [outcome, 0]));
  for (const amendement of amendements) {
    if (Object.hasOwn(counts, amendement.sort)) counts[amendement.sort] += 1;
  }
  return `
    <p class="source-ref">Répartition des issues sur ${amendements.length} amendement(s) documenté(s)${outcomeFilter !== "all" ? ` — filtre actif : ${escapeHtml(outcomeFilter)}` : ""}. Aucun taux isolé : l'issue dépend aussi de la procédure et du texte.</p>
    <div class="void-map">${AMENDMENT_OUTCOMES.map(([outcome, label]) => `
      <div class="void-signal"><span class="void-number">${counts[outcome]}</span><strong>${escapeHtml(label)}</strong></div>
    `).join("")}</div>
  `;
}

export function buildAmendementMatchMap(textes, amendements) {
  const normalizedTextes = textes.map((texte) => ({
    texte,
    key: normalizedText(simplifyTitle(texte.titre || "")),
  }));
  const map = new Map(textes.map((texte) => [texte, []]));
  for (const amendement of amendements) {
    const cible = normalizedText(simplifyTitle(amendement.texte_vise || ""));
    const direct = normalizedTextes.find(({ key }) => key && cible && (key.includes(cible) || cible.includes(key)));
    if (direct) {
      map.get(direct.texte).push(amendement);
    }
  }
  return map;
}

export function renderLegislativeDetails(profile, state) {
  const scope = state.textesScopeFilter;
  const textes = (scope === "all"
    ? (profile.textes_portes || []).filter((d) => inTheme(d, state.selectedTheme))
    : filterTextesByScope(profile, scope, state))
    .filter((d) => isPublicCarriedText(d))
    .sort((a, b) => toDateMs(b.date_max || b.date_min) - toDateMs(a.date_max || a.date_min));
  const amendements = filterAmendementsByScope(profile, scope, state)
    .sort((a, b) => toDateMs(b.date) - toDateMs(a.date));
  const amendementMap = buildAmendementMatchMap(textes, amendements);
  const outcomeLabels = Object.fromEntries(AMENDMENT_OUTCOMES.map(([value, label]) => [value, label]));
  const activeScopeLabel = {
    all: "Tous les éléments",
    majorite: "Majorité",
    opposition: "Opposition",
    non_distingue: "Non distingué",
    gouvernement: "Activité ministérielle",
  }[scope] || "Tous les éléments";
  return `
    <div class="legislative-details-head">
      <h2>Détail filtré</h2>
      <p class="source-ref">Filtre actif : ${escapeHtml(activeScopeLabel)}.</p>
    </div>
    <section class="legislative-block">
      <div class="legislative-block-head">
        <h3>Textes portés</h3>
      </div>
      ${textes.length ? `<div class="legislative-detail-list">${textes.map((texte) => {
    const linkedAmends = amendementMap.get(texte) || [];
    return `<article class="legislative-detail-card">
            <div class="text-leaf-title">${escapeHtml(simplifyTitle(texte.titre) || "Titre non renseigné")}</div>
            <div class="text-leaf-meta">${escapeHtml(TEXT_ROLE_LABELS[texte.role] || texte.role || "Rôle non renseigné")} / ${escapeHtml(TEXT_STAGE_LABELS[texte.stade_procedural] || texte.stade_procedural || "stade non renseigné")} / ${escapeHtml(formatIsoDate(texte.date_min))}${texte.date_max ? ` → ${escapeHtml(formatIsoDate(texte.date_max))}` : ""}</div>
            ${sourceLinkHtml(texte.source_url, "↗ source")}
            <div class="amendement-nested-list">
              ${linkedAmends.length ? linkedAmends.map((amendement) => `<article class="amendement-detail-card">
                <strong>${escapeHtml(amendement.numero || "Amendement sans numéro")}</strong>
                <div class="small">${escapeHtml(amendement.texte_vise || "Texte visé non renseigné")}</div>
                <div class="small">${escapeHtml(outcomeLabels[amendement.sort] || amendement.sort || "Issue non renseignée")} · ${escapeHtml(formatIsoDate(amendement.date))}</div>
                <div class="small">${escapeHtml(amendement.premier_signataire || "Auteur non renseigné")}</div>
                ${sourceLinkHtml(amendement.source_url, "↗ source")}
              </article>`).join("") : `<p class="small">Aucun amendement rattaché sur ce filtre.</p>`}
            </div>
          </article>`;
  }).join("")}</div>` : `<p class="empty">Aucun texte porté pour ce filtre.</p>`}
    </section>
    <section class="legislative-block">
      <div class="legislative-block-head">
        <h3>Amendements (liste filtrée)</h3>
      </div>
      ${scope === "gouvernement"
    ? `<p class="empty">Les amendements ne sont pas classés par activité ministérielle dans ce panneau.</p>`
    : (amendements.length
      ? `<div class="amendement-detail-list">${amendements.map((amendement) => `<article class="amendement-detail-card">
              <strong>${escapeHtml(amendement.numero || "Amendement sans numéro")}</strong>
              <div class="small">${escapeHtml(amendement.texte_vise || "Texte visé non renseigné")}</div>
              <div class="small">${escapeHtml(outcomeLabels[amendement.sort] || amendement.sort || "Issue non renseignée")} · ${escapeHtml(formatIsoDate(amendement.date))}</div>
              <div class="small">${escapeHtml(amendement.premier_signataire || "Auteur non renseigné")}</div>
              ${sourceLinkHtml(amendement.source_url, "↗ source")}
            </article>`).join("")}</div>`
      : `<p class="empty">Aucun amendement structuré pour ce filtre.</p>`)}
    </section>
  `;
}

export function sortVotesByDate(votes) {
  return [...votes].sort((a, b) => {
    const dateDiff = toDateMs(b.date) - toDateMs(a.date);
    return dateDiff || simplifyTitle(a.titre).localeCompare(simplifyTitle(b.titre), "fr");
  });
}

export function renderVotes(profile, state) {
  const items = (profile.votes || []).filter((v) => inTheme(v, state.selectedTheme));
  if (!items.length) {
    return `<p class="empty">${state.selectedTheme === "all" ? "Aucune donnée de vote trouvée dans cette fiche." : "Aucune donnée de vote trouvée sur ce thème."}</p>`;
  }

  const motions = items.filter((vote) => vote.type_vote === "motion_censure");
  const fortyNineThree = items.filter((vote) => vote.sort === "adopte_sans_vote_49_3");
  const ordinaryVotes = items.filter((vote) => vote.type_vote !== "motion_censure" && vote.sort !== "adopte_sans_vote_49_3");
  const byTheme = new Map();
  for (const vote of ordinaryVotes) {
    if (!byTheme.has(vote._theme)) byTheme.set(vote._theme, []);
    byTheme.get(vote._theme).push(vote);
  }
  const shelves = [...byTheme.entries()]
    .map(([theme, votes]) => [theme, sortVotesByDate(votes)])
    .sort((a, b) => {
      const countDiff = b[1].length - a[1].length;
      return countDiff || themeLabel(a[0]).localeCompare(themeLabel(b[0]), "fr");
    });

  return `
    ${fortyNineThree.length ? `<div class="party-coverage"><strong>49.3, sans vote sur le texte</strong><br>${fortyNineThree.map((vote) => `${escapeHtml(simplifyTitle(vote.titre))} · ${escapeHtml(formatIsoDate(vote.date))}`).join("<br>")}</div>` : ""}
    ${motions.length ? `<div class="party-coverage"><strong>Motions de censure, scrutins séparés</strong><br>${motions.map((vote) => {
      const badge = voteLabelAndClass(vote.position);
      return `${escapeHtml(simplifyTitle(vote.titre))} · ${escapeHtml(badge.label)} · ${escapeHtml(formatIsoDate(vote.date))}${vote.texte_lie_id ? ` · texte lié ${escapeHtml(vote.texte_lie_id)}` : ""}`;
    }).join("<br>")}</div>` : ""}
    <p class="source-ref">Dans chaque thème : du vote le plus récent au plus ancien.</p>
    <div class="vote-atlas">
      ${shelves.map(([theme, themeVotes]) => {
        const expanded = state.expandedVoteThemes.has(theme);
        const visible = expanded ? themeVotes : themeVotes.slice(0, 18);
        return `
          <section class="vote-shelf" aria-labelledby="vote-theme-${escapeHtml(theme)}">
            <div class="vote-shelf-head">
              <strong id="vote-theme-${escapeHtml(theme)}">${escapeHtml(themeLabel(theme))}</strong>
              <span></span>
              <span class="vote-shelf-count">${themeVotes.length} vote(s)</span>
            </div>
            <div class="vote-cloud">
              ${visible.map((v, index) => {
                const badge = voteLabelAndClass(v.position);
                const weight = 1 + (index % 5);
                const source = voteSourceUrl(profile, v);
                const tagName = source ? "a" : "span";
                const sourceAttrs = source ? `href="${escapeHtml(source.url)}" target="_blank" rel="noopener"` : "";
                return `<${tagName} class="vote-token ${badge.cls}" style="--weight:${weight}" title="${escapeHtml(v.titre || "")}" ${sourceAttrs}>
                  ${escapeHtml(simplifyTitle(v.titre))}
                  <em>${escapeHtml(badge.label)} / ${escapeHtml(formatIsoDate(v.date))}${source ? `<span class="source-mark">↗ ${source.direct ? "scrutin" : "profil source"}</span>` : ""}</em>
                </${tagName}>`;
              }).join("")}
            </div>
            ${themeVotes.length > 18 ? `<button type="button" class="vote-shelf-more" data-expand-vote-theme="${escapeHtml(theme)}">${expanded ? "Réduire" : `Voir les ${themeVotes.length} votes`} ${escapeHtml(themeLabel(theme))}</button>` : ""}
          </section>
        `;
      }).join("")}
    </div>
  `;
}

export function renderAbsences(profile, state) {
  const textes = publicCarriedTexts(profile).filter((d) => inTheme(d, state.selectedTheme));
  const inters = (profile.interventions || []).filter((i) => inTheme(i, state.selectedTheme));

  const themeUniverse = THEME_OPTIONS.filter((t) => t.key !== "all").map((t) => t.key);

  let noTextThemes = [];
  let noInterThemes = [];
  if (state.selectedTheme === "all") {
    const textThemes = new Set(publicCarriedTexts(profile).map((d) => d._theme));
    const interThemes = new Set((profile.interventions || []).map((i) => i._theme));
    noTextThemes = themeUniverse.filter((t) => !textThemes.has(t));
    noInterThemes = themeUniverse.filter((t) => !interThemes.has(t));
  }

  const missingTextCount = state.selectedTheme === "all" ? noTextThemes.length : (textes.length ? 0 : 1);
  const missingInterCount = state.selectedTheme === "all" ? noInterThemes.length : (inters.length ? 0 : 1);
  return `<div class="void-map">
    <div class="void-signal"><span class="void-number">${missingTextCount}</span><strong>thème(s) sans texte retrouvé</strong><small>${noTextThemes.map(themeLabel).join(" / ") || "aucun vide détecté"}</small></div>
    <div class="void-signal"><span class="void-number">${missingInterCount}</span><strong>thème(s) sans parole retrouvée</strong><small>${noInterThemes.map(themeLabel).join(" / ") || "aucun vide détecté"}</small></div>
  </div>`;
}

export function renderInterventions(profile, state) {
  let items = (profile.interventions || []).filter((i) => inTheme(i, state.selectedTheme));
  if (state.interventionsMode === "short") {
    items = items.filter((i) => i.format === "reaction_courte");
  } else if (state.interventionsMode === "long") {
    items = items.filter((i) => i.format === "prise_de_parole_developpee");
  }

  if (!items.length) {
    return `<p class="empty">${state.selectedTheme === "all" ? "Aucune prise de parole trouvée." : "Aucune prise de parole retrouvée sur ce thème dans les données actuellement disponibles."}</p>`;
  }

  const sorted = [...items].sort((a, b) => toDateMs(b.date || b.created_at) - toDateMs(a.date || a.created_at));
  const visible = sorted.slice(0, state.interventionsVisible);

  return `
    <div class="inter-controls">
      <button type="button" class="ghost-btn ${state.interventionsMode === "all" ? "active-choice" : ""}" data-inter-mode="all">Toutes</button>
      <button type="button" class="ghost-btn ${state.interventionsMode === "short" ? "active-choice" : ""}" data-inter-mode="short">Réactions courtes</button>
      <button type="button" class="ghost-btn ${state.interventionsMode === "long" ? "active-choice" : ""}" data-inter-mode="long">Prises de parole longues</button>
    </div>

    <div class="speech-tape">
      ${visible.map((i) => `
        <article class="speech-fragment">
          <div class="editorial-meta">${escapeHtml(formatIsoDate(i.date || i.created_at))} / ${escapeHtml(themeLabel(i._theme))}</div>
          <p class="speech-quote">“${escapeHtml(i.texte ? String(i.texte).slice(0, INTERVENTION_TEXT_PREVIEW_LENGTH) : (i.sujet || "Extrait non disponible"))}${i.texte && String(i.texte).length > INTERVENTION_TEXT_PREVIEW_LENGTH ? "…" : ""}”</p>
          <div>${sourceLinkHtml(i.url_detail || i.url, "↗ archive")}</div>
        </article>
      `).join("")}
    </div>

    ${sorted.length > visible.length ? `<p><button type="button" id="see-more-interventions" class="ghost-btn">Voir plus d’extraits</button></p>` : ""}
  `;
}

export function renderCompareSection(profile, state) {
  const baseTheme = state.selectedTheme === "all" ? state.compareTheme : state.selectedTheme;
  const availableCandidates = state.availableCompareCandidates;

  const activeProfiles = [{ slug: state.currentSlug, profile, meta: state.currentMeta }];
  for (const slug of state.compareSlugs.filter(Boolean)) {
    const p = state.compareProfiles[slug];
    const m = state.candidats.find((c) => c.slug === slug);
    if (p && m) activeProfiles.push({ slug, profile: p, meta: m });
  }

  return `
    <section id="compare" class="panel">
      <h2>Comparer</h2>
      <p class="section-kicker">Thème de comparaison</p>
      <div class="themes-row" aria-label="Thème de comparaison">
        ${THEME_OPTIONS.filter((t) => t.key !== "all").map((t) => `
          <button type="button" class="theme-pill ${baseTheme === t.key ? "active" : ""}" data-compare-theme="${t.key}">${t.icon ? `<span aria-hidden="true">${t.icon}</span>` : ""}<span>${escapeHtml(t.label)}</span></button>
        `).join("")}
      </div>

      <p class="section-kicker">Candidats à comparer (2 max)</p>
      <div class="avatar-carousel" role="group" aria-label="Choisir jusqu'à deux candidats à comparer">
        ${availableCandidates.map((c) => `
          <button type="button" class="avatar-chip avatar-chip--mini ${state.compareSlugs.includes(c.slug) ? "active" : ""}" data-compare-toggle="${escapeHtml(c.slug)}">
            <span class="avatar-chip-circle">${escapeHtml(shortName(c.nom))}</span>
            <span class="avatar-chip-name">${escapeHtml(c.nom.split(/\s+/).slice(-1)[0])}</span>
          </button>
        `).join("")}
      </div>

      <div class="versus-stage">
        ${activeProfiles.map(({ profile: p, meta: m }) => {
          const facts = compareFactsForTheme(p, baseTheme);
          return `
            <article class="versus-person">
              <div class="versus-name">${escapeHtml(p.identite?.nom_complet || m?.nom || p.slug)}</div>
              <div class="editorial-meta">${escapeHtml(themeLabel(baseTheme))}</div>
              <div class="versus-metrics">
                <div class="versus-metric"><b>${facts.votes.length}</b><small>votes</small></div>
                <div class="versus-metric"><b>${facts.textes.length}</b><small>textes</small></div>
                <div class="versus-metric"><b>${facts.interventions.length}</b><small>paroles</small></div>
              </div>
            </article>
          `;
        }).join("")}
      </div>
    </section>
  `;
}

export function renderHome(state) {
  if (state.profileMode === "groups") {
    renderRealGroupHome(state);
    return;
  }
  const root = document.getElementById("candidat-root");
  const available = state.candidats.filter((candidate) => candidate.slug);
  state.currentSlug = "";
  state.currentMeta = null;
  state.currentProfile = null;
  updateActiveAvatarChip();
  updateProfileRailVisibility();
  root.innerHTML = `
    <section class="home-stage">
      <div class="home-manifesto">
        <p class="section-kicker">En clair / Présidentielle 2027</p>
        <h2>Choisir, puis regarder les traces.</h2>
        <p><strong>Les traces parlementaires des candidats.</strong> Une lecture visuelle des mandats, textes, votes et prises de parole issus des données publiques. Aucun candidat n’est mis en avant par défaut.</p>
      </div>
      <div class="home-candidates">
        ${available.map((candidate) => `
          <button type="button" class="home-candidate" data-home-slug="${escapeHtml(candidate.slug)}">
            <strong>${escapeHtml(candidate.nom)}</strong>
            <small>${escapeHtml(candidate.parti || "Affiliation non renseignée")} ↗</small>
          </button>
        `).join("")}
      </div>
    </section>
  `;
  root.querySelectorAll("[data-home-slug]").forEach((button) => {
    button.addEventListener("click", () => selectCandidate(button.dataset.homeSlug));
  });
  updateStickyLayoutVars();
  setDocumentTitle("");
}

export function renderRealGroupHome(state) {
  const root = document.getElementById("candidat-root");
  state.currentRealGroupId = "";
  state.currentRealGroupProfile = null;
  updateActiveAvatarChip();
  updateProfileRailVisibility();
  root.innerHTML = `
    <section class="home-stage">
      <div class="home-manifesto">
        <p class="section-kicker">En clair / groupes parlementaires</p>
        <h2>Voir la composition réelle des groupes.</h2>
        <p><strong>Les groupes parlementaires effectivement constitués</strong> à l'Assemblée nationale et au Sénat, avec leur cohésion de vote, leurs amendements et leur effectif déclaré. La couverture individuelle (profils pivot disponibles localement) reste partielle par rapport à l'effectif réel du groupe — le détail est indiqué sur chaque fiche.</p>
      </div>
      <div class="home-candidates">
        ${REAL_GROUP_PROFILES.map((group) => `
          <button type="button" class="home-candidate" data-home-real-group="${escapeHtml(group.id)}">
            <strong>${escapeHtml(group.label)}</strong>
            <small>${escapeHtml(group.chambre)} ↗</small>
          </button>
        `).join("")}
      </div>
      <div class="home-note party-home-note">Ces fiches décrivent des groupes parlementaires réels (composition, cohésion de vote, amendements). La liste des membres avec profil détaillé reste limitée aux profils pivot disponibles localement : le taux de couverture est affiché sur chaque fiche, ainsi que les avertissements de fraîcheur des données.</div>
    </section>
  `;
  root.querySelectorAll("[data-home-real-group]").forEach((button) => {
    button.addEventListener("click", () => selectRealGroup(button.dataset.homeRealGroup));
  });
  updateStickyLayoutVars();
  setDocumentTitle("");
}

export function renderRealGroupPage(state) {
  const root = document.getElementById("candidat-root");
  const group = state.currentRealGroupProfile;
  if (!group) return;
  const title = group.groupe_nom || group.groupe_sigle || "Groupe parlementaire";
  const periode = group.periode || {};
  const periodeLabel = periode.debut
    ? `${formatIsoDate(periode.debut)} → ${periode.fin ? formatIsoDate(periode.fin) : "aujourd'hui"}${periode.actif ? "" : " (groupe dissous)"}`
    : "période non renseignée";
  const coverage = group.meta?.couverture_roster || {};
  const rosterTotal = Number.isFinite(coverage.roster_total) ? coverage.roster_total : null;
  const profilsDisponibles = Number.isFinite(coverage.profils_disponibles) ? coverage.profils_disponibles : (group.membres || []).length;
  const warnings = group.meta?.warnings || [];
  const members = group.membres || [];
  const tags = (group.tags_thematiques_agreges || [])
    .filter((tag) => tag.tag)
    .sort((a, b) => Number(b.nb_membres_porteurs || 0) - Number(a.nb_membres_porteurs || 0) || Number(b.poids_relatif || 0) - Number(a.poids_relatif || 0))
    .slice(0, 30);
  const maxTagMembers = Math.max(...tags.map((tag) => Number(tag.nb_membres_porteurs || 0)), 1);
  const cohesionVotes = (group.cohesion_votes || [])
    .slice()
    .sort((a, b) => String(b.date || "").localeCompare(String(a.date || "")));
  const visibleCount = Math.min(state.realGroupCohesionVisible, cohesionVotes.length);
  const visibleVotes = cohesionVotes.slice(0, visibleCount);
  const amendements = group.amendements_agreges || {};
  const amendementsDepute = amendements.par_type_deposant?.depute || {};

  root.innerHTML = `
    <article class="party-profile">
      <header class="party-hero">
        <p class="section-kicker">Groupe parlementaire / ${escapeHtml(group.chambre || "")}${group.legislature ? ` · législature ${escapeHtml(String(group.legislature))}` : ""} · ${escapeHtml(periodeLabel)}</p>
        <h2>${escapeHtml(title)}${group.groupe_sigle && group.groupe_sigle !== title ? ` (${escapeHtml(group.groupe_sigle)})` : ""}</h2>
      </header>
      <div class="party-coverage">
        PÉRIMÈTRE : ${profilsDisponibles} profil(s) pivot disponible(s) localement${rosterTotal !== null ? ` sur ${rosterTotal} membre(s) réel(s) du groupe` : ""}. Les thèmes et la liste de membres ci-dessous ne couvrent que ces profils ; la cohésion de vote et les amendements portent sur l'ensemble du groupe tel que déclaré par les sources.
        ${warnings.length ? `<br>Avertissement : ${warnings.map((w) => escapeHtml(w)).join(" ")}` : ""}
      </div>
      <section class="party-kpis" aria-label="Indicateurs du groupe">
        <div class="party-kpi"><b>${group.effectif?.actuel ?? "N/D"}</b><span>Effectif actuel déclaré</span></div>
        <div class="party-kpi"><b>${rosterTotal ?? "N/D"}</b><span>Membres réels du roster</span></div>
        <div class="party-kpi"><b>${cohesionVotes.length}</b><span>Scrutins de cohésion couverts</span></div>
        <div class="party-kpi"><b>${amendementsDepute.nb_amendements ?? 0}</b><span>Amendements déposés par des député(e)s</span></div>
      </section>
      <section class="party-section">
        <p class="section-kicker">Cohésion de vote du groupe</p>
        <h2>Scrutins</h2>
        ${cohesionVotes.length ? `
          <div class="party-vote-grid">
            ${visibleVotes.map((vote) => {
              const { label, cls } = voteLabelAndClass(vote.position_majoritaire);
              return `
                <div class="party-vote">
                  <span class="party-vote-position party-vote-position--${cls}">${escapeHtml(label)}</span>
                  <b>${escapeHtml(simplifyTitle(vote.texte))}</b>
                  <small>${formatIsoDate(vote.date)} · cohérence ${formatPercentage(Number(vote.taux_coherence))} · participation ${formatPercentage(Number(vote.taux_participation))}${vote.quorum_atteint === false ? " · quorum non atteint" : ""}</small>
                </div>
              `;
            }).join("")}
          </div>
          ${cohesionVotes.length > visibleCount ? `<p class="small"><button type="button" data-expand-cohesion>Voir plus de scrutins (${cohesionVotes.length - visibleCount} restants)</button></p>` : ""}
        ` : `<p class="empty">Aucun scrutin de cohésion disponible pour ce groupe.</p>`}
      </section>
      <section class="party-section">
        <p class="section-kicker">Amendements déposés au nom du groupe</p>
        <h2>Activité législative</h2>
        <p>${amendementsDepute.nb_amendements ?? 0} amendement(s) déposé(s) par des député(e)s du groupe, ${amendementsDepute.nb_adoptes ?? 0} adopté(s) (taux d'adoption ${formatPercentage(Number(amendementsDepute.taux_adoption))}).</p>
        <p class="small">Total tous déposants confondus (gouvernement, commissions, inconnu...) : ${amendements.nb_amendements ?? 0} amendement(s). Ne pas comparer directement ce total aux chiffres par député : les catégories de déposants ne sont pas homogènes.</p>
      </section>
      <section class="party-section">
        <p class="section-kicker">Mots-clés partagés entre les membres couverts</p>
        <h2>Empreinte thématique</h2>
        ${tags.length ? `<div class="party-tags">${tags.map((tag) => `
          <span class="party-tag" style="--weight:${Number(tag.nb_membres_porteurs || 0) / maxTagMembers}"><b>${escapeHtml(tag.tag)}</b><small>${tag.nb_membres_porteurs} profil(s) porteur(s)</small></span>
        `).join("")}</div>` : `<p class="empty">Aucun thème agrégé disponible.</p>`}
      </section>
      <section class="party-section">
        <p class="section-kicker">Profils individuels disponibles</p>
        <h2>Membres couverts</h2>
        ${members.length ? `<div class="party-members">${members.map((member) => `
          <div class="party-member"><strong>${escapeHtml(member.nom)}</strong><br><small>${member.actif ? "Membre actif" : `Membre du ${formatIsoDate(member.debut_dans_groupe)} au ${formatIsoDate(member.fin_dans_groupe)}`}</small></div>
        `).join("")}</div>` : `<p class="empty">Aucun profil pivot local disponible pour ce groupe.</p>`}
        <div class="party-sources">Généré le ${escapeHtml(formatIsoDate(group.meta?.genere_le))} · ${group.sources?.length || 0} source(s) déclarée(s) · <a href="methodologie.html" target="_blank" rel="noopener">Voir la méthode ↗</a></div>
      </section>
    </article>
  `;
  root.querySelectorAll("[data-expand-cohesion]").forEach((button) => {
    button.addEventListener("click", () => {
      state.realGroupCohesionVisible += 20;
      renderRealGroupPage(state);
    });
  });
  updateStickyLayoutVars();
  setDocumentTitle(title);
}

export function renderApercu(profile, state) {
  const kpis = expressSummaryData(profile);
  const theme = state.apercuFilter === "all" ? null : state.apercuFilter;
  const votes = (profile.votes || []).filter((v) => !theme || v._theme === theme);
  const textes = publicCarriedTexts(profile).filter((t) => !theme || t._theme === theme);
  const interventions = (profile.interventions || []).filter((i) => !theme || i._theme === theme);
  const views = [
    { key: "synthese", label: "Synthèse" },
    { key: "votes", label: "Votes" },
    { key: "textes", label: "Textes" },
    { key: "paroles", label: "Paroles" },
  ];
  const filterButtons = [{ key: "all", label: "Tous les thèmes" }, ...Object.entries(THEME_COLORS).map(([key]) => ({
    key,
    label: themeLabel(key),
  }))];

  return `
    <section class="panel apercu-panel">
      <h2>Aperçu</h2>
      <div class="apercu-view-tabs" role="tablist" aria-label="Vue Aperçu">
        ${views.map((v) => `
          <button type="button" class="apercu-view-tab ${state.apercuView === v.key ? "active" : ""}" data-apercu-view="${escapeHtml(v.key)}" role="tab" aria-selected="${state.apercuView === v.key}">
            ${escapeHtml(v.label)}
          </button>
        `).join("")}
      </div>
      <div class="apercu-filter-row" role="group" aria-label="Filtrer par thème">
        ${filterButtons.map((f) => `
          <button type="button" class="apercu-filter-btn ${state.apercuFilter === f.key ? "active" : ""}" data-apercu-filter="${escapeHtml(f.key)}">
            ${escapeHtml(f.label)}
          </button>
        `).join("")}
      </div>
      ${state.apercuView === "synthese" ? `
        <div class="apercu-kpi-grid">
          ${kpis.map((kpi) => `
            <div class="apercu-kpi-card">
              <p class="apercu-kpi-question">${escapeHtml(kpi.question)}</p>
              <p class="apercu-kpi-value"><b>${escapeHtml(kpi.value)}</b></p>
              <p class="apercu-kpi-note">${escapeHtml(kpi.note)}</p>
            </div>
          `).join("")}
        </div>
      ` : ""}
      ${state.apercuView === "votes" ? `
        <p class="apercu-count">${votes.length} vote(s) documenté(s)${theme ? ` — ${escapeHtml(themeLabel(theme))}` : ""}</p>
      ` : ""}
      ${state.apercuView === "textes" ? `
        <p class="apercu-count">${textes.length} texte(s) porté(s)${theme ? ` — ${escapeHtml(themeLabel(theme))}` : ""}</p>
      ` : ""}
      ${state.apercuView === "paroles" ? `
        <p class="apercu-count">${interventions.length} intervention(s)${theme ? ` — ${escapeHtml(themeLabel(theme))}` : ""}</p>
      ` : ""}
    </section>
  `;
}

export function renderPage(state) {
  const root = document.getElementById("candidat-root");
  const profile = state.currentProfile;
  const meta = state.currentMeta;

  if (!profile || !meta) {
    root.innerHTML = "";
    return;
  }

  root.innerHTML = `
    ${renderHeader(meta, profile, state)}

    <section class="theme-dock">
      <p class="section-kicker">Filtrer par thème</p>
      ${renderThemePills(state)}
    </section>

    ${renderPanelIndicator(state)}
    <div class="swipe-deck" id="swipe-deck">
      <div class="swipe-panel ${state.activePanelIndex === 0 ? "active" : ""}">
        ${renderApercu(profile, state)}
      </div>

      <div class="swipe-panel ${state.activePanelIndex === 1 ? "active" : ""}">
        <section class="panel">
          <h2>Mandats documentés <span class="source-ref">(${(profile.pivot_mandats || []).length})</span></h2>
          ${renderMinisterialIncompatibilities(profile)}
          <div id="mandats">${renderMandates(profile, state)}</div>
        </section>
      </div>

      <div class="swipe-panel ${state.activePanelIndex === 2 ? "active" : ""}">
        <section class="panel">
          <section class="legislative-layout">
            <div class="legislative-left-column">
              <h2>Textes portés & amendements</h2>
              ${renderTextesKpi(profile, state)}
            </div>
            <div class="legislative-right-column">
              <div class="legislative-scroll-frame">
                ${renderLegislativeDetails(profile, state)}
              </div>
            </div>
          </section>
        </section>
      </div>

      <div class="swipe-panel ${state.activePanelIndex === 3 ? "active" : ""}">
        <section class="panel">
          <h2>Votes enregistrés <span class="source-ref">(${(profile.votes || []).length})</span></h2>
          <div id="votes">${renderVotes(profile, state)}</div>
        </section>
      </div>

      <div class="swipe-panel ${state.activePanelIndex === 4 ? "active" : ""}">
        <section class="panel">
          <h2>Angles morts documentaires</h2>
          <div id="absences">${renderAbsences(profile, state)}</div>
        </section>
      </div>

      <div class="swipe-panel ${state.activePanelIndex === 5 ? "active" : ""}">
        <section class="panel">
          <h2>Prises de parole <span class="source-ref">(${(profile.interventions || []).length})</span></h2>
          <div id="interventions">${renderInterventions(profile, state)}</div>
        </section>
      </div>

      <div class="swipe-panel ${state.activePanelIndex === 6 ? "active" : ""}">${renderCompareSection(profile, state)}</div>
    </div>
    <p class="swipe-hint">← Glissez ou touchez les icônes pour changer de section →</p>
    ${renderExpressSummary(profile, state)}
  `;

  setDocumentTitle(profile.identite?.nom_complet || meta.nom);
  bindRenderedEvents();
  updateStickyLayoutVars();
}

export function expressSummaryData(profile) {
  const tenure = computeMandateTenure(profile);
  const responsibilities = computeResponsibilitiesSummary(profile);
  const voteProfile = computeFinalTextVoteProfile(profile);
  const pourPct = voteProfile.totalPositions
    ? Math.round((voteProfile.counts.pour / voteProfile.totalPositions) * 100)
    : null;
  const themeCounts = new Map();
  for (const item of [...(profile.votes || []), ...publicCarriedTexts(profile), ...(profile.interventions || [])]) {
    themeCounts.set(item._theme, (themeCounts.get(item._theme) || 0) + 1);
  }
  const dominant = [...themeCounts.entries()].sort((a, b) => b[1] - a[1])[0];
  return [
    {
      question: "Depuis combien de temps exerce-t-il un mandat parlementaire ?",
      value: tenure ? `${tenure.annees} ans` : "N/D",
      note: "Durée du mandat, pas mesure de l'implication.",
    },
    {
      question: "Quelles responsabilités institutionnelles a-t-il occupées ?",
      value: String(responsibilities.distinctCount),
      note: "Responsabilités distinctes, hors réaffectations administratives.",
    },
    {
      question: "Comment vote-t-il sur les textes entiers ?",
      value: pourPct === null ? "N/D" : `${pourPct} %`,
      note: voteProfile.totalPositions ? `${voteProfile.totalPositions} positions documentées, scrutins publics ordinaires et solennels.` : "Aucune position finale retrouvée.",
    },
    {
      question: "Quel thème apparaît le plus souvent dans ses traces ?",
      value: dominant ? themeLabel(dominant[0]) : "N/D",
      note: dominant ? `${dominant[1]} traces classées. Une fréquence documentaire, pas une priorité déclarée.` : "Thème non déterminé.",
    },
  ];
}

export function renderExpressSummary(profile, state) {
  return `
    <div class="express-summary" role="dialog" aria-modal="true" aria-label="Résumé express" aria-hidden="true">
      <button type="button" class="express-summary-close" aria-label="Fermer">×</button>
      <div class="express-summary-scenes">
        ${expressSummaryData(profile).map((item, index) => `
          <section class="express-summary-scene ${index === state.expressIndex ? "active" : ""}">
            <h2 class="express-summary-question">${escapeHtml(item.question)}</h2>
            <div class="express-summary-answer"><b>${escapeHtml(item.value)}</b><span>${escapeHtml(item.note)}</span></div>
          </section>
        `).join("")}
      </div>
      <div class="express-summary-progress"><i style="width:${(state.expressIndex + 1) * 25}%"></i></div>
      <nav class="express-summary-nav" aria-label="Navigation du résumé">
        <button type="button" data-express-dir="-1" aria-label="Précédent">←</button>
        <button type="button" data-express-dir="1" aria-label="Suivant">→</button>
      </nav>
    </div>
  `;
}

export function setExpressScene(index, state) {
  state.expressIndex = (index + 4) % 4;
  document.querySelectorAll(".express-summary-scene").forEach((scene, sceneIndex) => {
    scene.classList.toggle("active", sceneIndex === state.expressIndex);
  });
  const progress = document.querySelector(".express-summary-progress i");
  if (progress) progress.style.width = `${(state.expressIndex + 1) * 25}%`;
}

export function openExpressSummary(state) {
  state.expressIndex = 0;
  setExpressScene(0);
  const summary = document.querySelector(".express-summary");
  summary?.classList.add("open");
  summary?.setAttribute("aria-hidden", "false");
  document.body.classList.add("express-open");
  document.querySelector(".express-summary-close")?.focus();
}

export function closeExpressSummary() {
  const summary = document.querySelector(".express-summary");
  summary?.classList.remove("open");
  summary?.setAttribute("aria-hidden", "true");
  document.body.classList.remove("express-open");
  document.querySelector(".express-launch")?.focus();
}

export function renderPanelIndicator(state) {
  return `
    <div class="panel-indicator" role="tablist" aria-label="Sections du dossier">
      ${PANEL_ORDER.map((id, i) => `
        <button type="button" class="panel-dot ${state.activePanelIndex === i ? "active" : ""}" data-panel-index="${i}" title="${escapeHtml(PANEL_META[id].label)}" aria-label="${escapeHtml(PANEL_META[id].label)}">
          <span aria-hidden="true">${PANEL_META[id].icon}</span>
          <small>${escapeHtml(PANEL_META[id].label)}</small>
        </button>
      `).join("")}
    </div>
  `;
}

export function toggleKpiFlip(el, state) {
  const id = el.dataset.kpi;
  const flipped = el.classList.toggle("flipped");
  el.setAttribute("aria-pressed", String(flipped));
  if (flipped) state.flippedKpis.add(id); else state.flippedKpis.delete(id);
}

export function setActivePanel(index, { scroll = false } = {}, state) {
  if (index < 0 || index >= PANEL_ORDER.length) return;
  state.activePanelIndex = index;
  document.querySelectorAll(".panel-dot").forEach((dot, i) => {
    dot.classList.toggle("active", i === index);
  });
  document.querySelectorAll(".swipe-panel").forEach((panel, i) => {
    panel.classList.toggle("active", i === index);
  });
  if (scroll) document.getElementById("swipe-deck")?.scrollIntoView({ behavior: "smooth", block: "start" });
}

export function scrollToPanel(id, state) {
  setActivePanel(PANEL_ORDER.indexOf(id), { scroll: true }, state);
}
