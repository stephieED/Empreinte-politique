/*
 * Fondations de lecture — lot 1 de la refonte #324 (issue #326).
 *
 * Les six règles que toute vue applique AVANT d'exister vivent ici, et nulle
 * part ailleurs : six règles réécrites trois fois divergent trois fois. Les
 * lots 2, 3 et 4 les appliquent, ils ne les redéfinissent pas.
 *
 * Ce module ne dessine rien. Il décide ce qu'une vue a le droit d'afficher ;
 * `components/Lecture.jsx` en donne la forme.
 *
 * Chiffres cités : mesurés au commit de données `245511b4` le 31/08/2026, sur
 * les 481 profils publiés — 13 `candidat_declare` et 468 `roster_groupe`. Un
 * chiffre sur 481 mélange les deux et ne veut rien dire.
 */

/* ── Règle : les couleurs de vote ne forment pas une échelle ─────────────────
 *
 * Pour, Contre et Abstention sont des positions EXPRIMÉES : elles portent une
 * couleur, celle du DESIGN_SYSTEM. `non_votant` n'en est pas une — il se
 * distingue par la FORME (contour tireté, aucune teinte). Mettre les quatre sur
 * un dégradé chaud-froid fabriquerait un jugement, ce qu'interdit §2 règle 1.
 *
 * QUATRE valeurs, pas cinq. `absent` n'apparaît dans AUCUNE des 1 312 951
 * positions publiées : lui donner une catégorie publierait une absence comme un
 * fait de vote, c'est-à-dire le taux de présence individuel qu'interdit §2
 * règle 3. Toute valeur inconnue — `absent` comprise, si la source en produisait
 * une un jour — tombe donc sur la forme sans teinte, jamais sur une couleur.
 *
 * Ce que ce module ferme : `VOTE_STYLE` vivait dupliqué dans CandidateProfile
 * et GroupProfile, sans `non_votant`. Les 21 229 positions `non_votant` du
 * corpus (1 sur les 13 candidats déclarés) s'affichaient sans couleur NI
 * libellé — une pastille invisible et un texte vide.
 */
/*
 * LE SORT D'UN TEXTE — vocabulaire fermé, et le même des deux côtés.
 *
 * Ces neuf valeurs sont `KNOWN_SORTS_TEXTE_PORTE` (`src/schema_pivot.py`) ET
 * `KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL` (`src/schema_gouvernement.py`) : les
 * deux frozensets sont identiques par construction, parce que la même fonction
 * lit la même source (`statutConclusion.fam_code`, #743). Les libellés vivaient
 * dans `data/pivotAdapter.js`, au service des seules fiches de gouvernement ;
 * la fiche candidat les lit maintenant aussi, et un vocabulaire écrit deux fois
 * est un vocabulaire qui divergera.
 *
 * LE SORT N'EST PAS LE STADE, ET NE S'EN DÉDUIT JAMAIS. `stade_procedural`
 * encode une PROGRESSION — le cran le plus avancé réellement atteint — et le
 * sort une ISSUE. « Discuté en séance et pas adopté » ne veut pas dire
 * « rejeté » : la source ne le dit pas. Les deux se lisent côte à côte, jamais
 * l'un à la place de l'autre.
 *
 * `depose` et `rejete_49_3` ne sont portés par aucun texte du corpus au commit
 * de données `acd7f5b7` — ils sont ici quand même : le vocabulaire est celui du
 * schéma, pas celui des données d'aujourd'hui, et une valeur qui apparaît au
 * prochain run doit s'afficher, pas tomber dans un repli.
 */
export const LIBELLE_SORT_TEXTE = {
  depose: 'Déposé',
  navette_en_cours: 'Navette en cours',
  promulgue: 'Promulgué (publié au Journal officiel)',
  adopte: 'Adopté',
  adopte_cmp: 'Adopté (texte de commission mixte paritaire)',
  adopte_49_3: 'Adopté via 49.3',
  rejete: 'Rejeté',
  rejete_49_3: 'Rejeté via 49.3',
  retire: 'Retiré',
};

/*
 * LES DEUX SORTS QUI SONT UN FAIT PROCÉDURAL, PAS UNE POSITION DE VOTE.
 *
 * `AGENTS.md` §2 règle 4 : un 49.3 n'est jamais traité comme un vote. Un texte
 * adopté par engagement de responsabilité l'a été SANS QUE L'ASSEMBLÉE VOTE —
 * le ranger parmi les adoptions ordinaires effacerait précisément ce qui le
 * distingue. Il est donc nommé, compté à part, et jamais fondu.
 */
export const SORTS_PROCEDURE_49_3 = new Set(['adopte_49_3', 'rejete_49_3']);

/*
 * POURQUOI UN TEXTE N'A PAS DE SORT — quatre motifs, fermés, et ils ne se
 * réparent pas au même endroit (`KNOWN_MOTIFS_SORT_NON_RESOLU`, #743/#747).
 *
 * Le motif s'affiche À LA PLACE du sort, jamais un sort par défaut : une
 * absence est un fait, et le §2 règle 5 interdit de la combler. Aucun texte
 * publié n'en porte au commit de données `acd7f5b7` — la table est là parce
 * que le schéma l'impose dès qu'un `sort` est nul, pas parce que le cas se
 * présente aujourd'hui.
 */
