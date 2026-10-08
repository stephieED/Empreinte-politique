import { SUJET_NON_PUBLIE } from './sujetIntervention.js';

/* ── UN MÊME SUJET SOUS DEUX GRAPHIES (#1177, 07/10/2026) ────────────────────
 *
 * L'Assemblée intitule la même séance « Motion de censure » et « Motions de
 * censure ». L'agrégat des fiches de groupe (`tags_thematiques_agreges`) range
 * les deux sous une clé et publie la forme la plus fréquente ; la fiche, elle,
 * lisait l'intitulé exact, et comptait 26 membres là où l'agrégat en publie 34
 * (EPR, XVIIe). Arbitré par la propriétaire : la fiche regroupe avec la MÊME
 * clé.
 *
 * CE MODULE NE SERT QUE LA FICHE DE GROUPE. Sur la fiche candidat, deux intitulés
 * voisins restent deux entrées (#639, `tests/test_paroles_par_periode_328.py`) :
 * c'est pourquoi la règle ne vit pas dans `sujetIntervention.js`.
 *
 * `cleTagThematique` est la copie de `cle_tag_thematique` (`src/schema_pivot.py`),
 * et `tests/test_sujets_regroupes_1177.py` exécute les deux sur les mêmes
 * intitulés : elle retire le « s » final de chaque mot de plus de trois
 * lettres. Elle sert à REGROUPER, jamais à afficher — une clé est une forme
 * que la source n'écrit pas toujours (« fermeture de classe »).
 */
export function cleTagThematique(tag) {
  return String(tag || '').trim().toLowerCase().split(/\s+/).filter(Boolean)
    .map((mot) => ([...mot].length > 3 && mot.endsWith('s') ? mot.slice(0, -1) : mot))
    .join(' ');
}

/**
 * La forme sous laquelle chaque sujet s'affiche, une fois les graphies
 * regroupées : `Map(sujet lu → sujet affiché)`.
 *
 * La forme retenue est celle que l'agrégat publie (`formesPubliees`) ; pour un
 * sujet que l'agrégat ne porte pas, la plus fréquente parmi celles lues,
 * l'ordre alphabétique départageant une égalité — la règle de l'agrégat, et
 * toujours une forme de la source (§2 règle 2). « Intitulé non publié » n'est
 * pas un intitulé : il ne se regroupe avec rien.
 */
export function formesDesSujets(sujets, formesPubliees = []) {
  const publiee = new Map((formesPubliees || []).map((f) => [cleTagThematique(f), f]));
  const lues = new Map();
  for (const sujet of sujets || []) {
    if (sujet === SUJET_NON_PUBLIE) continue;
    const cle = cleTagThematique(sujet);
    if (!lues.has(cle)) lues.set(cle, new Map());
    lues.get(cle).set(sujet, (lues.get(cle).get(sujet) || 0) + 1);
  }
  const formes = new Map();
  for (const [cle, comptes] of lues) {
    const retenue = publiee.get(cle)
      ?? [...comptes].sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : 1))[0][0];
    for (const sujet of comptes.keys()) formes.set(sujet, retenue);
  }
  return formes;
}
