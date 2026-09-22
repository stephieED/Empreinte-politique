/* ── La recherche sur une fiche de groupe (#979) ─────────────────────────────
 *
 * LE MÊME GESTE QUE SUR LA FICHE CANDIDAT, SUR UNE PROJECTION. La page de
 * lignée ne lit pas des profils mais `vue-lignee`, calculée au build ; le filtre
 * réduit donc la PROJECTION, maillon par maillon, et recompte ce que chaque
 * figure publie à partir des listes qu'elle transporte déjà :
 *
 * - « Sur quoi ils ont pris la parole » : les débats dont l'intitulé porte le
 *   mot, pris dans la liste COMPLÈTE quand elle est chargée (`debats`) — la
 *   projection n'en porte que dix ;
 * - « Ce qu'ils ont proposé » : les textes portés par leur titre ; les
 *   amendements par le titre de leur dossier, commission par commission, les
 *   totaux recomptés sur les dossiers retenus ;
 * - « Ce qu'ils ont voté » : les scrutins de chaque part par leur intitulé, et
 *   les trois parts recomptées sur eux ;
 * - « Avec qui ils votent » : les textes comparés par leur intitulé, chaque
 *   nature et le nombre de textes communs recomptés.
 *
 * Ce qui NE SE RECOMPTE PAS se retire plutôt que de rester faux sous le mot :
 * le nombre total de scrutins agrégés (aucune liste ne le porte) et le reste
 * d'amendements sans type de déposant. C'est le composant qui les tait.
 *
 * Arbitré sur maquette le 17/09/2026 (Socialistes, « retraite »). */
import { contientLesMots, motsDuFiltre } from './filtreIntitule.js';
import { dansLaFenetre } from './filtrePeriode.js';
import { extraitsPortentLesMots } from './extraits.js';
import { amendementsQuiPortent } from './amendementsMots.js';
import { repartitionParCommission } from './lignee.js';

const somme = (liste, cle) => liste.reduce((a, x) => a + (x[cle] || 0), 0);

function detailRetenu(detail, ok) {
  const d = (detail || []).filter((x) => ok(x.titre));
  return { detail: d, textes: d.length, amendements: somme(d, 'amendements') };
}

function amendementsRetenus(parType, ok) {
  const out = {};
  for (const [type, bloc] of Object.entries(parType || {})) {
    const lignes = (bloc.lignes || [])
      .map((l) => ({ ...l, ...detailRetenu(l.detail, ok) }))
      .filter((l) => l.amendements > 0);
    const nd = bloc.nonEtablie ? detailRetenu(bloc.nonEtablie.detail, ok) : null;
    const tous = [...lignes.flatMap((l) => l.detail), ...(nd?.detail || [])];
    if (!tous.length) continue;
    out[type] = {
      amendements: somme(tous, 'amendements'),
      adoptes: somme(tous, 'adoptes'),
      dossiers: new Set(tous.map((d) => d.dossier)).size,
      lignes,
      nonEtablie: nd && nd.amendements > 0 ? nd : null,
    };
  }
  return out;
}

/* La répartition d'un maillon recomptée sur les amendements retenus. `table` :
 * `<maillon>.amendements.json` (scripts/amendements-lignees.mjs). */
function repartitionDesRetenus(table, parTypePublie, { mots, saisie, ok, periode, debut }) {
  const parContenu = mots.length && table.vocabulaire ? amendementsQuiPortent([table.vocabulaire], saisie) : null;
  const amendements = {};
  const textes = {};
  const commissions = new Map();
  const statuts = new Map();
  for (const [texte, dossier, titre, commission, statut] of table.textes) {
    textes[texte] = { dossier_id: dossier, titre };
    if (dossier) { commissions.set(dossier, commission); statuts.set(dossier, statut); }
  }
  const retenus = [];
  table.ids.forEach((id, i) => {
    const [type, adopte, date, t] = table.rows[i];
    const texte = t === null ? null : table.textes[t];
    if (periode && !dansLaFenetre(date, debut)) return;
    if (mots.length && !ok(texte?.[2]) && !parContenu?.has(id.replace(/^an:/, ''))) return;
    amendements[id] = { type_deposant: table.types[type], sort: adopte ? 'adopté' : null, date, texte_vise: texte?.[0] ?? null };
    retenus.push(id);
  });
  const { types } = repartitionParCommission(
    retenus, amendements, textes,
    (dossier) => (commissions.get(dossier) ? { sigle: commissions.get(dossier) } : null),
    (dossier) => statuts.get(dossier) ?? null,
  );
  // Seuls les types dont la répartition a été vérifiée au build restent.
  return Object.fromEntries(Object.entries(types).filter(([type]) => parTypePublie?.[type]));
}

/**
 * La lignée réduite à ce que le mot et la période portent. Rend l'objet
 * INCHANGÉ sans l'un ni l'autre.
 * `debats` : `{ [id de maillon]: sujets.liste complète }`, ou `null`.
 * `periode` / `debut` : la case cochée (`6m`, `12m`) et la date où sa fenêtre
 * commence (#1074).
 *
 * SOUS UNE PÉRIODE, LA PAROLE SE LIT DANS LES FENÊTRES DE BACKEND (#1077) : le
 * nombre de membres distincts intervenus sur chaque débat pendant la fenêtre,
 * sur le dénominateur de cette fenêtre. Les scrutins et les textes se datent
 * eux-mêmes. LES AMENDEMENTS SE RETIRENT : la projection les compte par
 * dossier sur toute la législature, avec la seule date du dernier — les
 * recompter dans une fenêtre serait inventer. C'est le composant qui le dit.
 */
