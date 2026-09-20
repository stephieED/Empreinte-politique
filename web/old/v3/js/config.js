export const CANDIDATS_URL = "../../raw_data/candidats.json";
export const PROFILE_URL = (slug) => `../../raw_data/profiles/${slug}.json`;
export const PIVOT_PROFILE_URL = (slug) => `../../pivot_data/profiles/${slug}.pivot.json`;
export const REAL_GROUP_PROFILES = [
  { id: "AN-REN-16", label: "Renaissance", chambre: "Assemblée nationale", fichier: "groupe-AN-REN-16.json" },
  { id: "AN-SOC-16", label: "Socialistes et apparentés", chambre: "Assemblée nationale", fichier: "groupe-AN-SOC-16.json" },
  { id: "AN-RN-16", label: "Rassemblement National", chambre: "Assemblée nationale", fichier: "groupe-AN-RN-16.json" },
  { id: "AN-LFI-16", label: "La France insoumise - NUPES", chambre: "Assemblée nationale", fichier: "groupe-AN-LFI-16.json" },
  { id: "AN-LR-16", label: "Les Républicains", chambre: "Assemblée nationale", fichier: "groupe-AN-LR-16.json" },
  { id: "Senat-LR", label: "Les Républicains", chambre: "Sénat", fichier: "groupe-Senat-LR.json" },
  { id: "Senat-SER", label: "Socialiste, Écologiste et Républicain", chambre: "Sénat", fichier: "groupe-Senat-SER.json" },
];
export const REAL_GROUP_PROFILE_URL = (fichier) => `../../pivot_data/groupes/${fichier}`;
export const UI_ICONS = {
  list: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 5h9"/><path d="M7 10h9"/><path d="M7 15h9"/><circle cx="4" cy="5" r="1"/><circle cx="4" cy="10" r="1"/><circle cx="4" cy="15" r="1"/></svg>',
  stethoscope: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 3v5a3 3 0 0 0 6 0V3"/><path d="M8 13v1a3 3 0 0 0 6 0v-1"/><path d="M14 13a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z"/><path d="M5 3H3"/><path d="M11 3H9"/></svg>',
  leaf: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M16 4c-5 0-9 2.5-11 8 4 2 8 1 11-2 2-2 2-4 0-6Z"/><path d="M7 11c1.5-.5 3.5-2 5-4"/></svg>',
  wallet: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 6.5A1.5 1.5 0 0 1 4.5 5h9A1.5 1.5 0 0 1 15 6.5v7A1.5 1.5 0 0 1 13.5 15h-9A1.5 1.5 0 0 1 3 13.5v-7Z"/><path d="M15 8h2v4h-2a2 2 0 1 1 0-4Z"/></svg>',
  graduation: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m2 7.5 8-4 8 4-8 4-8-4Z"/><path d="M5 9.5V13c0 1.5 2.2 2.5 5 2.5s5-1 5-2.5V9.5"/><path d="M18 7.5V13"/></svg>',
  shield: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 3 4.5 5v4.5c0 3.3 2.3 5.8 5.5 7 3.2-1.2 5.5-3.7 5.5-7V5L10 3Z"/></svg>',
  building: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 17h14"/><path d="M5 17V8l5-3 5 3v9"/><path d="M8 11h.01"/><path d="M12 11h.01"/><path d="M8 14h.01"/><path d="M12 14h.01"/></svg>',
  globe: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="10" cy="10" r="7"/><path d="M3.5 10h13"/><path d="M10 3c2 2 3 4.3 3 7s-1 5-3 7c-2-2-3-4.3-3-7s1-5 3-7Z"/></svg>',
  handshake: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7.5 6 10 8.2a1.8 1.8 0 0 0 2.4 0L14 7"/><path d="m3 8 3-3 3.2 2.7"/><path d="m17 8-3-3-3.2 2.7"/><path d="m6.5 10.5 2 2a1.2 1.2 0 0 0 1.7 0l.2-.2"/><path d="m8.8 12.6 1.4 1.4a1.2 1.2 0 0 0 1.7 0l.3-.3"/><path d="m11 13.8.8.8a1.2 1.2 0 0 0 1.7 0L16 12"/></svg>',
  briefcase: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="6" width="14" height="10" rx="1"/><path d="M7 6V4.8A1.8 1.8 0 0 1 8.8 3h2.4A1.8 1.8 0 0 1 13 4.8V6"/><path d="M3 10h14"/></svg>',
  fileText: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 3.5h5l3 3V16a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1v-11a1 1 0 0 1 1-1Z"/><path d="M11 3.5V7h3"/><path d="M7 10h6"/><path d="M7 13h6"/></svg>',
  ballot: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 7h12v10H4z"/><path d="m7 4 3 3 4-4"/></svg>',
  database: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><ellipse cx="10" cy="5" rx="6" ry="2.5"/><path d="M4 5v5c0 1.4 2.7 2.5 6 2.5s6-1.1 6-2.5V5"/><path d="M4 10v5c0 1.4 2.7 2.5 6 2.5s6-1.1 6-2.5v-5"/></svg>',
  messages: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 14H3.5A1.5 1.5 0 0 1 2 12.5v-6A1.5 1.5 0 0 1 3.5 5h8A1.5 1.5 0 0 1 13 6.5V8"/><path d="M6 8h4"/><path d="M6 11h3"/><path d="M9 10.5A1.5 1.5 0 0 1 10.5 9H16a1.5 1.5 0 0 1 1.5 1.5V14a1.5 1.5 0 0 1-1.5 1.5h-3.8L9 18v-3.5Z"/></svg>',
  scale: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 4v12"/><path d="M5 6h10"/><path d="m5 6-2.5 4h5L5 6Z"/><path d="m15 6-2.5 4h5L15 6Z"/><path d="M7 17h6"/></svg>',
};
export const THEME_OPTIONS = [
  { key: "all", label: "Tous les thèmes", icon: UI_ICONS.list },
  { key: "sante", label: "Santé", icon: UI_ICONS.stethoscope },
  { key: "environnement", label: "Environnement", icon: UI_ICONS.leaf },
  { key: "economie", label: "Économie", icon: UI_ICONS.wallet },
  { key: "education", label: "Éducation", icon: UI_ICONS.graduation },
  { key: "securite", label: "Sécurité", icon: UI_ICONS.shield },
  { key: "institutions", label: "Institutions", icon: UI_ICONS.building },
  { key: "europe_international", label: "Europe / International", icon: UI_ICONS.globe },
  { key: "social", label: "Social", icon: UI_ICONS.handshake },
];

