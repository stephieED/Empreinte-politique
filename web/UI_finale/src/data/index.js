import { INSTITUTION_PARLEMENT, sigleDuSiege } from '../utils/profilCandidat';
import { etiquettesThematiques } from '../utils/groupe';
import { filtrerProfil, motsDuFiltre, periodeCumulee } from '../utils/filtreIntitule';
import { porteeCommune } from '../utils/votesParPeriode';
import { titreDuTexteVote } from '../utils/lecture';
import { cheminDuPoint } from '../utils/parolesParPeriode';
import {
  buildCandidateView,
  buildGovernmentView,
  legislatureDeAmendementId,
} from './pivotAdapter';

/* Les adresses par défaut vivent dans leur propre module, sans dépendance :
 * `scripts/pages-par-adresse.mjs` les lit au build pour écrire les pages de
 * redirection (#969). */
export { DEFAULT_CANDIDATE_ID, DEFAULT_GROUP_ID, DEFAULT_GOVERNMENT_ID } from './adressesParDefaut.js';

let manifestPromise = null;
let scrutinsPromise = null;
let couverturePromise = null;
const amendementsPromises = new Map();

function loadManifest() {
  if (!manifestPromise) {
    manifestPromise = fetch('/data/manifest.json').then((r) => {
      if (!r.ok) throw new Error(`manifest.json : HTTP ${r.status}`);
      return r.json();
    });
  }
  return manifestPromise;
}

/**
 * Index des scrutins (#432), chargé une fois pour toute la session.
 *
 * Depuis la normalisation des votes, un profil ne porte plus que le mapping
 * `{ scrutin_id, position }` : le méta du scrutin — identique pour ses ~150
 * votants — vit une seule fois ici. Le fichier pèse ~8 Mo là où les profils
 * pesaient 180 Mo de votes, et il est **partagé** entre profils individuels et
 * profils de groupe (les 4 104 scrutins des groupes sont inclus dans les 17 422
 * des profils : zéro scrutin propre aux groupes).
 *
 * Mémoïsé, et non bloquant : un échec de chargement rend un index vide plutôt
 * que de faire échouer toute la page. Les vues affichent alors une donnée
 * manquante — jamais une donnée inventée.
 */
/**
 * Ce que le dépôt porte, tous profils confondus (/couverture).
 *
 * Projection calculée au build par `scripts/couverture-corpus.mjs` — 32 Ko là
 * où la page devrait sinon lire les 743 profils. Mémoïsée, et non bloquante :
 * un échec de chargement rend `null`, la page dit qu'elle ne peut pas afficher
 * la couverture plutôt que d'en approcher une.
 */
export function loadCouverture() {
  if (!couverturePromise) {
    couverturePromise = fetch('/data/couverture.json')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`couverture.json : HTTP ${r.status}`))));
  }
  return couverturePromise;
}

function loadScrutins() {
  if (!scrutinsPromise) {
    scrutinsPromise = fetch('/data/scrutins.json')
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => Object.fromEntries((d?.scrutins || []).map((s) => [s.id, s])))
      .catch(() => ({}));
  }
  return scrutinsPromise;
}

/**
 * Index des amendements d'UNE législature (#431), mémoïsé.
 *
 * Contrairement aux scrutins, l'index des amendements n'est pas un fichier
 * unique : il en pèserait 128,8 Mo, au-delà de la limite GitHub de 100 Mo par
 * blob. Il est découpé par législature, et l'UI ne charge que celles que le
 * profil affiché référence — un⋅e élu⋅e de la seule XVIIe ne télécharge pas les
 * trois autres.
 *
 * Les cosignatures vivent dans un fichier compagnon jamais chargé ici : elles
 * pèsent 59 % de l'index et aucune vue ne les affiche.
 *
 * Non bloquant : un échec de chargement rend un index vide plutôt que de faire
 * échouer la page. Les vues affichent alors une donnée manquante — jamais une
 * donnée inventée.
 */
