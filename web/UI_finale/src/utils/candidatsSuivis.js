/* LES CANDIDATS SUIVIS, sur la page Sources (#1298).
 *
 * Qui le site compte comme candidat, et sur quelle source : la page le dit pour
 * chaque entrée de `raw_data/candidats.json`, copié tel quel par `sync-data`.
 * Les candidatures retirées restent dans le tableau (forme A, retenue le
 * 15/10/2026) : leur fiche n'est plus publiée, mais le lecteur doit pouvoir
 * savoir pourquoi un nom a disparu de l'onglet Candidats.
 *
 * L'ORDRE EST CELUI DU NOM AFFICHÉ, comme la barre des candidats
 * (`scripts/sync-data.mjs`) : jamais un classement (§2 règle 1), et pas de
 * patronyme reconstruit — « Le Pen » ou « Dupont-Aignan » demanderaient une
 * règle que la source ne donne pas.
 */

const MOIS = [
  'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
  'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre',
];

/* `AAAA-MM-JJ` → « 12 février 2026 », `AAAA-MM` → « décembre 2025 ». Une date
 * absente ou illisible rend `null` : la page écrit « non connue », jamais une
 * date devinée (§2 règle 5). */
export function dateEnClair(iso) {
  const m = /^(\d{4})-(\d{2})(?:-(\d{2}))?$/.exec(iso || '');
  if (!m) return null;
  const mois = MOIS[Number(m[2]) - 1];
  if (!mois) return null;
  if (!m[3]) return `${mois} ${m[1]}`;
  const jour = Number(m[3]);
  return `${jour === 1 ? '1er' : jour} ${mois} ${m[1]}`;
}

export const LIBELLES_STATUT = {
  declare: 'Déclarée',
  decline: 'Retirée',
  pressenti: 'Pressentie',
  officiel: 'Officielle',
};

function domaine(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, '');
  } catch {
    return url;
  }
}

/* LES SOURCES CROISÉES (`sources[]`, PR #1301) quand l'entrée a été relue ;
 * sinon la seule `source`, nommée par son domaine. Une entrée ajoutée par la
 * collecte automatique n'a que `source` jusqu'à sa relecture : le repli n'est
 * pas une compatibilité provisoire. */
export function sourcesDe(entree) {
  const liste = (entree.sources || []).filter((s) => s?.url);
  if (liste.length) {
    return liste.map((s) => ({ url: s.url, media: s.media || domaine(s.url), date: s.date || null }));
  }
  return entree.source ? [{ url: entree.source, media: domaine(entree.source), date: null }] : [];
}

/* `fichesPubliees` : les slugs du manifeste. Un slug dans la liste ne suffit
 * pas — une candidature retirée garde le sien, mais sa fiche est masquée, et un
 * lien y mènerait à une page absente. */
export function lignesCandidats(candidats, fichesPubliees) {
  return (candidats || [])
    .filter((c) => c?.nom)
    .map((c) => ({
      nom: c.nom,
      statut: LIBELLES_STATUT[c.statut] || null,
      retiree: c.statut === 'decline',
      declaration: dateEnClair(c.date_declaration),
      fiche: c.slug && fichesPubliees.has(c.slug) ? c.slug : null,
      sources: sourcesDe(c),
    }))
    .sort((a, b) => a.nom.localeCompare(b.nom, 'fr', { sensitivity: 'base' }));
}
