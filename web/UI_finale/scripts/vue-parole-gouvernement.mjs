/*
 * LA PROJECTION DE PAROLE D'UN GOUVERNEMENT — qui a parlé, quand, et où le
 * vérifier (#330).
 *
 * La fiche affiche les sujets depuis `tags_thematiques_agreges`, publié sur le
 * pivot. Ce fichier-ci porte le DÉTAIL d'un sujet, que le pivot ne publie pas :
 * pour chaque intitulé de débat, LES MEMBRES qui y sont intervenus, avec la
 * date de leur première et de leur dernière prise de parole.
 *
 * UNE LIGNE PAR MEMBRE, PAS PAR PRISE DE PAROLE. Une intervention de la source
 * est un tour de parole : sur la motion de censure de décembre 2023, la
 * première version de ce fichier rendait 857 lignes, dont trente-quatre fois
 * « 21 décembre 2023 · Élisabeth Borne ». L'ordre est ALPHABÉTIQUE et jamais
 * par volume : classer les ministres par nombre de tours de parole fabriquerait
 * un indice d'activité (§2 règle 1).
 *
 * POURQUOI UNE PROJECTION, ET PAS UNE LECTURE DIRECTE. Le détail vit dans les
 * profils des membres — jusqu'à 55 fichiers par gouvernement, plusieurs Mo
 * chacun. La fiche en téléchargerait des dizaines pour afficher dix lignes.
 * Même geste que `vue-lignee.mjs` pour les débats d'une lignée (#979).
 *
 * CE QUE LA PROJECTION NE PORTE PAS : le verbatim. Les membres de gouvernement
 * sont collectés en mode réduit au thème (`meta.collecte_reduite`), et leurs
 * interventions n'ont pas de texte — mesuré le 20/09/2026 : `texte` n'existe
 * que sur les profils de candidats déclarés. La fiche dit donc QUI a parlé et
 * OÙ le lire, jamais ce qui a été dit.
 *
 * LA FENÊTRE EST CELLE DE CHAQUE MEMBRE, pas celle du gouvernement — même
 * règle que l'agrégat qu'elle détaille (#1020) : Yaël Braun-Pivet, ministre
 * trois jours puis présidente de l'Assemblée, n'apporte que ces trois jours.
 */
import { readFileSync } from 'node:fs';
import path from 'node:path';

/* LA CLÉ EST CELLE DE L'AGRÉGAT, PAS LE LIBELLÉ BRUT. `deriver_tags_thematiques`
   (schema_pivot.py) range un thème en `theme.strip().lower()`, et c'est cette
   forme que `tags_thematiques_agreges` publie. Keyer la projection sur le
   libellé brut donnait zéro correspondance : « Plan national maladies rares »
   contre « plan national maladies rares ». */
function cleDeSujet(intervention) {
  const theme = intervention.theme_officiel;
  if (typeof theme === 'string' && theme.trim()) return theme.trim().toLowerCase();
  return null;
}

/* La source publie le compte rendu en ARCHIVE (`syseron.xml.zip`), pas au
   paragraphe : un lien vers 100 Mo de zip n'atteste rien pour un lecteur. On
   ne garde que les adresses qui mènent à un document lisible. */
function lienLisible(url) {
  if (typeof url !== 'string' || !url) return null;
  if (/syceronbrut|syseron|\.zip($|\?)/i.test(url)) return null;
  return url;
}

/** Les fenêtres d'exercice de chaque membre, par `membre_id`. */
function fenetresParMembre(gouvernement) {
  const fin = gouvernement.periode?.fin || null;
  const fenetres = new Map();
  for (const membre of gouvernement.membres || []) {
    if (!membre.membre_id || !membre.debut) continue;
    const liste = fenetres.get(membre.membre_id) || [];
    liste.push({
      debut: membre.debut,
      fin: membre.fin || fin || '9999-12-31',
      nom: membre.nom,
      portefeuille: membre.portefeuille || null,
    });
    fenetres.set(membre.membre_id, liste);
  }
  return fenetres;
}