export const MOTIF_SORT = {
  sans_decision: 'le dossier n’a pas encore atteint de décision',
  fam_code_inconnu: 'code de la source non reconnu',
  archives_indisponibles: 'archives du dossier indisponibles',
  source_sans_sort: 'la source ne publie pas d’issue',
};

export function estProcedure49_3(sort) {
  return SORTS_PROCEDURE_49_3.has(sort);
}

export const VOTE_STYLE = {
  pour: { label: 'Pour', color: '#007A45', outlined: false },
  contre: { label: 'Contre', color: '#E53420', outlined: false },
  abstention: { label: 'Abstention', color: '#8B8794', outlined: false },
  non_votant: { label: 'Non-votant', color: null, outlined: true },
};

/*
 * Une position que la table ne connaît pas est rendue telle que la source
 * l'écrit, sans teinte : on n'invente ni couleur ni libellé (§2 règle 2).
 */
export function styleForPosition(position) {
  return (
    VOTE_STYLE[position] ?? { label: position ?? null, color: null, outlined: true }
  );
}

/*
 * Sorts d'amendement et d'issue — mêmes valeurs que le DESIGN_SYSTEM, elles
 * aussi dupliquées jusqu'ici dans les deux composants.
 */
export const OUTCOME_COLOR = {
  adopté: '#007A45',
  rejeté: '#E53420',
  retiré: '#F2A93B',
  tombé: '#8B8794',
  irrecevable: '#B8B4AE',
  non_soutenu: '#DCD9D3',
};

/* ── Règle : un ratio porte ses deux nombres ─────────────────────────────────
 *
 * Un pourcentage seul n'est pas vérifiable (§2 règle 7). Le dénominateur est
 * toujours nommé, parce que c'est lui qui décide si la mesure parle d'un texte
 * ou accuse une personne : « sur les scrutins où elle s'est prononcée » est
 * autorisé, « sur les scrutins où elle aurait pu se prononcer » est un taux
 * d'assiduité individuel, donc jamais publié (§2 règle 3).
 *
 * Un dénominateur absent ou nul rend `N/D` — jamais 0 %, jamais rien.
 */
export function ratio(numerator, denominator, denominatorLabel) {
  const usable =
    Number.isFinite(numerator) && Number.isFinite(denominator) && denominator > 0;

  if (!usable) {
    return { available: false, numerator, denominator, text: 'N/D' };
  }

  return {
    available: true,
    numerator,
    denominator,
    text: `${formatNumber(numerator)} sur ${formatNumber(denominator)} ${denominatorLabel}`,
  };
}

/* ── Règle : une troncature déclare sa règle ─────────────────────────────────
 *
 * Trois listes sont coupées en silence aujourd'hui : 12 votes sur 1 016 à
 * 4 976 selon le profil, 12 scrutins de cohésion sur 3 832 à 4 099, 20
 * mots-clés. Le lecteur croit voir une sélection ; il voit un `slice`.
 *
 * La récence est une règle acceptable À CONDITION d'être annoncée comme telle,
 * jamais présentée comme un choix des plus importants : les 12 votes affichés
 * sur un profil tombent sur deux jours.
 */
export function truncation(shown, total, rule) {
  if (!Number.isFinite(total) || shown >= total) {
    return { truncated: false, shown, total, text: null };
  }

  return {
    truncated: true,
    shown,
    total,
    text: `${formatNumber(shown)} sur ${formatNumber(total)} — ${rule}`,
  };
}

/* ── Règle : une liste vide dit pourquoi ─────────────────────────────────────
 *
 * Le bloc `couverture` porte déjà la cause sur 481 / 481 profils, et aucun
 * composant n'en lit une seule. Les quatre causes n'affirment pas la même
 * chose : les confondre publierait un zéro là où rien n'a été collecté, ce
 * qu'interdit §2 règle 5.
 *
 * `titre` est ce que le lecteur voit en premier ; `parle_de` dit de QUI ou de
 * QUOI la phrase parle, et c'est la distinction qui compte — un `fait_etabli`
 * parle de la personne, un `hors_couverture` parle de la source.
 */
export const EMPTY_LIST_CAUSES = {
  couvert: {
    titre: 'Aucun résultat',
    parle_de: 'la mesure',
    defaut:
      "La collecte a abouti sur toute la période et n'a rien trouvé. Ce vide est une mesure.",
  },
  fait_etabli: {
    titre: 'Aucun résultat',
    parle_de: 'la personne',
    defaut:
      "Un fait établi sur cette personne explique ce vide : elle n'était pas en situation d'en produire.",
  },
  hors_couverture: {
    titre: 'Rien à afficher pour cette période',
    parle_de: 'la source',
    defaut:
      "La source ne publie pas cette période. Ce qui a pu exister avant sa borne n'est pas décrit.",
  },
  non_collecte: {
    titre: 'Non collecté',
    parle_de: 'la collecte',
    defaut:
      "Cette liste n'a pas été interrogée. Nous ne pouvons donc rien affirmer — ni un résultat, ni son absence.",
  },
};

/*
 * `cause` vient de `meta.couverture[<liste>].etat` ; `motif` est la phrase que
 * le pipeline a écrite pour ce profil, et elle prime sur la phrase par défaut.
 * Une cause inconnue ne devient JAMAIS « aucun résultat » : elle se déclare
 * comme non renseignée (§2 règle 5).
 */
