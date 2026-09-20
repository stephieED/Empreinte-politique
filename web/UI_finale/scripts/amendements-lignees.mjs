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
      resultat.set(m.fichier, { types: verifies, ecarts, textes: textesDuMaillon(m.textes, commissionDuDossier) });
    }
  }
  return resultat;
}
