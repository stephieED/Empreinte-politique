/* ── Ce qui a été dit : extraits de parole et lien vers la séance (#1029) ────
 *
 * Backend publie, pour la parole des membres de roster et de gouvernement, un
 * EXTRAIT du verbatim — 280 caractères au plus, `texte_tronque` quand il
 * continue (#1086) — et, sur chaque entrée Syceron, `id_syceron`, l'ancre de la
 * prise de parole sur la page de séance de l'AN (#1087). Ce module est la seule
 * règle que le build et le navigateur partagent pour les lire.
 *
 * POURQUOI UN VOCABULAIRE ET DES PAQUETS, ET PAS LES EXTRAITS DANS LA FICHE.
 * Mesuré le 22/09/2026 sur le pivot : ~146 000 interventions à thème par an
 * pour les membres de roster de groupe. Les extraits d'un seul maillon (RN,
 * XVIIe) pèseraient ~20 Mo : trop pour une page. Le build écrit donc, par
 * fiche :
 *  - un INDEX : pour chaque débat, le vocabulaire de ses extraits — tous, ceux
 *    des 12 et des 6 derniers mois —, que le filtre par mot interroge ;
 *  - des PAQUETS : les extraits eux-mêmes, répartis par débat, dont un seul se
 *    charge quand un débat s'ouvre.
 *
 * LIMITE, À DIRE : le filtre ne voit que les 280 premiers caractères. Un mot
 * prononcé plus loin dans l'intervention lui échappe ; le lien mène au texte
 * entier, chez l'Assemblée.
 */
import { contientLesMots, normaliserIntitule } from './filtreIntitule.js';
import { dansLaFenetre } from './filtrePeriode.js';

export const EXTRAIT_CARACTERES = 280;
export const NB_PAQUETS = 16;

const ID_SYCERON = /^syceron_(CRSANR5L(\d+)S\w+?)_\d+$/;

/** Le lien vers la prise de parole sur la page de séance de l'AN (#1087).
 *  Même règle que `schema_pivot.url_seance_an` : l'uid du compte rendu est le
 *  préfixe de `intervention_id`, l'ancre est `id_syceron`. Sans ancre, la
 *  séance seule ; hors Syceron, `null`. */
/* ── UNE PRISE DE PAROLE SE CITE, ET SE CITE PAREIL PARTOUT ─────────────────
 *
 * Les guillemets français, avec leurs espaces fines insécables, et l'élision
 * qui dit qu'un extrait est COUPÉ. Trois fiches affichent du verbatim — le
 * candidat (`ParolesParPeriode`), la lignée et le gouvernement (tous deux par
 * `ExtraitsDuDebat`) — et elles ne le ponctuaient pas : rien ne séparait la
 * parole rapportée du texte de la fiche.
 *
 * La convention vit ICI et pas dans chaque composant : recopiée trois fois,
 * elle divergerait au premier ajustement. Demandé par la propriétaire le
 * 25/09/2026, « et ça devrait être le cas partout ».
 *
 * L'ÉLISION EST DANS LES GUILLEMETS, jamais après : un extrait de 280
 * caractères coupé au milieu d'une phrase ne doit pas se refermer comme s'il
 * était complet (§2 règle 5 — une troncature est un fait, pas un silence).
 *
 * ELLE S'ÉCRIT « […] » ET NON « … », arbitré sur maquette le 25/09/2026. Une
 * raison décide, et elle se voit : **le locuteur suspend lui-même sa phrase**
 * — 1 072 des 352 564 extraits tronqués finissent déjà sur des points de
 * suspension —, et « … » s'y colle sans que rien ne dise lequel est de lui.
 * Les crochets disent que la marque est de NOUS. Le reste suit : 73,7 % des
 * extraits tronqués finissent sur un point, où « articles. … » se lit comme
 * une coquille. C'est aussi la convention française de l'omission dans une
 * citation. */
export const CITATION_OUVRE = '\u00ab\u202f';
export const CITATION_FERME = '\u202f\u00bb';
export const CITATION_ELISION = '[\u2026]';

export function urlSeanceAn(intervention) {
  const m = ID_SYCERON.exec(String(intervention?.intervention_id ?? intervention?.id ?? ''));
  if (!m) return null;
  const url = `https://www.assemblee-nationale.fr/dyn/${m[2]}/comptes-rendus/seance/${m[1]}`;
  const ancre = intervention?.id_syceron;
  return ancre ? `${url}#${ancre}` : url;
}

const FIN_DE_PHRASE = /[.!?…](?=\s|$)/g;

/** `[extrait, tronqué]` d'un verbatim entier — la règle de
 *  `schema_pivot.extrait_de_texte`, pour les membres dont la parole est
 *  collectée en entier (un candidat déclaré devenu ministre) : tous les
 *  extraits d'une fiche se lisent alors à la même longueur. */
