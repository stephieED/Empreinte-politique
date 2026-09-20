// Ce que le dépôt porte, tous profils confondus — la matière de /couverture.
//
// POURQUOI ICI, ET PAS DANS `pivot_data/`. Cette projection ne crée aucun fait :
// elle compte ce que les sept sorties du pivot portent déjà, et le range par
// institution. En faire une huitième sortie ajouterait un job, un cache et un
// budget CI pour un fichier que seule l'interface lit — même raisonnement que
// `comparaison-groupes.mjs` (#329), calculé au build à partir de `pivot_data/`.
//
// POURQUOI UNE PAGE COMMUNE. Les deux tiers de « ce qu'on n'a pas pu lire »
// sont identiques sur toutes les fiches : les bornes de source, les
// rapprochements qui n'aboutissent pas, les institutions non couvertes. Une
// fiche les répétait 27 fois sans qu'aucune ne parle du candidat affiché.
//
// AUCUN CHIFFRE N'EST ÉCRIT À LA MAIN. Tout ce que la page affiche — les
// effectifs, les bornes, les noms des fiches où une liste manque — vient d'ici,
// mesuré au build. Un chiffre recopié dans du JSX est un chiffre qui aura
// vieilli au run suivant.
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import path from 'node:path';

/* ── Dates et tranches ──────────────────────────────────────────────────── */

/** Ramène une date au format ISO court, ou null si elle n'est pas lisible. */
export function iso(valeur) {
  if (typeof valeur !== 'string') return null;
  if (valeur.length >= 10 && valeur[4] === '-') return valeur.slice(0, 10);
  if (valeur.length === 10 && valeur[2] === '/') {
    const [j, m, a] = valeur.split('/');
    return `${a}-${m}-${j}`;
  }
  return null;
}

/* DEUX DATES, PAS DES TRANCHES (#328, 15/09/2026).
 *
 * Cette fonction rendait un segment par MOIS PORTEUR, les mois consécutifs
 * fusionnés — jusqu'à 78 segments pour les seuls mandats de l'Assemblée. Elle
 * répondait à la mauvaise question.
 *
 * Les blancs entre deux tranches ne disaient rien de la SOURCE : ils disaient
 * les mois où aucun de nos candidats déclarés n'était en fonction là. Mesuré le
 * 15/09/2026 : 73 mois sans aucun texte porté à l'Assemblée, 34 mois sans
 * mandat, 32 mois sans intervention européenne. Sur une page qui s'appelle
 * « Ce que le dépôt porte, et depuis quand », ces trous se lisent comme des
 * lacunes de collecte — l'inverse exact de ce qu'ils sont.
 *
 * L'étendue répond à la question posée : de quand à quand le dépôt porte-t-il
 * quelque chose. Deux dates, rien à fusionner, rien qui se recalcule au
 * prochain run — la robustesse était l'autre motif du changement.
 *
 * `null` quand aucune date n'est exploitable : un champ à zéro ne porte PAS un
 * segment de largeur nulle, qui se rendrait en trait fantôme. */
export function etendue(dates) {
  const jours = [...dates].filter(Boolean).map((d) => d.slice(0, 7)).sort();
  if (!jours.length) return null;
  return [`${jours[0]}-01`, `${jours[jours.length - 1]}-28`];
}

/* ── Lecture du pivot ───────────────────────────────────────────────────── */

const lire = (p) => JSON.parse(readFileSync(p, 'utf-8'));

/** Les profils publiés comme fiche de candidat, un par un — 652 fichiers
 *  chargés d'un coup saturent la mémoire du build. */
function* profilsCandidats(profilesDir, slugsPublies) {
  for (const f of readdirSync(profilesDir).filter((x) => x.endsWith('.pivot.json'))) {
    const slug = f.replace(/\.pivot\.json$/, '');
    if (slugsPublies && !slugsPublies.has(slug)) continue;
    const d = lire(path.join(profilesDir, f));
    if (d?.meta?.provenance !== 'candidat_declare') continue;
    yield d;
  }
}

/* ── Ce qui sépare le parlementaire du gouvernemental ────────────────────── */

/* TROIS MARQUEURS, AUCUNE DÉDUCTION. Chaque liste porte le sien, publié par la
 * source ; aucun n'est reconstruit à partir d'un intitulé (#639).
 *   - un mandat : `categorie === 'fonction_gouvernementale'` ;
 *   - un texte  : `role === 'initiateur_projet_de_loi'`, l'acte ministériel —
 *     un rapporteur sur un projet de loi reste un parlementaire ;
 *   - une intervention : `fonction`, la qualité que le compte rendu donne à
 *     l'orateur. 18 valeurs distinctes, dont 13 nomment une fonction
 *     gouvernementale et 5 la qualité de rapporteur. */