export function filtrerLignee(lignee, saisie, debats = null, periode = null, debut = null, extraits = null, tablesAmendements = null) {
  const mots = motsDuFiltre(saisie);
  if ((!mots.length && !periode) || !lignee) return lignee;
  const ok = (texte) => !mots.length || contientLesMots(texte, mots);
  const date = (d) => !periode || dansLaFenetre(d, debut);
  return {
    ...lignee,
    maillons: lignee.maillons.map((m) => {
      const intituleOk = ([id]) => ok(m.scrutins?.[id]?.texte) && date(m.scrutins?.[id]?.date);
      const listes = Object.fromEntries(
        Object.entries(m.partageListes || {}).map(([part, l]) => [part, l.filter(intituleOk)]),
      );
      const uneSeuleVoix = (listes.une_seule_voix || []).length;
      const partages = (listes.partages || []).length;
      /* AMENDEMENT PAR AMENDEMENT (#1029, voie 2), quand la table du maillon
         est chargée : un amendement reste si l'intitulé de son dossier OU son
         exposé porte le mot, et s'il est daté dans la fenêtre — la période
         redevient possible. La répartition se recompte par LA règle du build
         (`repartitionParCommission`), sur les seuls types vérifiés. Sans table,
         l'ancien geste : par dossier, et rien sous une période. */
      const table = tablesAmendements?.[m.id] ?? null;
      const parType = table
        ? repartitionDesRetenus(table, m.amendements?.parType, { mots, saisie, ok, periode, debut })
        : periode ? {} : amendementsRetenus(m.amendements?.parType, ok);
      const complete = debats?.[m.id] || m.sujets.liste;
      /* UNE FENÊTRE QUI NE RECOUPE PAS CELLE DU SITE NE COMPTE PAS. Sur une
         fiche close — XVe, XVIe législature —, Backend compte « 6 mois » depuis
         la fin de la fiche : 2023-12-09 → 2024-06-09 pour le RN de la XVIe.
         Mesuré le 22/09/2026 : 16 des 29 fiches AN dans ce cas. Sous la case,
         ces débats de 2024 s'afficheraient sous « depuis le 22/03/2026 ». Une
         fenêtre qui finit avant le début de celle du site n'a donc rien dedans. */
      const brute = periode ? (complete.fenetres?.[periode] ?? null) : null;
      const fenetre = brute && (!debut || (brute.fin && brute.fin >= debut)) ? brute : null;
      /* CE QUI A ÉTÉ DIT (#1029) : un débat reste aussi quand les EXTRAITS de
         ses membres portent le mot, dans la période cochée. `parIntitule` le
         dit au débat ouvert, qui ne montre alors que ces extraits-là. */
      const retenu = (s) => ok(s.label)
        || (mots.length > 0 && extraitsPortentLesMots(extraits?.[m.id], s.label, mots, periode));
      const marque = (s) => ({ ...s, parIntitule: ok(s.label) });
      const sujets = periode
        ? (fenetre ? complete : [])
          .map((s) => ({ ...s, porteurs: s.parFenetre?.[periode] ?? null, denominateur: fenetre?.nb_membres ?? null }))
          .filter((s) => s.porteurs > 0 && retenu(s)).map(marque)
        : complete.filter(retenu).map(marque);
      return {
        ...m,
        sujets: {
          ...m.sujets,
          liste: sujets,
          total: sujets.length,
          ...(periode ? { denominateur: fenetre?.nb_membres ?? null } : {}),
        },
        amendementsHorsPeriode: Boolean(periode) && !table,
        textes: m.textes ? m.textes.filter((t) => ok(t.titre) && date(t.date_max ?? t.date_min)) : m.textes,
        amendements: {
          ...m.amendements,
          parType,
          distincts: Object.values(parType).reduce((a, b) => a + b.amendements, 0),
        },
        partageListes: listes,
        partage: {
          mesurables: uneSeuleVoix + partages,
          uneSeuleVoix,
          partages,
          pourEtContre: (listes.pour_et_contre || []).length,
        },
        quorum: { ...m.quorum, mesurables: uneSeuleVoix + partages },
        convergences: m.convergences
          ? m.convergences.map((autre) => {
            const scrutins = Object.fromEntries(
              Object.entries(autre.scrutins || {}).map(([nature, l]) => [nature, l.filter(intituleOk)]),
            );
            const natures = autre.natures.map((n) => ({ ...n, valeur: (scrutins[n.cle] || []).length }));
            const autres = (scrutins.autres || []).length;
            return { ...autre, scrutins, natures, autres, communs: somme(natures, 'valeur') + autres };
          })
          : m.convergences,
      };
    }),
  };
}

/* Ce que chaque section retient d'un maillon sous un mot : les maillons sans
 * rien sont retirés de la pile (forme B), sauf s'ils le sont tous — la section
 * dit alors que le mot ne trouve rien. */
export const MAILLON_A_DES_RESULTATS = {
  parole: (m) => m.sujets.liste.length > 0,
  propose: (m) => (m.textes?.length || 0) > 0 || Object.keys(m.amendements?.parType || {}).length > 0,
  vote: (m) => m.partage.mesurables > 0,
  avec: (m) => (m.convergences || []).some((a) => a.communs > 0),
};
