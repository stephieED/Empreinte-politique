// Projection de comparaison entre les groupes d'une même législature (#329).
//
// La fiche de groupe compare, à sa toute fin, les groupes de la MÊME
// législature : mêmes scrutins, même période, mêmes dénominateurs. Elle a donc
// besoin d'un peu de chaque fiche voisine — et « un peu » est le mot :
//
//   les 5 fiches AN de la XVIe pèsent 15,1 Mo ; ce dont les sections 4 et 5 ont
//   besoin en pèse ~150 Ko, parce que seules comptent les positions
//   majoritaires des scrutins où le QUORUM EST ATTEINT : 2 415 entrées sur les
//   19 832 publiées (SOC 341, LFI 615, REN 523, RN 751, LR 185).
//
// C'est la règle #628 appliquée au navigateur : on lit par projection, on ne
// garde pas le document. Faire télécharger 15,1 Mo pour en afficher 150 Ko
// serait le même défaut, de l'autre côté du fil.
//
// Depuis la page de lignée (#329), elle n'est plus servie : `vue-lignee.mjs` la
// lit en mémoire, au build, pour « Avec qui ils votent ». Elle ne rejoint
// jamais `pivot_data/`, et aucun contrôle de perte ne la surveille.

/** Clé de regroupement : une comparaison ne traverse ni chambre ni législature. */
export function cleLegislature(groupe) {
  return `${groupe.chambre ?? 'chambre-inconnue'}-${groupe.legislature ?? 'sans-legislature'}`;
}

/**
 * La projection d'UNE fiche. Ne conserve que ce que les sections 4 et 5 lisent.
 *
 * `positions` ne porte que les scrutins où `quorum_atteint` est vrai ET où une
 * position majoritaire existe : c'est exactement l'univers publiable. En
 * dessous du quorum, rien n'est publié — pas même approché —, donc rien n'est
 * embarqué.
 */
export function projeterGroupe(groupe, id) {
  const entrees = groupe.cohesion_votes || [];
  const positions = {};
  let mesurables = 0;
  for (const entree of entrees) {
    if (entree?.quorum_atteint !== true) continue;
    mesurables += 1;
    if (entree.position_majoritaire) positions[entree.scrutin_id] = entree.position_majoritaire;
  }

  const agg = groupe.amendements_agreges || {};
  return {
    id,
    groupeId: groupe.groupe_id ?? null,
    sigle: groupe.groupe_sigle ?? null,
    nom: groupe.groupe_nom ?? null,
    // #686 : portée par 5 des 7 fiches depuis le commit de données `693b076d`
    // (01/09/2026). Les 2 fiches du Sénat, gelées depuis #516, restent à `null`,
    // publié tel quel — la fiche déclare l'absence, elle ne la comble pas.
    //
    // La projection DOIT la transporter : c'est elle, et non la fiche voisine,
    // que `comparaisonParPosture` lit pour séparer majorité et opposition.
    positionPolitique: groupe.position_politique ?? null,
    effectif: groupe.effectif?.a_la_date_de_reference ?? groupe.effectif?.actuel ?? null,
    membresPublies: (groupe.membres || []).length,
    amendements: {
      deposes: agg.nb_amendements ?? null,
      adoptes: agg.nb_adoptes ?? null,
    },
    scrutinsAgreges: entrees.length,
    scrutinsMesurables: mesurables,
    positions,
  };
}

/**
 * Rassemble les projections par (chambre, législature).
 *
 * `fiches` est une liste de `{ id, groupe }`. Rend une Map clé → objet
 * sérialisable, un fichier par législature.
 */
export function construireComparaisons(fiches) {
  const parLegislature = new Map();
  for (const { id, groupe } of fiches) {
    const cle = cleLegislature(groupe);
    const bloc = parLegislature.get(cle) ?? {
      schema_version: 'comparaison-groupes-v1',
      chambre: groupe.chambre ?? null,
      legislature: groupe.legislature ?? null,
      groupes: [],
    };
    bloc.groupes.push(projeterGroupe(groupe, id));
    parLegislature.set(cle, bloc);
  }
  return parLegislature;
}
