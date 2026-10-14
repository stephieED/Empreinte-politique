/* ── LES BUDGETS QU'UN GOUVERNEMENT A FAIT VOTER (#1053) ──────────────────────
 *
 * Ce que la section « Les budgets que ce gouvernement a fait voter » calcule,
 * à partir de `pivot_data/budgets_gouvernements.json`. Aucun import : le module
 * se teste par `node`, sans la fiche.
 *
 * LE FICHIER DIT DÉJÀ QUELLE ANNÉE REVIENT À QUI — une année revient au
 * gouvernement sous lequel sa loi de finances a été promulguée. Rien n'est
 * réparti ici, et aucune année n'est ajoutée ni retirée — la règle est dans la
 * décision de Backend sur #1053.
 *
 * TROIS RÈGLES QUE CE MODULE TIENT.
 *
 *   Les deux colonnes d'une figure ONT LA MÊME HAUTEUR, et c'est une égalité
 *   comptable, pas un arrondi : ce que l'État dépense de plus qu'il ne reçoit
 *   est ce qu'il emprunte. « Emprunt » complète donc la colonne de gauche.
 *
 *   Une année sans dépenses par mission, ou sans comptes de la sécurité
 *   sociale, N'ENTRE PAS dans la figure et EST NOMMÉE à côté (§2 règle 5) :
 *   additionner les seules recettes d'une année de plus fausserait les deux
 *   colonnes.
 *
 *   « Pour 100 € » arrondit de sorte que la colonne fasse son total, au plus
 *   fort reste : douze lignes arrondies une à une feraient 98 ou 103.
 */

/* Les dix premières dépenses, puis « Autres » : la liste entière compte une
   trentaine de missions, et une vingtaine de régimes. */
export const LIGNES_GARDEES = 10;

/* Les libellés de la source, dits pour un lecteur. Un libellé absent de ces
   tables est repris tel quel : il n'est jamais écarté. */
const RECETTES = {
  'Taxe sur la valeur ajoutée': 'TVA',
  'Taxe intérieure de consommation sur les produits énergétiques': 'Taxe sur les produits énergétiques',
  'Total recettes non fiscales': 'Recettes non fiscales',
};
const FONDS_DE_CONCOURS = 'Fonds de concours et attribution de produits';
const AUTRES_RESSOURCES = 'Autres ressources';
const COLLECTIVITES = 'PSR au profit des collectivités territoriales';
const UNION = "PSR au profit de l'Union européenne";

const EMPLOYEURS = "Cotisations sociales d'employeurs";
const SALARIES = 'Cotisations sociales de salariés';
/* L'ordre est celui de la figure, de haut en bas. */
export const ORIGINES = [
  ['employeurs', 'Cotisations des employeurs'],
  ['salaries', 'Cotisations des salariés'],
  ['autres-cotisations', 'Autres cotisations'],
  ['non-separees', 'Cotisations non séparées'],
  ['imputees', 'Cotisations imputées'],
  ['impots', 'Impôts et taxes affectés'],
  ['publics', 'Fonds publics (État, collectivités)'],
  ['autres', AUTRES_RESSOURCES],
];
const ORIGINE_DE = {
  [SALARIES]: 'salaries',
  'Autres cotisations sociales': 'autres-cotisations',
  'Cotisations sociales imputées': 'imputees',
  'Impôts et taxes affectés': 'impots',
  'Contributions publiques': 'publics',
};

