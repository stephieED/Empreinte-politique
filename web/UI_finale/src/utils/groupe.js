/*
 * Les règles de lecture d'une FICHE DE GROUPE — lot 3 de la refonte #324
 * (issue #329), reprise de bout en bout.
 *
 * Ce module ne dessine rien et ne redéfinit rien : les six fondations du lot 1
 * vivent dans `utils/lecture.js` (`ratio`, `truncation`, `emptyListMessage`,
 * `sourceBadge`, `styleForPosition`, `formatNumber`, `isWholeTextVote`,
 * `normalizeLabel`) et sont consommées ici. Ce qui est propre au groupe — et
 * seulement cela — est écrit ici.
 *
 * LA PREMIÈRE VERSION DE CETTE FICHE ÉTAIT ÉDITORIALEMENT IRRÉPROCHABLE ET
 * STRUCTURELLEMENT INUTILISABLE. Ses sections s'appelaient « Cohésion de vote »,
 * « Empreinte thématique », « Amendements déposés » : le vocabulaire du schéma,
 * pas les questions de quelqu'un qui cherche à comprendre un groupe. Et son fait
 * le plus important — sur 3 843 scrutins, la cohésion de `AN:SOC:16` n'est
 * mesurable que sur 341 — était enterré en fin de section « Vérification ».
 *
 * L'ordre est donc celui des questions, une seule focale à la fois, l'interne
 * d'abord et la comparaison à la fin :
 *
 *   1. qui sont-ils · 2. sur quoi ils choisissent de travailler ·
 *   3. ce qu'ils proposent et ce qu'il en reste · 4. comment ils votent ·
 *   5. comment ils se situent · 6. ce que cette fiche ne dit pas.
 *
 * La POSTURE — `majorite`, `opposition`, `minoritaire`, déclarées par
 * l'Assemblée (#686) — apparaît là où elle change le sens d'un chiffre, nulle
 * part ailleurs. Répétée partout, elle devient un avertissement, et un
 * avertissement répété devient une excuse.
 *
 * Deux populations, jamais mélangées (AGENTS.md §3) : une fiche de groupe
 * agrège les 468 profils `roster_groupe`, qui n'ont pas de page à eux. Aucun
 * chiffre de ce module ne parle des 13 candidats déclarés.
 *
 * Chiffres cités : mesurés au commit `e40d0d32` le 01/09/2026, sur les 7 fiches
 * publiées — 5 pour l'Assemblée nationale (XVIe législature) et 2 pour le Sénat,
 * gelées et jamais régénérées depuis #528/#516. Seule exception, remesurée sur
 * le commit de données `693b076d` du 01/09/2026 : la posture des groupes, qui
 * n'existait sur aucune fiche à l'écriture du module et en couvre 5 depuis.
 */

import {
  MENTION_DE_LECTURE_PARTOUT,
  formatNumber,
  isWholeTextVote,
  normalizeLabel,
  ratio,
} from './lecture.js';

/* ── Règle : aucun compteur ne veut dire « aujourd'hui » ─────────────────────
 *
 * Une fiche de groupe décrit UNE législature, et aucune des 7 publiées ne
 * décrit celle en cours (#653). Trois compteurs prétendaient au présent et
 * mesuraient en réalité la carrière ULTÉRIEURE des membres : `effectif.actuel`
 * égalait, exactement, le nombre de membres portant un mandat électif ouvert —
 * 38/38 sur `AN:LR:16`, 85/85 sur `AN:REN:16`, 60/60 sur `AN:LFI:16`, c'est-à-dire les
 * réélu⋅es de 2024, pas les membres du groupe en juin 2024.
 *
 * Les noms longs (`a_la_date_de_reference`) sont longs exprès. Ce module les
 * lit, et lit AUSSI les anciens noms, parce que les 2 fiches Sénat gelées ne
 * seront pas régénérées : exiger la clé ferait échouer le portail de qualité
 * sur des fichiers déjà publiés.
 */
export const ORIGINES_DATE_REFERENCE = {
  derniere_appartenance_close: 'dernière appartenance close',
  // #808 : l'ancien nom, gardé en lecture. Il annonçait un événement que deux
  // fiches sur douze n'ont pas connu — `NG-15` s'arrête 3 ans 9 mois avant la
  // clôture de la XVe. Les fiches qui le portent encore doivent rester
  // lisibles jusqu'à leur régénération.
  cloture_legislature: 'dernière appartenance close',
  generation: 'date de génération de la fiche',
};

/*
 * `{ date, origine, origineLabel, datee }`. `datee: false` dit que la fiche ne
 * rapporte ses comptes à AUCUNE date — ce n'est pas « aujourd'hui », et c'est
 * exactement ce qu'il faut écrire à l'écran plutôt qu'inventer une date.
 */
export function dateDeReference(groupe) {
  const bloc = groupe?.date_reference;
  const date = bloc?.date ?? null;
  const origine = bloc?.origine ?? null;

  return {
    date,
    origine,
    origineLabel: origine ? (ORIGINES_DATE_REFERENCE[origine] ?? origine) : null,
    datee: Boolean(date),
  };
}

/*
 * L'effectif, sous les deux noms. `a_la_date_de_reference` (#653) d'abord ;
 * `actuel` ensuite, et alors le compte n'est rapporté à aucune date.
 *
 * Le dénominateur publié est le nombre d'entrées de `membres[]` — la couverture
 * disponible de la fiche —, jamais `meta.couverture_roster.roster_total`, qui
 * compte des membres dont aucun profil n'est publié. Les deux diffèrent : 75
 * sur 76 pour `AN:LFI:16`, 169 sur 193 pour `AN:REN:16`.
 */
export function effectifDuGroupe(groupe) {
  const bloc = groupe?.effectif || {};
  const aLaDate = bloc.a_la_date_de_reference;
  const ancien = bloc.actuel;
  const valeur = Number.isFinite(aLaDate) ? aLaDate : (Number.isFinite(ancien) ? ancien : null);

  return {
    valeur,
    denominateur: (groupe?.membres || []).length,
    // `true` quand la valeur vient du champ daté, donc quand elle se rapporte
    // à `date_reference`. `false` sur les 2 fiches Sénat.
    rapporteALaDate: Number.isFinite(aLaDate),
  };
}

/*
 * Un mandat agrégé porte DEUX quantités, jamais une (#656) : « qui y siège » et
 * « qui y est passé ». 43 % des adhésions de commission publiées durent une
 * journée ou moins — un⋅e député⋅e n'appartient qu'à une commission permanente
 * à la fois, si bien que tout passage temporaire est écrit dans le référentiel
 * comme un mandat à part entière. Lire le cumul comme un effectif faisait dire
 * à la fiche que 67 des 76 membres LFI siégeaient aux finances quand ils sont 5.
 *
 * Les deux anciens noms (`nb_membres_actifs`, `nb_membres`) sont lus aussi :
 * sans ce repli les 17 cartes de mandats des 2 fiches Sénat rendaient
 * `undefined membre y a siégé au moins une fois`, et « Aucun membre n'y
 * siégeait » sur une donnée simplement absente (AGENTS.md §2 règle 5).
 */
