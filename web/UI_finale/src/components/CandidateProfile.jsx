/*
 * La fiche d'un candidat déclaré — lot 2 de la refonte #324 (issue #328).
 *
 * Sept sections, identiques pour les treize candidats déclarés, toujours dans
 * le même ordre. Ce qui varie est le contenu, jamais la forme — et chaque
 * emplacement est rempli à hauteur de ce que la donnée porte : uniformiser la
 * forme ne veut pas dire niveler le contenu.
 *
 * Ce composant REND. Les règles vivent dans `utils/profilCandidat.js` (#328),
 * les six fondations communes dans `utils/lecture.js` (#326) : les couleurs de
 * vote, les ratios, les troncatures, les listes vides et les badges de source
 * sont importés, jamais redéfinis. C'est exactement la duplication que le
 * lot 1 a supprimée.
 */
import '../styles/shell.css';
import './CandidateProfile.css';
import { BadgeSource, ListeVide } from './Lecture';
import { EtiquetteFiltre, MOT, VideDuFiltre } from './Recherche';
import { teinteMatiere, teinteThemeUe } from '../utils/matiere';
import { MATIERE_NON_ETABLIE, NATURES_UE } from '../utils/profilCandidat';
import { Cascade, ListeCascade } from './CascadeTextes';
import { cascadeDessinee, disposerCascadeUE, selectionDeTousLesTextes } from '../utils/cascadeTextes';
import { Fragment, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { LAST_READING_LABEL, formatNumber } from '../utils/lecture';
import { LIBELLE_QUALITE, QUALITE_AN, QUALITE_PE } from '../utils/parolesParPeriode';
import ParolesParPeriode from './ParolesParPeriode';
import VotesParPeriode from './VotesParPeriode';
import EcartsGroupe from './EcartsGroupe';
import {
  CAS_RIEN_A_MONTRER,
  INSTITUTION_GOUVERNEMENT,
  INSTITUTION_LOCAL,
  INSTITUTION_MISSION,
  INSTITUTION_PARLEMENT,
  INSTITUTION_PE,
  INSTITUTION_SENAT,
  LIBELLE_PISTE,
  pisteDuRole,
  libellePosition,
  motifPosition,
  positionSurAxe,
} from '../utils/profilCandidat';

const MOIS = [
  'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
  'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre',
];

function jour(iso) {
  if (!iso) return null;
  const [a, m, j] = iso.split('-');
  if (!a) return null;
  if (!m) return a;
  return `${Number(j)} ${MOIS[Number(m) - 1]} ${a}`;
}

function annee(iso) {
  return iso ? iso.slice(0, 4) : null;
}

function periode(debut, fin, actif) {
  if (actif) return `depuis le ${jour(debut)}`;
  return `${jour(debut)} → ${jour(fin)}`;
}

/* La période d'un rôle du parcours. Un mandat local achevé n'a pas de date de
 * fin publiée : sa borne est la date où la source l'atteste, et l'écrire comme
 * une fin la ferait passer pour un fait (§2 règle 5). */
function periodeDuRole(r) {
  if (r.finNonPubliee) return `${jour(r.debut)} → fin non publiée`;
  return periode(r.debut, r.fin, r.actif);
}

/*
 * Un en-tête de section : son numéro, son titre, et le critère qui dit ce que
 * la section montre ET ce qu'elle refuse de montrer. Le critère est du contenu
 * publié, pas une légende décorative — c'est lui qui empêche de lire un
 * décompte comme une note.
 */
/* `id` et `data-section` : c'est par eux que `SommaireSections` LIT la page, au
 * lieu de recevoir une liste. Le sommaire sert ainsi les trois types de fiche
 * sans qu'aucune ait à le connaître, et une section ajoutée y apparaît d'elle-
 * même. L'ancre est dérivée du NUMÉRO, pas du titre : un titre change avec la
 * voix du texte (« ce qu'il » / « ce qu'elle »), un lien partagé ne doit pas. */
function Section({ numero, titre, critere, pied, children }) {
  return (
    <section className="cp-section" id={`section-${numero}`} data-section={titre}>
      <div className="cp-section-bande">
        <span className="cp-section-numero">{numero}</span>
        <span className="cp-section-trait" />
      </div>
      <h2 className="cp-section-titre"><span>{titre}</span></h2>
      {critere && <p className="cp-section-critere">{critere}</p>}
      <div className="cp-section-corps">{children}</div>
      {/* Le pied porte la règle de lecture APRÈS le contenu, jamais avant : une
          section qui s'annonce avant qu'on ait rien lu fait lire la consigne à
          la place du fait. C'est aussi ce qui a fait retirer le critère d'en-tête
          de cette section-ci. */}
      {pied && <p className="cp-section-pied">{pied}</p>}
    </section>
  );
}

/* ── Le filtre par intitulé (#979) ───────────────────────────────────────────
 *
 * UNE BARRE EN TÊTE DE FICHE, et la fiche se recalcule sur ce que le mot porte
 * (`vueCandidat`). Arbitré sur maquette le 17/09/2026 :
 *
 * - « En bref », « Les fonctions exercées » et « Ce qu'on n'a pas pu lire » se
 *   RETIRENT tant qu'un mot est tapé : recalculé, « En bref » publiait « 259
 *   amendements sur 4 dossiers » sur « finances » ; une section non filtrée
 *   entre des sections filtrées se lirait comme filtrée ; la couverture
 *   décrirait les lacunes du filtre, pas celles de la collecte ;
 * - chaque figure porte le mot EN TÊTE (`EtiquetteFiltre`, « Contenant « … » »), pour qu'une capture
 *   de la figure seule ne circule pas sans lui ;
 * - les listes se DÉPLIENT sans clic ;
 * - un mot qui ne trouve rien laisse la section EN PLACE, avec un message du
 *   filtre (`VideDuFiltre`) — jamais le message d'une collecte vide, « Non
 *   collecté », qui serait faux (§2 règle 5). */

/*
 * Une pastille de position déclarée. Elle accompagne TOUJOURS le chiffre
 * qu'elle explique, jamais renvoyée en légende de bas de page : « 1 968
 * déposés, 67 adoptés » doit porter « groupe déclaré d'opposition » sur la même
 * ligne, sinon le lecteur lit une incompétence là où il y a une fonction.
 */
function Position({ position }) {
  const motif = motifPosition(position);
  return (
    <span className={`cp-position cp-position--${motif}`}>{libellePosition(position)}</span>
  );
}

/* ── § 1 — le parcours ───────────────────────────────────────────────────────
 *
 * UNE seule bande, une ligne par rôle, ordonnées par date de début, quelle que
 * soit l'institution : rien n'est au-dessus parce que c'est la date qui range.
 * La bande ne porte AUCUN texte — un libellé dans un segment de 2 % ne tient
 * pas, quelle que soit sa position. Des repères numérotés la surmontent et la
 * liste dessous porte les intitulés complets : la frise donne la silhouette, la
 * liste la nomme.
 */
const ECART_MINIMAL_REPERES = 3.4;

/* CE QUI S'ÉCRIT DANS UN SEGMENT, ET CE QUI N'Y TIENT PAS.
 *
 * La bande ne portait aucun texte : « un libellé dans un segment de 2 % ne tient
 * pas ». C'est vrai du libellé complet, pas de tout libellé — un mandat de cinq
 * ans occupe un tiers de la frise et peut porter son groupe. L'étiquette se
 * DÉGRADE donc au lieu de disparaître : le plus long qui tient, puis le groupe
 * seul, puis rien — et la liste datée dessous continue de tout nommer.
 *
 * Largeur estimée à 820 px : la colonne fait 1 020 px au plus large, moins la
 * marge intérieure de la carte, et moins ce que le sommaire prend à gauche ;
 * sous-estimer fait taire une étiquette qui aurait tenu, surestimer la fait
 * déborder. On sous-estime. */
const LARGEUR_BANDE_ESTIMEE = 820;
const POSITION_COURTE = {
  majorite: 'majoritaire',
  opposition: 'opposition',
  minoritaire: 'minoritaire',
};

/* LES CANDIDATES D'UNE ÉTIQUETTE, de la plus complète à la plus courte. La
 * première qui tient est écrite ; si aucune ne tient, le segment reste nu et la
 * liste datée dessous fait le travail. Rien n'est tronqué en milieu de mot :
 * « Secrétariat d'État auprès du mini… » ne dit pas mieux que rien. */
function candidatesEtiquette(role) {
  if (role.institution === INSTITUTION_GOUVERNEMENT) {
    // `detail` porte « Ministère de l'intérieur · gouvernement BARNIER » : le
    // portefeuille d'abord — le gouvernement est déjà dans la liste datée —,
    // puis sa tête avant « auprès de » ou « chargé de », puis la fonction.
    const portefeuille = (role.detail || '').split(' · ')[0] || '';
    // « Ministère » tout court ne dit rien — on garde la tête seulement quand
    // elle porte encore un rang, comme « Secrétariat d'État ».
    const tete = portefeuille.split(/ aupr[èe]s | charg[ée] /)[0].replace(/,$/, '');
    const court = /^minist[èe]re$/i.test(tete) ? null : tete;
    return [portefeuille, role.role, court].filter(Boolean);
  }
  if (role.institution === INSTITUTION_MISSION) return [role.role];
  // Un mandat local : la collectivité, puis la fonction — « Cannes » se lit
  // dans un segment de trois mois, « Maire · Cannes » dans un plus long.
  if (role.institution === INSTITUTION_LOCAL) {
    return [role.detail && `${role.role} · ${role.detail}`, role.detail, role.role].filter(Boolean);
  }

  // Un siège : LE SIGLE DU GROUPE ET LA PLACE DANS L'HÉMICYCLE, et rien d'autre
  // (maquette « En bref », 11/09/2026). La fonction se lit sur la couleur et la
  // légende, le nom complet du groupe au survol et dans la liste datée. Sans
  // sigle établi (`sigleDuSiege`) — un groupe européen, un groupe du Sénat —,
  // le segment se tait plutôt que de répéter la légende.
  const position = POSITION_COURTE[role.position] || null;
  const sigle = role.sigle ?? null;
  const candidates = [];
  if (sigle && position) candidates.push(`${sigle} · ${position}`);
  if (sigle) candidates.push(sigle);
  if (position) candidates.push(position);
  return candidates;
}

function etiquetteSegment(role, largeur) {
  const place = (largeur / 100) * LARGEUR_BANDE_ESTIMEE;
  for (const texte of candidatesEtiquette(role)) {
    if (texte.length * 6.2 + 16 <= place) return texte;
  }
  return null;
}

/* LES ANNÉES SOUS LA BANDE. Deux bornes ne situent rien au milieu : un segment
 * qui commence au tiers de la frise ne se date qu'en comptant. Le pas est choisi
 * pour rendre entre quatre et huit repères, quelle que soit la carrière — deux
 * ans pour Glucksmann, dix pour une carrière de quarante ans. */
function anneesDeLAxe(bornes) {
  const debut = Number(annee(bornes.debut));
  const fin = Number(annee(bornes.fin));
  if (!debut || !fin || fin <= debut) return [];
  const pas = [1, 2, 5, 10, 20].find((p) => (fin - debut) / p <= 7) ?? 25;
  const annees = [];
  for (let a = Math.ceil(debut / pas) * pas; a <= fin; a += pas) annees.push(a);
  /* Les deux bornes sont toujours écrites ; un repère rond trop proche d'elles
   * s'efface à leur profit. Depuis que l'axe s'arrête aujourd'hui, « 2025 » et
   * « 2026 » se chevauchaient au bout de chaque frise au pas de cinq ans. */
  const loinDesBornes = annees.filter((a) => a - debut >= pas * 0.3 && fin - a >= pas * 0.3);
  return [debut, ...loinDesBornes, fin];
}

function classeInstitution(role) {
  if (role.institution === INSTITUTION_MISSION) return 'cp-fs--mission';
  if (role.institution === INSTITUTION_GOUVERNEMENT) {
    return role.chef ? 'cp-fs--chef' : 'cp-fs--gouvernement';
  }
  // LA FRISE DIT L'INSTITUTION, ET RIEN D'AUTRE. Elle portait aussi la
  // qualification du groupe — majoritaire, opposition, minoritaire, non
  // déclarée — par quatre motifs. Deux encodages sur la même bande, dont un que
  // la légende devait expliquer : la qualification reste écrite en toutes
  // lettres dans la liste des rôles, à côté du mandat qu'elle qualifie, et
  // c'est là qu'elle se lit sans décodeur.
  return `cp-fs--${pisteDuRole(role)}`;
}

/* La légende ne montre QUE ce que la frise porte, et la frise ne porte plus que
 * l'institution : les quatre motifs de qualification de groupe sont retirés avec
 * elle. Chaque entrée dit à quelle piste elle appartient, et seules les pistes
 * présentes sur la fiche sont rendues — elle listait sept entrées partout, dont
 * quatre motifs de groupe sur des profils qui n'ont jamais siégé à l'Assemblée. */
const LEGENDE_FRISE = [
  { piste: INSTITUTION_PARLEMENT, classe: 'cp-fs--parlement', label: 'Député(e)' },
  { piste: INSTITUTION_SENAT, classe: 'cp-fs--senat', label: 'Sénateur(rice)' },
  { piste: INSTITUTION_PE, classe: 'cp-fs--pe', label: 'Député(e) européen(ne)' },
  { piste: INSTITUTION_GOUVERNEMENT, classe: 'cp-fs--gouvernement', label: 'Membre du gouvernement' },
  { piste: INSTITUTION_GOUVERNEMENT, classe: 'cp-fs--chef', label: 'Chef du gouvernement' },
  { piste: INSTITUTION_MISSION, classe: 'cp-fs--mission', label: 'Parlementaire en mission auprès d’un ministère' },
  // L'ASTÉRISQUE RENVOIE AU PIED D'« EN BREF » : les mandats locaux ne sont
  // publiés qu'à partir de 2020, et le répertoire ne porte que le mandat en
  // cours. Sans le renvoi, un segment de six mois se lit comme une expérience
  // de six mois (arbitré le 16/09/2026).
  { piste: INSTITUTION_LOCAL, classe: 'cp-fs--local', label: 'Mandat local', renvoi: true },
];

function Frise({ parcours }) {
  const { roles, nbLignes, bornes } = parcours;
  if (!roles.length || !bornes) return null;
  /* LA LÉGENDE LIT LES CLASSES DESSINÉES, PAS LES PISTES. « Membre du
   * gouvernement » et « Chef du gouvernement » partagent la piste
   * `gouvernement` : filtrer sur elle affichait « Chef du gouvernement » sur
   * toute fiche de ministre, sans un seul segment jaune. Une entrée de légende
   * n'a de sens que si sa teinte est à l'écran. */
  const classesDessinees = new Set(roles.map(classeInstitution));

  const hauteurLigne = 100 / nbLignes;

  // Repères : un numéro par rôle. Repliés sur un second niveau quand deux
  // débuts sont trop proches pour ne pas se chevaucher.
  const niveaux = [-Infinity, -Infinity];
  const reperes = roles.map((r) => {
    const x = positionSurAxe(r.debut, bornes);
    let n = 0;
    if (x - niveaux[0] < ECART_MINIMAL_REPERES) n = x - niveaux[1] < ECART_MINIMAL_REPERES ? 0 : 1;
    niveaux[n] = x;
    return { numero: r.numero, x, niveau: n };
  });
  const deuxNiveaux = reperes.some((r) => r.niveau === 1);

  return (
    <div className="cp-carte cp-frise">
      <div className="cp-reperes" style={{ height: deuxNiveaux ? 46 : 30 }}>
        {reperes.map((r) => (
          <span
            className="cp-repere"
            key={r.numero}
            style={{ left: `${r.x.toFixed(2)}%`, top: r.niveau === 0 ? 0 : '38%', height: r.niveau === 0 ? '100%' : '62%' }}
          >
            <b>{r.numero}</b>
            <i />
          </span>
        ))}
      </div>

      <div className="cp-bande" style={{ height: Math.max(46, nbLignes * 24) }}>
        {roles.map((r) => {
          const gauche = positionSurAxe(r.debut, bornes);
          const largeur = Math.max(0.6, positionSurAxe(r.fin, bornes) - gauche);
          return (
            <span
              className={`cp-fs ${classeInstitution(r)}`}
              key={r.numero}
              style={{
                left: `${gauche.toFixed(2)}%`,
                width: `${largeur.toFixed(2)}%`,
                top: `${(r.ligne * hauteurLigne).toFixed(2)}%`,
                height: `${hauteurLigne.toFixed(2)}%`,
              }}
              title={`${r.role}${r.detail ? ` · ${r.detail}` : ''} — ${periodeDuRole(r)}`}
            >
              {etiquetteSegment(r, largeur)}
            </span>
          );
        })}
      </div>

      <div className="cp-axe">
        {anneesDeLAxe(bornes).map((a) => (
          <span key={a} style={{ left: `${positionSurAxe(`${a}-01-01`, bornes).toFixed(2)}%` }}>
            {a}
          </span>
        ))}
      </div>

      <div className="cp-legende">
        <div className="cp-legende-grille">
          {LEGENDE_FRISE.filter((l) => classesDessinees.has(l.classe)).map((l) => (
            <span className="cp-legende-item" key={l.label}>
              <span className={`cp-legende-pave ${l.classe}`} />
              {/* Le libellé et son renvoi dans UN SEUL élément : l'entrée de
                  légende est un flex à `gap: 9px`, et un astérisque posé à côté
                  du texte devenait un second enfant, écarté de neuf pixels. */}
              <span>
                {l.label}
                {l.renvoi && <sup className="cp-legende-renvoi" aria-hidden="true">*</sup>}
              </span>
            </span>
          ))}
        </div>
      </div>

      {/* Le détail daté se replie : c'est du DÉTAIL, et il n'a pas à s'imposer
          entre la frise et ce qui suit. Même poignée que le bloc « Les grands
          chiffres » — deux plis de même nature ne prennent pas deux formes. */}
      <details className="cp-pli">
        <summary className="cp-poignee">
          <i className="cp-poignee-plus" aria-hidden="true" />
          Détails du parcours
        </summary>
      <ul className="cp-roles">
        {roles.map((r) => (
          <li className="cp-role" key={r.numero}>
            <span className="cp-role-numero">{r.numero}</span>
            <span className="cp-role-dates">{periodeDuRole(r)}</span>
            <span className="cp-role-intitule">
              <b>{r.role}</b>
              {/* La qualification du groupe est publiée PAR L'ASSEMBLÉE : la
                  porter sur un mandat européen ou sénatorial ferait dire à
                  l'Assemblée qu'elle n'a rien déclaré sur un siège dont elle ne
                  parle pas (§2 règle 2). */}
              {pisteDuRole(r) === INSTITUTION_PARLEMENT && <Position position={r.position} />}
              {r.detail && <span className="cp-role-detail"> · {r.detail}</span>}
            </span>
          </li>
        ))}
      </ul>
      </details>
    </div>
  );
}

/*
 * Un intitulé, coupé à DEUX lignes quand il déborde.
 *
 * Une seule ligne perdait trop : les commissions d'enquête portent des intitulés
 * de plus de 200 caractères, et la moitié du sens y passait. À deux lignes, plus
 * aucun ne déborde en pleine largeur ; c'est en écran étroit que la coupe sert.
 *
 * Le « … » est un VRAI bouton, pas un `text-overflow` : il faut pouvoir
 * l'atteindre au clavier et qu'un lecteur d'écran annonce qu'il déplie. C'est
 * aussi pourquoi la coupe est franche plutôt qu'un `-webkit-line-clamp`, qui
 * peindrait ses propres points et en afficherait deux.
 *
 * Il n'apparaît QUE sur ce qui déborde vraiment, et ça se mesure — poser
 * l'affordance partout apprendrait au lecteur à ne plus cliquer. La mesure se
 * refait au redimensionnement : la place disponible décide, pas le texte.
 */
function Intitule({ label, roles }) {
  const ligne = useRef(null);
  const [deborde, setDeborde] = useState(false);
  const [deplie, setDeplie] = useState(false);

  useLayoutEffect(() => {
    let attente = 0;
    const mesurer = () => {
      const el = ligne.current;
      if (el) setDeborde(el.scrollHeight > el.clientHeight + 1);
    };
    const auRedimensionnement = () => {
      clearTimeout(attente);
      attente = setTimeout(mesurer, 120);
    };
    mesurer();
    window.addEventListener('resize', auRedimensionnement);
    return () => {
      clearTimeout(attente);
      window.removeEventListener('resize', auRedimensionnement);
    };
  }, [label, roles]);

  return (
    <span className="cp-fonctions-objet">
      <span className="cp-fonctions-ligne" ref={ligne} data-deplie={deplie ? '' : undefined}>
        {label}
        {roles && <span className="cp-fonctions-role"> · {roles}</span>}
      </span>
      {deborde && (
        <button
          type="button"
          className="cp-fonctions-plus"
          aria-expanded={deplie}
          onClick={() => setDeplie((o) => !o)}
        >
          {deplie ? 'Replier l’intitulé' : '…'}
        </button>
      )}
    </span>
  );
}

/*
 * Les fonctions qu'on choisit d'exercer — ce que la section publie désormais en
 * entier, la frise et le détail daté vivant tous deux dans « En bref ».
 *
 * Un bloc par catégorie, JAMAIS un total : un groupe d'amitié et une commission
 * d'enquête ne s'additionnent pas. Chaque bloc montre ses trois plus longues, et
 * le filet marque celle qui dépasse la moitié du temps de mandat — deux états,
 * jamais une graduation. Le reste vit sous un pli, avec sa durée.
 *
 * La marque est SANS TEINTE, et ce n'est pas un oubli : aucune couleur n'était
 * libre. Le jaune signal est pris par la sélection, l'action et le badge de
 * source ; le vert et le rouge par les positions de vote ; le bleu et le bronze
 * par les institutions dans la frise. En ajouter une quatrième aurait dilué les
 * trois autres — et l'encre reste lisible en niveaux de gris et sous daltonisme,
 * sans avoir à doubler la marque d'un pictogramme.
 */
function Fonctions({ fonctions }) {
  if (!fonctions || !fonctions.blocs.length) return null;
  return (
    <div className="cp-carte cp-fonctions">
      {fonctions.blocs.map((b) => {
        const marquee = b.montrees.some((e) => e.marquee);
        // Le BANC porte la couleur, pas la catégorie. Neuf catégories auraient
        // demandé neuf teintes, en concurrence avec la seule grammaire de
        // couleurs de la fiche — et sur un profil qui a connu les deux bancs,
        // c'est le banc qu'on aurait perdu. Ce qui sépare une commission d'un
        // groupe d'amitié est écrit en toutes lettres dans le titre du bloc :
        // la marque ne le remplace pas.
        return (
          <div className={`cp-fonctions-bloc cp-fonctions-bloc--${b.banc}`} key={b.cle}>
            {/* Le dénominateur vit dans le titre, pas sous chaque ligne : c'est
                une constante du profil, et la répéter en faisait un refrain. Il
                n'apparaît QUE là où une ligne est marquée — c'est elle qui
                affirme « plus de la moitié », donc elle seule doit ses deux
                nombres (§2 règle 7). */}
            <p className="cp-fonctions-titre">
              {b.titre} · <span className="cp-num">{formatNumber(b.nbIntitules)}</span>{' '}
              {b.nbIntitules > 1 ? 'intitulés' : 'intitulé'}
              {marquee && ` · sur ${fonctions.mandat.duree} de mandat`}
            </p>

            <ul className="cp-fonctions-liste">
              {b.montrees.map((e) => (
                <li
                  className={`cp-fonctions-item${e.marquee ? ' cp-fonctions-item--marquee' : ''}`}
                  key={e.label}
                >
                  <span className="cp-fonctions-duree cp-num">{e.duree}</span>
                  <Intitule label={e.label} roles={e.roles} />
                </li>
              ))}
            </ul>

            {b.reste.length > 0 && (
              <details className="cp-pli cp-pli--fonctions">
                <summary className="cp-poignee">
                  <i className="cp-poignee-plus" aria-hidden="true" />
                  {formatNumber(b.reste.length)} {b.reste.length > 1 ? 'autres' : 'autre'}
                </summary>
                <div className="cp-puces">
                  {b.reste.map((e) => (
                    <span className="cp-puce" key={e.label}>
                      {e.label}
                      {e.roles && <span className="cp-fonctions-role"> · {e.roles}</span>}
                      <b className="cp-num">{e.duree}</b>
                    </span>
                  ))}
                </div>
              </details>
            )}
          </div>
        );
      })}
    </div>
  );
}

/* ── LES MATIÈRES, DEUX MESURES ET LEUR RAPPORT ─────────────────────────────
 *
 * REMPLACE LA CASCADE PAR ANNÉE. Celle-ci empilait les matières sur un axe du
 * temps, avec un bouton pour basculer entre « amendements déposés » et
 * « dossiers amendés » : deux lectures qu'il fallait faire l'une après l'autre,
 * et dont le rapport — le seul fait intéressant — n'apparaissait jamais.
 *
 * Le volume seul ne fait rien ressortir : il suit le calendrier de l'Assemblée,
 * et Finances arrive en tête pour à peu près tout le monde. Le classement
 * S'INVERSE dès qu'on compte les textes. Les deux mesures sont donc côte à côte,
 * avec le ratio AU MILIEU — c'est le terme qui les relie, pas une conclusion
 * posée au bout.
 *
 * CE RAPPORT N'EST NI UNE PERFORMANCE NI UN JUGEMENT. C'est une densité, et elle
 * porte ses deux termes : elle ne se compare à aucune moyenne, ne se normalise
 * par aucun effectif, et n'est jamais un taux d'adoption (§6). Aucune colonne
 * n'est mise en avant — un ratio sans ses deux termes n'est rien.
 *
 * UN NOMBRE PAR COLONNE. Empilés dans une même cellule, « 26 775 » et « 59 » se
 * lisaient « 26 77559 », et se copiaient ainsi.
 *
 * « Matière non établie » garde sa ligne, en gris et sans ratio : un dossier
 * dont la commission n'est pas résolue n'a pas de dénominateur, et lui en
 * inventer un le ferait disparaître dans les autres (§2 règle 5).
 */
function Matieres({ chute, matiere, onMatiere, ue = false }) {
  const rang = useMemo(
    () => new Map(chute.matieres.map((m, i) => [m, i])),
    [chute.matieres],
  );
  const lignes = useMemo(() => chute.matieres
    .filter((m) => m !== MATIERE_NON_ETABLIE)
    .map((m) => ({
      m,
      amdt: chute.totauxDepots[m] || 0,
      textes: chute.totauxDossiers[m] || 0,
    }))
    .filter((x) => x.amdt > 0)
    .sort((a, b) => b.amdt - a.amdt), [chute]);
  const nd = {
    amdt: chute.totauxDepots[MATIERE_NON_ETABLIE] || 0,
    textes: chute.totauxDossiers[MATIERE_NON_ETABLIE] || 0,
  };
  if (!lignes.length && !nd.amdt) return null;
  const maxA = Math.max(...lignes.map((x) => x.amdt), nd.amdt, 1);
  const maxD = Math.max(...lignes.map((x) => (x.textes ? x.amdt / x.textes : 0)), 1);

  return (
    <div className="cp-mat">
      <div className="cp-mr cp-mr--tete">
        <span className="cp-mr-lib" />
        <span />
        <span className="cp-mr-n">amendements</span>
        <span className="cp-mr-n">ratio par texte</span>
        <span />
        <span className="cp-mr-n">textes distincts</span>
      </div>
      {lignes.map((x) => {
        const dens = x.textes ? x.amdt / x.textes : null;
        const teinte = ue ? teinteThemeUe(x.m, rang.get(x.m)) : teinteMatiere(x.m, rang.get(x.m));
        return (
          <button
            aria-pressed={matiere === x.m}
            className="cp-mr cp-mr--cliquable"
            key={x.m}
            onClick={() => onMatiere(x.m)}
            type="button"
          >
            <span className="cp-mr-lib">{x.m}</span>
            <span className="cp-mr-rail">
              <i style={{ background: teinte, width: `${(x.amdt / maxA) * 100}%` }} />
            </span>
            <span className="cp-mr-n">{formatNumber(x.amdt)}</span>
            <span className="cp-mr-n">{dens == null ? '—' : formatNumber(Math.round(dens))}</span>
            <span className="cp-mr-rail">
              {dens != null && (
                <i style={{ background: teinte, opacity: 0.5, width: `${(dens / maxD) * 100}%` }} />
              )}
            </span>
            <span className="cp-mr-n cp-mr-n--textes">{formatNumber(x.textes)}</span>
          </button>
        );
      })}
      {nd.amdt > 0 && (
        <div className="cp-mr cp-mr--nd">
          <span className="cp-mr-lib">{MATIERE_NON_ETABLIE}</span>
          <span className="cp-mr-rail">
            <i style={{ background: '#dcd8d2', width: `${(nd.amdt / maxA) * 100}%` }} />
          </span>
          <span className="cp-mr-n">{formatNumber(nd.amdt)}</span>
          <span className="cp-mr-n">—</span>
          <span />
          <span className="cp-mr-n cp-mr-n--textes">{formatNumber(nd.textes) || '—'}</span>
        </div>
      )}
    </div>
  );
}

/* ── § 3 — ce qu'il a proposé ────────────────────────────────────────────── */

/* La cascade procédurale et sa liste vivent dans `CascadeTextes.jsx` depuis
 * #329 : la fiche de lignée dessine la même figure. */

/*
 * L'ORDRE DE LA SECTION EST CELUI DES DEUX POPULATIONS, ET IL S'EMBOÎTE.
 *
 * D'abord ce que sont devenus les textes dont il est l'AUTEUR ou le
 * RAPPORTEUR ; ensuite les amendements qu'il a déposés sur les textes DES
 * AUTRES. Deux populations distinctes, jamais additionnées, et la première
 * éclaire la seconde.
 *
 * CE QUE CETTE SECTION N'AFFICHE PLUS, ET POURQUOI C'EST DIT ICI. La barre des
 * sorts d'amendement par législature, qui portait la position déclarée du
 * groupe, a été retirée : la maquette validée ne la porte pas. Le fait n'est
 * pas perdu — `amendements.legislatures[].position` reste calculé, et la
 * remettre est une carte à écrire, pas une donnée à recollecter.
 */
/* ── Le commutateur des textes portés (#901) ─────────────────────────────────
 *
 * DEUX VERSANTS, JAMAIS ADDITIONNÉS. Un texte porté à l'Assemblée et une
 * proposition de résolution déposée au Parlement européen ne se comptent pas
 * ensemble : les stades n'ont ni la même nomenclature ni la même échelle, et
 * « 5 publiés » sur un total qui mêle les deux ne veut rien dire.
 *
 * LE COMMUTATEUR N'APPARAÎT QUE SI LES DEUX VERSANTS PORTENT QUELQUE CHOSE.
 * Quatre des six fiches à mandat européen n'ont aucun texte français ; un
 * bouton qui ne mène qu'à une liste vide est du mobilier, et la carte dit alors
 * d'elle-même de quel parlement elle parle.
 */
/* ── LE COMMUTATEUR DE VERSANT (#901, arbitré le 17/09/2026) ─────────────────
 *
 * IL PORTE LES MOTS ET LA FORME DE « CE QU'IL A DIT » — pastille de
 * l'institution, étiquette, effectif après un point médian. La fiche compte
 * déjà un commutateur qui distingue les deux parlements, celui des
 * interventions : en inventer un second vocabulaire aurait fait lire deux
 * mécaniques différentes là où il n'y en a qu'une. Les classes viennent donc de
 * `ParolesParPeriode.css`, et la puce n'est PAS redéfinie ici : une seule
 * définition de l'objet (#672).
 */
function CommutateurVersant({ ue, onFr, onUe, compteFr, compteUe, libelle }) {
  return (
    <div className="pp-qualites" role="group" aria-label={libelle}>
      <button aria-pressed={!ue} className="pp-qualite pp-qualite--an" onClick={onFr} type="button">
        <i aria-hidden="true" />
        {LIBELLE_QUALITE[QUALITE_AN]}
        <span>· {formatNumber(compteFr)}</span>
      </button>
      <button aria-pressed={ue} className="pp-qualite pp-qualite--pe" onClick={onUe} type="button">
        <i aria-hidden="true" />
        {LIBELLE_QUALITE[QUALITE_PE]}
        <span>· {formatNumber(compteUe)}</span>
      </button>
    </div>
  );
}

function Propositions({ amendements, amendementsParVersant, amendementsUe, textes, causeAmendements, causeTextes, voix, filtre = null }) {
  const mot = filtre?.mot || '';
  const [matiere, setMatiere] = useState(null);
  const [selTexte, setSelTexte] = useState(null);
  const europe = textes.europe || { total: 0, publies: 0, cascade: null };
  const deuxVersants = textes.total > 0 && europe.total > 0;
  const [versant, setVersant] = useState(textes.total > 0 ? 'fr' : 'ue');
  // Une sélection est un intervalle de crans : elle ne veut rien dire sur
  // l'autre échelle, et la garder ouvrirait une liste sans rapport.
  const [nature, setNature] = useState('tous');
  // Le filtre par nature des dossiers amendés au Parlement européen (#901).
  const [natureAmdt, setNatureAmdt] = useState('tous');
  const changerVersant = (v) => {
    setVersant(v);
    setSelTexte(null);
    setNature('tous');
    // « Finances » et « Legal Affairs » ne vivent pas dans le même référentiel :
    // garder la matière choisie ouvrirait une liste de dossiers sans rapport.
    setMatiere(null);
    setNatureAmdt('tous');
  };
  const ue = versant === 'ue' || (!deuxVersants && textes.total === 0);
  /* LE FILTRE PAR NATURE (#901, arbitré le 17/09/2026) : une sous-cascade par
   * nature, calculée sur ses seuls textes. Il ne s'affiche que si la fiche porte
   * au moins deux natures — une seule redirait « Toutes natures ». */
  const naturesPresentes = ue && europe.parNature
    ? NATURES_UE.filter((n) => europe.parNature[n.cle]?.total > 0)
    : [];
  const filtreNature = naturesPresentes.length > 1;
  const choisirNature = (n) => {
    setNature(n);
    setSelTexte(null);
  };
  const cascade = ue
    ? (filtreNature && nature !== 'tous' ? europe.parNature[nature].cascade : europe.cascade)
    : textes.cascade;
  const choisirMatiere = (m) => setMatiere((a) => (a === m ? null : m));
  /* UN SEUL VERSANT POUR TOUTE LA SECTION, COMMANDÉ DEPUIS DEUX ENDROITS. Les
   * amendements suivent les textes portés : le commutateur du haut et celui
   * posé au-dessus des amendements règlent le même état, pour qu'on puisse
   * changer de parlement sans remonter d'un écran. */
  const amdtFr = amendementsParVersant?.francais || amendements;
  const amdtUe = amendementsParVersant?.europeens || { totalAuteur: 0 };
  const deuxVersantsAmdt = amdtFr.totalAuteur > 0 && amdtUe.totalAuteur > 0;
  const commutateur = deuxVersants || deuxVersantsAmdt;
  const amdt = ue ? amdtUe : amdtFr;
  /* LE FILTRE PAR NATURE DES AMENDEMENTS EUROPÉENS (#901) : les puces des
   * textes portés, sur les dossiers amendés. Comme pour les textes, il ne
   * s'affiche que si la fiche porte au moins deux natures, et une procédure
   * hors des quatre natures reste comptée dans « Toutes natures ». */
  const naturesAmdt = ue && amendementsUe
    ? NATURES_UE.filter((n) => amendementsUe.depotsParNature[n.cle] > 0)
    : [];
  const filtreNatureAmdt = naturesAmdt.length > 1;
  const figureAmdt = ue && amendementsUe
    ? (filtreNatureAmdt && natureAmdt !== 'tous' ? amendementsUe.parNature[natureAmdt] : amendementsUe.figure)
    : amdt;
  /* Sous un mot, la liste des dossiers est dépliée sur toutes les matières
   * (#979) : la fiche réduite se lit sans chercher la matière du bon dossier. */
  const dossiersDeLaMatiere = matiere || mot
    ? (matiere
        ? (figureAmdt.chute?.dossiersParMatiere?.[matiere] || [])
        : Object.values(figureAmdt.chute?.dossiersParMatiere || {}).flat())
        .slice()
        .sort((a, b) => b.n - a.n)
    : [];
  /* Une cascade non dessinée, ou un mot tapé : la liste montre tous les textes
   * sans attendre de clic (#979). Un clic dans la cascade reste une sélection. */
  const disposer = ue ? disposerCascadeUE : undefined;
  const toutVoir = cascade && (Boolean(mot) || !cascadeDessinee(cascade, disposer));
  const selectionTextes = selTexte ?? (toutVoir ? selectionDeTousLesTextes(cascade) : null);
  return (
    <>
      {textes.total === 0 && europe.total === 0 && mot ? (
        <VideDuFiltre mot={mot}>Aucun texte porté dont l’intitulé contient {MOT(mot)}.</VideDuFiltre>
      ) : textes.total === 0 && europe.total === 0 ? (
        <div className="cp-carte">
          <ListeVide cause={causeTextes} source="Textes portés comme auteur ou rapporteur" />
        </div>
      ) : (
        <div className="cp-carte cp-textes">
          {mot && <EtiquetteFiltre mot={mot} />}
          <div className="cp-gouv-tete">
            <span className="cp-gouv-nom">
              Les textes {voix.quil} a portés
              {!deuxVersants && ue ? ' au Parlement européen' : ''}
            </span>
            <span className="cp-gouv-periode cp-num">
              {ue ? (
                <>
                  {formatNumber(europe.total)} textes portés ·{' '}
                  {formatNumber(europe.publies)} à un stade publié
                </>
              ) : (
                <>
                  {formatNumber(textes.publies.length)} publiés ·{' '}
                  {formatNumber(textes.promulgues)} promulgué{textes.promulgues > 1 ? 's' : ''}
                </>
              )}
            </span>
          </div>
          {commutateur && (
            <CommutateurVersant
              compteFr={textes.total}
              compteUe={europe.total}
              libelle="Parlement des textes portés"
              onFr={() => changerVersant('fr')}
              onUe={() => changerVersant('ue')}
              ue={ue}
            />
          )}
          {filtreNature && (
            <div className="cp-natures" role="group" aria-label="Nature des textes européens">
              {[{ cle: 'tous', libelle: 'Toutes natures', total: europe.total }]
                .concat(naturesPresentes.map((n) => ({ ...n, total: europe.parNature[n.cle].total })))
                .map((n) => (
                  <button
                    aria-pressed={nature === n.cle}
                    className="cp-nature"
                    key={n.cle}
                    onClick={() => choisirNature(n.cle)}
                    type="button"
                  >
                    {n.libelle} <b className="cp-num">{formatNumber(n.total)}</b>
                  </button>
                ))}
            </div>
          )}
          {cascade && cascade.total > 0 && (
            <>
              <Cascade
                cascade={cascade}
                disposer={disposer}
                ue={ue}
                onSelection={setSelTexte}
                selection={selTexte}
              />
              <ListeCascade
                cascade={cascade}
                onRaz={selTexte ? () => setSelTexte(null) : null}
                ordonnee={!ue}
                selection={selectionTextes}
              />
            </>
          )}
          {/* Ce que §6 ne publie pas est compté, jamais tu : un texte resté en
              phase préparatoire n'est pas un texte absent (§2 règle 5). */}
          {ue && europe.horsSeuil > 0 && (
            <p className="cp-chute-mentions">
              {formatNumber(europe.horsSeuil)} texte{europe.horsSeuil > 1 ? 's' : ''} en phase
              préparatoire au Parlement, que la fiche ne publie pas.
            </p>
          )}
        </div>
      )}

      {amdt.totalAuteur === 0 ? (
        <div className="cp-carte">
          {mot && <EtiquetteFiltre mot={mot} />}
          {/* Un versant vide DIT de quel parlement il parle : sans commutateur
              ni titre, « aucun amendement » se lirait comme un vide de
              collecte, alors que l'autre versant en porte des milliers. */}
          <div className="cp-gouv-tete">
            <span className="cp-gouv-nom">
              Les amendements dont {voix.sujet} est l’auteur
              {commutateur ? '' : ue ? ' au Parlement européen' : ''}
            </span>
          </div>
          {commutateur && (
            <CommutateurVersant
              compteFr={amdtFr.totalAuteur}
              compteUe={amdtUe.totalAuteur}
              libelle="Parlement des amendements"
              onFr={() => changerVersant('fr')}
              onUe={() => changerVersant('ue')}
              ue={ue}
            />
          )}
          {/* Sous un mot, ce vide est celui du FILTRE : « non collecté » y
              serait faux (§2 règle 5, #979). */}
          {mot ? (
            <p className="cp-note cp-filtre-vide">
              Aucun dossier amendé dont l’intitulé contient {MOT(mot)}.
              {filtre.amendementsEuropeens && amdtUe.totalAuteur === 0
                ? ' Au Parlement européen, ces intitulés sont publiés en anglais.'
                : ''}
            </p>
          ) : (
            <ListeVide
              cause={causeAmendements}
              source={`Amendements déposés comme auteur principal ${ue ? 'au Parlement européen' : 'à l’Assemblée nationale'}`}
            />
          )}
        </div>
      ) : amdt.chute && (
        <div className="cp-carte">
          {mot && <EtiquetteFiltre mot={mot} />}
          <div className="cp-gouv-tete">
            <span className="cp-gouv-nom">
              Les amendements dont {voix.sujet} est l’auteur
              {commutateur ? '' : ue ? ' au Parlement européen' : ''}
            </span>
            <span className="cp-gouv-periode cp-num">
              {formatNumber(amdt.totalAuteur)} amendements ·{' '}
              {formatNumber(amdt.dossiers?.distincts ?? amdt.chute.totalDossiers)}{' '}
              dossiers ·{' '}
              {/* Un `0` n'est publiable que si la source dit quelque chose du
                  sort. Aucun des 7 303 amendements européens n'en porte : « 0
                  adopté » s'y lisait « aucun n'a été adopté » quand la vérité
                  est que rien n'est publié (§2 règle 5). */}
              {amdt.sortsPublies === 0
                ? 'sort non publié'
                : `${formatNumber(amdt.adoptes)} adopté${amdt.adoptes > 1 ? 's' : ''}`}
            </span>
          </div>
          {commutateur && (
            <CommutateurVersant
              compteFr={amdtFr.totalAuteur}
              compteUe={amdtUe.totalAuteur}
              libelle="Parlement des amendements"
              onFr={() => changerVersant('fr')}
              onUe={() => changerVersant('ue')}
              ue={ue}
            />
          )}
          {filtreNatureAmdt && (
            <div className="cp-natures" role="group" aria-label="Nature des dossiers amendés">
              {[{ cle: 'tous', libelle: 'Toutes natures', total: amdt.totalAuteur }]
                .concat(naturesAmdt.map((n) => ({ ...n, total: amendementsUe.depotsParNature[n.cle] })))
                .map((n) => (
                  <button
                    aria-pressed={natureAmdt === n.cle}
                    className="cp-nature"
                    key={n.cle}
                    onClick={() => { setNatureAmdt(n.cle); setMatiere(null); }}
                    type="button"
                  >
                    {n.libelle} <b className="cp-num">{formatNumber(n.total)}</b>
                  </button>
                ))}
            </div>
          )}
          {figureAmdt.chute && (
            <Matieres
              ue={ue}
              chute={figureAmdt.chute}
              matiere={matiere}
              onMatiere={choisirMatiere}
            />
          )}
          {/* CE QUI RESTAIT EN TROIS CARTES TIENT EN UNE LIGNE. Les adoptés et
              les deux motifs d'irrecevabilité étaient rendus en `cp-bloc`, la
              forme réservée aux grands chiffres : trois nombres de la taille des
              totaux de la fiche, pour un fait qui se lit sous la légende. Aucun
              n'est perdu — ils sont ici, à la suite de la figure qu'ils
              qualifient, et sans accent. */}
          {/* Les articles 40 et 45 sont une règle de l'Assemblée : côté
              européen, la liste est vide et la mention ne s'affiche pas. */}
          {amdt.irrecevabilites.length > 0 && (
            <p className="cp-chute-mentions">
              {amdt.irrecevabilites
                .map((b) => `${formatNumber(b.n)} ${b.titre}`)
                .join(' · ')}
            </p>
          )}
          {(matiere || mot) && (
            <div className="cp-chute-liste">
              <div className="cp-chute-liste-tete">
                <span className="cp-chute-liste-quoi">
                  {matiere || 'Toutes les commissions'} — {formatNumber(dossiersDeLaMatiere.length)} dossier
                  {dossiersDeLaMatiere.length > 1 ? 's' : ''}
                </span>
                {matiere && (
                  <button className="cp-chute-raz" onClick={() => setMatiere(null)} type="button">
                    Tout afficher
                  </button>
                )}
              </div>
              <ul>
                {dossiersDeLaMatiere.map((d) => (
                  <li key={d.cle}>
                    <span className="cp-chute-titre">{d.nom || 'Dossier non nommé par la source'}</span>
                    <span className="cp-chute-fait">
                      {formatNumber(d.n)} amendement{d.n > 1 ? 's' : ''} déposé{d.n > 1 ? 's' : ''}
                      {/* Aucun sort publié sur la population affichée — les
                          dépôts européens n'en portent aucun : « aucun adopté »
                          y publiait un zéro là où la source ne dit rien (§2
                          règle 5). L'en-tête dit déjà « sort non publié ». */}
                      {amdt.sortsPublies === 0 ? null : d.adoptes > 0 ? (
                        <>
                          , <b className="cp-chute-oui">{formatNumber(d.adoptes)} adopté{d.adoptes > 1 ? 's' : ''}</b>
                        </>
                      ) : (
                        ', aucun adopté'
                      )}
                      {d.annee ? ` · ${d.annee}` : ''}
                    </span>
                  </li>
                ))}
              </ul>
              {/* LA NOTE SOUS LA LISTE EST PARTIE EN DEUX TEMPS. Sa première
                  moitié parlait de l'axe des années, retiré avec la cascade. La
                  seconde recomptait ce que la liste montre déjà : chaque ligne
                  porte « N adoptés » ou « aucun adopté », et une phrase qui
                  totalise ce que l'œil vient de lire fait relire au lieu de
                  compléter. */}
            </div>
          )}
        </div>
      )}

      <p className="cp-methodo">
        <Link to="/methodologie#propose">
          Quels textes et quels amendements sont retenus, et pourquoi aucun taux d’adoption
        </Link>
      </p>
    </>
  );
}

/* ── § 4 — ce qu'il a dit ────────────────────────────────────────────────────
 *
 * REMPLACÉ EN ENTIER LE 09/09/2026 (#328). Ce qui était ici — le régime de
 * qualité en pavé, la liste des natures, la liste des fonctions, le bloc des
 * questions au gouvernement — publiait quatre listes de totaux de carrière et
 * un paragraphe de méthode, sans jamais montrer un mot de ce qui avait été dit,
 * alors que le corpus porte 16 188 verbatims du compte rendu intégral. La
 * maquette validée ne garde rien de cela : la section est désormais la figure
 * par période, ses deux facettes croisées et le fil.
 *
 * CE QUI N'EST PAS PERDU. Le régime de qualité et la direction des questions au
 * gouvernement restent calculés — « En bref » les consomme —, et la qualité est
 * écrite intervention par intervention dans le fil (« prononcé comme ministre
 * délégué »), là où elle qualifie un fait plutôt qu'une carrière. Ce que la
 * section ne sait pas est publié sous la figure.
 */
function Paroles({ interventions, cause, mot = '' }) {
  if (!interventions.total && mot) {
    return <VideDuFiltre mot={mot}>Aucune intervention dont le sujet ou le propos contient {MOT(mot)}.</VideDuFiltre>;
  }
  if (!interventions.total) {
    return (
      <div className="cp-carte">
        <ListeVide cause={cause} source="Interventions en séance et en commission" />
      </div>
    );
  }

  if (!interventions.periodes?.length) {
    return (
      <div className="cp-carte">
        <ListeVide
          cause="non_collecte"
          motif="Aucune de ses interventions ne porte de date exploitable : sans date, ni le banc ni le gouvernement en place ne peuvent être lus, et une période politique ne se construit pas."
        />
      </div>
    );
  }

  return (
    <ParolesParPeriode
      deplie={Boolean(mot)}
      mot={mot}
      etiquette={mot ? <EtiquetteFiltre mot={mot} /> : null}
      qualites={interventions.qualites}
      plafondPeriode={interventions.plafondPeriode}
      plafondEnsemble={interventions.plafondEnsemble}
      couverture={interventions.couverture}
    />
  );
}

/* ── § 5 — ce qu'il a voté ─────────────────────────────────────────────────── */
/* ── § 3 — CE QU'IL A VOTÉ, DES DEUX CÔTÉS (#901) ───────────────────────────
 *
 * Le même commutateur que « Ce qu'il a proposé », et la même figure que côté
 * français — le composant est partagé, seuls trois traits changent, chacun
 * parce que la source ne publie pas la même chose à Strasbourg : aucun
 * découpage par période, aucune origine de texte, et le thème du dossier à la
 * place de la commission saisie au fond.
 */
function Votes({ votes, cause, mot = '' }) {
  const europe = votes.europe || { textes: 0 };
  const deuxVersants = votes.textes > 0 && europe.textes > 0;
  const [versant, setVersant] = useState(votes.textes > 0 ? 'fr' : 'ue');
  const ue = europe.textes > 0 && (versant === 'ue' || !deuxVersants);
  /* Sous un mot, rien à afficher n'est pas rien à dire : la carte le dit
   * plutôt que de disparaître (§2 règle 5). Depuis #901, les positions
   * européennes sont rattachées et filtrées comme les autres : la phrase
   * qui les déclarait absentes n'a plus lieu d'être. */
  if (mot && votes.derniereLectureDisponible !== false
    && !europe.textes && (!votes.textes || !votes.periodes?.length)) {
    return (
      <VideDuFiltre mot={mot}>
        Aucun vote affiché dont l’intitulé contient {MOT(mot)}.
      </VideDuFiltre>
    );
  }
  if (ue || deuxVersants) {
    return (
      <>
        {deuxVersants && (
          <CommutateurVersant
            compteFr={votes.textes}
            compteUe={europe.textes}
            libelle="Parlement des votes"
            onFr={() => setVersant('fr')}
            onUe={() => setVersant('ue')}
            ue={ue}
          />
        )}
        {ue ? (
          <VotesParPeriode
            key="ue"
            periodes={europe.periodes}
            portee={europe.portee}
            regle={`${formatNumber(europe.textes)} textes — dernier vote retenu pour chaque texte`}
            reperes={europe.reperes}
            ue
          />
        ) : (
          <VotesFrancais cause={cause} mot={mot} votes={votes} />
        )}
      </>
    );
  }
  return <VotesFrancais cause={cause} mot={mot} votes={votes} />;
}

function VotesFrancais({ votes, cause, mot = '' }) {
  if (!votes.total) {
    return (
      <div className="cp-carte">
        <ListeVide cause={cause} source="Positions de vote publiées" />
      </div>
    );
  }

  /* DEUX FIGURES RETIRÉES LE 08/09, ET CE QU'ELLES PORTAIENT.
   *
   * 1. L'AXE DES ANNÉES — une barre par année civile, avec trois situations
   *    (`gouvernement`, `hors_mandat`, `en_mandat`). Il existait pour qu'un
   *    zéro ne se lise pas comme une absence individuelle (§2 règle 3), ce qui
   *    n'a de sens que sur un axe CONTINU. La vue par période n'affiche que
   *    les périodes où la personne a voté : il n'y a plus de zéro à expliquer,
   *    donc plus rien à protéger.
   *
   * 2. LA NOTE « un membre du gouvernement ne vote pas » — corollaire du même
   *    axe : elle nommait les années creuses. Le fait lui-même n'est pas perdu,
   *    il est porté par « Les fonctions exercées » et par la frise d'« En bref ».
   *
   * Ce qui RESTE, et qui n'est pas décoratif : les quatre branches de vide
   * ci-dessous, qui distinguent quatre causes qu'aucune figure ne remplace, et
   * les dénominateurs du repli, qu'un ratio ne peut pas taire (§2 règle 7).
   */
  return (
    <>
      {!votes.derniereLectureDisponible ? (
        <div className="cp-carte">
          <ListeVide
            cause="non_collecte"
            motif="L’index des scrutins n’a pas pu être lu. Sans lui, la dernière lecture de chaque texte n’est pas déterminable, et un décompte non replié afficherait une position de première lecture comme sa position sur la loi."
          />
        </div>
      ) : votes.surEnsemble === 0 ? (
        /* CE QUE CETTE BRANCHE NE DIT PLUS (#901). Elle portait, pour les fiches
           dont tous les votes sont européens, « ses N positions au Parlement
           européen sont collectées, mais aucune n'est rattachée à un scrutin
           identifié ». Ce n'est plus vrai : elles le sont, par numéro et date,
           et le versant européen les affiche — la carte française n'est plus
           atteinte dans ce cas. */

        <div className="cp-carte">
          <ListeVide
            cause="couvert"
            motif="Aucune de ses positions ne porte sur l’ensemble d’un texte au sens de la règle publiée ci-dessous. Ses autres positions — sur un article, sur un amendement — restent comptées dans le total."
          />
        </div>
      ) : votes.textes === 0 ? (
        <div className="cp-carte">
          <ListeVide
            cause="couvert"
            motif="Toutes ses positions sur l’ensemble d’un texte portent sur une lecture qu’un scrutin plus tardif a suivie, et il n’a pas de position enregistrée sur ces dernières lectures. Nous ne pouvons pas dire pourquoi, et le dire serait publier une absence individuelle."
          />
        </div>
      ) : (
        <>
          {/* DEUX PHRASES, ET PLUS DEUX PARAGRAPHES (#328).
              Le « pourquoi » des deux règles — quatre lectures d'un même texte,
              un code de scrutin qui ne sépare pas l'ensemble de l'article —
              est passé dans la page de méthodologie, où le renvoi sous la
              figure mène. Trois pages de raisonnement sous un graphique font
              lire la légende à la place du fait.
              Ce qui NE PART PAS : les deux phrases elles-mêmes. #711 les veut
              à côté du chiffre, pas seulement dans la méthodologie — qui
              annonçait déjà la règle à l'époque où rien ne l'appliquait. */}
          {votes.periodes?.length ? (
            <>
              <VotesParPeriode
                etiquette={mot ? <EtiquetteFiltre mot={mot} /> : null}
                periodes={votes.periodes}
                portee={votes.portee}
                reperes={votes.reperes}
                regle={`${formatNumber(votes.textes)} textes — ${LAST_READING_LABEL}`}
              />
            </>
          ) : (
            <div className="cp-carte">
              <ListeVide
                cause="non_collecte"
                motif="Aucune de ses positions de dernière lecture ne porte de date exploitable : sans date, ni le banc ni le gouvernement en place ne peuvent être lus, et une période politique ne se construit pas."
              />
            </div>
          )}
        </>
      )}
    </>
  );
}

/* ── § 7 — ce qu'on n'a pas pu lire ─────────────────────────────────────────── */
const LIBELLE_ETAT = {
  couvert: 'couvert',
  hors_couverture: 'hors couverture',
  non_collecte: 'non collecté',
  fait_etabli: 'fait établi',
};

function Couverture({ couverture, parcours, collecte }) {
  return (
    <>
      {/* `--rangs` : les rangs portent leur marge et leur filet court d'un bord
          à l'autre, donc la carte s'efface devant eux. La seule de la fiche. */}
      <div className="cp-carte cp-carte--rangs">
        <div className="cp-gouv-tete cp-rangs-tete">
          <span className="cp-gouv-nom">Ce que chaque liste porte</span>
          <span className="cp-gouv-periode cp-num">
            {formatNumber(couverture.length)} liste{couverture.length > 1 ? 's' : ''}
          </span>
        </div>
        {couverture.map((c) => (
          <div className="cp-ligne cp-ligne--couverture" key={c.cle}>
            <span className="cp-ligne-cle">{c.titre}</span>
            <span className="cp-ligne-corps">
              {c.etats.map((e) => (
                <span className="cp-etat" key={`${e.etat}-${e.debut}-${e.fin}`}>
                  <b>{LIBELLE_ETAT[e.etat] || e.etat}</b>
                  {e.debut && ` depuis le ${jour(e.debut)}`}
                  {!e.debut && e.fin && ` jusqu’au ${jour(e.fin)}`}
                  {/* La même borne explique souvent « couvert depuis » ET
                      « hors couverture jusqu'au » : elle se dit une fois par
                      liste, jamais deux (`preuveDejaDite`). */}
                  {e.preuve && !e.preuveDejaDite && <em>{e.preuve}</em>}
                </span>
              ))}
            </span>
            <span className="cp-ligne-nombre cp-num">
              {formatNumber(c.decompte)}
              <span>entrées</span>
            </span>
          </div>
        ))}
      </div>

      {/* DEUX SOUS-PARTIES, PARCE QU'IL Y A DEUX SUJETS.
          Le tableau ci-dessus dit, liste par liste, CE QUE LE DÉPÔT PORTE et
          depuis quand. Les signalements ci-dessous disent ce que LA COLLECTE a
          rencontré — une source qui ne publie pas, un identifiant introuvable.
          Mêlés, ils faisaient un tableau suivi de paragraphes flottants que rien
          ne rattachait à rien.

          Chaque signalement est coupé sur son premier tiret cadratin, que nos
          propres messages posent entre la source et son explication (« Parlement
          européen — votes non publiés : … »). Un message qui n'en porte pas est
          rendu entier : on ne devine pas un intitulé qui n'existe pas. */}
      {parcours.length > 0 && (
        <div className="cp-carte cp-signal">
          <div className="cp-gouv-tete">
            <span className="cp-gouv-nom">Ce que le corpus ne dit pas de son parcours</span>
            <span className="cp-gouv-periode cp-num">
              {formatNumber(parcours.length)} point{parcours.length > 1 ? 's' : ''}
            </span>
          </div>
          <dl className="cp-signal-dl">
            {parcours.map((l) => (
              <Fragment key={l.cle}>
                <dt>{LIBELLE_LIMITE[l.cle] || 'Corpus'}</dt>
                <dd>{l.texte}</dd>
              </Fragment>
            ))}
          </dl>
        </div>
      )}

      {collecte.length > 0 && (
        <div className="cp-carte cp-signal">
          <div className="cp-gouv-tete">
            <span className="cp-gouv-nom">Ce que la collecte signale</span>
            <span className="cp-gouv-periode cp-num">
              {formatNumber(collecte.length)} signalement{collecte.length > 1 ? 's' : ''}
            </span>
          </div>
          <dl className="cp-signal-dl">
            {collecte.map((l) => {
              const coupe = /^(.+?)\s+—\s+([\s\S]+)$/.exec(l.texte);
              return (
                <Fragment key={l.cle}>
                  <dt>{coupe ? coupe[1] : 'Collecte'}</dt>
                  <dd>{coupe ? coupe[2] : l.texte}</dd>
                </Fragment>
              );
            })}
          </dl>
        </div>
      )}
      {/* LE BLOC « ASSIDUITÉ / CLASSEMENT / 49.3 » EST RETIRÉ (#328). Mesuré
          sur la page rendue de `delphine-batho` : « aucun classement » y
          apparaissait TROIS fois — ici, dans le pied de la fiche juste en
          dessous, et dans le pied du site. Les trois refus restent publiés là
          où ils s'argumentent : `STATED_REFUSALS` est rendu par la
          méthodologie, source unique, et « Ce que vous ne trouverez pas ici »
          l'expose sur l'accueil. Le 49.3, lui, est déjà porté là où il sert —
          la pastille d'encre de « Ce qu'il a voté » marque chaque texte adopté
          sans vote (#743). */}
      {/* DEUX renvois, deux questions distinctes : ce que ces bornes valent
          pour tout le corpus, et pourquoi une limite se déclare au lieu de se
          combler (DESIGN_SYSTEM §7 règle 2). */}
      <p className="cp-methodo">
        <Link to="/sources#frise">Ce que le dépôt porte, et depuis quand</Link>
        {' · '}
        <Link to="/methodologie#couverture">
          Pourquoi ces limites se déclarent au lieu de se combler
        </Link>
      </p>
    </>
  );
}

/* ── § Les grands chiffres — la frise commande les colonnes ──────────────────
 *
 * **La frise est CELLE DU PARCOURS, pas une seconde.** Ce bloc en portait une
 * copie — pistes par institution, étiquettes propres, légende propre — et cette
 * copie coûtait exactement ce que #672 a fermé sur `isWholeTextVote` : deux
 * définitions du même objet, qui divergent au premier ajustement. Relevé en
 * relecture d'écran le 03/09/2026 : « reprends exactement la même frise que dans
 * la section parcours, avec la légende et le détail daté ».
 *
 * `Frise` porte déjà tout ce que la copie refaisait, et mieux : la teinte porte
 * l'institution, le MOTIF porte la position, les repères numérotés renvoient à
 * une liste datée, et la légende dit pourquoi les deux familles ne forment
 * aucune progression. La couleur fait donc toujours le lien avec les colonnes —
 * ce sont désormais les colonnes qui prennent la teinte de la frise, et non
 * l'inverse.
 */

/* Une cellule : UNE LIGNE AU CORPS DU TEXTE, le nombre en gras (forme « la
 * phrase », maquette « En bref » du 11/09/2026). Les grands chiffres donnaient à
 * 3 933 interventions le poids visuel de 28 textes portés ; aucun nombre ne
 * domine plus les autres. Le total du rang vient en tête, le détail dessous. */
function CelluleChiffre({ cellule: c, piste }) {
  // La PISTE est portée par la cellule, pas déduite de sa position (#328). La
  // règle d'avant partait de l'en-tête « gouvernement » et descendait sur tous
  // ses frères : dans une grille, les cellules de la colonne PARLEMENT viennent
  // après cet en-tête, et prenaient donc la teinte du gouvernement.
  const classe = `cp-gc-cell cp-gc-cell--${piste}`;
  if (!c) return <div className={`${classe} cp-gc-cell--vide`} />;
  if (c.absent) {
    return (
      <div className={classe}>
        <p className="cp-gc-absent">
          <span aria-hidden="true">—</span> {c.absent}
        </p>
      </div>
    );
  }
  return (
    <div className={classe}>
      <p className="cp-gc-n">
        <b className="cp-num">{formatNumber(c.nombre)}</b> <small>{c.objet}</small>
        {c.sur != null && (
          <>
            {' '}
            <b className="cp-num">{formatNumber(c.sur)}</b> <small>{c.objetSur}</small>
          </>
        )}
      </p>
      {c.quantifieur && (
        <p className="cp-gc-q">
          {c.quantifieur.avant ? `${c.quantifieur.avant} ` : ''}
          <span className="cp-num">{formatNumber(c.quantifieur.nombre)}</span>{' '}
          {c.quantifieur.texte}
          {c.quantifieur.suite ? ` · ${c.quantifieur.suite}` : ''}
        </p>
      )}
      {c.detail && <p className="cp-gc-d">{c.detail}</p>}
    </div>
  );
}

/* La largeur vient de la CLASSE, jamais d'un style en ligne : une valeur en
 * ligne ne se surcharge qu'avec `!important`, que la media query du petit écran
 * devrait alors reprendre. Quatre largeurs, autant que d'institutions. */
const MOT_COLONNES = { 1: 'une', 2: 'deux', 3: 'trois', 4: 'quatre' };

/* LE SÉNAT EST REPLIÉ D'ENTRÉE, SAUF S'IL EST SEUL — et c'est un choix de
 * lecture, pas une suppression : sa puce reste allumée au-dessus du tableau et
 * dit ce qui est là. Sa colonne ne porterait, sur les deux fiches concernées,
 * que des cellules vides : la collecte du Sénat est hors périmètre (#528), donc
 * ni vote, ni amendement, ni intervention. La replier met en avant ce que la
 * fiche sait dire ; la retirer effacerait un siège réel (§2 règle 5).
 *
 * Seule exception, celle qui empêche une fiche vide : si le Sénat est la seule
 * colonne, il s'ouvre. Un tableau sans colonne ne se replie pas, il disparaît. */
function repliParDefaut(colonnes) {
  if (colonnes.length <= 1) return new Set();
  return new Set(colonnes.filter((c) => c === INSTITUTION_SENAT));
}

function GrandsChiffres({ chiffres, parcours }) {
  const { colonnes = [], lignes = [] } = chiffres || {};
  const [replies, setReplies] = useState(() => repliParDefaut(colonnes));
  /* UNE FICHE SANS AUCUN CHIFFRE PEUT AVOIR UN PARCOURS (#922). David Lisnard,
   * Karim Bouamrane, Fabien Verdier et Marine Tondelier n'ont ni siège national
   * ni fonction gouvernementale, mais des mandats locaux : le bloc se taisait
   * entièrement, frise comprise. Il se rend désormais dès qu'il a une frise à
   * montrer, et seul le tableau des chiffres reste absent. */
  const sansChiffres = !chiffres || chiffres.cas === CAS_RIEN_A_MONTRER;
  if (sansChiffres && !parcours?.roles?.length) return null;
  const ouvertes = colonnes.filter((c) => !replies.has(c));
  const basculer = (c) => setReplies((avant) => {
    const apres = new Set(avant);
    // JAMAIS ZÉRO COLONNE : replier la dernière ne laisserait que des intitulés
    // de rang, c'est-à-dire le gabarit et aucune personne.
    if (!apres.has(c) && ouvertes.length === 1) return avant;
    if (apres.has(c)) apres.delete(c);
    else apres.add(c);
    return apres;
  });
  return (
    <section className="cp-gc">
      {/* « En bref » prend la bande, le filet et le h2 d'un titre de section.
          SANS numéro : le numéroter ferait de ce bloc la section 1 et décalerait
          les sept suivantes, ce qui n'a pas été décidé. */}
      <div className="cp-section-bande">
        <span className="cp-section-trait" />
      </div>
      <h2 className="cp-section-titre"><span>En bref</span></h2>

      <div className="cp-carte cp-gc-carte">
        {/* La FRISE reste toujours dépliée : c'est l'ossature, et elle donne aux
            colonnes leur couleur et leur raison d'être. Replier le bloc entier
            cachait ce qui explique le reste.

            C'est LE composant `Frise`, celui de la section « Le parcours » —
            même bande, même légende, même liste datée. Une seconde frise aurait
            divergé de la première au premier ajustement. */}
        <div className="cp-gc-frise">
          <Frise parcours={parcours} />
        </div>

        {/* La thèse introduit LES COLONNES, pas le parcours : elle se lit juste
            avant « À l'Assemblée », et elle sert de poignée à ce qui la suit. La
            partie dense — cinq rangs sur deux colonnes — est ce qui se replie,
            et le « + » le dit sans une phrase.

            La ligne elle-même a été réduite trois fois : le texte explicatif est
            un aveu d'échec, et si une phrase doit expliquer un chiffre, c'est la
            forme qui n'a pas fait son travail. */}
        {!sansChiffres && (
        <details className="cp-pli">
          <summary className="cp-poignee">
            <i className="cp-poignee-plus" aria-hidden="true" />
            Ce que cette personne a engagé, en chiffres.
          </summary>

          {/* Le nombre de colonnes vient de la CLASSE, jamais d'un style en
              ligne : sous 720 px le tableau défile latéralement, et une valeur en
              ligne ne se surcharge qu'avec `!important` — que le prochain
              ajustement oublierait. */}
          {/* LE NOM DU RANG UNE FOIS, À GAUCHE — et non répété au-dessus de
              chaque colonne. Avec deux institutions il se lisait deux fois ;
              avec les quatre qu'une carrière peut traverser, « TEXTES PORTÉS »
              s'écrivait quatre fois sur la même ligne. Le tableau met le rang
              en tête de ligne et laisse les colonnes aux chiffres, qui sont ce
              qu'on compare. */}
          {/* LES PUCES DISENT CE QUE LE TABLEAU NE MONTRE PAS. Une colonne
              repliée sort de la grille — le tableau se resserre sur ce qui
              reste —, mais sa puce demeure, éteinte : le lecteur voit qu'une
              institution existe et qu'il peut la rouvrir. Sans elles, replier
              serait effacer. */}
          {colonnes.length > 1 && (
            <div className="cp-gc-puces" role="group" aria-label="Institutions affichées">
              {colonnes.map((c) => (
                <button
                  type="button"
                  key={`p-${c}`}
                  className={`cp-gc-puce cp-gc-puce--${c}`}
                  aria-pressed={!replies.has(c)}
                  onClick={() => basculer(c)}
                >
                  <i aria-hidden="true" />
                  {LIBELLE_PISTE[c]}
                </button>
              ))}
            </div>
          )}

          <div className={`cp-gc-duo cp-gc-duo--${MOT_COLONNES[ouvertes.length] || 'quatre'}`}>
            <div className="cp-gc-coin" />
            {ouvertes.map((c) => (
              <div className={`cp-gc-tete-col cp-gc-tete-col--${c}`} key={`t-${c}`}>
                <span className="cp-gc-bandeau" />
                <span className="cp-gc-col-nom">
                  <i />
                  {LIBELLE_PISTE[c]}
                </span>
              </div>
            ))}
            {/* La règle « un rang sans aucun chiffre ne s'affiche pas » vaut sur
                les colonnes OUVERTES : replier le Sénat ne doit pas laisser un
                intitulé seul face à rien. */}
            {lignes
              .filter((l) => ouvertes.some((c) => l.cellules[c] && !l.cellules[c].absent))
              .map((l) => (
              <Fragment key={l.cle}>
                <p className="cp-gc-rang">{l.titre}</p>
                {ouvertes.map((c) => (
                  <CelluleChiffre cellule={l.cellules[c]} key={`c-${l.cle}-${c}`} piste={c} />
                ))}
              </Fragment>
            ))}
          </div>
        </details>
        )}
      </div>

      {/* LE PIED EST HORS DE LA CARTE, comme celui de toutes les sections :
          `Section` rend sa prop `pied` après `cp-section-corps`, jamais dedans.
          « En bref » n'est pas un `Section` — il compose sa bande et son titre à
          la main —, donc il compose aussi son pied, avec la même classe et au
          même endroit relatif.

          Il remplace la note « Majorité, minorité et opposition selon l'AN », la
          seule phrase qui rattachait les trois postures à l'Assemblée plutôt
          qu'à nous (§2 règle 2) : la frise ne les porte plus, mais la liste des
          rôles les écrit toujours. */}
      {parcours?.roles?.some((r) => r.institution === INSTITUTION_LOCAL) && (
        <p className="cp-section-pied">
          * Mandats locaux : données parcellaires, publiées seulement à partir de 2020.
        </p>
      )}
      <p className="cp-section-pied">
        <Link to="/methodologie#fonctions">Majorité, minorité et opposition, selon l’Assemblée →</Link>
      </p>
    </section>
  );
}

/* « L'essentiel » a été remplacé par « Les grands chiffres » (#328) : sa vue —
 * la fonction `Point` et ses trois rendus — est retirée. Le VIVIER, lui, reste
 * calculé dans `profilCandidat.js` et testé : la décision prévoit explicitement
 * qu'un vrai résumé prenne la place que ce bloc libère, et supprimer le calcul
 * avant de savoir ce qui le remplace détruirait ce que
 * `tests/test_essentiel_328.py` documente.
 */

/* L'intitulé de chaque limite de parcours : il nomme SUR QUOI elle porte, pour
 * que trois phrases deviennent trois lignes rangées. Les clés viennent de
 * `profilCandidat.js` ; une clé inconnue retombe sur « Corpus » plutôt que de
 * rendre une ligne sans intitulé. */
const LIBELLE_LIMITE = {
  'position-non-declaree': 'Qualification du groupe',
  suspension: 'Entrée au gouvernement',
  'sieges-replies': 'Enregistrements de mandat',
  'mandats-anterieurs': 'Mandats antérieurs',
};

/* DEUX SORTES DE LIMITES, ET ELLES NE DISENT PAS LA MÊME CHOSE.
 *
 * Les unes disent ce que le corpus NE DIT PAS de cette personne : la
 * qualification que l'Assemblée n'a pas déclarée sur un mandat, la suspension
 * pour fonction gouvernementale qu'aucun mandat électif ne renseigne, les
 * enregistrements repliés sur un même siège. Les autres disent ce que la
 * COLLECTE a rencontré : une source qui ne publie pas, un identifiant
 * introuvable.
 *
 * Toutes restent en « ce qu'on n'a pas pu lire » — c'est la section qui parle
 * des trous —, mais chacune sous son intitulé : mêlées, elles faisaient une
 * suite de phrases sans rang. */
const LIMITES_DU_PARCOURS = new Set([
  'position-non-declaree',
  'suspension',
  'sieges-replies',
  /* Un mandat antérieur à ce que l'Assemblée publie est, très exactement, ce
     que le corpus ne dit pas de son parcours (#860). */
  'mandats-anterieurs',
]);

export default function CandidateProfile({ candidate, mot = '' }) {
  const c = candidate;
  const filtre = mot ? c.filtre : null;
  const limitesDuParcours = (c.limites || []).filter((l) => LIMITES_DU_PARCOURS.has(l.cle));
  const limitesDeCollecte = (c.limites || []).filter((l) => !LIMITES_DU_PARCOURS.has(l.cle));

  return (
    <main className="cp-main">
      <div className="cp-breadcrumb">
        Candidats / <strong>{c.nom}</strong>
      </div>

      <header className="cp-entete">
        <p className="cp-sourcil">Candidat déclaré · élection présidentielle 2027</p>
        <h1>{c.nom}</h1>
        {/* LA SOURCE TERMINE LA LIGNE QU'ELLE SOURCE. Elle était posée en
            dessous, sur sa propre ligne : le lecteur devait rattacher un badge
            flottant à un texte, alors qu'il atteste exactement ces faits-là —
            profession, groupe, parti, naissance. */}
        <p className="cp-qui">
          <span>
            {[c.profession].filter(Boolean).map((t) => `${t} · `)}
            {c.groupe && (
              <>
                {/* LE LIEN N'EST POSÉ QUE S'IL MÈNE AU GROUPE QUE LE TEXTE
                    NOMME — voir `ficheDuGroupeAffiche`. Sans fiche, le libellé
                    reste du texte : « Parti socialiste », « Sans étiquette » ou
                    un groupe du Parlement européen ne sont pas des fiches, et un
                    lien mort vaut moins que pas de lien. */}
                {/* Un libellé du Parlement européen commence déjà par « Groupe » :
                    « Groupe Groupe de l'Alliance… » sur Raphaël Glucksmann. */}
                {/^groupe\b/i.test(c.groupe) ? '' : 'Groupe '}
                {c.groupeFiche
                  ? <Link to={`/groupes/${c.groupeFiche.id}`}>{c.groupe}</Link>
                  : c.groupe}
                {c.parti ? ' · ' : ''}
              </>
            )}
            {c.parti}
            {c.naissance && `. ${c.voix.ne} le ${jour(c.naissance.date)}${c.naissance.lieu ? ` à ${c.naissance.lieu}` : ''}.`}
          </span>
          <BadgeSource url={c.sourceUrl} />
        </p>
      </header>

      {/* « Les grands chiffres » remplace « L'essentiel » (#328). Deux noms ont
          été essayés et écartés : « Coup d'œil » promettait de la rapidité, pas
          du contenu ; « L'essentiel » promettait une synthèse que le bloc ne
          délivre pas. Ce qu'on a construit est un TABLEAU DE BORD, et le nommer
          honnêtement libère la place pour un vrai résumé ailleurs.

          Il est dense — c'est assumé — donc repliable : il ne doit pas s'imposer
          avant que le lecteur ait choisi de le lire. */}
      {!filtre && <GrandsChiffres chiffres={c.grandsChiffres} parcours={c.parcours} />}

      {/* La frise ET le détail daté vivent dans « En bref », au-dessus : les
          republier ici était de la redondance pure. Ce qui reste est ce que
          personne d'autre ne porte — les fonctions qu'on choisit d'exercer —
          et le titre le dit. */}
      {!filtre && (
      <Section
        numero="1"
        titre="Les fonctions exercées"
        pied={
          <>
            Les trois plus longues par catégorie ; ligne surlignée = expérience sur + de la
            moitié du mandat.{' '}
            <Link to="/methodologie#fonctions">Pourquoi ce n’est pas un palmarès →</Link>
          </>
        }
      >
        {c.fonctions.blocs.length === 0 ? (
          <div className="cp-carte">
            <ListeVide cause={c.causes.mandats} source="Fonctions exercées" />
          </div>
        ) : (
          <Fonctions fonctions={c.fonctions} />
        )}
      </Section>
      )}

      {/* PAS DE CHAPEAU SUR CETTE SECTION. Il annonçait la règle avant qu'on
          ait rien lu — « une seule liste, quel que soit le banc… » — et faisait
          lire la consigne à la place du fait. Chaque figure porte désormais sa
          note SOUS elle : la cascade dit qu'aucun seuil ne s'applique et que la
          branche basse n'est pas un rejet, la chute dit que l'axe est le
          calendrier et qu'aucun rapport n'est calculé. */}
      <Section numero="2" titre={c.voix.titres.propose}>
        <Propositions
          filtre={filtre}
          key={`propose-${mot}`}
          amendements={c.amendements}
          amendementsParVersant={c.amendementsParVersant}
          amendementsUe={c.amendementsUe}
          textes={c.textes}
          causeAmendements={c.causes.amendements}
          causeTextes={c.causes.textes_portes}
          voix={c.voix}
        />
      </Section>

      <Section
        numero="3"
        titre={c.voix.titres.vote}
      >
        <Votes cause={c.causes.votes} key={`vote-${mot}`} mot={mot} votes={c.votes} />
      </Section>

      <Section
        numero="4"
        titre={c.voix.titres.ecarts}
        critere="Sa position à côté de celle de son groupe, scrutin par scrutin. Jamais totalisée."
      >
        {mot && !c.ecarts.bande.length ? (
          <VideDuFiltre mot={mot}>
            Aucun scrutin comparable avec son groupe dont l’intitulé contient {MOT(mot)}.
          </VideDuFiltre>
        ) : (
          <EcartsGroupe
            ecarts={c.ecarts}
            etiquette={mot ? <EtiquetteFiltre mot={mot} /> : null}
            voix={c.voix}
          />
        )}
      </Section>

      <Section
        numero="5"
        titre={c.voix.titres.dit}
        critere="Ses interventions par période politique, puis par nature et par sujet. Le verbatim est celui du compte rendu."
      >
        <Paroles cause={c.causes.interventions} interventions={c.interventions} key={`dit-${mot}`} mot={mot} />
      </Section>

      {!filtre && (
      <Section
        numero="6"
        titre="Ce qu’on n’a pas pu lire"
      >
        <Couverture
          couverture={c.couverture}
          parcours={limitesDuParcours}
          collecte={limitesDeCollecte}
        />
      </Section>
      )}

      {/* La licence SEULE. La phrase de refus qui l'accompagnait était la
          troisième occurrence de « aucun score, aucun classement » sur la même
          page ; elle vit maintenant dans le pied du site, une fois. */}
      <footer className="cp-pied">
        <span>{c.licence}</span>
      </footer>
    </main>
  );
}
