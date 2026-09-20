/*
 * LA FICHE DE GOUVERNEMENT — ce qu'elle sait lire, et ce qu'elle refuse de
 * deviner (#330).
 *
 * Tout ce qui se décide ici se décide sur le LIBELLÉ OFFICIEL du portefeuille,
 * tel que l'Assemblée nationale le publie. Rien n'est déduit d'un nom, d'un
 * parti ou d'une proximité supposée : « Secrétariat d'État AUPRÈS DU ministre
 * de l'Europe » dit son rattachement, et c'est cette phrase-là qu'on lit.
 *
 * Trois pièges payés en maquette, les 17 et 18/09/2026 :
 *
 * 1. LA SOURCE ÉCRIT DES ESPACES INSÉCABLES. « Ministère<nbsp>auprès<nbsp>du
 *    Premier ministre » : le rattachement devenait illisible ET le libellé ne
 *    revenait pas à la ligne. Normalisés à l'entrée, une fois.
 * 2. LA SOURCE SE TROMPE PARFOIS. « Secrétariat d'État APRÈS de la ministre
 *    des solidarités » existe tel quel : la faute est dans la donnée, elle se
 *    lit, elle ne se corrige pas — sinon un ministère fantôme apparaît.
 * 3. LE LIBELLÉ D'UN MINISTÈRE ET CELUI DE SON RATTACHEMENT NE COMMENCENT PAS
 *    PAREIL : « Ministère de l'agriculture » contre « du ministre de
 *    l'agriculture ». On retire les têtes de phrase TANT QU'IL Y EN A, sinon
 *    les deux ne s'apparient jamais et le même ministère fait deux blocs.
 */

export const MATIERE_ABSENTE = 'Matière non établie';
export const COMMISSIONS_SPECIALES = 'Commissions spéciales';

/* Une vague de nominations regroupe les prises de fonction rapprochées : un
 * décret de nomination et son complément tombent à deux ou trois jours
 * d'écart. Sans ce seuil, Attal serait « remanié 2 fois » le jour de sa
 * formation. Le seuil est DÉCLARÉ, il n'est pas deviné. */
export const JOURS_MEME_VAGUE = 8;

function normaliser(texte) {
  return String(texte || '').replace(/\u00a0/g, ' ');
}

/** Le ministère auquel un portefeuille est rattaché, tel que son libellé le
 *  nomme — `null` pour un ministère de plein exercice. */
export function rattachementDuPortefeuille(portefeuille) {
  const m = /\b(?:aupr[èe]s|apr[èe]s)\s+(.*?)(?:,\s*charg|$)/i.exec(normaliser(portefeuille));
  return m ? m[1].trim() : null;
}

/** La charge d'un ministre délégué ou secrétaire d'État (« chargé de … »), ou
 *  `null` quand la source ne la précise pas — jamais un libellé inventé. */
export function chargeDuPortefeuille(portefeuille) {
  const m = /charg[ée]e?\s+(.*)$/i.exec(normaliser(portefeuille));
  return m ? capitale(m[1]) : null;
}