/* EN QUALITÉ DE QUOI LA PERSONNE A PARLÉ. La source ne le dit pas sur
   l'intervention — `fonction` est vide sur les 4 213 entrées d'Élisabeth Borne —,
   mais le portefeuille qu'elle exerçait CE JOUR-LÀ est publié par l'Assemblée.
   On le LIT dans la fenêtre qui contient la date ; on ne le devine pas. Onze
   membres du gouvernement Borne en ont tenu deux successivement : ils portent
   deux lignes, chacune avec son intitulé et ses dates. */
function fenetreDe(date, fenetres) {
  return fenetres.find((f) => date >= f.debut && date <= f.fin) || null;
}

/**
 * Construit `{ [intitulé de débat]: [{ membre, premiere, derniere, tours, types }] }` pour un
 * gouvernement. `lireProfil` est injecté pour que la fonction reste testable
 * sans disque.
 */
export function construireParoles(gouvernement, lireProfil) {
  const fenetres = fenetresParMembre(gouvernement);
  const parSujet = new Map();

  for (const [membreId, fenetresDuMembre] of fenetres) {
    const profil = lireProfil(membreId);
    if (!profil) continue;
    const nom = fenetresDuMembre[0]?.nom || profil.nom || membreId;

    for (const intervention of profil.interventions || []) {
      const date = intervention.date;
      const sujet = cleDeSujet(intervention);
      // Un intitulé absent n'est pas un sujet vide : l'intervention n'entre
      // pas, et « Ce qu'on n'a pas pu lire » porte la limite (§2 règle 5).
      const fenetre = date ? fenetreDe(date, fenetresDuMembre) : null;
      if (!sujet || !date || !fenetre) continue;

      const parMembre = parSujet.get(sujet) || new Map();
      const cle = `${nom}\u0000${fenetre.portefeuille || ''}`;
      const connu = parMembre.get(cle) || {
        membre: nom,
        portefeuille: fenetre.portefeuille,
        premiere: date,
        derniere: date,
        tours: 0,
        types: new Set(),
        url: null,
      };
      connu.tours += 1;
      if (date < connu.premiere) connu.premiere = date;
      if (date > connu.derniere) connu.derniere = date;
      if (intervention.type_detail) connu.types.add(intervention.type_detail);
      connu.url = connu.url || lienLisible(intervention.source_url);
      parMembre.set(cle, connu);
      parSujet.set(sujet, parMembre);
    }
  }

  const sujets = {};
  for (const [sujet, parMembre] of parSujet) {
    sujets[sujet] = [...parMembre.values()]
      .map((e) => ({
        membre: e.membre,
        portefeuille: e.portefeuille,
        premiere: e.premiere,
        derniere: e.derniere,
        tours: e.tours,
        types: [...e.types].sort(),
        url: e.url,
      }))
      /* DEUX NIVEAUX, arbitrés par la propriétaire le 20/09/2026 : la DATE de
         la dernière prise de parole d'abord, décroissante — le débat le plus
         récent d'abord —, puis le nombre de tours, décroissant. L'ordre
         alphabétique retenu la veille est abandonné.
         Ce que ça ne publie pas : aucun total, aucun rang affiché, et rien qui
         rapporte ce nombre à un possible — ce serait un taux (§2 règle 3). */
      .sort((a, b) => b.derniere.localeCompare(a.derniere)
        || b.tours - a.tours
        || a.membre.localeCompare(b.membre, 'fr'));
  }
  return sujets;
}

/** La même chose, en lisant les profils sur disque, un par un — les garder
 *  tous en mémoire a coûté un OOM au pipeline (#635). */
export function construireParolesDepuisDisque(gouvernement, dossierProfils) {
  const cache = new Map();
  return construireParoles(gouvernement, (membreId) => {
    if (!cache.has(membreId)) {
      const chemin = path.join(dossierProfils, `${membreId}.pivot.json`);
      try {
        const profil = JSON.parse(readFileSync(chemin, 'utf-8'));
        cache.set(membreId, { nom: profil.nom, interventions: profil.interventions || [] });
      } catch {
        cache.set(membreId, null);
      }
    }
    return cache.get(membreId);
  });
}