export function emptyListMessage(cause, motif) {
  const known = EMPTY_LIST_CAUSES[cause];

  if (!known) {
    return {
      cause: cause ?? null,
      known: false,
      titre: 'Cause non renseignée',
      message:
        "Cette liste est vide et la raison n'est pas publiée. Nous ne pouvons pas dire s'il s'agit d'un zéro mesuré ou d'une collecte absente.",
    };
  }

  return {
    cause,
    known: true,
    titre: known.titre,
    message: motif || known.defaut,
  };
}

/* ── Livrable : le badge de source ───────────────────────────────────────────
 *
 * La couverture est réelle et très inégale : scrutins 17 748 / 17 748,
 * interventions des 13 candidats déclarés 16 242 / 16 242, textes de
 * gouvernement 725 / 725, textes portés 472 / 472, mandats 1 915 / 41 723,
 * amendements 0 / 484 132.
 *
 * D'où la formulation, qui EST le livrable : « Lien de source non publié »
 * parle de NOUS. « Non vérifié » ferait porter le doute sur les 484 132
 * amendements eux-mêmes, qui viennent tous de l'open data de l'Assemblée
 * nationale — ce serait un jugement sur la donnée, pas un constat sur la page.
 *
 * ET « VÉRIFIÉE » EST TOMBÉ POUR LA MÊME RAISON, DANS L'AUTRE SENS (#328).
 * Le badge est vrai quand un `source_url` existe et qu'il est publié : il
 * n'atteste NI une vérification que nous ne faisons pas, NI une autorité qu'il
 * ne mesure pas. « Source officielle » a été écarté sur mesure — sur les 23 499
 * liens publiés des 32 fiches candidats, des 19 fiches de groupe et des 10
 * fiches de gouvernement, 22 988 pointent vers l'Assemblée ou le Parlement
 * européen, mais **511 pointent vers nosdeputes.fr**, un tiers (Regards
 * Citoyens) : le mot aurait été faux 511 fois. Reste le seul mot qui ne dit que
 * ce que le badge fait — il mène à la source.
 *
 * Que la source fasse foi parce qu'elle est institutionnelle est une phrase
 * vraie, argumentée, et qui se dit UNE fois : en méthodologie et dans le bloc
 * Sources de l'accueil, pas en trois mots répétés sous chaque fait.
 */
export const SOURCE_BADGE_VERIFIED = 'Source';
export const SOURCE_BADGE_UNPUBLISHED = 'Lien de source non publié';

export function sourceBadge(sourceUrl) {
  const verified = typeof sourceUrl === 'string' && sourceUrl.length > 0;
  return {
    verified,
    label: verified ? SOURCE_BADGE_VERIFIED : SOURCE_BADGE_UNPUBLISHED,
    href: verified ? sourceUrl : null,
  };
}

/* ── Livrable : les trois niveaux de lecture ─────────────────────────────────
 *
 * Les mêmes trois niveaux sur les trois types de profil. Le troisième n'est pas
 * un repli pour ce qui n'a pas trouvé sa place : c'est la contrepartie de la
 * traçabilité (§2 règle 2).
 */
export const READING_LEVELS = [
  { id: 'coup-doeil', label: "Coup d'œil", duree: '~30 s' },
  { id: 'lecture', label: 'Lecture', duree: '~3 min' },
  { id: 'verification', label: 'Vérification', duree: 'sans limite' },
];

/* ── Règle : ce qui est interdit est écrit ───────────────────────────────────
 *
 * Une page qui se contente de ne pas répondre laisse croire qu'elle n'y a pas
 * pensé. Ces phrases sont du contenu publié, pas des commentaires de code.
 */
export const STATED_REFUSALS = [
  {
    id: 'assiduite',
    sujet: 'Assiduité',
    phrase: 'Nous ne publions aucun taux de présence individuel.',
    pourquoi:
      "Un dénominateur « scrutins où la personne aurait pu voter » transformerait une absence en information négative. Nous n'avons aucun moyen de distinguer une absence d'un déport, d'une délégation ou d'une mission.",
  },
  {
    id: 'classement',
    sujet: 'Classement',
    phrase: 'Aucun score, aucun classement, aucune comparaison entre personnes.',
    pourquoi:
      'Les décomptes sont donnés avec leurs dénominateurs pour être vérifiés, jamais pour être ordonnés.',
  },
  {
    id: 'engagement-responsabilite',
    sujet: '49.3',
    phrase: "Un texte adopté sans vote n'est pas une position.",
    pourquoi:
      "L'engagement de responsabilité est un fait de procédure. Il est affiché comme tel, jamais agrégé à un décompte de votes ni coloré comme une position.",
  },
];

/*
 * Espace fine insécable entre les milliers, comme partout ailleurs dans le
 * site. Les nombres se comparent en tabulaire côté CSS.
 */
export function formatNumber(n) {
  return Number.isFinite(n) ? n.toLocaleString('fr-FR').replace(/ /g, ' ') : '—';
}

