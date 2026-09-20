/*
 * Les règles de lecture d'une FICHE DE LIGNÉE — la page de groupe de #329,
 * depuis que la propriétaire a tranché, le 10/09/2026, qu'on publie une fiche
 * par lignée et non par maillon (#836).
 *
 * Ce module ne dessine rien. Il est importé DEUX FOIS : par le navigateur, et
 * par `scripts/vue-lignee.mjs`, qui en calcule la projection au build. Une
 * règle écrite une fois et lue par les deux ne peut pas diverger — d'où
 * l'extension explicite des imports, que Node exige et que Vite accepte.
 *
 * Ce qui est propre à la lignée, et seulement cela, est écrit ici. Le quorum,
 * le partage, les convergences restent dans `utils/groupe.js` : un maillon est
 * une fiche de groupe, et ses règles ne changent pas parce qu'on l'enchaîne.
 */

import { formatNumber, urlDossierAN } from './lecture.js';

/* ── Règle : l'effectif se recompte jour par jour, et retombe sur le publié ──
 *
 * La frise de « En bref » trace le nombre de membres du groupe à chaque date où
 * il change, depuis `membres[].periodes` (#809) — les intervalles réels
 * d'appartenance, jamais l'enveloppe `debut_dans_groupe`/`fin_dans_groupe`, qui
 * recolle en un seul intervalle un membre parti puis revenu.
 *
 * La courbe n'est pas une seconde source de l'effectif : sa valeur à la date de
 * référence d'un maillon RETROUVE `effectif.a_la_date_de_reference`, au membre
 * près, sur les 28 maillons AN du corpus du 11/09/2026. Un écart voudrait dire
 * que l'une des deux lectures a changé sans l'autre.
 *
 * Une fin d'appartenance est INCLUSE : le membre compte encore ce jour-là, et
 * ne sort que le lendemain.
 */
