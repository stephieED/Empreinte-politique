/*
 * Les règles du profil candidat — lot 2 de la refonte #324 (issue #328).
 *
 * Ce module ne dessine rien : il décide ce que la fiche d'un candidat déclaré a
 * le droit d'afficher. `components/CandidateProfile.jsx` en donne la forme,
 * `data/pivotAdapter.js` l'appelle. Même partage que le lot 1
 * (`utils/lecture.js`, #326) et le lot 3 (`utils/groupe.js`, #329) : les six
 * fondations communes vivent là-bas et sont IMPORTÉES ici, jamais réécrites.
 *
 * Le principe directeur de la trame, arrêté sur maquette après sept itérations
 * (#328) : **l'institution n'est jamais un chapitre, c'est une colonne.**
 * L'ordre est chronologique, jamais hiérarchique, et AUCUN total n'additionne
 * deux natures d'acte — c'est ce qui empêche la comparaison de virer au
 * classement (AGENTS.md §2 règle 1).
 *
 * Population : les 13 profils `meta.provenance == "candidat_declare"`. Les 468
 * `roster_groupe` ne sont pas une page et ne sont jamais liés. Un chiffre sur
 * les 481 mélange les deux et ne veut rien dire (#630).
 *
 * Chiffres cités : mesurés sur le dépôt au commit `9c702c4b`, 01/09/2026.
 */

import {
  SORTS_PROCEDURE_49_3,
  formatNumber,
  isWholeTextVote,
  normalizeLabel,
  selectDerniereLectureVotes,
} from './lecture.js';

/* ── Règle : la position dans l'hémicycle est DÉCLARÉE, jamais déduite ───────
 *
 * L'Assemblée publie `organe.positionPolitique` sur chaque groupe politique —
 * trois valeurs, jamais deux : `Majoritaire`, `Minoritaire`, `Opposition`.
 * `candidate_profile.py` la reporte sur les mandats `groupe_politique` sous
 * `position_dans_hemicycle`, avec le `source_url` du référentiel qu'exige
 * AGENTS.md §2 règle 6 — sans `source_url`, la valeur n'est pas affichable.
 *
 * Mesuré sur les 541 mandats des 13 candidats déclarés : 14 `opposition`,
 * 7 `majorite`, 17 `gouvernement`, 503 non renseignés, et **`minoritaire`
 * n'apparaît sur aucun**. La valeur reste déclarée ici parce que le schéma la
 * connaît (`KNOWN_POSITIONS_HEMICYCLE`) : la retirer ferait tomber en silence
 * un groupe `Minoritaire` le jour où l'un des treize en rejoint un.
 *
 * `null` n'est pas une quatrième position : c'est « l'Assemblée ne l'a pas
 * déclaré ». Elle ne le déclare pas pour la législature en cours — Guedj et
 * Attal siègent tous deux dans la XVIIe et aucun de leurs mandats de groupe de
 * cette législature ne porte de position. Le déduire d'un comportement de vote
 * serait exactement le jugement à ne pas porter (§2 règle 1).
 */
export const POSITIONS_HEMICYCLE = {
  majorite: { label: 'groupe majoritaire', motif: 'plein' },
  opposition: { label: "groupe d'opposition", motif: 'diagonales' },
  minoritaire: { label: 'groupe minoritaire', motif: 'points' },
  gouvernement: { label: 'membre du gouvernement', motif: 'rayures' },
};

export const POSITION_NON_DECLAREE = {
  label: "position non déclarée par l'Assemblée",
  motif: 'fines-rayures',
};

export function libellePosition(position) {
  return (POSITIONS_HEMICYCLE[position] ?? POSITION_NON_DECLAREE).label;
}

export function motifPosition(position) {
  return (POSITIONS_HEMICYCLE[position] ?? POSITION_NON_DECLAREE).motif;
}

/* ── Règle : la voix du texte suit la source, ou n'affirme rien ──────────────
 *
 * La trame écrit « ce qu'il a proposé ». Appliquée telle quelle aux treize, la
 * formule se trompe sur quatre d'entre eux — deux des treize candidats déclarés
 * sont des femmes, et deux profils vides ne disent rien. Déduire le genre d'un
 * prénom serait une inférence non sourcée là où la source en porte une :
 * `identite.civilite`, renseignée sur 9 des 13 (« M. » ×7, « Mme » ×2).
 *
 * Quand elle manque, la page ne choisit pas : elle emploie une tournure qui
 * n'affirme aucun genre (« ce que cette personne a proposé »). Un vide reste un
 * vide (§2 règle 5) — y compris dans la grammaire.
 */
const VOIX_MASCULINE = {
  pronom: 'il',
  sujet: 'il',
  Sujet: 'Il',
  quil: "qu'il",
  depute: 'député',
  accorde: '',
  ne: 'Né',
  titres: {
    propose: "Ce qu'il a proposé",
    dit: "Ce qu'il a dit",
    vote: "Ce qu'il a voté",
    ecarts: "Où il s'est écarté des siens",
  },
};

const VOIX_FEMININE = {
  pronom: 'elle',
  sujet: 'elle',
  Sujet: 'Elle',
  quil: "qu'elle",
  depute: 'députée',
  accorde: 'e',
  ne: 'Née',
  titres: {
    propose: "Ce qu'elle a proposé",
    dit: "Ce qu'elle a dit",
    vote: "Ce qu'elle a voté",
    ecarts: "Où elle s'est écartée des siens",
  },
};

const VOIX_NON_DECLAREE = {
  pronom: 'cette personne',
  sujet: 'cette personne',
  Sujet: 'Cette personne',
  quil: 'que cette personne',
  depute: 'parlementaire',
  accorde: '',
  ne: 'Naissance le',
  titres: {
    propose: 'Ce que cette personne a proposé',
    dit: 'Ce que cette personne a dit',
    vote: 'Ce que cette personne a voté',
    ecarts: 'Les écarts avec son groupe',
  },
};

export function voixDuProfil(civilite) {
  if (civilite === 'M.') return VOIX_MASCULINE;
  if (civilite === 'Mme') return VOIX_FEMININE;
  return VOIX_NON_DECLAREE;
}

const FIN_OUVERTE = '9999-12-31';

function borneFin(mandat) {
  return mandat.actif || !mandat.fin ? FIN_OUVERTE : mandat.fin;
}

function chevauche(a, b) {
  return a.debut <= borneFin(b) && b.debut <= borneFin(a);
}

/* ── Règle : une période de position n'est lue que si elle est sourcée ───────
 *
 * §2 règle 6 : `position_dans_hemicycle` sans `source_url` n'est pas publiable.
 * Le filtre est ici, une fois, et pas dans chaque appelant.
 */
function periodesDePosition(mandats, categorie) {
  return mandats
    .filter(
      (m) =>
        m.categorie === categorie &&
        m.position_dans_hemicycle &&
        m.source_url &&
        m.debut,
    )
    .map((m) => ({
      position: m.position_dans_hemicycle,
      sigle: sigleDeGroupePolitique(m.label),
      debut: m.debut,
      fin: borneFin(m),
      sourceUrl: m.source_url,
    }));
}

/*
 * `groupe_politique` porte son sigle dans l'intitulé : « Groupe politique
 * (SOC) ». Il n'existe pas de champ pour lui. Sans parenthèse, on rend
 * l'intitulé tel que la source l'écrit plutôt que d'inventer un sigle.
 */
/* LE SIGLE D'UN SIÈGE, pour la frise (maquette « En bref », 11/09/2026) : un
 * segment ne porte que le sigle du groupe et la place dans l'hémicycle.
 *
 * L'intitulé entre parenthèses est un sigle quand il en a la forme (« FI »,
 * « LaREM ») ; ailleurs l'Assemblée y écrit le nom complet (« Ensemble pour la
 * République »), et le sigle vit sur la fiche de groupe. `siglesParNom` vient
 * des fiches de groupe du manifeste : un nom qui y porte deux sigles n'y figure
 * pas. Sans sigle établi, rien — jamais une abréviation fabriquée. */
/** Le marqueur d'institution que #328 pose sur une entrée que l'Assemblée ne
 *  source pas : `scrutin_non_resolu.institution`, `amendement_non_resolu`,
 *  `institution` sur un texte, `source.institution` sur une intervention. */
export const INSTITUTION_PE_SOURCE = 'parlement_europeen';

const FORME_DE_SIGLE = /^[\p{L}&-]{1,8}$/u;

export function sigleDuSiege(detail, siglesParNom = new Map()) {
  const d = (detail || '').trim();
  if (!d) return null;
  if (FORME_DE_SIGLE.test(d)) return d;
  return siglesParNom.get(d) ?? null;
}

export function sigleDeGroupePolitique(label) {
  const m = /\(([^)]+)\)\s*$/.exec(label || '');
  return m ? m[1] : label || null;
}

/* ── Le groupe politique européen, qui se lit et ne se devine pas (#863) ─────
 *
 * L'Assemblée écrit le sigle dans l'intitulé, entre parenthèses, et il faut
 * l'en extraire. Le Parlement européen, lui, le PUBLIE : depuis #863 le mandat
 * porte `sigle_organe` (« S&D », « GUE/NGL », « Verts/ALE ») à côté de
 * `type_organe_source`. Il n'y a donc rien à deviner, et c'est ce qui fait que
 * ces segments peuvent parler alors que ceux du Sénat se taisent.
 *
 * DEUX PIÈGES, tous deux mesurés le 13/09/2026 sur les 6 candidats déclarés qui
 * ont un mandat européen :
 *
 * 1. `sigle_organe` est AUSSI porté par le SIÈGE européen, où il vaut
 *    « 10e législature ». Lire le sigle sur le siège écrirait « 10e
 *    législature » en travers du segment. Le discriminant est
 *    `type_organe_source`, jamais la présence du champ.
 * 2. Ces sigles ne passent pas `FORME_DE_SIGLE` : « GUE/NGL » et « Verts/ALE »
 *    portent une barre, « The Left » une espace, et le second fait 9 signes.
 *    Ce garde-fou existe pour ne jamais FABRIQUER une abréviation à partir d'un
 *    nom complet ; ici la source publie le sigle lui-même, donc il est posé
 *    directement et `avecSiglesDeSiege` ne le recalcule pas.
 */
export const TYPE_GROUPE_EUROPEEN = 'groupe_politique_europeen';

function periodesDeGroupeEuropeen(mandats) {
  return (mandats || [])
    .filter((m) => m.type_organe_source === TYPE_GROUPE_EUROPEEN && m.sigle_organe && m.debut)
    .map((m) => ({
      sigle: m.sigle_organe,
      /* Le NOM COMPLET, pour la liste datée : « Groupe de l'Alliance
         Progressiste des Socialistes et Démocrates au Parlement européen ».
         La frise donne la silhouette et le sigle, la liste la nomme — c'est le
         partage posé le 11/09, et un sigle seul ne dit rien de ce qu'est S&D à
         qui ne le connaît pas déjà. */
      nom: m.label || null,
      debut: m.debut,
      fin: borneFin(m),
      sourceUrl: m.source_url ?? null,
    }));
}

/** Le groupe d'un siège européen : celui où il a passé le plus de temps.
 *
 *  Un siège européen en croise souvent plusieurs — Emmanuel Maurel, sur la
 *  législature 2014-2019, passe de S&D à NI puis à GUE/NGL. Prendre le premier
 *  venu donnerait un sigle exact mais arbitraire ; on prend le plus long, et
 *  les autres restent visibles dans la liste datée.
 */
function groupeEuropeenDuSiege(siege, periodes) {
  const jours = (p) => {
    const debut = p.debut > siege.debut ? p.debut : siege.debut;
    const finP = p.fin === FIN_OUVERTE ? '9999-12-31' : p.fin;
    const finS = borneFin(siege) === FIN_OUVERTE ? '9999-12-31' : borneFin(siege);
    const fin = finP < finS ? finP : finS;
    return Math.max(0, Date.parse(fin) - Date.parse(debut));
  };
  const chevauchantes = periodes.filter((p) => chevauche(p, siege));
  if (!chevauchantes.length) return null;
  return chevauchantes.reduce((meilleure, p) => (jours(p) > jours(meilleure) ? p : meilleure));
}

/* ── Règle : un siège, pas un enregistrement ─────────────────────────────────
 *
 * #640 : « un profil publie TOUS ses mandats électifs, un par siège ». La
 * fusion additive (#465) a pourtant conservé, sur plusieurs profils, DEUX
 * enregistrements pour un même siège — un ancien sans `chambre`, un récent avec.
 * Mesuré : Jérôme Guedj porte 5 enregistrements pour 4 sièges, Gabriel Attal 5
 * pour 3. Les afficher tous ferait lire deux mandats là où il y en a un.
 *
 * Le regroupement se fait sur la DATE DE FIN — deux mandats qui se chevauchent
 * et s'arrêtent le même jour sont le même siège — et jamais sur la seule
 * législature, ce que #640 interdit explicitement (deux mandats séparés par une
 * élection annulée seraient soudés). L'enregistrement qui porte une `chambre`
 * est préféré comme représentant, la date de début retenue est la plus ancienne
 * : on ne raccourcit pas un mandat observé.
 *
 * Le nombre d'enregistrements repliés est RENDU, pas caché : il alimente la
 * section « ce qu'on n'a pas pu lire ».
 */
export function siegesElectifs(mandats) {
  const electifs = (mandats || [])
    .filter((m) => m.categorie === 'mandat_electif' && m.debut)
    .sort((a, b) => (a.debut < b.debut ? -1 : 1));

  const sieges = [];
  for (const m of electifs) {
    const fin = borneFin(m);
    const existant = sieges.find((s) => s.fin === fin && chevauche(s, m));
    if (!existant) {
      sieges.push({
        debut: m.debut,
        fin,
        actif: Boolean(m.actif) || !m.fin,
        chambre: m.chambre ?? null,
        label: m.label ?? null,
        enregistrements: 1,
      });
      continue;
    }
    existant.enregistrements += 1;
    if (m.debut < existant.debut) existant.debut = m.debut;
    if (!existant.chambre && m.chambre) existant.chambre = m.chambre;
    if (m.chambre) existant.label = m.label ?? existant.label;
  }
  return sieges.sort((a, b) => (a.debut < b.debut ? -1 : 1));
}

const CHAMBRE_ROLE = {
  AN: 'Député(e)',
  Senat: 'Sénateur(rice)',
  PE: 'Député(e) européen(ne)',
  mairie: 'Maire',
};

/*
 * Une fonction gouvernementale se lit sur deux enregistrements distincts pour
 * la même période : l'appartenance (`fonction: "membre"`, intitulé
 * « Gouvernement (BORNE) ») et le portefeuille (« Ministre délégué… »). Le
 * portefeuille porte le rôle, l'appartenance porte le nom du gouvernement.
 * `fonction: "en mission"` n'est ni l'un ni l'autre : c'est un·e parlementaire
 * en mission auprès d'un ministère, qui reste parlementaire.
 */
const FONCTION_MEMBRE = 'membre';
const FONCTION_MISSION = 'en mission';

export function appartenancesGouvernementales(mandats) {
  return (mandats || [])
    .filter((m) => m.categorie === 'fonction_gouvernementale' && m.fonction === FONCTION_MEMBRE && m.debut)
    .map((m) => ({
      nom: sigleDeGroupePolitique(m.label) || m.label,
      debut: m.debut,
      fin: borneFin(m),
      actif: Boolean(m.actif) || !m.fin,
      sourceUrl: m.source_url ?? null,
    }))
    .sort((a, b) => (a.debut < b.debut ? -1 : 1));
}

/* ── Livrable : le parcours, une seule frise ─────────────────────────────────
 *
 * Pas deux couloirs empilés — un couloir au-dessus de l'autre EST une
 * hiérarchie, au sens littéral. Une ligne par rôle, ordonnées par date de
 * début, quelle que soit l'institution : c'est la date qui range, pour tout le
 * monde. Quand deux rôles se chevauchent (Attal est élu député 33 jours alors
 * qu'il est ministre délégué), la bande se scinde par un rangement glouton et
 * la légende dit que c'en est un.
 */
export const INSTITUTION_PARLEMENT = 'parlement';
export const INSTITUTION_GOUVERNEMENT = 'gouvernement';
export const INSTITUTION_MISSION = 'mission';

/* LE MANDAT LOCAL N'EST PAS UNE INSTITUTION, MAIS IL A SA PISTE (#922).
 *
 * Le schéma le pose : les mandats locaux « vivent dans `mandats[]` avec les
 * autres », sans chambre — un conseil régional n'entre pas dans `chambres[]`.
 * Sur la frise, ils prennent pourtant une piste à eux, parce que le lecteur doit
 * distinguer d'un coup d'œil une mairie d'un siège de député. Aucun des
 * consommateurs du parcours ne la lit par erreur : tous filtrent explicitement
 * sur `parlement` ou `gouvernement` (comparaison au groupe, périodes politiques,
 * colonnes d'« En bref »). */
export const INSTITUTION_LOCAL = 'local';

/* LE SIÈGE PORTE SA CHAMBRE, ET LA CHAMBRE FAIT LA PISTE (#328).
 *
 * `institution` dit le BANC — on siège, on gouverne, on est en mission —, et
 * quinze endroits du code en dépendent : la comparaison au groupe, les périodes
 * politiques, les limites de couverture. Le scinder en trois aurait demandé de
 * relire ces quinze-là un par un. La chambre voyage donc à côté, et seule
 * l'affichage la lit.
 *
 * Ce que ça ferme, mesuré le 10/09/2026 sur les 30 fiches publiées : un mandat
 * européen était rangé dans la piste `parlement`, donc peint de la teinte de
 * l'Assemblée sur la frise et compté dans une colonne intitulée « À
 * l'Assemblée ». Sur `raphael-glucksmann`, qui n'a jamais siégé à l'Assemblée,
 * cette colonne portait ses 4 mandats en commission européens ; sur
 * `bruno-retailleau`, sénateur, ses 35 textes. Un intitulé faux n'est pas une
 * approximation (§2 règle 2).
 */
export const INSTITUTION_SENAT = 'senat';
export const INSTITUTION_PE = 'pe';

const PISTE_PAR_CHAMBRE = {
  AN: INSTITUTION_PARLEMENT,
  Senat: INSTITUTION_SENAT,
  PE: INSTITUTION_PE,
};

/** La piste d'un rôle : son banc, et pour un siège la chambre où il s'exerce.
 *  Une chambre inconnue — `mairie`, ou `null` sur un mandat d'avant #492 —
 *  retombe sur `parlement` : c'est ce que la fiche faisait déjà, et inventer
 *  une piste pour une valeur non estampillée serait pire que de la ranger. */
export function pisteDuRole(role) {
  if (!role || role.institution !== INSTITUTION_PARLEMENT) return role?.institution ?? null;
  return PISTE_PAR_CHAMBRE[role.chambre] || INSTITUTION_PARLEMENT;
}

/** L'ordre des colonnes ne se lit pas comme un classement : c'est celui de la
 *  frise, qui range par date de début. Il est fixe pour que deux fiches se
 *  comparent. */
export const ORDRE_COLONNES = [
  INSTITUTION_PARLEMENT,
  INSTITUTION_SENAT,
  INSTITUTION_PE,
  INSTITUTION_GOUVERNEMENT,
];

const INTITULE_CHEF = /^premier ministre$/;

const CATEGORIE_MANDAT_LOCAL = 'mandat_local';

/* Le siège, quand la source ne publie aucune fonction : un conseiller municipal
 * n'a pas d'autre titre. Les quatre types présents au corpus du 16/09/2026 ;
 * un type absent de la table retombe sur « Mandat local », jamais sur un titre
 * deviné. */
const SIEGE_LOCAL = {
  conseil_municipal: 'Conseiller(ère) municipal(e)',
  conseil_communautaire: 'Conseiller(ère) communautaire',
  conseil_departemental: 'Conseiller(ère) départemental(e)',
  conseil_regional: 'Conseiller(ère) régional(e)',
};