const QUALITE_GOUVERNEMENTALE = /\bministre\b|\bsecrétaire d[’']état\b/i;

export const estMandatGouvernemental = (m) => m?.categorie === 'fonction_gouvernementale';
export const estTexteMinisteriel = (t) => t?.role === 'initiateur_projet_de_loi';
export const estParoleMinisterielle = (i) =>
  Boolean(i?.fonction) && QUALITE_GOUVERNEMENTALE.test(i.fonction);

/* LE PARLEMENT EUROPÉEN EST UNE INSTITUTION DU DÉPÔT, pas une ligne « non
 * collectée » (11/09/2026). Le corpus en porte les cinq listes, collectées via
 * ParlTrack, et chacune le dit par un marqueur publié — jamais par un intitulé :
 *   - un mandat : `chambre === 'PE'` ou `categorie_source === 'europarl'` —
 *     180 commissions et délégations ne portent pas de `chambre` ;
 *   - un vote : `scrutin_non_resolu.institution`, l'Assemblée seule publiant
 *     un identifiant de scrutin que l'index partagé résout ;
 *   - un amendement : `amendement_non_resolu.institution` ;
 *   - un texte : `institution` ;
 *   - une intervention : `source.institution`.
 * Mesuré sur les 30 fiches de candidats publiées le 11/09/2026 : sans ces marqueurs, 160
 * mandats, 383 textes et 5 329 interventions européens étaient comptés sous
 * l'Assemblée, et les 11 013 votes et 7 303 amendements n'étaient nulle part.
 *
 * LE SÉNAT N'A PAS DE LIGNE, et cette phrase disait le contraire jusqu'au
 * 15/09/2026 : la hiérarchie n'en porte que trois — AN, gouvernement, PE. Ses
 * mandats sortent de la piste Assemblée (voir `estMandatSenatorial` plus bas),
 * mais ils ne sont encore affichés nulle part. Un manque déclaré, pas un
 * arbitrage rendu. */
const PE = 'parlement_europeen';

/* LA BORNE BASSE DE LA SOURCE EUROPÉENNE, mesurée sur les dumps ParlTrack
 * (parltrack.org/dumps, ODbL) le 11/09/2026 — la seule chose ici qui ne vient
 * pas de `pivot_data/`, et pour une raison : aucun profil ne la porte, le
 * pipeline ne déclarant que la dernière parution (#683). Une borne basse
 * d'archive ne vieillit pas comme une borne de fraîcheur (#484) : le premier
 * scrutin de 2004 restera le premier.
 *   - votes : 1er scrutin nominatif du dump `ep_votes` (44 648 scrutins,
 *     15/09/2004 → 26/03/2026) ;
 *   - amendements : 1er amendement daté du dump `ep_amendments` (commissions),
 *     01/02/2008 — le dump des amendements de séance commence en 2019.
 * Interventions et textes n'en ont pas : leurs dates sont celles de la
 * republication ParlTrack du 22/11/2016 pour tout ce qui précède (#858), pas celles
 * des séances. */
const BORNES_BASSES_PE = { votes: '2004-09-15', amendements: '2008-02-01' };

/* Les titres des cinq listes métier, pour les institutions qui n'en portent
 * aucune entrée : une ligne vide doit être NOMMÉE comme les autres, sinon le
 * lecteur ne sait pas ce qui manque. */
const TITRE_LISTE = {
  mandats: 'Mandats et appartenances',
  votes: 'Votes et scrutins',
  amendements: 'Amendements',
  textes_portes: 'Textes portés',
  interventions: 'Interventions',
};
const HORS_ASSEMBLEE = new Set(['Senat', 'PE']);
export const estMandatEuropeen = (m) => m?.chambre === 'PE' || m?.categorie_source === 'europarl';

/* UNE CHAMBRE SE RECONNAÎT À DEUX MARQUEURS, JAMAIS À UN SEUL (#885).
 *
 * `chambre` n'est porté que par le mandat électif lui-même. Les organes —
 * commissions, délégations, groupes d'amitié — n'en portent pas : leur seule
 * marque est `categorie_source`. Le Parlement européen l'avait appris à ses
 * dépens (180 organes sans `chambre`), et la ligne au-dessus teste donc ses
 * deux marqueurs depuis le 11/09/2026 ; le Sénat, entré au corpus le
 * 13/09/2026, n'avait jamais reçu le sien.
 *
 * Mesuré le 15/09/2026 sur les candidats déclarés : 133 mandats ont pour source
 * `senat.fr`, dont **7 seulement** portent `chambre: "Senat"`. Les 126 autres —
 * commissions et groupes d'amitié sénatoriaux — passaient le filtre par
 * `chambre: null` et étaient comptés sous l'Assemblée : 126 sur 1 124, soit
 * 11,2 % de cette ligne.
 *
 * Ne pas revenir à un test sur `chambre` seule : c'est la forme du défaut, pas
 * un raccourci. */
export const estMandatSenatorial = (m) => m?.chambre === 'Senat' || m?.categorie_source === 'senat';

export const estMandatAssemblee = (m) =>
  !estMandatGouvernemental(m)
  && !HORS_ASSEMBLEE.has(m?.chambre)
  && !estMandatSenatorial(m)
  && !estMandatEuropeen(m);
export const estVoteEuropeen = (v) => v?.scrutin_non_resolu?.institution === PE;
export const estAmendementEuropeen = (a) => a?.amendement_non_resolu?.institution === PE;
export const estTexteEuropeen = (t) => t?.institution === PE;
export const estParoleEuropeenne = (i) => i?.source?.institution === PE;

/* ── Construction ───────────────────────────────────────────────────────── */

const sujetIntervention = (i) =>
  i?.dossier?.point_ordre_du_jour || i?.theme_officiel || i?.sujet || null;

/** Une couche = une population sur une piste. */
const couche = (pop, titre, entrees, dateDe) => ({
  pop,
  titre,
  total: entrees.length,
  etendue: etendue(entrees.map(dateDe)),
});

/** Un champ = une ligne dépliée, quelles que soient les fiches qui le portent.
 *  Les couches d'un même champ vivent dans le MÊME rail : dédoubler la piste
 *  par origine mettrait deux lignes là où une suffit. */
const champ = (titre, apports) => ({
  titre,
  n: apports.reduce((s, a) => s + a.n, 0),
  total: apports.reduce((s, a) => s + a.total, 0),
  couches: apports,
});

const apport = (pop, origine, entrees, predicat, dateDe) => {
  const retenues = entrees.filter(predicat);
  return {
    pop,
    origine,
    n: retenues.length,
    total: entrees.length,
    etendue: etendue(retenues.map(dateDe)),
  };
};

export function construireCouverture({ repoRoot, slugsPublies = null }) {
  const profilesDir = path.join(repoRoot, 'pivot_data', 'profiles');
  const groupesDir = path.join(repoRoot, 'pivot_data', 'groupes');
  const gouvernementsDir = path.join(repoRoot, 'pivot_data', 'gouvernements');

  // --- index partagés -----------------------------------------------------
  /* `scrutins.json` porte une LISTE, pas un dictionnaire : l'indexer par
   * `scrutin_id` comme s'il était déjà une table rendait tous les votes vides
   * sans lever la moindre erreur. */
  const scrutinsPath = path.join(repoRoot, 'pivot_data', 'scrutins.json');
  const scrutins = new Map(
    (existsSync(scrutinsPath) ? lire(scrutinsPath).scrutins || [] : []).map((s) => [s.id, s]),
  );
  /* `scrutins_dossiers.scrutins` associe un scrutin à un `dossier_id` — une
   * CHAÎNE, pas un objet portant le dossier (#758). */
  const scrutinsDossiersPath = path.join(repoRoot, 'pivot_data', 'scrutins_dossiers.json');
  const scrutinsDossiers = existsSync(scrutinsDossiersPath)
    ? lire(scrutinsDossiersPath).scrutins || {}
    : {};
  const dossierDuScrutin = (s) => scrutinsDossiers[s?.id] || null;
  const commissionsPath = path.join(repoRoot, 'pivot_data', 'commissions_dossiers.json');
  const commissions = existsSync(commissionsPath) ? lire(commissionsPath).commissions || {} : {};

  // --- les fiches ---------------------------------------------------------
  const candidats = [...profilsCandidats(profilesDir, slugsPublies)];
  const groupes = existsSync(groupesDir)
    ? readdirSync(groupesDir)
        .filter((f) => f.endsWith('.json') && !f.startsWith('comparaison-'))
        .map((f) => lire(path.join(groupesDir, f)))
    : [];
  const gouvernements = existsSync(gouvernementsDir)
    ? readdirSync(gouvernementsDir).filter((f) => f.endsWith('.json'))
        .map((f) => lire(path.join(gouvernementsDir, f)))
    : [];

  // --- les entrées, à plat ------------------------------------------------
  const mandats = candidats.flatMap((d) => d.mandats || []);
  const mandatsAN = mandats.filter(estMandatAssemblee);
  const mandatsGouv = mandats.filter(estMandatGouvernemental);
  const mandatsPE = mandats.filter(estMandatEuropeen);
  const mandatsSenat = mandats.filter(estMandatSenatorial);
  const textes = candidats.flatMap((d) => d.textes_portes || []);
  const textesMinistre = textes.filter(estTexteMinisteriel);
  const textesPE = textes.filter(estTexteEuropeen);
  const textesParlement = textes.filter((t) => !estTexteMinisteriel(t) && !estTexteEuropeen(t));
  const paroles = candidats.flatMap((d) => d.interventions || []);
  const parolesGouv = paroles.filter(estParoleMinisterielle);
  const parolesPE = paroles.filter(estParoleEuropeenne);
  const parolesAN = paroles.filter((i) => !estParoleMinisterielle(i) && !estParoleEuropeenne(i));
  // Un vote ou un amendement européen porte ses champs sous son `*_non_resolu`
  // (§5) : c'est ce bloc qui est lu, pas un identifiant qu'il n'a pas.
  const votesPE = candidats.flatMap((d) => d.votes || []).filter(estVoteEuropeen)
    .map((v) => v.scrutin_non_resolu);
  const amendementsPE = candidats.flatMap((d) => d.amendements || []).filter(estAmendementEuropeen)
    .map((a) => a.amendement_non_resolu);

  // Un vote pivot ne porte que { scrutin_id, position } : sa date vit dans
  // l'index partagé (#432). Le scrutin est joint, jamais deviné.
  const votes = candidats
    .flatMap((d) => (d.votes || []).map((v) => scrutins.get(v.scrutin_id) || null))
    .filter(Boolean);

  const membresGroupes = groupes.flatMap((g) => g.membres || []);
  const cohesion = groupes.flatMap((g) =>
    (g.cohesion_votes || []).map((c) => ({ ...c, scrutin: scrutins.get(c.scrutin_id) || null })),
  );
  const membresGouv = gouvernements.flatMap((g) => g.membres || []);
  const textesGouv = gouvernements.flatMap((g) => g.textes || []);

  // --- amendements : la date vit dans l'index par législature (#431) -------
  const amendements = lireAmendements(repoRoot, candidats);

  const bornes = bornesPubliees(candidats);
  const finsPE = finsEuropeennes(candidats);

  const dMandat = (m) => iso(m.debut);
  const dVote = (s) => iso(s.date);
  const dCohesion = (c) => iso(c.scrutin?.date);
  const dAmdt = (a) => iso(a.date);
  const dTexte = (t) => iso(t.date_min);
  const dTexteGouv = (t) => iso(t.date_depot);
  const dParole = (i) => iso(i.date);
  const dMembreGroupe = (m) => iso(m.debut_dans_groupe);
  const dMembreGouv = (m) => iso(m.debut);

  const CAND = 'Fiches de candidats';
  const GOUV = 'Fiches de gouvernement';
  const GRP = 'Fiches de groupe';

  const hierarchie = [
    {
      cle: 'AN',
      titre: 'Assemblée nationale',
      pistes: [
        {
          cle: 'mandats',
          titre: 'Mandats et appartenances',
          couches: [
            couche('cand', CAND, mandatsAN, dMandat),
            couche('grp', GRP, membresGroupes, dMembreGroupe),
          ],
          champs: [
            champ('avec une date de début ou d’entrée', [
              apport('cand', CAND, mandatsAN, (m) => iso(m.debut), dMandat),
              apport('grp', GRP, membresGroupes, (m) => iso(m.debut_dans_groupe), dMembreGroupe),
            ]),
            champ('avec un lien vers la source', [
              apport('cand', CAND, mandatsAN, (m) => m.source_url, dMandat),
            ]),
            champ('avec une date de fin ou de sortie', [
              apport('grp', GRP, membresGroupes, (m) => iso(m.fin_dans_groupe), dMembreGroupe),
            ]),
            // Propre à l'Assemblée : après les champs communs aux institutions.
            champ('appartenances de groupe avec le banc déclaré', [
              apport(
                'cand',
                CAND,
                mandatsAN.filter((m) => m.categorie === 'groupe_politique'),
                (m) => m.position_dans_hemicycle,
                dMandat,
              ),
            ]),
          ],
        },
        {
          cle: 'votes',
          titre: 'Votes et scrutins',
          couches: [
            couche('cand', CAND, votes, dVote),
            couche('grp', GRP, cohesion, dCohesion),
          ],
          champs: [
            champ('avec une date de scrutin', [
              apport('cand', CAND, votes, (s) => iso(s.date), dVote),
              apport('grp', GRP, cohesion, (c) => iso(c.scrutin?.date), dCohesion),
            ]),
            champ('rattachés à leur texte ou dossier', [
              apport('cand', CAND, votes, dossierDuScrutin, dVote),
            ]),
            champ('avec un lien vers la source', [
              apport('cand', CAND, votes, (s) => s.source_url, dVote),
              apport('grp', GRP, cohesion, (c) => c.scrutin?.source_url, dCohesion),
            ]),
            // Propres à l'Assemblée : après les champs communs aux institutions.
            champ('avec la commission saisie au fond', [
              apport(
                'cand',
                CAND,
                votes,
                (s) => commissions[dossierDuScrutin(s)],
                dVote,
              ),
            ]),
            champ('avec une position majoritaire établie', [
              apport('grp', GRP, cohesion, (c) => c.position_majoritaire, dCohesion),
            ]),
          ],
        },
        {
          cle: 'amendements',
          titre: 'Amendements',
          couches: [couche('cand', CAND, amendements, dAmdt)],
          champs: [
            champ('avec une date de dépôt', [
              apport('cand', CAND, amendements, (a) => iso(a.date), dAmdt),
            ]),
            champ('rattachés à leur texte ou dossier', [
              apport('cand', CAND, amendements, (a) => a.dossier_id, dAmdt),
            ]),
            champ('avec un sort publié', [
              apport('cand', CAND, amendements, (a) => a.sort, dAmdt),
            ]),
            champ('avec un lien vers la source', [
              apport('cand', CAND, amendements, (a) => a.source_url, dAmdt),
            ]),
          ],
        },
        {
          cle: 'textes_portes',
          titre: 'Textes portés',
          couches: [couche('cand', CAND, textesParlement, dTexte)],
          champs: [
            champ('rattachés à leur texte ou dossier', [
              apport('cand', CAND, textesParlement, (t) => t.dossier_id, dTexte),
            ]),
            champ('avec leur stade de procédure', [
              apport('cand', CAND, textesParlement, (t) => t.stade_procedural, dTexte),
            ]),
            champ('avec un sort ou un statut publié', [
              apport('cand', CAND, textesParlement, (t) => t.sort, dTexte),
            ]),
            champ('avec un lien vers la source', [
              apport('cand', CAND, textesParlement, (t) => t.source_url, dTexte),
            ]),
          ],
        },
        {
          cle: 'interventions',
          titre: 'Interventions',
          couches: [couche('cand', CAND, parolesAN, dParole)],
          champs: champsInterventions(parolesAN, dParole, CAND),
        },
      ],
    },
    {
      cle: 'gouvernement',
      titre: 'Gouvernement',
      pistes: [
        {
          cle: 'mandats',
          titre: 'Fonctions gouvernementales',
          /* AUCUNE BORNE DÉCLARÉE (#859). La borne des mandats — le 19/06/2002
           * de l'AMO30 — était reprise ici par sa clé de liste, alors que la
           * plus ancienne fonction gouvernementale du corpus date du
           * 18/05/2007 et que les gouvernements 2002-2007 manquent : la hachure
           * affirmait « la source ne publie pas avant 2002 » sur un fait qui
           * n'est pas établi. Rien n'est hachuré tant que la borne n'est pas
           * déclarée. */
          borne: null,
          couches: [
            couche('cand', CAND, mandatsGouv, dMandat),
            couche('gouv', GOUV, membresGouv, dMembreGouv),
          ],
          champs: [
            champ('avec une date de début ou d’entrée', [
              apport('cand', CAND, mandatsGouv, (m) => iso(m.debut), dMandat),
              apport('gouv', GOUV, membresGouv, (m) => iso(m.debut), dMembreGouv),
            ]),
            champ('avec un lien vers la source', [
              apport('cand', CAND, mandatsGouv, (m) => m.source_url, dMandat),
              apport('gouv', GOUV, membresGouv, (m) => m.source_url, dMembreGouv),
            ]),
            champ('avec un portefeuille nommé', [
              apport('gouv', GOUV, membresGouv, (m) => m.portefeuille, dMembreGouv),
            ]),
            champ('avec une date de fin ou de sortie', [
              apport('cand', CAND, mandatsGouv, (m) => iso(m.fin), dMandat),
              apport('gouv', GOUV, membresGouv, (m) => iso(m.fin), dMembreGouv),
            ]),
          ],
        },
        {
          cle: 'textes_portes',
          titre: 'Textes portés comme ministre',
          couches: [
            couche('cand', CAND, textesMinistre, dTexte),
            couche('gouv', GOUV, textesGouv, dTexteGouv),
          ],
          champs: [
            champ('rattachés à leur texte ou dossier', [
              apport('cand', CAND, textesMinistre, (t) => t.dossier_id, dTexte),
              apport('gouv', GOUV, textesGouv, (t) => t.dossier_id, dTexteGouv),
            ]),
            champ('avec leur stade de procédure', [
              apport('cand', CAND, textesMinistre, (t) => t.stade_procedural, dTexte),
            ]),
            champ('avec un sort ou un statut publié', [
              apport('cand', CAND, textesMinistre, (t) => t.sort, dTexte),
              apport('gouv', GOUV, textesGouv, (t) => t.statut, dTexteGouv),
            ]),
            champ('avec un lien vers la source', [
              apport('cand', CAND, textesMinistre, (t) => t.source_url, dTexte),
            ]),
            champ('déposés à l’Assemblée', [
              apport('gouv', GOUV, textesGouv, (t) => t.chambre_depot_initial === 'AN', dTexteGouv),
            ]),
          ],
        },
        {
          cle: 'interventions',
          titre: 'Interventions comme membre du gouvernement',
          couches: [couche('cand', CAND, parolesGouv, dParole)],
          /* « avec la qualité de l'orateur » vaudrait 100 % ici : c'est la
           * DÉFINITION du sous-ensemble, pas une mesure. */
          champs: champsInterventions(parolesGouv, dParole, CAND).filter(
            (c) => c.titre !== 'avec la qualité de l’orateur',
          ),
        },
      ],
    },
    /* LES MÊMES SOUS-PARTIES QUE L'ASSEMBLÉE, ET LES MÊMES CHAMPS quand la
     * donnée a la même nature. Un champ propre à l'Assemblée — la commission
     * saisie au fond, le banc déclaré — n'a pas d'équivalent ici et n'est pas
     * rendu. Un champ commun que la source ne remplit pas l'est, à zéro : « 0
     * sur 383 » dit que le sort d'un texte européen n'est pas publié.
     *
     * LES `portee` EUROPÉENNES NE SONT PAS DES BORNES : elles vont de la
     * première à la dernière donnée de chaque personne. Les faire passer pour
     * telles dessinait sur l'Assemblée une hachure qui s'arrêtait en 2004. La
     * borne basse vient des dumps (`BORNES_BASSES_PE`), la haute de la
     * dernière parution que le pipeline déclare (`finsEuropeennes`). */
    {
      cle: 'PE',
      titre: 'Parlement européen',
      pistes: [
        {
          cle: 'mandats',
          titre: 'Mandats et appartenances',
          borne: null,
          couches: [couche('cand', CAND, mandatsPE, dMandat)],
          champs: [
            champ('avec une date de début ou d’entrée', [
              apport('cand', CAND, mandatsPE, (m) => iso(m.debut), dMandat),
            ]),
            champ('avec un lien vers la source', [
              apport('cand', CAND, mandatsPE, (m) => m.source_url, dMandat),
            ]),
            champ('avec une date de fin ou de sortie', [
              apport('cand', CAND, mandatsPE, (m) => iso(m.fin), dMandat),
            ]),
          ],
        },
        {
          cle: 'votes',
          titre: 'Votes et scrutins',
          borne: BORNES_BASSES_PE.votes,
          finSource: finsPE.votes ?? null,
          couches: [couche('cand', CAND, votesPE, dVote)],
          champs: [
            champ('avec une date de scrutin', [
              apport('cand', CAND, votesPE, (s) => iso(s.date), dVote),
            ]),
            champ('rattachés à leur texte ou dossier', [
              apport('cand', CAND, votesPE, (s) => s.reference_dossier, dVote),
            ]),
            champ('avec un lien vers la source', [
              apport('cand', CAND, votesPE, (s) => s.source_url, dVote),
            ]),
          ],
        },
        {
          cle: 'amendements',
          titre: 'Amendements',
          borne: BORNES_BASSES_PE.amendements,
          finSource: finsPE.amendements ?? null,
          couches: [couche('cand', CAND, amendementsPE, dAmdt)],
          champs: [
            champ('avec une date de dépôt', [
              apport('cand', CAND, amendementsPE, (a) => iso(a.date), dAmdt),
            ]),
            champ('rattachés à leur texte ou dossier', [
              apport('cand', CAND, amendementsPE, (a) => a.texte_vise, dAmdt),
            ]),
            champ('avec un sort publié', [
              apport('cand', CAND, amendementsPE, (a) => a.sort, dAmdt),
            ]),
            champ('avec un lien vers la source', [
              apport('cand', CAND, amendementsPE, (a) => a.source_url, dAmdt),
            ]),
          ],
        },
        {
          cle: 'textes_portes',
          titre: 'Textes portés',
          borne: null,
          finSource: finsPE.textes_portes ?? null,
          couches: [couche('cand', CAND, textesPE, dTexte)],
          champs: [
            champ('rattachés à leur texte ou dossier', [
              apport('cand', CAND, textesPE, (t) => t.dossier_id, dTexte),
            ]),
            champ('avec leur stade de procédure', [
              apport('cand', CAND, textesPE, (t) => t.stade_procedural, dTexte),
            ]),
            champ('avec un sort ou un statut publié', [
              apport('cand', CAND, textesPE, (t) => t.sort, dTexte),
            ]),
            champ('avec un lien vers la source', [
              apport('cand', CAND, textesPE, (t) => t.source_url, dTexte),
            ]),
          ],
        },
        {
          cle: 'interventions',
          titre: 'Interventions',
          borne: null,
          finSource: finsPE.interventions ?? null,
          couches: [couche('cand', CAND, parolesPE, dParole)],
          champs: champsInterventions(parolesPE, dParole, CAND),
        },
      ],
    },
    /* LE SÉNAT EST UNE INSTITUTION, pas une ligne à part (#885, 15/09/2026).
     *
     * Il portait un rail unique en JAUNE — « données non collectées » —, et
     * c'était vrai tant que #528 le tenait hors périmètre : le trou était de
     * notre côté. Depuis #885 les appartenances sont collectées, et les quatre
     * autres listes ne sont pas absentes par notre fait : `src/senat_opendata.py`
     * lit 24 des 93 tables du dump, et AUCUNE ne porte de scrutin, de compte
     * rendu, d'amendement ni de texte. Les trois tables refusées à l'entrée
     * sont de la présence et des procurations (§2 règle 3) — elles ne
     * nourrissent aucune de nos cinq listes, donc leur refus ne creuse rien ici.
     *
     * Les quatre listes sortent donc en `nonPublie`, la hachure : un fait sur la
     * source. Le jaune aurait dit « nous ne l'avons pas fait », et ce serait un
     * fait faux sur nous. */
    {
      cle: 'Senat',
      titre: 'Sénat',
      pistes: [
        {
          cle: 'mandats',
          titre: 'Mandats et appartenances',
          borne: null,
          couches: [couche('cand', CAND, mandatsSenat, dMandat)],
          champs: [
            champ('avec une date de début ou d’entrée', [
              apport('cand', CAND, mandatsSenat, (m) => iso(m.debut), dMandat),
            ]),
            champ('avec un lien vers la source', [
              apport('cand', CAND, mandatsSenat, (m) => m.source_url, dMandat),
            ]),
            champ('avec une date de fin ou de sortie', [
              apport('cand', CAND, mandatsSenat, (m) => iso(m.fin), dMandat),
            ]),
          ],
        },
        ...['votes', 'amendements', 'textes_portes', 'interventions'].map((cle) => ({
          cle,
          titre: TITRE_LISTE[cle],
          borne: null,
          nonPublie: 'aucune des 93 tables de l’export sénatorial ne porte cette liste',
          couches: [],
          champs: [],
        })),
      ],
    },
  ];

  return {
    collecteLe: collecteLe(candidats),
    bornes,
    hierarchie,
    accueil: accueil(hierarchie, bornes, candidats),
    institutions: institutions(candidats),
    couvertureFiches: couvertureFiches(candidats, bornes),
    reperes: reperes({ candidats, groupes, gouvernements }),
  };
}

function champsInterventions(lot, dateDe, origine) {
  return [
    champ('avec une date exploitable', [apport('cand', origine, lot, (i) => iso(i.date), dateDe)]),
    champ('avec l’intitulé de l’ordre du jour', [
      apport('cand', origine, lot, sujetIntervention, dateDe),
    ]),
    champ('avec le verbatim du compte rendu', [
      apport('cand', origine, lot, (i) => i.texte, dateDe),
    ]),
    champ('avec la qualité de l’orateur', [
      apport('cand', origine, lot, (i) => i.fonction, dateDe),
    ]),
    champ('hors collecte réduite au thème', [
      apport('cand', origine, lot, (i) => i.collecte !== 'theme_seul', dateDe),
    ]),
  ];
}

/* L'INDEX DES AMENDEMENTS EST LU LÉGISLATURE PAR LÉGISLATURE, et relâché entre
 * deux : les quatre fichiers pèsent 141 Mo, les charger ensemble ferait tomber
 * le build. Seules les métadonnées des amendements que le corpus signe sont
 * retenues — 172 241 sur les 1,4 million que l'index porte. */
function lireAmendements(repoRoot, candidats) {
  const dir = path.join(repoRoot, 'pivot_data', 'amendements');
  if (!existsSync(dir)) return [];
  const parLegislature = new Map();
  for (const d of candidats) {
    for (const a of d.amendements || []) {
      const m = /AMANR5L(\d+)/.exec(a.amendement_id || '');
      if (!m) continue;
      if (!parLegislature.has(m[1])) parLegislature.set(m[1], []);
      parLegislature.get(m[1]).push(a.amendement_id);
    }
  }
  const out = [];
  for (const [leg, ids] of parLegislature) {
    const fichier = path.join(dir, `${leg}.json`);
    if (!existsSync(fichier)) continue;
    const index = lire(fichier);
    const meta = index.amendements || {};
    const textes = index.textes || {};
    for (const id of ids) {
      const a = meta[id];
      if (!a) continue;
      out.push({
        date: a.date,
        sort: a.sort,
        source_url: a.source_url,
        dossier_id: textes[a.texte_vise]?.dossier_id ?? null,
      });
    }
  }
  return out;
}

/* LA BORNE EST CELLE QUE LA SOURCE DÉCLARE, pas la première donnée du corpus.
 *
 * Chaque profil porte son bloc `couverture` : par liste, l'état `couvert` et sa
 * `portee.debut`, avec la preuve qui l'établit. Prendre à la place le minimum
 * des dates rencontrées rendrait la borne tautologique — la hachure s'arrêterait
 * exactement là où la première donnée commence, et ne dirait plus rien.
 *
 * Les 32 fiches déclarent la même borne par liste ; le minimum est pris par
 * sûreté, et une divergence serait un fait à investiguer, pas à moyenner. */
function bornesPubliees(candidats) {
  const out = {};
  for (const d of candidats) {
    for (const [liste, etats] of Object.entries(d.couverture || {})) {
      for (const e of etats || []) {
        /* Une entrée européenne n'est pas une borne : sa `portee` va de la
         * première à la dernière donnée de la personne. La prendre pour une
         * borne de publication faisait commencer les votes de l'Assemblée au
         * 15/09/2004 — la première donnée européenne d'une fiche. */
        if (e.source === PE) continue;
        /* `couvert` et `fait_etabli` disent tous deux « publiée à partir
         * de » : les interventions portent le second, et ne retenir que le
         * premier laissait leur borne vide — donc aucune hachure, donc un
         * blanc qui se lit « rien fait » (§2 règle 5). */
        if (e.etat !== 'couvert' && e.etat !== 'fait_etabli') continue;
        const debut = iso(e.portee?.debut);
        if (debut && (!out[liste] || debut < out[liste])) out[liste] = debut;
      }
    }
  }
  return out;
}

/* CE QUE LA SOURCE EUROPÉENNE DÉCLARE, ET SEULEMENT CELA.
 *
 * `couverture_profil.bornes_europeennes` (#683) écrit, liste par liste, la
 * dernière date parue chez la source pour chaque fiche : « ce qui suit n'est
 * pas absent, il n'est pas encore paru chez elle ». Pour le corpus, c'est la
 * PLUS TARDIVE des fiches. Le début, lui, n'est pas une borne — la première
 * donnée d'une personne dit quand elle a commencé, pas depuis quand la source
 * publie — et rien n'est dessiné avant. */
function finsEuropeennes(candidats) {
  const out = {};
  for (const d of candidats) {
    for (const [liste, etats] of Object.entries(d.couverture || {})) {
      for (const e of etats || []) {
        if (e.source !== PE || e.etat !== 'couvert') continue;
        const fin = iso(e.portee?.fin);
        if (fin && (!out[liste] || fin > out[liste])) out[liste] = fin;
      }
    }
  }
  return out;
}

/* L'ACCUEIL NE DIT QU'UNE CHOSE PAR INSTITUTION : depuis quand elle est lue
 * (relecture du 11/09/2026 — « juste les bornes par institution, pour que
 * quelqu'un ne se demande pas pourquoi le mandat d'un tel n'est pas visible »).
 *
 * `debut` est la plus ancienne des dates qui ouvrent une liste : sa borne
 * déclarée, ou à défaut sa première donnée. `hachureJusqua` n'existe que si
 * TOUTES les listes de l'institution déclarent une borne : la hachure dit « la
 * source ne publie rien avant », et une seule liste sans borne suffit à ne plus
 * pouvoir l'affirmer pour l'institution entière (le Gouvernement, #859 ; les
 * mandats européens). */
function accueil(hierarchie, bornes, candidats) {
  const plusTot = (a, b) => (!a ? b : !b ? a : a < b ? a : b);
  const institutions = hierarchie.map((inst) => {
    let debut = null;
    let hachure = null;
    let toutesBornees = true;
    for (const p of inst.pistes) {
      const premiere = p.couches.reduce((m, c) => plusTot(m, c.etendue?.[0] ?? null), null);
      const borne = 'borne' in p ? p.borne : bornes[p.cle];
      const fin = borne ? plusTot(borne, premiere) : null;
      if (!fin) toutesBornees = false;
      hachure = plusTot(hachure, fin);
      debut = plusTot(debut, fin ?? premiere);
    }
    return { cle: inst.cle, titre: inst.titre, debut, hachureJusqua: toutesBornees ? hachure : null };
  });

  /* LES FICHES HORS COUVERTURE, NOMMÉES — calculées sur les fiches publiées,
   * jamais écrites à la main : une liste recopiée n'accueille pas le prochain
   * candidat déclaré.
   *
   * « MANDAT ANTÉRIEUR À LA PUBLICATION DES DONNÉES DE L'ASSEMBLÉE NATIONALE »
   * se lit dans `mandats_anterieurs`, la table relue sur Sycomore et le Journal
   * officiel que le pipeline porte sur chaque fiche (#860). Le corpus seul ne la
   * déduisait pas : la règle « premier mandat lu le 19/06/2002 » se trompait sur
   * 3 des 5 cas (11/09/2026). Une fiche « non relue » (`null`) n'y figure pas :
   * absent n'est pas « aucun ». */
  const personne = (d) => ({ id: d.id, nom: d.nom });
  // Rangés par nom de famille — le dernier mot du nom publié.
  const famille = (nom) => nom.split(' ').pop();
  const parNom = (a, b) => famille(a.nom).localeCompare(famille(b.nom), 'fr') || a.nom.localeCompare(b.nom, 'fr');
  const senat = candidats
    .filter((d) => (d.mandats || []).some((m) => m.chambre === 'Senat'))
    .map(personne)
    .sort(parNom);
  const sansMandat = candidats
    .filter((d) => !(d.mandats || []).length)
    .map(personne)
    .sort(parNom);
  const anterieurs = candidats
    .filter((d) => Array.isArray(d.mandats_anterieurs) && d.mandats_anterieurs.length > 0)
    .map(personne)
    .sort(parNom);
  return { institutions, horsCouverture: { anterieurs, senat, sansMandat } };
}

/** La date de collecte la plus récente parmi les fiches publiées. */
function collecteLe(candidats) {
  const dates = candidats
    .map((d) => iso(d.meta?.derniere_collecte || d.meta?.genere_le))
    .filter(Boolean)
    .sort();
  return dates.length ? dates[dates.length - 1] : null;
}

/* OÙ NOS CANDIDATS ONT SIÉGÉ.
 *
 * LES MANDATS LOCAUX Y ENTRENT (#922, compté ici le 16/09/2026). Le Répertoire
 * national des élus les verse dans `mandats[]` avec `categorie: "mandat_local"`
 * et sans chambre ; la frise disait « aucune source » alors que les fiches
 * publiées en portaient 34, sur 14 candidats (mesuré le 16/09/2026). Leur BORNE voyage avec la donnée, dans
 * `mandats_locaux_couverture.borne_couverture` (une année) : avant elle, la
 * source ne publie rien, et la frise le hachure. */
function institutions(candidats) {
  const acc = new Map();
  const ajoute = (cle, slug, m) => {
    if (!acc.has(cle)) acc.set(cle, { cle, candidats: new Set(), mandats: 0, debut: null, fin: null });
    const e = acc.get(cle);
    e.candidats.add(slug);
    e.mandats += 1;
    const d = iso(m.debut);
    if (d && (!e.debut || d < e.debut)) e.debut = d;
    const f = iso(m.fin);
    if (f && (!e.fin || f > e.fin)) e.fin = f;
  };
  let borneLocale = null;
  for (const d of candidats) {
    const annee = d.mandats_locaux_couverture?.borne_couverture;
    if (annee && (!borneLocale || `${annee}-01-01` < borneLocale)) borneLocale = `${annee}-01-01`;
    for (const m of d.mandats || []) {
      if (m.categorie === 'mandat_local') ajoute('local', d.id, m);
      else if (estMandatGouvernemental(m)) ajoute('gouvernement', d.id, m);
      else if (m.chambre && m.chambre !== 'AN') ajoute(m.chambre, d.id, m);
      else if (m.categorie === 'mandat_electif') ajoute('AN', d.id, m);
    }
  }
  return [...acc.values()].map((e) => ({
    ...e,
    candidats: e.candidats.size,
    ...(e.cle === 'local' ? { borne: borneLocale } : {}),
  }));
}

/* CE QUI MANQUE, ET SUR QUELLES FICHES.
 *
 * Le dénominateur n'est pas le nombre de fiches : une fiche sans mandat à
 * l'Assemblée n'a pas de vote à porter, et sa liste vide est un fait sur elle,
 * pas un trou. Rapporté aux seules fiches qui y ont siégé, un manquant se
 * nomme — et se sépare en deux : celui dont tout le mandat précède la borne de
 * publication n'est pas un trou, l'autre si (§2 règle 5). */
function couvertureFiches(candidats, bornes) {
  const aSiege = (d) => (d.mandats || []).some((m) => estMandatAssemblee(m) && m.categorie === 'mandat_electif');
  const siegeants = candidats.filter(aSiege);
  const finMandatAN = (d) =>
    (d.mandats || [])
      .filter((m) => estMandatAssemblee(m) && m.categorie === 'mandat_electif')
      .map((m) => iso(m.fin) || '9999-99-99')
      .sort()
      .pop();
  /* Rapporté aux fiches qui ont SIÉGÉ À L'ASSEMBLÉE, un manquant ne se
   * comble pas par des entrées européennes : une fiche dont les seuls votes
   * sont européens n'en porte aucun de l'Assemblée. */
  const LISTES = [
    ['votes', 'Votes', (d) => (d.votes || []).filter((v) => !estVoteEuropeen(v)).length],
    ['amendements', 'Amendements', (d) => (d.amendements || []).filter((a) => !estAmendementEuropeen(a)).length],
    ['textes_portes', 'Textes portés', (d) => (d.textes_portes || []).filter((t) => !estTexteEuropeen(t)).length],
    ['interventions', 'Interventions', (d) => (d.interventions || []).filter((i) => !estParoleEuropeenne(i)).length],
  ];
  return {
    fiches: candidats.length,
    siege: siegeants.length,
    listes: LISTES.map(([cle, titre, compte]) => {
      const vides = siegeants.filter((d) => compte(d) === 0);
      const borne = bornes[cle];
      const horsBorne = vides.filter((d) => borne && finMandatAN(d) < borne);
      const trous = vides.filter((d) => !(borne && finMandatAN(d) < borne));
      return {
        cle,
        titre,
        borne,
        porte: siegeants.length - vides.length,
        horsBorne: horsBorne.map((d) => d.nom),
        trous: trous.map((d) => d.nom),
      };
    }),
  };
}

/* LES CHIFFRES DE TÊTE. Mesurés, jamais écrits dans le JSX : un repère recopié
 * à la main est un repère qui aura vieilli au run suivant. */
function reperes({ candidats, groupes, gouvernements }) {
  return {
    fichesPubliees: candidats.length + groupes.length + gouvernements.length,
    candidats: candidats.length,
    groupes: groupes.length,
    gouvernements: gouvernements.length,
  };
}