function lendemain(iso) {
  const d = new Date(`${iso}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + 1);
  return d.toISOString().slice(0, 10);
}

export function serieEffectif(membres, jusqua = null) {
  const evenements = new Map();
  const ajouter = (date, pas) => evenements.set(date, (evenements.get(date) ?? 0) + pas);

  for (const membre of membres || []) {
    const periodes = Array.isArray(membre?.periodes) && membre.periodes.length
      ? membre.periodes
      : [{ debut: membre?.debut_dans_groupe ?? null, fin: membre?.fin_dans_groupe ?? null }];
    for (const p of periodes) {
      // Une appartenance sans début n'est pas datée : elle ne se place sur
      // aucune date, plutôt que d'être posée d'office au premier jour (§2 r. 5).
      if (!p?.debut) continue;
      ajouter(p.debut, +1);
      if (p.fin) ajouter(lendemain(p.fin), -1);
    }
  }

  let niveau = 0;
  const points = [];
  for (const date of [...evenements.keys()].sort()) {
    niveau += evenements.get(date);
    points.push([date, niveau]);
  }
  return jusqua ? points.filter(([date]) => date <= jusqua) : points;
}

/* ── Règle : d'où vient chaque personne d'un maillon ─────────────────────────
 *
 * « Qui sont-ils » montre un point par personne et par maillon (forme B,
 * retenue par la propriétaire le 11/09/2026). Chaque point dit d'où vient la
 * personne, en trois états et pas plus :
 *
 *  - `prec`    — elle était du maillon qui précède immédiatement ;
 *  - `retour`  — elle était d'un maillon plus ancien, pas du précédent ;
 *  - `nouveau` — c'est son premier maillon dans la lignée.
 *
 * Trois états et non un taux de renouvellement : un taux comparé d'une lignée
 * à l'autre deviendrait un indice (§2 règle 1). Les trois comptes sont publiés
 * côte à côte, et leur somme retombe sur le nombre de personnes du maillon.
 *
 * « Nouveau dans la lignée » ne dit PAS « nouveau député » : la personne a pu
 * siéger ailleurs avant. La donnée ne porte que la lignée, et la page n'en dit
 * pas plus qu'elle.
 */
export const PASSAGES = {
  prec: { label: 'déjà là au groupe précédent', compte: 'déjà là' },
  retour: { label: "revenu d'un groupe plus ancien", compte: 'revenus' },
  nouveau: { label: 'nouveau dans la lignée', compte: 'nouveaux' },
};

export const ORDRE_PASSAGES = ['prec', 'retour', 'nouveau'];

/*
 * `indices` : les rangs des maillons où la personne figure, croissants.
 */
export function passage(indices, rang) {
  if (!indices.length || indices[0] === rang) return 'nouveau';
  return indices.includes(rang - 1) ? 'prec' : 'retour';
}

/*
 * Les personnes de chaque maillon, rangées par état puis par nom.
 *
 * `lignee.membres[].maillons` porte les `groupe_id` traversés (#836) : c'est lui
 * qui est lu, jamais une ressemblance de nom.
 */
export function personnesParMaillon(lignee) {
  const rangs = new Map((lignee?.maillons || []).map((m, i) => [m.groupe_id, i]));
  const personnes = (lignee?.membres || []).map((m) => ({
    id: m.membre_id,
    nom: m.nom,
    indices: (m.maillons || []).map((g) => rangs.get(g)).filter((i) => i != null).sort((a, b) => a - b),
  }));

  return (lignee?.maillons || []).map((_, rang) => {
    const presents = personnes
      .filter((p) => p.indices.includes(rang))
      .map((p) => ({ ...p, passage: passage(p.indices, rang) }))
      .sort((a, b) => ORDRE_PASSAGES.indexOf(a.passage) - ORDRE_PASSAGES.indexOf(b.passage)
        || a.nom.localeCompare(b.nom, 'fr'));
    const comptes = Object.fromEntries(ORDRE_PASSAGES.map((cle) => [cle, 0]));
    for (const p of presents) comptes[p.passage] += 1;
    return { personnes: presents, comptes };
  });
}

/* ── Règle : les amendements d'un maillon, par commission saisie au fond ─────
 *
 * « Ce qu'ils ont proposé » reprend le gabarit de la fiche candidat
 * (annotation de la propriétaire, 11/09/2026) : une barre par commission, le
 * ratio par texte au milieu, les textes distincts au bout. Les deux types de
 * déposant d'un groupe se lisent séparément, ou RÉUNIS quand le lecteur
 * sélectionne les deux (relecture du 11/09/2026) — voir `cumulerTypes`.
 *
 * LA POPULATION EST CELLE DE LA FICHE, et elle se VÉRIFIE. Un amendement compte
 * pour un maillon s'il figure dans l'`amendements[]` d'un de ses membres ET que
 * son identifiant porte la législature du maillon — la règle de #821, lue sur
 * l'identifiant et jamais sur une date —, une fois quel que soit le nombre de
 * cosignataires (#643). C'est une seconde écriture d'une règle du pipeline, et
 * elle n'est tolérable qu'à une condition : retomber sur les totaux publiés.
 * `sync-data` compare, type par type, à `amendements_agreges.par_type_deposant`
 * — 28 maillons AN sur 28 au chiffre près le 11/09/2026 — et ne publie PAS la
 * répartition d'un type qui s'en écarte. Un écart ne se corrige pas ici : il
 * dit que l'une des deux règles a bougé.
 *
 * La matière est la commission saisie au fond du DOSSIER (#328), par le même
 * chemin que la fiche candidat : `texte_vise` → `textes[].dossier_id` →
 * `commissions_dossiers.json`. Un amendement sans dossier, ou dont le dossier
 * n'a pas de commission connue, reste compté sous `null` — « matière non
 * établie » au rendu —, jamais déduit d'un intitulé (§2 règle 1).
 */
export const TYPES_DEPOSANT_GROUPE = ['depute', 'commission_rapporteur'];

export function repartitionParCommission(ids, amendements, textes, commissionDuDossier, statutDuDossier = () => null) {
  const parType = new Map();
  let introuvables = 0;
  for (const id of ids) {
    const a = amendements?.[id];
    if (!a) { introuvables += 1; continue; }
    const type = a.type_deposant || 'inconnu';
    if (!parType.has(type)) {
      parType.set(type, { n: 0, adoptes: 0, dossiers: new Set(), parCommission: new Map() });
    }
    const bloc = parType.get(type);
    bloc.n += 1;
    if (a.sort === 'adopté') bloc.adoptes += 1;
    const dossier = a.texte_vise ? (textes?.[a.texte_vise]?.dossier_id ?? null) : null;
    if (dossier) bloc.dossiers.add(dossier);
    const c = dossier ? commissionDuDossier(dossier) : null;
    const cle = c ? (c.sigle || c.nom || null) : null;
    if (!bloc.parCommission.has(cle)) bloc.parCommission.set(cle, { amendements: 0, dossiers: new Map() });
    const ligne = bloc.parCommission.get(cle);
    ligne.amendements += 1;
    if (dossier) {
      if (!ligne.dossiers.has(dossier)) {
        ligne.dossiers.set(dossier, {
          dossier,
          titre: textes?.[a.texte_vise]?.titre ?? null,
          sourceUrl: urlDossierAN(dossier),
          amendements: 0,
          adoptes: 0,
          dernier: null,
        });
      }
      const d = ligne.dossiers.get(dossier);
      d.amendements += 1;
      if (a.sort === 'adopté') d.adoptes += 1;
      if (a.date && (!d.dernier || a.date > d.dernier)) d.dernier = a.date;
    }
  }

  /* Les textes d'une commission, au clic (annotation du 11/09/2026). RANGÉS PAR
   * DATE, le plus récemment amendé d'abord, jamais par volume : déposer beaucoup
   * sur un texte peut être un travail de fond comme une obstruction, et le
   * nombre ne les distingue pas (règle de forme 6, #326). Le sort du TEXTE vient
   * de `scrutins_dossiers.json` (#758) et n'existe que pour un dossier passé par
   * un scrutin : ailleurs il reste `null`, dit « non publié » au rendu. */
  const textesDe = (dossiers) => [...dossiers.values()]
    .map((d) => ({ ...d, statut: statutDuDossier(d.dossier) }))
    .sort((x, y) => String(y.dernier ?? '').localeCompare(String(x.dernier ?? '')) || x.dossier.localeCompare(y.dossier));

  const types = {};
  for (const [type, bloc] of parType) {
    const lignes = [...bloc.parCommission.entries()]
      .filter(([cle]) => cle !== null)
      .map(([commission, l]) => ({
        commission, amendements: l.amendements, textes: l.dossiers.size, detail: textesDe(l.dossiers),
      }))
      // Par volume, puis par nom : jamais l'ordre d'insertion, qui rendrait une
      // égalité comme une avance.
      .sort((x, y) => y.amendements - x.amendements || x.commission.localeCompare(y.commission, 'fr'));
    const nd = bloc.parCommission.get(null);
    types[type] = {
      amendements: bloc.n,
      adoptes: bloc.adoptes,
      dossiers: bloc.dossiers.size,
      lignes,
      nonEtablie: nd ? { amendements: nd.amendements, textes: nd.dossiers.size, detail: textesDe(nd.dossiers) } : null,
    };
  }
  return { types, introuvables };
}

/* ── Règle : la frise de la lignée porte la posture en MOTIF ─────────────────
 *
 * Retenu par la propriétaire le 11/09/2026, en maquette, sur quatre jeux
 * comparés : majoritaire en aplat foncé, opposition en diagonales, minoritaire
 * en mauve clair uni, non déclarée en petits points serrés — un grisé. Les deux
 * postures « claires » ne sont pas un rang : la clarté sépare ce qui est dit de
 * ce qui ne l'est pas, pas un groupe d'un autre (§2 règle 1).
 *
 * La fiche candidat a retiré ses motifs le même jour (#328, « la frise dit
 * l'institution, et rien d'autre ») parce que la bande y portait DEUX
 * encodages, l'institution en teinte et la posture en motif. La frise d'une
 * lignée n'en porte qu'un : la teinte est toujours celle de l'Assemblée, et le
 * motif y est la seule chose qui change d'un maillon à l'autre.
 *
 * Les points restent dans la teinte de l'Assemblée : gris neutre, ils se
 * liraient comme l'encre des absences, qui désigne le Sénat ailleurs sur le
 * site. `absente` — une fiche qui ne porte pas le champ, les deux du Sénat — ne
 * prend aucun motif : c'est un contour tireté, un trou chez nous.
 */
export const MOTIFS_POSTURE = {
  majorite: 'plein',
  opposition: 'diagonales',
  minoritaire: 'mauve',
  non_declaree: 'points',
};

export function motifDePosture(posture) {
  return (posture?.declaree && MOTIFS_POSTURE[posture.valeur]) || 'absente';
}

/* ── Règle : les deux types de déposant, réunis ──────────────────────────────
 *
 * La propriétaire veut pouvoir sélectionner « comme députés » ET « comme
 * rapporteurs de commission », et lire alors des comptes portant sur les deux
 * catégories réunies (relecture du 11/09/2026). Deux comptes ne se réunissent
 * pas de la même façon :
 *
 *  - les AMENDEMENTS s'additionnent : un amendement n'a qu'un type de déposant,
 *    donc les deux ensembles sont disjoints, et la somme est le compte distinct ;
 *    même chose pour les adoptés ;
 *  - les TEXTES ne s'additionnent pas : un même dossier peut être amendé par un
 *    député et par un rapporteur, et la somme le compterait deux fois. Ils se
 *    réunissent sur `dossier` — une union, jamais une somme.
 *
 * Ce qui reste interdit ne change pas : aucun TAUX d'adoption commun aux types
 * de déposant (`AGENTS.md` §6). Réunir deux comptes n'est pas en faire un taux.
 *
 * Rend un bloc de la même forme qu'un type seul, pour que le rendu n'ait
 * qu'une lecture. Un seul type sélectionné rend son bloc tel quel.
 */
function reunirTextes(listes) {
  const parDossier = new Map();
  for (const detail of listes) {
    for (const d of detail || []) {
      const t = parDossier.get(d.dossier);
      if (!t) { parDossier.set(d.dossier, { ...d }); continue; }
      t.amendements += d.amendements;
      t.adoptes += d.adoptes;
      if (d.dernier && (!t.dernier || d.dernier > t.dernier)) t.dernier = d.dernier;
    }
  }
  return [...parDossier.values()]
    .sort((x, y) => String(y.dernier ?? '').localeCompare(String(x.dernier ?? '')) || x.dossier.localeCompare(y.dossier));
}

/* ── Règle : les textes qu'un groupe a portés, un dossier une fois ───────────
 *
 * La cascade de la fiche candidat, pour le groupe (annotation de la
 * propriétaire, 11/09/2026 : « le gabarit candidat, sankey et barres, avec le
 * switch auteur / rapporteur »). La collecte des textes portés couvre les
 * membres des groupes depuis le run du 11/09/2026 (`collect_dossiers_legislatifs`,
 * #835) : 993 des 1 148 profils de membres en portent, 10 092 entrées.
 *
 * LA POPULATION EST CELLE DES AMENDEMENTS. Un texte compte pour un maillon s'il
 * figure dans les `textes_portes[]` d'un de ses membres et que sa `legislature`
 * est celle du maillon — la règle de #821, lue sur un champ et jamais sur une
 * date. UN DOSSIER COMPTE UNE FOIS : une proposition de loi cosignée par
 * quarante membres est un texte, pas quarante (#643, même règle que les
 * amendements distincts).
 *
 * DEUX QUALITÉS, JAMAIS UNE TROISIÈME. Auteur (d'une proposition de loi ou de
 * résolution) et rapporteur (ou co-rapporteur). `initiateur_projet_de_loi` est
 * écarté : un projet de loi est signé comme MINISTRE, et un membre du
 * gouvernement ne porte pas un texte au nom de son groupe (#689). Un même
 * dossier peut porter les deux qualités — un membre l'a déposé, un autre en est
 * rapporteur : il est alors dans les deux, et une seule fois quand les deux
 * sont retenues ensemble, comme `cumulerTypes`.
 *
 * LE STADE D'UN DOSSIER EST LE PLUS AVANCÉ que ses copies portent : c'est un
 * fait du dossier, recopié sur chaque profil à la date de sa collecte. */
export const QUALITES_TEXTE = {
  auteur: ['auteur_proposition_de_loi', 'auteur_proposition_de_resolution', 'auteur'],
  rapporteur: ['rapporteur', 'co-rapporteur'],
};
const QUALITE_DU_ROLE = Object.fromEntries(
  Object.entries(QUALITES_TEXTE).flatMap(([q, roles]) => roles.map((r) => [r, q])),
);
const ORDRE_STADES = ['depose', 'examine_commission', 'inscrit_ordre_jour', 'discute_seance', 'adopte', 'promulgue'];
const rangStade = (s) => ORDRE_STADES.indexOf(s);

export function qualiteDuRole(role) {
  return QUALITE_DU_ROLE[role] ?? null;
}

export function textesDuMaillon(entrees, commissionDuDossier = () => null) {
  const parDossier = new Map();
  for (const t of entrees || []) {
    const qualite = qualiteDuRole(t?.role);
    if (!qualite || !t.dossier_id) continue;
    let d = parDossier.get(t.dossier_id);
    if (!d) {
      const c = commissionDuDossier(t.dossier_id);
      d = {
        dossier_id: t.dossier_id,
        titre: t.titre ?? null,
        nature_texte: t.nature_texte ?? null,
        stade_procedural: t.stade_procedural ?? null,
        sort: t.sort ?? null,
        sort_non_resolu: t.sort_non_resolu ?? null,
        date_min: t.date_min ?? null,
        date_max: t.date_max ?? null,
        legislature: t.legislature ?? null,
        source_url: t.source_url ?? null,
        commission: c ? { sigle: c.sigle ?? null, nom: c.nom ?? null } : null,
        roles: {},
      };
      parDossier.set(t.dossier_id, d);
    }
    if (rangStade(t.stade_procedural) > rangStade(d.stade_procedural)) {
      d.stade_procedural = t.stade_procedural;
      d.sort = t.sort ?? d.sort;
      d.sort_non_resolu = t.sort_non_resolu ?? d.sort_non_resolu;
    }
    if (t.date_min && (!d.date_min || t.date_min < d.date_min)) d.date_min = t.date_min;
    if (t.date_max && (!d.date_max || t.date_max > d.date_max)) d.date_max = t.date_max;
    if (!d.source_url && t.source_url) d.source_url = t.source_url;
    // Le rôle retenu par qualité : le premier rencontré, qui se relit tel quel
    // dans la liste ; le compte des membres qui le portent n'est pas publié —
    // il se lirait comme un palmarès interne au groupe (§2 règle 1).
    if (!d.roles[qualite]) d.roles[qualite] = t.role;
  }
  return [...parDossier.values()].sort((a, b) => String(b.date_max || '').localeCompare(String(a.date_max || '')));
}

/* Les textes d'une sélection de qualités, sous la forme que `textesPortes` de
 * la fiche candidat attend : la même règle de cascade, pas une seconde. */
export function textesDesQualites(textes, qualites) {
  const retenues = (qualites || []).filter((q) => QUALITES_TEXTE[q]);
  return (textes || [])
    .filter((t) => retenues.some((q) => t.roles?.[q]))
    .map((t) => ({ ...t, role: retenues.map((q) => t.roles[q]).find(Boolean) }));
}

/* ── Règle : ce qu'on n'a pas pu lire se dit fiche par fiche ─────────────────
 *
 * La section 6 porte ce que CHAQUE fiche de groupe signale d'elle-même, et
 * rien d'autre (arbitrage de `page-couverture-commune-328`) : une limite vraie
 * de tout le corpus vit sur `/couverture`, son raisonnement sous
 * `/methodologie#couverture`. Mesuré sur les 30 fiches du 11/09/2026 : trois
 * avertissements sont identiques en nature sur les 28 fiches AN — la source
 * AMO30, la date de référence, l'effectif min/max, et la carrière écartée des
 * agrégats — et ne sont donc PAS repris ici. Restent cinq signalements, portés
 * par 14 fiches sur 30 : 9 lignées sur 13 en ont au moins un.
 *
 * LA POPULATION EST CELLE DES PROFILS. Un vote sans identifiant de scrutin est
 * compté sur toute la carrière des membres, faute de législature lisible — la
 * phrase dit donc « des profils de ses membres », jamais « du groupe ».
 *
 * LU DANS LES CHAMPS QUAND IL Y EN A UN. `couverture_roster` et
 * `amendements_agreges.nb_sans_identifiant` sont structurés. Deux faits ne
 * vivent que dans `meta.warnings`, écrits par `group_profile.py` sur un gabarit
 * fixe : le motif s'ancre sur ce gabarit, et un test le relit dans le source
 * Python — un message reformulé casse le test, pas la page en silence.
 *
 * L'ordre est celui des sections de la page : membres (§1), interventions
 * (§2), amendements (§3), votes (§4 et §5). */
export const LISTES_SIGNALEES = {
  membres: 'Membres',
  interventions: 'Interventions',
  amendements: 'Amendements',
  votes: 'Votes',
};

export const MOTIFS_AVERTISSEMENT = {
  votesSansScrutin: /^cohesion_votes : (\d+) vote\(s\) sans scrutin_id écarté\(s\)/,
  interventionsSansLegislature: /^tags_thematiques_agreges : (\d+) intervention\(s\) dont l'identifiant ne porte pas de législature sont CONSERVÉES/,
  amendementsIntrouvables: /^amendements_agreges : (\d+) amendement\(s\) introuvable\(s\) dans l'index partagé/,
};

const pluriel = (n, un, plusieurs) => (n > 1 ? plusieurs : un);

export function signalementsDuMaillon(groupe) {
  const out = [];
  const lu = (motif) => {
    for (const w of groupe?.meta?.warnings || []) {
      const m = motif.exec(w);
      if (m) return Number(m[1]);
    }
    return 0;
  };

  const roster = groupe?.meta?.couverture_roster || {};
  const total = roster.roster_total;
  const profils = roster.profils_disponibles;
  if (Number.isInteger(total) && Number.isInteger(profils) && profils < total) {
    const manquent = total - profils;
    out.push({
      liste: 'membres',
      n: manquent,
      texte: roster.etat === 'hors_perimetre'
        ? `${formatNumber(profils)} profils pour ${formatNumber(total)} membres : le Sénat est hors du périmètre`
        : `${formatNumber(manquent)} ${pluriel(manquent, 'membre', 'membres')} sur ${formatNumber(total)} sans profil, `
          + `donc sans vote, amendement ni intervention lus`,
    });
  }

  const interventions = lu(MOTIFS_AVERTISSEMENT.interventionsSansLegislature);
  if (interventions) {
    out.push({
      liste: 'interventions',
      n: interventions,
      texte: `${formatNumber(interventions)} ${pluriel(interventions, 'intervention', 'interventions')} des profils `
        + `de ses membres sans législature dans leur identifiant, gardées dans les sujets`,
    });
  }

  const sansId = groupe?.amendements_agreges?.nb_sans_identifiant || 0;
  if (sansId) {
    out.push({
      liste: 'amendements',
      n: sansId,
      texte: `${formatNumber(sansId)} ${pluriel(sansId, 'amendement', 'amendements')} sans identifiant, `
        + `comptés une fois par signataire`,
    });
  }
  const introuvables = lu(MOTIFS_AVERTISSEMENT.amendementsIntrouvables);
  if (introuvables) {
    out.push({
      liste: 'amendements',
      n: introuvables,
      texte: `${formatNumber(introuvables)} ${pluriel(introuvables, 'amendement', 'amendements')} introuvables `
        + `dans l'index, écartés`,
    });
  }

  const votes = lu(MOTIFS_AVERTISSEMENT.votesSansScrutin);
  if (votes) {
    out.push({
      liste: 'votes',
      n: votes,
      texte: `${formatNumber(votes)} ${pluriel(votes, 'vote', 'votes')} des profils de ses membres sans identifiant `
        + `de scrutin, écartés`,
    });
  }
  return out;
}

export function cumulerTypes(parType, types) {
  const blocs = (types || []).map((t) => parType?.[t]).filter(Boolean);
  if (blocs.length <= 1) return blocs[0] ?? null;

  const parCommission = new Map();
  for (const bloc of blocs) {
    for (const l of bloc.lignes || []) {
      if (!parCommission.has(l.commission)) parCommission.set(l.commission, { amendements: 0, details: [] });
      const c = parCommission.get(l.commission);
      c.amendements += l.amendements;
      c.details.push(l.detail);
    }
  }
  const lignes = [...parCommission.entries()]
    .map(([commission, c]) => {
      const detail = reunirTextes(c.details);
      return { commission, amendements: c.amendements, textes: detail.length, detail };
    })
    .sort((x, y) => y.amendements - x.amendements || x.commission.localeCompare(y.commission, 'fr'));

  const nonEtablies = blocs.map((b) => b.nonEtablie).filter(Boolean);
  const detailNonEtabli = reunirTextes(nonEtablies.map((n) => n.detail));
  const dossiers = new Set();
  for (const l of lignes) for (const d of l.detail) dossiers.add(d.dossier);
  for (const d of detailNonEtabli) dossiers.add(d.dossier);

  return {
    amendements: blocs.reduce((a, b) => a + b.amendements, 0),
    adoptes: blocs.reduce((a, b) => a + b.adoptes, 0),
    dossiers: dossiers.size,
    lignes,
    nonEtablie: nonEtablies.length
      ? {
        amendements: nonEtablies.reduce((a, n) => a + n.amendements, 0),
        textes: detailNonEtabli.length,
        detail: detailNonEtabli,
      }
      : null,
  };
}