/* ── Règle : un libellé se compare sous forme normalisée ─────────────────────
 *
 * Deux apostrophes coexistent dans `pivot_data/scrutins.json` : l'ASCII `'` et
 * la typographique `’`. La seconde n'apparaît que dans les législatures 16
 * (343 scrutins) et 17 (541), c'est-à-dire les DEUX PLUS RÉCENTES — un motif
 * écrit sur l'ASCII décroche donc sur ce que la source publie aujourd'hui, et
 * décrochera de plus en plus.
 *
 * D'où la règle, qui vaut PARTOUT où un libellé est comparé et pas seulement
 * ici : on normalise avant de comparer. NFC d'abord (un « é » composé et un
 * « e » + accent combinant sont le même caractère pour un lecteur, pas pour
 * `===`), puis les apostrophes sur l'ASCII, puis les espaces, puis la casse.
 *
 * Le résultat est une FORME DE COMPARAISON : elle ne s'affiche jamais. Ce qui
 * s'affiche est le libellé de la source, tel qu'elle l'écrit (§2 règle 2).
 */
const APOSTROPHES = /[’ʼʹ′]/g;

export function normalizeLabel(texte) {
  if (typeof texte !== 'string') return '';
  return texte
    .normalize('NFC')
    .replace(APOSTROPHES, "'")
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase();
}

/* ── Règle : ce qu'est un vote « sur l'ensemble d'un texte » ─────────────────
 *
 * Cinq vues de la refonte #324 sélectionnent ces scrutins. La règle est écrite
 * ICI et une seule fois : jusqu'à cette issue elle n'était écrite nulle part,
 * et c'est déjà la cause des deux tableaux du temps 2 que le temps 3 n'a pas su
 * reproduire (`audit/faisabilite-visualisations-20260831.md` §6).
 *
 * Elle a deux moitiés, et elles ne sont pas de la même nature.
 *
 * 1. UNE MOITIÉ SOURCÉE, qui ne rouille pas. `type_vote` vient de
 *    `typeVote.codeTypeVote` (#639), un champ que l'Assemblée publie. Il écarte
 *    les 66 motions de censure des 17 748 scrutins : une motion de censure est
 *    un fait de procédure, jamais une position sur un texte (§2 règle 4).
 *
 * 2. UNE MOITIÉ APPROCHÉE, qui rouille, et qui se déclare comme telle. Le code
 *    de scrutin ne suffit pas : `AGENTS.md` §5 le dit, `SPO` couvre
 *    indifféremment les votes sur article, sur amendement et sur l'ensemble —
 *    il ne constitue donc PAS l'univers des votes sur un texte entier. Il reste
 *    l'intitulé, qui nomme l'objet du vote en clair.
 *
 * Le motif est ANCRÉ EN TÊTE, jamais cherché en sous-chaîne. Mesuré au commit
 * de données `c6edee05` le 31/08/2026, sur les 17 748 scrutins publiés :
 *
 *   sous-chaîne `l'ensemble` n'importe où, normalisée : 938
 *   ancrée en tête, `sur` initial optionnel          : 933
 *   moins les votes sur une sous-partie              : 925  ← la règle
 *
 * Les 5 que l'ancrage écarte sont des votes que la sous-chaîne publiait à tort
 * comme des votes sur un texte entier : 1 motion de rejet préalable (leg 14),
 * 1 article unique, 2 amendements et 1 article premier (leg 17). Publier l'un
 * d'eux affirmerait une position que la personne n'a pas prise (§2 règle 2, et
 * §2 règle 4 pour la motion).
 *
 * Le `sur ` initial est optionnel parce qu'un ancrage strict écartait un vrai
 * vote sur l'ensemble : le scrutin SOLENNEL `an:14:32`, « sur l'ensemble du
 * projet de loi organique relatif à la programmation et à la gouvernance des
 * finances publiques ». Un seul scrutin sur 17 748 — et c'est bien pour cela
 * qu'il faut un test : personne ne le reverra à l'œil.
 */
export const WHOLE_TEXT_VOTE_PATTERN = /^(?:sur )?l'ensemble\b/;

/*
 * L'ancrage ne suffit toujours pas. 8 des 933 scrutins ancrés portent sur une
 * SOUS-PARTIE du texte, et les publier comme des votes sur l'ensemble serait
 * exactement le contresens que l'ancrage vient de fermer :
 *
 *   5 votes sur un article — « l'ensemble de l'article premier du projet de loi
 *     constitutionnelle de protection de la Nation » (leg 14, ×2), l'article 5
 *     bis du PLFR 2014, les articles premier et 3 du texte sur la délimitation
 *     des régions ;
 *   3 votes sur une partie de budget — la première partie du PLF 2014 (un
 *     scrutin SOLENNEL) et du PLFG 2024, la deuxième partie du PLFSS 2025.
 *
 * Cette exclusion est la partie la plus fragile de la règle : elle nomme deux
 * formes observées, et une troisième forme d'objet partiel passerait au travers.
 * C'est pourquoi la borne ci-dessous est publiée, et pourquoi les 8 sont cités
 * un par un dans `tests/test_selection_vote_ensemble_672.py`.
 */
export const SUBPART_VOTE_PATTERN =
  /^(?:sur )?l'ensemble (?:de l'article\b|de la (?:[a-zàâçéèêëîïôûùüÿœ]+ )?partie\b)/;

/*
 * Vrai si ce scrutin porte sur l'ensemble d'un texte, au sens de la règle
 * ci-dessus. Attend une entrée de `pivot_data/scrutins.json` : `texte` et
 * `type_vote`.
 *
 * Un `type_vote` absent ne devient jamais `vote_texte` par défaut : sans le
 * champ, on ne sait pas, et §2 règle 5 interdit de combler par une valeur.
 */