function loadAmendementsLegislature(legislature) {
  if (!amendementsPromises.has(legislature)) {
    amendementsPromises.set(
      legislature,
      fetch(`/data/amendements/${legislature}.json`)
        .then((r) => (r.ok ? r.json() : null))
        // `textes` est conservé depuis #328 : il porte, par `texte_vise`, le
        // `dossier_id` et le titre du dossier législatif. Sans lui, les dépôts
        // se compteraient sur les textes visés — 47 là où il y a 25 dossiers
        // chez Jérôme Guedj — et aucun dossier ne pourrait être NOMMÉ au
        // lecteur, ce qui est l'essentiel de ce que la section publie.
        .then((d) => ({ amendements: d?.amendements || {}, textes: d?.textes || {} }))
        .catch(() => ({ amendements: {}, textes: {} })),
    );
  }
  return amendementsPromises.get(legislature);
}

/**
 * Commission saisie au fond, par dossier législatif (#328).
 *
 * Un seul fichier, chargé une fois : la commission est une propriété du
 * DOSSIER, pas du texte visé — la ranger dans la table `textes` de chaque
 * législature la recopierait une fois par texte visé et la dupliquerait entre
 * législatures.
 *
 * Non bloquant, et l'absence n'est pas comblée : sans cette table, « L'essentiel »
 * n'affiche simplement pas la répartition par commission. Elle n'est jamais
 * déduite d'un intitulé de dossier — ce serait une classification construite
 * ici (AGENTS.md §2 règle 1).
 */
let commissionsPromise = null;

function loadCommissionsDossiers() {
  if (!commissionsPromise) {
    commissionsPromise = fetch('/data/commissions_dossiers.json')
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => d?.commissions || null)
      .catch(() => null);
  }
  return commissionsPromise;
}

/**
 * Dossier législatif d'un scrutin, statut du texte et 49.3 (#758).
 *
 * Un scrutin ne porte AUCUNE référence législative — mesuré : 0 des 18 311
 * scrutins de l'archive portent `objet.referenceLegislative`. La jointure se
 * fait donc dans l'autre sens, depuis les `voteRefs` des actes du dossier, et
 * `src/build_scrutins_dossiers.py` la fige dans ce fichier : 715 scrutins vers
 * 561 dossiers, 72 Ko.
 *
 * Sans lui, « ce qu'il a voté » perd la matière du texte et son statut final ;
 * elle ne les remplace pas — une matière déduite d'un intitulé serait une
 * classification construite ici (§2 règle 1).
 *
 * Non bloquant et mémoïsé, comme les autres index partagés.
 */
let scrutinsDossiersPromise = null;

function loadScrutinsDossiers() {
  if (!scrutinsDossiersPromise) {
    scrutinsDossiersPromise = fetch('/data/scrutins_dossiers.json')
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => (d ? { scrutins: d.scrutins || {}, dossiers: d.dossiers || {} } : null))
      .catch(() => null);
  }
  return scrutinsDossiersPromise;
}

/**
 * Les dossiers européens : référence de procédure → titre, type, stade et
 * commission saisie au fond (#901). 355 entrées, 125 Ko.
 *
 * C'est la table de matière du versant européen — l'équivalent exact de
 * `commissions_dossiers.json` côté Assemblée. Sans elle, la cascade européenne
 * dessine ses rubans en « matière non établie » : elle ne devine rien depuis
 * l'intitulé du texte (§2 règle 2).
 *
 * Indexée par `reference`, et non par un identifiant de dossier : c'est la clé
 * que les textes portés et les amendements européens citent tous les deux
 * (`2021/0136(COD)`).
 *
 * Non bloquant et mémoïsé, comme les autres index partagés.
 */
let dossiersEuropeensPromise = null;
let documentsEuropeensPromise = null;

/* Les documents européens (#901) : l'identifiant doceo d'un texte porté
 * (`B-8-2014-0056`) → ses matières EuroVoc, chacune avec son domaine. Même
 * contrat que l'index des dossiers : absent, les textes sans dossier n'ont
 * aucun thème, jamais un thème deviné. */
function loadDocumentsEuropeens() {
  if (!documentsEuropeensPromise) {
    documentsEuropeensPromise = fetch('/data/documents_europeens.json')
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => (d?.documents
        ? Object.fromEntries(d.documents.map((x) => [x.id, x]))
        : null))
      .catch(() => null);
  }
  return documentsEuropeensPromise;
}

/* Les scrutins nominatifs du Parlement européen, par NUMÉRO (#901) : c'est la
 * clé que portent les positions du profil, avec leur date. */