export function siegeEtPasse(mandat, effectifDeSecours) {
  const siege = Number.isFinite(mandat?.nb_membres_a_la_date_de_reference)
    ? mandat.nb_membres_a_la_date_de_reference
    : (Number.isFinite(mandat?.nb_membres_actifs) ? mandat.nb_membres_actifs : null);
  const passe = Number.isFinite(mandat?.nb_membres_cumul_historique)
    ? mandat.nb_membres_cumul_historique
    : (Number.isFinite(mandat?.nb_membres) ? mandat.nb_membres : null);

  return {
    siege,
    passe,
    effectif: Number.isFinite(mandat?.effectif_reference)
      ? mandat.effectif_reference
      : effectifDeSecours,
    // `true` seulement si le compte vient du champ daté : sinon il ne se
    // rapporte à aucune date, et la section le dit une fois pour toutes.
    siegeRapporteALaDate: Number.isFinite(mandat?.nb_membres_a_la_date_de_reference),
  };
}

/* ── Règle : les absences ne franchissent jamais l'écran ─────────────────────
 *
 * Une entrée de `cohesion_votes` porte six décomptes qui partitionnent
 * exactement `membres_eligibles` — vérifié sur les 19 832 entrées des 5 fiches
 * AN. Deux d'entre eux ne sortent pas du fichier :
 *
 *  - `absents` compte les membres éligibles pour lesquels AUCUN vote n'a été
 *    trouvé sur ce scrutin. Publié, agrégé ou non, il devient un taux de
 *    présence sur des personnes nommées (AGENTS.md §2 règle 3).
 *  - `excuses` vaut 0 sur les 19 832 entrées publiées, faute de position
 *    `excuse` dans le corpus. Un zéro structurel affiché comme un zéro mesuré
 *    affirmerait « personne n'était excusé » (§2 règle 5).
 *
 * La version précédente de cette fiche les publiait sous des libellés prudents
 * (« Sans trace de vote », « Excusés »). Un libellé prudent sur une donnée
 * interdite reste la donnée interdite : la refonte les retire de la lecture,
 * et ce module ne les lit plus nulle part.
 */
export const DECOMPTES_JAMAIS_PUBLIES = ['absents', 'excuses'];

/*
 * Les quatre décomptes lisibles. `non_votant` n'est pas une position exprimée :
 * il compte dans la participation à un scrutin, jamais dans les voix qui
 * disent quelque chose (voir `POSITIONS_EXPRIMEES`).
 */
export const DECOMPTES_LISIBLES = ['pour', 'contre', 'abstention', 'non_votant'];

/*
 * Les trois positions qui expriment un sens. C'est sur elles, et sur elles
 * seules, que « le groupe a parlé d'une seule voix » se décide.
 */
export const POSITIONS_EXPRIMEES = ['pour', 'contre', 'abstention'];

/* ── Règle : la posture apparaît là où elle change le sens d'un chiffre ──────
 *
 * `position_politique` (#686) est une qualification DÉCLARÉE PAR L'ASSEMBLÉE et
 * recopiée : `organe.positionPolitique` du référentiel AMO30. Elle n'est jamais
 * déduite d'un comportement de vote — un groupe qui vote souvent contre n'est
 * pas « d'opposition » parce qu'il vote contre, il l'est parce que l'Assemblée
 * l'écrit (§2 règle 1).
 *
 * Elle a atterri le 01/09/2026, au commit de données `693b076d` : **5 des 7
 * fiches la portent** — `AN:REN:16` en `majorite`, `AN:LFI:16`/`AN:LR:16`/`AN:RN:16`/`AN:SOC:16`
 * en `opposition`, toutes sourcées sur l'archive AMO30 avec leur `verifie_le`.
 * `AN:SOC:16` réunit ses deux organes successifs (`SOC` puis `SOC-A`), qui portent
 * la même valeur. Les 2 fiches du Sénat restent sans posture : elles sont gelées
 * depuis #516 et ne seront pas régénérées — `postureDuGroupe` y rend
 * `declaree: false`, et le rendu l'écrit. Il ne la simule pas, il ne la dérive
 * pas, et cette absence-là est définitive, pas transitoire.
 *
 * Le vocabulaire est fermé (`POSITIONS_POLITIQUES_GROUPE`, schema_groupe.py) et
 * `non_declaree` en fait partie : c'est une VALEUR PUBLIÉE, distincte d'un champ
 * absent. Les deux se disent différemment — « l'Assemblée ne l'a pas déclaré »
 * n'est pas « notre fiche ne porte pas le champ ».
 */
export const POSTURES_GROUPE = {
  majorite: {
    label: 'Groupe majoritaire',
    forme: 'majorite',
    phrase: 'Soutient le gouvernement et porte ses textes.',
  },
  opposition: {
    label: "Groupe d'opposition",
    forme: 'opposition',
    phrase: "Conteste des textes qu'il n'a pas choisis.",
  },
  minoritaire: {
    label: 'Groupe minoritaire',
    forme: 'minoritaire',
    phrase: "Soutient sans être le groupe majoritaire.",
  },
  non_declaree: {
    label: 'Posture non déclarée',
    forme: 'inconnue',
    phrase: "L'Assemblée ne qualifie pas ce groupe pour cette législature.",
  },
  divergente: {
    label: 'Posture divergente',
    forme: 'inconnue',
    phrase:
      "Les organes successifs du groupe ne portent pas la même qualification : aucune ne résume les autres.",
  },
};

export const ORDRE_POSTURES = ['majorite', 'opposition', 'minoritaire', 'divergente', 'non_declaree'];

/*
 * `{ declaree, valeur, label, forme, phrase, sourceUrl, verifieLe, organes }`.
 *
 * `declaree: false` ne se replie sur aucune valeur : la clé de lecture de cette
 * page manque, et c'est ce qu'il faut écrire (§2 règle 5). `source_url` est
 * obligatoire dès que le bloc existe, y compris sur `non_declaree` — un constat
 * d'absence nomme sa source comme un constat de présence (§2 règle 2).
 */
export function postureDuGroupe(groupe) {
  const bloc = groupe?.position_politique ?? null;
  const valeur = bloc?.position ?? null;
  const connue = valeur ? POSTURES_GROUPE[valeur] : null;

  if (!bloc || !valeur) {
    return {
      declaree: false,
      valeur: null,
      label: 'Posture non publiée',
      forme: 'absente',
      phrase:
        "Cette fiche ne porte pas la qualification que l'Assemblée donne à ses groupes. Nous ne la déduisons d'aucun comportement de vote : sans elle, plusieurs chiffres de cette page se lisent sans leur clé.",
      sourceUrl: null,
      verifieLe: null,
      organes: [],
    };
  }

  return {
    declaree: true,
    valeur,
    label: connue ? connue.label : valeur,
    forme: connue ? connue.forme : 'inconnue',
    phrase: connue
      ? connue.phrase
      : "Cette qualification n'a pas de libellé publié dans l'interface.",
    sourceUrl: bloc.source_url ?? null,
    verifieLe: bloc.verifie_le ?? null,
    organes: Array.isArray(bloc.organes) ? bloc.organes : [],
  };
}

