/* ── Ce que la fiche d'une législature lit de son fichier (#1314) ─────────────
 *
 * UN SEUL ADAPTATEUR. Les fichiers de Backend (`legislatures.json`,
 * `dossiers_an/<n>.json`, PR #1325) se joignent ici à `commissions_dossiers.json`
 * et `textes_promulgues.json` par l'uid du dossier. Si leurs champs bougent, c'est
 * ici qu'ils se rattrapent : les sections ne lisent que la vue `vueLegislature`.
 *
 * Une absence reste une absence (AGENTS.md §2 règle 5) : un champ que le fichier
 * ne porte pas vaut `null`, jamais zéro, et la section qui en dépend se tait.
 */

const ROMAINS = { 14: 'XIVe', 15: 'XVe', 16: 'XVIe', 17: 'XVIIe' };
export const romain = (id) => ROMAINS[Number(id)] || `${id}e`;

/* Les quatre étapes d'un texte renvoyé à une commission, dans l'ordre où il les
 * franchit. « Devenu loi » se déduit : promulgué ET adopté par l'Assemblée
 * pendant la législature (rattachement arbitré le 21/10/2026). */
export const ETAPES = [
  { cle: 'jamais', libelle: 'Jamais examiné', pluriel: 'Jamais examinés', couleur: '#D6D2CC' },
  { cle: 'examine', libelle: 'Examiné en commission', pluriel: 'Examinés en commission', couleur: '#D9B3C8' },
  { cle: 'debattu', libelle: 'Débattu en séance', pluriel: 'Débattus en séance', couleur: '#803060' },
  { cle: 'loi', libelle: 'Devenu loi pendant la législature', pluriel: 'Devenus lois pendant la législature', couleur: '#14151A' },
];

/* Les trois meubles de la bibliothèque. Les textes sans décision n'y sont pas :
 * ils sont 1 316 en XVIe, et leur meuble écrasait les trois autres (21/10). */
export const SORTS = [
  { cle: 'promulgue', libelle: 'Promulgués', singulier: 'Promulgué' },
  { cle: 'adopte', libelle: 'Adoptés', singulier: 'Adopté par l’Assemblée, pas encore loi' },
  { cle: 'rejete', libelle: 'Rejetés', singulier: 'Rejeté' },
];

export const ORIGINES = {
  gouvernement: { libelle: 'Le gouvernement', couleur: '#A84B12' },
  deputes: { libelle: 'Des députés', couleur: '#803060' },
  senateurs: { libelle: 'Des sénateurs', couleur: '#169E9E' },
};
// Plus foncé que le fond des étagères, où #D6D2CC ne se voyait pas (22/10/2026).
export const SANS_ORIGINE = { libelle: 'Auteur non renseigné', couleur: '#9A958D' };

const dansPeriode = (date, periode) =>
  !!date && !!periode?.debut && date >= periode.debut && (!periode.fin || date <= periode.fin);

const QUALITES = {
  depute: ['député', 'deputes'],
  senateur: ['sénateur', 'senateurs'],
  membre_du_gouvernement: ['membre du gouvernement', 'gouvernement'],
  president_de_la_republique: ['président de la République', 'gouvernement'],
};
const ADOPTES = new Set(['adopte', 'adopte_cmp', 'adopte_49_3']);
const REJETES = new Set(['rejete', 'rejete_49_3']);
const ETAPE_AN = { depose: 'jamais', examine_en_commission: 'examine', debattu_en_seance: 'debattu' };

const domaine = (c) => {
  if (!c?.sigle) return 'Domaine non renseigné';
  return c.sigle.startsWith('CS ') ? `Commission spéciale : ${c.sigle.slice(3)}` : c.sigle;
};

/* Une ligne de `dossiers_an/<n>.json`, jointe à sa commission et à sa
 * promulgation par l'uid du dossier. */
