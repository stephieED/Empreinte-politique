// Projection d'une FICHE DE LIGNÉE pour le navigateur (#329, sur le socle #836).
//
// La page de groupe publie une fiche par lignée (décision du 10/09/2026). La
// fiche de lignée de `pivot_data/lignees/` pèse de 5 Ko (Sénat) à 7,7 Mo
// (`lignee-AN-REN.json`), et la page en lit une fraction : ses sections 2 à 5
// se lisent MAILLON PAR MAILLON, sur les fiches de groupe elles-mêmes, qui
// pèsent 2 à 5 Mo chacune. Faire télécharger 11 Mo pour la lignée socialiste
// serait le défaut que #628 interdit, de l'autre côté du fil — même motif que
// `comparaison-groupes.mjs`.
//
// La projection ne CALCULE rien qui lui soit propre : chaque nombre sort d'une
// fonction de `src/utils/groupe.js` ou de `src/utils/lignee.js`, les mêmes que le
// navigateur importe. Une règle lue au build et à l'écran reste une seule règle.
//
// Ce qui ne traverse PAS : `absents` et `excuses` (`DECOMPTES_JAMAIS_PUBLIES`,
// §2 règle 3) — aucune des fonctions appelées ici ne les lit —, les trois taux
// synthétiques de cohésion, et `mandats_agreges`, qui compte la carrière des
// membres et non leur passage dans le groupe (#853).
//
// Le fichier produit est un ARTEFACT DE BUILD (`public/data/` est ignoré par
// git) : il ne rejoint jamais `pivot_data/`.

import {
  convergences,
  couvertureRoster,
  dateDeReference,
  effectifDuGroupe,
  etiquettesThematiques,
  partageDuGroupe,
  postureDuGroupe,
  quorumDeLaFiche,
  scrutinsParNature,
  scrutinsParPartage,
} from '../src/utils/groupe.js';
import { isWholeTextVote } from '../src/utils/lecture.js';
import { personnesParMaillon, serieEffectif, signalementsDuMaillon } from '../src/utils/lignee.js';

/* Les amendements d'un maillon : le total distinct publié, et la répartition
 * par commission des deux types de déposant qu'un groupe porte, VÉRIFIÉE contre
 * ce total type par type (`amendements-lignees.mjs`). `gouvernement` n'en est
 * pas un : un groupe ne dépose jamais au nom du gouvernement, et la ligne « 0 »
 * qu'affichait la fiche ne disait rien au lecteur (règle de forme 1, #326).
 *
 * `sansType` est le reste que la source ne range sous aucun type — 3 991 des
 * 10 987 amendements de GDR-17 le 11/09/2026 : il se DIT en pied de section,
 * il ne se fond dans aucune barre (règle de forme 7). */
function amendementsDuMaillon(groupe, repartition) {
  const agg = groupe.amendements_agreges || {};
  return {
    distincts: agg.nb_amendements ?? null,
    sansType: agg.par_type_deposant?.inconnu?.nb_amendements ?? 0,
    parType: repartition?.types ?? {},
  };
}

/* L'entrée du dictionnaire des intitulés. `ensemble` dit si le scrutin porte
 * sur l'ENSEMBLE d'un texte, au sens de `isWholeTextVote` (#672) : la liste de
 * § 4 met ces votes en tête et replie le reste — amendements, articles,
 * motions — (annotation de la propriétaire, 11/09/2026). */
function intitule(s, dernieres) {
  return {
    date: s?.date ?? null,
    texte: s?.texte ?? null,
    sourceUrl: s?.source_url ?? null,
    ensemble: isWholeTextVote(s),
    // La DERNIÈRE lecture de son texte, au sens de `selectDerniereLectureVotes`
    // (#711) — calculée sur le corpus entier des scrutins, jamais sur ceux du
    // groupe : c'est elle seule que la liste met en tête (annotation du 11/09).
    derniere: Boolean(s && dernieres.has(s.id)),
  };
}

/* Les convergences, et de quoi dérouler chaque segment au clic. Les scrutins
 * sont rangés du plus récent au plus ancien — le nombre ne classe rien, la date
 * range (règle de forme 6, #326) —, et leur intitulé n'est transporté qu'UNE
 * fois par maillon, dans `scrutins`, pour les seuls scrutins nommés. */