const AGIRC = 'Agirc-Arrco, retraite complémentaire';
const REGIMES = {
  'Association des régimes de retraite complémentaire des salariés': AGIRC,
  'Association générale des institutions de retraite des cadres': AGIRC,
  'Association générale des institutions de retraite des cadres et association des régimes de retraite complémentaire des salariés': AGIRC,
  'Autres ODASS': 'Autres organismes de sécurité sociale',
  'CNAVPL base complementaire': 'Professions libérales, retraite',
  "Caisse nationale de solidarité pour l'autonomie": 'Autonomie (CNSA)',
  'Caisse nationale des allocations familiales': 'Allocations familiales (Cnaf)',
  'Caisse nationale d’assurance maladie': 'Assurance maladie (Cnam)',
  'Caisse nationale d’assurance vieillesse': 'Assurance vieillesse (Cnav)',
  'Institution de retraite complémentaire des agents non titulaires de l’État et des collectivités publiques': 'Ircantec, agents non titulaires',
  'Pôle emploi': 'France Travail (ex-Pôle emploi)',
  "Régime d'intervention sociale des hôpitaux publics": 'Hôpitaux publics',
  'Régime des salariés agricoles': 'Salariés agricoles',
  'UNEDIC et autres régimes': 'Chômage (Unédic)',
};

const MOIS_ABREGES = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin',
  'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.'];

const somme = (liste, valeur) => liste.reduce((t, x) => t + valeur(x), 0);

/* « 2023 », « 2023 et 2024 », « 2018, 2019 et 2020 ». */
export function listeDesAnnees(annees) {
  if (annees.length < 2) return annees[0] || '';
  return `${annees.slice(0, -1).join(', ')} et ${annees[annees.length - 1]}`;
}

/* Les parts d'une colonne ramenées à 100 € : chaque ligne reçoit `euros`, un
   entier, et la colonne fait `cible` — au plus fort reste. */
export function pour100(lignes, total, cible = 100) {
  if (!(total > 0)) return lignes.map((l) => ({ ...l, euros: 0 }));
  const parts = lignes.map((l, i) => {
    const exact = (l.montant / total) * 100;
    return { i, entier: Math.floor(exact), reste: exact % 1 };
  });
  let aDonner = cible - somme(parts, (p) => p.entier);
  [...parts].sort((a, b) => b.reste - a.reste).forEach((p) => {
    if (aDonner > 0) { p.entier += 1; aDonner -= 1; }
  });
  return lignes.map((l, i) => ({ ...l, euros: parts[i].entier }));
}

/* ── La cascade : recettes, dépenses, puis le reste, année après année ─────── */

/* Chaque année part du niveau où la précédente s'est arrêtée : la dernière
   marche donne le solde de tous les budgets de la fiche. Un exercice en cours
   s'arrête au dernier mois publié, et son étiquette le dit. */
export function cascadeDesBudgets(exercices) {
  let niveau = 0;
  const annees = (exercices || []).filter((e) => e.budget_de_l_etat).map((e) => {
    const b = e.budget_de_l_etat;
    const depart = niveau;
    niveau += b.solde;
    const mois = MOIS_ABREGES[Number((b.dernier_mois || '').slice(5)) - 1];
    return {
      annee: e.exercice,
      /* Les montants courent depuis janvier. */
      periode: b.exercice_complet || !mois ? null : `janv.–${mois}`,
      depart,
      recettes: b.recettes_nettes,
      depenses: b.depenses_nettes,
      /* Ce qui est reversé aux collectivités et à l'Union européenne, et le
         solde des comptes tenus à part : ce qui sépare « recettes moins
         dépenses » du solde que la source publie. */
      reste: b.solde - (b.recettes_nettes - b.depenses_nettes),
      niveau,
    };
  });
  return { annees, solde: niveau };
}

/* ── Les deux colonnes du budget de l'État ─────────────────────────────────── */

/* Le total écrit en tête d'une colonne est la somme des euros de ses lignes,
   complément exclu : le lecteur peut refaire l'addition. */
function lesDeuxColonnes(recoit, depense, total) {
  const arrondie = (lignes) => pour100(lignes, total, Math.round((somme(lignes, (l) => l.montant) / total) * 100));
  const propre = (lignes) => lignes.filter((l) => !l.hachure && !l.vide);
  const gauche = arrondie(recoit);
  const droite = arrondie(depense);
  return {
    recoit: gauche,
    depense: droite,
    recu: somme(propre(gauche), (l) => l.montant),
    recuPour100: somme(propre(gauche), (l) => l.euros),
    verse: somme(propre(droite), (l) => l.montant),
    versePour100: somme(propre(droite), (l) => l.euros),
    total,
  };
}