function vueDossier(uid, d, id, periode, { acteurs, organes, commissions, promulgues }) {
  const commission = commissions[uid] || null;
  const promulgation = promulgues[uid]?.date_promulgation ?? null;
  const adoption = d.derniere_adoption_an?.date ?? null;
  const sort = promulgation ? 'promulgue' : ADOPTES.has(d.statut) ? 'adopte' : REJETES.has(d.statut) ? 'rejete' : null;
  /* UNE LOI COMPTE POUR LA LÉGISLATURE OÙ L'ASSEMBLÉE L'A ADOPTÉE (21/10). Un
   * texte rejeté y compte si l'Assemblée y a agi sur lui. */
  const deLaLegislature = sort === 'rejete'
    ? !!d.etape_an?.[id]
    : sort ? (adoption ? dansPeriode(adoption, periode) : dansPeriode(promulgation, periode)) : false;
  /* L'origine se lit dans la qualité de l'initiateur, que Backend lit dans le
   * mandat cité par le dossier — jamais dans le préfixe du texte. */
  const initiateurs = (d.initiateurs || []).map((i) => ({
    nom: acteurs[i.acteur_ref] || null,
    fonction: QUALITES[i.qualite]?.[0] || null,
    groupe: i.groupe_ref ? (organes[i.groupe_ref]?.nom || organes[i.groupe_ref]?.libelle_abrege || null) : null,
    origine: QUALITES[i.qualite]?.[1] || null,
  })).filter((i) => i.nom);
  return {
    id: uid,
    legislature: d.legislature,
    titre: d.titre || null,
    commission: commission?.sigle ?? null,
    commissionSpeciale: commission?.type === 'CNPS' || (commission?.sigle || '').startsWith('CS '),
    domaine: domaine(commission),
    sort: deLaLegislature ? sort : null,
    etape: sort === 'promulgue' && deLaLegislature ? 'loi' : (ETAPE_AN[d.etape_an?.[id]] || 'jamais'),
    initiateurs,
    origine: initiateurs[0]?.origine || null,
    depot: d.date_depot ?? null,
    adoption,
    promulgation,
    solennel: (d.scrutins_solennels || []).length > 0,
    article493: d.statut === 'adopte_49_3' || (d.engagements_49_3 || []).some((e) => e.issue === 'considere_adopte'),
    url: d.source_url || `https://www.assemblee-nationale.fr/dyn/${d.legislature}/dossiers/${uid}`,
  };
}

/** La vue que les sections lisent. `sources` est ce que rend `getLegislature`. */
export function vueLegislature(sources, id, gouvernements = []) {
  if (!sources) return null;
  const { legislature: l, dossiers: fichier, comptes, commissions, promulgues, groupesDuSite } = sources;
  const periode = { debut: l.debut ?? null, fin: l.fin ?? null };
  const contexte = { acteurs: fichier.acteurs || {}, organes: fichier.organes || {}, commissions, promulgues };
  const dossiers = Object.entries(fichier.dossiers || {}).map(([uid, d]) => vueDossier(uid, d, String(id), periode, contexte));
  /* Un gouvernement nommé le dernier jour de la législature n'y a pas
   * gouverné : Philippe II commence le 20/06/2017, jour où la XIVe finit. Le
   * garder posait une étiquette hors de la frise (22/10/2026). */
  const govs = gouvernements
    .filter((g) => periode.debut && g.debut && g.debut < (periode.fin || '9999') && (g.fin || '9999') >= periode.debut)
    .sort((a, b) => a.debut.localeCompare(b.debut));
  /* La position déclarée vient des fiches de groupe, jointes par l'organe de
   * l'Assemblée : les sigles des deux sources diffèrent (« LFI-NUPES », « LFI »). */
  const duSite = (organe) => groupesDuSite.find((g) => (g.organes || []).includes(organe)) || null;
  /* L'Assemblée numérote ses sièges de la droite vers la gauche : la place
   * médiane la plus haute siège le plus à gauche de la figure. */
  const groupes = (l.groupes || [])
    .filter((g) => g.place_mediane != null)
    .map((g) => {
      // Le sigle et le nom des fiches de groupe du site, pour que la fiche parle
      // comme elles ; à défaut, ceux de l'Assemblée.
      const s = duSite(g.organe_ref);
      /* LE SIGLE DU JOUR DE RÉFÉRENCE QUAND LE SITE EN GARDE UN AUTRE (22/10/2026,
       * « ceux du 20 juin 2017 ») : la fiche de groupe XIVe porte le sigle de son
       * premier organe (SRC, UMP), alors qu'au 20/06/2017 les groupes s'appelaient
       * SER et LES-REP. Le sigle du site reste quand il est une forme courte de
       * celui de l'Assemblée (LFI pour LFI-NUPES, SOC pour SOC-A, UDR pour UDDPLR) :
       * ses lettres s'y retrouvent dans l'ordre. */
      const court = (a, b) => { let i = 0; for (const c of b) if (c === a[i]) i += 1; return i === a.length; };
      const sigle = s?.sigle && (court(s.sigle, g.sigle) || court(g.sigle, s.sigle)) ? s.sigle : g.sigle;
      return {
        sigle, nom: s?.nom || g.nom, effectif: g.membres_au_jour,
        position: s?.position ?? (g.sigle === 'NI' ? 'non_inscrit' : null), place_mediane: g.place_mediane,
      };
    })
    /* Les non-inscrits ne forment pas un groupe et n'ont pas de bloc de
     * sièges : leur siège médian les posait au centre (XIVe : sièges 66 à 399).
     * Ils passent en fin de liste et en bout d'hémicycle (22/10/2026). */
    .sort((a, b) => (a.position === 'non_inscrit') - (b.position === 'non_inscrit') || b.place_mediane - a.place_mediane);
  const lois = dossiers.filter((d) => d.etape === 'loi');
  return {
    id,
    nom: `${romain(id)} législature`,
    periode,
    fin: { mode: l.mode_fin ?? null, decret: l.decret_dissolution ?? null },
    termePrevu: l.terme_prevu ?? null,
    gouvernements: govs,
    groupes,
    sieges: groupes.reduce((s, g) => s + (g.effectif || 0), 0) || null,
    comptes: {
      lois: lois.length,
      solennels: comptes?.scrutins_solennels ?? null,
      motions: comptes?.motions_censure ?? null,
      article493: lois.filter((d) => d.article493).length,
    },
    /* La commission : les dossiers ouverts dans la législature, renvoyés à une
     * commission (la base de la maquette, 1 506 en XVIe). */
    dossiers: dossiers.filter((d) => d.sort || (d.legislature === String(id) && d.commission)),
  };
}