export function rolesDuParcours(mandats) {
  const liste = mandats || [];
  const positionsGroupe = periodesDePosition(liste, 'groupe_politique');
  const groupesEuropeens = periodesDeGroupeEuropeen(liste);
  const gouvernements = appartenancesGouvernementales(liste);

  const roles = [];

  for (const siege of siegesElectifs(liste)) {
    const chevauchantes = positionsGroupe.filter((p) => chevauche(p, siege));
    // Une position par siège : celle de la période la plus longue passée dans
    // ce siège. Un siège qui en croise deux (un changement de qualification en
    // cours de législature) reste rendu par sa plus longue — et les deux
    // restent visibles dans la liste des rôles, jamais fusionnées en une.
    const retenue = chevauchantes[0] ?? null;
    // Le groupe se lit d'abord sur le mandat `groupe_politique`, qui porte AUSSI
    // la position déclarée. Quand il n'y en a pas — c'est le cas de toute la
    // XVIIe législature — l'intitulé du mandat électif le porte encore
    // (« Mandat parlementaire (Socialistes et apparentés) ») : c'est la même
    // source, pas une déduction. Sans ce repli, le siège en cours s'afficherait
    // sans groupe alors que la source en nomme un.
    const groupe = retenue?.sigle ?? sigleDeGroupePolitique(siege.label);
    // Un siège européen n'a pas de mandat `groupe_politique` : son groupe vit
    // sur un mandat à part, qui publie son sigle (#863). Le sigle est donc posé
    // ici, tel que la source l'écrit, et `avecSiglesDeSiege` ne le recalcule pas.
    const groupePE = siege.chambre === 'PE' ? groupeEuropeenDuSiege(siege, groupesEuropeens) : null;
    roles.push({
      institution: INSTITUTION_PARLEMENT,
      // La chambre voyage avec le siège : elle fait la piste et la teinte, sans
      // toucher au banc que quinze consommateurs lisent (`pisteDuRole`).
      chambre: siege.chambre ?? null,
      role: CHAMBRE_ROLE[siege.chambre] || 'Mandat parlementaire',
      // Le SIGLE va sur le segment, le NOM COMPLET dans la liste datée.
      detail: groupePE?.nom ?? groupePE?.sigle ?? (groupe && groupe !== siege.label ? groupe : null),
      sigle: groupePE?.sigle ?? undefined,
      debut: siege.debut,
      fin: siege.fin,
      actif: siege.actif,
      position: retenue?.position ?? null,
      sourceUrl: groupePE?.sourceUrl ?? retenue?.sourceUrl ?? null,
    });
  }

  for (const m of liste) {
    if (m.categorie !== 'fonction_gouvernementale' || !m.debut) continue;
    if (m.fonction === FONCTION_MEMBRE) continue;

    if (m.fonction === FONCTION_MISSION) {
      roles.push({
        institution: INSTITUTION_MISSION,
        role: 'Parlementaire en mission',
        detail: m.label ? `auprès du ${m.label}` : null,
        debut: m.debut,
        fin: borneFin(m),
        actif: Boolean(m.actif) || !m.fin,
        position: null,
        sourceUrl: m.source_url ?? null,
      });
      continue;
    }

    const gouvernement = gouvernements.find((g) => chevauche(g, { debut: m.debut, fin: borneFin(m) }));
    const chef = INTITULE_CHEF.test(normalizeLabel(m.fonction));
    roles.push({
      institution: INSTITUTION_GOUVERNEMENT,
      chef,
      role: m.fonction || 'Membre du gouvernement',
      detail: [m.label, gouvernement ? `gouvernement ${gouvernement.nom}` : null]
        .filter(Boolean)
        .join(' · ') || null,
      debut: m.debut,
      fin: borneFin(m),
      actif: Boolean(m.actif) || !m.fin,
      position: 'gouvernement',
      sourceUrl: m.source_url ?? null,
    });
  }

  /* LES MANDATS LOCAUX, TELS QUE LE RÉPERTOIRE LES PUBLIE (#922).
   *
   * LA DATE DE DÉBUT EST CELLE DU MANDAT EN COURS. Le répertoire national des
   * élus ne publie que la mandature commencée — mars 2026 pour les communes —,
   * et le fichier des sortants la précédente : un maire depuis vingt ans
   * apparaît « depuis le 21 mars 2026 ». C'est vrai du mandat, pas de la
   * personne, et rien avant 2020 n'est publié (`borne-mandats-locaux-2020-922`).
   *
   * LA FONCTION D'ABORD : « Maire » commence le jour où le conseil l'élit, pas le
   * jour du scrutin municipal. Sans fonction publiée, le siège seul.
   *
   * AUCUNE DATE DE FIN N'EST PUBLIÉE. Un mandat en cours est ouvert. Un mandat
   * du fichier des sortants est clos, sans date : son segment s'arrête au jour
   * où la source l'atteste (`fin_non_resolue.constate_le`), et la liste datée
   * écrit « fin non publiée ». `actif` se lit sur la source — le déduire de
   * l'absence de fin, comme pour une fonction gouvernementale, rouvrirait un
   * mandat que la source dit achevé. */
  for (const m of liste) {
    if (m.categorie !== CATEGORIE_MANDAT_LOCAL || !m.debut) continue;
    const actif = Boolean(m.actif);
    const finConstatee = !actif && !m.fin ? m.fin_non_resolue?.constate_le ?? null : null;
    roles.push({
      institution: INSTITUTION_LOCAL,
      role: m.fonction || SIEGE_LOCAL[m.type_organe_source] || 'Mandat local',
      detail: m.label || null,
      debut: (m.fonction && m.debut_fonction) || m.debut,
      // OUVERT se dit `FIN_OUVERTE`, comme pour tous les autres rôles : c'est
      // la valeur que `positionSurAxe` rabat sur la fin de l'axe. Un `null` y
      // vaut 0, et chaque mandat en cours se dessinait à la largeur minimale —
      // la présidence de région de Bruno Retailleau, commencée en 2021, tenait
      // sur la frise comme trois mois.
      fin: m.fin || finConstatee || (actif ? FIN_OUVERTE : null),
      actif,
      finNonPubliee: !actif && !m.fin,
      position: null,
      sourceUrl: m.source_url ?? null,
    });
  }

  roles.sort((a, b) => (a.debut === b.debut ? (a.fin < b.fin ? -1 : 1) : a.debut < b.debut ? -1 : 1));

  // Rangement glouton : la première ligne libre à cette date. Un rangement,
  // pas une hiérarchie — la légende le dit sur la page.
  const lignes = [];
  for (const r of roles) {
    let i = lignes.findIndex((l) => l.every((o) => !chevauche(o, r)));
    if (i < 0) {
      lignes.push([]);
      i = lignes.length - 1;
    }
    lignes[i].push(r);
    r.ligne = i;
  }

  return { roles: roles.map((r, i) => ({ ...r, numero: i + 1 })), nbLignes: Math.max(1, lignes.length) };
}

/*
 * Les bornes de la frise : du premier début observé à AUJOURD'HUI, pour tous.
 *
 * LA BORNE DROITE EST LA DATE DU JOUR, lue à l'affichage. Elle s'arrêtait à la
 * fin la plus tardive quand aucun mandat n'était en cours : la frise de
 * Bernard Cazeneuve finissait en 2017, celle de Jean-Luc Mélenchon en 2022, et
 * rien ne distinguait ces axes de ceux qui s'arrêtent aujourd'hui. Le lecteur
 * concluait que la carrière courait jusqu'à maintenant (signalé le 16/09/2026).
 * Mesuré ce jour-là sur les 23 candidats déclarés qui ont une frise : 4 axes
 * s'arrêtaient avant aujourd'hui — Cazeneuve, Royal, Philippot, Mélenchon.
 *
 * Le blanc à droite dit « rien de collecté depuis », ce qui est vrai des sources
 * que la fiche lit. La borne gauche reste le premier début observé, jamais une
 * année ronde inventée.
 *
 * Une fin postérieure à aujourd'hui — un mandat daté à l'avance — n'est pas
 * rognée : l'axe s'étend jusqu'à elle.
 */
export function bornesDuParcours(roles, aujourdhui = aujourdhuiISO()) {
  if (!roles.length) return null;
  const debuts = roles.map((r) => r.debut).filter(Boolean).sort();
  const fins = roles
    .map((r) => (r.actif || r.fin === FIN_OUVERTE ? null : r.fin))
    .filter(Boolean)
    .sort();
  const finMax = fins[fins.length - 1];
  return { debut: debuts[0], fin: finMax && finMax > aujourdhui ? finMax : aujourdhui };
}

export function positionSurAxe(date, bornes) {
  if (!bornes) return 0;
  const a = Date.parse(bornes.debut);
  const b = Date.parse(bornes.fin);
  const d = Date.parse(date === FIN_OUVERTE ? bornes.fin : date);
  if (!Number.isFinite(a) || !Number.isFinite(b) || b <= a || !Number.isFinite(d)) return 0;
  return Math.min(100, Math.max(0, ((d - a) / (b - a)) * 100));
}

/* ── Livrable : les fonctions qu'on choisit d'exercer ────────────────────────
 *
 * 124 mandats chez Guedj, dont 15 groupes d'études et 6 commissions d'enquête,
 * réduits à une puce par la fiche d'avant. Ce sont pourtant les seuls gestes
 * du corpus que personne n'impose : ils disent où quelqu'un choisit de passer
 * son temps. Une catégorie par bloc, jamais un total — un groupe d'amitié et
 * une commission d'enquête ne s'additionnent pas.
 */
/** Le nom de la chambre dans un titre de bloc — « Commissions · Assemblée
 *  nationale ». Distinct de `LIBELLE_PISTE`, qui nomme des colonnes et se lit
 *  « À l'Assemblée ». */
const NOM_DE_CHAMBRE = {
  [INSTITUTION_PARLEMENT]: 'Assemblée nationale',
  [INSTITUTION_SENAT]: 'Sénat',
  [INSTITUTION_PE]: 'Parlement européen',
};

export const CATEGORIES_FONCTIONS = [
    // La source range sous `commission` bien plus que les commissions
  // permanentes : commissions spéciales, groupes de travail, un comité
  // consultatif. Le titre reprend donc la catégorie telle qu'elle est, sans
  // promettre une taxonomie que le corpus ne porte pas (§2 règle 2).
  { cle: 'commission', titre: 'Commissions', banc: INSTITUTION_PARLEMENT },
  { cle: 'commission_enquete', titre: "Commissions d'enquête et commissions spéciales", banc: INSTITUTION_PARLEMENT },
  { cle: 'mission_information', titre: "Missions d'information", banc: INSTITUTION_PARLEMENT },
  { cle: 'groupe_etudes', titre: "Groupes d'études", banc: INSTITUTION_PARLEMENT },
  { cle: 'delegation', titre: 'Délégations', banc: INSTITUTION_PARLEMENT },
  { cle: 'extra_parlementaire', titre: 'Organismes extra-parlementaires', banc: INSTITUTION_PARLEMENT },
  { cle: 'groupe_amitie', titre: "Groupes d'amitié", banc: INSTITUTION_PARLEMENT },

  /* Ces deux-là sont rangés `categorie: "autre"` par la normalisation, et leur
     nature vraie vit dans `type_organe_source`. L'équivalent existe déjà à
     l'Assemblée — `delegation` — et une délégation européenne n'est pas moins
     une fonction exercée parce que le pivot n'a pas de case pour elle. */
  {
    cle: 'delegation_europeenne',
    typeOrgane: 'delegation_parlementaire_europeenne',
    titre: 'Délégations',
    banc: INSTITUTION_PARLEMENT,
  },
  {
    cle: 'groupe_liaison',
    typeOrgane: 'groupe_liaison_senatorial',
    titre: 'Groupes de liaison',
    banc: INSTITUTION_PARLEMENT,
  },

  /*
   * UNE FONCTION EXERCÉE NE L'EST PAS TOUJOURS AU PARLEMENT (#328).
   *
   * Un portefeuille ministériel est un siège occupé, au même titre qu'une
   * commission : il a un intitulé, des dates, une durée. Il manquait ici, et la
   * section ne montrait donc qu'une moitié des fonctions — 6 des 13 candidats
   * déclarés ont exercé au gouvernement.
   *
   * LE FILTRE PAR `fonction` EST SOURCÉ, pas lexical. La catégorie
   * `fonction_gouvernementale` mélange trois natures que le même champ sépare
   * déjà pour `appartenancesGouvernementales` :
   *
   *   `membre`     → l'appartenance au gouvernement. C'est l'ENVELOPPE, pas un
   *                  intitulé de fonction : elle nourrit la frise, et la
   *                  publier ici doublerait chaque portefeuille d'une ligne
   *                  « Gouvernement (BORNE) » qui ne dit pas ce qu'on y faisait ;
   *   `en mission` → un⋅e parlementaire en mission auprès d'un ministère, qui
   *                  RESTE parlementaire. La frise lui donne sa propre piste
   *                  depuis #328 ; elle a ici son propre bloc, pour la même
   *                  raison — la ranger avec les ministres serait le
   *                  contresens que la frise évite déjà ;
   *   le reste     → le portefeuille lui-même (Ministre, Secrétaire d'État,
   *                  Premier ministre).
   *
   * Filtrer sur le libellé (« Gouvernement (… ) ») aurait été une jointure par
   * ressemblance de chaîne, ce que `regrouper-nest-pas-joindre-639` interdit.
   */
  {
    cle: 'fonction_gouvernementale',
    titre: 'Portefeuilles ministériels',
    banc: INSTITUTION_GOUVERNEMENT,
    fonctions: (f) => f !== FONCTION_MEMBRE && f !== FONCTION_MISSION,
    sansMarque: true,
  },
  {
    cle: 'fonction_gouvernementale',
    titre: 'Missions auprès d’un ministère',
    suffixe: 'mission',
    banc: INSTITUTION_MISSION,
    fonctions: (f) => f === FONCTION_MISSION,
    sansMarque: true,
  },
];

/* ── Règle : le rôle ne s'affiche que lorsqu'il DISTINGUE ────────────────────
 *
 * `Membre` couvre 90,7 % des 14 128 mandats de commission du corpus, et 203 des
 * 225 des 13 candidats déclarés. L'écrire sur neuf lignes sur dix serait un mot
 * dont le lecteur ne tire rien — la règle 1 de #326 le disqualifie. Ce qui
 * s'affiche est ce qui distingue : une présidence, un rapport, un secrétariat.
 *
 * ⚠ La casse n'est pas normalisée à la source : `Membre`/`membre`,
 * `Vice-Président`/`vice-président`, `vice-présidente`. 48 des 225 mandats de
 * commission des 13 candidats déclarés sont en bas de casse. On normalise à
 * L'AFFICHAGE seulement : la donnée n'est pas touchée, et le défaut de collecte
 * reste lisible pour qui l'ouvre. Le dépôt a déjà tranché ce point côté fiches
 * de groupe — voir `normalisation-fonction-mandats-agreges`.
 */
const ROLES_PAR_DEFAUT = new Set(['membre', 'membre titulaire', 'membre de droit']);

export function roleDistinctif(fonction) {
  const brut = (fonction || '').trim();
  if (!brut || ROLES_PAR_DEFAUT.has(brut.toLowerCase())) return null;
  return brut.slice(0, 1).toUpperCase() + brut.slice(1).toLowerCase();
}

/* ── Règle : une durée de siège se compte en UNION d'intervalles ─────────────
 *
 * Le nombre affiché n'est PAS un compte d'enregistrements. La source réécrit un
 * même siège à chaque changement de composition : 27 entrées pour 5 ans 10 mois
 * continus à la commission des affaires sociales de Jérôme Guedj, dont aucune ne
 * dure un jour ; en face, 4 entrées pour 2 jours à la commission des lois. Le
 * compte ne distingue pas les deux, la durée si. C'est la même confusion que
 * #656 a séparée sur les fiches de groupe — « y siège » n'est pas « y est
 * passé » — vue depuis la fiche candidat.
 *
 * L'union, JAMAIS la somme : la fusion additive a laissé des doublons littéraux
 * (même début, fin décalée d'un jour), et la somme donnerait 9,5 ans là où il y
 * en a 5,8.
 *
 * Un mandat sans `debut` n'est comptable à aucune date : il ne compte pas, et il
 * ne vaut pas zéro non plus — il est simplement absent du calcul (§2 règle 5).
 */
const MS_PAR_JOUR = 86400000;
const JOURS_PAR_MOIS = 30.44;

export function aujourdhuiISO() {
  return new Date().toISOString().slice(0, 10);
}

export function joursCumules(mandats, aujourdhui = aujourdhuiISO()) {
  const intervalles = (mandats || [])
    .filter((m) => m.debut)
    .map((m) => [m.debut, m.actif || !m.fin ? aujourdhui : m.fin])
    .filter(([debut, fin]) => fin >= debut)
    .sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0));
  if (!intervalles.length) return 0;

  const ecart = (a, b) => Math.round((Date.parse(b) - Date.parse(a)) / MS_PAR_JOUR);
  let total = 0;
  let [debut, fin] = intervalles[0];
  for (const [d, f] of intervalles.slice(1)) {
    if (d <= fin) {
      if (f > fin) fin = f;
    } else {
      total += ecart(debut, fin);
      debut = d;
      fin = f;
    }
  }
  return total + ecart(debut, fin);
}

/* Une durée se lit en années et en mois, jamais en jours au-delà d'un mois : le
 * lecteur compare des sièges, pas des calendriers. En deçà, le jour reste la
 * seule unité honnête — « 0 mois » effacerait un passage réel. */
export function dureeDeSiege(jours) {
  if (jours < 31) return `${jours} jour${jours > 1 ? 's' : ''}`;
  const mois = Math.round(jours / JOURS_PAR_MOIS);
  const ans = Math.floor(mois / 12);
  const reste = mois % 12;
  if (!ans) return `${reste} mois`;
  const annees = `${ans} an${ans > 1 ? 's' : ''}`;
  return reste ? `${annees} ${reste} mois` : annees;
}

/* ── Règle : ce qui ressort dépasse la MOITIÉ du temps de mandat ─────────────
 *
 * Chaque catégorie montre ses trois fonctions les plus longues — toujours trois,
 * jamais une seule : un bloc à une grande ligne et un autre à trois petites
 * déséquilibraient la carte sans que la donnée le justifie.
 *
 * Une seule d'entre elles peut porter la marque, et c'est un FAIT, pas un seuil
 * choisi : la personne y a passé plus de la moitié de son temps de mandat. C'est
 * le test de majorité que #328 a déjà retenu pour les amendements (« ce dossier
 * porte plus que tous les autres réunis »), posé cette fois sur un dénominateur
 * qui en est un.
 *
 * LE DÉNOMINATEUR EST L'UNION DES SIÈGES ÉLECTIFS, et ce choix est le cœur de la
 * règle : on ne siège pas deux fois à la fois, donc c'est un vrai tout, et le
 * ratio est publiable (§2 règle 7). Le total des fonctions n'en serait pas un —
 * on appartient à treize groupes d'amitié simultanément, et leur somme fait
 * 33 ans sur une carrière de 19.
 *
 * Elle sait se taire, et c'est ce qui la rend utile : mesurée sur les 13 blocs
 * des deux profils de référence, elle parle 4 fois. Une règle qui ne peut pas se
 * taire ne dit rien quand elle parle (#326, règle 5).
 */
export const NB_FONCTIONS_MONTREES = 3;

export function fonctionsExercees(mandats, aujourdhui = aujourdhuiISO()) {
  const liste = mandats || [];
  const jours = joursCumules(
    liste.filter((m) => m.categorie === 'mandat_electif'),
    aujourdhui,
  );

  /* LA CHAMBRE D'UN ORGANE, ET POURQUOI ELLE SCINDE LE BLOC (#328).
   *
   * `banc` était écrit en dur à `parlement` pour les sept catégories
   * parlementaires, si bien qu'une commission du Parlement européen se peignait
   * de la teinte de l'Assemblée — le défaut même que #328 avait corrigé sur la
   * frise, et que cette section n'avait pas suivi. Mesuré le 13/09/2026 sur les
   * 21 fiches qui ont des fonctions : **4** les ont toutes européennes
   * (Glucksmann, Philippot, Bardella, Massard) et **3** mélangent les deux
   * chambres dans leur bloc « Commissions » (Maurel, Mélenchon, Le Pen).
   *
   * Pour ces trois-là, une seule teinte ne pouvait pas dire les deux — et le
   * titre annonçait « 13 intitulés » sans dire combien étaient européens, un
   * dénominateur qui agrège deux institutions (§2 règle 7). Scinder corrige les
   * deux d'un même geste.
   *
   * Le Sénat n'apparaît pas : ses organes ne sont pas collectés (#528). */
  const chambreDOrgane = (m) => {
    /* TROIS CHAMBRES, ET C'EST LE SÉNAT QUI L'A MONTRÉ (#885, 13/09/2026).
       La première version n'en connaissait que deux : un organe sénatorial
       retombait sur l'Assemblée, donc sur sa teinte et dans son compte. Mesuré
       le jour où le Sénat est entré — Bruno Retailleau porte 26 commissions
       sénatoriales contre 1 à l'Assemblée, 26 groupes d'études et 24 groupes
       d'amitié, tous sénatoriaux ; et le bloc « commission » de Jean-Luc
       Mélenchon en mêle TROIS : 31 à l'Assemblée, 10 au Parlement européen,
       8 au Sénat. `categorie_source` les sépare, et rien d'autre ne le fait. */
    if (m.categorie_source === 'europarl') return INSTITUTION_PE;
    if (m.categorie_source === 'senat') return INSTITUTION_SENAT;
    return INSTITUTION_PARLEMENT;
  };

  const blocs = CATEGORIES_FONCTIONS.flatMap(({ cle, titre, banc, fonctions, sansMarque, suffixe, typeOrgane }) => {
    /* UN ORGANE QUE LA CATÉGORIE N'ATTRAPE PAS (#885, 13/09/2026).
       87 mandats de candidats déclarés portent `categorie: "autre"` et
       n'apparaissaient donc NULLE PART — ni ici, ni ailleurs sur la fiche. Ce
       n'était pas un mauvais libellé, c'était un silence. Les deux que la
       source nomme sans ambiguïté comme des fonctions exercées entrent par
       leur `type_organe_source` ; le reste — un parti national, un groupe
       politique déjà porté par la frise, 20 organes sans type — n'entre pas :
       inventer une taxonomie que le corpus ne porte pas serait pire. */
    const retenus = liste.filter((x) => (typeOrgane
      ? x.type_organe_source === typeOrgane
      : x.categorie === cle) && (!fonctions || fonctions(x.fonction)));
    // Seules les fonctions PARLEMENTAIRES se scindent : un portefeuille
    // ministériel n'a pas de chambre, et lui en inventer une serait faux.
    const chambres = banc === INSTITUTION_PARLEMENT
      ? [...new Set(retenus.map(chambreDOrgane))]
      : [null];
    // Le titre ne porte la chambre que si la fiche en a PLUSIEURS : sur une
    // fiche qui n'a connu qu'un banc, la teinte suffit et le préciser ferait un
    // refrain.
    const nommerLaChambre = chambres.length > 1;
    return chambres.map((chambre) => {
    const parIntitule = new Map();
    for (const m of (chambre ? retenus.filter((x) => chambreDOrgane(x) === chambre) : retenus)) {
      const label = m.label || 'Intitulé non publié';
      if (!parIntitule.has(label)) parIntitule.set(label, []);
      parIntitule.get(label).push(m);
    }

    const lignes = [...parIntitule.entries()]
      .map(([label, lot]) => {
        const j = joursCumules(lot, aujourdhui);
        const roles = [...new Set(lot.map((m) => roleDistinctif(m.fonction)).filter(Boolean))];
        return {
          label,
          jours: j,
          duree: dureeDeSiege(j),
          roles: roles.length ? roles.sort().join(' · ') : null,
          marquee: false,
        };
      })
      .sort((a, b) => b.jours - a.jours || a.label.localeCompare(b.label, 'fr'));

    // La marque va nécessairement à la plus longue : dépasser la moitié du tout
    // interdit qu'une autre le fasse aussi.
    //
    // Elle ne s'applique PAS aux blocs gouvernementaux (`sansMarque`) : leur
    // dénominateur serait le temps de mandat ÉLECTIF, et un portefeuille ne
    // s'y compare pas. Édouard Philippe a été Premier ministre trois ans sans
    // siéger : la marque aurait dit « plus de la moitié » d'un tout dont il
    // était absent, ce que §2 règle 7 interdit — un ratio se publie avec son
    // numérateur ET son dénominateur, et celui-ci n'en est pas un.
    if (!sansMarque && lignes.length && jours > 0 && lignes[0].jours * 2 > jours) {
      lignes[0].marquee = true;
    }

    return {
      // Deux blocs partagent la catégorie `fonction_gouvernementale` : leur clé
      // les distingue, sinon React en monterait deux sous la même. La chambre
      // s'y ajoute depuis que les blocs parlementaires se scindent.
      cle: [cle, suffixe, chambre].filter(Boolean).join('_'),
      titre: nommerLaChambre && chambre ? `${titre} · ${NOM_DE_CHAMBRE[chambre]}` : titre,
      // Le BANC dont relève la fonction, pour que la vue reprenne la grammaire
      // de couleurs de la frise plutôt que d'en inventer une. Depuis le
      // 13/09/2026 il porte la CHAMBRE quand il y en a une : une commission
      // européenne se peignait de la teinte de l'Assemblée.
      banc: chambre ?? banc,
      nbIntitules: lignes.length,
      montrees: lignes.slice(0, NB_FONCTIONS_MONTREES),
      reste: lignes.slice(NB_FONCTIONS_MONTREES),
    };
    });
  }).filter((c) => c.nbIntitules > 0);

  return { mandat: { jours, duree: dureeDeSiege(jours) }, blocs };
}

