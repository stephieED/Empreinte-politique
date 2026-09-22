// Les amendements de chaque maillon, par commission saisie au fond (#329).
//
// La fiche de lignée reprend le gabarit « amendements par matière » de la fiche
// candidat. Les fiches de groupe publient les totaux par type de déposant, pas
// la matière : elle se reconstitue ici, au build, depuis les `amendements[]`
// des membres, l'index par législature et `commissions_dossiers.json` — par la
// règle écrite UNE fois dans `src/utils/lignee.js` (`repartitionParCommission`).
//
// LE CONTRÔLE, ET CE QU'IL DÉCIDE. Chaque type de déposant recompté est comparé
// à `amendements_agreges.par_type_deposant[type].nb_amendements` de la fiche.
// Un écart n'est pas arrondi : la répartition de ce type n'est PAS publiée pour
// ce maillon, et le script le nomme. 28 maillons AN sur 28 retombaient au
// chiffre près le 11/09/2026.
//
// UNE LÉGISLATURE À LA FOIS. L'index de la XVe pèse 72 Mo : les quatre chargés
// ensemble, plus les profils, reconstruiraient l'empreinte que #377 a payée.
// Chaque profil n'est lu qu'une fois par législature, et seul l'ensemble des
// identifiants retenus survit à sa lecture.

import { readFileSync, existsSync } from 'node:fs';
import path from 'node:path';
import { legislatureDeAmendementId } from '../src/utils/lecture.js';
import { TYPES_DEPOSANT_GROUPE, qualiteDuRole, repartitionParCommission, textesDuMaillon } from '../src/utils/lignee.js';
import { vocabulairesDesFiches } from '../src/utils/amendementsMots.js';

const lire = (p) => JSON.parse(readFileSync(p, 'utf-8'));

/**
 * `fiches` : Map `fichier` → fiche de groupe. Rend une Map `fichier` →
 * `{ types, ecarts }`, où `types` ne porte que les types vérifiés.
 */
export function repartitionsDesMaillons({ fiches, profilesDir, amendementsDir, commissionsPath, scrutinsDossiersPath }) {
  const commissions = existsSync(commissionsPath) ? (lire(commissionsPath).commissions || {}) : null;
  const resultat = new Map();
  if (!commissions) return resultat;
  const commissionDuDossier = (dossier) => commissions[dossier] ?? null;
  // Le sort d'un TEXTE, quand un scrutin le rattache à son dossier (#758).
  const statuts = scrutinsDossiersPath && existsSync(scrutinsDossiersPath)
    ? (lire(scrutinsDossiersPath).dossiers || {})
    : {};
  const statutDuDossier = (dossier) => statuts[dossier]?.statut ?? null;

  const parLegislature = new Map();
  for (const [fichier, groupe] of fiches) {
    const leg = groupe.legislature == null ? null : String(groupe.legislature);
    if (!leg || groupe.chambre !== 'AN') continue;
    if (!parLegislature.has(leg)) parLegislature.set(leg, []);
    parLegislature.get(leg).push({ fichier, groupe, ids: new Set(), textes: [] });
  }

  for (const [leg, maillons] of parLegislature) {
    const indexPath = path.join(amendementsDir, `${leg}.json`);
    if (!existsSync(indexPath)) continue;

    const maillonsDe = new Map();
    for (const m of maillons) {
      for (const membre of m.groupe.membres || []) {
        if (!maillonsDe.has(membre.membre_id)) maillonsDe.set(membre.membre_id, []);
        maillonsDe.get(membre.membre_id).push(m);
      }
    }
    for (const [membreId, siens] of maillonsDe) {
      const profilPath = path.join(profilesDir, `${membreId}.pivot.json`);
      if (!existsSync(profilPath)) continue;
      const profil = lire(profilPath);
      for (const a of profil.amendements || []) {
        if (legislatureDeAmendementId(a?.amendement_id) !== leg) continue;
        for (const m of siens) m.ids.add(a.amendement_id);
      }
      // Les textes portés, lus dans la même passe : même population, même
      // règle de législature (`textesDuMaillon`, utils/lignee.js).
      for (const t of profil.textes_portes || []) {
        if (t?.legislature == null || String(t.legislature) !== leg || !qualiteDuRole(t.role)) continue;
        for (const m of siens) m.textes.push(t);
      }
    }

    const index = lire(indexPath);
    // Le contenu des exposés (#1029, voie 2), s'il est publié pour cette
    // législature : le vocabulaire de chaque maillon, sur ses seuls amendements.
    const contenuPath = path.join(amendementsDir, `${leg}.contenu.json`);
    const vocabulaires = existsSync(contenuPath)
      // L'index de contenu porte l'uid AN, sans le préfixe `an:` du pivot.
      ? vocabulairesDesFiches(lire(contenuPath), new Map(maillons.map((m) => [m.fichier, new Set([...m.ids].map((id) => id.replace(/^an:/, '')))])))
      : new Map();
    for (const m of maillons) {
      const { types } = repartitionParCommission(m.ids, index.amendements, index.textes, commissionDuDossier, statutDuDossier);
      const publie = m.groupe.amendements_agreges?.par_type_deposant || {};
      const verifies = {};
      const ecarts = [];
      for (const type of TYPES_DEPOSANT_GROUPE) {
        const attendu = publie[type]?.nb_amendements ?? 0;
        const recompte = types[type]?.amendements ?? 0;
        if (recompte !== attendu) ecarts.push({ type, recompte, attendu });
        else if (types[type]) verifies[type] = types[type];
      }
      resultat.set(m.fichier, {
        types: verifies,
        ecarts,
        textes: textesDuMaillon(m.textes, commissionDuDossier),
        parAmendement: tableDesAmendements(m.ids, index, commissionDuDossier, statutDuDossier, vocabulaires.get(m.fichier)),
      });
    }
  }
  return resultat;
}