/* ── Règle : une fonction exercée n'est jamais rangée en silence ─────────────
 *
 * `mandats_agreges[].par_fonction` porte, verbatim, l'intitulé que le
 * référentiel donne au rôle : 40 libellés distincts sur les 7 fiches publiées,
 * de `membre` (18 629 occurrences) à `ministre des outre-mer` (1). Les réunir
 * en quatre familles est un acte de lecture, donc il se déclare — et il ne
 * perd rien : tout libellé que la table ne connaît pas tombe dans `autre`, qui
 * est AFFICHÉ avec ses intitulés d'origine.
 *
 * Le contraire a un coût mesuré : la maquette de cette refonte rangeait
 * « représentant suppléant » nulle part et publiait 1 351 sièges simples pour
 * `AN:SOC:16` là où la fiche en porte 1 352. Un libellé perdu ne se voit pas.
 *
 * `AGENTS.md` §5 interdit d'agréger un taux d'adoption sur des types de
 * déposant différents ; la même raison vaut ici, et la page l'écrit : un rapport
 * se confie, il ne se prend pas — ces quatre nombres ne se comparent pas entre
 * groupes en taux.
 */
export const CLASSES_FONCTION = {
  presidence: {
    label: 'Présidences',
    phrase:
      "Président, co-président ou président de groupe — d'une commission, d'un groupe d'études, d'une instance extérieure.",
  },
  rapport: {
    label: 'Rapports',
    phrase: "Rapporteur ou co-rapporteur d'un texte ou d'une mission.",
  },
  bureau: {
    label: 'Secrétariats et vice-présidences',
    phrase: 'Fonctions de bureau.',
  },
  siege: {
    label: 'Sièges simples',
    phrase: 'Membre, titulaire ou suppléant.',
  },
  autre: {
    label: 'Autres fonctions',
    phrase:
      "Intitulés que la lecture ci-dessus ne range dans aucune des quatre familles. Ils sont donnés tels que le référentiel les écrit, plutôt que rangés d'office.",
  },
};

export const ORDRE_CLASSES_FONCTION = ['presidence', 'rapport', 'bureau', 'siege', 'autre'];

/*
 * La table est écrite sur le libellé ENTIER, normalisé. Un motif en
 * sous-chaîne rangerait « membre de droit (président de la commission des
 * lois) » parmi les présidences : c'est un siège occupé de droit, pas une
 * présidence de plus.
 */
const CLASSE_PAR_LIBELLE = {
  'président': 'presidence',
  'présidente': 'presidence',
  'co-président': 'presidence',
  'co-présidente': 'presidence',
  'président de groupe': 'presidence',
  'présidente de droit': 'presidence',
  'rapporteur': 'rapport',
  'rapporteure': 'rapport',
  'co-rapporteur': 'rapport',
  'co-rapporteure': 'rapport',
  'rapporteure thématique': 'rapport',
  'vice-président': 'bureau',
  'vice-présidente': 'bureau',
  'premier vice-président': 'bureau',
  'secrétaire': 'bureau',
  'membre du bureau': 'bureau',
  'trésorier': 'bureau',
  'membre': 'siege',
  'membre titulaire': 'siege',
  'membre suppléant': 'siege',
  'membre suppléant(e)': 'siege',
  'membre suppléante': 'siege',
  'membre avec voix consultative': 'siege',
  'juge titulaire': 'siege',
  'apparenté': 'siege',
  'apparentée': 'siege',
};

/*
 * Les deux seuls préfixes admis, et ils ne désignent que des sièges : « membre
 * de droit (…) » et « représentant (…) » portent la commission ou la personne
 * représentée entre parenthèses, donc un libellé par instance. Les énumérer un
 * à un rendrait la table fausse au prochain organe.
 */
const PREFIXES_SIEGE = ['membre de droit', 'représentant'];

export function classeDeFonction(libelle) {
  const normalise = normalizeLabel(libelle);
  if (!normalise) return 'autre';
  const exact = CLASSE_PAR_LIBELLE[normalise];
  if (exact) return exact;
  if (PREFIXES_SIEGE.some((p) => normalise.startsWith(p))) return 'siege';
  return 'autre';
}

/*
 * Les quatre familles, plus `autre`, sur l'ensemble des mandats agrégés de la
 * fiche. `total` permet au rendu de vérifier que rien n'a été perdu : la somme
 * des classes retrouve la somme des `par_fonction`, par construction.
 *
 * Mesuré au commit `e40d0d32`, sur `AN:SOC:16` : 13 présidences, 17 rapports, 16
 * secrétariats et vice-présidences, 1 352 sièges simples, 0 autre — 1 398 au
 * total, soit exactement la somme des `par_fonction` de ses 615 mandats
 * agrégés.
 */
export function fonctionsDuGroupe(groupe) {
  const totaux = new Map();
  const libellesParClasse = new Map();

  for (const mandat of groupe?.mandats_agreges || []) {
    for (const [libelle, nombre] of Object.entries(mandat?.par_fonction || {})) {
      if (!Number.isFinite(nombre)) continue;
      const classe = classeDeFonction(libelle);
      totaux.set(classe, (totaux.get(classe) ?? 0) + nombre);
      const vus = libellesParClasse.get(classe) ?? new Map();
      vus.set(libelle, (vus.get(libelle) ?? 0) + nombre);
      libellesParClasse.set(classe, vus);
    }
  }

  const classes = ORDRE_CLASSES_FONCTION
    .map((cle) => ({
      cle,
      label: CLASSES_FONCTION[cle].label,
      phrase: CLASSES_FONCTION[cle].phrase,
      total: totaux.get(cle) ?? 0,
      // Les intitulés d'origine, du plus fréquent au moins fréquent. Le rendu
      // ne les montre que pour `autre`, où ils sont la seule description
      // honnête de ce que la classe contient.
      libelles: [...(libellesParClasse.get(cle) ?? new Map())]
        .sort((a, b) => b[1] - a[1])
        .map(([libelle, nombre]) => ({ libelle, nombre })),
    }))
    // Une classe vide ne se publie pas comme un zéro mesuré : `autre` à 0 veut
    // dire « la table a tout reconnu », ce qui n'a rien à dire au lecteur.
    .filter((c) => c.total > 0);

  return {
    classes,
    total: classes.reduce((acc, c) => acc + c.total, 0),
    effectif: (groupe?.membres || []).length,
  };
}