function convergencesDeroulables(comparaisonComplete, sigle, parId, ligneeDeFiche, nomsDesLignees, dernieres) {
  if (!comparaisonComplete) return { convergences: null, scrutins: {} };
  // « Avec qui ils votent » ne compare plus que la DERNIÈRE lecture de chaque
  // texte (annotation du 11/09/2026) : un texte, une position, la règle de #711.
  // Le filtre porte sur la projection, AVANT les règles de `groupe.js`, qui
  // restent les seules à décider d'une nature — un compte et sa liste restent
  // le même nombre par construction.
  const comparaison = {
    ...comparaisonComplete,
    groupes: (comparaisonComplete.groupes || []).map((g) => ({
      ...g,
      positions: Object.fromEntries(Object.entries(g.positions || {}).filter(([id]) => dernieres.has(id))),
    })),
  };
  const listes = scrutinsParNature(comparaison, sigle);
  // La page du groupe voisin : sa LIGNÉE, jamais sa fiche de législature — le
  // lien d'un sigle doit survivre au renouvellement (#836, annotation du 11/09).
  const ficheDe = new Map((comparaison.groupes || []).map((g) => [g.sigle, g.id]));
  const scrutins = {};
  const dateDe = (id) => parId.get(id)?.date ?? '';
  const lignes = convergences(comparaison, sigle).map((ligne) => {
    const siennes = listes.get(ligne.sigle) || {};
    const parNature = {};
    for (const [nature, entrees] of Object.entries(siennes)) {
      parNature[nature] = entrees
        .slice()
        .sort((a, b) => dateDe(b[0]).localeCompare(dateDe(a[0])) || a[0].localeCompare(b[0]));
      for (const [id] of entrees) {
        if (scrutins[id]) continue;
        const s = parId.get(id);
        scrutins[id] = intitule(s, dernieres);
      }
    }
    const lignee = ligneeDeFiche.get(ficheDe.get(ligne.sigle)) ?? null;
    return { ...ligne, lignee, ligneeNom: nomsDesLignees.get(lignee) ?? null, scrutins: parNature };
  });
  return { convergences: lignes, scrutins };
}

/* Les trois listes de partage, et les intitulés de TOUS les scrutins qu'elles
 * nomment, dans le même dictionnaire que les convergences : un intitulé n'est
 * transporté qu'une fois par maillon, quelle que soit la vue qui le déroule. */
function avecIntitules({ convergences: lignes, scrutins }, listesPartage, parId, dernieres) {
  for (const liste of Object.values(listesPartage)) {
    for (const [id] of liste) {
      if (scrutins[id]) continue;
      const s = parId.get(id);
      scrutins[id] = intitule(s, dernieres);
    }
  }
  return { convergences: lignes, scrutins, partageListes: listesPartage };
}

/* L'identifiant de page d'une lignée : son nom de fichier, `lignee-AN-SOC.json`
 * → `AN-SOC`. Il vient d'un `lignee_id` DÉCLARÉ (#836), jamais d'un sigle de
 * maillon — qui changerait à chaque législature et casserait les liens. */
export function idDePage(fichier) {
  return fichier.replace(/^lignee-/, '').replace(/\.json$/, '');
}

/**
 * La vue d'une lignée.
 *
 * - `lignee` : la fiche de `pivot_data/lignees/` ;
 * - `fiches` : Map `fichier` → fiche de groupe (les maillons) ;
 * - `idsDeFiche` : Map `fichier` → identifiant de page de la fiche de groupe ;
 * - `scrutins` : l'index partagé `pivot_data/scrutins.json` (liste) ;
 * - `comparaisons` : Map clé de législature → projection de `comparaison-groupes.mjs` ;
 * - `cleDe` : fiche → clé de législature ;
 * - `candidats` : Set des slugs de candidats déclarés publiés ;
 * - `repartitions` : Map `fichier` → répartition vérifiée (`amendements-lignees.mjs`) ;
 * - `ligneeDeFiche` : Map identifiant de fiche de groupe → identifiant de page de sa lignée ;
 * - `nomsDesLignees` : Map identifiant de page de lignée → son nom déclaré ;
 * - `dernieresLectures` : Set des scrutins qui sont la dernière lecture de leur texte (#711).
 */