/* ── Livrable : ce qu'il a proposé, par législature ──────────────────────────
 *
 * `role_signataire: "auteur_principal"` — la cosignature n'est pas la même
 * chose et ne se totalise pas avec (§6 : « une cosignature est UN amendement »,
 * et le taux d'adoption sur signatures n'est jamais publié).
 *
 * Le découpage par législature n'est pas décoratif : c'est le seul endroit où
 * la position déclarée du groupe peut accompagner le chiffre qu'elle explique.
 * 24 déposés / 6 adoptés comme député de la MAJORITÉ et 1 968 / 67 comme député
 * d'OPPOSITION ne sont pas deux performances, ce sont deux métiers. Sans la
 * mention sur la même ligne, le lecteur lit une incompétence.
 */
export const SORTS_AMENDEMENT = [
  'adopté',
  'rejeté',
  'tombé',
  'retiré',
  'irrecevable',
  'non_soutenu',
];

export const LIBELLE_SORT = {
  adopté: 'adoptés',
  rejeté: 'rejetés',
  tombé: 'tombés',
  retiré: 'retirés',
  irrecevable: 'irrecevables',
  non_soutenu: 'non soutenus',
  non_publie: 'sort non publié',
};

/*
 * `sort: null` n'est pas un sort : c'est l'absence de sort publié. Le confondre
 * avec « rejeté » publierait un zéro là où il n'y a pas de mesure (§2 règle 5).
 * Mesuré chez Guedj : 659 des 1 968 amendements de la XVIe législature.
 */
export const SORT_NON_PUBLIE = 'non_publie';

/* La matière d'un dépôt est la commission saisie au fond de son dossier. Quand
 * la source ne la donne pas — pas de dossier, ou pas de commission dans la
 * table — le dépôt garde sa place sous ce nom, qui dit l'absence au lieu de la
 * combler (§2 règle 5). */
export const MATIERE_NON_ETABLIE = 'Matière non établie';

/* ── Règle : ce que la Constitution a écarté avant discussion ────────────────
 *
 * `base_juridique_irrecevabilite` vaut « art. 40 » (dépense nouvelle sans
 * compensation) ou « art. 45 » (lien avec le texte discuté). C'est une
 * information sur la RÈGLE, pas sur la personne : 246 amendements écartés au
 * titre de l'article 40 disent qu'ils coûtaient de l'argent public, pas qu'ils
 * étaient mauvais. La phrase qui accompagne le chiffre est donc obligatoire —
 * le chiffre seul se lirait comme un compte d'échecs.
 */
export const BASES_IRRECEVABILITE = {
  'art. 40': {
    titre: "écartés au titre de l'article 40",
    explication: 'Dépense publique non compensée.',
  },
  'art. 45': {
    titre: "écartés au titre de l'article 45",
    explication: 'Amendement hors du sujet du texte.',
  },
};

/* ── Règle : un dossier se nomme, ou il ne se compte pas au lecteur ──────────
 *
 * « 6 dossiers sur 34 concentrent 2 206 de ses 2 429 amendements » décrivait la
 * FORME d'une distribution, pas ce sur quoi la personne a travaillé. Un ratio
 * de concentration ne se convertit en rien de lisible : la substance est dans
 * la liste des dossiers, pas dans leur nombre. La mesure est donc remplacée par
 * les dossiers eux-mêmes, nommés, avec leur compte.
 *
 * Un dossier n'est nommable que si la source le nomme. Deux chemins, et un
 * troisième qui n'en est pas un :
 *  - `textes[texte_vise].titre` de l'index par législature — le cas normal ;
 *  - le `texte_vise` lui-même quand ce n'en est PAS une référence de source :
 *    l'index publie parfois l'intitulé en clair à cette place (2 458 des 2 831
 *    dépôts de Jean-Luc Mélenchon sont visés par « Système universel de
 *    retraite », qui n'est la clé d'aucune entrée `textes`) ;
 *  - jamais la référence brute — « PRJLANR5L14B1395 » n'est pas un nom, et
 *    l'afficher donnerait au lecteur un identifiant à la place d'un texte.
 *
 * Le critère de distinction est structurel : une référence de source ne contient
 * pas d'espace, un intitulé en contient toujours.
 *
 * Ce que ça laisse à découvert est mesuré, et la page le dit plutôt que de le
 * combler : la XIVe législature n'a qu'UNE entrée `textes` dans l'index, donc
 * aucun des 12 dossiers de Xavier Bertrand ni aucun des 3 d'Édouard Philippe
 * n'est nommable (mesuré au SHA e40d0d3, 01/09/2026).
 */
const REFERENCE_DE_SOURCE = /^\S+$/;

export function nomDeDossier(dossierTitre, texteVise) {
  if (dossierTitre) return dossierTitre;
  if (texteVise && !REFERENCE_DE_SOURCE.test(texteVise)) return texteVise;
  return null;
}

/** Combien de dossiers nommés « L'essentiel » montre — les suivants ne sont pas
 * cachés, ils sont ailleurs sur la page, dans « ce qu'il a proposé ». */
export const NB_DOSSIERS_NOMMES = 3;

/** Combien de commissions la barre de répartition porte. Trois, parce qu'au-delà
 * les segments deviennent trop courts pour que leur longueur se compare — pas
 * parce qu'un quatrième compterait moins. Le total est publié à côté. */
export const NB_COMMISSIONS_MONTREES = 3;

/** L'institution que porte un amendement que l'index ne résout pas (#901). */
const INSTITUTION_AMENDEMENT_PE = 'parlement_europeen';

/** Un dépôt au Parlement européen. Le test porte sur ce que la donnée dit
 *  d'elle-même : aucun dépôt européen ne porte d'`amendement_id`, et tous
 *  portent `amendement_non_resolu.institution`. */
export const estAmendementEuropeen = (a) =>
  a?.amendement_non_resolu?.institution === INSTITUTION_AMENDEMENT_PE;

/** Rattache chaque dépôt européen à SON dossier, que `joinAmendements` laisse
 *  à `null` : la table des dossiers qu'il consulte est celle de l'AN, et une
 *  référence de procédure européenne (`2021/0136(COD)`) n'y figure pas. Le
 *  dossier n'est posé que s'il existe vraiment dans l'index européen — sinon la
 *  matière reste non établie, jamais déduite de l'intitulé (§2 règle 2). */
export function* rattacheDossierEuropeen(amendementsJoints, dossierEuropeen) {
  for (const a of amendementsJoints) {
    const dossier = a.texte_vise ? dossierEuropeen(a.texte_vise) : null;
    yield dossier
      ? { ...a, dossier_id: a.texte_vise, dossier_titre: dossier.titre ?? null }
      : a;
  }
}

/*
 * UNE SEULE PASSE sur les amendements, et jamais de forme plate rematérialisée.
 *
 * `joinAmendements` est un générateur pour une raison mesurée (#377, #431) :
 * étendre index × mapping a coûté un facteur ~21 et un OOM. Trois agrégats sont
 * donc calculés dans la même itération plutôt que par trois passes — un
 * générateur ne se relit pas, et le matérialiser pour pouvoir le relire
 * reconstruirait exactement ce que #431 supprime.
 *
 * `positionALaDate` rend la position déclarée du groupe à une date : c'est elle
 * qui accompagne le chiffre, jamais une moyenne de législature.
 *
 * `commissionDuDossier` rend la commission saisie au fond d'un dossier, lue
 * dans `pivot_data/commissions_dossiers.json` (#328). Absente, la répartition
 * n'est pas publiée — jamais remplacée par une déduction depuis l'intitulé.
 */
export function agregerAmendements(
  amendementsJoints,
  positionALaDate,
  commissionDuDossier = () => null,
) {
  const parLeg = new Map();
  const parBase = new Map();
  const parDossier = new Map();
  // La borne, comptée à part et jamais fondue dans le compte de dossiers : un
  // dépôt que la source ne rattache à aucun dossier n'est pas un dossier de
  // plus. Les deux compteurs vivaient sur une clé `dossier_id || texte_vise`,
  // qui publiait « 34 dossiers législatifs » là où il y en a 25 et 9 textes
  // visés orphelins — le défaut de clé `a or b` que décrit AGENTS.md §3a (#668).
  const textesSansDossier = new Set();
  let depotsSansDossier = 0;
  let totalAuteur = 0;
  // Le dépôt daté, par année et par dossier : la matière d'un dépôt est celle
  // de SON dossier, et elle ne se connaît qu'une fois la table des commissions
  // consultée — ce qui ne peut pas se faire dans la boucle sans la ralentir.
  const parAnnee = new Map();
  let depotsSansDate = 0;
  let adoptesTotal = 0;
  /* Combien de dépôts portent un sort PUBLIÉ. Sans ce compte, « 0 adopté »
     se lit « aucun n'a été adopté » là où la vérité est « le sort n'est publié
     pour aucun » — c'est le cas des 7 303 amendements européens, dont pas un
     ne porte de `sort` (mesuré le 13/09/2026). Une absence n'est pas un zéro
     (§2 règle 5). */
  let sortsPublies = 0;

  for (const a of amendementsJoints) {
    if (a.role_signataire !== 'auteur_principal') continue;
    totalAuteur += 1;

    const leg = a.legislature ?? 'inconnue';
    if (!parLeg.has(leg)) parLeg.set(leg, { legislature: leg, total: 0, sorts: new Map(), dates: [] });
    const bloc = parLeg.get(leg);
    bloc.total += 1;
    const sort = a.sort || SORT_NON_PUBLIE;
    bloc.sorts.set(sort, (bloc.sorts.get(sort) || 0) + 1);
    // Le compte d'adoptés porte sur TOUS les dépôts, y compris ceux qu'aucun
    // dossier ne rattache : la somme par dossier en perdrait 6 chez Jérôme
    // Guedj et 25 chez Laurent Wauquiez.
    if (sort === 'adopté') adoptesTotal += 1;
    if (a.sort) sortsPublies += 1;
    if (a.date) bloc.dates.push(a.date);

    if (a.base_juridique_irrecevabilite) {
      const base = a.base_juridique_irrecevabilite;
      parBase.set(base, (parBase.get(base) || 0) + 1);
    }

    // L'ANNÉE DU DÉPÔT, retenue ici et nulle part ailleurs : `joinAmendements`
    // est un générateur, il ne se relit pas (#431), et une seconde passe
    // reconstruirait exactement ce que cette contrainte supprime.
    if (a.date) {
      const an = a.date.slice(0, 4);
      if (!parAnnee.has(an)) parAnnee.set(an, new Map());
      // La matière n'est connue qu'après la boucle — la commission se lit par
      // dossier. On empile donc par dossier, et on la résout ensuite. La clé
      // est `dossier_id` SEUL, jamais un repli sur `texte_vise` : le défaut de
      // clé `a or b` de #668 vaut ici comme ailleurs, et un dépôt sans dossier
      // se range sous `null`, qui deviendra « matière non établie ».
      const parCle = parAnnee.get(an);
      parCle.set(a.dossier_id ?? null, (parCle.get(a.dossier_id ?? null) || 0) + 1);
    } else {
      depotsSansDate += 1;
    }

    if (a.dossier_id) {
      if (!parDossier.has(a.dossier_id)) {
        parDossier.set(a.dossier_id, {
          cle: a.dossier_id,
          nom: nomDeDossier(a.dossier_titre, a.texte_vise),
          n: 0,
          adoptes: 0,
          dateMin: null,
        });
      }
      const d = parDossier.get(a.dossier_id);
      d.n += 1;
      if (sort === 'adopté') d.adoptes += 1;
      if (a.date && (d.dateMin === null || a.date < d.dateMin)) d.dateMin = a.date;
    } else {
      depotsSansDossier += 1;
      if (a.texte_vise) textesSansDossier.add(a.texte_vise);
    }
  }

  const ordre = [...SORTS_AMENDEMENT, SORT_NON_PUBLIE];
  const legislatures = [...parLeg.values()]
    .map((bloc) => {
      bloc.dates.sort();
      const mediane = bloc.dates[Math.floor(bloc.dates.length / 2)] ?? null;
      return {
        legislature: bloc.legislature,
        total: bloc.total,
        position: mediane ? positionALaDate(mediane) : null,
        sorts: ordre
          .filter((s) => bloc.sorts.has(s))
          .map((s) => ({ cle: s, label: LIBELLE_SORT[s], n: bloc.sorts.get(s) })),
      };
    })
    .sort((a, b) => Number(a.legislature) - Number(b.legislature));

  const irrecevabilites = [...parBase.entries()]
    .filter(([base]) => BASES_IRRECEVABILITE[base])
    .map(([base, n]) => ({ base, n, ...BASES_IRRECEVABILITE[base] }))
    .sort((a, b) => b.n - a.n);

  // Les dossiers, nommés quand la source les nomme — et le compte de ce qu'elle
  // ne nomme pas, qui reste visible au lieu d'être absorbé dans le total.
  const classes = [...parDossier.values()].sort((a, b) => b.n - a.n || a.cle.localeCompare(b.cle));
  const nommes = classes.filter((d) => d.nom);

  // La commission SAISIE AU FOND de chaque dossier, comptée en dossiers et
  // jamais en dépôts : un dossier très amendé ne pèse pas plus lourd qu'un
  // autre dans la répartition, sans quoi la barre mesurerait un épisode de
  // dépôt en masse (574 des 2 429 dépôts de Jérôme Guedj, 23,6 %, portent sur
  // le seul PLFRSS 2023) au lieu d'une manière de travailler.
  //
  // Départage alphabétique à égalité — jamais l'ordre d'insertion, qui rendrait
  // une égalité comme une avance. Laurent Wauquiez a 4 et 4 en tête : c'est la
  // DONNÉE qui ne produit pas de tendance, et la barre le montre en n'en
  // montrant pas.
  const parCommission = new Map();
  let dossiersSansCommission = 0;
  for (const d of classes) {
    const commission = commissionDuDossier(d.cle);
    const sigle = commission?.sigle || commission?.nom || null;
    if (!sigle) {
      dossiersSansCommission += 1;
      continue;
    }
    if (!parCommission.has(sigle)) parCommission.set(sigle, { sigle, nom: commission.nom ?? null, n: 0 });
    parCommission.get(sigle).n += 1;
  }
  const commissions = [...parCommission.values()].sort(
    (a, b) => b.n - a.n || a.sigle.localeCompare(b.sigle, 'fr'),
  );

  /* ── LA CHUTE : comment le total s'est construit, année par année ─────────
   *
   * Une marche par année CIVILE, découpée par matière, et une barre de total
   * qui repart du sol. L'axe est le calendrier : une année sans dépôt garde sa
   * place et son palier — « il n'a rien déposé en 2019 » n'est pas « 2019
   * n'existe pas ».
   *
   * DEUX MESURES, PARCE QU'ELLES NE SE DÉDUISENT PAS L'UNE DE L'AUTRE. Le
   * nombre d'amendements et le nombre de dossiers amendés répondent à deux
   * questions — 2 831 dépôts sur 25 dossiers chez Jean-Luc Mélenchon. Les deux
   * sont publiés côte à côte plutôt qu'en rapport : §6 interdit le taux.
   *
   * LE DOMAINE EST L'UNION DES DEUX, jamais recalculé à la bascule : les dépôts
   * de Laurent Wauquiez commencent en 2012, ses dossiers datés en 2024, et un
   * axe qui bouge cesse d'être comparable.
   *
   * LA MATIÈRE EST CELLE DU DOSSIER, et l'absence en est une (§2 règle 5) : un
   * dépôt qu'aucun dossier ne rattache, ou dont le dossier n'a pas de
   * commission saisie au fond dans la table, tombe dans « matière non
   * établie » — compté, jamais réparti au prorata ni deviné depuis l'intitulé.
   */
  const matiereDuDossier = (cle) => {
    if (!cle) return null;
    const commission = commissionDuDossier(cle);
    return commission?.sigle || commission?.nom || null;
  };
  const totauxDepots = new Map();
  const totauxDossiers = new Map();
  const chuteParAnnee = new Map();
  for (const [an, parCle] of parAnnee) {
    const bloc = new Map();
    for (const [cle, n] of parCle) {
      const m = matiereDuDossier(cle) || MATIERE_NON_ETABLIE;
      bloc.set(m, (bloc.get(m) || 0) + n);
      totauxDepots.set(m, (totauxDepots.get(m) || 0) + n);
    }
    chuteParAnnee.set(an, bloc);
  }
  // Le dossier compte UNE fois, l'année de son premier dépôt — jamais une fois
  // par année où il reçoit un amendement, qui gonflerait le total.
  const dossiersParAnnee = new Map();
  for (const d of parDossier.values()) {
    if (!d.dateMin) continue;
    const an = d.dateMin.slice(0, 4);
    const m = matiereDuDossier(d.cle) || MATIERE_NON_ETABLIE;
    if (!dossiersParAnnee.has(an)) dossiersParAnnee.set(an, new Map());
    const bloc = dossiersParAnnee.get(an);
    bloc.set(m, (bloc.get(m) || 0) + 1);
    totauxDossiers.set(m, (totauxDossiers.get(m) || 0) + 1);
  }

  const annees = [...new Set([...chuteParAnnee.keys(), ...dossiersParAnnee.keys()])].sort();
  const chute = annees.length
    ? {
        // L'ordre des matières — donc les teintes — est fixé une fois par le
        // volume de DÉPÔTS : recalculé à chaque mesure, le bouton rebattrait
        // les couleurs et deux lectures cesseraient de se comparer.
        matieres: [...new Set([...totauxDepots.keys(), ...totauxDossiers.keys()])].sort(
          (a, b) => (totauxDepots.get(b) || 0) - (totauxDepots.get(a) || 0)
            || a.localeCompare(b, 'fr'),
        ),
        annees: anneesPleines(annees),
        depots: serieParAnnee(anneesPleines(annees), chuteParAnnee),
        dossiers: serieParAnnee(anneesPleines(annees), dossiersParAnnee),
        totauxDepots: Object.fromEntries(totauxDepots),
        totauxDossiers: Object.fromEntries(totauxDossiers),
        totalDepots: [...totauxDepots.values()].reduce((s2, v) => s2 + v, 0),
        totalDossiers: [...totauxDossiers.values()].reduce((s2, v) => s2 + v, 0),
        // La borne se déclare : un dépôt sans date ne figure sur aucune marche.
        sansDate: depotsSansDate,
        // Les dossiers derrière chaque matière, pour que le clic réponde
        // « lesquels » et pas seulement « combien ». `adoptes` porte le fait
        // qui compte — au moins un amendement entré dans le texte — et jamais
        // un rapport à autre chose (§6).
        dossiersParMatiere: [...parDossier.values()].reduce((acc, d) => {
          const m = matiereDuDossier(d.cle) || MATIERE_NON_ETABLIE;
          (acc[m] = acc[m] || []).push({
            cle: d.cle, nom: d.nom, n: d.n, adoptes: d.adoptes, annee: d.dateMin?.slice(0, 4) ?? null,
          });
          return acc;
        }, {}),
      }
    : null;

  const dossiers = classes.length || depotsSansDossier
    ? {
        distincts: classes.length,
        depots: classes.reduce((s, d) => s + d.n, 0),
        nommes: nommes.slice(0, NB_DOSSIERS_NOMMES),
        distinctsNommes: nommes.length,
        depotsNommes: nommes.reduce((s, d) => s + d.n, 0),
        commissions,
        dossiersAvecCommission: commissions.reduce((s, c) => s + c.n, 0),
        dossiersSansCommission,
        // La borne se déclare, elle ne se comble pas (§2 règle 5). Elle est
        // grande : 2 499 des 2 831 dépôts de Jean-Luc Mélenchon, faute d'index
        // de la XIVe et de textes visés non résolus (issue #696).
        sansDossier: { depots: depotsSansDossier, textesVises: textesSansDossier.size },
      }
    : null;

  return {
    totalAuteur, adoptes: adoptesTotal, sortsPublies, legislatures, irrecevabilites, dossiers, chute,
  };
}