/* ── Règle : le quorum ouvre la section des votes, pas la page ───────────────
 *
 * Un groupe ne vote pas : ses membres votent. Pour dire s'il s'est exprimé
 * d'une seule voix, il faut qu'assez de ses membres aient pris part au
 * scrutin. `quorum_atteint` est publié entrée par entrée, et `meta.seuil_quorum`
 * porte le seuil (0,5 sur les 7 fiches) : l'afficher sans son seuil laisserait
 * croire à un seuil légal.
 *
 * Le fait le plus important de la fiche est ce rapport, et il était enterré :
 * mesuré au commit `e40d0d32`, `AN:SOC:16` publie 3 843 scrutins agrégés dont
 * 341 mesurables — `AN:LFI:16` 615 sur 3 973, `AN:REN:16` 523 sur 4 099, `AN:RN:16` 751
 * sur 4 108, `AN:LR:16` 185 sur 3 832.
 *
 * En dessous du seuil, RIEN n'est publié — pas même approché. Ce n'est pas une
 * lacune de collecte : les autres scrutins sont là, ils ne permettent
 * simplement pas cette mesure (§2 règle 5).
 */
export function quorumDeLaFiche(groupe) {
  const entrees = groupe?.cohesion_votes || [];
  const mesurables = entrees.filter((e) => e?.quorum_atteint === true).length;
  const seuil = groupe?.meta?.seuil_quorum;

  return {
    agreges: entrees.length,
    mesurables,
    sousLeSeuil: entrees.length - mesurables,
    seuil: Number.isFinite(seuil) ? seuil : null,
    seuilLabel: Number.isFinite(seuil) ? `${formatNumber(Math.round(seuil * 100))} %` : null,
    // Deux nombres, jamais un pourcentage seul (§2 règle 7).
    part: ratio(mesurables, entrees.length, 'scrutins agrégés sur la période'),
  };
}

/* ── Règle : un groupe partagé se montre scrutin par scrutin, jamais en indice
 *
 * « Cohésion de 87 % » serait une note attribuée à un groupe, et un classement
 * dès qu'on en aligne cinq (§2 règle 1). `taux_coherence`,
 * `taux_coherence_hors_absents` et `taux_participation` sont dans la donnée :
 * ce module ne les lit pas.
 *
 * « D'une seule voix » se décide sur les positions EXPRIMÉES : toutes celles
 * qui ont été prises allaient dans le même sens. Les absences n'entrent pas
 * dans le calcul — les compter ferait de la cohésion un taux de présence
 * déguisé (§2 règle 3).
 *
 * Mesuré au commit `e40d0d32` sur `AN:SOC:16` : 293 des 341 scrutins mesurables
 * d'une seule voix, 48 partagés, dont 23 où des membres ont voté pour et
 * d'autres contre.
 *
 * Les scrutins partagés sont montrés un par un, avec leurs décomptes — jamais
 * totalisés, et JAMAIS NOMINATIFS : la fiche dit combien de membres ont pris
 * chaque position, jamais lesquels. Désigner les écarts produirait un classement
 * à l'intérieur du groupe (§2 règles 1 et 7).
 */
export const NB_SCRUTINS_PARTAGES_AFFICHES = 6;
export const REGLE_TRONCATURE_PARTAGES =
  'les plus partagés, par nombre de voix minoritaires, puis les plus récents';

export function partageDuGroupe(groupe) {
  const mesurables = (groupe?.cohesion_votes || []).filter((e) => e?.quorum_atteint === true);
  const partages = [];
  let uneSeuleVoix = 0;
  let pourEtContre = 0;

  for (const entree of mesurables) {
    const exprimees = POSITIONS_EXPRIMEES
      .map((cle) => ({ cle, valeur: Number.isFinite(entree[cle]) ? entree[cle] : 0 }))
      .filter((d) => d.valeur > 0);

    if (exprimees.length <= 1) {
      uneSeuleVoix += 1;
      continue;
    }

    const total = exprimees.reduce((acc, d) => acc + d.valeur, 0);
    const majoritaire = exprimees.reduce((a, b) => (b.valeur > a.valeur ? b : a));
    const opposees = entree.pour > 0 && entree.contre > 0;
    if (opposees) pourEtContre += 1;

    partages.push({
      scrutinId: entree.scrutin_id ?? null,
      // Les trois positions exprimées, dans l'ordre publié, avec leur part de
      // l'ensemble des voix exprimées — jamais de `membres_eligibles`, qui
      // ferait entrer les absences dans une largeur affichée.
      exprimees: exprimees.map((d) => ({ ...d, part: d.valeur / total })),
      voixExprimees: total,
      eligibles: Number.isFinite(entree.membres_eligibles) ? entree.membres_eligibles : null,
      pourEtContre: opposees,
      // Combien de voix ne suivaient pas la position la plus nombreuse. C'est
      // le critère de tri, et il ne s'affiche pas : un « nombre de dissidents »
      // publié serait le même indice individuel par un autre chemin.
      minoritaires: total - majoritaire.valeur,
    });
  }

  return {
    mesurables: mesurables.length,
    uneSeuleVoix,
    partages: partages.length,
    pourEtContre,
    exemples: partages
      .slice()
      .sort((a, b) => b.minoritaires - a.minoritaires)
      .slice(0, NB_SCRUTINS_PARTAGES_AFFICHES),
    troncature: {
      shown: Math.min(NB_SCRUTINS_PARTAGES_AFFICHES, partages.length),
      total: partages.length,
      rule: REGLE_TRONCATURE_PARTAGES,
    },
  };
}

/*
 * Les scrutins mesurables, rangés dans les trois parts de la barre de partage,
 * pour filtrer la liste au clic sur un segment (annotation du 11/09/2026) :
 *
 *  - `une_seule_voix` — toutes les positions exprimées vont dans le même sens ;
 *  - `abstention`     — partagés entre une position et l'abstention ;
 *  - `pour_et_contre` — des voix pour ET des voix contre.
 *
 * Même décision que `partageDuGroupe`, et elle seule : les trois longueurs
 * retombent sur `uneSeuleVoix`, `partages − pourEtContre` et `pourEtContre`.
 *
 * L'ORDRE. Les deux parts partagées suivent le critère de `partageDuGroupe` —
 * les plus partagés d'abord, par nombre de voix minoritaires, puis les plus
 * récents —, et ce nombre ne sort pas : il range, il ne s'affiche jamais (§2
 * règle 7). « D'une seule voix » n'a rien à ranger par volume — tous y valent
 * zéro —, et c'est la date qui range (règle de forme 6, #326).
 *
 * `dateDe(scrutinId)` est fournie par l'appelant, qui détient l'index des
 * scrutins. Chaque entrée : `[scrutinId, pour, contre, abstention]`. Une
 * quatrième liste, `partages`, réunit les deux parts partagées au même ordre.
 */
