/* ── Rattacher un rôle à la législature ou au gouvernement de sa période (#1329) ─
 *
 * Les mandats d'un profil ne portent ni l'identifiant de leur législature ni
 * celui de leur gouvernement : seulement leurs dates et leur intitulé. Or deux
 * législatures ne se chevauchent jamais, deux gouvernements non plus. Un rôle
 * se rattache donc à la période qu'il recouvre LE PLUS LONGTEMPS : c'est un
 * fait de calendrier, pas une lecture de l'intitulé, que
 * `regrouper-nest-pas-joindre-639` interdit.
 *
 * PAS LA DATE DE DÉBUT SEULE : un mandat de député commence le jour de
 * l'élection, quelques jours avant l'ouverture de la législature. Gabriel
 * Attal, élu le 18/06/2017, serait tombé dans la XIVe, close le 20/06/2017.
 *
 * Mesuré le 26/10/2026 sur les 34 candidats du manifeste : les 20 appartenances
 * à un gouvernement sont rattachées, et le gouvernement trouvé est chaque fois
 * celui que nomme l'intitulé ; 27 des 35 sièges à l'Assemblée sont rattachés,
 * les 8 autres sont antérieurs à la XIVe, sans fiche.
 *
 * À durée égale, la période la plus récente l'emporte. Un rôle sans fin court
 * jusqu'à aujourd'hui.
 */
const JOUR = 86400000;

export function periodeDuRole(debut, fin, periodes = [], aujourdhui = new Date().toISOString().slice(0, 10)) {
  if (!debut) return null;
  const finDuRole = fin || aujourdhui;
  let retenue = null;
  let meilleure = -1;
  for (const p of periodes) {
    if (!p.debut) continue;
    const a = debut > p.debut ? debut : p.debut;
    const finP = p.fin || aujourdhui;
    const b = finDuRole < finP ? finDuRole : finP;
    if (a > b) continue;
    const duree = (Date.parse(b) - Date.parse(a)) / JOUR;
    if (duree > meilleure || (duree === meilleure && p.debut > retenue.debut)) {
      retenue = p;
      meilleure = duree;
    }
  }
  return retenue;
}
