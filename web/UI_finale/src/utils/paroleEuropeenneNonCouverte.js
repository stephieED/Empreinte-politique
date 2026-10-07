/* ── LES ANNÉES DE MANDAT EUROPÉEN SANS PRISE DE PAROLE PUBLIÉE (#1163) ──────
 *
 * Deux candidats ont cinq ans de mandat au Parlement européen sans une seule
 * prise de parole sur leur fiche : aucune source ne les publie pour ces
 * années-là. Mesuré par la session Backend le 07/10/2026 — ni les fichiers de
 * ParlTrack, ni son site, ni le portail du Parlement européen. Ce n'est ni une
 * panne ni un oubli de collecte, et rien ne viendra combler ces années.
 *
 * Arbitré par la propriétaire le 07/10/2026 : le dire dans « Ce qu'on n'a pas
 * pu lire », sans chercher d'autre source pour l'instant.
 *
 * CE QUE CE MODULE LIT, ET RIEN D'AUTRE. Dans `couverture.interventions` de la
 * fiche, les entrées `etat: "hors_couverture"` et `source: "parlement_europeen"`
 * dont `portee.debut` est une date. C'est la forme que les données emploient
 * déjà pour dire « l'Assemblée ne publie rien avant telle date » : aucun champ
 * nouveau. `portee.fin` absente se dit « depuis ».
 *
 * LA TOURNURE EST CELLE DE LA LIGNE DE L'ASSEMBLÉE — « Son mandat … n'est pas
 * couvert : … » —, arrêtée par la propriétaire pour la section. La fin de la
 * phrase dit ce qui manque et seulement cela : les votes de ces années sont
 * publiés, eux.
 *
 * Ce module n'importe rien : `tests/test_parole_europeenne_non_couverte_1163.py`
 * l'exécute.
 */

const MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'];
const moisEtAnnee = (iso) => `${MOIS[Number(iso.slice(5, 7)) - 1]} ${iso.slice(0, 4)}`;
// « d’avril », « d’août », « d’octobre » : la préposition s'élide devant voyelle.
const deMois = (iso) => (/^[ao]/.test(moisEtAnnee(iso)) ? `d’${moisEtAnnee(iso)}` : `de ${moisEtAnnee(iso)}`);
const estUneDate = (v) => typeof v === 'string' && /^\d{4}-\d{2}-\d{2}/.test(v);

export const CLE_PAROLE_EUROPEENNE_NON_COUVERTE = 'parole-europeenne-non-couverte';

export function paroleEuropeenneNonCouverte(profil) {
  const periodes = (profil?.couverture?.interventions || [])
    .filter((e) => e?.etat === 'hors_couverture' && e?.source === 'parlement_europeen' && estUneDate(e?.portee?.debut))
    .map((e) => ({ debut: e.portee.debut.slice(0, 10), fin: estUneDate(e.portee.fin) ? e.portee.fin.slice(0, 10) : null }))
    .sort((a, b) => (a.debut < b.debut ? -1 : 1));
  if (!periodes.length) return [];
  const dites = periodes
    .map((p) => (p.fin ? `${deMois(p.debut)} à ${moisEtAnnee(p.fin)}` : `depuis ${moisEtAnnee(p.debut)}`))
    .join(', puis ');
  return [{
    cle: CLE_PAROLE_EUROPEENNE_NON_COUVERTE,
    titre: 'Parlement européen',
    texte: `Son mandat ${dites} n’est pas couvert : la source ne publie aucune de ses prises de parole.`,
    periodes,
  }];
}