export function scrutinsParPartage(groupe, dateDe = () => '') {
  const listes = { une_seule_voix: [], abstention: [], pour_et_contre: [] };
  for (const e of groupe?.cohesion_votes || []) {
    if (e?.quorum_atteint !== true) continue;
    const v = POSITIONS_EXPRIMEES.map((cle) => (Number.isFinite(e[cle]) ? e[cle] : 0));
    const exprimees = v.filter((x) => x > 0);
    const entree = [e.scrutin_id ?? null, ...v];
    if (exprimees.length <= 1) {
      listes.une_seule_voix.push({ entree, minoritaires: 0 });
      continue;
    }
    const total = exprimees.reduce((a, b) => a + b, 0);
    const minoritaires = total - Math.max(...exprimees);
    const cle = v[0] > 0 && v[1] > 0 ? 'pour_et_contre' : 'abstention';
    listes[cle].push({ entree, minoritaires });
  }
  const recent = (a, b) => String(dateDe(b.entree[0]) ?? '').localeCompare(String(dateDe(a.entree[0]) ?? ''));
  const plusPartages = (a, b) => b.minoritaires - a.minoritaires || recent(a, b);
  listes.une_seule_voix.sort(recent);
  listes.abstention.sort(plusPartages);
  listes.pour_et_contre.sort(plusPartages);
  // `partages` : les deux parts réunies, la vue par défaut — « les plus
  // partagés », au même ordre.
  listes.partages = [...listes.abstention, ...listes.pour_et_contre].sort(plusPartages);
  return Object.fromEntries(Object.entries(listes).map(([cle, l]) => [cle, l.map((x) => x.entree)]));
}

/* ── Règle : un texte se reconnaît à l'intitulé, et la page le dit ───────────
 *
 * Regrouper les scrutins par LOI demanderait une clé de dossier. Elle n'existe
 * pas ici : `texte_lie_id` est `null` sur 4 105 des 4 105 scrutins de la XVIe
 * législature, et `pivot_data/scrutins.json` ne porte pas de `dossier_id`.
 * `AGENTS.md` §4 est explicite sur le sujet — un `dossier_id` ne se reconstruit
 * jamais depuis un titre.
 *
 * Ce que nous faisons donc n'est PAS de reconstruire cette clé, et la page
 * n'affirme pas l'avoir. Nous regroupons les scrutins dont l'INTITULÉ OFFICIEL
 * nomme le même texte, et c'est exactement ce que le compte publié dit :
 * « scrutins dont l'intitulé officiel nomme ce texte ». Le lecteur peut le
 * vérifier — les intitulés sont publics et l'un d'eux est affiché.
 *
 * La borne est publiée avec la vue : 51 des 4 105 intitulés de la XVIe ne
 * portent aucune désignation de texte (motions de censure, déclarations du
 * gouvernement) et n'entrent dans aucun groupe.
 */
const DESIGNATIONS_TEXTE = [
  'projet de loi organique',
  'projet de loi constitutionnelle',
  'projet de loi de financement',
  'projet de loi',
  'proposition de loi organique',
  'proposition de loi constitutionnelle',
  'proposition de loi',
  'proposition de résolution',
];

/*
 * La mention de lecture est retirée AVANT le regroupement : sans cela, les
 * quatre lectures du projet de loi de finances rectificative pour 2022
 * formeraient quatre textes distincts, et c'est précisément le mouvement d'une
 * lecture à l'autre que cette vue existe pour montrer.
 *
 * Le vocabulaire des mentions vient de `utils/lecture.js` et n'est PAS réécrit
 * ici (#711) : il était dupliqué, et la copie de ce module ignorait les formes
 * en chiffres — 60 des 17 748 scrutins publiés portaient « (1ère lecture) » ou
 * « (2ème lecture) » et fabriquaient une désignation de plus. Ce qui reste
 * propre à cette vue est l'ANCRAGE, pas la liste : la mention est cherchée
 * partout dans l'intitulé, parce que 547 scrutins portent du texte après elle.
 */

/*
 * `null` quand l'intitulé ne nomme aucun texte. Jamais une désignation
 * inventée, jamais un repli sur l'intitulé entier — qui ferait un « texte »
 * par scrutin (§2 règle 5).
 */
export function designationDuTexte(intitule) {
  const normalise = normalizeLabel(intitule);
  if (!normalise) return null;

  // La désignation retenue est la PREMIÈRE du libellé, et à position égale la
  // plus longue : « projet de loi de financement de la sécurité sociale » n'est
  // pas « projet de loi », et l'ordre du tableau ne doit pas en décider.
  let debut = -1;
  let designation = null;
  for (const candidate of DESIGNATIONS_TEXTE) {
    const position = normalise.indexOf(candidate);
    if (position === -1) continue;
    if (debut === -1 || position < debut || (position === debut && candidate.length > designation.length)) {
      debut = position;
      designation = candidate;
    }
  }
  if (debut === -1) return null;

  const reste = normalise
    .slice(debut)
    .replace(MENTION_DE_LECTURE_PARTOUT, ' ')
    .replace(/\s+/g, ' ')
    .replace(/[.;,\s]+$/, '')
    .trim();
  return reste || null;
}

/*
 * Les textes que le plus de scrutins nomment, et la position de chaque groupe à
 * CHAQUE LECTURE.
 *
 * L'ordre est celui du nombre de scrutins portant la désignation — un fait sur
 * le débat parlementaire, jamais une mesure sur un groupe. Une lecture est un
 * vote sur l'ensemble du texte, au sens de `selectWholeTextVotes` (lot 1) : la
 * règle est sourcée pour moitié (`type_vote`, publié par l'Assemblée) et
 * approchée pour moitié (l'intitulé), et le lot 1 publie déjà cette borne.
 *
 * Un texte sans aucune lecture mesurable n'entre pas : la vue existe pour
 * montrer des positions, et une ligne vide se lirait comme une abstention
 * collective.
 *
 * Une case vide n'est pas une position : elle dit que le quorum de CE groupe
 * n'était pas atteint sur CE scrutin. Le rendu la marque comme telle.
 */
export const NB_GRANDES_LOIS_AFFICHEES = 8;
export const REGLE_TRONCATURE_GRANDES_LOIS =
  "les plus nommés, par nombre de scrutins dont l'intitulé officiel porte le texte";