export const THEME_RULES = {
  sante: ["santé", "hopital", "hôpital", "malad", "soin", "medec", "médec", "cancer"],
  environnement: ["climat", "environ", "biodivers", "energie", "énergie", "carbone", "pollution", "écologi"],
  economie: ["budget", "fiscal", "impôt", "impot", "entreprise", "travail", "emploi", "financ"],
  education: ["éduc", "ecole", "école", "universit", "apprentiss", "scolair"],
  securite: ["sécurit", "police", "défense", "defense", "terror", "justice pénale", "violence"],
  institutions: ["constitution", "assemblée", "assemblee", "sénat", "senat", "scrutin", "loi organique", "collectivités"],
  europe_international: ["europe", "union européenne", "ue", "international", "onu", "otan", "étrang", "maghreb", "afrique"],
  social: ["retraite", "logement", "social", "pauvret", "solidarit", "sécurité sociale", "égalité", "salaire"],
};
export const DEFAULT_THEME = "institutions";
export const MAX_COMPARE_CANDIDATES = 2;
export const TITLE_TRUNCATE_LENGTH = 120;
// On garde 3 caractères de marge pour ajouter des points de suspension sans allonger visuellement la ligne.
export const TITLE_TRUNCATE_SLICE = TITLE_TRUNCATE_LENGTH - 3;
export const INTERVENTION_TEXT_PREVIEW_LENGTH = 200;
export const NON_VOTING_PATTERN = /non[ _-]?vot/;
export const DEBATED_TEXT_STAGES = new Set(["examine_commission", "inscrit_ordre_jour", "discute_seance", "adopte", "promulgue"]);
export const TEXT_ROLE_LABELS = { auteur: "auteur", rapporteur: "rapporteur", "co-rapporteur": "co-rapporteur" };
export const TEXT_STAGE_LABELS = {
  examine_commission: "examiné en commission",
  inscrit_ordre_jour: "inscrit à l’ordre du jour",
  discute_seance: "discuté en séance",
  adopte: "adopté",
  promulgue: "promulgué",
};
export const AMENDMENT_OUTCOMES = [
  ["adopté", "Adoptés"], ["rejeté", "Rejetés"], ["retiré", "Retirés"],
  ["tombé", "Tombés"], ["irrecevable", "Irrecevables"], ["non_soutenu", "Non soutenus"],
];
export const TEXT_STAGE_COLORS = {
  examine_commission: "#B0C4DE",
  inscrit_ordre_jour: "#6A9EC7",
  discute_seance:     "#2E86C1",
  adopte:             "#1E8449",
  promulgue:          "#145A32",
};
export const TEXT_STAGES_ORDER = ["examine_commission", "inscrit_ordre_jour", "discute_seance", "adopte", "promulgue"];
export const THEME_COLORS = {
  sante: "#0077B6",
  environnement: "#2D6A4F",
  economie: "#D4A017",
  education: "#4895EF",
  securite: "#9B2226",
  institutions: "#6C757D",
  europe_international: "#003566",
  social: "#7B2D8B",
};

