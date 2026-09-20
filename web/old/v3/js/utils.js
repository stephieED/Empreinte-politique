// Imports from config
import { TITLE_TRUNCATE_LENGTH, TITLE_TRUNCATE_SLICE, NON_VOTING_PATTERN, THEME_RULES, DEFAULT_THEME, THEME_OPTIONS, TEXT_ROLE_LABELS, DEBATED_TEXT_STAGES, READING_STAGE_RANK, ENSEMBLE_VOTE_PATTERN, INTERVENTION_TEXT_PREVIEW_LENGTH } from './config.js';

export function setDocumentTitle(label) {
  document.title = label ? `Empreinte politique — ${label}` : "Empreinte politique — En clair";
}

export function escapeHtml(str) {
  return String(str ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[c]);
}

export function toDateMs(value) {
  if (!value) return 0;
  const t = Date.parse(value);
  return Number.isNaN(t) ? 0 : t;
}

export function formatIsoDate(value) {
  if (!value) return "non renseignée";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString("fr-FR");
}

export function shortName(name) {
  if (!name) return "?";
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join("");
}

export function simplifyTitle(text) {
  const raw = String(text || "").trim();
  if (!raw) return "Intitulé non renseigné";
  const cleaned = raw.replace(/^(la|le|les)\s+/i, "");
  return cleaned.length > TITLE_TRUNCATE_LENGTH ? `${cleaned.slice(0, TITLE_TRUNCATE_SLICE).trim()}…` : cleaned;
}

export function normalizedText(...parts) {
  return parts
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

export function detectThemeFromText(text) {
  const t = String(text || "").toLowerCase();
  for (const [theme, needles] of Object.entries(THEME_RULES)) {
    if (needles.some((needle) => t.includes(needle))) return theme;
  }
  return DEFAULT_THEME;
}

export function themeLabel(themeKey) {
  return THEME_OPTIONS.find((t) => t.key === themeKey)?.label || "Institutions";
}

export function voteLabelAndClass(position) {
  const p = String(position || "").toLowerCase();
  if (p.includes("pour")) return { label: "Pour", cls: "pour" };
  if (p.includes("contre")) return { label: "Contre", cls: "contre" };
  if (p.includes("abst")) return { label: "Abstention", cls: "abstention" };
  if (NON_VOTING_PATTERN.test(p) || p.includes("absent")) {
    return { label: "Absent / non votant", cls: "absent" };
  }
  return { label: "Position non précisée", cls: "absent" };
}

export function readingStageRank(stage) {
  if (!stage) return 1;
  return READING_STAGE_RANK[stage.trim().toLowerCase()] ?? 1;
}

export function parseEnsembleVote(titre) {
  const m = ENSEMBLE_VOTE_PATTERN.exec((titre || "").trim());
  if (!m) return null;
  return { key: m[1].trim().toLowerCase(), stage: m[2] || null, rank: readingStageRank(m[2]) };
}

export function withTheme(profile) {
  const votes = (profile.votes || []).map((v) => ({
    ...v,
    _theme: detectThemeFromText(normalizedText(v.titre, v.position)),
  }));
  const textesPortes = (profile.textes_portes || []).map((d) => ({
    ...d,
    _theme: detectThemeFromText(normalizedText(d.titre)),
  }));
  const interventions = (profile.interventions || []).map((i) => ({
    ...i,
    _theme: i.theme_officiel
      ? detectThemeFromText(normalizedText(i.theme_officiel))
      : detectThemeFromText(normalizedText(i.sujet, i.texte, ...(i.mots_cles || []))),
  }));
  const amendements = (profile.amendements || []).map((a) => ({
    ...a,
    _theme: detectThemeFromText(normalizedText(a.titre, a.objet)),
  }));
  return { ...profile, votes, textes_portes: textesPortes, interventions, amendements };
}

export function inTheme(item, selectedTheme) {
  return selectedTheme === "all" ? true : item._theme === selectedTheme;
}

export function isPublicCarriedText(texte) {
  return Boolean(TEXT_ROLE_LABELS[texte.role] && DEBATED_TEXT_STAGES.has(texte.stade_procedural));
}

export function publicCarriedTexts(profile) {
  return (profile.textes_portes || []).filter((texte) => isPublicCarriedText(texte));
}

export function textExclusionReasons(texte) {
  const reasons = [];
  if (!TEXT_ROLE_LABELS[texte.role]) reasons.push("role factuel non renseigne");
  if (!DEBATED_TEXT_STAGES.has(texte.stade_procedural)) reasons.push("stade non retenu pour publication");
  return reasons.length ? reasons : ["hors criteres publics"];
}

export function sourceLinkHtml(url, label = "Source officielle") {
  if (!url) return `<span class="small">${escapeHtml(label)} indisponible</span>`;
  return `<a class="link" href="${escapeHtml(url)}" target="_blank" rel="noopener">${escapeHtml(label)}</a>`;
}

export function voteSourceUrl(profile, vote) {
  const directUrl = vote.url_source || vote.url || vote.source;
  if (/^https?:\/\//i.test(directUrl || "")) return { url: directUrl, direct: true };
  const legislature = String(profile.votes_source || "").match(/l[ée]gislature\s*(\d+)/i)?.[1]
    || (profile.textes_portes || []).find((item) => item.legislature)?.legislature;
  if (vote.numero_scrutin && legislature) {
    return {
      url: `https://www.assemblee-nationale.fr/dyn/${encodeURIComponent(legislature)}/scrutins/${encodeURIComponent(vote.numero_scrutin)}`,
      direct: true,
    };
  }
  const fallback = profile.synthese_activite?.url_an_ou_senat || profile.source;
  return /^https?:\/\//i.test(fallback || "") ? { url: fallback, direct: false } : null;
}

export function compareFactsForTheme(profile, theme) {
  const votes = (profile.votes || []).filter((v) => v._theme === theme);
  const textes = publicCarriedTexts(profile).filter((d) => d._theme === theme);
  const interventions = (profile.interventions || []).filter((i) => i._theme === theme);
  return { votes, textes, interventions };
}

export function average(values) {
  const valid = values
    .filter((value) => value !== null && value !== undefined && value !== "" && Number.isFinite(Number(value)))
    .map(Number);
  return valid.length ? valid.reduce((sum, value) => sum + value, 0) / valid.length : null;
}

export function formatPercentage(value) {
  return !Number.isFinite(value) ? "N/D" : `${Math.round(value * 100)} %`;
}

export function candidateLastName(nom) {
  const parts = String(nom || "").split(/\s+/).filter(Boolean);
  return parts.length ? parts[parts.length - 1] : "?";
}
