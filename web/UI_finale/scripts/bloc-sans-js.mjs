/*
 * LE TEXTE QU'UN ROBOT LIT SANS JAVASCRIPT (#969, arbitré le 17/09/2026).
 *
 * Mesuré en production le 17/09/2026, après #1002 : le corps d'une fiche servie
 * contient 0 caractère. Tout est construit par React. Google exécute le
 * JavaScript ; les robots des modèles de langage (GPTBot, ClaudeBot,
 * PerplexityBot) en général non — ils ne lisaient donc que le titre et la
 * description, environ 180 caractères par fiche.
 *
 * Ce module écrit, DANS le conteneur de l'application, les faits déjà publiés :
 * mandats et fonctions avec leurs dates et leur source, composition d'un
 * gouvernement, groupes d'une lignée. L'application remplace ce contenu dès
 * qu'elle démarre — une personne dont le JavaScript est bloqué le lit tel quel.
 *
 * RIEN N'EST ÉCRIT À LA MAIN : le bloc est refait à chaque build, depuis les
 * mêmes fichiers que les pages. Un nouveau candidat déclaré a le sien ; une
 * candidature déclinée n'a plus de page du tout (#761).
 *
 * CE QU'IL NE PORTE PAS, sur avis de la session backend et de §2 :
 * aucun compte d'activité (votes, amendements, interventions), qui se lirait
 * comme un indicateur de performance dans un extrait de moteur (règle 1) ;
 * aucun `meta.avertissements`, qui porte un destinataire et peut viser l'agent
 * de collecte ; aucun `notableCount` (§6, interne) ; aucun statut de texte,
 * tant que #997 n'a pas tranché ce que « déposé » veut dire.
 *
 * DEUX PIÈGES DE DONNÉES, tenus par des tests :
 * - `fin` peut être absente sur un mandat TERMINÉ (mandats locaux, #922/#966) :
 *   la période se lit sur `actif`, jamais sur la présence de `fin`, sinon un
 *   extrait de moteur affiche « en cours » sur une fonction achevée ;
 * - la collecte des mandats locaux COMMENCE EN 2020 (AGENTS.md §7) : une fiche
 *   sans mandat le dit avec cette limite, et n'écrit jamais « aucun mandat ».
 */

const CATEGORIES_PUBLIEES = ['mandat_electif', 'fonction_gouvernementale', 'mandat_local'];

function ech(texte) {
  return String(texte ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function jour(date) {
  return /^\d{4}-\d{2}-\d{2}/.test(date || '') ? `${date.slice(8, 10)}/${date.slice(5, 7)}/${date.slice(0, 4)}` : null;
}

/* `actif` fait foi. Une fin absente sur un mandat terminé est une donnée
 * manquante, qui se dit (§2 règle 5), jamais un mandat en cours. */
export function periode({ debut, fin, actif }) {
  const d = jour(debut);
  const f = jour(fin);
  if (actif) return d ? `depuis le ${d}` : 'en cours';
  if (d && f) return `du ${d} au ${f}`;
  if (d) return `à partir du ${d}, terminé — date de fin non publiée`;
  return 'dates non publiées';
}

function source(url) {
  return url ? ` · <a href="${ech(url)}">source</a>` : ' · source non publiée';
}

function pied(date, aussi) {
  return `<p>Faits publiés le ${ech(jour(date) || date)}. Cette fiche publie aussi, avec JavaScript, ${aussi}.`
    + ' <a href="/sources">Sources et couverture</a> · <a href="/methodologie">Méthode éditoriale</a></p>';
}

export function blocCandidat(entree, profil, dateDuBuild) {
  const mandats = (profil.mandats || [])
    .filter((m) => CATEGORIES_PUBLIEES.includes(m.categorie))
    .sort((a, b) => (b.debut || '').localeCompare(a.debut || ''));
  const corps = mandats.length
    ? `<h2>Mandats et fonctions</h2><ul>${mandats
      .map((m) => `<li>${ech(m.label)} — ${periode(m)}${source(m.source_url)}</li>`).join('')}</ul>`
    : "<p>Aucun mandat n'est publié sur cette fiche. La collecte des mandats locaux commence en 2020 :"
      + " une absence avant cette date n'est pas une absence de mandat.</p>";
  return `<h1>${ech(entree.nom)}</h1>`
    + `<p>Candidature déclarée à l'élection présidentielle de 2027${entree.parti ? ` · ${ech(entree.parti)}` : ''}</p>`
    + corps
    + pied(dateDuBuild, 'les votes, les textes portés, les amendements et les interventions');
}

const CHAMBRE_EN_TOUTES_LETTRES = { AN: "à l'Assemblée nationale", Senat: 'au Sénat', PE: 'au Parlement européen' };

export function blocLignee(vue, dateDuBuild) {
  const ou = CHAMBRE_EN_TOUTES_LETTRES[vue.chambre];
  if (!ou) throw new Error(`${vue.id} : chambre sans libellé — ${vue.chambre}`);
  const quand = periode({ debut: vue.periode?.debut, fin: vue.periode?.fin, actif: !vue.periode?.fin });
  const combien = Number.isFinite(vue.cumul) ? ` · ${vue.cumul} personnes y ont siégé` : '';
  const maillons = (vue.maillons || [])
    .map((m) => `<li>${ech(m.nom)}${m.legislature ? ` — ${ech(m.legislature)}<sup>e</sup> législature` : ''}</li>`)
    .join('');
  return `<h1>${ech(vue.nom)}</h1>`
    + `<p>Groupe ${ou} · ${quand}${combien}</p>`
    + (maillons ? `<h2>Groupes de la lignée</h2><ul>${maillons}</ul>` : '')
    + pied(dateDuBuild, 'les votes du groupe, ses amendements et ses débats');
}

export function blocGouvernement(profil, dateDuBuild) {
  const membres = profil.membres || [];
  const liste = membres
    .map((m) => `<li>${ech(m.nom)}${m.portefeuille ? ` — ${ech(m.portefeuille)}` : ''} · ${periode(m)}</li>`)
    .join('');
  return `<h1>${ech(profil.nom)}</h1>`
    + `<p>${periode({ ...profil.periode })} · ${membres.length} membres</p>`
    + (liste ? `<h2>Composition</h2><ul>${liste}</ul>` : '')
    + pied(dateDuBuild, 'les textes portés par le gouvernement');
}

/* Le bloc vit DANS le conteneur de l'application : au démarrage, React le
 * remplace par la page rendue. Hors du conteneur, il resterait affiché deux
 * fois. */
export function avecBloc(html, bloc) {
  const vide = '<div id="root"></div>';
  if (!html.includes(vide)) throw new Error('index.html ne porte plus <div id="root"></div>');
  return html.replace(vide, `<div id="root">${bloc}</div>`);
}
