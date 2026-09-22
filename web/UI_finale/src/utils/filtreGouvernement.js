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
import { extraitsPortentLesMots } from './extraits.js';

/**
 * La fiche réduite à ce que le mot porte. Rend la vue INCHANGÉE sans mot.
 *
 * `paroles.total` suit la liste retenue : le pied de section compte « N sur M
 * débats », et M sous un mot est le nombre de débats qui le portent, pas le
 * corpus entier. `denominateur` et `membres` ne bougent pas : ce sont des
 * effectifs de membres, pas des intitulés (§2 règle 7 — un numérateur filtré
 * sur un dénominateur filtré ne dirait plus de quoi il est le ratio).
 */
export function filtrerGouvernement(gouvernement, saisie, extraits = null, periode = null) {
  const mots = motsDuFiltre(saisie);
  if (!mots.length || !gouvernement) return gouvernement;
  const ok = (texte) => contientLesMots(texte, mots);
  /* CE QUI A ÉTÉ DIT (#1029) : un débat reste aussi quand ses EXTRAITS portent
     le mot — dans la période cochée —, même si son intitulé ne le porte pas.
     `parIntitule` le dit au débat ouvert, qui ne montre alors que les extraits
     qui portent le mot. Sans index chargé, l'intitulé seul décide. */
  const debats = (gouvernement.paroles?.tous || gouvernement.paroles?.liste || [])
    .map((s) => ({ ...s, parIntitule: ok(s.label) }))
    .filter((s) => s.parIntitule || extraitsPortentLesMots(extraits, s.label, mots, periode));
  return {
    ...gouvernement,
    paroles: { ...gouvernement.paroles, liste: debats, tous: debats, total: debats.length },
    textes: (gouvernement.textes || []).filter((t) => ok(t.titre)),
  };
}