let scrutinsEuropeensPromise = null;
function loadScrutinsEuropeens() {
  if (!scrutinsEuropeensPromise) {
    scrutinsEuropeensPromise = fetch('/data/scrutins_europeens.json')
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => (d?.scrutins
        ? Object.fromEntries(d.scrutins.map((x) => [x.numero_scrutin, x]))
        : null))
      .catch(() => null);
  }
  return scrutinsEuropeensPromise;
}

function loadDossiersEuropeens() {
  if (!dossiersEuropeensPromise) {
    dossiersEuropeensPromise = fetch('/data/dossiers_europeens.json')
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => (d?.dossiers
        ? Object.fromEntries(d.dossiers.map((x) => [x.reference, x]))
        : null))
      .catch(() => null);
  }
  return dossiersEuropeensPromise;
}

/**
 * Charge les seules législatures que le mapping du profil référence, et rend
 * `{ legislature: { id: amendement } }`.
 *
 * Les index par législature ne sont pas fusionnés en un seul objet : la
 * résolution se fait par législature, lue dans l'identifiant, donc la fusion ne
 * servirait qu'à recopier jusqu'à 207 238 entrées pour rien.
 */
async function loadAmendementsPour(pivot) {
  const legislatures = [
    ...new Set(
      (pivot?.amendements || [])
        .map((a) => legislatureDeAmendementId(a.amendement_id))
        .filter(Boolean),
    ),
  ];
  const parts = await Promise.all(legislatures.map(loadAmendementsLegislature));
  return Object.fromEntries(legislatures.map((l, i) => [l, parts[i]]));
}

function fetchJson(url) {
  return fetch(url).then((r) => (r.ok ? r.json() : null));
}

export async function getCandidatesList() {
  const manifest = await loadManifest();
  return manifest.candidates.map((c) => ({
    id: c.slug,
    nom: c.nom,
    /* Les fiches de groupe dont la personne est membre, appariées par
     * `sync-data`. Le filtre de la barre des candidats les lit : il était
     * servi par le manifeste et perdu ici, si bien que sélectionner un groupe
     * ne retenait AUCUN candidat (constaté en câblant les lignées, #329). */
    groupIds: c.groupIds || [],
    parti: c.parti,
    /* Calculé par `scripts/sync-data.mjs` : un banc — « AN » ou « PE » dans
       `chambres` — ou au moins un mandat de catégorie
       `fonction_gouvernementale` (#328). L'ordre de la liste est déjà
       alphabétique à la source — l'UI ne retrie pas, sans quoi deux tris
       cohabiteraient. */
    aSiegeOuGouverne: c.aSiegeOuGouverne !== false,
  }));
}

export async function getGroupsList() {
  const manifest = await loadManifest();
  /* UNE ENTRÉE PAR LIGNÉE DÉCLARÉE (#836), dans l'ordre alphabétique de son nom.
   *
   * Les lignées viennent du backend (`pivot_data/lignees/`, `lignee_id`
   * déclaré), plus d'un chaînage de `succede_a` refait ici : deux définitions
   * du même objet divergent au premier cas qu'une seule prévoit — une scission.
   *
   * `fiches` accompagne l'entrée parce que le FILTRE des candidats en dépend :
   * sélectionner « Socialistes » retient les membres de n'importe lequel des
   * quatre maillons. */
  return (manifest.lignees || [])
    .map((l) => ({
      id: l.id,
      title: l.nom,
      chambre: l.chambre,
      fiches: l.fiches || [],
    }))
    .sort((a, b) => a.title.localeCompare(b.title, 'fr', { sensitivity: 'base' }));
}

/**
 * Fiches de groupe où ce candidat est membre (#328).
 *
 * `manifest.candidates[].groupIds` est calculé par `scripts/sync-data.mjs`, qui
 * a déjà apparié `membre_id` → slug sur chaque fiche : l'UI n'a donc pas à
 * télécharger les sept fiches pour savoir lesquelles la concernent — elles
 * pèsent de 8 Ko à 4,5 Mo.
 *
 * Non bloquant : une fiche manquante rend la section « où il s'est écarté des
 * siens » incomparable, ce que la page DIT, plutôt que vide, ce qui se lirait
 * comme « il n'a jamais divergé ».
 */
function loadFichesGroupe(manifest, entry) {
  const ids = entry.groupIds || [];
  return Promise.all(
    ids.map((id) => {
      const fiche = manifest.groupes.find((g) => g.id === id);
      return fiche ? fetchJson(`/data/groupes/${fiche.fichier}`).catch(() => null) : null;
    }),
  );
}

