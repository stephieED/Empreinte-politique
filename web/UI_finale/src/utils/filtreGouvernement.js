/* ── La recherche sur une fiche de gouvernement (#979) ───────────────────────
 *
 * LE MÊME GESTE QUE SUR LA FICHE DE GROUPE, sur une fiche plus simple. Le
 * filtre réduit la vue avant le rendu, et les deux sections qui portent des
 * intitulés se recalculent ensemble, figure et liste :
 *
 * - « Sur quoi ils ont pris la parole » : les débats dont l'intitulé porte le
 *   mot. La section n'en affiche que les dix plus portés, mais la fiche a
 *   téléchargé la liste ENTIÈRE (`paroles.tous`) : la recherche la couvre sans
 *   rien charger de plus — contrairement à la lignée, dont la projection ne
 *   transporte que les dix (`filtreLignee`) ;
 * - « Ce qu'il a fait déposer » : les textes dont le titre porte le mot. La
 *   figure des matières et des sorts est dessinée à partir de cette liste :
 *   filtrée, elle suit d'elle-même.
 *
 * Ce que le filtre NE TOUCHE PAS : « En bref » et « Qui le composait » — ni
 * chiffres ni personnes ne portent d'intitulé, et les deux sections se retirent
 * tant qu'un mot est tapé —, et « Ce qu'on n'a pas pu lire », qui reste
 * affichée : ses limites portent sur la collecte, jamais sur le mot.
 */
import { contientLesMots, motsDuFiltre } from './filtreIntitule.js';

/**
 * La fiche réduite à ce que le mot porte. Rend la vue INCHANGÉE sans mot.
 *
 * `paroles.total` suit la liste retenue : le pied de section compte « N sur M
 * débats », et M sous un mot est le nombre de débats qui le portent, pas le
 * corpus entier. `denominateur` et `membres` ne bougent pas : ce sont des
 * effectifs de membres, pas des intitulés (§2 règle 7 — un numérateur filtré
 * sur un dénominateur filtré ne dirait plus de quoi il est le ratio).
 */
export function filtrerGouvernement(gouvernement, saisie) {
  const mots = motsDuFiltre(saisie);
  if (!mots.length || !gouvernement) return gouvernement;
  const ok = (texte) => contientLesMots(texte, mots);
  const debats = (gouvernement.paroles?.tous || gouvernement.paroles?.liste || [])
    .filter((s) => ok(s.label));
  return {
    ...gouvernement,
    paroles: { ...gouvernement.paroles, liste: debats, tous: debats, total: debats.length },
    textes: (gouvernement.textes || []).filter((t) => ok(t.titre)),
  };
}