/* Les années civiles d'un bout à l'autre, trous compris : c'est la seule façon
 * de distinguer « rien déposé cette année-là » de « cette année n'existe pas ». */
export function anneesPleines(annees) {
  if (!annees.length) return [];
  const a0 = Number(annees[0]);
  const a1 = Number(annees[annees.length - 1]);
  const pleines = [];
  for (let a = a0; a <= a1; a += 1) pleines.push(String(a));
  return pleines;
}

function serieParAnnee(annees, parAnnee) {
  return annees.map((an) => ({
    annee: an,
    parts: [...(parAnnee.get(an) || new Map()).entries()].map(([matiere, n]) => ({ matiere, n })),
  }));
}

/* ── Règle : un texte porté n'est publié qu'à partir de l'examen en commission
 *
 * AGENTS.md §6 : « `textes_portes[]` en deçà du seuil — non publié par défaut ».
 * Les deux maquettes d'août affichaient les textes simplement DÉPOSÉS ; c'était
 * une violation de la règle. Ce qui est écarté est compté et sa raison dite —
 * l'écarter en silence transformerait une règle éditoriale en trou de données.
 */
export const STADES_PUBLIES = [
  'examine_commission',
  'inscrit_ordre_jour',
  'discute_seance',
  'adopte',
  'promulgue',
];

export const LIBELLE_STADE = {
  depose: 'déposé',
  examine_commission: 'examiné en commission',
  inscrit_ordre_jour: "inscrit à l'ordre du jour",
  discute_seance: 'discuté en séance',
  adopte: 'adopté',
  promulgue: 'promulgué',
  /* LES SEIZE STADES EUROPÉENS, DANS LEUR PROPRE NOMENCLATURE (#901). Ils ne
     se traduisent pas en stades français — « procédure achevée » recouvre
     l'adoption comme l'échec, et « procédure rejetée » existe à côté — et ils
     ne s'ordonnent pas entre eux. Sans libellé, la fiche afficherait
     `ue_procedure_achevee` tel quel. Chaque ligne suit le libellé de la source
     (`STADE_UE_PAR_LIBELLE_SOURCE`, `src/normalize_parltrack_dumps.py`), sans
     rien y ajouter : « achevée » n'est pas « adoptée ». */
  ue_procedure_achevee: 'procédure achevée',
  ue_procedure_achevee_acte_delegue_en_vigueur: 'procédure achevée, acte délégué en vigueur',
  ue_procedure_achevee_acte_delegue_rejete: 'procédure achevée, acte délégué rejeté',
  ue_procedure_achevee_attente_publication_jo:
    'procédure achevée, en attente de publication au Journal officiel',
  ue_procedure_caduque_ou_retiree: 'procédure caduque ou retirée',
  ue_procedure_rejetee: 'procédure rejetée',
  ue_phase_preparatoire_parlement: 'phase préparatoire au Parlement',
  ue_attente_decision_commission: 'en attente d’une décision de la commission',
  ue_attente_decision_finale: 'en attente de la décision finale',
  ue_attente_position_parlement_1re_lecture:
    'en attente de la position du Parlement en 1re lecture',
  ue_attente_parlement_1re_lecture:
    'en attente du Parlement — 1re lecture, lecture unique ou 1re étape budgétaire',
  ue_attente_parlement_2e_lecture: 'en attente du Parlement — 2e lecture',
  ue_attente_vote_parlement: 'en attente du vote du Parlement',
  ue_attente_debat_vote_pleniere: 'en attente du débat ou du vote en plénière',
  ue_attente_position_conseil_1re_lecture: 'en attente de la position du Conseil en 1re lecture',
  ue_attente_decision_conseil_2e_lecture: 'en attente de la décision du Conseil — 2e lecture',
};

/* ── Le seuil §6, versant européen ───────────────────────────────────────────
 *
 * `STADES_PUBLIES` ci-dessus est un ORDRE : un texte est publié s'il a atteint
 * au moins l'examen en commission. Aucune valeur européenne n'a de rang dans
 * cette liste, et leur en donner un publierait un avancement que la source
 * n'établit pas. `AGENTS.md` §6 pose donc la règle PAR EXCLUSION : tout stade
 * `ue_` est public SAUF `ue_phase_preparatoire_parlement`, le seul qui dise
 * « pas encore examiné nulle part » — le contrepoint de `depose`.
 *
 * Écrire la règle dans l'autre sens (une liste de stades publiés) ferait
 * disparaître en silence tout stade que la source ajouterait ensuite ; ici, il
 * arrive publié, et c'est la conséquence voulue de l'arbitrage du 14/09/2026.
 */
export const STADES_UE_NON_PUBLIES = ['ue_phase_preparatoire_parlement'];

export function estStadeUe(stade) {
  return typeof stade === 'string' && stade.startsWith('ue_');
}

export function estStadeUePublie(stade) {
  return estStadeUe(stade) && !STADES_UE_NON_PUBLIES.includes(stade);
}

/* Pourquoi un texte européen ne porte pas de stade — trois causes, jamais
 * confondues (`deux-fabriques-textes-portes-europeens-901`). La cascade en
 * fait autant de branches basses : « la source se tait sur ce dossier » et
 * « il n'y a pas de dossier » ne sont pas le même fait (§2 règle 5). */
export const LIBELLE_MOTIF_STADE_UE = {
  activite_sans_dossier: 'sans dossier rattaché',
  source_sans_stade: 'stade non publié par la source',
  stade_source_inconnu: 'stade inconnu de notre table',
};

export const LIBELLE_ROLE_TEXTE = {
  // #689 a scindé `auteur`, qui couvrait deux actes de nature différente. Les
  // trois valeurs neuves DOIVENT figurer ici : sans libellé, la fiche
  // afficherait la clé technique telle quelle dès le premier run qualifié.
  //
  // Le libellé nomme QUI EST À L'ORIGINE du texte, pas le terme juridique. Le
  // terme officiel — « projet » contre « proposition » — est contre-intuitif :
  // il ne dit pas ce qu'on propose mais qui le dépose, et un lecteur qui ne
  // connaît pas l'article 39 lit exactement l'inverse. « Résolution » est pire
  // encore : il se lit comme un morceau de loi, alors qu'une résolution ne
  // crée aucune règle. Mesuré sur les 423 textes portés des 13 candidats
  // déclarés : 313 projets de loi, 78 propositions, 26 résolutions.
  //
  // « à l'initiative du gouvernement » et « issue d'un(e) parlementaire »
  // disent l'initiative, JAMAIS la chambre de dépôt : 122 des 313 projets ont
  // été déposés au Sénat sans cesser d'être des textes du gouvernement, et 35
  // des 78 propositions sont sénatoriales (Bruno Retailleau). « Issue de
  // l'Assemblée nationale » aurait donc été faux 157 fois sur 391.
  //
  // La parenthèse de la résolution énumère les deux procédures que la source
  // distingue elle-même (`procedureParlementaire.code`) sans trancher laquelle
  // s'applique au texte affiché : 10 des 26 sont des résolutions de l'article
  // 34-1 (l'Assemblée déclare une position), 16 relèvent du code 8 générique,
  // dont les intitulés sont des demandes d'enquête. « Demande », et non
  // « décision » : 2 des 26 seulement portent le stade `adopte`, et un texte
  // déposé sans être voté n'a rien décidé (AGENTS.md §2 règle 5).
  initiateur_projet_de_loi: "Projet de loi à l'initiative du gouvernement",
  auteur_proposition_de_loi: "Proposition de loi issue d'un(e) parlementaire",
  auteur_proposition_de_resolution:
    'Résolution (prise de position ou demande procédurale)',
  auteur: 'Auteur',
  rapporteur: 'Rapporteur',
  'co-rapporteur': 'Co-rapporteur',
};

/*
 * Un projet de loi est un texte du GOUVERNEMENT, porté comme ministre — pas une
 * proposition déposée comme parlementaire.
 *
 * `nature_texte` (#689) est le fait sourcé : le préfixe de l'uid du document
 * déposé, lu dans l'archive AN. Il fait foi dès qu'il est présent, y compris
 * contre l'intitulé.
 *
 * Le repli par intitulé est CONSERVÉ, et il est déclaré : le corpus publié ne
 * porte `nature_texte` qu'à partir du run qui recollecte les dossiers, et le
 * retirer aujourd'hui afficherait 0 projet de loi là où la page en signale 13.
 * Il ne tient que sur les XVI/XVII — les dossiers de la XV portent des
 * intitulés descriptifs (« Bioéthique », « CETA ») et il en manque 283 sur 304.
 * Condition de retrait : la §5c du quality gate à 0 initiateur sans nature.
 */
const PROJET_DE_LOI = /^projet de loi\b/;

export function estProjetDeLoi(texte) {
  if (texte?.nature_texte) return texte.nature_texte === 'projet_de_loi';
  return PROJET_DE_LOI.test(normalizeLabel(texte?.titre));
}

/*
 * De quelle institution un texte porté relève — la SEULE attribution de rôle du
 * dépôt qui soit un fait sourcé texte par texte (#689).
 *
 * DEUX CHAMPS, PAS UN. La nature ne suffit pas : Gabriel Attal est RAPPORTEUR
 * d'un projet de loi, ce qui est un acte parlementaire sur un texte du
 * gouvernement. Le ranger au gouvernement sur sa seule nature serait le
 * contresens exact que #689 a corrigé dans l'autre sens. `role` est lu d'abord,
 * et il est lui-même dérivé de la nature par #689 — sauf `rapporteur` /
 * `co-rapporteur`, qui existent indépendamment d'elle.
 *
 * TROIS ÉTATS, PAS DEUX : quand ni le rôle ni la nature ne tranchent (4 des 423
 * textes portés des 13 candidats déclarés, tous `role: auteur` sans nature), le
 * texte n'est attribué à AUCUNE institution. Ranger par défaut au parlement
 * inventerait une initiative personnelle (§2 règle 5).
 *
 * `estProjetDeLoi` ci-dessus répond à une AUTRE question — « de quelle nature
 * est ce texte » — et reste indifférent au rôle : les deux ne se confondent pas
 * et ne se remplacent pas.
 */
const ROLE_INSTITUTION = {
  initiateur_projet_de_loi: INSTITUTION_GOUVERNEMENT,
  auteur_proposition_de_loi: INSTITUTION_PARLEMENT,
  auteur_proposition_de_resolution: INSTITUTION_PARLEMENT,
  rapporteur: INSTITUTION_PARLEMENT,
  'co-rapporteur': INSTITUTION_PARLEMENT,
};

export function institutionDuTexte(texte) {
  const parLeRole = ROLE_INSTITUTION[texte?.role];
  if (parLeRole) return parLeRole;
  const nature = texte?.nature_texte;
  if (nature === 'projet_de_loi') return INSTITUTION_GOUVERNEMENT;
  if (nature === 'proposition_de_loi' || nature === 'proposition_de_resolution') {
    return INSTITUTION_PARLEMENT;
  }
  if (nature) return null;
  // Repli d'intitulé, déclaré : il ne tranche que vers le gouvernement — un
  // intitulé qui ne commence pas par « projet de loi » ne prouve pas une
  // initiative parlementaire.
  return PROJET_DE_LOI.test(normalizeLabel(texte?.titre)) ? INSTITUTION_GOUVERNEMENT : null;
}

/*
 * L'ÉCHELLE DE LA CASCADE EST CELLE QUE LE CORPUS REMPLIT.
 *
 * Un cran n'existe que si au moins un texte S'Y ARRÊTE. `inscrit_ordre_jour`
 * est publié par le schéma et porté par AUCUN des 423 textes des 13 candidats
 * déclarés : le dessiner ouvrirait une colonne que rien ne franchit et que
 * rien ne quitte. La règle est générale, pas une exception codée en dur — le
 * jour où un texte s'y arrête, le cran apparaît, et la négation de la porte
 * précédente devient « non inscrit à l'ordre du jour » toute seule.
 *
 * Elle garantit aussi ce dont la mise en page a besoin : les crans vifs
 * forment un préfixe sans trou, donc aucun lien ne vise un nœud absent.
 */
export function textesPortes(
  textes,
  commissionDuDossier = () => null,
  dossierEuropeen = () => null,
  documentEuropeen = () => null,
) {
  /* DEUX POPULATIONS, DEUX FIGURES, ET AUCUN TOTAL COMMUN (#901).
   *
   * Les textes portés au Parlement européen étaient comptés dans `total` et
   * rangés dans `ecartes` : Emmanuel Maurel publiait « 45 autres textes portés
   * dont la source ne publie pas le stade », alors que ces 45 sont ses textes
   * EUROPÉENS, dont 37 portent un stade que la source publie. Le commutateur
   * de la section les sépare ; les deux jeux de chiffres ne s'additionnent
   * nulle part. */
  const toutes = textes || [];
  const liste = toutes.filter((t) => t.institution !== INSTITUTION_PE_SOURCE);
  const europeens = toutes.filter((t) => t.institution === INSTITUTION_PE_SOURCE);
  const publies = liste.filter((t) => STADES_PUBLIES.includes(t.stade_procedural));
  const ecartes = liste.filter((t) => !STADES_PUBLIES.includes(t.stade_procedural));
  const parStade = new Map();
  for (const t of publies) parStade.set(t.stade_procedural, (parStade.get(t.stade_procedural) || 0) + 1);

  return {
    total: liste.length,
    publies: publies
      .map((t) => ({
        titre: t.titre,
        role: LIBELLE_ROLE_TEXTE[t.role] || t.role || 'Rôle non publié',
        // La CLÉ brute à côté du libellé : composer une phrase sur le libellé
        // la casserait au premier changement de mot (`LIBELLE_ROLE_TEXTE`).
        roleCle: t.role ?? null,
        stade: LIBELLE_STADE[t.stade_procedural] || t.stade_procedural,
        stadeCle: t.stade_procedural,
        legislature: t.legislature ?? null,
        dateMin: t.date_min ?? null,
        dateMax: t.date_max ?? null,
        projetDeLoi: estProjetDeLoi(t),
        institution: institutionDuTexte(t),
        // La CHAMBRE d'où vient le texte, à côté du banc qui le signe : une
        // proposition de résolution européenne n'est pas une proposition
        // déposée à l'Assemblée, et 405 des 423 textes portés publiés le sont.
        europeen: t.institution === INSTITUTION_PE_SOURCE,
        sourceUrl: t.source_url ?? null,
      }))
      .sort((a, b) => String(b.dateMax || '').localeCompare(String(a.dateMax || ''))),
    repartition: STADES_PUBLIES.filter((s) => parStade.has(s)).map((s) => ({
      cle: s,
      label: LIBELLE_STADE[s],
      n: parStade.get(s),
    })),
    promulgues: parStade.get('promulgue') || 0,
    projetsDeLoi: liste.filter(estProjetDeLoi).length,
    // Les textes publiés que la source ne qualifie pas : ni projet, ni
    // proposition. Comptés, jamais rangés par défaut d'un côté (§2 règle 5).
    sansNature: publies.filter((t) => institutionDuTexte(t) === null).length,
    ecartes: {
      total: ecartes.length,
      deposes: ecartes.filter((t) => t.stade_procedural === 'depose').length,
      sansStade: ecartes.filter((t) => !t.stade_procedural).length,
    },
    cascade: cascadeDesTextes(publies, commissionDuDossier),
    europe: textesEuropeens(europeens, dossierEuropeen, documentEuropeen),
  };
}

/* ── Les textes portés au Parlement européen ─────────────────────────────────
 *
 * MÊME FIGURE, UNE SEULE PORTE. Le détail de la mise en page vit dans
 * `cascadeTextes.disposerCascadeUE` ; ici on produit ce qu'elle dessine.
 *
 * L'AXE EST LE THÈME, ET UN TEXTE EN A PLUSIEURS (arbitré le 17/09/2026, sur
 * maquettes rendues sur la cascade réelle — `axe-europeen-prorata-domaines-901`).
 * La commission saisie au fond, l'axe d'avant, ne couvrait que 17 des 383 textes
 * portés européens des candidats déclarés. Le thème est désormais :
 *
 *   - le DOMAINE EuroVoc de chaque matière du document (`documents_europeens.json`,
 *     `matieres[].domaine`), tel que le thésaurus le publie, « Géographie »
 *     comprise — aucun domaine n'est écarté ;
 *   - à défaut, la FAMILLE OEIL du dossier (`dossiers_europeens.json`,
 *     `familles[]`), en anglais, telle que la source la publie ;
 *   - à défaut, la matière n'est pas établie (§2 règle 5).
 *
 * UN TEXTE VAUT UNE UNITÉ, RÉPARTIE AU PRORATA DE SES CONCEPTS. Un texte porte
 * 6,9 concepts EuroVoc en moyenne, et 326 des 345 textes classés touchent au
 * moins deux domaines : lui choisir UN domaine écrasait le thème minoritaire,
 * ce que la propriétaire a refusé. Trois concepts « Finances » et un « Droit »
 * envoient ¾ d'unité depuis Finances et ¼ depuis Droit ; les familles OEIL se
 * partagent l'unité à parts égales. Les stades à droite comptent donc toujours
 * des textes entiers.
 *
 * AUCUN COMPTE N'EST AFFICHÉ PAR THÈME : une « part de texte » porterait à
 * confusion auprès d'un public qui ne connaît pas la structure des données
 * (arbitré le 17/09/2026). Le thème se lit par la largeur de son ruban, et le
 * clic liste les textes qui le touchent.
 */
const CHEMIN_DOCEO = 'www.europarl.europa.eu/doceo/document';

/** `…/doceo/document/RC-9-2024-0227_EN.html` → `RC-9-2024-0227` — la même
 *  lecture que `src/documents_europeens.py`, schéma retiré : le corpus mêle
 *  `http://` et `https://`. */
export function referenceDocumentDoceo(url) {
  if (typeof url !== 'string' || !url.includes(CHEMIN_DOCEO)) return null;
  const nom = url.split(CHEMIN_DOCEO)[1].replace(/^\/+|\/+$/g, '').split('.')[0];
  return nom.replace(/_(EN|FR)$/, '') || null;
}

/* Le libellé d'un domaine EuroVoc, verbatim, se publie en capitales et numéroté
 * (« 08 RELATIONS INTERNATIONALES »). L'affichage retire le numéro et la casse ;
 * il n'écrit aucun mot. */
export function libelleDomaine(libelle) {
  const nu = String(libelle).replace(/^\d+\s+/, '').toLocaleLowerCase('fr');
  return nu.charAt(0).toLocaleUpperCase('fr') + nu.slice(1);
}

/** Les thèmes d'un texte et la part de chacun : `[[thème, part], …]`, parts
 *  sommant à 1. */
export function themesEuropeens(texte, dossierEuropeen = () => null, documentEuropeen = () => null) {
  const document = documentEuropeen(referenceDocumentDoceo(texte.source_url));
  const domaines = (document?.matieres || [])
    .map((m) => m.domaine?.libelle)
    .filter(Boolean)
    .map(libelleDomaine);
  if (domaines.length) {
    const parts = new Map();
    for (const d of domaines) parts.set(d, (parts.get(d) || 0) + 1 / domaines.length);
    return [...parts.entries()];
  }
  const dossier = texte.reference_dossier ? dossierEuropeen(texte.reference_dossier) : null;
  const familles = (dossier?.familles || []).map((f) => f.libelle).filter(Boolean);
  if (familles.length) return familles.map((f) => [f, 1 / familles.length]);
  return [[MATIERE_NON_ETABLIE, 1]];
}

/* LA NATURE D'UN TEXTE, lue dans le type de procédure que la source publie pour
 * son dossier — jamais dans l'intitulé. Libellés et forme arbitrés le
 * 17/09/2026 : des puces au-dessus de la figure, « Toutes natures » par défaut. */
