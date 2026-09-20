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

/**
 * La lignée réduite à ce que le mot porte. Rend l'objet INCHANGÉ sans mot.
 * `debats` : `{ [id de maillon]: sujets.liste complète }`, ou `null`.
 */
export function filtrerLignee(lignee, saisie, debats = null) {
  const mots = motsDuFiltre(saisie);
  if (!mots.length || !lignee) return lignee;
  const ok = (texte) => contientLesMots(texte, mots);
  return {
    ...lignee,
    maillons: lignee.maillons.map((m) => {
      const intituleOk = ([id]) => ok(m.scrutins?.[id]?.texte);
      const listes = Object.fromEntries(
        Object.entries(m.partageListes || {}).map(([part, l]) => [part, l.filter(intituleOk)]),
      );
      const uneSeuleVoix = (listes.une_seule_voix || []).length;
      const partages = (listes.partages || []).length;
      const parType = amendementsRetenus(m.amendements?.parType, ok);
      const sujets = (debats?.[m.id] || m.sujets.liste).filter((s) => ok(s.label));
      return {
        ...m,
        sujets: { ...m.sujets, liste: sujets, total: sujets.length },
        textes: m.textes ? m.textes.filter((t) => ok(t.titre)) : m.textes,
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
