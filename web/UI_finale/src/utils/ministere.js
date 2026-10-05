/*
 * UNE TEINTE PAR MINISTÈRE, la même dans les trois sections de la fiche de
 * gouvernement : la carte de « Qui le composait », les carrés des projets de
 * loi, la barre des actes au Journal officiel (forme A, retenue par la
 * propriétaire sur maquette le 04/10/2026).
 *
 * AUCUNE TABLE ÉCRITE À LA MAIN. Un libellé — le portefeuille du ministre qui
 * présente un projet (`initiateurs[].portefeuille`, #1204), le ministère d'un
 * acte — se rattache à sa carte par la règle qui construit ces cartes
 * (`organigramme`) : un ministre délégué « auprès du ministre de… » rejoint
 * le ministère que son titre nomme.
 *
 * LA TEINTE SUIT LE NOM, PAS LE RANG. Les cinq teintes d'avant étaient
 * attribuées au rang : la première barre était toujours bleue, d'une fiche à
 * l'autre. Ici, la place d'un ministère dans la palette vient du PREMIER MOT
 * de son nom (« économie », « justice », « armées ») ; elle ne glisse à la
 * place libre suivante que si un autre ministère de la même fiche l'occupe
 * déjà. Le même ministère garde ainsi le plus souvent sa teinte d'un
 * gouvernement à l'autre — le plus souvent, pas toujours, et rien ne le promet.
 *
 * 24 TEINTES, PAS UNE DE PLUS : au-delà, deux teintes ne se distinguent plus
 * (écart minimal entre deux teintes de la palette : 12,1, mesuré en OKLab × 100,
 * le seuil de `DESIGN_SYSTEM.md`). Une fiche qui compte plus de 24 ministères
 * sert d'abord ceux qui présentent un projet de loi ; les autres restent au
 * neutre. Le Premier ministre n'a pas de teinte : il signe tous les projets.
 */
import { motsClesPortefeuille, organigramme, rattachementDuPortefeuille } from './gouvernement.js';

export const PALETTE_MINISTERES = [
  '#f000fc', '#000cfc', '#fc0000', '#00a800', '#8400b4', '#0090fc', '#a80048', '#006c00',
  '#cc6ca8', '#b48400', '#9c60fc', '#0c54a8', '#0ca89c', '#fc8454', '#cc00a8', '#b44800',
  '#9c9cf0', '#6c24fc', '#9cb40c', '#6c5400', '#9054a8', '#fc1884', '#60843c', '#d878fc',
];
/** Le gris d'un projet ou d'un acte qu'aucun ministère de la fiche ne porte. */
export const GRIS_SANS_MINISTERE = '#b5b3af';

/** Les cartes de « Qui le composait », dans leur ordre d'affichage. */
export function polesDuGouvernement(government) {
  /* La source publie parfois DEUX mandats d'appartenance pour la même
     personne, dont un sans portefeuille — Damien Abad et Yaël Braun-Pivet
     sous Borne (#996). L'entrée muette est écartée UNIQUEMENT quand la
     personne est déjà placée ailleurs. */
  const nommes = new Set(government.membres.filter((m) => m.portefeuille).map((m) => m.nom));
  const membres = government.membres.filter((m) => m.portefeuille || !nommes.has(m.nom));
  return organigramme(membres, government.premierMinistre, government.periode);
}

/** La carte à laquelle un libellé de ministère se rattache, ou `null`. */
export function poleDuLibelle(poles, libelle) {
  if (!libelle) return null;
  const cle = motsClesPortefeuille(rattachementDuPortefeuille(libelle) || libelle);
  if (!cle) return null;
  return poles.find((p) => p.cle && (p.cle.startsWith(cle) || cle.startsWith(p.cle))) || null;
}

/** Les ministères qui présentent un texte, Premier ministre exclu. */
export function clesDuTexte(poles, texte) {
  const cles = new Set();
  for (const i of texte.initiateurs || []) {
    const p = poleDuLibelle(poles, i.portefeuille);
    if (p && !p.pm) cles.add(p.cle);
  }
  return [...cles];
}

function placeDuNom(cle) {
  const mot = String(cle).split(' ')[0];
  let h = 5381;
  for (const c of mot) h = ((h * 33) ^ c.codePointAt(0)) >>> 0;
  return h % PALETTE_MINISTERES.length;
}

/** `Map(clé de ministère → teinte)`. Un ministère absent de la table reste au neutre. */
export function teintesDesMinisteres(poles, textes = []) {
  const avecTexte = new Set(textes.flatMap((t) => clesDuTexte(poles, t)));
  const candidats = poles.filter((p) => !p.pm && p.cle);
  const ordre = [...candidats.filter((p) => avecTexte.has(p.cle)), ...candidats.filter((p) => !avecTexte.has(p.cle))];
  const prises = new Set();
  const teintes = new Map();
  for (const p of ordre) {
    if (prises.size >= PALETTE_MINISTERES.length) break;
    let place = placeDuNom(p.cle);
    while (prises.has(place)) place = (place + 1) % PALETTE_MINISTERES.length;
    prises.add(place);
    teintes.set(p.cle, PALETTE_MINISTERES[place]);
  }
  return teintes;
}

/** Le fond d'un carré : la teinte de son ministère, ou une bande par ministère
 *  quand plusieurs présentent le texte — aucun n'est choisi à la place des autres. */
export function fondDuTexte(poles, teintes, texte) {
  const couleurs = clesDuTexte(poles, texte).map((c) => teintes.get(c)).filter(Boolean);
  if (!couleurs.length) return GRIS_SANS_MINISTERE;
  if (couleurs.length === 1) return couleurs[0];
  const pas = 100 / couleurs.length;
  return `linear-gradient(135deg, ${couleurs.map((c, i) => `${c} ${(i * pas).toFixed(1)}% ${((i + 1) * pas).toFixed(1)}%`).join(', ')})`;
}

/** Le nom court d'un ministère, pour une légende : « Ministère de la justice » → « Justice ». */
export function nomCourtDuMinistere(titre) {
  const court = String(titre || '').replace(/^Minist[èe]re\s+(de la |de l’|de l'|des |du |de )/i, '');
  return court.charAt(0).toUpperCase() + court.slice(1);
}
