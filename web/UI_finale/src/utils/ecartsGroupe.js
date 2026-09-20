/* ── Ses divergences : sa position à côté de celle de son groupe (#328) ───────
 *
 * La section publiait la seule LISTE des scrutins où sa position diffère de la
 * position majoritaire de son groupe. Elle était juste, et elle était muette
 * pour dix des treize candidats déclarés : trois d'entre eux ont une base réelle
 * et zéro divergence, six n'ont aucune fiche de groupe publiée.
 *
 * Ce module ajoute ce qui manquait : la BANDE — un scrutin par colonne, dans
 * l'ordre du temps — qui donne à voir, sans compter, si la personne s'écarte et
 * dans quel groupe. Trois faits, trois éléments, jamais deux faits sur un même :
 *
 *   1. LE SOCLE, un filet coloré par scrutin — ce qu'a voté son groupe ;
 *   2. LA BARRE, en encre neutre — combien de ses membres n'ont pas suivi ;
 *   3. LE POINT, coloré et cerclé — les scrutins où elle-même diverge.
 *
 * CE QUE LA SECTION NE PUBLIERA JAMAIS, et c'est la contrainte qui a décidé de
 * la forme : le NOMBRE de divergences, son rapport aux scrutins comparables, ou
 * un taux de cohésion. `AGENTS.md` §2 règle 7 nomme cet exemple mot pour mot —
 * « a voté contre son groupe 47 fois » est l'indice individuel mesuré contre la
 * moyenne du groupe, par un autre chemin. Ce qui est publiable est la
 * JUXTAPOSITION, scrutin par scrutin, et la dispersion du GROUPE, qui est un
 * fait de groupe et porte son dénominateur.
 *
 * D'où deux choix qui ne sont pas cosmétiques : la bande fait lire d'abord ce
 * que fait le groupe, la divergence en second ; et le commutateur de candidats
 * de la maquette porte une pastille BINAIRE — « il s'écarte » ou non —, jamais
 * un compte.
 */
import { isWholeTextVote, titreDuTexteVote } from './lecture';

export const POSITIONS_COMPARABLES = ['pour', 'contre', 'abstention'];

/* ── Règle : un groupe est DIVISÉ dès que ses exprimés ne sont pas unanimes ──
 *
 * Aucun seuil, aucune pondération : un membre qui s'abstient quand 67 votent
 * pour suffit. Les absents et les non-votants sont hors du critère — ne pas
 * voter n'est pas voter autrement.
 *
 * C'est un fait de GROUPE, publié avec son dénominateur, et c'est lui qui donne
 * son sens à une divergence : se séparer d'un groupe uni et se ranger dans
 * l'une des deux moitiés d'un groupe partagé ne sont pas le même geste. Mesuré
 * au commit de données `a48e92e3` : le groupe de François Ruffin ne s'est divisé
 * sur AUCUN de ses 56 scrutins comparables, celui de Gabriel Attal sur 47 de
 * ses 108 — et ni l'un ni l'autre n'a jamais divergé.
 */
export function groupeDivise(entree) {
  return [entree.pour, entree.contre, entree.abstention].filter((n) => n > 0).length > 1;
}

/* La hauteur de la barre : les membres qui n'ont pas suivi leur majorité,
 * rapportés à l'effectif éligible pour que deux législatures se comparent
 * (31 membres au groupe SOC de la XVIe, 68 à celui de la XVIIe). */
export function partDissidente(entree) {
  const exprimes = entree.pour + entree.contre + entree.abstention;
  if (!exprimes) return 0;
  const majoritaires = Math.max(entree.pour, entree.contre, entree.abstention);
  return (exprimes - majoritaires) / (entree.membresEligibles || exprimes);
}