/* ── Les mots des titres, pour le nuage des commissions ──────────────────────
 * Les règles arbitrées sur maquette les 21-22/10 : mots de liaison, formules
 * (« proposition de loi visant à ») et verbes d'intention retirés ; singulier
 * et pluriel réunis ; masculin et féminin des adjectifs réunis par terminaisons
 * sûres (« commune » ne devient pas « commun »). */
const VIDES = new Set(`a à au aux avec ce ces cet cette dans de des du d en et est être il ils la le les l leur leurs lors mais même ni nos notre ou où par pas plus pour qu que qui sa sans se ses son sous sur ta te tes ton tous tout toute toutes très un une vos votre y afin ainsi entre contre dont chez via vers selon ne non aussi autres autre deux trois loi lois projet projets proposition propositions visant tendant portant relatif relative relatifs relatives ordonnance ordonnances article articles code n° no mise œuvre oeuvre cadre matière ensemble dispositions disposition diverses divers mesures mesure mieux comme`.split(' '));
const INTENTIONS = new Set(`renforcer garantir créer création améliorer amélioration lutter permettre assurer favoriser protéger protection instaurer instauration rendre mettre faciliter encadrer encadrement interdire supprimer modifier modification prévoir établir développer soutenir simplifier simplification adapter adaptation reconnaître reconnaissance valoriser accompagner accélérer accélération moderniser modernisation clarifier préserver promouvoir prolonger étendre élargir limiter réduire sécuriser rétablir instituer autoriser approuver ratifier ratification approbation ouverture organisation orientation programmation lutte faire donner porter`.split(' '));
const FEMININS = [['ales', 'al'], ['ale', 'al'], ['elles', 'el'], ['elle', 'el'], ['aises', 'ais'], ['aise', 'ais'], ['iques', 'ic'], ['ique', 'ic'], ['ives', 'if'], ['ive', 'if'], ['euses', 'eux'], ['euse', 'eux'], ['ières', 'ier'], ['ière', 'ier'], ['ées', 'é'], ['ée', 'é']];

function motsBruts(titre) {
  return (titre || '').replace(/’/g, "'").match(/[A-Za-zÀ-ÿœŒ'-]+/g)?.map((w) => w.toLowerCase().split("'").pop().replace(/^-+|-+$/g, ''))
    .filter((w) => w.length >= 3 && !VIDES.has(w) && !INTENTIONS.has(w)) || [];
}

/** Ajoute `mots` à chaque dossier et rend les mots transversaux (présents dans
 *  au moins 7 des 9 commissions, commissions spéciales réunies), que le nuage
 *  global écarte. */
export function motsDesTitres(dossiers) {
  const bruts = dossiers.map((d) => motsBruts(d.titre));
  const vus = new Set(bruts.flat());
  const singulier = (w) => {
    if (w.endsWith('aux') && vus.has(`${w.slice(0, -3)}al`)) return `${w.slice(0, -3)}al`;
    if ((w.endsWith('s') || w.endsWith('x')) && vus.has(w.slice(0, -1))) return w.slice(0, -1);
    return w;
  };
  const masculin = (w) => {
    for (const [f, m] of FEMININS) if (w.endsWith(f) && vus.has(w.slice(0, -f.length) + m)) return w.slice(0, -f.length) + m;
    return w;
  };
  const avecMots = dossiers.map((d, i) => ({ ...d, mots: [...new Set(bruts[i].map((w) => masculin(singulier(w))))] }));
  const presence = new Map();
  avecMots.forEach((d) => {
    const c = d.commissionSpeciale ? 'CS' : d.commission;
    if (!c) return;
    d.mots.forEach((w) => {
      if (!presence.has(w)) presence.set(w, new Set());
      presence.get(w).add(c);
    });
  });
  const transversaux = new Set([...presence].filter(([, s]) => s.size >= 7).map(([w]) => w));
  return { dossiers: avecMots, transversaux };
}