/* Les dépenses par mission ne sont publiées que pour certaines années, et
   seulement une fois l'année close. `annees` sont celles de la figure,
   `sansDetail` celles que le fichier porte sans leurs missions. */
export function colonnesDuBudget(exercices) {
  const tous = (exercices || []).filter((e) => e.budget_de_l_etat);
  const retenus = tous.filter((e) => Array.isArray(e.budget_de_l_etat.missions));
  const annees = retenus.map((e) => e.exercice);
  const sansDetail = tous.filter((e) => !retenus.includes(e)).map((e) => e.exercice);
  if (!retenus.length) return { annees, sansDetail, recoit: [], depense: [] };
  const blocs = retenus.map((e) => e.budget_de_l_etat);

  const cumul = (liste, cle) => {
    const par = new Map();
    blocs.forEach((b) => (b[liste] || []).forEach((l) => par.set(l[cle], (par.get(l[cle]) || 0) + l.montant)));
    return par;
  };
  const recettes = cumul('recettes', 'ligne');
  const reverse = cumul('reverse', 'ligne');
  const missions = [...cumul('missions', 'mission')].filter(([, v]) => v > 0).sort((a, b) => b[1] - a[1]);
  // Les programmes de chaque mission, additionnés sur les mêmes années : ce que
  // le survol d'une mission détaille. Un programme sans nom garde son numéro.
  const programmes = new Map();
  blocs.forEach((bloc) => (bloc.missions || []).forEach((m) => (m.programmes || []).forEach((p) => {
    const par = programmes.get(m.mission) || new Map();
    const deja = par.get(p.programme) || { nom: p.libelle || `Programme ${p.programme}`, montant: 0 };
    deja.montant += p.montant;
    par.set(p.programme, deja);
    programmes.set(m.mission, par);
  })));
  const detailDe = (mission) => {
    const par = programmes.get(mission);
    return par ? [...par.values()].filter((p) => p.montant > 0).sort((x, y) => y.montant - x.montant) : undefined;
  };
  const aPart = somme(blocs, (b) => b.comptes_a_part || 0);
  const solde = somme(blocs, (b) => b.solde);
  const depenses = somme(blocs, (b) => b.depenses_nettes);

  // À gauche : les impôts un par un, puis le reste de ce qui est reçu.
  const recoit = [...recettes].filter(([nom]) => nom !== FONDS_DE_CONCOURS)
    .map(([nom, montant], rang) => ({ nom: RECETTES[nom] || nom, montant, rang }))
    .filter((l) => l.montant > 0);
  recoit.push({ nom: AUTRES_RESSOURCES, montant: (recettes.get(FONDS_DE_CONCOURS) || 0) + Math.max(aPart, 0), pale: true });
  if (solde < 0) recoit.unshift({ nom: 'Emprunt', montant: -solde, hachure: true });

  // À droite : les dix premières missions et ce qui est reversé, rangés par
  // montant ; puis ce qui reste, en gris.
  const gardees = missions.slice(0, LIGNES_GARDEES);
  const petites = missions.slice(LIGNES_GARDEES);
  const depense = [
    ...gardees.map(([nom, montant]) => ({ nom, montant, detail: detailDe(nom) })),
    { nom: 'Reversé aux collectivités', montant: reverse.get(COLLECTIVITES) || 0 },
    { nom: 'Reversé à l’Union européenne', montant: reverse.get(UNION) || 0 },
  ].sort((a, b) => b.montant - a.montant);
  if (petites.length) {
    depense.push({
      nom: `Autres missions (${petites.length})`,
      montant: somme(petites, ([, v]) => v),
      detail: petites.map(([nom, montant]) => ({ nom, montant })),
    });
  }
  const ecart = depenses - somme(missions, ([, v]) => v) + Math.max(-aPart, 0);
  if (ecart > 0) depense.push({ nom: 'Non réparti par mission, comptes à part', montant: ecart, pale: true });

  const total = Math.max(somme(recoit, (l) => l.montant), somme(depense, (l) => l.montant));
  return { annees, sansDetail, ...lesDeuxColonnes(recoit, depense, total) };
}