export const NATURES_UE = [
  { cle: 'legislatif', libelle: 'Législatif', procedures: ['COD', 'CNS', 'INL', 'DEA'] },
  { cle: 'rapport', libelle: 'Rapports d’initiative et institutionnels', procedures: ['INI', 'INS'] },
  { cle: 'resolution', libelle: 'Résolutions d’actualité', procedures: ['RSP'] },
  { cle: 'sans_dossier', libelle: 'Propositions de résolution sans dossier', procedures: [] },
];
/* Un dossier hors index, ou d'une procédure que la liste ne nomme pas, n'est
 * rangé dans aucune nature : il reste dans « Toutes natures », et nulle part
 * ailleurs (§2 règle 5). */
export function natureEuropeenne(texte, dossierEuropeen = () => null) {
  if (!texte.reference_dossier) return 'sans_dossier';
  const procedure = String(dossierEuropeen(texte.reference_dossier)?.type_procedure || '').slice(0, 3);
  return NATURES_UE.find((n) => n.procedures.includes(procedure))?.cle ?? null;
}

export function textesEuropeens(
  textes,
  dossierEuropeen = () => null,
  documentEuropeen = () => null,
  parNature = true,
) {
  const liste = textes || [];
  const nonPublies = liste.filter((t) => STADES_UE_NON_PUBLIES.includes(t.stade_procedural));
  const dessines = liste.filter((t) => !STADES_UE_NON_PUBLIES.includes(t.stade_procedural));
  const issueDe = (t) => (estStadeUePublie(t.stade_procedural)
    ? t.stade_procedural
    : t.stade_procedural_non_resolu?.motif || 'source_sans_stade');
  const libelleIssue = (cle) => LIBELLE_MOTIF_STADE_UE[cle] || LIBELLE_STADE[cle] || cle;

  const flux = new Map();
  const poids = new Map();
  let sansMatiere = 0;
  const textesListe = dessines.map((t) => {
    const themes = themesEuropeens(t, dossierEuropeen, documentEuropeen);
    if (themes.length === 1 && themes[0][0] === MATIERE_NON_ETABLIE) sansMatiere += 1;
    const issue = issueDe(t);
    for (const [theme, part] of themes) {
      const cle = `${theme}${SEPARATEUR_FLUX}${issue}`;
      flux.set(cle, (flux.get(cle) || 0) + part);
      poids.set(theme, (poids.get(theme) || 0) + part);
    }
    return {
      titre: t.titre,
      // Le thème le plus lourd sert de clé de tri ; la SÉLECTION lit `themes`,
      // pour qu'un texte se retrouve sous chacun de ses thèmes.
      matiere: [...themes].sort((a, b) => b[1] - a[1])[0][0],
      themes: themes.map(([theme]) => theme),
      stadeCle: issue,
      stade: libelleIssue(issue),
      sortCle: t.sort ?? null,
      sortMotif: t.sort_non_resolu?.motif ?? null,
      role: LIBELLE_ROLE_TEXTE[t.role] || t.role || null,
      url: t.source_url ?? null,
      an: t.date_max ? String(t.date_max).slice(0, 4) : null,
      // Aucun texte européen n'est un projet de loi : la liste garde donc une
      // seule colonne, et `ListeCascade` n'en ouvre pas une vide.
      projetDeLoi: false,
      europeen: true,
    };
  });

  /* L'ORDRE DES ISSUES N'EST PAS UNE ÉCHELLE — c'est l'ordre d'affichage, et
   * il sert d'index à la sélection. Les branches basses d'abord, pour que le
   * rang 0 soit ce qui n'a pas de stade ; les stades publiés ensuite, dans
   * l'ordre du schéma, pour que deux fiches ne les empilent pas différemment. */
  const basses = Object.keys(LIBELLE_MOTIF_STADE_UE)
    .filter((m) => textesListe.some((t) => t.stadeCle === m));
  const hautes = Object.keys(LIBELLE_STADE)
    .filter((st) => estStadeUePublie(st) && textesListe.some((t) => t.stadeCle === st));

  return {
    total: liste.length,
    publies: dessines.filter((t) => estStadeUePublie(t.stade_procedural)).length,
    // Comptés, et dits : un texte que §6 ne publie pas n'est pas un texte absent.
    horsSeuil: nonPublies.length,
    // Une sous-cascade par nature, pour le filtre ; chacune calculée sur ses
    // seuls textes, jamais découpée dans la figure entière.
    parNature: parNature
      ? Object.fromEntries(NATURES_UE.map(({ cle }) => [
        cle,
        textesEuropeens(
          liste.filter((t) => natureEuropeenne(t, dossierEuropeen) === cle),
          dossierEuropeen,
          documentEuropeen,
          false,
        ),
      ]))
      : null,
    cascade: {
      total: dessines.length,
      stades: [...basses, ...hautes],
      basses,
      // Le vocabulaire voyage avec la figure : la mise en page ne connaît ni
      // les motifs d'absence, ni la nomenclature européenne.
      libelles: Object.fromEntries([...basses, ...hautes].map((cle) => [cle, libelleIssue(cle)])),
      // Du thème le plus lourd au plus léger ; « non établie » en dernier.
      matieres: [...poids.keys()].sort(
        (a, b) => (a === MATIERE_NON_ETABLIE) - (b === MATIERE_NON_ETABLIE)
          || poids.get(b) - poids.get(a) || a.localeCompare(b, 'fr'),
      ),
      flux: [...flux.entries()].map(([cle, n]) => {
        const [matiere, issue] = cle.split(SEPARATEUR_FLUX);
        return [matiere, issue, n];
      }),
      sansMatiere,
      // Le 49.3 est une procédure française : la figure européenne n'en porte
      // aucun, et le bouton ne s'affiche pas.
      procedure493: 0,
      textes: textesListe,
    },
  };
}
/*
 * La cascade : un flux par (matière, cran d'arrêt), et la liste des textes qui
 * le composent. La MATIÈRE est la commission saisie au fond du dossier, la
 * même table que la chute des amendements — les deux figures doivent colorier
 * pareil, sinon la section se lit comme deux sections. Son absence en est une
 * (§2 règle 5) : un texte sans dossier, ou dont le dossier n'a pas de
 * commission dans la table, tombe sous « matière non établie » — compté,
 * jamais réparti au prorata ni déduit de l'intitulé.
 */
const SEPARATEUR_FLUX = String.fromCharCode(0);

function cascadeDesTextes(publies, commissionDuDossier) {
  const matiereDuTexte = (t) => {
    const commission = t.dossier_id ? commissionDuDossier(t.dossier_id) : null;
    return commission?.sigle || commission?.nom || MATIERE_NON_ETABLIE;
  };
  const parStade = new Map();
  for (const t of publies) parStade.set(t.stade_procedural, (parStade.get(t.stade_procedural) || 0) + 1);
  const stades = STADES_PUBLIES.filter((s) => (parStade.get(s) || 0) > 0);
  const flux = new Map();
  let sansMatiere = 0;
  const listeTextes = publies.map((t) => {
    const matiere = matiereDuTexte(t);
    if (matiere === MATIERE_NON_ETABLIE) sansMatiere += 1;
    const cle = `${matiere}\u0000${t.stade_procedural}`;
    flux.set(cle, (flux.get(cle) || 0) + 1);
    return {
      titre: t.titre,
      matiere,
      stadeCle: t.stade_procedural,
      stade: LIBELLE_STADE[t.stade_procedural] || t.stade_procedural,
      // Le SORT à côté du STADE, jamais à sa place (#743). Le stade dit jusqu'où
      // le texte est allé, le sort ce qu'il est devenu, et l'un ne se déduit pas
      // de l'autre. `null` porte toujours son motif, qui s'affiche à sa place —
      // un sort par défaut serait une invention (§2 règle 5).
      sortCle: t.sort ?? null,
      sortMotif: t.sort_non_resolu?.motif ?? null,
      role: LIBELLE_ROLE_TEXTE[t.role] || t.role || null,
      url: t.source_url ?? null,
      an: t.date_max ? String(t.date_max).slice(0, 4) : null,
      // L'INSTITUTION VOYAGE AVEC LE TEXTE, jusque dans la liste ouverte au clic
      // sur la cascade : un projet de loi est signé comme MINISTRE, une
      // proposition déposée comme PARLEMENTAIRE. `role` les sépare à la source
      // (#689) et la liste les range en deux colonnes plutôt qu'en une phrase.
      projetDeLoi: estProjetDeLoi(t),
    };
  });
  // L'ordre des matières fixe les teintes, et il suit le VOLUME : recalculé
  // ailleurs, la cascade et la chute cesseraient de colorier pareil.
  const volume = new Map();
  for (const t of listeTextes) volume.set(t.matiere, (volume.get(t.matiere) || 0) + 1);
  const matieres = [...volume.keys()].sort(
    (a, b) => volume.get(b) - volume.get(a) || a.localeCompare(b, 'fr'),
  );
  /* LE 49.3 SE COMPTE À PART, PARCE QU'IL NE SE VOIT NULLE PART AILLEURS.
   *
   * Un texte adopté par engagement de responsabilité se range, dans la
   * cascade, là où son STADE le met — et son stade ne dit rien du 49.3. Sur
   * les 423 textes portés publiés, les cinq concernés sont invisibles : quatre
   * de Gabriel Attal fondus dans la barre « promulgué », un d'Édouard Philippe
   * dans une barre « non adopté » qui le contredit. La figure a le stade pour
   * axe et ne peut pas porter ce fait ; il est donc compté, nommé et publié à
   * côté d'elle (§2 règle 4 : jamais un vote, toujours un fait procédural). */
  const procedure493 = listeTextes.filter((t) => SORTS_PROCEDURE_49_3.has(t.sortCle)).length;
  const parSort = new Map();
  for (const t of listeTextes) parSort.set(t.sortCle, (parSort.get(t.sortCle) || 0) + 1);
  return {
    total: publies.length,
    sansMatiere,
    procedure493,
    parSort: Object.fromEntries(parSort),
    stades,
    matieres,
    flux: [...flux.entries()]
      .map(([cle, n]) => [cle.split('\u0000')[0], cle.split('\u0000')[1], n])
      .sort((a, b) => b[2] - a[2] || String(a[0]).localeCompare(String(b[0]), 'fr')),
    textes: listeTextes,
  };
}

/* ── Livrable : ce qu'il a dit, et en quelle qualité ─────────────────────────
 *
 * Deux régimes, jamais confondus (§2 règle 2) :
 *  - SOURCÉ  — le compte rendu publie `fonction` (Attal : 3 555 / 3 963) ;
 *  - DÉRIVÉ  — il ne la publie pas (Guedj : 0 / 2 702), et lire ce silence
 *    comme « il parlait comme député » est NOTRE inférence, licite seulement
 *    parce que ses mandats disent qu'il n'exerçait rien d'autre à ces dates.
 *    Elle est donc déclarée comme telle sur la page.
 */
export const TYPES_INTERVENTION = [
  { cles: ['loi'], label: 'Débats sur un texte de loi' },
  { cles: ['debat'], label: 'Débats' },
  { cles: ['question', 'question_orale'], label: 'Questions écrites et orales' },
  { cles: ['question_gouvernement'], label: 'Questions au gouvernement' },
  { cles: ['motion_censure'], label: 'Motions de censure' },
  { cles: ['explication_vote'], label: 'Explications de vote' },
  { cles: ['commission'], label: 'Commission' },
];

/* `interventionsParNature()` est partie avec #328. Elle rendait la liste des
 * natures d'intervention TOUTES PÉRIODES CONFONDUES, pour un bloc de la fiche
 * qui n'existe plus : la nature est devenue une facette de « Ce qu'il a dit »,
 * comptée sous la période et le sujet retenus. `TYPES_INTERVENTION` reste — la
 * table de libellés, elle, sert toujours, et à un seul endroit.
 */

export function regimeQualiteOrateur(interventions) {
  const liste = interventions || [];
  const sourcees = liste.filter((i) => i.fonction).length;
  const parFonction = new Map();
  for (const i of liste) {
    if (!i.fonction) continue;
    parFonction.set(i.fonction, (parFonction.get(i.fonction) || 0) + 1);
  }
  // TROIS états, pas deux. « Sourcée » dès la première fonction publiée dirait
  // que la qualité est connue là où elle l'est sur 35 des 3 933 interventions
  // de Jean-Luc Mélenchon (0,9 %). Un seuil serait un arbitrage éditorial : la
  // page publie donc les deux nombres et nomme l'état partiel.
  const regime = sourcees === 0 ? 'derive' : sourcees === liste.length ? 'source' : 'partiel';

  return {
    total: liste.length,
    sourcees,
    regime,
    sourcee: sourcees > 0,
    fonctions: [...parFonction.entries()]
      .map(([label, n]) => ({ label, n }))
      .sort((a, b) => b.n - a.n),
  };
}

/* ── Règle : un même champ recouvre deux actes opposés ───────────────────────
 *
 * `type_detail: "question_gouvernement"` compte les questions POSÉES par un·e
 * député·e et celles auxquelles un·e ministre RÉPOND. Guedj : 215, dont 0
 * portent une qualité ministérielle — il les a posées. Attal : 743, dont 723 —
 * il y a répondu. Publier « ce sur quoi il a interpellé le gouvernement » pour
 * le second serait exactement inversé.
 *
 * Deux conditions, et pas une : la qualité publiée par la source ET une date
 * tombant dans une période de gouvernement. Mesuré sur Attal, les deux règles
 * donnent 723 séparément ; les conjoindre évite qu'un `fonction: "rapporteur"`
 * — 204 chez lui — compte un jour pour une qualité ministérielle.
 */
export function depuisLeBancDuGouvernement(interventions, appartenances) {
  const liste = interventions || [];
  const periodes = appartenances || [];
  const dansGouvernement = (date) =>
    Boolean(date) && periodes.some((p) => p.debut <= date && date <= p.fin);
  const ministerielles = liste.filter((i) => i.fonction && dansGouvernement(i.date)).length;
  return {
    total: liste.length,
    ministerielles,
    // La MAJORITÉ tranche, et rien d'autre : un profil sans qualité publiée
    // (Jérôme Guedj, 0 des 2 702) tombe du côté parlementaire, ce qui est le
    // constat de la source et non une déduction sur la personne. Le compte des
    // deux est publié à côté du verdict, pour que le lecteur voie sur quoi il
    // repose.
    banc: ministerielles > liste.length / 2 ? INSTITUTION_GOUVERNEMENT : INSTITUTION_PARLEMENT,
  };
}

export function directionQuestionsGouvernement(interventions, appartenances) {
  const qag = (interventions || []).filter((i) => i.type_detail === 'question_gouvernement');
  if (!qag.length) return null;

  const { ministerielles, banc } = depuisLeBancDuGouvernement(qag, appartenances);

  const parSujet = new Map();
  for (const i of qag) {
    if (!i.sujet) continue;
    parSujet.set(i.sujet, (parSujet.get(i.sujet) || 0) + 1);
  }

  // `sujets` est TRONQUÉ à douze pour l'affichage : `avecSujet` et
  // `sujetsDistincts` se comptent donc sur l'ensemble, jamais sur la tranche.
  // Les sommer après la coupe donnerait un dénominateur faux dès le treizième
  // sujet — et c'est le dénominateur qui porte la couverture du point.
  let avecSujet = 0;
  for (const n of parSujet.values()) avecSujet += n;

  return {
    total: qag.length,
    ministerielles,
    avecSujet,
    sujetsDistincts: parSujet.size,
    banc,
    sens: banc === INSTITUTION_GOUVERNEMENT ? 'recues' : 'posees',
    sujets: [...parSujet.entries()]
      .map(([label, n]) => ({ label, n }))
      .sort((a, b) => b.n - a.n || a.label.localeCompare(b.label, 'fr'))
      .slice(0, 12),
  };
}

/* ── Livrable : ce qu'il a voté, et les périodes où voter était impossible ───
 *
 * La sélection des votes « sur l'ensemble d'un texte » vient du lot 1
 * (`isWholeTextVote`, corrigée par #672) et n'est pas réécrite ici. Elle est un
 * PLANCHER, jamais un relevé exhaustif, et `WHOLE_TEXT_VOTE_BOUND` porte cette
 * phrase sur la page.
 *
 * Le décompte porte sur des TEXTES, pas sur des votes (#711) : un texte revenu
 * plusieurs fois devant l'Assemblée ne compte qu'une fois, à sa DERNIÈRE
 * LECTURE — la règle qu'`AGENTS.md` §6 publie depuis toujours et que rien
 * n'appliquait. `selectDerniereLectureVotes` (lot 1) la porte, elle non plus
 * n'est pas réécrite ici, et `LAST_READING_RULE` la publie sur la page.
 *
 * La dernière lecture d'un texte se lit sur le CORPUS des scrutins, jamais sur
 * les seuls votes de la personne. Mesuré sur `gabriel-attal` : ses 150 votes
 * sur l'ensemble d'un texte donnent 120 textes si l'on ordonne ses propres
 * lectures, mais 111 si l'on ordonne celles du corpus. Les 9 d'écart sont des
 * textes dont il a voté une lecture ANTÉRIEURE et pas la dernière — dont le
 * projet de loi de simplification de la vie économique, qu'il avait déposé
 * comme Premier ministre, voté contre en première lecture le 17/06/2025, adopté
 * sur le texte de la commission mixte paritaire le 14/04/2026, scrutin où
 * aucune position de lui n'est enregistrée. Afficher ce « contre » comme sa
 * position sur cette loi aurait été faux, et dire pourquoi il manque au scrutin
 * final publierait une absence individuelle (§2 règle 3).
 *
 * Sans le corpus, la dernière lecture n'est pas déterminable : la fonction le
 * DÉCLARE (`derniereLectureDisponible`) au lieu de retomber sur les seuls votes
 * de la personne. Une règle de repli qui remplace silencieusement la règle
 * publiée est ce qui a rendu #510 invisible.
 *
 * « Un membre du gouvernement ne vote pas » est un FAIT ÉTABLI sur la personne,
 * pas une lacune de collecte — sans cette phrase, Attal paraît absent de 2018 à
 * 2024. Il n'est pas non plus une raison de masquer ses autres votes : la
 * maquette suspendait la barre entière, ce qui aurait tu 150 votes réels.
 *
 * AUCUN ratio de participation : un dénominateur « scrutins où la personne
 * aurait pu voter » est un taux d'assiduité individuel (§2 règle 3).
 */
export function votesDuProfil(
  votesJoints,
  appartenances,
  rolesParlementaires,
  scrutinsCorpus = null,
) {
  const liste = votesJoints || [];
  const surEnsemble = liste.filter((v) => isWholeTextVote(v.scrutin));

  /* LES VOTES QUE L'INDEX NE RÉSOUT PAS, ET POURQUOI ILS SE COMPTENT À PART.
   *
   * Un vote européen n'a pas de `scrutin_id` — mesuré le 13/09/2026 : **0 des
   * 11 013** votes européens portés par les 7 fiches concernées en porte un.
   * `joinVotes` retombe alors sur `scrutin_non_resolu`, qui ne porte ni
   * `type_vote` ni `texte` : `isWholeTextVote` rend faux, et la section se
   * vidait en expliquant qu'« aucune de ses positions ne porte sur l'ensemble
   * d'un texte ».
   *
   * C'est vrai à l'Assemblée. Sur une fiche européenne, cela attribuait à la
   * personne une limite qui est la NÔTRE (§2 règle 2) : ses votes existent, ils
   * sont collectés et comptés, et c'est notre index qui ne sait pas les
   * rattacher à un scrutin. */
  const nonResolusEuropeens = liste.filter(
    (v) => !v.scrutin_id && v.scrutin?.institution === INSTITUTION_PE_SOURCE,
  ).length;

  // `null` — et non un tableau vide — quand le corpus des scrutins n'a pas pu
  // être lu : « je ne sais pas quelle est la dernière lecture » n'est pas
  // « aucun texte » (§2 règle 5).
  const dernieresLectures = scrutinsCorpus
    ? new Set(selectDerniereLectureVotes(scrutinsCorpus).map((s) => s.id))
    : null;
  const retenus = dernieresLectures
    ? surEnsemble.filter((v) => dernieresLectures.has(v.scrutin_id))
    : [];

  const positions = new Map();
  for (const v of retenus) positions.set(v.position, (positions.get(v.position) || 0) + 1);

  const periodes = appartenances || [];
  const sieges = rolesParlementaires || [];
  const dansGouvernement = (date) =>
    Boolean(date) && periodes.some((p) => p.debut <= date && date <= p.fin);

  const compte = new Map();
  for (const v of liste) {
    const annee = (v.date || '').slice(0, 4);
    if (!annee) continue;
    compte.set(annee, (compte.get(annee) || 0) + 1);
  }

  /*
   * L'axe des années est CONTINU entre la première et la dernière année
   * observée, et chaque année porte sa situation. Un axe troué — 2018 puis 2022
   * chez Gabriel Attal — laisse croire que les années intermédiaires n'existent
   * pas, alors qu'elles portent le fait le plus important de sa fiche : il était
   * au gouvernement et ne pouvait pas voter.
   *
   * Mais un `0` nu serait pire encore. Trois situations, jamais confondues :
   *   - `gouvernement` : voter était impossible, c'est un fait sur la personne ;
   *   - `hors_mandat`  : aucun mandat parlementaire cette année-là, il n'y avait
   *                      rien à voter — publier `0` sans le dire se lirait comme
   *                      une absence, c'est-à-dire le taux de présence
   *                      individuel qu'interdit §2 règle 3 ;
   *   - `en_mandat`    : un zéro mesuré, et celui-là seul est un décompte.
   */
  const annees = [...compte.keys()].sort();
  const parAnnee = [];
  if (annees.length) {
    const debut = Number(annees[0]);
    const fin = Number(annees[annees.length - 1]);
    for (let a = debut; a <= fin; a += 1) {
      const annee = String(a);
      const gouvernement = periodes.some(
        (p) => p.debut.slice(0, 4) <= annee && annee <= p.fin.slice(0, 4),
      );
      const enMandat = sieges.some(
        (r) => r.debut.slice(0, 4) <= annee && annee <= r.fin.slice(0, 4),
      );
      parAnnee.push({
        annee,
        n: compte.get(annee) || 0,
        situation: gouvernement ? 'gouvernement' : enMandat ? 'en_mandat' : 'hors_mandat',
      });
    }
  }

  return {
    total: liste.length,
    surEnsemble: surEnsemble.length,
    nonResolusEuropeens,
    derniereLectureDisponible: dernieresLectures !== null,
    textes: retenus.length,
    // Les votes RETENUS eux-mêmes, et non leur seul décompte : « ce qu'il a
    // voté » les range ensuite par période politique (`utils/votesParPeriode`).
    // Les rendre ici garantit que le repli sur la dernière lecture n'est
    // calculé QU'UNE FOIS, et qu'aucune vue n'en écrit une seconde version
    // (AGENTS.md §6 : la sélection vit dans `utils/lecture.js`, #711).
    retenus,
    // Ce que le repli a retiré, nommé plutôt que laissé à la soustraction. Il
    // ne dit RIEN d'une absence : il compte des positions bien réelles de la
    // personne, sur des lectures qu'un scrutin plus tardif a suivies.
    lecturesDepassees: surEnsemble.length - retenus.length,
    positions: ['pour', 'contre', 'abstention', 'non_votant']
      .filter((p) => positions.has(p))
      .map((p) => ({ position: p, n: positions.get(p) })),
    pendantGouvernement: liste.filter((v) => dansGouvernement(v.date)).length,
    aExerceAuGouvernement: periodes.length > 0,
    parAnnee,
  };
}