function capitale(texte) {
  const t = String(texte || '').replace(/^(du|de la|de l’|de l'|des|de)\s+/i, '');
  return t ? t.charAt(0).toUpperCase() + t.slice(1) : t;
}

/** La clé de rapprochement d'un portefeuille : ce qui nomme le domaine, une
 *  fois retirées les têtes de phrase administratives. */
export function motsClesPortefeuille(portefeuille) {
  let t = normaliser(portefeuille)
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[’']/g, ' ')
    .replace(/[^a-z ]/g, ' ');
  let avant;
  do {
    avant = t;
    t = t.replace(/^\s*(ministere|ministre|secretariat d etat|secretaire d etat)\s+/, '');
    t = t.replace(/^\s*(delegue|deleguee)\s+/, '');
    t = t.replace(/^\s*(aupres|apres)\s+/, '');
    t = t.replace(/^\s*(de la|de l|du|des|de|d)\s+/, '');
    t = t.replace(/^\s*etat\s+/, '');
  } while (t !== avant);
  return t.replace(/\s+/g, ' ').trim();
}

/* Une même personne porte plusieurs entrées quand son intitulé change : on
 * garde la dernière, par date de début. Sans ça, Castaner apparaît trois fois
 * dans le même bloc. */
function dedoublonner(membres) {
  const parNom = new Map();
  for (const m of membres) {
    const connu = parNom.get(m.nom);
    if (!connu || String(m.debut || '') > String(connu.debut || '')) parNom.set(m.nom, m);
  }
  return [...parNom.values()].sort((a, b) => String(a.debut || '').localeCompare(String(b.debut || '')));
}

/**
 * L'organigramme : un bloc par ministère, ses titulaires successifs, et les
 * ministres délégués et secrétaires d'État qui lui sont rattachés.
 *
 * Un ministère tenu successivement par deux personnes reste UN ministère — la
 * transition écologique de Philippe II en a eu trois, et trois blocs auraient
 * dit trois ministères.
 */
export function organigramme(membres = [], premierMinistre = null, periode = {}) {
  const poles = [];
  const pourCle = (cle, titre, connu) => {
    for (const p of poles) {
      if (p.cle && cle && (p.cle.startsWith(cle) || cle.startsWith(p.cle))) {
        if (connu && !p.connu) { p.connu = true; p.titre = titre; }
        return p;
      }
    }
    const nouveau = { cle, titre, titulaires: [], enfants: [], connu };
    poles.push(nouveau);
    return nouveau;
  };

  for (const m of membres) {
    if (rattachementDuPortefeuille(m.portefeuille)) continue;
    pourCle(motsClesPortefeuille(m.portefeuille), normaliser(m.portefeuille) || 'Portefeuille non renseigné', true)
      .titulaires.push(m);
  }
  for (const m of membres) {
    const parent = rattachementDuPortefeuille(m.portefeuille);
    if (!parent) continue;
    pourCle(motsClesPortefeuille(parent), capitale(normaliser(parent)), false).enfants.push(m);
  }

  const pm = poles.find((p) => p.cle === 'premier ministre');
  if (pm) pm.pm = true;
  else if (premierMinistre) {
    poles.unshift({
      cle: 'premier ministre',
      titre: 'Premier ministre',
      titulaires: [{ nom: premierMinistre, portefeuille: 'Premier ministre', debut: periode.debut, fin: periode.fin }],
      enfants: [],
      connu: true,
      pm: true,
    });
  }

  return poles
    .map((p) => ({ ...p, titulaires: dedoublonner(p.titulaires), enfants: dedoublonner(p.enfants) }))
    .sort((a, b) => {
      if (Boolean(a.pm) !== Boolean(b.pm)) return a.pm ? -1 : 1;
      if (a.connu !== b.connu) return a.connu ? -1 : 1;
      return a.titre.localeCompare(b.titre, 'fr');
    });
}

/** Les vagues de nomination, de la formation au dernier remaniement. */
export function vaguesDeNomination(membres = []) {
  const parDate = new Map();
  for (const m of membres) {
    if (!m.debut) continue;
    parDate.set(m.debut, (parDate.get(m.debut) || 0) + 1);
  }
  const vagues = [];
  for (const date of [...parDate.keys()].sort()) {
    const derniere = vagues[vagues.length - 1];
    const ecart = derniere ? (Date.parse(date) - Date.parse(derniere.fin)) / 86400000 : Infinity;
    if (derniere && ecart < JOURS_MEME_VAGUE) {
      derniere.n += parDate.get(date);
      derniere.fin = date;
    } else {
      vagues.push({ date, fin: date, n: parDate.get(date) });
    }
  }
  return vagues;
}

/** Combien de PERSONNES en fonction à une date — pas combien de portefeuilles :
 *  quelqu'un qui en tient deux le même jour ne compte qu'une fois. */
export function effectifAu(membres = [], iso) {
  const t = Date.parse(iso);
  const noms = new Set();
  for (const m of membres) {
    if (Date.parse(m.debut) <= t && (!m.fin || Date.parse(m.fin) >= t)) noms.add(m.nom);
  }
  return noms.size;
}

/**
 * La fourchette d'effectif simultané, lue APRÈS la formation : le premier jour,
 * le Premier ministre est seul nommé, et publier ce 1 ferait lire un
 * gouvernement d'une personne.
 */
export function fourchetteEffectif(membres = [], periode = {}) {
  const vagues = vaguesDeNomination(membres);
  if (!vagues.length) return null;
  const finPeriode = periode.fin || null;
  const jalons = new Set([vagues[0].fin]);
  for (const m of membres) {
    if (m.debut >= vagues[0].fin) jalons.add(m.debut);
    if (m.fin && (!finPeriode || m.fin < finPeriode)) jalons.add(m.fin);
  }
  const effectifs = [...jalons].map((d) => effectifAu(membres, d));
  return { mini: Math.min(...effectifs), maxi: Math.max(...effectifs) };
}

/**
 * LE GROUPE MAJORITAIRE N'EST PAS UNE LECTURE DE NOTRE PART. L'Assemblée
 * déclare elle-même la position de chaque groupe — « Majoritaire »,
 * « Opposition », « Minoritaire » —, et depuis 2024 elle ne déclare plus rien.
 * Cette absence se dit ; elle ne se comble pas en désignant le plus nombreux,
 * ce qui serait notre jugement et non un fait (§2 règles 1 et 5).
 *
 * `groupes` vient du manifest : { nom, legislature, position, debut, fin }.
 */
export function majoriteDuGouvernement(groupes = [], periode = {}) {
  const fin = periode.fin || new Date().toISOString().slice(0, 10);
  const concernes = groupes.filter((g) => g.debut && g.debut <= fin && (!g.fin || g.fin >= periode.debut));
  if (!concernes.length) return [];

  const parLegislature = new Map();
  for (const g of concernes) {
    const cle = String(g.legislature);
    const connu = parLegislature.get(cle);
    if (!connu || (g.position === 'majorite' && connu.position !== 'majorite')) {
      parLegislature.set(cle, g);
    }
  }
  return [...parLegislature.values()]
    .sort((a, b) => String(a.debut).localeCompare(String(b.debut)))
    .map((g) => (g.position === 'majorite'
      ? { legislature: g.legislature, debut: g.debut, nom: g.nom, declaree: true }
      : { legislature: g.legislature, debut: g.debut, nom: 'aucun groupe déclaré majoritaire', declaree: false }));
}

/**
 * Les trois nombres de « Projets de loi ». `adoptes` réunit les quatre statuts
 * d'adoption, promulgation comprise : un texte promulgué a d'abord été adopté.
 * Le 49.3 est rendu À PART — un texte adopté sans vote n'est pas une position
 * de vote, et il ne se fond dans aucun décompte (§2 règle 4).
 */
export function chiffresDesTextes(comptages = {}, nombreDeTextes = 0) {
  const n = (cle) => comptages[cle] || 0;
  return {
    deposes: nombreDeTextes,
    adoptes: n('adopte') + n('adopte_cmp') + n('adopte_49_3') + n('promulgue'),
    promulgues: n('promulgue'),
    sansVote: n('adopte_49_3') + n('rejete_49_3'),
  };
}

/* Dans une figure, les commissions spéciales — créées pour un seul texte —
 * sont regroupées : une par texte produirait une dizaine de rubans d'un texte
 * dont les étiquettes se recouvrent. La liste, elle, nomme chacune. */
export function matiereDeFigure(texte = {}) {
  const commission = texte.commission || null;
  if (commission && /sp[ée]ciale/i.test(commission)) return COMMISSIONS_SPECIALES;
  return commission || MATIERE_ABSENTE;
}

/**
 * Le flux « matière → étape » : à gauche la commission saisie au fond, à droite
 * l'étape où le texte s'est arrêté. Aucun seuil, aucun filtrage : du plus gros
 * ruban au texte unique, tout est tracé.
 */
export function fluxMatiereSort(textes = [], ordreSorts = []) {
  const compteMatiere = new Map();
  for (const t of textes) {
    const m = matiereDeFigure(t);
    compteMatiere.set(m, (compteMatiere.get(m) || 0) + 1);
  }
  const matieres = [...compteMatiere.entries()]
    .sort((a, b) => {
      if (a[0] === MATIERE_ABSENTE) return 1;
      if (b[0] === MATIERE_ABSENTE) return -1;
      return b[1] - a[1] || a[0].localeCompare(b[0], 'fr');
    })
    .map(([nom, n], rang) => ({ nom, n, rang }));

  const compteSort = new Map();
  for (const t of textes) compteSort.set(t.statut, (compteSort.get(t.statut) || 0) + 1);
  const sorts = ordreSorts
    .filter((s) => compteSort.has(s))
    .map((s) => ({ statut: s, n: compteSort.get(s) }));

  const paires = new Map();
  for (const t of textes) {
    const cle = `${matiereDeFigure(t)} ${t.statut}`;
    paires.set(cle, (paires.get(cle) || 0) + 1);
  }
  const liens = [...paires.entries()].map(([cle, valeur]) => {
    const [matiere, statut] = cle.split(' ');
    return { matiere, statut, valeur };
  });

  return { matieres, sorts, liens };
}

/**
 * SUR QUOI SES MEMBRES ONT PRIS LA PAROLE — mêmes règles que sur la fiche de
 * groupe (#329) : des SUJETS, jamais des positions, et un compte de MEMBRES,
 * jamais d'occurrences (§2 règles 1 et 8).
 *
 * Le dénominateur publié est `comptages.membres_avec_interventions` — les
 * membres dont la parole est collectée —, et non l'effectif du gouvernement :
 * il dit sur quelle population le numérateur est compté (§2 règle 7).
 *
 * Un débat n'entre ici que si la source publie son intitulé. L'étiquetage est
 * plus fin sur les années récentes : sur Philippe II, 329 interventions sur
 * 48 370 en portent un (mesuré le 19/09/2026). C'est une limite de la source,
 * dite dans « Ce qu'on n'a pas pu lire », jamais un silence du gouvernement.
 */
export function sujetsDeParole(tags = [], comptages = {}, limite = 10) {
  const liste = [...tags]
    .filter((t) => t && t.tag)
    .sort((a, b) => (b.nb_membres_porteurs || 0) - (a.nb_membres_porteurs || 0)
      || String(a.tag).localeCompare(String(b.tag), 'fr'));
  const tous = liste.map((t) => ({ label: t.tag, porteurs: t.nb_membres_porteurs || 0 }));
  return {
    liste: tous.slice(0, limite),
    // La liste ENTIÈRE, que la fiche a déjà téléchargée : la recherche sur la
    // page la filtre sans rien charger de plus (#979). La section, elle,
    // continue de n'afficher que les dix plus portés.
    tous,
    total: liste.length,
    denominateur: comptages.membres_avec_interventions || 0,
    membres: comptages.membres_distincts || 0,
  };
}