export function grandesLois(scrutins, comparaison, sigleDuGroupe, limite = NB_GRANDES_LOIS_AFFICHEES) {
  const liste = Array.isArray(scrutins) ? scrutins : Object.values(scrutins || {});
  const legislature = comparaison?.legislature ?? null;
  const groupes = ordonnerGroupesPourComparaison(comparaison, sigleDuGroupe);
  if (!groupes.length) return { lois: [], troncature: null, sansDesignation: 0, total: 0 };

  const parTexte = new Map();
  let sansDesignation = 0;
  let total = 0;

  for (const scrutin of liste) {
    if (legislature != null && String(scrutin?.legislature) !== String(legislature)) continue;
    total += 1;
    const designation = designationDuTexte(scrutin?.texte);
    if (!designation) {
      sansDesignation += 1;
      continue;
    }
    const entree = parTexte.get(designation) ?? { designation, scrutins: 0, lectures: [], intitule: null };
    entree.scrutins += 1;
    // L'intitulé affiché est celui d'une lecture, verbatim : il nomme le texte
    // en clair là où la désignation normalisée sert seulement à regrouper.
    if (isWholeTextVote(scrutin)) entree.lectures.push(scrutin);
    parTexte.set(designation, entree);
  }

  const lois = [...parTexte.values()]
    .map((entree) => {
      const lectures = entree.lectures
        .slice()
        .sort((a, b) => String(a.date || '').localeCompare(String(b.date || '')))
        .map((scrutin) => ({
          scrutinId: scrutin.id,
          date: scrutin.date ?? null,
          intitule: scrutin.texte ?? null,
          sourceUrl: scrutin.source_url ?? null,
          positions: groupes.map((g) => ({
            sigle: g.sigle,
            nom: g.nom,
            estLeGroupe: g.estLeGroupe,
            // `null` = quorum non atteint pour CE groupe sur CE scrutin.
            position: g.positions?.[scrutin.id] ?? null,
          })),
        }));
      return { ...entree, lectures };
    })
    .filter((loi) => loi.lectures.length > 0)
    .sort((a, b) => b.scrutins - a.scrutins || a.designation.localeCompare(b.designation, 'fr'));

  return {
    colonnes: groupes.map((g) => ({ sigle: g.sigle, nom: g.nom, estLeGroupe: g.estLeGroupe })),
    lois: lois.slice(0, limite),
    troncature: { shown: Math.min(limite, lois.length), total: lois.length, rule: REGLE_TRONCATURE_GRANDES_LOIS },
    sansDesignation,
    total,
  };
}

/* ── Règle : voter dans le même sens n'est pas s'entendre ────────────────────
 *
 * La comparaison ne porte que sur les scrutins où LES DEUX groupes atteignent
 * leur quorum : les dénominateurs diffèrent donc d'une ligne à l'autre, et
 * chacun est publié à côté de son numérateur (§2 règle 7). L'ordre est d'abord
 * celui du nombre de scrutins comparables : trier sur l'accord SEUL rangerait
 * des parts calculées sur des bases différentes, et ferait un classement des
 * alliés (§2 règle 1). À base égale, et seulement là, l'accord départage
 * (relecture de la propriétaire, 11/09/2026) : deux groupes qui partagent le
 * même nombre de textes se comparent sur le même dénominateur, et le nombre de
 * votes dans le même sens dit alors la même chose que sa part.
 *
 * Trois natures, et la troisième est ce qui empêche la lecture fausse :
 *
 *  - MÊME SENS : les deux positions majoritaires sont identiques ;
 *  - SENS OPPOSÉ : l'une est « pour » et l'autre « contre » ;
 *  - NUANCE : l'une est une abstention face à une position exprimée. Une
 *    abstention n'est pas un vote contraire.
 *
 * Mesuré au commit `e40d0d32`, depuis `AN:SOC:16` : LFI 269 communs (230 · 12 ·
 * 27), RN 231 (79 · 46 · 106), REN 237 (36 · 177 · 24), LR 123 (22 · 81 · 20).
 * La décomposition renverse la lecture : SOC et RN ne sont opposés que 46 fois,
 * mais en nuance 106 — un décompte brut aurait affiché « 152 divergences ».
 *
 * `autres` compte les couples que ces trois natures ne décrivent pas. Il vaut 0
 * sur les quatre paires mesurées, et il existe pour que ce zéro reste vérifiable
 * plutôt que supposé : `position_majoritaire` pourrait valoir `non_votant` un
 * jour, et le ranger d'office en « nuance » affirmerait une intention.
 */
export const NATURES_CONVERGENCE = [
  { cle: 'meme_sens', label: 'même sens' },
  { cle: 'nuance', label: 'nuance' },
  { cle: 'oppose', label: 'sens opposé' },
];

export function natureDeConvergence(positionA, positionB) {
  if (!positionA || !positionB) return null;
  if (positionA === positionB) return 'meme_sens';
  if (
    (positionA === 'pour' && positionB === 'contre')
    || (positionA === 'contre' && positionB === 'pour')
  ) {
    return 'oppose';
  }
  const exprimee = (p) => p === 'pour' || p === 'contre';
  if (
    (positionA === 'abstention' && exprimee(positionB))
    || (positionB === 'abstention' && exprimee(positionA))
  ) {
    return 'nuance';
  }
  return 'autres';
}

export function convergences(comparaison, sigleDuGroupe) {
  const groupes = ordonnerGroupesPourComparaison(comparaison, sigleDuGroupe);
  const moi = groupes.find((g) => g.estLeGroupe);
  if (!moi) return [];

  return groupes
    .filter((g) => !g.estLeGroupe)
    .map((autre) => {
      const compte = { meme_sens: 0, nuance: 0, oppose: 0, autres: 0 };
      let communs = 0;
      for (const [scrutinId, position] of Object.entries(moi.positions || {})) {
        const nature = natureDeConvergence(position, autre.positions?.[scrutinId] ?? null);
        if (!nature) continue;
        communs += 1;
        compte[nature] += 1;
      }
      return {
        sigle: autre.sigle,
        nom: autre.nom,
        communs,
        natures: NATURES_CONVERGENCE.map((n) => ({
          ...n,
          valeur: compte[n.cle],
          part: communs > 0 ? compte[n.cle] / communs : 0,
        })),
        autres: compte.autres,
        // Le dénominateur, nommé, à côté du numérateur (§2 règle 7).
        denominateurLabel: 'scrutins où les deux groupes atteignent leur quorum',
      };
    })
    .sort((a, b) => b.communs - a.communs
      || memeSens(b) - memeSens(a)
      || a.sigle.localeCompare(b.sigle, 'fr'));
}

const memeSens = (ligne) => ligne.natures.find((n) => n.cle === 'meme_sens')?.valeur ?? 0;

/*
 * Les scrutins derrière chaque segment de `convergences`, pour les dérouler au
 * clic (annotation de la propriétaire, 11/09/2026). Même univers, même nature,
 * écrite par `natureDeConvergence` et nulle part ailleurs : le compte d'un
 * segment et la longueur de sa liste sont le même nombre par construction.
 *
 * Rend `Map` sigle → `{ meme_sens, nuance, oppose, autres }`, chaque liste de
 * `[scrutinId, positionDuGroupe, positionDeLAutre]`. L'ordre est laissé à
 * l'appelant, qui connaît les dates.
 */