/* ── Livrable : L'essentiel ──────────────────────────────────────────────────
 *
 * Cinq points, tirés d'un VIVIER de sept, chacun issu d'un jeu de données
 * distinct. Aucun rapprochement thématique, aucune synthèse : Empreinte
 * politique ne classe pas les textes par sujet (§2 règle 8), et chaque point est
 * DÉRIVÉ par comptage d'un champ de la source, jamais d'une table de mots-clés
 * écrite à la main.
 *
 * La section s'appelait « Coup d'œil ». Le titre promettait de la rapidité, pas
 * du contenu, et c'est le contenu qui est en jeu ici.
 *
 * ── Ce que chaque point doit porter ────────────────────────────────────────
 *
 * 1. UNE CHOSE NOMMÉE, pas la forme d'une distribution. « 6 dossiers sur 34
 *    concentrent 2 206 de ses 2 429 amendements » est vrai et ne se convertit
 *    en rien : le lecteur ne sait pas quoi en faire. Le dossier nommé, lui, dit
 *    sur quoi la personne a travaillé.
 *
 * 2. SA PROPRE COUVERTURE. Un point qui compte sur une sous-population dit
 *    laquelle et combien elle pèse. C'est ce qui empêche d'écrire « sujets très
 *    ciblés » là où l'on décrirait notre collecte en croyant décrire son
 *    travail (§2 règle 5). Le numérateur et le dénominateur sont TOUJOURS de la
 *    même population.
 *
 * 3. LE MOINS DE NOTES POSSIBLE. Une note qui met en garde contre un contresens
 *    est une information et se garde (`garde`) : « questions reçues depuis le
 *    banc du gouvernement, pas des questions posées » évite de lire à l'envers
 *    les 743 questions de Gabriel Attal. Une note qui justifie notre méthode ne
 *    sert qu'à nous et se retire.
 *
 * 4. SON RÔLE, qui est un fait collecté. Voir ci-dessous.
 *
 * ── Le vivier et la garantie de rôle (option C) ────────────────────────────
 *
 * LE DÉFAUT QU'ELLE CORRIGE EST STRUCTUREL. Les cinq points étaient cinq
 * CATÉGORIES FIXES — interventions, amendements, commissions, questions, textes
 * — qui décrivent le métier d'un⋅e député⋅e. Chez un⋅e ancien⋅ne ministre elles
 * se remplissent surtout de ce que son ministère a produit, et son travail
 * parlementaire disparaît : les 34 « textes portés » de Gabriel Attal étaient à
 * 31 des projets de loi du gouvernement, ses 743 « questions au gouvernement »
 * lui étaient posées, et ses 49 amendements de député se lisaient comme un
 * résidu à côté.
 *
 * LE RÔLE SE LIT SUR UN FAIT COLLECTÉ, jamais sur une catégorie éditoriale :
 *
 *  - `gouvernement` est tenu si la personne a été MEMBRE d'un gouvernement
 *    (`appartenancesGouvernementales`) — 6 des 13 candidats déclarés au SHA
 *    f635cb60, 01/09/2026 : Bruno Retailleau, Édouard Philippe, Gabriel Attal,
 *    Laurent Wauquiez, Ségolène Royal, Xavier Bertrand. Un⋅e parlementaire EN
 *    MISSION auprès d'un ministère n'en est pas membre : les 2 mandats « en
 *    mission » de Jérôme Guedj sont correctement écartés ;
 *  - `parlement` est tenu dès qu'un point du vivier en relève.
 *
 * ET LE RÔLE DE CHAQUE POINT AUSSI. Aucun n'est étiqueté à la main :
 *
 *  - `amendements` → parlement. Les 6 651 dépôts comme auteur principal des 13
 *    candidats déclarés portent `type_deposant` `depute` (6 645) ou
 *    `commission_rapporteur` (6), JAMAIS `gouvernement`, et aucun ne tombe dans
 *    une période d'appartenance gouvernementale ;
 *  - `commissions` → parlement : un siège en commission est un mandat
 *    parlementaire, la source le range sous `mandats` ;
 *  - `interventions` et `questions` → le banc d'où la parole est portée, par la
 *    règle à deux conditions de `depuisLeBancDuGouvernement` (qualité publiée
 *    par la source ET date dans une période de gouvernement) ;
 *  - `textes` → SCINDÉ EN DEUX POINTS par `nature_texte` (#689), et c'est la
 *    réparation principale : porter un projet de loi au nom du gouvernement
 *    n'est pas déposer une proposition comme parlementaire, et la source
 *    rangeait les deux sous le même `role: auteur` jusqu'à #689 ;
 *  - `qualite` → aucun rôle : il compte les qualités d'orateur des deux bancs
 *    confondus. Un point sans rôle ne peut pas satisfaire la garantie ; il ne
 *    remplit qu'une place restante.
 *
 * LA GARANTIE. Pour chaque rôle tenu, le premier point du vivier qui en relève
 * est retenu AVANT que les places restantes ne soient remplies dans l'ordre.
 * L'ordre du vivier est fixe pour les treize ; la sélection est ensuite remise
 * dans cet ordre, si bien que la garantie change QUI est retenu, jamais dans
 * quel ordre la page se lit.
 *
 * ELLE NE FABRIQUE RIEN. Un rôle tenu dont le vivier ne porte aucun point ne
 * reçoit pas de place : la section le DIT (`rolesSansPoint`) au lieu d'inventer
 * un chiffre. C'est le cas de Ségolène Royal et de Xavier Bertrand, membres de
 * gouvernement dont le corpus ne publie ni intervention, ni question, ni texte
 * porté.
 *
 * ELLE VAUT IDENTIQUEMENT POUR UN⋅E DÉPUTÉ⋅E PUR⋅E : un seul rôle tenu, tous
 * les points en relèvent, la garantie retient le premier — c'est-à-dire ce que
 * l'ordre fixe aurait donné. AUCUN SECOND GABARIT : mêmes points possibles,
 * même ordre, mêmes champs pour les treize.
 *
 * CE QU'ELLE NE FAIT PAS AUJOURD'HUI : elle ne déplace aucun point sur les 13
 * profils publiés — sur chacun, l'ordre fixe suffisait déjà à représenter les
 * rôles tenus. Elle est écrite quand même, parce que c'est la règle qui empêche
 * le défaut de revenir quand le vivier ou le corpus bouge, et elle est
 * verrouillée sur un cas construit (`tests/test_essentiel_328.py`).
 *
 * L'ordre est fixe pour les treize ; ne sont rendus que les points dont la
 * donnée existe, cinq au plus. Un point absent n'est pas remplacé : c'est la
 * trame qui uniformise les emplacements, pas leur remplissage.
 */
export const NB_POINTS_ESSENTIEL = 5;

/** « puis « X » (12) et « Y » (7) » — les suivants, nommés, jamais résumés. */
function suiteNommee(items, format) {
  const suivants = items.slice(1, 3);
  if (!suivants.length) return null;
  return `puis ${suivants.map(format).join(' et ')}`;
}

/** L'accord se fait sur le nombre, pas sur un « (s) » : la page est lue, pas
 * remplie. Un seul point d'accord suffit — le reste de la phrase est écrit deux
 * fois plutôt que rendu approximatif. */
function pluriel(n, singulier, pluriels) {
  return n > 1 ? pluriels : singulier;
}

const entreGuillemets = ({ label, n }) => `« ${label} » (${formatNumber(n)})`;

/** Ce que le lot parlementaire contient VRAIMENT — déposer une proposition et
 * rapporter un texte ne sont pas le même acte, et écrire « propositions » sur un
 * lot qui contient un rapport serait faux. Le libellé se compose du contenu, il
 * n'est pas choisi d'avance. */
function natureDesTextesPortes(lot) {
  const rapportes = lot.filter((t) => t.roleCle === 'rapporteur' || t.roleCle === 'co-rapporteur').length;
  const deposes = lot.length - rapportes;
  const morceaux = [];
  if (deposes > 0) morceaux.push(pluriel(deposes, 'proposition déposée', 'propositions déposées'));
  if (rapportes > 0) morceaux.push(pluriel(rapportes, 'texte rapporté', 'textes rapportés'));
  return morceaux.join(' et ');
}

/** Comment un point se donne à voir. La forme suit le cas, jamais l'inverse :
 * « 27 sur 60 » se compare mal en prose, cinq intitulés de texte se lisent très
 * bien en liste. Valeur fermée — un rendu inconnu retombe sur `ratio`. */
export const RENDU_RATIO = 'ratio';
export const RENDU_COUPLE = 'couple';
export const RENDU_PODIUM = 'podium';
export const RENDUS_POINT = [RENDU_RATIO, RENDU_COUPLE, RENDU_PODIUM];

/** Les libellés des deux rôles, tels que la page les écrit. « au banc du
 * gouvernement » et non « comme ministre » : la source publie une appartenance,
 * pas toujours un portefeuille. */
export const LIBELLE_ROLE_POINT = {
  [INSTITUTION_PARLEMENT]: 'comme parlementaire',
  [INSTITUTION_GOUVERNEMENT]: 'au banc du gouvernement',
};

/** Le même rôle, nommé pour la phrase qui déclare qu'AUCUN point ne le
 * documente. Forme nominale : « son passage au gouvernement » se lit, « au banc
 * du gouvernement » ne s'insère pas dans cette phrase-là. */
export const LIBELLE_ROLE_ABSENT = {
  [INSTITUTION_PARLEMENT]: 'son travail parlementaire',
  [INSTITUTION_GOUVERNEMENT]: 'son passage au gouvernement',
};

/*
 * Le vivier : tous les points que la donnée permet, dans l'ordre fixe des
 * treize. La sélection vient après, et elle seule décide lesquels sont rendus.
 */
function vivierDesPoints({
  interventions,
  dossiers,
  fonctions,
  questions,
  qualite,
  textes,
  appartenances,
}) {
  const points = [];

  // 1. Les points de l'ordre du jour où la parole a le plus porté. La
  //    couverture est le nerf : une intervention dont le compte rendu ne donne
  //    pas le point de l'ordre du jour n'est pas classable, et l'inclure au
  //    dénominateur ferait passer un trou de collecte pour de la dispersion.
  //
  //    Pas de barre ici, et c'est un choix de cas : 417 points de l'ordre du
  //    jour forment un vocabulaire OUVERT, où trois segments sur 417 ne disent
  //    rien de la forme. C'est le nombre 417 qui la dit.
  const liste = interventions || [];
  const situees = liste.filter((i) => i.sujet);
  if (situees.length) {
    const parSujet = new Map();
    for (const i of situees) parSujet.set(i.sujet, (parSujet.get(i.sujet) || 0) + 1);
    const classes = [...parSujet.entries()]
      .map(([label, n]) => ({ label, n }))
      .sort((a, b) => b.n - a.n || a.label.localeCompare(b.label, 'fr'));
    const muettes = liste.length - situees.length;
    const { banc, ministerielles } = depuisLeBancDuGouvernement(liste, appartenances);
    points.push({
      cle: 'interventions',
      role: banc,
      rendu: RENDU_RATIO,
      valeur: classes[0].n,
      sur: situees.length,
      texte: `${pluriel(classes[0].n, 'intervention porte', 'interventions portent')} sur « ${classes[0].label} »`,
      suite: suiteNommee(classes, entreGuillemets),
      socle:
        `${formatNumber(classes.length)} ${pluriel(classes.length, 'point', 'points')} de l’ordre du jour en tout` +
        (muettes > 0
          ? `, et ${formatNumber(muettes)} ${pluriel(muettes, 'intervention dont le compte rendu n’indique', 'interventions dont le compte rendu n’indique')} aucun point`
          : ''),
      garde:
        banc === INSTITUTION_GOUVERNEMENT
          ? `${ministerielles === liste.length ? `toutes ces ${formatNumber(liste.length)}` : `${formatNumber(ministerielles)} de ces ${formatNumber(liste.length)}`} interventions portent une qualité ministérielle publiée par la source, à une date d’appartenance à un gouvernement`
          : null,
    });
  }

  // 2. Le COUPLE : combien de dossiers législatifs, et combien de dépôts sur
  //    eux. Un nombre seul appellerait un classement ; deux nombres qui varient
  //    en sens inverse appellent une lecture. Marine Le Pen fait 83 dossiers
  //    pour 685 dépôts (large et léger), Laurent Wauquiez 14 pour 326
  //    (l'inverse) — aucun des deux n'est « meilleur », et c'est ce qui rend le
  //    couple publiable (§2 règle 1).
  //
  //    Ce qui a été écarté, et pourquoi (mesures du 01/09/2026, 13 candidats
  //    déclarés) : le COMPTE BRUT ne dit rien — la médiane de dépôts par dossier
  //    va de 2,5 à 8 sur les quatre profils qui en portent plus de 50, et
  //    l'écart entre 2 831 et 584 mesure la participation à un épisode de dépôt
  //    en masse : 574 des 2 429 dépôts de Jérôme Guedj (23,6 %) portent sur le
  //    seul PLFRSS 2023, 182 des 584 de Laurent Wauquiez (31,2 %) sur le seul
  //    PLF 2026. FILTRER SUR LES ADOPTÉS
  //    mesure le terrain, pas la personne, et le `sort` est inconnu sur 1 822
  //    de ces 2 831 : un décompte sur un dénominateur amputé de 64 % viole
  //    §2 règle 5, et §6 interdit tout taux d'adoption entre types de
  //    déposants. COMPTER LES `texte_vise` DISTINCTS est faux : ce sont des
  //    LECTURES, pas des lois — Jérôme Guedj passe de 47 lectures à 25 dossiers.
  //
  //    QUAND AUCUN DOSSIER N'EST RÉSOLU, le point ne disparaît pas : il dit le
  //    nombre de dépôts et pourquoi il ne peut rien en dire de plus. Xavier
  //    Bertrand (62 dépôts) et Édouard Philippe (6) sont dans ce cas — leurs
  //    textes visés relèvent de la XIVe législature, dont l'archive de dossiers
  //    n'est pas ingérée. Supprimer le point ferait disparaître 68 dépôts
  //    collectés (§2 règle 5).
  if (dossiers && dossiers.distincts === 0 && dossiers.sansDossier.depots > 0) {
    const { depots: horsDossier, textesVises } = dossiers.sansDossier;
    points.push({
      cle: 'amendements',
      role: INSTITUTION_PARLEMENT,
      rendu: RENDU_RATIO,
      valeur: horsDossier,
      sur: horsDossier,
      texte: `${pluriel(horsDossier, 'amendement déposé comme auteur principal', 'amendements déposés comme auteur principal')}`,
      suite: null,
      socle: null,
      garde: `${pluriel(horsDossier, 'il vise', 'ils visent')} ${formatNumber(textesVises)} ${pluriel(textesVises, 'texte que la source ne rattache', 'textes que la source ne rattache')} à aucun dossier législatif : ni le dossier, ni la commission qui l’a examiné ne sont publiables ici`,
    });
  } else if (dossiers && dossiers.distincts > 0) {
    const nomme = dossiers.nommes[0] || null;
    const anonymes = dossiers.distincts - dossiers.distinctsNommes;
    const { depots: horsDossier, textesVises } = dossiers.sansDossier;
    points.push({
      cle: 'amendements',
      role: INSTITUTION_PARLEMENT,
      rendu: RENDU_COUPLE,
      couple: [
        {
          n: dossiers.distincts,
          label: pluriel(dossiers.distincts, 'dossier législatif amendé', 'dossiers législatifs amendés'),
        },
        {
          n: dossiers.depots,
          label: pluriel(dossiers.depots, 'amendement déposé sur eux', 'amendements déposés sur eux'),
        },
      ],
      // « examinées par », jamais « travaille sur » : une commission n'est pas
      // un sujet — « Lois » couvre l'immigration, la justice et les
      // institutions. Aide à la lecture (§2 règle 8), pas position déclarée.
      repartition: dossiers.commissions.length
        ? {
            titre: 'Dossiers examinés par',
            segments: dossiers.commissions.slice(0, NB_COMMISSIONS_MONTREES),
            // Le dénominateur de la barre est le TOTAL des dossiers, pas la
            // somme des trois segments : ce qui reste — autres commissions,
            // dossiers sans commission publiée — reste visible comme du vide,
            // au lieu d'être normalisé à 100 % (DESIGN_SYSTEM §5).
            total: dossiers.distincts,
            reste:
              dossiers.commissions.length > NB_COMMISSIONS_MONTREES
                ? dossiers.commissions.length - NB_COMMISSIONS_MONTREES
                : 0,
            sansCommission: dossiers.dossiersSansCommission,
          }
        : null,
      texte: nomme ? `le plus amendé : « ${nomme.nom} » (${formatNumber(nomme.n)})` : null,
      suite: nomme
        ? suiteNommee(
            dossiers.nommes.map((d) => ({ label: d.nom, n: d.n })),
            entreGuillemets,
          )
        : null,
      socle:
        anonymes > 0
          ? `${formatNumber(anonymes)} ${pluriel(anonymes, 'de ces dossiers n’est nommé par aucune entrée d’index', 'de ces dossiers ne sont nommés par aucune entrée d’index')}`
          : null,
      // LA BORNE SE DÉCLARE. Chez Jean-Luc Mélenchon la répartition reposerait
      // sur 12 % de ses dépôts : la page l'écrit au lieu de la présenter comme
      // complète (§2 règle 5).
      garde:
        horsDossier > 0
          ? `${formatNumber(horsDossier)} ${pluriel(horsDossier, 'autre dépôt vise', 'autres dépôts visent')} ${formatNumber(textesVises)} ${pluriel(textesVises, 'texte que la source ne rattache', 'textes que la source ne rattache')} à aucun dossier : ${pluriel(horsDossier, 'il ne figure', 'ils ne figurent')} ni dans les deux nombres ci-dessus${dossiers.commissions.length ? ', ni dans les commissions' : ''}`
          : null,
    });
  }

  // 3. Les commissions. Déjà nommées, rien à réparer — la suite l'est aussi.
  //    En PODIUM : trois rangs côte à côte se comparent d'un regard là où la
  //    prose oblige à relire. Un siège en commission est un mandat
  //    parlementaire, quel que soit ce que la personne a fait par ailleurs.
  //
  //    Le point se lit sur la DURÉE, jamais sur un compte d'entrées : #328 a
  //    mesuré que le nombre d'entrées d'un intitulé compte des enregistrements
  //    de collecte (27 chez Guedj pour 5 ans 10 mois, 4 chez un autre pour
  //    2 jours) et ne dit rien du temps passé. Il lit donc la forme rendue par
  //    `fonctionsExercees` — `blocs[].montrees`, déjà triées par durée — et
  //    n'en recalcule aucune part.
  const commissions = (fonctions?.blocs || []).find((f) => f.cle === 'commission');
  if (commissions?.montrees.length) {
    const tete = commissions.montrees[0];
    points.push({
      cle: 'commissions',
      role: INSTITUTION_PARLEMENT,
      rendu: RENDU_PODIUM,
      valeur: tete.jours,
      sur: fonctions.mandat.jours,
      rangs: commissions.montrees,
      texte: `le temps passé en commission l'a le plus été à la ${tete.label} : ${tete.duree}`,
      // Pas de `suite` : le podium NOMME déjà les deux suivantes avec leur
      // durée. La garder ferait lire deux fois la même liste, une fois en
      // prose et une fois en colonnes.
      suite: null,
      socle:
        commissions.nbIntitules > NB_COMMISSIONS_MONTREES
          ? `${formatNumber(commissions.nbIntitules)} commissions en tout`
          : null,
      garde: null,
    });
  }

  // 4. Les questions au gouvernement. Le dénominateur est le nombre de
  //    questions PORTANT UN SUJET PUBLIÉ, jamais le total : diviser par le
  //    total quand la couverture est partielle publie un ratio faux. Et quand
  //    aucun sujet n'est publié, le point ne nomme rien et dit pourquoi —
  //    écrire « sujets très divers » décrirait notre collecte.
  if (questions?.total) {
    const { avecSujet } = questions;
    const garde =
      questions.sens === 'recues'
        ? 'questions reçues depuis le banc du gouvernement, pas des questions posées'
        : null;
    if (avecSujet > 0) {
      points.push({
        cle: 'questions',
        role: questions.banc,
        rendu: RENDU_RATIO,
        valeur: questions.sujets[0].n,
        sur: avecSujet,
        texte: `${pluriel(questions.sujets[0].n, 'question au gouvernement porte', 'questions au gouvernement portent')} sur « ${questions.sujets[0].label} »`,
        suite: suiteNommee(questions.sujets, entreGuillemets),
        socle:
          `${formatNumber(questions.sujetsDistincts)} ${pluriel(questions.sujetsDistincts, 'sujet distinct', 'sujets distincts')}` +
          (avecSujet < questions.total
            ? `, et ${formatNumber(questions.total - avecSujet)} ${pluriel(questions.total - avecSujet, 'question dont aucun sujet n’est publié', 'questions dont aucun sujet n’est publié')}`
            : ''),
        garde,
      });
    } else {
      points.push({
        cle: 'questions',
        role: questions.banc,
        rendu: RENDU_RATIO,
        valeur: questions.total,
        sur: questions.total,
        texte: `${pluriel(questions.total, 'question au gouvernement, qui ne porte', 'questions au gouvernement, dont aucune ne porte')} de sujet publié`,
        suite: null,
        socle: 'la source ne dit pas sur quoi elles portaient, et la page ne le devine pas',
        garde,
      });
    }
  }

  // 5 et 6. Les textes portés, SCINDÉS par l'institution qui les initie.
  //    Rien de graphique : cinq intitulés se lisent en liste. Seuls les textes
  //    ayant atteint l'examen en commission sont publiés (§6), et ceux qui sont
  //    restés au dépôt sont comptés plutôt que tus.
  if (textes && textes.publies.length) {
    const { total: ecartes, deposes, sansStade } = textes.ecartes;
    // Le socle des écartés est commun aux deux points : il décrit la même
    // liste, et le répéter deux fois le ferait lire comme deux lacunes.
    const socleEcartes =
      ecartes === 0
        ? null
        : sansStade === 0
          ? `${formatNumber(ecartes)} ${pluriel(ecartes, 'autre texte porté en est resté', 'autres textes portés en sont restés')} au dépôt`
          : `${formatNumber(ecartes)} ${pluriel(ecartes, 'autre texte porté', 'autres textes portés')} : ${formatNumber(deposes)} au dépôt, ${formatNumber(sansStade)} dont la source ne publie pas le stade`;

    let premierPointDeTexte = true;
    for (const institution of [INSTITUTION_GOUVERNEMENT, INSTITUTION_PARLEMENT]) {
      const lot = textes.publies.filter((t) => t.institution === institution);
      if (!lot.length) continue;
      const promulgues = lot.filter((t) => t.stadeCle === 'promulgue');
      // `publies` est déjà trié du plus récent au plus ancien : nommer les trois
      // premiers est un ORDRE, pas un choix, et la phrase le dit. Sans elle, le
      // lecteur croirait à une sélection éditoriale.
      const nommables = (promulgues.length ? promulgues : lot).slice(0, 3);
      const gouvernemental = institution === INSTITUTION_GOUVERNEMENT;
      // Le socle des écartés et le compte des textes sans nature décrivent la
      // MÊME liste : ils vont sur le premier point de texte réellement produit,
      // jamais sur une moitié fixe — l'accrocher au point gouvernemental le
      // faisait disparaître de tous les profils qui n'en ont pas.
      const porteLeSocle = premierPointDeTexte;
      premierPointDeTexte = false;
      points.push({
        cle: gouvernemental ? 'textes_gouvernement' : 'textes_parlement',
        role: institution,
        rendu: RENDU_RATIO,
        // Le dénominateur est l'ENSEMBLE des textes publiés de la personne :
        // c'est ce qui dit quelle part de ses textes portés relève de ce banc.
        valeur: lot.length,
        sur: textes.publies.length,
        texte:
          (gouvernemental
            ? `${pluriel(lot.length, 'projet de loi porté au nom du gouvernement', 'projets de loi portés au nom du gouvernement')}`
            : natureDesTextesPortes(lot)) +
          (promulgues.length
            ? `, dont ${formatNumber(promulgues.length)} ${pluriel(promulgues.length, 'promulgué', 'promulgués')}`
            : ''),
        suite: `${pluriel(nommables.length, 'le plus récent', 'les plus récents')} : ${nommables.map((t) => `« ${t.titre} »`).join(', ')}`,
        socle: porteLeSocle
          ? [
              socleEcartes,
              textes.sansNature > 0
                ? `${formatNumber(textes.sansNature)} ${pluriel(textes.sansNature, 'texte publié que la source ne qualifie ni de projet ni de proposition', 'textes publiés que la source ne qualifie ni de projet ni de proposition')}`
                : null,
            ]
              .filter(Boolean)
              .join(' ; ') || null
          : null,
        // Un projet de loi engage le gouvernement, pas la personne qui le signe
        // comme ministre. La garde disait cela sous un point qui mélangeait les
        // deux ; la scission la rend au point qu'elle concerne.
        garde: gouvernemental
          ? 'des textes du gouvernement, portés comme membre de celui-ci — pas des propositions déposées comme parlementaire'
          : null,
      });
    }
  }

  // 7. La qualité d'orateur. Le dénominateur est le nombre d'interventions dont
  //    la source PUBLIE la qualité : 35 des 3 933 de Jean-Luc Mélenchon. Diviser
  //    par le total ferait lire 1 % là où la mesure porte sur 100 % de ce
  //    qu'on sait. AUCUN RÔLE : il compte les deux bancs confondus.
  if (qualite?.sourcees > 0 && qualite.fonctions.length) {
    points.push({
      cle: 'qualite',
      role: null,
      rendu: RENDU_RATIO,
      valeur: qualite.fonctions[0].n,
      sur: qualite.sourcees,
      texte: `${pluriel(qualite.fonctions[0].n, 'intervention a été prononcée', 'interventions ont été prononcées')} comme « ${qualite.fonctions[0].label} »`,
      suite: suiteNommee(qualite.fonctions, entreGuillemets),
      socle:
        qualite.sourcees < qualite.total
          ? `${formatNumber(qualite.sourcees)} des ${formatNumber(qualite.total)} interventions portent une qualité publiée par la source`
          : 'qualité publiée par la source sur chacune',
      garde: null,
    });
  }

  return points;
}