/* La page de groupe vers laquelle le libellé affiché peut mener — ou `null`.
 *
 * Deux conditions, et les deux sont nécessaires :
 *   1. la personne est membre de cette fiche — `groupIds`, apparié par
 *      `sync-data` sur `membre_id`, jamais sur un nom (#639) ;
 *   2. cette fiche porte le nom qu'on AFFICHE. Sans cette seconde condition, le
 *      lien mènerait ailleurs que là où le texte le dit — c'était le cas de
 *      Delphine Batho et François Ruffin tant que la fiche ECOS XVIIe n'était
 *      pas publiée.
 *
 * La fiche la plus récente est seule candidate : c'est celle que le libellé
 * courant peut nommer. Le lien mène à sa LIGNÉE, la page de groupe depuis #329 —
 * la fiche par législature n'a plus de page. Mesuré le 11/09/2026 : 12 des 30
 * fiches de candidats publiées portent un lien ; les 18 autres nomment un
 * parti, un groupe du Parlement européen ou « Non inscrit ».
 */
function ficheDuGroupeAffiche(manifest, entry, pivot) {
  const libelle = (pivot?.groupe || '').trim();
  if (!libelle) return null;
  const fiches = (entry.groupIds || [])
    .map((gid) => (manifest.groupes || []).find((g) => g.id === gid))
    .filter(Boolean)
    .sort((a, b) => (Number(a.legislature) || 0) - (Number(b.legislature) || 0));
  const recente = fiches[fiches.length - 1];
  if (!recente || (recente.nom || '').trim() !== libelle) return null;
  return { id: recente.lignee ?? recente.id, nom: recente.nom, legislature: recente.legislature };
}

/* ── CHARGER UNE FOIS, CALCULER À CHAQUE MOT (#979) ──────────────────────────
 *
 * Le filtre par intitulé reconstruit la fiche sur un profil réduit : il ne
 * doit rien retélécharger. `chargerSourcesCandidat` rassemble ce que la fiche
 * lit — profil, index, chronologie —, `vueCandidat` la calcule, avec ou sans
 * mot. `getCandidateProfile` reste la composition des deux, sans mot. */
export async function chargerSourcesCandidat(id) {
  const manifest = await loadManifest();
  const entry = manifest.candidates.find((c) => c.slug === id);
  if (!entry) return null;
  const [pivot, scrutins, fichesGroupe, commissions, scrutinsDossiers, dossiersEuropeens, documentsEuropeens, scrutinsEuropeens] =
    await Promise.all([
      fetchJson(`/data/profiles/${entry.slug}.pivot.json`),
      loadScrutins(),
      loadFichesGroupe(manifest, entry),
      loadCommissionsDossiers(),
      loadScrutinsDossiers(),
      loadDossiersEuropeens(),
      loadDocumentsEuropeens(),
      loadScrutinsEuropeens(),
    ]);
  if (!pivot) return null;
  // L'index des amendements se charge APRÈS le profil : ce sont les
  // identifiants du mapping qui disent quelles législatures aller chercher.
  const amendements = await loadAmendementsPour(pivot);
  return {
    manifest, entry, pivot, scrutins, fichesGroupe, commissions, scrutinsDossiers,
    dossiersEuropeens, documentsEuropeens, scrutinsEuropeens, amendements,
  };
}

/* Ce que le filtre compare, lu là où la fiche l'affiche : le titre de texte
 * d'un vote (`titreDuTexteVote`, le même que « Ce qu'il a voté »), le dossier
 * d'un amendement (index par législature côté Assemblée,
 * `dossiers_europeens.json` côté Parlement européen), le chemin du point de
 * séance d'une intervention ET son verbatim. */
function lecteursDIntitule(sources) {
  const { scrutins, amendements, dossiersEuropeens } = sources;
  return {
    intituleDuVote: (v) => {
      const scrutin = (scrutins && v.scrutin_id && scrutins[v.scrutin_id]) || v.scrutin_non_resolu || null;
      const brut = scrutin?.texte ?? scrutin?.titre ?? null;
      return titreDuTexteVote(brut) || brut;
    },
    intituleDeLAmendement: (a) => {
      const europeen = a.amendement_non_resolu;
      if (europeen) return dossiersEuropeens?.[europeen.texte_vise]?.titre ?? null;
      const index = amendements?.[legislatureDeAmendementId(a.amendement_id)];
      const texteVise = index?.amendements?.[a.amendement_id]?.texte_vise;
      return (texteVise && index?.textes?.[texteVise]?.titre) || null;
    },
    /* Le sujet OU le propos : la barre dit « Rechercher sur cette page », et
     * les verbatims sont sur la page. Arbitré le 17/09/2026 — « nucléaire »
     * ne trouvait aucune des 5 interventions où Maurel en parle. */
    intituleDeLIntervention: (i) => [cheminDuPoint(i), i.texte].filter(Boolean).join('\n'),
  };
}

