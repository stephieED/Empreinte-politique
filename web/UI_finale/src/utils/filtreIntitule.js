/* ── Le filtre par intitulé de la fiche candidat (#979) ─────────────────────
 *
 * UN MOT, ET LA FICHE SE RECALCULE SUR CE QUI LE PORTE. Le filtre ne masque
 * pas des lignes après coup : il retire du PROFIL PIVOT les textes, votes,
 * amendements et interventions dont l'intitulé ne contient pas le mot, puis la
 * fiche est reconstruite par les mêmes règles que sans filtre. Figures et
 * listes suivent donc ensemble — une liste filtrée sous une figure qui ne
 * l'est pas montrait deux choses différentes (maquette du 17/09/2026).
 *
 * CE QUI N'EST PAS FILTRÉ : `mandats`. Un mandat n'a pas d'intitulé au sens
 * du filtre ; les sections qui les lisent (« En bref », « Les fonctions
 * exercées », « Ce qu'on n'a pas pu lire ») sont RETIRÉES tant qu'un mot est
 * tapé, par le composant.
 *
 * SANS CASSE NI ACCENTS, ET SANS TRADUCTION. « energie » trouve « énergie » ;
 * « énergie » ne trouve pas « energy ». Les intitulés européens sont publiés
 * en anglais pour une partie d'entre eux, et la fiche le dit au lecteur quand
 * un mot ne trouve rien — elle ne traduit pas (§2 règle 2).
 *
 * PLUSIEURS MOTS : TOUS DOIVENT FIGURER, dans n'importe quel ordre.
 * « loi finances » trouve « Projet de loi de finances pour 2026 ».
 */

/** Minuscules, accents retirés, apostrophes typographiques ramenées à `'`. */
export function normaliserIntitule(texte) {
  return String(texte ?? '')
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[’‘ʼ]/g, "'")
    .toLowerCase();
}

/** Les mots d'une saisie, normalisés. Une saisie vide n'en a aucun. */
export function motsDuFiltre(saisie) {
  return normaliserIntitule(saisie).split(/\s+/).filter(Boolean);
}

/** Vrai si l'intitulé porte chacun des mots. Un intitulé absent n'en porte
 *  aucun : il ne passe pas un filtre actif (§2 règle 5 — on ne suppose pas). */
export function contientLesMots(intitule, mots) {
  if (!mots.length) return true;
  if (typeof intitule !== 'string' || !intitule) return false;
  const n = normaliserIntitule(intitule);
  return mots.every((m) => n.includes(m));
}

/**
 * Le profil pivot réduit à ce dont l'intitulé porte le mot.
 *
 * Les intitulés des votes et des amendements ne vivent pas dans le profil —
 * ils sont dans les index partagés (#431, #432). Le lecteur de chaque intitulé
 * est donc fourni par l'appelant, qui a ces index chargés :
 *
 * - `intituleDuVote(vote)` — celui que « Ce qu'il a voté » affiche ;
 * - `intituleDeLAmendement(amendement)` — celui du dossier amendé ;
 * - `intituleDeLIntervention(intervention)` — le chemin du point de séance.
 *
 * Rend le profil INCHANGÉ (même objet) quand la saisie ne porte aucun mot.
 */
export function filtrerProfil(pivot, saisie, { intituleDuVote, intituleDeLAmendement, intituleDeLIntervention }) {
  const mots = motsDuFiltre(saisie);
  if (!mots.length || !pivot) return pivot;
  const garde = (lire) => (x) => contientLesMots(lire(x), mots);
  return {
    ...pivot,
    textes_portes: (pivot.textes_portes || []).filter(garde((t) => t.titre)),
    votes: (pivot.votes || []).filter(garde(intituleDuVote)),
    amendements: (pivot.amendements || []).filter(garde(intituleDeLAmendement)),
    interventions: (pivot.interventions || []).filter(garde(intituleDeLIntervention)),
  };
}

/* ── Règle : SOUS UN MOT, LES PÉRIODES SE CUMULENT (#979) ───────────────────
 *
 * Hors filtre, « Ce qu'il a voté » refuse de cumuler les périodes : les
 * additionner reformerait le total de carrière que la vue par période existe
 * pour ne pas publier. Sous un mot du filtre de la fiche, la liste porte déjà
 * toutes les périodes, et une figure restée sur une seule ne montrait plus ce
 * que la liste dessous montre — arbitré le 17/09/2026 : la figure suit.
 *
 * Une seule période, `cumul: true`, bornée par la première et la dernière. Les
 * votes restent dans l'ordre des périodes. Aucune période : aucun cumul. */
export function periodeCumulee(periodes) {
  const liste = periodes || [];
  if (!liste.length) return null;
  const votes = liste.flatMap((p) => p.votes || []);
  return {
    cle: 'cumul',
    cumul: true,
    banc: null,
    gouvernementId: null,
    gouvernement: null,
    debut: liste[0].debut,
    fin: liste[liste.length - 1].fin,
    votes,
    groupes: [...new Set(liste.flatMap((p) => p.groupes || []))],
    sansRepere: false,
  };
}

/* ── Le mot surligné dans un verbatim (#979) ────────────────────────────────
 *
 * Une intervention retenue par son PROPOS peut porter un sujet sans rapport
 * avec le mot : sans le surligner, le lecteur ne voit pas pourquoi elle est là.
 * La comparaison est celle du filtre — sans casse ni accents —, mais le texte
 * rendu est celui du compte rendu, caractère pour caractère : on repère les
 * positions sur la forme normalisée et on découpe l'original. */
export function segmentsSurlignes(texte, saisie) {
  const source = String(texte ?? '');
  const mots = motsDuFiltre(saisie);
  if (!mots.length || !source) return [{ texte: source, marque: false }];
  // Forme normalisée, et pour chacun de ses caractères l'indice d'origine.
  let norm = '';
  const origine = [];
  for (let i = 0; i < source.length; i += 1) {
    const n = normaliserIntitule(source[i]);
    for (const c of n) { norm += c; origine.push(i); }
  }
  const marque = Array.from({ length: source.length }, () => false);
  for (const m of mots) {
    let k = norm.indexOf(m);
    while (k !== -1) {
      for (let j = k; j < k + m.length; j += 1) marque[origine[j]] = true;
      k = norm.indexOf(m, k + m.length);
    }
  }
  const out = [];
  for (let i = 0; i < source.length; i += 1) {
    const dernier = out[out.length - 1];
    if (dernier && dernier.marque === marque[i]) dernier.texte += source[i];
    else out.push({ texte: source[i], marque: marque[i] });
  }
  return out;
}