/* ── Ce qui est comparable, et rien de plus ─────────────────────────────────
 *
 * Un scrutin entre dans la bande quand QUATRE conditions sont réunies : la
 * personne y a une position, la fiche de son groupe aussi, la position
 * majoritaire du groupe est publiée, et le scrutin porte sur l'ensemble d'un
 * texte. Cette dernière restriction n'est pas un détail de collecte : sur un
 * article ou un amendement, la position majoritaire d'un groupe se déplace d'un
 * vote à l'autre pour des raisons de négociation que le corpus ne porte pas.
 *
 * `communs` compte les scrutins communs TOUTES NATURES CONFONDUES, et il n'est
 * plus affiché : rapproché des divergences, il servait de dénominateur à une
 * division que le lecteur faisait tout seul — et avec le mauvais nombre, les
 * divergences ne portant que sur les votes sur l'ensemble. Il reste calculé
 * parce qu'il distingue deux vides : « aucune fiche ne recouvre ses votes » et
 * « des fiches les recouvrent, mais aucun vote sur l'ensemble ».
 *
 * `matiereDuScrutin` est PASSÉE par l'adaptateur, jamais reconstruite ici :
 * c'est la même jointure que « ce qu'il a voté » — scrutin → dossier (#758),
 * puis dossier → commission saisie au fond (#328). Elle rend `null` dès que le
 * rattachement manque, et l'affichage le DIT (§2 règle 5) : une puce absente se
 * lirait comme un texte sans commission, alors que c'est notre rattachement qui
 * manque.
 */
export function ecartsAvecLeGroupe(votesJoints, fichesGroupe, matiereDuScrutin = () => null) {
  const fiches = (fichesGroupe || []).filter(Boolean);
  if (!fiches.length) {
    return { fiches: [], communs: 0, bande: [], ecarts: [], divises: 0, comparable: false };
  }

  const parScrutin = new Map();
  for (const v of votesJoints || []) {
    if (v.scrutin_id) parScrutin.set(v.scrutin_id, v);
  }

  let communs = 0;
  const bande = [];
  for (const fiche of fiches) {
    for (const c of fiche.cohesion_votes || []) {
      const mien = parScrutin.get(c.scrutin_id);
      if (!mien) continue;
      communs += 1;
      if (!c.position_majoritaire) continue;
      if (!POSITIONS_COMPARABLES.includes(mien.position)) continue;
      if (!isWholeTextVote(mien.scrutin)) continue;
      bande.push({
        scrutinId: c.scrutin_id,
        // Le titre NETTOYÉ, comme dans « ce qu'il a voté » : la source écrit
        // « l'ensemble du projet de loi … (première lecture). », et publier ce
        // libellé-là ferait lire la mécanique du scrutin à la place du texte.
        // Le repli sur l'intitulé brut garde la source quand le nettoyage ne
        // rend rien — un titre approximatif vaut mieux qu'un titre absent.
        texte: titreDuTexteVote(mien.texte) || mien.texte || null,
        date: mien.date ?? null,
        sourceUrl: mien.scrutin?.source_url ?? null,
        sort: mien.scrutin?.sort ?? null,
        matiere: matiereDuScrutin(c.scrutin_id),
        position: mien.position,
        positionGroupe: c.position_majoritaire,
        ecart: mien.position !== c.position_majoritaire,
        groupe: fiche.groupe_sigle ?? null,
        legislature: fiche.legislature ?? null,
        pour: c.pour ?? 0,
        contre: c.contre ?? 0,
        abstention: c.abstention ?? 0,
        absents: (c.absents ?? 0) + (c.non_votant ?? 0),
        membresEligibles: c.membres_eligibles ?? 0,
        // `quorum_atteint` vaut `taux_participation >= 0,5` sur les membres
        // éligibles (`src/group_profile.py`). En dessous, la « position
        // majoritaire » repose sur une poignée de membres : §2 règle 7 refuse un
        // ratio sans couverture suffisante, et la fiche le DIT au lieu de taire
        // le scrutin — l'écarter reviendrait à choisir les faits qui arrangent.
        quorum: c.quorum_atteint !== false,
      });
    }
  }

  // La bande va dans le sens du temps : elle raconte une carrière.
  bande.sort((a, b) => String(a.date || '').localeCompare(String(b.date || '')));
  // La liste se lit par le haut, et le haut d'une liste de faits est ce qui
  // vient de se passer.
  const ecarts = bande.filter((x) => x.ecart).slice().reverse();

  return {
    fiches: fiches.map((f) => ({
      sigle: f.groupe_sigle,
      nom: f.groupe_nom,
      legislature: f.legislature,
      debut: f.periode?.debut ?? null,
      fin: f.periode?.fin ?? null,
    })),
    communs,
    bande,
    ecarts,
    divises: bande.filter(groupeDivise).length,
    comparable: communs > 0,
  };
}