/* ── LA TABLE DES AMENDEMENTS D'UN MAILLON (#1029, voie 2) ────────────────────
 *
 * De quoi RECOMPTER la répartition sous un mot ou une période, par la même
 * règle (`repartitionParCommission`) : pour chaque amendement distinct du
 * maillon, son type de déposant, son sort adopté ou non, sa date et le texte
 * visé ; pour chaque texte, son dossier, son titre, sa commission et le sort du
 * texte. Plus, quand l'exposé est indexé, le vocabulaire (`mots`) renuméroté sur
 * `ids`. La page ne la charge qu'au premier mot ou à la première période.
 *
 * `rows[i]` : `[type (rang dans types), adopté (0/1), date, texte (rang dans textes)]`.
 * `textes[j]` : `[texte_vise, dossier_id, titre, commission (sigle ou nom), statut]`. */
function tableDesAmendements(ids, index, commissionDuDossier, statutDuDossier, vocabulaire) {
  const types = [];
  const rangType = new Map();
  const textes = [];
  const rangTexte = new Map();
  const liste = [...ids].filter((id) => index.amendements?.[id]).sort();
  const rows = liste.map((id) => {
    const a = index.amendements[id];
    const type = a.type_deposant || 'inconnu';
    if (!rangType.has(type)) { rangType.set(type, types.length); types.push(type); }
    let t = null;
    if (a.texte_vise) {
      if (!rangTexte.has(a.texte_vise)) {
        const dossier = index.textes?.[a.texte_vise]?.dossier_id ?? null;
        const c = dossier ? commissionDuDossier(dossier) : null;
        rangTexte.set(a.texte_vise, textes.length);
        textes.push([a.texte_vise, dossier, index.textes?.[a.texte_vise]?.titre ?? null,
          c ? (c.sigle || c.nom || null) : null, dossier ? statutDuDossier(dossier) : null]);
      }
      t = rangTexte.get(a.texte_vise);
    }
    return [rangType.get(type), a.sort === 'adopté' ? 1 : 0, a.date ?? null, t];
  });
  return { ids: liste, types, rows, textes, vocabulaire: vocabulaire ?? null };
}
