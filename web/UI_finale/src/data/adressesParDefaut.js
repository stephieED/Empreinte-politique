/* Où mènent `/groupes` et `/gouvernements`. `/candidats` ne mène plus à une
 * fiche choisie d'avance : c'est une page de choix (#1329).
 *
 * Module SANS IMPORT, et c'est voulu : `scripts/pages-par-adresse.mjs` le lit
 * sous Node au build pour écrire les pages de redirection (#969). Une seule
 * source, pour que la redirection de l'application et celle déclarée aux
 * moteurs de recherche ne puissent pas diverger. */
/* Une LIGNÉE, plus une fiche de législature (#329, #836) : l'adresse d'un
 * groupe vient de son `lignee_id` déclaré, et ne bouge pas quand il change de
 * sigle ou de législature. */
export const DEFAULT_GROUP_ID = 'AN-SOC';
export const DEFAULT_GOVERNMENT_ID = 'LECORNU_II';