// Ordre des panneaux du carrousel glissant (remplace la pile d'accordéons)
export const PANEL_ORDER = ["apercu", "mandats", "textes", "votes", "absences", "interventions", "compare"];
export const PANEL_ICON_ATTRS = 'viewBox="0 0 20 20" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"';
export const PANEL_META = {
  apercu: { label: "Aperçu", icon: UI_ICONS.list },
  mandats: { label: "Mandats", icon: UI_ICONS.briefcase },
  textes: { label: "Textes", icon: UI_ICONS.fileText },
  votes: { label: "Votes", icon: UI_ICONS.ballot },
  absences: { label: "Données", icon: UI_ICONS.database },
  interventions: { label: "Paroles", icon: UI_ICONS.messages },
  compare: { label: "Comparer", icon: UI_ICONS.scale },
};

// Pictogrammes des cartes KPI (SVG inline, sans dépendance externe)
export const KPI_ICONS = {
  anciennete: '<svg viewBox="0 0 20 20" width="26" height="26" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 3h10M5 17h10M6 3c0 4 3 5 4 6 1-1 4-2 4-6M6 17c0-4 3-5 4-6 1 1 4 2 4 6"/></svg>',
  responsabilites: '<svg viewBox="0 0 20 20" width="26" height="26" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 17h14M4 17V9l6-4 6 4v8M8 17v-5h4v5"/></svg>',
  vote: '<svg viewBox="0 0 20 20" width="26" height="26" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8h14v9H3z"/><path d="M7 8V5a3 3 0 0 1 6 0v3M10 11v3"/></svg>',
  theme: '<svg viewBox="0 0 20 20" width="26" height="26" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h6l6 6-6 6-6-6z"/><circle cx="7" cy="7" r="1" fill="currentColor" stroke="none"/></svg>',
};

// --- KPI de synthèse (voir analyse KPI : ancienneté, responsabilités, profil de vote, thème dominant) ---

export const MS_PER_YEAR = 365.25 * 24 * 3600 * 1000;
export const RESPONSIBILITY_CATEGORIES = ["commission", "extra_parlementaire", "groupe_amitie"];
export const ROLE_PRIORITY = [
  "président", "présidente", "co-président", "co-présidente",
  "vice-président", "vice-présidente", "rapporteur", "co-rapporteur", "rapporteure",
];
export const CATEGORIE_LABELS_FR = {
  mandat_electif: "Mandat électif",
  commission: "Commission / mission",
  extra_parlementaire: "Engagement extra-parlementaire",
  groupe_amitie: "Groupe d'amitié",
  groupe_politique: "Groupe politique",
  autre: "Autre responsabilité",
};
export const MANDATE_FILTERS = {
  all: () => true,
  elective: (mandate) => mandate.categorie === "mandat_electif",
  responsibilities: (mandate) => !["mandat_electif", "groupe_politique", "groupe_amitie"].includes(mandate.categorie),
  groups: (mandate) => ["groupe_politique", "groupe_amitie"].includes(mandate.categorie),
};

// KPI 1 — Ancienneté et statut du mandat : ne mesure pas l'implication, seulement la durée.
export const ENSEMBLE_VOTE_PATTERN = /^l[’']ensemble\s+(?:du|de la)\s+(.*?)\s*(?:\(([^)]*)\))?\.?$/i;
export const READING_STAGE_RANK = {
  "lecture définitive": 4,
  "texte de la commission mixte paritaire": 3,
  "texte de la commission paritaire": 3,
  "nouvelle lecture": 2,
  "deuxième lecture": 2,
  "première lecture": 1,
  "premiere lecture": 1,
};