export function scrutinsParNature(comparaison, sigleDuGroupe) {
  const groupes = ordonnerGroupesPourComparaison(comparaison, sigleDuGroupe);
  const moi = groupes.find((g) => g.estLeGroupe);
  const resultat = new Map();
  if (!moi) return resultat;
  for (const autre of groupes) {
    if (autre.estLeGroupe) continue;
    const listes = { meme_sens: [], nuance: [], oppose: [], autres: [] };
    for (const [scrutinId, position] of Object.entries(moi.positions || {})) {
      const sienne = autre.positions?.[scrutinId] ?? null;
      const nature = natureDeConvergence(position, sienne);
      if (nature) listes[nature].push([scrutinId, position, sienne]);
    }
    resultat.set(autre.sigle, listes);
  }
  return resultat;
}

/* ── Règle : la comparaison est réunie par posture, jamais alignée ───────────
 *
 * Un groupe majoritaire et un groupe d'opposition ne font pas le même métier :
 * les aligner sur une échelle unique les mettrait en concurrence sur une tâche
 * qu'ils ne partagent pas, ce qui est le classement que §2 règle 1 refuse.
 *
 * Aucun pourcentage n'est affiché, et c'est délibéré : un taux d'adoption
 * comparé entre groupes mesurerait surtout la posture de chacun. Mesuré au
 * commit `e40d0d32`, XVIe législature : `AN:REN:16` fait adopter 30 686
 * amendements, les quatre autres fiches 21 558 à elles toutes, alors qu'elles en
 * déposent 386 810 contre 142 143.
 *
 * Depuis le commit de données `693b076d`, la XVIe législature se sépare en deux
 * blocs réels : `majorite` ne contient que `AN:REN:16`, `opposition` réunit
 * `AN:SOC:16`, `AN:RN:16`, `AN:LFI:16` et `AN:LR:16`. `minoritaire` reste une posture que le
 * vocabulaire connaît et qu'aucune fiche de cette législature ne porte — elle
 * est nommée plutôt que tue (§2 règle 5).
 *
 * Le cas « posture non publiée » n'est donc plus l'état par défaut, mais il
 * survit et doit survivre : les 2 fiches du Sénat sont gelées depuis #516.
 */
export function comparaisonParPosture(comparaison, sigleDuGroupe) {
  const groupes = ordonnerGroupesPourComparaison(comparaison, sigleDuGroupe);
  const parPosture = new Map();

  for (const g of groupes) {
    const cle = g.posture?.declaree ? g.posture.valeur : 'non_publiee';
    const bloc = parPosture.get(cle) ?? { cle, posture: g.posture, groupes: [] };
    bloc.groupes.push(g);
    parPosture.set(cle, bloc);
  }

  const rang = (cle) => {
    const i = ORDRE_POSTURES.indexOf(cle);
    return i === -1 ? ORDRE_POSTURES.length : i;
  };

  // Le maximum sert d'échelle commune AUX SEULES LARGEURS, à l'intérieur d'une
  // posture comme à l'extérieur : c'est une aide à la lecture des deux nombres
  // affichés, jamais une note. Aucun pourcentage n'en est publié.
  const maxDeposes = Math.max(1, ...groupes.map((g) => g.amendements?.deposes ?? 0));

  return {
    blocs: [...parPosture.values()]
      .sort((a, b) => rang(a.cle) - rang(b.cle))
      .map((bloc) => ({
        ...bloc,
        groupes: bloc.groupes.map((g) => ({
          ...g,
          partDeposes: (g.amendements?.deposes ?? 0) / maxDeposes,
          partAdoptes: (g.amendements?.adoptes ?? 0) / maxDeposes,
        })),
      })),
    // Les postures que le vocabulaire connaît et qu'aucune fiche de cette
    // législature ne porte : la page le dit plutôt que de laisser croire
    // qu'elles n'existent pas (§2 règle 5).
    posturesSansFiche: ORDRE_POSTURES.filter(
      (cle) => !parPosture.has(cle) && (cle === 'majorite' || cle === 'opposition' || cle === 'minoritaire'),
    ).map((cle) => ({ cle, ...POSTURES_GROUPE[cle] })),
  };
}

/*
 * L'ordre des colonnes et des lignes de comparaison : le groupe décrit d'abord,
 * puis les autres par effectif décroissant. Un ordre par effectif n'est pas un
 * classement — c'est la seule grandeur qui rende deux groupes comparables sans
 * rien mesurer de ce qu'ils font.
 */
export function ordonnerGroupesPourComparaison(comparaison, sigleDuGroupe) {
  const groupes = (comparaison?.groupes || []).map((g) => ({
    ...g,
    estLeGroupe: g.sigle === sigleDuGroupe,
    posture: postureDuGroupe({ position_politique: g.positionPolitique ?? null }),
  }));

  return groupes.sort((a, b) => {
    if (a.estLeGroupe !== b.estLeGroupe) return a.estLeGroupe ? -1 : 1;
    const ea = Number.isFinite(a.effectif) ? a.effectif : -1;
    const eb = Number.isFinite(b.effectif) ? b.effectif : -1;
    if (eb !== ea) return eb - ea;
    return String(a.sigle).localeCompare(String(b.sigle), 'fr');
  });
}

/* ── Règle : une étiquette ne se publie jamais sans son porteur ──────────────
 *
 * `tags_thematiques_agreges` est l'agrégation des `tags_thematiques[]` des
 * membres, eux-mêmes dérivés de leurs `interventions[]` : `theme_officiel`
 * quand le compte rendu de l'Assemblée en porte un, `mots_cles` sinon. Ce sont
 * donc les SUJETS sur lesquels les membres sont intervenus, intitulés par la
 * source — jamais des positions du groupe (AGENTS.md §2 règle 8).
 *
 * Le garde-fou est `nb_membres_porteurs`, et il est publié avec l'étiquette,
 * jamais après elle : une étiquette portée par 1 membre sur 76 ne dit pas ce
 * que dit une étiquette portée par 60, et l'afficher seule donnerait l'empreinte
 * d'UNE personne pour celle du groupe — le défaut exact que #657 a corrigé, en
 * faisant collecter le thème des interventions des 468 membres de roster.
 *
 * Mesuré au commit `c6edee05` le 31/08/2026 : 448 des 468 profils
 * `roster_groupe` portent au moins une étiquette, les 5 fiches AN en publient
 * de 1 554 (`AN:SOC:16`) à 4 303 (`AN:REN:16`), et `nb_membres_porteurs` y monte
 * jusqu'à 99. Les 2 fiches Sénat en portent 0, parce qu'elles sont conservées
 * et jamais régénérées (#528) — c'est `ListeVide` qui le dit, pas un zéro.
 *
 * Le dénominateur est `len(membres)`, la population que l'agrégation a
 * réellement lue (vérifié sur les 5 fiches AN : 76, 62, 193, 90, 31, retrouvés
 * à partir de `poids_relatif`), jamais `roster_total`, qui compte des membres
 * dont aucun profil n'est publié. `poids_relatif` lui-même n'est pas publié :
 * la fiche donne ses deux nombres (§2 règle 7), comme `mandats_agreges` depuis
 * #656.
 */
export const LIBELLE_DENOMINATEUR_TAGS = 'membres du groupe dont le profil est publié';