export function construireVueLignee({ fichier, lignee, fiches, idsDeFiche, scrutins, comparaisons, cleDe, candidats, repartitions, ligneeDeFiche = new Map(), nomsDesLignees = new Map(), dernieresLectures = new Set(), aujourdhui }) {
  const parId = new Map(scrutins.map((s) => [s.id, s]));
  const personnes = (lignee.membres || []).map((m) => ({
    id: m.membre_id,
    nom: m.nom,
    candidat: candidats.has(String(m.membre_id).split(':').pop()),
  }));
  const rangPersonne = new Map(personnes.map((p, i) => [p.id, i]));
  const passages = personnesParMaillon(lignee);

  const maillons = (lignee.maillons || []).map((maillon, rang) => {
    const groupe = fiches.get(maillon.fichier);
    if (!groupe) throw new Error(`vue-lignee : ${fichier} nomme ${maillon.fichier}, absent de pivot_data/groupes/`);
    const comparaison = comparaisons.get(cleDe(groupe)) ?? null;
    const sigle = groupe.groupe_sigle ?? null;
    const partage = partageDuGroupe(groupe);
    const fin = groupe.periode?.fin ?? null;

    return {
      id: idsDeFiche.get(maillon.fichier),
      groupeId: groupe.groupe_id,
      sigle,
      nom: groupe.groupe_nom ?? null,
      legislature: groupe.legislature ?? null,
      periode: {
        debut: groupe.periode?.debut ?? null,
        fin,
        actif: groupe.periode?.actif ?? false,
      },
      // Recopiée du maillon, jamais réunie : l'Assemblée la publie par
      // législature (#686), et en choisir une pour la lignée serait un
      // jugement que personne n'a porté (§2 règle 1).
      posture: postureDuGroupe(groupe),
      // Les deux noms de l'effectif (#653) et la date à laquelle il se
      // rapporte : `datee: false` ne veut pas dire « aujourd'hui » — les deux
      // fiches Sénat gelées n'en portent aucune.
      effectif: effectifDuGroupe(groupe).valeur,
      dateReference: dateDeReference(groupe).date,
      // Ce que la fiche dit de ses propres listes : un maillon hors périmètre
      // (Sénat, #528) déclare pourquoi elles sont vides, et c'est ce que la page
      // écrit à leur place — jamais un zéro (§2 règle 5).
      couverture: couvertureRoster(groupe),
      // Ce que la fiche signale d'elle-même, et qui varie d'un maillon à
      // l'autre — la section 6. Le reste des limites vit sur `/couverture`.
      signalements: signalementsDuMaillon(groupe),
      serie: serieEffectif(groupe.membres, fin ?? aujourdhui),
      // [rang de la personne, état de passage] — la liste des noms est portée
      // une fois, au niveau de la lignée.
      presents: passages[rang].personnes.map((p) => [rangPersonne.get(p.id), p.passage]),
      comptes: passages[rang].comptes,
      sujets: {
        liste: etiquettesThematiques(groupe, 10),
        total: (groupe.tags_thematiques_agreges || []).length,
        denominateur: (groupe.membres || []).length,
      },
      amendements: amendementsDuMaillon(groupe, repartitions.get(maillon.fichier)),
      // Les textes portés par ses membres, un dossier une fois — `null` quand
      // la fiche n'en permet pas la lecture (Sénat), jamais une liste vide.
      textes: repartitions.get(maillon.fichier)?.textes ?? null,
      quorum: quorumDeLaFiche(groupe),
      partage: {
        mesurables: partage.mesurables,
        uneSeuleVoix: partage.uneSeuleVoix,
        partages: partage.partages,
        pourEtContre: partage.pourEtContre,
      },
      ...avecIntitules(
        convergencesDeroulables(comparaison, sigle, parId, ligneeDeFiche, nomsDesLignees, dernieresLectures),
        scrutinsParPartage(groupe, (id) => parId.get(id)?.date ?? ''),
        parId,
        dernieresLectures,
      ),
    };
  });

  return {
    schema_version: 'vue-lignee-v1',
    id: idDePage(fichier),
    ligneeId: lignee.lignee_id,
    nom: lignee.lignee_nom,
    chambre: lignee.chambre,
    periode: lignee.periode,
    cumul: lignee.effectif?.cumul_historique ?? personnes.length,
    couverture: lignee.meta?.couverture_profils ?? null,
    genereLe: lignee.meta?.genere_le ?? null,
    licence: lignee.meta?.licence_donnees ?? null,
    personnes,
    maillons,
  };
}

/* ── LES DÉBATS COMPLETS D'UNE LIGNÉE, POUR LA RECHERCHE (#979) ──────────────
 *
 * La projection ne porte que les dix débats les plus portés de chaque maillon :
 * c'est ce que « Sur quoi ils ont pris la parole » affiche. Une recherche sur
 * la fiche doit pourtant les couvrir TOUS — 284 débats pour NG-15, dont 274
 * qu'elle ne verrait pas. Les livrer dans la projection coûtait ~2 Mo sur les
 * 29 fiches (+336 Ko pour la lignée socialiste, mesuré le 17/09/2026), payés
 * par chaque lecteur. Ils vivent donc à part, et la page ne les charge que
 * quand un mot est tapé.
 *
 * Même règle que la projection (`etiquettesThematiques`), sans limite ; une
 * entrée compacte `[intitulé, porteurs]`, le dénominateur une fois par maillon. */
export function construireDebatsLignee({ fichier, lignee, fiches, idsDeFiche }) {
  const maillons = {};
  for (const maillon of lignee.maillons || []) {
    const groupe = fiches.get(maillon.fichier);
    if (!groupe) throw new Error(`vue-lignee : ${fichier} nomme ${maillon.fichier}, absent de pivot_data/groupes/`);
    const debats = etiquettesThematiques(groupe, Infinity);
    maillons[idsDeFiche.get(maillon.fichier)] = {
      denominateur: (groupe.membres || []).length,
      debats: debats.map((d) => [d.label, d.porteurs]),
    };
  }
  return { schema_version: 'debats-lignee-v1', id: idDePage(fichier), maillons };
}