/**
 * Retient au plus `NB_POINTS_ESSENTIEL` points, en réservant une place au
 * premier point de chaque rôle tenu.
 *
 * Le résultat est remis dans l'ordre du vivier : la garantie change QUI est
 * retenu, jamais l'ordre de lecture. `rolesTenus` est une liste, jamais un
 * booléen — un troisième rôle s'ajouterait sans toucher à cette fonction.
 */
export function selectionnerPoints(vivier, rolesTenus, limite = NB_POINTS_ESSENTIEL) {
  const retenus = new Set();
  for (const role of rolesTenus) {
    if (retenus.size >= limite) break;
    const premier = vivier.findIndex((p) => p.role === role);
    if (premier >= 0) retenus.add(premier);
  }
  for (let i = 0; i < vivier.length && retenus.size < limite; i += 1) retenus.add(i);
  return [...retenus].sort((a, b) => a - b).map((i) => vivier[i]);
}

export function essentiel({
  interventions,
  dossiers,
  fonctions,
  questions,
  qualite,
  textes,
  appartenances,
}) {
  const vivier = vivierDesPoints({
    interventions,
    dossiers,
    fonctions,
    questions,
    qualite,
    textes,
    appartenances,
  });

  // Les rôles TENUS, dans l'ordre où la page les nomme. `gouvernement` est un
  // fait collecté ; `parlement` est tenu dès qu'un point du vivier en relève —
  // trois des treize (David Lisnard, Marine Tondelier, Nathalie Arthaud) n'ont
  // aucun point du tout, et la section ne s'affiche pas.
  const rolesTenus = [];
  if (vivier.some((p) => p.role === INSTITUTION_PARLEMENT)) rolesTenus.push(INSTITUTION_PARLEMENT);
  if ((appartenances || []).length > 0) rolesTenus.push(INSTITUTION_GOUVERNEMENT);

  const points = selectionnerPoints(vivier, rolesTenus);

  return {
    points,
    // Combien le vivier portait : sans ce nombre, cinq points sur sept se
    // liraient comme cinq points sur cinq, c'est-à-dire comme un relevé complet.
    vivier: vivier.length,
    rolesTenus,
    // Les rôles que le vivier documente RÉELLEMENT : c'est sur eux que la
    // garantie porte, et c'est eux que la phrase d'annonce peut promettre.
    // Promettre « au moins un par rôle » à Laurent Wauquiez, dont le corpus ne
    // publie rien de son passage au gouvernement, contredirait la ligne
    // suivante.
    rolesRepresentes: rolesTenus.filter((r) => vivier.some((p) => p.role === r)),
    // Un rôle tenu que le vivier ne documente pas. La page le DIT plutôt que de
    // laisser croire que la personne n'y a rien fait (§2 règle 5) : Laurent
    // Wauquiez, Ségolène Royal et Xavier Bertrand sont dans ce cas.
    rolesSansPoint: rolesTenus.filter((r) => !vivier.some((p) => p.role === r)),
    // Le cadre initiative/réaction ne tient pas au banc du gouvernement. Un
    // seul fait le déclenche, et il est collecté.
    aSiegeAuGouvernement: (appartenances || []).length > 0,
    // Le rôle ne s'affiche que s'il distingue : cinq fois « comme
    // parlementaire » sur un profil qui n'a jamais été ministre est du bruit,
    // et le champ existe pourtant sur les treize. Même conditionnel, même fait
    // collecté que la phrase d'introduction.
    montrerLesRoles: rolesTenus.length > 1,
  };
}

/* ── Livrable : « Les grands chiffres » ──────────────────────────────────────
 *
 * Le bloc de tête de la fiche, arbitré en maquette (#328). Ce n'est pas un
 * résumé — c'est un tableau de bord, et il est nommé pour ce qu'il est.
 *
 * DEUX RÈGLES le gouvernent, et tout le reste en découle.
 *
 * 1. **La frise commande les colonnes.** Le parcours n'est pas une section à
 *    part : c'est l'ossature. Une piste par rôle, une colonne par rôle, et la
 *    COULEUR fait le lien. Le constat qui l'a imposé : chez un ancien ministre,
 *    cinq catégories décrivant le métier de député se remplissent de ce que son
 *    ministère a produit, et son travail parlementaire disparaît.
 *
 * 2. **Les lignes sont appariées.** Des objets de même nature se font face et
 *    se traitent pareil, et CHAQUE COLONNE COMPTE CONTRE SON PROPRE TOTAL. Le
 *    total du profil n'apparaît nulle part : « 580 / 618 » d'un côté et
 *    « 2 759 / 3 345 » de l'autre sont deux mesures, pas deux parts d'une
 *    troisième.
 *
 * Ce qui est INTERDIT ici et le restera : additionner les deux colonnes, les
 * comparer, ou en tirer un ratio. Ce sont deux métiers, pas deux notes.
 */

export const COLONNE_PARLEMENT = INSTITUTION_PARLEMENT;
export const COLONNE_GOUVERNEMENT = INSTITUTION_GOUVERNEMENT;

/* Les trois cas de la maquette. Le gabarit est UNIQUE — ce sont les lignes et
 * les colonnes qui apparaissent ou non selon ce que la donnée porte. Deux
 * gabarits rendraient deux fiches incomparables, ce que la garantie par rôle
 * cherche précisément à éviter. */
export const CAS_DEUX_ROLES = 'deux_roles';
export const CAS_PARLEMENT_SEUL = 'parlement_seul';
export const CAS_GOUVERNEMENT_SEUL = 'gouvernement_seul';
export const CAS_RIEN_A_MONTRER = 'rien_a_montrer';


/* `LIBELLE_PISTE` survit à la fabrique de pistes : il nomme les COLONNES, que
 * la frise du parcours ne porte pas. Le reste — `ORDRE_PISTES`,
 * `ETIQUETTE_PISTE`, `pistesDuParcours` — était une seconde frise, et la
 * première la rendait inutile (#672 : jamais deux définitions du même objet).
 * `ORDRE_COLONNES`, ajouté par #328, ne la ressuscite pas : il range les
 * colonnes, il ne fabrique aucune piste — la frise reste seule à le faire.
 */
export const LIBELLE_PISTE = {
  [INSTITUTION_PARLEMENT]: "À l'Assemblée",
  [INSTITUTION_SENAT]: 'Au Sénat',
  [INSTITUTION_PE]: 'Au Parlement européen',
  [INSTITUTION_GOUVERNEMENT]: 'Au gouvernement',
  [INSTITUTION_MISSION]: 'Parlementaire en mission',
};

/* ── Une cellule ─────────────────────────────────────────────────────────────
 *
 * **Un nombre sans son objet ne dit rien.** « 24 / 67 » — et quoi ? Chaque
 * cellule nomme donc ce sur quoi elle porte, et SEULS LES NOMBRES sont en gros :
 * mettre l'objet à la même échelle que le chiffre était le défaut de la
 * première maquette.
 *
 * `absent` n'est pas un vide : c'est un FAIT sur le métier — « un ministre ne
 * dépose pas d'amendement » — et il se distingue d'une liste vide, qui est un
 * fait sur la collecte.
 */
function cellule({ nombre, objet, sur = null, objetSur = null, quantifieur = null, detail = null }) {
  return { nombre, objet, sur, objetSur, quantifieur, detail };
}

function celluleAbsente(motif) {
  return { absent: motif };
}

/* LA BARRE DES STADES EST RETIRÉE (maquette « En bref », 11/09/2026) : le bloc
 * ne garde que des nombres. Les stades se lisent dans la cascade de « Ce qu'il
 * a proposé », qui les porte déjà un par un. */

/* ── Le bloc ─────────────────────────────────────────────────────────────────
 *
 * Les cinq lignes sont ordonnées par DEGRÉ D'ENGAGEMENT sur la nature des
 * actes — porter un texte, l'amender, siéger là où il s'examine, interroger,
 * parler — jamais sur les personnes.
 */
export const RANGS_GRANDS_CHIFFRES = [
  { cle: 'textes', titre: 'Textes portés' },
  { cle: 'amendements', titre: 'Amendements' },
  { cle: 'commissions', titre: 'Mandats en commission' },
  { cle: 'questions', titre: 'Questions au gouvernement' },
  { cle: 'interventions', titre: 'Interventions' },
];