export function isWholeTextVote(scrutin) {
  if (!scrutin || scrutin.type_vote !== 'vote_texte') return false;

  const libelle = normalizeLabel(scrutin.texte);
  return WHOLE_TEXT_VOTE_PATTERN.test(libelle) && !SUBPART_VOTE_PATTERN.test(libelle);
}

/*
 * La sélection que les cinq vues appellent, plutôt que d'en réécrire cinq
 * variantes. Accepte la liste de `scrutins.json` ou l'index `{id: scrutin}`
 * que `pivotAdapter` manipule.
 */
export function selectWholeTextVotes(scrutins) {
  const liste = Array.isArray(scrutins) ? scrutins : Object.values(scrutins || {});
  return liste.filter(isWholeTextVote);
}

/* ── Livrable : le NOM du texte, quand c'est le texte qu'on nomme ────────────
 *
 * L'intitulé d'un vote sur l'ensemble commence par « l'ensemble du projet de
 * loi… » et finit par la mention de lecture. Les deux disent la PLACE du vote,
 * pas le nom du texte : une carte qui réunit les quatre lectures du projet de
 * loi de finances rectificative pour 2022 ne peut pas s'intituler
 * « (première lecture) », et « l'ensemble du… » y répète ce que la carte dit
 * déjà (#329).
 *
 * Ce retrait vit ICI, à côté de `WHOLE_TEXT_VOTE_PATTERN` dont il est
 * exactement le complément, et pas dans la vue qui l'affiche : un motif sur
 * « l'ensemble » écrit une seconde fois est le défaut que #326 puis #672 ont
 * fermé, et `tests/test_selection_vote_ensemble_672.py` le refuse.
 *
 * DEUX retraits, et deux seulement. Rien n'est reformulé : ce qui reste est la
 * chaîne de la source, capitale initiale mise à part (§2 règle 2). La vue
 * publie l'intitulé complet à côté — en infobulle, et par le lien de source du
 * scrutin.
 */
const OUVERTURE_VOTE_ENSEMBLE = /^(?:sur )?l['’]ensemble (?:du |de la |de l['’]|des )?/i;

/* ── Règle : le VOCABULAIRE des mentions de lecture est écrit une seule fois ──
 *
 * Deux modules retiraient la mention de lecture d'un intitulé, chacun avec sa
 * propre liste : `titreDuTexteVote` ici et `designationDuTexte` dans
 * `utils/groupe.js` — et rien du tout ne regroupait les lectures, ce que #711
 * ajoute. Le vocabulaire vit désormais ICI, et les deux ancrages s'en
 * déduisent : la liste des mentions reconnues ne peut plus diverger d'un module
 * à l'autre, seule la place où on les cherche varie.
 *
 * La liste est MESURÉE, pas devinée. Distribution des mentions finales sur les
 * 925 scrutins « sur l'ensemble d'un texte » des 17 748 publiés, au commit de
 * données `f635cb60` le 02/09/2026 :
 *
 *   première lecture                        546      2e lecture                 2
 *   texte de la commission mixte paritaire  158      troisième lecture          2
 *   lecture définitive                       54      1re lecture                1
 *   (aucune parenthèse finale)               49      texte cmp                  1
 *   deuxième lecture                         48      premiere lecture           1
 *   nouvelle lecture                         46      + 4 coquilles de la source
 *   texte de la commission paritaire          8      (commisison, commisson,
 *   1ère lecture                              3       défintive, défnitive)
 *
 * Deux parenthèses finales ne sont PAS des mentions de lecture et ne doivent
 * jamais être retirées : « (article 34-1 de la Constitution) » et
 * « (art. 34-1 de la Constitution) », 1 scrutin chacune — une résolution de
 * l'article 34-1 n'a pas de lecture. Deux autres formes, mesurées ailleurs dans
 * le corpus, distinguent des textes et non des lectures : le « (2) » du projet
 * de loi de finances rectificative pour 2020 (2), et le « (2ème vote) » du
 * scrutin `an:14:1086` qui remplace le scrutin annulé `an:14:1085`.
 *
 * D'où la forme de la liste : les ordinaux en CHIFFRES exigent le mot
 * « lecture » derrière eux — sans cette exigence, « (2ème vote) » serait pris
 * pour une lecture et souderait un scrutin annulé à son remplaçant. Les
 * ordinaux en LETTRES restent nus, comme avant ce lot : c'est ce qui retire
 * « (seconde délibération) », et le changer déplacerait 547 désignations de
 * fiche de groupe pour une raison étrangère à ce lot.
 */
const MENTIONS_DE_LECTURE =
  /première|premiere|nouvelle|deuxième|seconde|texte|lecture|c\.m\.p|(?:1\s*(?:ère|re|ere)|2\s*(?:ème|eme|e)|3\s*(?:ème|eme|e)|troisième|troisieme|deuxieme)\s*lecture/;

/*
 * La mention EN FIN d'intitulé — celle qu'on retire pour nommer le texte et
 * pour le regrouper.
 */
export const MENTION_DE_LECTURE = new RegExp(
  `\\s*\\((?:${MENTIONS_DE_LECTURE.source})[^)]*\\)\\s*\\.?\\s*$`,
  'i',
);