/* ── Les deux colonnes de la sécurité sociale ──────────────────────────────── */

/* La source compte la sécurité sociale en millions d'euros, l'État en euros :
   tout est rendu en euros. */
const MILLION = 1e6;

/* Les caisses reçoivent et versent des sommes qui ne s'égalent pas : la colonne
   la plus courte est complétée en haut, et ce complément est nommé. */
export function colonnesDeLaSecuriteSociale(exercices) {
  const tous = exercices || [];
  const retenus = tous.filter((e) => e.securite_sociale);
  const annees = retenus.map((e) => e.exercice);
  const sansDetail = tous.filter((e) => !e.securite_sociale).map((e) => e.exercice);
  if (!retenus.length) return { annees, sansDetail, recoit: [], depense: [] };

  const origines = new Map();
  const regimes = new Map();
  const nonSeparees = [];
  let frais = 0;
  retenus.forEach((e) => {
    const s = e.securite_sociale;
    const lignes = s.ressources || [];
    // La source provisoire donne les trois cotisations sur la seule ligne des
    // employeurs : sans la ligne des salariés, elle ne dit plus « employeurs ».
    const separees = lignes.some((l) => l.origine === SALARIES);
    if (!separees && lignes.some((l) => l.origine === EMPLOYEURS)) nonSeparees.push(e.exercice);
    lignes.forEach((l) => {
      const cle = l.origine === EMPLOYEURS ? (separees ? 'employeurs' : 'non-separees') : (ORIGINE_DE[l.origine] || 'autres');
      origines.set(cle, (origines.get(cle) || 0) + l.montant * MILLION);
    });
    (s.prestations || []).forEach((p) => {
      const nom = REGIMES[p.regime] || p.regime;
      regimes.set(nom, (regimes.get(nom) || 0) + p.montant * MILLION);
    });
    frais += (s.autres_emplois || 0) * MILLION;
  });

  const recoit = ORIGINES.map(([cle, nom], rang) => ({ nom, montant: origines.get(cle) || 0, rang, cle }))
    .filter((l) => l.montant > 0)
    .map((l) => (l.cle === 'autres' ? { nom: l.nom, montant: l.montant, pale: true }
      : l.cle === 'non-separees' ? { nom: `${l.nom} (${listeDesAnnees(nonSeparees)})`, montant: l.montant, sombre: true }
        : { nom: l.nom, montant: l.montant, rang: l.rang > 3 ? l.rang - 1 : l.rang }));
  const tries = [...regimes].filter(([, v]) => v > 0).sort((a, b) => b[1] - a[1]);
  const petits = tries.slice(LIGNES_GARDEES);
  const depense = tries.slice(0, LIGNES_GARDEES).map(([nom, montant]) => ({ nom, montant }));
  if (petits.length) {
    depense.push({
      nom: `Autres régimes (${petits.length})`,
      montant: somme(petits, ([, v]) => v),
      gris: true,
      detail: petits.map(([nom, montant]) => ({ nom, montant })),
    });
  }
  if (frais > 0) depense.push({ nom: 'Frais de gestion et autres emplois', montant: frais, gris: true });

  const recu = somme(recoit, (l) => l.montant);
  const verse = somme(depense, (l) => l.montant);
  if (recu > verse) depense.unshift({ nom: 'Non dépensé, ou versé à un autre bloc', montant: recu - verse, vide: true });
  else if (verse > recu) recoit.unshift({ nom: 'Ce qui manque, ou reçu d’un autre bloc', montant: verse - recu, hachure: true });
  return { annees, sansDetail, ...lesDeuxColonnes(recoit, depense, Math.max(recu, verse)) };
}