export function extraitDeTexte(texte, limite = EXTRAIT_CARACTERES) {
  if (typeof texte !== 'string' || !texte) return [null, false];
  if (texte.length <= limite) return [texte, false];
  const fenetre = texte.slice(0, limite);
  const fins = [...fenetre.matchAll(FIN_DE_PHRASE)].map((m) => m.index + m[0].length);
  if (fins.length && fins.at(-1) >= Math.floor(limite / 2)) return [fenetre.slice(0, fins.at(-1)), true];
  const blanc = fenetre.trimEnd().lastIndexOf(' ');
  const coupe = blanc > 0 ? fenetre.slice(0, blanc) : fenetre;
  return [coupe.trimEnd(), true];
}

/** L'extrait d'une entrée d'intervention, quelle que soit sa collecte :
 *  `extrait` tel que Backend l'a coupé, texte entier coupé ici, `theme_seul`
 *  sans texte. */
export function extraitDeLIntervention(i) {
  if (i?.collecte === 'extrait') return [i.texte ?? null, i.texte_tronque === true];
  if (i?.collecte) return [null, false];
  return extraitDeTexte(i?.texte);
}

/** Le paquet d'un débat : un hachage stable de son intitulé (FNV-1a). */
export function paquetDe(sujet, n = NB_PAQUETS) {
  let h = 0x811c9dc5;
  for (let k = 0; k < sujet.length; k += 1) {
    h ^= sujet.charCodeAt(k);
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return h % n;
}

const BORD = /^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu;

/** Les mots distincts de textes, normalisés comme le filtre, joints par une
 *  espace : `contientLesMots` s'y applique tel quel. */
export function vocabulaire(textes) {
  const mots = new Set();
  for (const t of textes) {
    if (!t) continue;
    for (const brut of normaliserIntitule(t).split(/\s+/)) {
      const mot = brut.replace(BORD, '');
      if (mot.length > 1) mots.add(mot);
    }
  }
  return [...mots].join(' ');
}

/**
 * L'index et les paquets d'une fiche.
 *
 * `entrees` : `[{ sujet, orateur, date, texte, tronque, id, ancre }]` — `orateur`
 * est ce que la page sait résoudre (un nom, ou un rang dans `personnes`).
 * `debuts` : `{ '12m': date, '6m': date }`, les débuts de fenêtre comptés depuis
 * la date des données, ou `null`.
 *
 * Rend `{ index: { [sujet]: [vocTout, voc12m, voc6m, paquet] }, paquets: [ { [sujet]: [entrée compacte] } ] }`.
 * Une entrée compacte : `[orateur, date, texte, tronqué (0/1), intervention_id, id_syceron]`,
 * de la plus récente à la plus ancienne.
 */
export function construireExtraits(entrees, debuts = null) {
  const parSujet = new Map();
  for (const e of entrees) {
    if (!e.sujet || !e.date) continue;
    const liste = parSujet.get(e.sujet) || [];
    liste.push(e);
    parSujet.set(e.sujet, liste);
  }
  const index = {};
  const paquets = Array.from({ length: NB_PAQUETS }, () => ({}));
  for (const [sujet, liste] of parSujet) {
    liste.sort((a, b) => b.date.localeCompare(a.date) || String(a.id).localeCompare(String(b.id)));
    const dans = (debut) => (debut ? liste.filter((e) => dansLaFenetre(e.date, debut)) : []);
    const k = paquetDe(sujet);
    index[sujet] = [
      vocabulaire(liste.map((e) => e.texte)),
      vocabulaire(dans(debuts?.['12m']).map((e) => e.texte)),
      vocabulaire(dans(debuts?.['6m']).map((e) => e.texte)),
      k,
    ];
    paquets[k][sujet] = liste.map((e) => [e.orateur, e.date, e.texte ?? null, e.tronque ? 1 : 0, e.id ?? null, e.ancre ?? null]);
  }
  return { index, paquets };
}

/** Vrai si les extraits du débat portent chacun des mots, dans la période.
 *  Sans index pour ce débat : faux — on ne suppose pas (§2 règle 5). */
export function extraitsPortentLesMots(index, sujet, mots, periode = null) {
  const entree = index?.[sujet];
  if (!entree || !mots.length) return false;
  const voc = periode === '6m' ? entree[2] : periode === '12m' ? entree[1] : entree[0];
  return contientLesMots(voc, mots);
}

/** Les extraits d'un débat, lisibles : dans la fenêtre, et — sous un mot que
 *  l'intitulé ne porte pas — ceux-là seuls dont le texte le porte. */
export function extraitsDuDebat(compacts, { mots = [], debut = null, parIntitule = false } = {}) {
  return (compacts || [])
    .map(([orateur, date, texte, tronque, id, ancre]) => ({
      orateur,
      date,
      texte,
      tronque: tronque === 1,
      url: urlSeanceAn({ intervention_id: id, id_syceron: ancre }),
      id,
    }))
    .filter((e) => dansLaFenetre(e.date, debut))
    .filter((e) => parIntitule || !mots.length || contientLesMots(e.texte, mots));
}