/*
 * La même mention CHERCHÉE PARTOUT dans l'intitulé, forme dont
 * `designationDuTexte` (`utils/groupe.js`) a besoin : 547 scrutins portent du
 * texte APRÈS la parenthèse — « […] (première lecture). scrutin annulé -
 * remplacé par le scrutin 1086 ». Deux ancrages, un seul vocabulaire.
 */
export const MENTION_DE_LECTURE_PARTOUT = new RegExp(
  `\\s*\\((?:${MENTIONS_DE_LECTURE.source})[^)]*\\)\\s*`,
  'gi',
);

export function titreDuTexteVote(intitule) {
  if (typeof intitule !== 'string' || !intitule.trim()) return null;
  const nu = intitule.replace(OUVERTURE_VOTE_ENSEMBLE, '').replace(MENTION_DE_LECTURE, '').trim();
  if (!nu) return intitule;
  return nu.charAt(0).toUpperCase() + nu.slice(1);
}

/* ── Règle : un texte voté plusieurs fois n'est compté qu'une fois ───────────
 *
 * `AGENTS.md` §6 publie « `votes[]` vote sur le texte (`vote_texte`, DERNIÈRE
 * LECTURE) », et le DESIGN_SYSTEM §6 cite la formule comme exemple de la voix
 * de la maison. Aucun code ne l'appliquait (#711) : `isWholeTextVote` (#672)
 * sélectionnait les votes sur l'ensemble d'un texte et s'arrêtait là.
 *
 * Mesuré au commit de données `f635cb60` le 02/09/2026, sur les 17 748
 * scrutins publiés : 925 votes sur l'ensemble d'un texte, 697 textes distincts
 * une fois les lectures repliées, 187 textes votés plusieurs fois — 228
 * scrutins, soit 24,6 %, comptaient une lecture déjà comptée.
 *
 * ── Pourquoi le regroupement par libellé est permis ICI ────────────────────
 *
 * `docs/decisions/regrouper-nest-pas-joindre-639.md` autorise à regrouper des
 * faits d'UNE MÊME SOURCE par leur propre libellé ; les 925 intitulés viennent
 * tous des scrutins de l'Assemblée. Et le mode d'échec est SÛR : un intitulé
 * mal replié ÉCHOUE À REGROUPER, il ne rapproche jamais à tort. Deux lectures
 * restent alors comptées séparément — c'est-à-dire l'état d'avant ce lot.
 * C'est l'inverse exact de `texte_vise` (#696), où un appariement par libellé
 * aurait FUSIONNÉ des textes distincts.
 *
 * ── Pourquoi la DATE, et jamais le rang ────────────────────────────────────
 *
 * Le rang de lecture n'est pas un champ : notre projection de scrutin porte
 * `date`, `legislature`, `numero_scrutin`, `sort`, `texte`, `type_scrutin`,
 * `type_vote`, `demandeur` (#639). Le rang n'existe que DANS l'intitulé, où il
 * manque 51 fois sur 925. Le repli sert à GROUPER ; la date ORDONNE.
 *
 * Et l'ordre par rang serait FAUX là où les deux divergent — 4 groupes mesurés,
 * tous des textes budgétaires dont l'Assemblée réemploie le titre :
 * « projet de loi de finances rectificative pour 2017 » porte deux premières
 * lectures (06/11 et 12/12/2017) encadrant une lecture définitive (14/11). Un
 * tri par rang y retiendrait la lecture définitive de novembre, alors que le
 * dernier scrutin de décembre est le plus récent.
 *
 * ── Ce que le repli NE rattrape pas, et dans quel sens il se trompe ─────────
 *
 * La clé porte la LÉGISLATURE. Sans elle, 10 groupes soudent deux textes
 * homonymes votés dans deux législatures différentes. Un texte réellement
 * repris après une dissolution reste donc compté deux fois : c'est un manque,
 * pas une affirmation.
 *
 * Il reste 9 groupes — 20 scrutins des 925, borne HAUTE — qui portent DEUX FOIS
 * la même mention de lecture à des dates différentes dans une même
 * législature : deux collectifs budgétaires d'une même année, deux lois
 * spéciales, deux prorogations de l'état d'urgence. Certains sont légitimes (un
 * intitulé qui omet sa mention deux fois de suite), les autres soudent deux
 * textes distincts. Le sens de l'erreur reste le bon : le scrutin retenu est
 * toujours un scrutin réel de la personne, jamais un vote inventé — ce qui se
 * perd est un texte, jamais une position attribuée à tort.
 */

/*
 * La clé de regroupement : (législature, titre débarrassé de sa mention de
 * lecture). `null` quand l'intitulé ne donne rien à regrouper — jamais une clé
 * inventée, jamais un repli sur l'intitulé entier, qui ferait un texte par
 * scrutin (§2 règle 5).
 *
 * Le séparateur est un caractère nul : il ne peut pas apparaître dans un
 * libellé, donc deux clés ne peuvent pas se confondre par concaténation.
 */
export function cleDuTexteVote(scrutin) {
  const libelle = normalizeLabel(scrutin?.texte);
  if (!libelle) return null;

  const titre = libelle
    .replace(OUVERTURE_VOTE_ENSEMBLE, '')
    .replace(MENTION_DE_LECTURE, '')
    .replace(/[.\s]+$/, '')
    .trim();
  if (!titre) return null;

  return `${scrutin?.legislature ?? ''}\u0000${titre}`;
}