export function vueCandidat(sources, mot = '') {
  if (!sources) return null;
  const {
    manifest, entry, scrutins, fichesGroupe, commissions, scrutinsDossiers,
    dossiersEuropeens, documentsEuropeens, scrutinsEuropeens, amendements,
  } = sources;
  const pivot = filtrerProfil(sources.pivot, mot, lecteursDIntitule(sources));
  const view = buildCandidateView(
    pivot,
    entry,
    scrutins,
    amendements,
    fichesGroupe.filter(Boolean),
    commissions,
    scrutinsDossiers,
    // TOUS les gouvernements, pas les seuls dont la personne fut membre : « ce
    // qu'il a voté » découpe la carrière par gouvernement en place, ce qui
    // demande la chronologie entière. Les dates vivent déjà dans le manifeste,
    // aucune fiche supplémentaire n'est téléchargée.
    manifest.gouvernements || [],
    ficheDuGroupeAffiche(manifest, entry, sources.pivot),
    dossiersEuropeens,
    documentsEuropeens,
    scrutinsEuropeens,
  );
  if (!view || !motsDuFiltre(mot).length) return avecSiglesDeSiege(view, manifest);
  /* SOUS UN MOT, « Ce qu'il a voté » cumule ses périodes (`periodeCumulee`) :
   * la figure montre alors ce que sa liste montre. L'échelle est recalculée sur
   * ce seul cumul. `filtre` porte ce que les messages « aucun résultat » disent
   * de la fiche ENTIÈRE, que le profil réduit ne sait plus. */
  const cumul = periodeCumulee(view.votes.periodes);
  return avecSiglesDeSiege({
    ...view,
    votes: {
      ...view.votes,
      periodes: cumul ? [cumul] : [],
      portee: cumul ? porteeCommune([cumul]) : view.votes.portee,
    },
    filtre: {
      mot: mot.trim(),
      amendementsEuropeens: (sources.pivot.amendements || []).some((a) => a.amendement_non_resolu),
    },
  }, manifest);
}

export async function getCandidateProfile(id) {
  return vueCandidat(await chargerSourcesCandidat(id));
}

/* Le sigle de chaque siège, lu sur les fiches de groupe du manifeste quand
 * l'intitulé du mandat porte le nom complet (`sigleDuSiege`). */
function avecSiglesDeSiege(view, manifest) {
  if (!view?.parcours?.roles) return view;
  const parNom = new Map();
  const ambigus = new Set();
  for (const g of manifest.groupes || []) {
    if (g.chambre !== 'AN' || !g.nom || !g.sigle) continue;
    const nom = g.nom.trim();
    if (parNom.has(nom) && parNom.get(nom) !== g.sigle) ambigus.add(nom);
    parNom.set(nom, g.sigle);
  }
  for (const nom of ambigus) parNom.delete(nom);
  /* Un sigle DÉJÀ POSÉ n'est pas recalculé : c'est le cas du groupe européen,
     que la source publie elle-même (`sigle_organe`, #863). Le repasser par
     `sigleDuSiege` le perdrait — « GUE/NGL » et « Verts/ALE » portent une
     barre, « The Left » une espace, et aucun ne passe `FORME_DE_SIGLE`, qui
     existe pour ne jamais fabriquer une abréviation, pas pour refuser celles
     que la source écrit. */
  const roles = view.parcours.roles.map((r) => (r.institution === INSTITUTION_PARLEMENT
    ? { ...r, sigle: r.sigle ?? sigleDuSiege(r.detail, parNom) }
    : r));
  return { ...view, parcours: { ...view.parcours, roles } };
}

