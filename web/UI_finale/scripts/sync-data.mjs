#!/usr/bin/env node
// Copie pivot_data/ (+ raw_data/candidats.json) vers public/data/ et génère un
// manifest listant les candidats et groupes réellement disponibles. Exécuté
// avant `dev`/`build` (voir package.json) car Vite ne sert pas de fichiers
// situés hors du dossier du projet.
import { readFileSync, writeFileSync, mkdirSync, readdirSync, cpSync, existsSync, rmSync, statSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { cleLegislature, construireComparaisons } from './comparaison-groupes.mjs';
import { construireCouverture } from './couverture-corpus.mjs';
import { accumulateurs, projection, ranger } from './actes-gouvernement.mjs';
import { construireDebatsLignee, construireExtraitsLignee, construireVueLignee, idDePage } from './vue-lignee.mjs';
import { construireExtraitsGouvernement, construireParoles, lecteurDeProfils } from './vue-parole-gouvernement.mjs';
import { debutDeFenetre } from '../src/utils/filtrePeriode.js';
import { repartitionsDesMaillons } from './amendements-lignees.mjs';
import { legislatureDeAmendementId, selectDerniereLectureVotes } from '../src/utils/lecture.js';
import { vocabulairesDesFiches } from '../src/utils/amendementsMots.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(here, '..');
const repoRoot = path.resolve(projectRoot, '..', '..');
const outDir = path.join(projectRoot, 'public', 'data');

const pivotProfilesDir = path.join(repoRoot, 'pivot_data', 'profiles');
const pivotGroupesDir = path.join(repoRoot, 'pivot_data', 'groupes');
const pivotGouvernementsDir = path.join(repoRoot, 'pivot_data', 'gouvernements');
const actesDir = path.join(repoRoot, 'pivot_data', 'actes_reglementaires');
const pivotLigneesDir = path.join(repoRoot, 'pivot_data', 'lignees');
const candidatsPath = path.join(repoRoot, 'raw_data', 'candidats.json');
const scrutinsPath = path.join(repoRoot, 'pivot_data', 'scrutins.json');
const amendementsDir = path.join(repoRoot, 'pivot_data', 'amendements');

mkdirSync(path.join(outDir, 'profiles'), { recursive: true });
mkdirSync(path.join(outDir, 'groupes'), { recursive: true });
mkdirSync(path.join(outDir, 'gouvernements'), { recursive: true });
mkdirSync(path.join(outDir, 'lignees'), { recursive: true });

// --- scrutins.json (index partagé, #432) ---
// Depuis la normalisation des votes, un profil ne porte plus que le mapping
// { scrutin_id, position } : sans cet index, l'UI n'a ni date, ni texte, ni
// sort à afficher. Copié en premier, et son absence est signalée plutôt que
// silencieuse — c'est la seule dépendance entre fichiers de pivot_data/, et
// une copie oubliée viderait les votes de toutes les vues d'un coup.
if (existsSync(scrutinsPath)) {
  cpSync(scrutinsPath, path.join(outDir, 'scrutins.json'));
} else {
  console.warn(
    `sync-data : ${scrutinsPath} absent — les votes s'afficheront vides (#432). ` +
    'Construire l\'index : python3 src/build_scrutins_index.py',
  );
}

// --- amendements/ (index partagé, #431) ---
// Un fichier de méta par législature, `<lég>.json`, et RIEN D'AUTRE : la liste
// se construit par le nom, elle n'exclut pas. Les fichiers voisins ne sont pas
// copiés tant qu'une vue ne les lit pas — `.cosignatures.json` (59 % de
// l'index, 75,7 Mo, #324) et `.contenu.json` (#1029 voie 2, l'index de mots
// des exposés : 93 Mo pour les quatre législatures). Ils restent dans le
// dépôt, accessibles pour l'analyse.
const INDEX_AMENDEMENTS = /^\d+\.json$/;
if (existsSync(amendementsDir)) {
  mkdirSync(path.join(outDir, 'amendements'), { recursive: true });
  const metaFiles = readdirSync(amendementsDir).filter((f) => INDEX_AMENDEMENTS.test(f));
  for (const file of metaFiles) {
    cpSync(path.join(amendementsDir, file), path.join(outDir, 'amendements', file));
  }
  if (metaFiles.length === 0) {
    console.warn(`sync-data : ${amendementsDir} vide — les amendements s'afficheront vides (#431).`);
  }
} else {
  console.warn(
    `sync-data : ${amendementsDir} absent — les amendements s'afficheront vides (#431). ` +
    'Construire l\'index : python3 src/build_amendements_index_pivot.py',
  );
}

// --- commissions_dossiers.json (commission saisie au fond par dossier, #328) ---
// Absent tant qu'aucun run n'a exécuté `build_commissions_dossiers.py` : la
// fiche candidat n'affiche alors pas la répartition par commission, et ne la
// déduit surtout pas d'un intitulé de dossier (AGENTS.md §2 règle 1).
const commissionsPath = path.join(repoRoot, 'pivot_data', 'commissions_dossiers.json');
if (existsSync(commissionsPath)) {
  cpSync(commissionsPath, path.join(outDir, 'commissions_dossiers.json'));
} else {
  console.warn(
    `sync-data : ${commissionsPath} absent — « L'essentiel » n'affichera pas la ` +
    'répartition par commission saisie au fond (#328). Construire l\'index : ' +
    'python3 src/build_commissions_dossiers.py',
  );
}

// --- scrutins_dossiers.json (scrutin → dossier, statut, 49.3 — #758) ---
// Un scrutin ne porte aucune référence législative : la jointure vient des
// `voteRefs` des actes du dossier, figée par `src/build_scrutins_dossiers.py`.
// Absent, « ce qu'il a voté » n'affiche ni matière ni statut du texte — et ne
// les déduit surtout pas de l'intitulé du scrutin (AGENTS.md §2 règle 1).
const scrutinsDossiersPath = path.join(repoRoot, 'pivot_data', 'scrutins_dossiers.json');
if (existsSync(scrutinsDossiersPath)) {
  cpSync(scrutinsDossiersPath, path.join(outDir, 'scrutins_dossiers.json'));
} else {
  console.warn(
    `sync-data : ${scrutinsDossiersPath} absent — « ce qu'il a voté » n'affichera ni `
    + 'matière ni statut du texte (#758). Construire l\'index : '
    + 'python3 src/build_scrutins_dossiers.py',
  );
}

// --- dossiers_europeens.json (référence → titre, stade, commission au fond — #901) ---
// Le pendant européen de `commissions_dossiers.json`. Sans lui, la cascade du
// versant européen n'a pas de matière et les amendements européens n'ont pas de
// dossier nommé : ni l'une ni l'autre ne se déduit d'un intitulé (§2 règle 1).
const dossiersEuropeensPath = path.join(repoRoot, 'pivot_data', 'dossiers_europeens.json');
if (existsSync(dossiersEuropeensPath)) {
  cpSync(dossiersEuropeensPath, path.join(outDir, 'dossiers_europeens.json'));
} else {
  console.warn(
    `sync-data : ${dossiersEuropeensPath} absent — la cascade européenne n'affichera `
    + 'aucune matière (#901). Construire l\'index : '
    + 'python3 src/dossiers_europeens.py --profils-dir pivot_data/profiles '
    + '--out pivot_data/dossiers_europeens.json',
  );
}

// --- scrutins_europeens.json (scrutins nominatifs du Parlement européen — #901) ---
const scrutinsEuropeensPath = path.join(repoRoot, 'pivot_data', 'scrutins_europeens.json');
if (existsSync(scrutinsEuropeensPath)) {
  cpSync(scrutinsEuropeensPath, path.join(outDir, 'scrutins_europeens.json'));
}

// --- documents_europeens.json (document doceo → matières EuroVoc et leur domaine — #901) ---
// L'axe de la cascade européenne : le domaine EuroVoc de chaque concept d'un
// texte porté. Sans lui, les textes sans dossier restent en « matière non
// établie » ; rien ne se déduit de l'intitulé.
const documentsEuropeensPath = path.join(repoRoot, 'pivot_data', 'documents_europeens.json');
if (existsSync(documentsEuropeensPath)) {
  cpSync(documentsEuropeensPath, path.join(outDir, 'documents_europeens.json'));
} else {
  console.warn(
    `sync-data : ${documentsEuropeensPath} absent — les textes européens sans dossier `
    + 'n\'auront aucun thème (#901). Construire l\'index : '
    + 'python3 src/documents_europeens.py',
  );
}

// --- candidats.json (roster brut : nom, parti, statut) ---
cpSync(candidatsPath, path.join(outDir, 'candidats.json'));
const candidats = JSON.parse(readFileSync(candidatsPath, 'utf-8')).candidats;

// Statuts dont la fiche n'est PAS publiée par l'interface (#761).
//
// Une candidature déclinée cesse d'être une candidature : sa fiche sort de
// l'onglet Candidats, et son profil n'est même pas copié — un fichier servi que
// rien ne référence est du poids mort, et une URL qui répond ferait de la fiche
// masquée une page encore atteignable.
//
// Ce que le masquage NE fait PAS : supprimer quoi que ce soit de `pivot_data/`.
// Le profil reste publié dans le dépôt — ce que la personne a fait au Parlement
// reste vrai, seule sa candidature a cessé — et supprimer un fichier publié est
// une disparition qu'`audit_diff_profils` bloque (#460/#470). Elle reste aussi
// membre de son groupe : les fiches de groupe sont bâties sur `membres[]` et ne
// passent pas par cette liste.
//
// MÊME ENSEMBLE que `STATUTS_GELES` de `src/perimetre_candidats.py`, qui décide
// du périmètre de COLLECTE (#760), et `tests/test_fiches_masquees_761.py` fait
// échouer la suite s'ils divergent. Les deux disent la même chose — « cette
// personne n'est plus candidate » — et les séparer un jour devra être une
// décision écrite, pas une dérive.
export const STATUTS_MASQUES = new Set(['decline']);

const estMasque = (c) => STATUTS_MASQUES.has(c.statut);
const slugsMasques = new Set(candidats.filter(estMasque).map((c) => c.slug));

// --- profils pivot individuels ---
const profileFiles = readdirSync(pivotProfilesDir).filter((f) => f.endsWith('.pivot.json'));
for (const file of profileFiles) {
  const cible = path.join(outDir, 'profiles', file);
  if (slugsMasques.has(file.replace(/\.pivot\.json$/, ''))) {
    // Ce script ne nettoie pas son dossier de sortie : sans cette suppression,
    // le profil copié par une exécution PRÉCÉDENTE resterait servi à son URL, et
    // la fiche « masquée » serait encore atteignable.
    if (existsSync(cible)) rmSync(cible);
    continue;
  }
  cpSync(path.join(pivotProfilesDir, file), cible);
}
const availableSlugs = new Set(
  profileFiles
    .map((f) => f.replace(/\.pivot\.json$/, ''))
    .filter((slug) => !slugsMasques.has(slug)),
);

// `c.slug &&` est retiré (#539) : il datait du jour où un slug valait
// « référencé sur nosdeputes.fr », plateforme hors pipeline depuis #529. Le
// slug est désormais l'identifiant du profil, renseigné pour les 13 candidats
// déclarés — le test ne filtrait donc plus rien de vrai, il ne faisait que
// perpétuer une prémisse fausse. Le manifeste liste les candidats DÉCLARÉS.
//
// `availableSlugs.has(...)` reste, et c'est délibéré : ce script copie les
// fichiers de profil, et un candidat listé sans profil sur disque produirait
// un lien qui casse au clic. Le rendu d'un candidat déclaré sans page relève
// du lot UI #324/#328 ; ici on ne fabrique pas la promesse d'une page absente.
/* ── Qui a siégé à l'Assemblée, ou gouverné (#328) ───────────────────────────
 *
 * La barre des candidats grise les fiches qui ne portent NI mandat à
 * l'Assemblée nationale NI fonction gouvernementale. Ce n'est pas un jugement
 * sur la personne : c'est ce que la fiche peut montrer. Sans l'un des deux, le
 * corpus n'a ni vote, ni intervention, ni amendement à publier — la page existe
 * et le dit, mais elle ne porte pas d'activité parlementaire.
 *
 * DEUX FAITS, ET AUCUN DEVINÉ. `chambres` est le champ DÉRIVÉ des mandats
 * (#493) : il vaut `["PE"]` pour un député européen, et un mandat au Parlement
 * européen n'est pas un mandat à l'Assemblée. `fonction_gouvernementale` est une
 * catégorie de mandat, pas une inférence sur un intitulé.
 *
 * Mesuré sur les 27 candidats déclarés au commit de données courant : 17 ont
 * l'un des deux, 10 n'ont ni l'un ni l'autre — 6 sans aucun mandat collecté
 * (Tondelier, Arthaud, Lisnard, Labib, Verdier, Mathieu) et 4 dont toute la
 * carrière est au Parlement européen (Bardella, Glucksmann, Philippot,
 * Massard). Ségolène Royal, elle, n'a aucun vote publié mais sept fonctions
 * gouvernementales : elle n'est pas grisée, parce que le critère porte sur ce
 * qu'elle a exercé et non sur ce que nous avons collecté.
 */
const aSiegeOuGouverne = (slug) => {
  const profil = JSON.parse(
    readFileSync(path.join(pivotProfilesDir, `${slug}.pivot.json`), 'utf-8'),
  );
  /* `chambres` UNIQUEMENT, jamais le scalaire `chambre` : #328 avait retiré le
   * dernier consommateur de ce scalaire dans l'interface, et le rétablir en
   * repli annulerait la condition de retrait que `test_garde_fou_chambre.py`
   * surveille. Les 19 profils du corpus sans la clé sont tous des
   * `roster_groupe`, jamais listés comme candidats — l'absence retomberait
   * donc sur le seul test de fonction gouvernementale, et le dirait. */
  const chambres = profil.chambres || [];
  const gouvernement = (profil.mandats || []).some(
    (m) => m.categorie === 'fonction_gouvernementale',
  );
  /* UN MANDAT DANS L'UNE DES QUATRE INSTITUTIONS, quelle qu'elle soit
     (arbitrage de la propriétaire, 13/09/2026). `chambres` porte les trois
     assemblées — Assemblée nationale, Sénat, Parlement européen — et la
     quatrième institution est le gouvernement.

     Le critère ne nommait que l'Assemblée et le gouvernement, et grisait donc
     trois fiches qui portent de l'activité : Glucksmann 4 672 entrées,
     Philippot 3 466, Massard 432. La pastille affirmait « ni vote, ni
     intervention, ni amendement » — c'était faux.

     Il reste ce qui a été EXERCÉ, jamais ce que nous avons collecté : c'est ce
     qui garde Ségolène Royal non grisée, sept fonctions gouvernementales et
     aucun vote publié. Mesuré le 13/09/2026 : les 11 fiches grisées portent
     zéro mandat, toutes institutions confondues. */
  return chambres.length > 0 || gouvernement;
};

const manifestCandidates = candidats
  .filter((c) => !estMasque(c) && availableSlugs.has(c.slug))
  .map((c) => ({
    slug: c.slug,
    nom: c.nom,
    parti: c.parti,
    famillePolitique: c.famille_politique,
    statut: c.statut,
    aSiegeOuGouverne: aSiegeOuGouverne(c.slug),
  }))
  /* L'ORDRE EST CELUI DU LIBELLÉ AFFICHÉ, pas celui du fichier source.
   * `raw_data/candidats.json` suit l'ordre de collecte, que rien ne rend
   * lisible : une barre de vingt-cinq pastilles où l'œil ne peut pas prédire
   * la place d'un nom se parcourt en entier à chaque fois. Le tri porte sur
   * `nom` — ce que le lecteur lit — et non sur un patronyme reconstruit :
   * découper « Le Pen » ou « Dupont-Aignan » demanderait une règle que la
   * source ne donne pas. */
  .sort((a, b) => a.nom.localeCompare(b.nom, 'fr', { sensitivity: 'base' }));

// --- profils de groupe réels ---
/* LES GROUPES DU SÉNAT SORTENT DE L'INTERFACE (#885, 13/09/2026).
 *
 * `groupe-Senat-LR` et `groupe-Senat-SER` sont gelés depuis #516 : jamais
 * régénérés, ils étaient conservés parce qu'« une migration ne se paie pas en
 * cassant ce qui est déjà publié »
 * (`docs/decisions/date-de-reference-des-comptes-de-groupe-653.md`). La
 * réouverture partielle du Sénat (#885) tranche l'autre sens : les
 * APPARTENANCES sont collectées, les groupes ne le seront pas.
 *
 * Ce qui restait à l'écran n'était plus une fiche mais une coquille — mesuré le
 * 13/09/2026, après le retrait des 19 profils orphelins (#905) : 0 membre,
 * 0 scrutin de cohésion, 0 mandat agrégé. Deux boutons menaient à deux pages
 * qui ne pouvaient rien dire, et une page vide se lit comme une absence
 * d'activité (§2 règle 5).
 *
 * Le retrait est NOMMÉ au build, comme les fiches masquées : une page qui
 * disparaît en silence est une page qu'on croit encore publiée. */
/* ── LE VOCABULAIRE DES AMENDEMENTS DE CHAQUE CANDIDAT (#1029, voie 2) ────────
 * Les mots des exposés de SES amendements, législature par législature, tirés
 * de `<lég>.contenu.json` : le filtre de la fiche y cherche un sujet que
 * l'intitulé du dossier ne nomme pas. Un fichier par candidat, chargé au
 * premier mot tapé. Une législature à la fois : l'index de la XVe pèse 37 Mo. */
{
  const parLegislature = new Map();
  for (const c of manifestCandidates) {
    const profil = JSON.parse(readFileSync(path.join(pivotProfilesDir, `${c.slug}.pivot.json`), 'utf-8'));
    for (const a of profil.amendements || []) {
      const leg = legislatureDeAmendementId(a?.amendement_id);
      if (!leg) continue;
      if (!parLegislature.has(leg)) parLegislature.set(leg, new Map());
      const fiches = parLegislature.get(leg);
      if (!fiches.has(c.slug)) fiches.set(c.slug, new Set());
      // L'index de contenu porte l'uid AN, sans le préfixe `an:` du pivot.
      fiches.get(c.slug).add(String(a.amendement_id).replace(/^an:/, ''));
    }
  }
  const parCandidat = new Map();
  for (const [leg, fiches] of parLegislature) {
    const chemin = path.join(amendementsDir, `${leg}.contenu.json`);
    if (!existsSync(chemin)) continue;
    const vocabulaires = vocabulairesDesFiches(JSON.parse(readFileSync(chemin, 'utf-8')), fiches);
    for (const [slug, v] of vocabulaires) {
      if (!v.ids.length) continue;
      if (!parCandidat.has(slug)) parCandidat.set(slug, {});
      parCandidat.get(slug)[leg] = v;
    }
  }
  let octets = 0;
  for (const c of manifestCandidates) {
    const cible = path.join(outDir, 'profiles', `${c.slug}.amendements-mots.json`);
    if (!parCandidat.has(c.slug)) {
      if (existsSync(cible)) rmSync(cible);
      continue;
    }
    const texte = JSON.stringify({ legislatures: parCandidat.get(c.slug) });
    octets += Buffer.byteLength(texte);
    writeFileSync(cible, texte);
  }
  console.log(`sync-data : vocabulaire des amendements de ${parCandidat.size} candidat(s) — ${(octets / 1e6).toFixed(1)} Mo écrits.`);
}

const CHAMBRE_HORS_INTERFACE = 'Senat';
const slugByMembreId = new Map(manifestCandidates.map((c) => [c.slug, c]));
const groupeFiles = readdirSync(pivotGroupesDir).filter((f) => f.endsWith('.json'));
const groupesRetires = [];
const manifestGroupes = [];
const fichesPourComparaison = [];
for (const file of groupeFiles) {
  const groupe = JSON.parse(readFileSync(path.join(pivotGroupesDir, file), 'utf-8'));
  const id = file.replace(/^groupe-/, '').replace(/\.json$/, '');
  if (groupe.chambre === CHAMBRE_HORS_INTERFACE) {
    groupesRetires.push(id);
    continue;
  }
  cpSync(path.join(pivotGroupesDir, file), path.join(outDir, 'groupes', file));
  fichesPourComparaison.push({ id, groupe });
  manifestGroupes.push({
    id,
    fichier: file,
    groupeId: groupe.groupe_id,
    sigle: groupe.groupe_sigle,
    nom: groupe.groupe_nom,
    chambre: groupe.chambre,
    legislature: groupe.legislature,
    rosterTotal: groupe.meta?.couverture_roster?.roster_total ?? null,
    // #330 : la fiche de gouvernement nomme le groupe que l'Assemblée DÉCLARE
    // majoritaire pendant sa période. La position et les bornes suffisent — la
    // fiche complète du groupe pèse jusqu'à 500 Ko et n'est pas téléchargée.
    position: groupe.position_politique?.position ?? null,
    debut: groupe.periode?.debut ?? null,
    fin: groupe.periode?.fin ?? null,
  });
  // Rattache chaque candidat au groupe réel dont il est membre (membre_id ->
  // slug), pour permettre le filtrage "Candidats" par "Groupes" côté UI sans
  // avoir à télécharger les fichiers de groupe (certains dépassent 500 Ko).
  for (const membre of groupe.membres || []) {
    const slug = String(membre.membre_id || '').split(':').pop();
    const candidate = slugByMembreId.get(slug);
    if (candidate) {
      if (!candidate.groupIds) candidate.groupIds = [];
      candidate.groupIds.push(id);
    }
  }
}

/* --- LES LIGNÉES : UN BOUTON PAR LIGNÉE DÉCLARÉE --------------------------
 *
 * Le corpus publie une fiche par groupe ET par législature (#700) ; la
 * propriétaire a tranché le 10/09/2026 que l'interface publie une fiche par
 * LIGNÉE. Ces lignées, le backend les DÉCLARE (`lignee_id`, #836) et les écrit
 * dans `pivot_data/lignees/` : ce script les lit, il ne les recalcule plus.
 *
 * Il les recalculait, en chaînant `succede_a`. Deux définitions du même objet,
 * dont l'une ignorait le travail du backend : elles coïncidaient le 11/09/2026
 * (13 lignées de part et d'autre, maillon pour maillon), mais seulement parce
 * qu'aucune scission n'était encore déclarée — `UDR` quittant `DR`, #815, est
 * exactement le cas où une chaîne et une partition déclarée divergent.
 *
 * Les fiches de lignée ne sont PAS copiées : 5 Ko à 7,7 Mo chacune, dont la page
 * lit une fraction. `vue-lignee.mjs` en écrit la projection, une par lignée.
 */
const lignesFiles = existsSync(pivotLigneesDir)
  ? readdirSync(pivotLigneesDir).filter((f) => f.endsWith('.json')).sort()
  : [];
if (lignesFiles.length === 0) {
  console.warn(`sync-data : ${pivotLigneesDir} vide ou absent — aucune page de groupe ne sera servie (#836).`);
}
const idDeFicheParFichier = new Map(manifestGroupes.map((g) => [g.fichier, g.id]));
const ficheParFichier = new Map(fichesPourComparaison.map(({ id, groupe }) => [`groupe-${id}.json`, groupe]));
const manifestLignees = [];
const ligneeDeFiche = new Map();
const ligneesRetirees = [];
for (const file of lignesFiles) {
  const lignee = JSON.parse(readFileSync(path.join(pivotLigneesDir, file), 'utf-8'));
  const id = idDePage(file);
  // La lignée suit ses maillons : sans fiche de groupe, elle n'a rien à publier.
  if (lignee.chambre === CHAMBRE_HORS_INTERFACE) {
    ligneesRetirees.push(id);
    continue;
  }
  const fiches = (lignee.maillons || []).map((m) => idDeFicheParFichier.get(m.fichier)).filter(Boolean);
  for (const f of fiches) ligneeDeFiche.set(f, id);
  manifestLignees.push({
    id,
    fichier: `${id}.json`,
    // Les débats complets, pour la recherche sur la fiche (#979) : chargés
    // seulement quand un mot est tapé.
    debats: `${id}.debats.json`,
    // Ce qui a été dit (#1029) : par maillon, `<maillon>.extraits.index.json`
    // pour le filtre et `<maillon>.extraits.<paquet>.json` pour un débat ouvert.
    extraits: true,
    ligneeId: lignee.lignee_id,
    nom: lignee.lignee_nom,
    chambre: lignee.chambre,
    // Les fiches de groupe de la lignée, du plus ancien au plus récent : le
    // FILTRE des candidats en dépend — sélectionner « Socialistes » retient les
    // membres de n'importe lequel des quatre maillons.
    fiches,
  });
}
for (const g of manifestGroupes) g.lignee = ligneeDeFiche.get(g.id) ?? null;
// Une fiche de groupe qu'aucune lignée ne déclare n'aurait plus de page. Le
// portail le refuse déjà (§4c, #836) ; si elle passait quand même, elle se
// NOMME ici plutôt que de disparaître de l'interface en silence (#510).
const orphelines = manifestGroupes.filter((g) => !g.lignee).map((g) => g.id);
if (orphelines.length) {
  console.warn(`sync-data : ${orphelines.length} fiche(s) de groupe dans aucune lignée déclarée — sans page : ${orphelines.join(', ')}.`);
}
console.log(
  `sync-data : ${manifestGroupes.length} fiches de groupe → ${manifestLignees.length} lignées déclarées.`,
);

// --- comparaisons par législature (#329) ---
// Une projection par (chambre, législature) : sigle, effectif, amendements
// agrégés, position politique déclarée, et les positions majoritaires des seuls
// scrutins où le quorum est atteint. Elle n'est plus SERVIE : la page de lignée
// la lit ici, au build, pour « Avec qui ils votent », et aucune page ne la
// télécharge plus — l'écrire dans public/data serait du poids mort.
const comparaisons = construireComparaisons(fichesPourComparaison);

/* La date la plus récente parmi des fichiers et des répertoires : la clé des
 * deux caches de ce script, `couverture.json` et les vues de lignée. */
const plusRecent = (...chemins) => chemins.reduce((max, c) => {
  if (!existsSync(c)) return max;
  const st = statSync(c);
  if (st.isDirectory()) {
    return readdirSync(c).reduce((m, f) => Math.max(m, statSync(path.join(c, f)).mtimeMs), max);
  }
  return Math.max(max, st.mtimeMs);
}, 0);

// --- vues de lignée (#329) ---
// Une projection par lignée : ce que la page lit, calculé par les MÊMES
// fonctions que le navigateur (`src/utils/groupe.js`, `src/utils/lignee.js`).
// ~1 Mo pour les 13 lignées du 11/09/2026, contre 50 Mo de fiches de lignée.
//
// LE CACHE EST SUR LES DATES, comme `couverture.json` : la répartition des
// amendements par commission relit les profils des membres et les quatre index
// (une minute), et la refaire à chaque `npm run dev` serait insupportable.
/* LA DATE DES DONNÉES (#1074), lue une fois : les extraits (#1029) en tirent
 * les débuts de fenêtre de leur vocabulaire, et `donnees.json` la publie plus
 * bas. Elle est lue LÀ OÙ BACKEND COMPTE SES PROPRES FENÊTRES — la
 * `date_reference.date` des fiches de groupe (#1077), la plus récente. */
const dateDesDonnees = (() => {
  const dates = readdirSync(pivotGroupesDir)
    .filter((f) => f.endsWith('.json'))
    .map((f) => JSON.parse(readFileSync(path.join(pivotGroupesDir, f), 'utf-8'))?.date_reference?.date)
    .filter((d) => typeof d === 'string' && /^\d{4}-\d{2}-\d{2}/.test(d))
    .sort();
  if (dates.length) return dates.at(-1).slice(0, 10);
  return null;
})();
const debutsDesFenetres = dateDesDonnees
  ? { '12m': debutDeFenetre(dateDesDonnees, '12m'), '6m': debutDeFenetre(dateDesDonnees, '6m') }
  : null;

/* Les extraits d'une fiche (#1029) : l'index, que le filtre charge au premier
 * mot, et les paquets non vides, dont un seul se charge quand un débat s'ouvre.
 * Rend le poids écrit, pour le journal du build. */
function ecrireExtraits(dossier, base, { index, paquets }) {
  let octets = 0;
  const ecrire = (nom, contenu) => {
    const texte = JSON.stringify(contenu);
    octets += Buffer.byteLength(texte);
    writeFileSync(path.join(dossier, nom), texte);
  };
  ecrire(`${base}.extraits.index.json`, index);
  paquets.forEach((paquet, k) => {
    if (Object.keys(paquet).length) ecrire(`${base}.extraits.${k}.json`, paquet);
  });
  return octets;
}

const entreesLignees = plusRecent(
  pivotLigneesDir,
  pivotGroupesDir,
  pivotProfilesDir,
  amendementsDir,
  commissionsPath,
  scrutinsPath,
  scrutinsDossiersPath,
  candidatsPath,
  path.join(here, 'vue-lignee.mjs'),
  path.join(here, 'amendements-lignees.mjs'),
  path.join(here, 'comparaison-groupes.mjs'),
  path.join(projectRoot, 'src', 'utils', 'lignee.js'),
  path.join(projectRoot, 'src', 'utils', 'groupe.js'),
  path.join(projectRoot, 'src', 'utils', 'lecture.js'),
  path.join(projectRoot, 'src', 'utils', 'extraits.js'),
  path.join(projectRoot, 'src', 'utils', 'amendementsMots.js'),
);
const vuesAJour = manifestLignees.length > 0 && manifestLignees.every((l) => {
  const f = path.join(outDir, 'lignees', l.fichier);
  const d = path.join(outDir, 'lignees', l.debats);
  const x = path.join(outDir, 'lignees', `${l.id}.extraits.json`);
  return existsSync(f) && statSync(f).mtimeMs >= entreesLignees
    && existsSync(d) && statSync(d).mtimeMs >= entreesLignees
    && existsSync(x) && statSync(x).mtimeMs >= entreesLignees;
});
if (vuesAJour) {
  console.log('sync-data : vues de lignée à jour, reconstruction sautée.');
} else {
  const debut = Date.now();
  let octetsExtraitsLignees = 0;
  const repartitions = repartitionsDesMaillons({
    fiches: ficheParFichier,
    profilesDir: pivotProfilesDir,
    amendementsDir,
    commissionsPath,
    scrutinsDossiersPath,
  });
  // Un écart au total publié se NOMME : la répartition de ce type n'est pas
  // servie, et la page le dira plutôt que d'afficher des barres fausses.
  for (const [fichier, r] of repartitions) {
    for (const e of r.ecarts) {
      console.warn(`sync-data : ${fichier} — ${e.type} recompté ${e.recompte}, publié ${e.attendu} : répartition par commission non servie.`);
    }
  }
  /* LA TABLE DES AMENDEMENTS DE CHAQUE MAILLON (#1029, voie 2) : de quoi
   * recompter la répartition sous un mot — par l'exposé — ou sous une période
   * — par la date de chaque amendement. Chargée au premier mot ou à la première
   * période seulement. */
  let octetsAmendements = 0;
  for (const [fichier, r] of repartitions) {
    const maillon = idDeFicheParFichier.get(fichier);
    if (!maillon || !r.parAmendement) continue;
    const texte = JSON.stringify(r.parAmendement);
    octetsAmendements += Buffer.byteLength(texte);
    writeFileSync(path.join(outDir, 'lignees', `${maillon}.amendements.json`), texte);
  }
  console.log(`sync-data : tables d'amendements des maillons — ${(octetsAmendements / 1e6).toFixed(1)} Mo écrits.`);
  const scrutinsListe = existsSync(scrutinsPath)
    ? Object.values(JSON.parse(readFileSync(scrutinsPath, 'utf-8')).scrutins || {})
    : [];
  const candidatsPublies = new Set(manifestCandidates.map((c) => c.slug));
  // La dernière lecture de chaque texte, choisie par la date sur le corpus
  // ENTIER (#711) : une fois pour les treize lignées.
  const dernieresLectures = new Set(selectDerniereLectureVotes(scrutinsListe).map((s) => s.id));
  const aujourdhui = new Date().toISOString().slice(0, 10);
  for (const entree of manifestLignees) {
    const lignee = JSON.parse(readFileSync(path.join(pivotLigneesDir, `lignee-${entree.id}.json`), 'utf-8'));
    const vue = construireVueLignee({
      fichier: `lignee-${entree.id}.json`,
      lignee,
      fiches: ficheParFichier,
      idsDeFiche: idDeFicheParFichier,
      scrutins: scrutinsListe,
      comparaisons,
      cleDe: cleLegislature,
      candidats: candidatsPublies,
      repartitions,
      ligneeDeFiche,
      nomsDesLignees: new Map(manifestLignees.map((l) => [l.id, l.nom])),
      dernieresLectures,
      aujourdhui,
    });
    writeFileSync(path.join(outDir, 'lignees', entree.fichier), JSON.stringify(vue));
    const debats = construireDebatsLignee({
      fichier: `lignee-${entree.id}.json`,
      lignee,
      fiches: ficheParFichier,
      idsDeFiche: idDeFicheParFichier,
    });
    writeFileSync(path.join(outDir, 'lignees', entree.debats), JSON.stringify(debats));
    // Ce qui a été dit (#1029), maillon par maillon. Le témoin
    // `<lignée>.extraits.json` nomme les maillons servis ; il est écrit en
    // dernier, pour qu'un build interrompu se refasse.
    const extraits = construireExtraitsLignee({
      lignee,
      fiches: ficheParFichier,
      idsDeFiche: idDeFicheParFichier,
      lireProfil: lecteurDeProfils(pivotProfilesDir, { cache: false }),
      debuts: debutsDesFenetres,
    });
    for (const [maillon, x] of Object.entries(extraits)) {
      octetsExtraitsLignees += ecrireExtraits(path.join(outDir, 'lignees'), maillon, x);
    }
    writeFileSync(path.join(outDir, 'lignees', `${entree.id}.extraits.json`), JSON.stringify({ maillons: Object.keys(extraits) }));
  }
  console.log(`sync-data : extraits de parole des lignées — ${(octetsExtraitsLignees / 1e6).toFixed(1)} Mo écrits.`);
  console.log(`sync-data : ${manifestLignees.length} vues de lignée écrites en ${((Date.now() - debut) / 1000).toFixed(1)} s.`);
}

/* ── CE QUE L'EXÉCUTIF A FAIT ENTRER EN VIGUEUR (#1029 voie 1) ──────────────
 *
 * 238 fichiers mensuels, 389 000 actes : ils sont lus UNE SEULE FOIS, et
 * chaque acte est rangé dans les gouvernements dont la fenêtre le couvre. Une
 * passe par gouvernement relirait 197 Mo dix-sept fois.
 *
 * Les fichiers eux-mêmes ne sont pas copiés vers `public/` : seule la
 * projection l'est, un fichier par gouvernement.
 */
function projeterLesActes(gouvernements) {
  if (!existsSync(actesDir)) return { par: new Map(), lus: 0 };
  const textes = (() => {
    const chemin = path.join(repoRoot, 'pivot_data', 'textes_promulgues.json');
    if (!existsSync(chemin)) return {};
    const doc = JSON.parse(readFileSync(chemin, 'utf-8'));
    const par = {};
    for (const t of Object.values(doc.textes || {})) if (t.numero_loi) par[t.numero_loi] = t;
    return par;
  })();
  const acc = accumulateurs(gouvernements);
  let lus = 0;
  for (const fichier of readdirSync(actesDir).filter((f) => f.endsWith('.json')).sort()) {
    const doc = JSON.parse(readFileSync(path.join(actesDir, fichier), 'utf-8'));
    const natures = doc.natures || [];
    const ministeres = doc.ministeres || [];
    const ids = doc.ids || [];
    // Le rangement du sommaire du JO (#1134), aligné sur `ids` et non sur la
    // ligne d'`actes` : la forme d'une ligne n'a pas bougé.
    const rubriques = doc.rubriques || [];
    const rubriqueDesActes = doc.rubrique_des_actes || [];
    (doc.actes || []).forEach((ligne, i) => {
      lus += 1;
      const r = rubriqueDesActes[i];
      ranger(acc, {
        date: ligne[2],
        titre: ligne[1] || '',
        ministere: ligne[3] === null || ligne[3] === undefined ? null : ministeres[ligne[3]],
        id: ids[i],
        nature: natures[ligne[0]],
        rubrique: r === null || r === undefined ? null : rubriques[r],
      });
    });
  }
  const par = new Map();
  for (const a of acc) par.set(a.id, projection(a, textes));
  return { par, lus };
}

// --- profils de gouvernement réels ---
const debutParoles = Date.now();
let sujetsEcrits = 0;
let octetsExtraitsGouvernements = 0;
const gouvernementFiles = readdirSync(pivotGouvernementsDir).filter((f) => f.endsWith('.json'));
const manifestGouvernements = [];
const debutActes = Date.now();
const fenetres = gouvernementFiles.map((file) => {
  const g = JSON.parse(readFileSync(path.join(pivotGouvernementsDir, file), 'utf-8'));
  return {
    id: file.replace(/^gouvernement-/, '').replace(/\.json$/, ''),
    debut: g.periode?.debut ?? null,
    fin: g.periode?.fin ?? null,
  };
});
const { par: actesParGouvernement, lus: actesLus } = projeterLesActes(fenetres);
let octetsActes = 0;
for (const file of gouvernementFiles) {
  cpSync(path.join(pivotGouvernementsDir, file), path.join(outDir, 'gouvernements', file));
  const gouvernement = JSON.parse(readFileSync(path.join(pivotGouvernementsDir, file), 'utf-8'));
  const id = file.replace(/^gouvernement-/, '').replace(/\.json$/, '');
  const lireProfil = lecteurDeProfils(pivotProfilesDir);
  const paroles = construireParoles(gouvernement, lireProfil);
  sujetsEcrits += Object.keys(paroles).length;
  writeFileSync(path.join(outDir, 'gouvernements', `${id}.paroles.json`), JSON.stringify(paroles));
  // Ce que l'exécutif a fait entrer en vigueur (#1029 voie 1).
  const actes = actesParGouvernement.get(id);
  if (actes) {
    const cible = path.join(outDir, 'gouvernements', `${id}.actes.json`);
    const contenu = JSON.stringify(actes);
    writeFileSync(cible, contenu);
    octetsActes += contenu.length;
  }
  // Ce qui a été dit (#1029) : les extraits des membres, pendant leurs fonctions.
  octetsExtraitsGouvernements += ecrireExtraits(
    path.join(outDir, 'gouvernements'), id,
    construireExtraitsGouvernement(gouvernement, lireProfil, debutsDesFenetres),
  );

  manifestGouvernements.push({
    id,
    fichier: file,
    gouvernementId: gouvernement.gouvernement_id,
    nom: gouvernement.nom,
    debut: gouvernement.periode?.debut ?? null,
    fin: gouvernement.periode?.fin ?? null,
    actif: gouvernement.periode?.actif ?? false,
    // #328 : la fiche de profil doit savoir de QUELS gouvernements la personne
    // a été membre avant d'en télécharger un seul (les dix pèsent 580 Ko).
    // L'appariement se fait ici, une fois, sur `membre_id` — le même champ que
    // pour les groupes, quelques lignes plus haut.
    membreIds: [...new Set((gouvernement.membres || []).map((m) => m.membre_id).filter(Boolean))],
    // #330 : le détail d'un sujet de parole — qui, quand, où le vérifier.
    // Chargé au premier clic, jamais avec la fiche : 2,6 Mo sur Borne.
    paroles: `${id}.paroles.json`,
    // #1029 voie 1 : ce que l'exécutif a fait entrer en vigueur, chargé au
    // déploiement de la section et pas avec la fiche (0,4 Mo).
    actes: actesParGouvernement.has(id) ? `${id}.actes.json` : null,
    // #1029 : ce qui a été dit, par débat — `<id>.extraits.index.json` pour le
    // filtre, `<id>.extraits.<paquet>.json` pour un débat ouvert.
    extraits: id,
  });
}
manifestGouvernements.sort((a, b) => (b.debut || '').localeCompare(a.debut || ''));

console.log(
  `sync-data : ${sujetsEcrits} sujets de parole de gouvernement écrits en `
  + `${((Date.now() - debutParoles) / 1000).toFixed(1)} s ; extraits : ${(octetsExtraitsGouvernements / 1e6).toFixed(1)} Mo.`,
);
console.log(
  `sync-data : ${actesLus.toLocaleString('fr-FR')} actes réglementaires lus une fois, `
  + `projetés sur ${actesParGouvernement.size} gouvernement(s) — ${(octetsActes / 1e6).toFixed(1)} Mo écrits `
  + `en ${((Date.now() - debutActes) / 1000).toFixed(1)} s.`,
);

/* ── Ce que le dépôt porte, tous profils confondus (/couverture) ────────────
 *
 * Une projection au build, comme les comparaisons de groupe (#329) : elle ne
 * crée aucun fait, elle compte ce que `pivot_data/` porte déjà et le range par
 * institution. En faire une huitième sortie du pivot ajouterait un job, un
 * cache et un budget CI pour un fichier que seule l'interface lit.
 *
 * LE CACHE EST SUR LES DATES, PAS SUR UN DRAPEAU. La lecture des quatre index
 * d'amendements (141 Mo) coûte une trentaine de secondes : la refaire à chaque
 * `npm run dev` rendrait le démarrage insupportable, et la sauter sans regarder
 * les entrées servirait un corpus périmé après un run de données. On compare
 * donc la date du fichier produit à la plus récente des entrées.
 */
const couverturePath = path.join(outDir, 'couverture.json');
const entreesCouverture = plusRecent(
  pivotProfilesDir,
  pivotGroupesDir,
  pivotGouvernementsDir,
  scrutinsPath,
  scrutinsDossiersPath,
  commissionsPath,
  amendementsDir,
  path.join(here, 'couverture-corpus.mjs'),
);
if (!existsSync(couverturePath) || statSync(couverturePath).mtimeMs < entreesCouverture) {
  const debut = Date.now();
  writeFileSync(
    couverturePath,
    JSON.stringify(construireCouverture({ repoRoot, slugsPublies: availableSlugs })),
  );
  console.log(`sync-data : couverture.json reconstruit en ${((Date.now() - debut) / 1000).toFixed(1)} s.`);
} else {
  console.log('sync-data : couverture.json à jour, reconstruction sautée.');
}

writeFileSync(
  path.join(outDir, 'manifest.json'),
  JSON.stringify(
    { candidates: manifestCandidates, groupes: manifestGroupes, lignees: manifestLignees, gouvernements: manifestGouvernements },
    null,
    2,
  ),
);

console.log(`sync-data : ${manifestCandidates.length} candidat(s), ${manifestGroupes.length} groupe(s), ${manifestGouvernements.length} gouvernement(s) copiés vers public/data/.`);
if (slugsMasques.size) {
  // Nommés, jamais seulement comptés : une fiche retirée de l'interface doit se
if (groupesRetires.length || ligneesRetirees.length) {
  console.log(
    `sync-data : ${groupesRetires.length} fiche(s) de groupe et ${ligneesRetirees.length} lignée(s) `
    + `retirées de l'interface — ${[...groupesRetires, ...ligneesRetirees].join(', ')} `
    + '(groupes du Sénat, hors périmètre #885 ; fichiers conservés dans pivot_data/).',
  );
}
  // distinguer d'une fiche qu'on a oublié de produire (#510).
  console.log(`sync-data : ${slugsMasques.size} fiche(s) masquée(s) — ${[...slugsMasques].join(', ')} (statut masqué, profil conservé dans pivot_data/).`);
}

/* ── LA DATE DES DONNÉES (#1074) ───────────────────────────────────────────────
 * Les cases « 6 derniers mois » et « 12 derniers mois » se comptent depuis
 * elle, pas depuis le jour. Elle est lue LÀ OÙ BACKEND COMPTE SES PROPRES
 * FENÊTRES : la `date_reference.date` des fiches de groupe (#1077), la plus
 * récente. Une seule date pour toutes les fiches — sinon deux fiches
 * afficheraient « depuis le » à deux dates différentes.
 * Sans aucune date lisible, le fichier n'est pas écrit : les cases ne
 * filtrent alors rien, plutôt que de compter depuis une date inventée. */
{
  if (dateDesDonnees) {
    const au = dateDesDonnees;
    writeFileSync(path.join(outDir, 'donnees.json'), JSON.stringify({ au }));
    console.log(`sync-data : données au ${au} — les fenêtres de période se comptent depuis cette date.`);
  } else {
    console.log('sync-data : aucune date de référence lisible — donnees.json non écrit, les cases de période ne filtrent rien.');
  }
}