export function etiquettesThematiques(groupe, limite = NB_TAGS_AFFICHES) {
  const denominateur = (groupe?.membres || []).length;
  return (groupe?.tags_thematiques_agreges || []).slice(0, limite).map((t) => {
    const porteurs = ratio(t.nb_membres_porteurs, denominateur, LIBELLE_DENOMINATEUR_TAGS);
    return {
      label: t.tag,
      porteurs: Number.isFinite(t.nb_membres_porteurs) ? t.nb_membres_porteurs : null,
      denominateur,
      // La phrase complète, dénominateur nommé, pour l'infobulle et les
      // technologies d'assistance : le pastille n'affiche que les deux nombres.
      porteursTexte: porteurs.text,
    };
  });
}

export const NB_TAGS_AFFICHES = 20;
export const REGLE_TRONCATURE_TAGS = 'les plus portés par les membres du groupe';

/*
 * Les ENTRÉES de la règle, pas son résultat : c'est `Troncature` (lot 1) qui
 * décide s'il y a coupe, et lui seul. Rendre ici le texte déjà composé
 * obligerait le rendu à le redécouper pour le réafficher.
 */
export function troncatureTags(total) {
  return {
    shown: Math.min(NB_TAGS_AFFICHES, total ?? 0),
    total: total ?? 0,
    rule: REGLE_TRONCATURE_TAGS,
  };
}

/* ── Règle : `meta` se lit, et rien ne le lisait ─────────────────────────────
 *
 * `couverture_roster.etat` et `preuve` sont publiés sur 7 / 7 fiches et aucun
 * composant n'en lisait un seul. Le ratio seul ne dit pas de quoi il est le
 * ratio : `groupe-Senat-LR` publie 15 profils sur 235 — 6,4 % —, et lu sans son
 * état ce chiffre se lit comme une perte. C'en est un périmètre : le Sénat est
 * hors du périmètre éditorial depuis #528, et la `preuve` le dit en toutes
 * lettres, avec ses références et sa condition de reprise.
 *
 * La cause est traduite dans le vocabulaire du lot 1 (`EMPTY_LIST_CAUSES`) :
 * `hors_perimetre` parle de NOTRE décision, donc `hors_couverture` ; un état
 * inconnu ne devient jamais « aucun résultat ».
 */
export const ETATS_COUVERTURE_ROSTER = {
  dans_le_perimetre: {
    titre: 'Dans le périmètre',
    phrase:
      "Les membres du groupe sans profil publié manquent à la collecte : ils n'ont pas été écartés.",
    // Une liste vide sur une fiche du périmètre est une mesure : la collecte a
    // abouti et n'a rien trouvé. La phrase par défaut du lot 1 convient.
    causeListeVide: 'couvert',
    motifListeVide: null,
  },
  hors_perimetre: {
    titre: 'Hors périmètre',
    phrase:
      "Les membres sans profil publié le sont par une décision éditoriale, pas par un défaut de collecte.",
    // `non_collecte`, et non `hors_couverture` : ce vide vient de NOTRE décision
    // de ne plus interroger la source, pas d'une période que la source ne
    // publierait pas. Les deux causes n'affirment pas la même chose (#326).
    causeListeVide: 'non_collecte',
    // La phrase renvoyait à la section « Vérification » de la fiche par
    // législature, qui a disparu avec la fiche de lignée (#329). La `preuve`
    // reste dans la donnée : c'est un paragraphe technique (runs, issues), et
    // un paragraphe n'a pas sa place sur la fiche (règle de forme 2).
    motifListeVide:
      "Cette fiche est hors du périmètre éditorial du produit : sa collecte est suspendue, et ses listes ne sont plus alimentées. Ce vide est une décision, pas un résultat.",
  },
};

export function couvertureRoster(groupe) {
  const bloc = groupe?.meta?.couverture_roster || {};
  const etat = bloc.etat ?? null;
  const connu = etat ? ETATS_COUVERTURE_ROSTER[etat] : null;

  return {
    etat,
    connu: Boolean(connu),
    titre: connu ? connu.titre : 'État de couverture non publié',
    phrase: connu
      ? connu.phrase
      : "Cette fiche ne déclare pas si les membres sans profil publié relèvent d'une décision ou d'un défaut de collecte.",
    // La `preuve` n'est exigée par le schéma que sur `hors_perimetre` : ailleurs
    // son absence est normale et ne se signale pas.
    preuve: typeof bloc.preuve === 'string' && bloc.preuve.trim() ? bloc.preuve : null,
    causeListeVide: connu ? connu.causeListeVide : null,
    // La `preuve` verbatim n'est publiée qu'UNE fois, sous « Vérification » :
    // elle fait un paragraphe, et la répéter sous chacune des trois listes
    // vides d'une fiche Sénat noierait la page.
    motifListeVide: connu ? connu.motifListeVide : null,
    profils: ratio(bloc.profils_disponibles, bloc.roster_total, 'membres du groupe'),
  };
}

/* ── Règle : ce qui est interdit est écrit (lot 1) ───────────────────────────
 *
 * Le refus propre à la fiche de groupe. Les écarts individu / groupe sont une
 * donnée de CONTRÔLE INTERNE (`--rapport-interne`), volontairement absente du
 * schéma de groupe : les publier désignerait qui s'est écarté de la ligne,
 * c'est-à-dire un classement interne au groupe (§2 règles 1 et 7).
 */
export const REFUS_FICHE_GROUPE = [
  {
    id: 'indice-de-cohesion',
    sujet: 'Un indice de cohésion',
    phrase: "Aucun chiffre unique ne résume la cohésion d'un groupe.",
    pourquoi:
      "La donnée porte trois taux synthétiques — cohérence, cohérence hors absents, participation. Ils ne sortent pas du fichier : un chiffre unique par groupe est une note, et cinq notes sont un classement. Les scrutins où le groupe s'est partagé sont montrés un par un.",
  },
  {
    id: 'ecarts-individuels',
    sujet: 'Écarts individuels',
    phrase: "Cette fiche ne nomme jamais qui s'est écarté de la position majoritaire.",
    pourquoi:
      "Les décomptes disent combien de membres ont pris chaque position, jamais lesquels. Désigner les écarts produirait un classement à l'intérieur du groupe, et l'écart entre un vote individuel et sa ligne de groupe reste une donnée de contrôle interne.",
  },
  {
    id: 'assiduite-de-groupe',
    sujet: 'Les absences',
    phrase: "Cette fiche connaît les absents de chaque scrutin et ne les publie jamais.",
    pourquoi:
      "La donnée compte, scrutin par scrutin, les membres éligibles pour lesquels aucun vote n'a été trouvé, et ceux qui étaient excusés. Publiés, agrégés ou non, ils deviennent un taux de présence sur des personnes nommées. Aucun décompte de cette page ne les fait entrer, ni dans un total, ni dans une largeur affichée.",
  },
];