/*
 * L'ordre des lectures d'un texte : par DATE, puis par numéro de scrutin.
 *
 * Le numéro ne départage qu'À L'INTÉRIEUR d'une législature — il repart à 1 à
 * chaque législature (`AGENTS.md` §5) — et c'est précisément le cas ici, parce
 * que la clé de regroupement porte la législature. Il ne sert que d'ex aequo :
 * un seul groupe des 697 en a besoin, les scrutins `an:15:2769` et
 * `an:15:2770` du 25/06/2020, deux votes du même jour sur la proposition de loi
 * pour une éthique de l'urgence.
 */
function ordreDesLectures(a, b) {
  const parDate = String(a?.date || '').localeCompare(String(b?.date || ''));
  if (parDate !== 0) return parDate;
  return Number(a?.numero_scrutin || 0) - Number(b?.numero_scrutin || 0);
}

/*
 * Les votes sur l'ensemble d'un texte, regroupés par texte. Accepte la liste de
 * `pivot_data/scrutins.json` ou l'index `{id: scrutin}` que `pivotAdapter`
 * manipule, comme `selectWholeTextVotes` dont ce regroupement est le
 * prolongement.
 */
export function grouperLecturesParTexte(scrutins) {
  const groupes = new Map();

  for (const scrutin of selectWholeTextVotes(scrutins)) {
    const cle = cleDuTexteVote(scrutin);
    if (!cle) continue;

    const entree = groupes.get(cle) ?? {
      cle,
      legislature: scrutin.legislature ?? null,
      titre: titreDuTexteVote(scrutin.texte),
      lectures: [],
    };
    entree.lectures.push(scrutin);
    groupes.set(cle, entree);
  }

  for (const entree of groupes.values()) entree.lectures.sort(ordreDesLectures);
  return groupes;
}

/*
 * La dernière lecture d'un texte, ou `null` quand elle n'est pas déterminable.
 *
 * Une lecture SANS DATE ne s'ordonne pas. Un groupe qui en porte une n'a donc
 * pas de dernière lecture connue, et il vaut mieux ne rien publier que de
 * choisir au hasard (§2 règle 5) — sauf si le groupe ne compte qu'une lecture :
 * il n'y a alors rien à ordonner. Aucun des 925 scrutins mesurés n'est dans ce
 * cas, et c'est bien pour cela que la garde est écrite plutôt que supposée.
 */
export function derniereLecture(lectures) {
  const liste = Array.isArray(lectures) ? lectures : [];
  if (!liste.length) return null;
  if (liste.length === 1) return liste[0];
  if (liste.some((scrutin) => !scrutin?.date)) return null;

  const triees = liste.slice().sort(ordreDesLectures);
  return triees[triees.length - 1];
}

/*
 * Un scrutin par texte : celui de sa dernière lecture. C'est la sélection que
 * les vues appellent pour compter des TEXTES plutôt que des votes.
 */
export function selectDerniereLectureVotes(scrutins) {
  const retenus = [];
  for (const entree of grouperLecturesParTexte(scrutins).values()) {
    const derniere = derniereLecture(entree.lectures);
    if (derniere) retenus.push(derniere);
  }
  return retenus.sort(ordreDesLectures);
}

/* ── Livrable : la règle, en texte publié ────────────────────────────────────
 *
 * Un compteur qui replie sans le dire ment par omission : le lecteur qui
 * compare 111 à une liste de 150 votes ne peut pas savoir ce qui a été retiré,
 * et le DESIGN_SYSTEM §6 exige que chaque métrique porte sa propre limite.
 *
 * Le libellé court accompagne le chiffre ; la phrase et le pourquoi vivent en
 * note, à côté de `WHOLE_TEXT_VOTE_BOUND` dont cette règle est le second temps.
 */
export const LAST_READING_LABEL = 'dernière lecture retenue pour chaque texte';

export const LAST_READING_RULE = {
  id: 'derniere-lecture',
  sujet: 'Dernière lecture',
  phrase:
    'Un texte voté plusieurs fois ne compte qu’une fois : la position retenue est celle de sa dernière lecture.',
  pourquoi:
    'Un même texte revient devant l’Assemblée — première lecture, nouvelle lecture, texte de la commission mixte paritaire, lecture définitive. Compter chacune séparément gonfle le décompte, et afficher une position de première lecture comme la position sur la loi serait faux dès qu’un vote plus tardif l’a suivie. Nous regroupons donc les lectures d’un même texte par leur intitulé, et nous retenons la plus récente par sa date : le rang de lecture n’est pas un champ de la source. Quand la personne n’a pas de position enregistrée sur cette dernière lecture, le texte n’est pas affiché — nous ne pouvons pas dire pourquoi elle y manque, et le dire serait publier une absence individuelle.',
};

/* ── Livrable : la borne, en texte publié ────────────────────────────────────
 *
 * 925 est un PLANCHER, jamais un décompte exhaustif, et la page le dit (§2
 * règle 5). Deux mesures le montrent, au commit `c6edee05` :
 *
 *   - la source ne distingue pas : 17 312 des 17 748 scrutins portent le code
 *     `SPO`, qui couvre l'ensemble, l'article et l'amendement sans les séparer ;
 *   - le libellé ne dit pas toujours « l'ensemble » : 70 des 361 scrutins
 *     SOLENNELS ne sont pas retenus, et certains sont d'authentiques votes sur
 *     un texte entier dont l'intitulé emploie une autre tournure — « le projet
 *     de loi de modernisation, de développement et de protection des
 *     territoires de montagne (première lecture) ».
 *
 * Ces votes-là manquent. C'est un vide, et un vide se préfère à un décompte
 * gonflé : un vote manqué ne dit rien, un vote attribué à tort affirme une
 * position que la personne n'a pas prise.
 */