export function grandsChiffres({
  roles = [],
  mandats = [],
  amendements = null,
  amendementsParVersant = null,
  textes = null,
  interventions = [],
  appartenances = [],
}) {
  const sieges = roles.filter((r) => r.institution === INSTITUTION_PARLEMENT);
  const pistesDeSiege = ORDRE_COLONNES.filter(
    (piste) => piste !== INSTITUTION_GOUVERNEMENT && sieges.some((r) => pisteDuRole(r) === piste),
  );
  const aParlement = pistesDeSiege.length > 0;
  const aGouvernement = roles.some((r) => r.institution === INSTITUTION_GOUVERNEMENT);

  /* LA PISTE FRANÇAISE D'UN PROFIL — celle où atterrit une matière que la
   * source rattache au référentiel de l'Assemblée sans dire de quel siège elle
   * vient. Un sénateur qui dépose une proposition de loi la voit enregistrée
   * par l'Assemblée qui l'examine : la ranger « à l'Assemblée » ferait de
   * Retailleau un député. Elle va donc à son seul siège français, le Sénat. */
  const pisteFrancaise = pistesDeSiege.includes(INSTITUTION_PARLEMENT)
    ? INSTITUTION_PARLEMENT
    : (pistesDeSiege.includes(INSTITUTION_SENAT) ? INSTITUTION_SENAT : INSTITUTION_PARLEMENT);

  let cas = CAS_RIEN_A_MONTRER;
  if (aParlement && aGouvernement) cas = CAS_DEUX_ROLES;
  else if (aParlement) cas = CAS_PARLEMENT_SEUL;
  else if (aGouvernement) cas = CAS_GOUVERNEMENT_SEUL;

  const colonnes = [...pistesDeSiege];
  if (aGouvernement) colonnes.push(COLONNE_GOUVERNEMENT);

  if (cas === CAS_RIEN_A_MONTRER) {
    // Quatre des treize candidats déclarés n'ont ni mandat parlementaire ni
    // appartenance gouvernementale — un mandat européen, une mairie. Le bloc
    // n'a rien à montrer, et il le DIT plutôt que d'afficher cinq tirets :
    // l'arbitrage sur ces deux formes d'activité est ouvert, pas rendu.
    return { cas, colonnes, lignes: [] };
  }

  /* Le partage des interventions est DATÉ, jamais global. `depuisLeBancDuGouvernement`
   * rend une qualité pour tout le profil ; ici il faut savoir, pour chaque prise
   * de parole, de quel banc elle vient — c'est la date d'appartenance qui le dit,
   * et rien d'autre. Une intervention sans date n'est attribuée à aucun banc. */
  const auBanc = (date) =>
    Boolean(date) && appartenances.some((a) => a.debut <= date && date <= (a.fin || '9999-12-31'));

  /* Une prise de parole européenne ne se partage pas entre les bancs français :
   * elle a lieu dans un autre hémicycle. Elle est donc lue sur sa source, avant
   * la règle de date — sans quoi les 1 803 interventions européennes de
   * Mélenchon se répartiraient entre « À l'Assemblée » et « Au gouvernement ». */
  const estEuropeenne = (i) => (i?.source?.institution) === INSTITUTION_PE_SOURCE;
  const coteDe = (i) => {
    if (estEuropeenne(i)) return INSTITUTION_PE;
    return auBanc(i.date) ? COLONNE_GOUVERNEMENT : pisteFrancaise;
  };
  const cotes = Object.fromEntries(ORDRE_COLONNES.map((p) => [p, []]));
  for (const i of interventions) cotes[coteDe(i)].push(i);

  const lignes = [];

  // 1. Textes portés — le RÔLE publié range le texte (#689), jamais son intitulé :
  //    313 des 414 entrées publiées par les 13 candidats déclarés sont des projets
  //    de loi portés au nom du gouvernement, qui ne sont pas un acte personnel.
  //
  //    Les rôles sont nommés un par un plutôt que repliés sur l'institution :
  //    être RAPPORTEUR d'une proposition n'est pas en être l'auteur, et « 3
  //    propositions de loi » pour 2 propositions et 1 rapport serait faux.
  const tousPublies = textes?.publies ?? [];
  const europeens = tousPublies.filter((t) => t.europeen);
  const publies = tousPublies.filter((t) => !t.europeen);
  const ROLES_PROPOSITION = ['auteur_proposition_de_loi', 'auteur_proposition_de_resolution'];
  const propositions = publies.filter((t) => ROLES_PROPOSITION.includes(t.roleCle));
  const projets = publies.filter((t) => t.roleCle === 'initiateur_projet_de_loi');
  const autresRoles = publies.filter(
    (t) => !ROLES_PROPOSITION.includes(t.roleCle) && t.roleCle !== 'initiateur_projet_de_loi',
  );
  // Ce que le seuil de publication écarte SE DIT. AGENTS.md §6 ne publie par
  // défaut qu'un texte parvenu au moins en commission ; taire les autres ferait
  // lire « 2 » comme « il n'en a déposé que 2 » (§2 règle 5).
  const ecartes = textes?.ecartes?.total ?? 0;
  const detailTextes = [
    autresRoles.length
      ? `${formatNumber(autresRoles.length)} ${pluriel(autresRoles.length, 'texte porté à un autre titre', 'textes portés à un autre titre')} (${[...new Set(autresRoles.map((t) => t.role))].join(', ')})`
      : null,
    ecartes
      ? `${formatNumber(ecartes)} ${pluriel(ecartes, 'texte déposé n’est pas compté', 'textes déposés ne sont pas comptés')} : la fiche ne publie que ce qui est parvenu au moins en commission`
      : null,
  ]
    .filter(Boolean)
    .join(' · ');
  const celluleTextes = (lot, objet, detail) =>
    lot.length
      ? cellule({ nombre: lot.length, objet, detail: detail || null })
      : null;
  /* LES TEXTES PORTÉS AU PARLEMENT EUROPÉEN (#901). `textes.publies` ne porte
   * que la liste française depuis que les textes européens ont leur propre
   * cascade : filtrer dessus rendait une cellule toujours vide, et les 45 textes
   * européens d'Emmanuel Maurel n'apparaissaient pas ici. Le compte est celui
   * que publie la cascade européenne — tout stade sauf la phase préparatoire
   * (AGENTS.md §6) —, et ce qu'elle écarte se dit, comme côté français. */
  const europe = textes?.europe ?? null;
  const celluleTextesEuropeens = europe?.total
    ? cellule({
      nombre: europe.total,
      objet: pluriel(europe.total, 'texte porté', 'textes portés'),
      detail: europe.horsSeuil
        ? `${formatNumber(europe.horsSeuil)} ${pluriel(europe.horsSeuil, 'texte en phase préparatoire n’est pas compté', 'textes en phase préparatoire ne sont pas comptés')} : la fiche ne publie que ce qui a dépassé cette phase`
        : null,
    })
    : null;
  lignes.push({
    cle: 'textes',
    titre: 'Textes portés',
    cellules: {
      [pisteFrancaise]: celluleTextes(propositions, 'propositions de loi', detailTextes),
      [INSTITUTION_PE]: celluleTextesEuropeens,
      [COLONNE_GOUVERNEMENT]: celluleTextes(projets, 'projets de loi', null),
    },
  });

  // 2. Amendements. Le COUPLE dépôts / dossiers, jamais le compte seul : deux
  //    nombres qui varient en sens inverse appellent une lecture, un nombre seul
  //    appelle un classement (§2 règle 1).
  /* DEUX CELLULES, UNE PAR PARLEMENT (#901). La cellule « À l'Assemblée »
   * comptait tous les dépôts mais seulement les dossiers de l'AN : Emmanuel
   * Maurel y lisait « 2 944 amendements sur 18 dossiers législatifs », dont
   * 2 609 déposés au Parlement européen. Chaque parlement a désormais sa
   * cellule, avec ses dépôts ET ses dossiers.
   *
   * Côté européen, le mot « législatif » n'est pas repris : 105 des 170
   * dossiers amendés par Maurel sont des rapports d'initiative (INI), et les
   * 5 de Jean-Luc Mélenchon le sont tous. */
  const celluleDepots = (lot, dossier, dossiers) => {
    const d = lot?.dossiers ?? null;
    const totalAuteur = lot?.totalAuteur ?? 0;
    if (totalAuteur === 0) return null;
    // La CONCENTRATION ne s'affirme que là où elle se prouve : ce dossier doit
    // porter plus que tous les autres réunis. Aucune constante arbitraire —
    // c'est un fait, pas un seuil. Un percentile a été essayé et écarté : il
    // sélectionne toujours 10 % des dossiers, donc il ne peut JAMAIS se taire.
    const tete = (d?.nommes ?? []).slice().sort((a, b) => (b.depots ?? 0) - (a.depots ?? 0))[0] ?? null;
    const concentre = tete && tete.depots * 2 > totalAuteur ? tete : null;
    // LE TOTAL EN TÊTE, LE DÉTAIL DESSOUS (maquette « En bref », 11/09/2026) :
    // « 2 968 et 25 » au même corps se lisaient comme une fraction.
    return cellule({
      nombre: totalAuteur,
      objet: 'amendements',
      quantifieur: d?.distincts != null
        ? { avant: 'sur', nombre: d.distincts, texte: pluriel(d.distincts, dossier, dossiers) }
        : null,
      detail: concentre
        ? `${formatNumber(concentre.depots)} d’entre eux sur « ${concentre.titre} »`
        : null,
      // Les dossiers se listent PAR DATE, jamais par volume : déposer beaucoup
      // sur un texte peut être un travail de fond comme une stratégie de
      // blocage, et le nombre ne les distingue pas.
    });
  };
  const celluleAmendements = celluleDepots(
    amendementsParVersant?.francais ?? amendements,
    'dossier législatif',
    'dossiers législatifs',
  );
  /* « dossier », et non « dossier législatif » : 105 des 170 dossiers amendés
   * par Emmanuel Maurel sont des rapports d'initiative, et les 5 de Jean-Luc
   * Mélenchon le sont tous. */
  const celluleAmendementsUe = celluleDepots(amendementsParVersant?.europeens, 'dossier', 'dossiers');
  lignes.push({
    cle: 'amendements',
    titre: 'Amendements',
    cellules: {
      [pisteFrancaise]: celluleAmendements,
      [INSTITUTION_PE]: celluleAmendementsUe,
      [COLONNE_GOUVERNEMENT]: celluleAbsente('un ministre ne dépose pas d’amendement'),
    },
  });

  // 3. Mandats en commission. Le NOMBRE DE MANDATS et le nombre de commissions
  //    DISTINCTES ne disent pas la même chose : 67 mandats sur 14 commissions,
  //    c'est une réélection, pas une dispersion.
  // La commission se range sur `categorie_source`, l'estampille de la collecte :
  // `europarl` pour les commissions et intergroupes du Parlement européen, `an`
  // pour le référentiel de l'Assemblée. C'est une donnée, pas une déduction sur
  // l'intitulé (§2 règle 2) — les 4 commissions de Glucksmann sont européennes.
  const commissions = mandats.filter((m) => m.categorie === 'commission' && m.label);
  const celluleCommissions = (lot) => {
    if (!lot.length) return null;
    const parCommission = new Map();
    for (const m of lot) parCommission.set(m.label, (parCommission.get(m.label) || 0) + 1);
    const classees = [...parCommission.entries()].sort(
      (a, b) => b[1] - a[1] || a[0].localeCompare(b[0], 'fr'),
    );
    // Le TOTAL des mandats en tête ; la commission la plus fréquentée dessous,
    // à côté du nombre de commissions distinctes.
    return cellule({
      nombre: lot.length,
      objet: pluriel(lot.length, 'mandat', 'mandats'),
      quantifieur: {
        nombre: parCommission.size,
        texte: pluriel(parCommission.size, 'commission distincte', 'commissions distinctes'),
        suite: `${formatNumber(classees[0][1])} à la ${classees[0][0]}`,
      },
    });
  };
  lignes.push({
    cle: 'commissions',
    titre: 'Mandats en commission',
    cellules: {
      [pisteFrancaise]: celluleCommissions(commissions.filter((m) => m.categorie_source !== 'europarl')),
      [INSTITUTION_PE]: celluleCommissions(commissions.filter((m) => m.categorie_source === 'europarl')),
      [COLONNE_GOUVERNEMENT]: celluleAbsente('un ministre ne siège pas en commission'),
    },
  });

  // 4. Questions au gouvernement. LE MÊME OBJET DE CHAQUE CÔTÉ, et deux actes
  //    opposés : on la pose depuis les bancs, on y répond depuis le banc. Les
  //    deux ne s'additionnent pas et ne se comparent pas.
  const qg = (cote) => cotes[cote].filter((i) => i.type_detail === 'question_gouvernement');
  const celluleQuestions = (cote, objet) => {
    const lot = qg(cote);
    if (!lot.length) return null;
    const sujets = new Set(lot.map((i) => i.sujet).filter(Boolean));
    return cellule({
      nombre: lot.length,
      objet,
      quantifieur: sujets.size
        ? { nombre: sujets.size, texte: pluriel(sujets.size, 'sujet distinct', 'sujets distincts') }
        : null,
    });
  };
  lignes.push({
    cle: 'questions',
    titre: 'Questions au gouvernement',
    cellules: {
      [pisteFrancaise]: celluleQuestions(pisteFrancaise, 'posées'),
      [COLONNE_GOUVERNEMENT]: celluleQuestions(COLONNE_GOUVERNEMENT, 'prises de parole depuis le banc'),
    },
  });

  // 5. Interventions. « SITUÉES » porte la limite sans phrase : le chiffre se
  //    rapporte aux interventions dont le compte rendu donne un point de l'ordre
  //    du jour, pas à toutes. Chaque colonne compte contre SON propre total.
  const celluleInterventions = (cote) => {
    const lot = cotes[cote];
    if (!lot.length) return null;
    const situees = lot.filter((i) => i.sujet);
    if (!situees.length) return null;
    const parSujet = new Map();
    for (const i of situees) parSujet.set(i.sujet, (parSujet.get(i.sujet) || 0) + 1);
    const classes = [...parSujet.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], 'fr'));
    // Le TOTAL des interventions en tête ; « 309 sur les retraites » était un
    // détail affiché plus gros que le total qu'il détaille.
    return cellule({
      nombre: lot.length,
      objet: pluriel(lot.length, 'intervention', 'interventions'),
      quantifieur: {
        nombre: situees.length,
        texte: pluriel(situees.length, 'située', 'situées'),
        suite: `${formatNumber(parSujet.size)} ${pluriel(parSujet.size, 'sujet distinct', 'sujets distincts')}`,
      },
      detail: `${formatNumber(classes[0][1])} sur « ${classes[0][0]} »`,
    });
  };
  lignes.push({
    cle: 'interventions',
    titre: 'Interventions',
    cellules: Object.fromEntries(colonnes.map((c) => [c, celluleInterventions(c)])),
  });

  // Une ligne dont AUCUNE colonne ne porte de chiffre ne s'affiche pas : cinq
  // rangs vides ne décrivent pas une personne, ils décrivent le gabarit.
  const retenues = lignes.filter((l) => colonnes.some((c) => l.cellules[c] && !l.cellules[c].absent));

  return { cas, colonnes, lignes: retenues };
}

/* ── Livrable : ce qu'on n'a pas pu lire ─────────────────────────────────────
 *
 * `couverture` porte la cause sur 481 / 481 profils. Les états ne disent pas la
 * même chose et ne se confondent pas (§2 règle 5) : `couvert` est une mesure,
 * `hors_couverture` parle de la source, `non_collecte` parle de la collecte.
 * Les libellés viennent d'`EMPTY_LIST_CAUSES` (lot 1) — ils ne sont pas
 * réécrits ici.
 */
export const LISTES_COUVERTES = [
  { cle: 'mandats', titre: 'Mandats et fonctions' },
  { cle: 'votes', titre: 'Votes' },
  { cle: 'amendements', titre: 'Amendements' },
  { cle: 'textes_portes', titre: 'Textes portés' },
  { cle: 'interventions', titre: 'Interventions' },
];

/* ── Règle : une liste vide dit de quelle sorte de vide il s'agit ────────────
 *
 * Les quatre causes d'`EMPTY_LIST_CAUSES` (lot 1) n'affirment pas la même
 * chose, et `couverture` en porte souvent DEUX pour une même liste : « couvert
 * depuis 2012 » et « hors couverture avant ». Quand la liste est vide, c'est la
 * cause la plus spécifique qui explique le vide — une collecte écartée le dit
 * mieux qu'une borne de source, et une borne de source mieux qu'un zéro mesuré.
 * L'ordre est donc une priorité, pas un tri.
 */
const PRIORITE_CAUSES = ['non_collecte', 'hors_couverture', 'fait_etabli', 'couvert'];

export function causeListeVide(entrees) {
  const etats = (entrees || []).map((e) => e.etat);
  return PRIORITE_CAUSES.find((c) => etats.includes(c)) ?? null;
}

/* ── Règle : la borne de source n'est plus rendue sur la fiche ───────────────
 *
 * CE QUE LA FICHE GARDE, ET CE QUI PART. Une preuve de borne — « l'Assemblée
 * nationale ne publie pas de scrutins avant la XIVe législature… » — ne dit
 * rien de la personne affichée : elle dit ce que l'Assemblée publie. Elle était
 * recopiée sur toutes les fiches, où elle se lisait comme une limite DE CETTE
 * PERSONNE. Elle vit désormais une fois, sur `/couverture` (#328).
 *
 * L'ÉTAT DATÉ, LUI, RESTE. « Couvert depuis le 20.06.2012 » est ce qui empêche
 * de lire une liste vide comme une absence d'activité (§2 règle 5) : c'est la
 * ligne, pas sa preuve, qui porte cette fonction.
 *
 * LE DISCRIMINANT EST L'ÉTAT, ET IL EST GARANTI À LA SOURCE — pas reconnu au
 * texte. `couverture_profil._deriver` attache `borne.preuve` à `couvert` et à
 * `hors_couverture`, et bascule sur `fait_etabli` dès que la preuve devient
 * propre à la personne (« aucun acteur AMO30 pour X »). `non_collecte` porte
 * une décision de run. Vérifié sur les 32 fiches de candidats déclarés :
 * partition exacte, zéro exception — 180 entrées de borne sur 286, soit 6 413
 * des 8 328 mots de preuve rendus (77 %).
 *
 * LA PREUVE QUI RESTE SE DIT UNE FOIS POUR LA SECTION, plus une fois par liste.
 * #802 avait délibérément limité la mémoire à la liste, parce qu'une mémoire
 * partagée aurait fait disparaître la borne AMO30 de « Votes » après que
 * « Mandats » l'a écrite. Cette raison tombe avec la borne : ce qui reste est
 * propre à la personne ou au run, identique d'une liste à l'autre, et se répète
 * cinq fois pour rien — 700 mots sur la fiche Retailleau, dont le certificat de
 * suspension Sénat/LR compte 140 mots par liste.
 */
export const ETATS_PORTANT_LA_BORNE = new Set(['couvert', 'hors_couverture']);

export function couvertureDesListes(couverture, decomptes) {
  const dites = new Set();
  return LISTES_COUVERTES.map(({ cle, titre }) => {
    const entrees = (couverture || {})[cle] || [];
    return {
      cle,
      titre,
      decompte: decomptes[cle] ?? null,
      etats: entrees.map((e) => {
        const borne = ETATS_PORTANT_LA_BORNE.has(e.etat);
        const preuve = borne ? null : e.preuve ?? null;
        const dejaDite = Boolean(preuve) && dites.has(preuve);
        if (preuve) dites.add(preuve);
        return {
          etat: e.etat,
          cause: e.cause ?? null,
          debut: e.portee?.debut ?? null,
          fin: e.portee?.fin ?? null,
          preuve,
          preuveDejaDite: dejaDite,
        };
      }),
    };
  });
}

/* ── Règle : une limite se déclare, elle ne se comble pas ────────────────────
 *
 * Quatre manques que la trame suppose et que le corpus ne porte pas. Ils sont
 * CALCULÉS sur le profil affiché, pas recopiés en dur : une limite écrite à la
 * main survit à sa cause, et c'est ainsi qu'un transitoire devient permanent.
 *
 * `meta.avertissements` (#642) ne fournit aujourd'hui que des messages dont le
 * `destinataire` vaut `interne` — ils ne sont donc pas affichés. La clé est
 * lue, pas devinée : un avertissement `lecteur` apparaîtra le jour où il en
 * sera écrit un, sans toucher à ce composant.
 */
/* Le premier jour des données publiées par l'Assemblée — la XIIe législature.
 * Sa jumelle, qui valide la table, est `BORNE_COUVERTURE_AN` dans
 * `src/mandats_anterieurs.py` : aucune sortie ne la porte, et une borne
 * structurelle ne vieillit pas comme une borne de fraîcheur (#484). */
export const JOUR_BORNE_AN = '19 juin 2002';

export function limitesDeclarees({ profil, roles, sieges }) {
  /* CES TEXTES SONT DES LIMITES, PAS DES EXPLICATIONS (#328).
   *
   * Chacun dit UN fait sur CE profil, avec ses nombres. Le « pourquoi » — la
   * qualification d'un groupe n'est pas déductible d'un comportement de vote,
   * un enregistrement écarté est une collecte qu'on ne peut plus vérifier —
   * vit dans la méthodologie, sous l'ancre `#couverture` où mène le renvoi
   * posé sous la liste. DESIGN_SYSTEM §7 règle 2 : « une limite tient en deux
   * mots, une explication en paragraphe ». Une phrase ajoutée ici est une
   * phrase qui manque là-bas.
   */
  const limites = [];

  for (const a of profil?.meta?.avertissements || []) {
    if (a.destinataire === 'lecteur') limites.push({ cle: `avertissement:${a.message}`, texte: a.message });
  }

  /* DEUX CORRECTIONS SUR LA MÊME PHRASE (#328).
   *
   * « dont la législature en cours » était écrit en dur et n'était vérifié
   * nulle part : sur Bruno Retailleau, dont le mandat à l'Assemblée est clos
   * depuis longtemps, la fiche l'affirmait quand même (§2 règle 2).
   *
   * Et la limite ne se déclenche plus À PARTIR D'UN SEUL mandat : « la
   * qualification n'est pas déclarée sur 1 des mandats parlementaires » d'un
   * profil qui n'en a qu'un ne décrit aucune lacune de corpus — c'est la
   * situation ordinaire, et l'écrire ajoute une ligne qui ne dit rien. */
  /* La phrase nomme l'ASSEMBLÉE : elle ne peut donc compter que des mandats de
   * députée ou de député. Un mandat européen ou sénatorial n'a pas de
   * qualification de groupe non déclarée « par l'Assemblée » — l'Assemblée n'en
   * dit rien, et n'a pas à en dire. Mesuré le 10/09/2026 : sur Mélenchon, la
   * limite comptait 5 mandats parlementaires — un à l'Assemblée, un au Sénat,
   * deux au Parlement européen et un non estampillé (§2 règle 2). */
  const aLAssemblee = roles.filter((r) => pisteDuRole(r) === INSTITUTION_PARLEMENT);
  const sansPosition = aLAssemblee.filter((r) => !r.position);
  const parlementaires = aLAssemblee;
  if (sansPosition.length > 1 || (sansPosition.length === 1 && parlementaires.length > 1)) {
    limites.push({
      cle: 'position-non-declaree',
      texte:
        `La qualification du groupe — majoritaire, minoritaire, d'opposition — n'est pas déclarée ` +
        `par l'Assemblée sur ${sansPosition.length} de ses ${parlementaires.length} mandats parlementaires.`,
    });
  }

  const aExerce = (profil?.mandats || []).some(
    (m) => m.categorie === 'fonction_gouvernementale' && m.fonction === FONCTION_MEMBRE,
  );
  const electifs = (profil?.mandats || []).filter((m) => m.categorie === 'mandat_electif');
  if (aExerce && electifs.length && electifs.every((m) => m.suspendu_pour_fonction_gouvernementale == null)) {
    limites.push({
      cle: 'suspension',
      texte:
        `Le corpus ne dit pas si un mandat s'est arrêté parce que la personne entrait au gouvernement : ` +
        `« suspendu_pour_fonction_gouvernementale » n'est renseigné sur aucun de ses ${electifs.length} `
        + `mandat${electifs.length > 1 ? 's' : ''} électif${electifs.length > 1 ? 's' : ''}.`,
    });
  }

  /* LA LIMITE « PROJETS DE LOI » EST RETIRÉE : elle décrivait un corpus qui a
   * changé (#328). Elle affirmait que projets et propositions sont « rangés
   * sous le même rôle "auteur" » et que « seul l'intitulé officiel les
   * distingue ». Mesuré sur les textes portés des 32 fiches de candidats
   * déclarés : `role` les sépare sur 570 des 575 — `initiateur_projet_de_loi`
   * (313) contre `auteur_proposition_de_loi` (183) et
   * `auteur_proposition_de_resolution` (59) ; les 5 restants portent `auteur`
   * sans `nature_texte`. Le fait vrai — combien de textes sont des projets de
   * loi signés comme ministre — reste publié sous la cascade de « Ce qui est
   * proposé », et la répartition sur `/couverture`. */

  /* LES MANDATS QUE LE CORPUS NE PEUT PAS PORTER (#860).
   *
   * `mandats_anterieurs` ne vient d'aucune collecte : c'est une table relue à
   * la main, une ligne par mandat, chacune sur sa source primaire — Sycomore
   * pour un siège, un décret au Journal officiel pour une fonction. Sa place
   * est donc ici et nulle part ailleurs sur la fiche : un fait cité n'a ni
   * vote, ni amendement, ni intervention derrière lui, et le poser sur la frise
   * du parcours ferait lire « couvert depuis 1988 » là où rien ne l'est.
   *
   * Une fiche NON RELUE (`null` + `non_relu`) ne produit aucune limite : elle
   * dirait que la relecture n'a pas eu lieu, ce qui parle de notre travail et
   * non de cette personne. */
  const anterieurs = profil?.mandats_anterieurs || [];
  if (anterieurs.length) {
    const parInstitution = anterieurs.reduce((acc, m) => {
      acc[m.institution] = (acc[m.institution] || 0) + 1;
      return acc;
    }, {});
    const detail = [
      parInstitution.assemblee_nationale ? `${parInstitution.assemblee_nationale} à l’Assemblée` : null,
      parInstitution.gouvernement ? `${parInstitution.gouvernement} au gouvernement` : null,
    ].filter(Boolean);
    const n = anterieurs.length;
    const pluriel = n > 1;
    limites.push({
      cle: 'mandats-anterieurs',
      texte:
        `${n} mandat${pluriel ? 's' : ''} exercé${pluriel ? 's' : ''} avant le ${JOUR_BORNE_AN}`
        + (detail.length > 1 ? ` — ${detail.join(', ')} —` : '')
        + ` ${pluriel ? 'sont cités' : 'est cité'} depuis ${pluriel ? 'leur' : 'sa'} source primaire. `
        + `Aucune activité n’y est collectée.`,
    });
  }

  const enregistrements = electifs.length;
  if (sieges && enregistrements > sieges.length) {
    limites.push({
      cle: 'sieges-replies',
      texte:
        `${enregistrements} enregistrements de mandat électif pour ${sieges.length} sièges, regroupés sur ` +
        `leur date de fin. Aucun n'est supprimé.`,
    });
  }

  return limites;
}