/**
 * La fiche d'une lignée : sa PROJECTION de build (`scripts/vue-lignee.mjs`),
 * jamais la fiche de `pivot_data/lignees/` ni ses maillons — 134 Ko pour la
 * lignée socialiste, contre 5,3 Mo de fiche de lignée et 11 Mo de maillons.
 * Tout ce que la page affiche y est déjà calculé, par les règles de
 * `utils/groupe.js` et `utils/lignee.js` que ce navigateur importe aussi.
 */
export async function getLigneeProfile(id) {
  const manifest = await loadManifest();
  const entry = (manifest.lignees || []).find((l) => l.id === id);
  if (!entry) return null;
  return fetchJson(`/data/lignees/${entry.fichier}`);
}

/* Les débats complets d'une lignée (#979) : la projection n'en porte que dix
 * par groupe. La page ne les demande que quand un mot est tapé dans sa
 * recherche. Rendus sous la forme de `sujets.liste`, par la MÊME règle
 * (`etiquettesThematiques`) : le fichier ne transporte que `[intitulé,
 * porteurs]` et le dénominateur, et la phrase des porteurs se compose ici comme
 * au build. `null` si le fichier manque : la section filtre alors les dix. */
export async function getDebatsLignee(id) {
  const manifest = await loadManifest();
  const entry = (manifest.lignees || []).find((l) => l.id === id);
  if (!entry?.debats) return null;
  const brut = await fetchJson(`/data/lignees/${entry.debats}`);
  if (!brut?.maillons) return null;
  return Object.fromEntries(Object.entries(brut.maillons).map(([maillon, m]) => [
    maillon,
    etiquettesThematiques({
      tags_thematiques_agreges: m.debats.map(([tag, n]) => ({ tag, nb_membres_porteurs: n })),
      membres: { length: m.denominateur },
    }, Infinity),
  ]));
}

/**
 * La lignée d'une fiche de groupe — pour les adresses d'avant #329
 * (`/groupes/AN-SOC-17`), qui mènent désormais à la lignée entière. `null`
 * quand l'identifiant n'est pas une fiche de groupe connue.
 */
export async function ligneeDeLaFiche(idDeFiche) {
  const manifest = await loadManifest();
  return (manifest.groupes || []).find((g) => g.id === idDeFiche)?.lignee ?? null;
}

export async function getGovernmentsList() {
  const manifest = await loadManifest();
  return (manifest.gouvernements || []).map((g) => ({
    id: g.id,
    title: g.nom,
    kicker: g.actif ? 'En fonction' : `Jusqu'en ${g.fin ? new Date(g.fin).getFullYear() : '?'}`,
    // La frise de « En bref » situe le gouvernement parmi les autres : elle a
    // besoin des bornes, que le manifest porte déjà (#330).
    debut: g.debut,
    fin: g.fin,
    actif: g.actif,
  }));
}

/**
 * LE DÉTAIL D'UN SUJET DE PAROLE, chargé au premier clic et pas avant : la
 * projection pèse jusqu'à 4,1 Mo (Borne), quand la fiche entière en fait 1.
 * Même geste que les débats d'une lignée (#979).
 */
export async function getParolesDuGouvernement(id) {
  const manifest = await loadManifest();
  const entry = (manifest.gouvernements || []).find((g) => g.id === id);
  if (!entry?.paroles) return {};
  return (await fetchJson(`/data/gouvernements/${entry.paroles}`)) || {};
}

export async function getGovernmentProfile(id) {
  const manifest = await loadManifest();
  const entry = (manifest.gouvernements || []).find((g) => g.id === id);
  if (!entry) return null;
  const gouvernement = await fetchJson(`/data/gouvernements/${entry.fichier}`);
  if (!gouvernement) return null;
  // Les groupes du manifest, pas leurs fiches : seules la position déclarée et
  // les bornes servent ici (#330).
  //
  // LE LIEN VERS LE PREMIER MINISTRE NE SE POSE QUE SI LA PAGE EXISTE. Seules
  // les fiches de candidats déclarés sont publiées : 4 des 17 Premiers
  // ministres en ont une — Attal, Cazeneuve et Philippe (deux gouvernements).
  // Les 13 autres nommaient une adresse qui rend « Aucun candidat trouvé ».
  // Même règle que `ficheDuGroupeAffiche` : un lien mène là où le texte dit.
  const pm = gouvernement.premier_ministre?.nom;
  const fiche = pm
    ? (manifest.candidates || []).find((c) => c.nom === pm)
    : null;
  return buildGovernmentView(gouvernement, manifest.groupes || [], fiche?.slug ?? null);
}