export const WHOLE_TEXT_VOTE_BOUND = {
  id: 'votes-sur-ensemble',
  sujet: 'Votes sur l’ensemble d’un texte',
  phrase:
    "Ce décompte est un plancher, pas un relevé exhaustif : il ne prétend pas contenir tous les votes sur un texte entier.",
  pourquoi:
    "L’Assemblée publie un même code de scrutin pour les votes sur l’ensemble d’un texte, sur un article et sur un amendement : rien dans la source ne les sépare. Nous reconnaissons donc ces votes à leur intitulé, qui commence par « l’ensemble du projet de loi… » ou « l’ensemble de la proposition de loi… ». Un vote sur un texte entier formulé autrement n’est pas repris ici. Nous préférons ce manque à un décompte gonflé : un vote absent ne dit rien, un vote attribué à tort affirme une position que la personne n’a pas prise.",
};

/**
 * Législature portée par un identifiant d'amendement (`an:AMANR5L17…` → `'17'`).
 *
 * Lecture structurelle de l'identifiant, pas une déduction depuis la date :
 * c'est l'AN qui l'y écrit. `null` si la forme n'est pas reconnue — on ne
 * devine pas une législature pour aller chercher le mauvais fichier.
 *
 * Déplacée de `data/pivotAdapter.js` par #329 : la fiche de lignée la lit au
 * BUILD (`scripts/vue-lignee.mjs`), et ce module-ci est le seul des deux que
 * Node sait importer.
 */
export function legislatureDeAmendementId(amendementId) {
  const m = /^an:AMANR5L(\d+)/.exec(amendementId || '');
  return m ? m[1] : null;
}

/**
 * La page d'un dossier législatif sur le site de l'Assemblée, depuis son
 * identifiant (`DLR5L16N46116` → `…/dyn/16/dossiers/DLR5L16N46116`).
 *
 * Le pipeline construit ses liens de dossier sur `titreChemin`, que seuls les
 * dossiers relus en entier transportent ; l'index des amendements ne porte que
 * `dossier_id`. L'Assemblée résout aussi l'identifiant : vérifié le 11/09/2026
 * sur quatre dossiers des XIVe, XVe et XVIe législatures, chaque page porte le
 * titre que l'index publie — et un identifiant inconnu rend la page d'accueil,
 * pas une erreur, d'où la forme vérifiée ici avant de construire quoi que ce
 * soit. La législature est celle de l'identifiant, jamais une déduction.
 */
export function urlDossierAN(dossierId) {
  const m = /^DLR5L(\d+)N\d+$/.exec(dossierId || '');
  return m ? `https://www.assemblee-nationale.fr/dyn/${m[1]}/dossiers/${dossierId}` : null;
}

/*
 * UN LIEN QUI TÉLÉCHARGE 100 Mo N'ATTESTE RIEN.
 *
 * Le compte rendu de séance est publié par l'Assemblée en ARCHIVE — trois
 * fichiers `syseron.xml.zip`, un par législature —, et c'est cette adresse que
 * `source_url` porte sur la plupart des interventions : mesuré le 20/09/2026,
 * 27 007 des 33 823 interventions des candidats déclarés. Un badge « Source »
 * par ligne y menait, et cliquer lançait un téléchargement.
 *
 * Le lien par ligne ne subsiste donc que lorsqu'il mène à un DOCUMENT — une
 * question écrite, par exemple. L'archive, elle, est nommée une fois par
 * section, par une mention vers la page du jeu de données.
 */
export const PAGE_JEU_DE_DONNEES_DEBATS = 'https://data.assemblee-nationale.fr/travaux-parlementaires/debats';
/* L'annuaire des acteurs, mandats et organes (AMO30) est lui aussi publié en
   archive : la légende « Selon l'Assemblée nationale » de la fiche de lignée y
   menait, et cliquer téléchargeait 13 Mo. */
export const PAGE_JEU_DE_DONNEES_ACTEURS = 'https://data.assemblee-nationale.fr/acteurs';

export function estArchiveTelechargeable(url) {
  return typeof url === 'string' && /syceronbrut|syseron|\.zip($|\?)/i.test(url);
}

/** L'adresse à publier pour une entrée, ou `null` quand la source ne publie
 *  qu'une archive : l'absence se dit, elle ne se comble pas d'un lien qui
 *  télécharge (§2 règles 2 et 5). */
export function lienDocumentaire(url) {
  if (typeof url !== 'string' || !url) return null;
  return estArchiveTelechargeable(url) ? null : url;
}

/** La page du jeu de données qui porte une archive — pour les légendes qui
 *  doivent RESTER un lien : le lecteur y trouve le téléchargement, on ne le
 *  lui déclenche pas. */
export function pageDuJeuDeDonnees(url) {
  if (!estArchiveTelechargeable(url)) return url;
  return /amo|acteur/i.test(url) ? PAGE_JEU_DE_DONNEES_ACTEURS : PAGE_JEU_DE_DONNEES_DEBATS;
}
