/* ── Le filtre de période (#1074) ────────────────────────────────────────────
 *
 * DEUX DURÉES FIXES, ET AUCUNE FENÊTRE LIBRE : « 6 derniers mois », « 12
 * derniers mois ». Arbitré le 22/09/2026 — deux dates libres sont l'outil idéal
 * pour découper la période qui fait dire ce qu'on veut aux chiffres. Sans case
 * cochée, la fiche montre tout.
 *
 * COMPTÉES DEPUIS LA DATE DES DONNÉES, pas depuis le jour : la fenêtre se lit
 * sur ce que le corpus contient (`donnees.json`, écrit par `sync-data`).
 *
 * LE MÊME GESTE QUE LE MOT : la période réduit ce que la fiche lit AVANT qu'elle
 * se construise, donc figures et listes suivent ensemble. Un élément sans date
 * ne passe pas une fenêtre active — on ne suppose pas (§2 règle 5).
 */

export const PERIODES = {
  '6m': { mois: 6, libelle: '6 derniers mois' },
  '12m': { mois: 12, libelle: '12 derniers mois' },
};

export function periodeValide(periode) {
  return Object.hasOwn(PERIODES, periode ?? '') ? periode : null;
}

/** La date de début de la fenêtre, `AAAA-MM-JJ`, ou null sans période. */
export function debutDeFenetre(au, periode) {
  const p = PERIODES[periode];
  if (!p || typeof au !== 'string' || !/^\d{4}-\d{2}-\d{2}/.test(au)) return null;
  const [annee, mois, jour] = au.slice(0, 10).split('-').map(Number);
  /* LE JOUR EST BORNÉ AU DERNIER DU MOIS D'ARRIVÉE : six mois avant le 31 août
     est le 28 février (29 en année bissextile), pas le 3 mars — `Date.UTC`
     déborde en silence sur le mois suivant. */
  const debutDuMois = new Date(Date.UTC(annee, mois - 1 - p.mois, 1));
  const dernierJour = new Date(Date.UTC(debutDuMois.getUTCFullYear(), debutDuMois.getUTCMonth() + 1, 0)).getUTCDate();
  debutDuMois.setUTCDate(Math.min(jour, dernierJour));
  return debutDuMois.toISOString().slice(0, 10);
}

export function dansLaFenetre(date, debut) {
  if (!debut) return true;
  return typeof date === 'string' && date.slice(0, 10) >= debut;
}

/** « depuis le 21/03/2026 ». */
export function libelleDebut(debut) {
  if (!debut) return '';
  const [a, m, j] = debut.split('-');
  return `depuis le ${j}/${m}/${a}`;
}

/**
 * Le profil pivot réduit à la fenêtre. Un texte porté y est s'il y a été ACTIF
 * — sa dernière date est dans la fenêtre —, pas seulement s'il y a été déposé.
 * Les votes et les amendements ne portent pas leur date dans le profil : le
 * lecteur de chaque date est fourni par l'appelant, qui a les index chargés.
 */
export function filtrerProfilParPeriode(pivot, debut, { dateDuVote, dateDeLAmendement }) {
  if (!debut || !pivot) return pivot;
  const garde = (liste, date) => (liste || []).filter((x) => dansLaFenetre(date(x), debut));
  return {
    ...pivot,
    interventions: garde(pivot.interventions, (i) => i.date),
    textes_portes: garde(pivot.textes_portes, (t) => t.date_max ?? t.date_min),
    votes: garde(pivot.votes, dateDuVote),
    amendements: garde(pivot.amendements, dateDeLAmendement),
  };
}
