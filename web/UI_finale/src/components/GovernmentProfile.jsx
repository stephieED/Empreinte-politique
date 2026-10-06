/*
 * LA FICHE DE GOUVERNEMENT (#330), arbitrée en maquette avec la propriétaire du
 * dépôt les 17 et 18/09/2026.
 * Maquette de référence : https://claude.ai/artifact/BE1ez5DkE83kqCS6n6QxTC
 *
 * Trois sections, et ce que chacune répond :
 *
 *   01 « En bref »            — où ce gouvernement se situe. Même intention que
 *      sur les fiches sœurs : ce que l'objet EST, jamais ce qu'il a fait. La
 *      frise des dix-sept gouvernements, puis quatre faits sourcés.
 *   02 « Qui le composait »   — un bloc par ministère, replié ; le rattachement
 *      d'un ministre délégué se LIT dans le libellé officiel de son
 *      portefeuille, il ne se devine pas.
 *   03 « Ce qu'il a fait déposer » — le flux matière → étape.
 *
 * Trois formes ont été écartées en maquette, et il vaut mieux le savoir avant
 * de les reproposer : les grandes tuiles de chiffres (« une rangée de chiffres
 * ne dit pas quand »), la frise des dépôts mois par mois (elle avançait ce que
 * la section 03 dit déjà), et la liste des remaniements ligne à ligne (douze
 * lignes pour Philippe II, quand « remanié 10 fois » suffit).
 */
import { useEffect, useId, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Condition, EtiquetteFiltre, useFiltreActif } from './Recherche';
import { getPaquetExtraitsGouvernement, getParolesDuGouvernement, getSujetsComptesDuGouvernement } from '../data';
import { ProposDuMembre, usePaquetExtraits } from './ExtraitsDuDebat';
import { extraitsDuDebat, paquetDe } from '../utils/extraits';
import { motsDuFiltre } from '../utils/filtreIntitule';
import { SUJET_NON_PUBLIE } from '../utils/sujetIntervention.js';
import '../styles/shell.css';
import './CarresTextes.css';
import './GovernmentProfile.css';
import {
  LIBELLE_SORT_TEXTE, SOURCE_BADGE_VERIFIED, formatNumber, pageDuJeuDeDonnees,
} from '../utils/lecture';
import { useReplieAuClicDehors } from '../hooks/useReplieAuClicDehors';
import InfoBulle from './InfoBulle';
import {
  MATIERE_ABSENTE,
  chargeDuPortefeuille,
} from '../utils/gouvernement';
import ActesDuGouvernement from './ActesDuGouvernement';
import {
  GRIS_SANS_MINISTERE, clesDuTexte, fondDuTexte, nomCourtDuMinistere, polesDuGouvernement, teintesDesMinisteres,
} from '../utils/ministere';

/* LES BULLES (revue d'ergonomie du 04/10/2026). Une phrase dit ce que la
 * section présente, une note aide à ne pas mal la lire, un lien mène à la
 * méthode — la forme des fiches candidat et de groupe. Chaque texte a été
 * écrit ou recomposé par la propriétaire, rendu dans sa bulle avant d'être
 * retenu ; `tests/test_revue_ergonomie_fiche_gouvernement.py` les recopie, pour
 * qu'une reformulation échoue. Elles remplacent les quatre renvois qui
 * fermaient les sections. */
const LIRE_LA_METHODE = 'Lire la méthode →';
/* S'ajoute à la note d'« En bref » quand la fiche écrit « aucun groupe déclaré
 * majoritaire » : sans elle, l'absence se lit comme un défaut de la fiche.
 * Texte de la propriétaire, 04/10/2026. */
export const NOTE_MAJORITE_NON_DITE = 'L’Assemblée nationale ne dit quel groupe est majoritaire qu’une fois la législature achevée.';
export const BULLES = {
  enBref: {
    phrase: 'Le gouvernement en quelques faits.',
    note: 'Note : Le nombre de membres varie au fil des remaniements.',
    liens: [{ libelle: LIRE_LA_METHODE, vers: '/methodologie#gouv-composition' }],
  },
  composition: {
    phrase: 'Les ministres, ministres délégués et secrétaires d’État de ce gouvernement, par ministère.',
    note: 'Note : Sont comptés tous les membres passés par ce gouvernement, même brièvement.',
    liens: [{ libelle: LIRE_LA_METHODE, vers: '/methodologie#gouv-composition' }],
  },
  paroles: {
    phrase: 'Les prises de parole des membres du gouvernement à l’Assemblée, par débat.',
    note: 'Note : Une prise de parole peut tenir en quelques mots.',
    liens: [{ libelle: LIRE_LA_METHODE, vers: '/methodologie#gouv-paroles' }],
  },
  textes: {
    phrase: 'Les projets de loi que ce gouvernement a présentés au Parlement, et jusqu’où chacun est allé.',
    note: 'Note : Un texte arrêté à une étape n’est pas nécessairement rejeté. Le 49.3 est un fait de procédure, jamais un vote.',
    liens: [{ libelle: LIRE_LA_METHODE, vers: '/methodologie#gouv-textes' }],
  },
  actes: {
    phrase: 'Les décrets, arrêtés et ordonnances parus au Journal officiel pendant ce gouvernement, par ministère.',
    note: 'Note : Seuls les actes qui touchent au droit sont pris en compte et non ceux qui relèvent du fonctionnement interne de l’État (nominations, promotions…). Un acte peut appliquer une loi adoptée avant ce gouvernement.',
    liens: [{ libelle: LIRE_LA_METHODE, vers: '/methodologie#gouv-actes' }],
  },
  couverture: {
    phrase: 'Les limites de cette fiche : ce que les sources ne disent pas sur ce gouvernement.',
    note: 'Note : Une information absente de cette fiche n’a pas été trouvée dans les sources. Cela ne veut pas dire qu’il ne s’est rien passé.',
    liens: [{ libelle: LIRE_LA_METHODE, vers: '/methodologie#couverture' }],
  },
};

/* Le titre d'une section et sa bulle, sur une ligne. */
function TitreDeSection({ titre, bulle }) {
  return (
    <div className="gvp-section-titre-rang ib-ancre">
      <h2 className="gvp-section-titre"><span>{titre}</span></h2>
      <InfoBulle sujet={titre} {...bulle} />
    </div>
  );
}

const MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin',
  'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'];

function jour(iso) {
  if (!iso) return null;
  const [a, m, j] = iso.split('-');
  return `${Number(j)} ${MOIS[Number(m) - 1]} ${a}`;
}

function moisEtAnnee(iso) {
  return iso ? `${MOIS[Number(iso.slice(5, 7)) - 1]} ${iso.slice(0, 4)}` : null;
}

function moisCourt(iso) {
  return iso ? `${iso.slice(5, 7)}/${iso.slice(0, 4)}` : null;
}

function duree(debut, fin) {
  const jours = Math.round((Date.parse(fin || new Date().toISOString().slice(0, 10)) - Date.parse(debut)) / 86400000);
  if (jours <= 1) return `${jours} jour`;
  if (jours < 62) return `${jours} jours`;
  const mois = Math.round(jours / 30.44);
  if (mois < 24) return `${mois} mois`;
  return `${String(Math.round((jours / 365.25) * 10) / 10).replace('.', ',')} ans`;
}

/* L'étape où un texte s'est arrêté, dans l'ordre de la procédure. `depose` et
 * `rejete_49_3` n'ont aucun texte au commit de données du 18/09/2026 : ils sont
 * ici quand même — le vocabulaire est celui du schéma, pas celui du jour. */
const ORDRE_SORTS = [
  'promulgue', 'adopte', 'adopte_cmp', 'adopte_49_3',
  'navette_en_cours', 'depose', 'rejete', 'rejete_49_3', 'retire',
];

/* Les teintes d'issue du système (DESIGN_SYSTEM §2). Le 49.3 n'en reçoit
 * AUCUNE : c'est un fait de procédure, et une teinte le rangerait parmi les
 * issues de vote (§2 règle 4). Il se distingue par un contour. */
const TEINTE_SORT = {
  promulgue: '#007A45',
  adopte: '#4C9A6E',
  adopte_cmp: '#8FBFA5',
  navette_en_cours: '#c4c0b9',
  depose: '#DCD9D3',
  rejete: '#E53420',
  retire: '#F2A93B',
  adopte_49_3: null,
  rejete_49_3: null,
};

/* Le type d'une prise de parole, tel que la source le code. Une valeur
 * inconnue s'affiche telle quelle plutôt que de disparaître (§2 règle 5). */
const LIBELLE_TYPE_PAROLE = {
  debat: 'débat',
  loi: 'examen d’un texte',
  motion_censure: 'motion de censure',
  question_gouvernement: 'question au Gouvernement',
  question_orale: 'question orale',
  explication_vote: 'explication de vote',
  explication_de_vote: 'explication de vote',
};

const LIBELLE_COURT_SORT = {
  promulgue: 'Promulgué',
  adopte: 'Adopté',
  adopte_cmp: 'Adopté après CMP',
  adopte_49_3: 'Adopté via 49.3',
  rejete_49_3: 'Rejeté via 49.3',
  navette_en_cours: 'Navette en cours',
  depose: 'Déposé',
  rejete: 'Rejeté',
  retire: 'Retiré',
};

function VerifiedIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
      <path d="M2.5 9.5L9 3" stroke="#14151A" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M5.7 4.8l1.4 1.4" stroke="#14151A" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

/* ── 01 · En bref ────────────────────────────────────────────────────────── */

/* La frise des dix-sept gouvernements, celui de la fiche en teinte. Elle ne
 * remonte pas avant 2007 : l'Assemblée ne publie rien de plus ancien, et la
 * frise ne montre donc pas tous les gouvernements de la Ve République. */
function FriseDesGouvernements({ chronologie, courantId }) {
  const aujourdhui = new Date().toISOString().slice(0, 10);
  const tries = [...chronologie].filter((g) => g.debut).sort((a, b) => a.debut.localeCompare(b.debut));
  if (!tries.length) return null;

  const debut = Date.parse(tries[0].debut);
  const fin = Date.parse(aujourdhui);
  const etendue = Math.max(fin - debut, 1);
  const L = 1000;
  const GAUCHE = 2;
  const LARGEUR = L - 4;
  const HAUT = 26;
  const BANDE = 34;
  const x = (iso) => GAUCHE + ((Date.parse(iso) - debut) / etendue) * LARGEUR;

  const annees = [];
  for (let a = new Date(tries[0].debut).getUTCFullYear() + 1; a <= new Date(aujourdhui).getUTCFullYear(); a += 2) {
    annees.push(a);
  }

  return (
    <svg className="gvp-frise" viewBox={`0 0 ${L} 92`} role="img"
      aria-label={`Les ${tries.length} gouvernements publiés depuis ${tries[0].debut.slice(0, 4)}, celui de cette fiche mis en évidence`}>
      {tries.map((g) => {
        const x0 = x(g.debut);
        const x1 = x(g.fin || aujourdhui);
        const courant = g.id === courantId;
        const milieu = (x0 + x1) / 2;
        const ancre = milieu < 60 ? 'start' : (milieu > L - 60 ? 'end' : 'middle');
        return (
          <g key={g.id}>
            <rect x={x0} y={HAUT} width={Math.max(x1 - x0 - 1, 1.2)} height={BANDE} rx="2"
              fill={courant ? 'var(--gouv)' : 'var(--border-strong)'}>
              <title>
                {`${g.title} — ${jour(g.debut)}${g.fin ? ` → ${jour(g.fin)}` : ' → en fonction'}`}
              </title>
            </rect>
            {courant && (
              <text x={ancre === 'start' ? x0 : (ancre === 'end' ? x1 : milieu)} y={HAUT - 9}
                textAnchor={ancre} className="gvp-frise-nom">
                {g.title.replace(/^Gouvernement\s+/, '')}
              </text>
            )}
          </g>
        );
      })}
      {annees.map((a) => (
        <text key={a} x={x(`${a}-01-01`)} y={HAUT + BANDE + 18} textAnchor="middle" className="gvp-frise-annee">{a}</text>
      ))}
    </svg>
  );
}

function Fait({ cle, children, sous }) {
  return (
    <div className="gvp-fait">
      <span className="gvp-fait-cle">{cle}</span>
      <div className="gvp-fait-corps">
        <p className="gvp-fait-valeur">{children}</p>
        {sous && <p className="gvp-fait-sous">{sous}</p>}
      </div>
    </div>
  );
}

function EnBref({ government, chronologie }) {
  const { effectif, remaniements, majorite, chiffres } = government;
  const majoriteDeclaree = majorite.length > 0;

  return (
    <section className="gvp-section" data-section="En bref" id="section-bref">
      <div className="gvp-section-tete">
        <span className="gvp-section-numero">01</span>
        <span className="gvp-section-trait" />
      </div>
      <TitreDeSection
        bulle={government.majorite.some((m) => !m.declaree)
          ? { ...BULLES.enBref, note: `${BULLES.enBref.note} ${NOTE_MAJORITE_NON_DITE}` }
          : BULLES.enBref}
        titre="En bref"
      />
      <div className="gvp-carte">
        {chronologie.length > 1 && (
          <FriseDesGouvernements chronologie={chronologie} courantId={government.id} />
        )}

        <div className="gvp-faits">
          <Fait cle="Composition">
            {effectif && (effectif.mini === effectif.maxi
              ? <span className="gvp-nombre">{`${effectif.mini} membre${effectif.mini > 1 ? 's' : ''}`}</span>
              : (
                <>
                  {'entre '}
                  <span className="gvp-nombre">{effectif.mini}</span>
                  {' et '}
                  <span className="gvp-nombre">{`${effectif.maxi} membres`}</span>
                </>
              ))}
            {remaniements === 0 ? ' · jamais remanié' : ' · remanié '}
            {remaniements > 0 && <span className="gvp-fort">{`${remaniements} fois`}</span>}
          </Fait>

          <Fait
            cle="Majorité à l’Assemblée"
            sous={majoriteDeclaree ? null : 'nous ne collectons les groupes qu’à partir de 2017'}
          >
            {majoriteDeclaree ? majorite.map((m, i) => (
              <span key={m.legislature}>
                {i > 0 && ', puis '}
                <span className={m.declaree ? 'gvp-fort' : 'gvp-nd'}>{m.nom}</span>
                {i > 0 && ` à partir de ${moisEtAnnee(m.debut)}`}
              </span>
            )) : <span className="gvp-nd">non collectée pour cette période</span>}
          </Fait>

          <Fait
            cle="Projets de loi"
            sous={chiffres.sansVote
              ? `dont ${chiffres.sansVote} adopté${chiffres.sansVote > 1 ? 's' : ''} sans vote (article 49.3), fait de procédure`
              : null}
          >
            {chiffres.deposes ? (
              <>
                <span className="gvp-nombre">{chiffres.deposes}</span>{' déposés · '}
                <span className="gvp-nombre">{chiffres.adoptes}</span>
                {chiffres.adoptes === 1 ? ' adopté · ' : ' adoptés · '}
                <span className="gvp-nombre">{chiffres.promulgues}</span>
                {chiffres.promulgues === 1 ? ' promulgué à ce jour' : ' promulgués à ce jour'}
              </>
            ) : <span className="gvp-nd">aucun lisible sur cette période</span>}
          </Fait>
        </div>
      </div>
    </section>
  );
}

/* ── 02 · Qui le composait ───────────────────────────────────────────────── */

/* Replié par défaut, et une seule carte ouverte à la fois : la page ne
 * s'allonge pas au fil des clics. Les colonnes sont construites ici et non
 * laissées à une grille CSS — une grille aligne chaque rangée sur son bloc le
 * plus haut, si bien qu'ouvrir une carte les ouvrait visuellement toutes. */
function colonnes(poles, nombre) {
  const piles = Array.from({ length: nombre }, () => []);
  poles.forEach((pole, i) => piles[i % nombre].push(pole));
  return piles;
}

/* Les cartes et leurs teintes, calculées une fois par fiche : la même table
 * sert la composition, les projets de loi et les actes (`utils/ministere.js`). */
function useMinisteres(government) {
  return useMemo(() => {
    const poles = polesDuGouvernement(government);
    return { poles, teintes: teintesDesMinisteres(poles, government.textes) };
  }, [government]);
}

function Ministere({ pole, ouvert, onBasculer, teinte = null }) {
  const enfants = pole.enfants;
  const basculer = (ev) => {
    ev.stopPropagation();
    onBasculer();
  };
  return (
    <div
      className={`gvp-pole${pole.connu ? '' : ' gvp-pole--absent'}${enfants.length ? ' gvp-pole--cliquable' : ''}${teinte ? ' gvp-pole--teinte' : ''}`}
      onClick={enfants.length ? basculer : undefined}
      // Le liseré est la légende des deux sections qui suivent : la teinte du
      // ministère sur ses projets de loi et sur sa barre d'actes.
      style={teinte ? { '--ministere': teinte } : undefined}
    >
      <p className="gvp-pole-portefeuille">{pole.titre}</p>
      {pole.titulaires.length ? (
        <p className="gvp-pole-titulaire">
          {pole.titulaires.map((t, i) => (
            <span key={t.nom}>
              {i > 0 && <span className="gvp-passation"> → </span>}
              {t.nom}
              {i > 0 && <span className="gvp-depuis">{` depuis ${moisCourt(t.debut)}`}</span>}
            </span>
          ))}
        </p>
      ) : (
        <p className="gvp-pole-titulaire gvp-nd">Titulaire sans fiche ici</p>
      )}

      {enfants.length > 0 && (
        <>
          <button type="button" className="gvp-bascule" aria-expanded={ouvert} onClick={basculer}>
            <span className="gvp-chevron" aria-hidden="true">{ouvert ? '▾' : '▸'}</span>
            {`${enfants.length} rattaché${enfants.length > 1 ? 's' : ''}`}
          </button>
          <div className="gvp-tiroir" hidden={!ouvert}>
            {enfants.map((m) => {
              const charge = chargeDuPortefeuille(m.portefeuille);
              return (
                <p className="gvp-enfant" key={m.nom}>
                  <span className="gvp-enfant-nom">{m.nom}</span>
                  {charge && <span className="gvp-enfant-charge"> {charge}</span>}
                </p>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

function QuiLeComposait({ government }) {
  const [deplie, setDeplie] = useState(null);
  // Ce qui s'ouvre au clic se replie au clic ailleurs, comme sur les fiches
  // candidat et de groupe (04/10/2026).
  const carte = useRef(null);
  useReplieAuClicDehors(carte, deplie !== null, () => setDeplie(null));
  const { poles, teintes } = useMinisteres(government);
  const piles = colonnes(poles, 3);

  return (
    <section className="gvp-section" data-section="Qui le composait" id="section-composition">
      <div className="gvp-section-tete">
        <span className="gvp-section-numero">02</span>
        <span className="gvp-section-trait" />
      </div>
      <TitreDeSection bulle={BULLES.composition} titre="Qui le composait" />
      <div className="gvp-carte" ref={carte}>
        {poles.length === 0 ? (
          <p className="gvp-vide">Aucun membre n’est publié pour ce gouvernement.</p>
        ) : (
          <div className="gvp-orga">
            {piles.map((pile, i) => (
              // eslint-disable-next-line react/no-array-index-key
              <div className="gvp-colonne" key={i}>
                {pile.map((pole) => (
                  <Ministere
                    key={pole.cle || pole.titre}
                    pole={pole}
                    teinte={teintes.get(pole.cle) || null}
                    ouvert={deplie === (pole.cle || pole.titre)}
                    onBasculer={() => setDeplie((actuel) => (
                      actuel === (pole.cle || pole.titre) ? null : (pole.cle || pole.titre)
                    ))}
                  />
                ))}
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

/* ── 03 · Sur quoi ils ont pris la parole ───────────────────────────────────
 *
 * Le gabarit de la fiche de groupe (#329), repris tel quel : les débats où le
 * plus de MEMBRES sont intervenus, un compte de membres et jamais
 * d'occurrences, et le dénominateur à côté du numérateur (§2 règle 7).
 *
 * Ce que cette section ne dit pas, et ne dira pas : ce qu'ils ont dit. Un
 * intitulé de débat est un sujet, pas une position (§2 règle 8).
 */
/* ── La recherche sur la fiche (#979) ────────────────────────────────────────
 *
 * Même geste que sur la fiche candidat et la fiche de groupe : sous un mot,
 * « En bref » et « Qui le composait » se retirent — ni chiffres ni personnes ne
 * portent d'intitulé —, « Ce qu'on n'a pas pu lire » ne bouge pas, et les deux
 * sections d'intitulés se recalculent, figure et liste ensemble
 * (`filtrerGouvernement`). Chaque figure porte le mot en tête, pour qu'une
 * capture ne circule pas sans lui. */
/* LA PAROLE DU GOUVERNEMENT, COMPTÉE (revue d'ergonomie du 04/10/2026).
 *
 * La figure de la fiche de groupe : les débats rangés par nombre de PRISES DE
 * PAROLE, une barre par débat, un segment par membre. La ligne d'avant
 * écrivait « 21 / 50 » sans dire de quoi ; un relecteur y a lu 21
 * interventions. Les deux colonnes se nomment désormais.
 *
 * UN SUJET OUVERT MONTRE UN MEMBRE À LA FOIS. Tous les membres dépliés d'un
 * coup faisaient 5 880 px sur « motion de censure » (Borne). Le membre désigné
 * — au CLIC d'un segment, jamais au survol — se nomme sous la barre avec son nombre
 * de prises de parole ; ce nombre ne s'écrit plus à côté de vingt noms à la
 * fois. Ses propos se lisent le nom en tête, la date au-dessus de chacun.
 *
 * « INTITULÉ NON PUBLIÉ » SE COMPTE ET S'OUVRE comme les autres lignes (#1178),
 * depuis que les intitulés publiés l'ont rendue petite. Aucun filtre de rôle : un ministre ne préside pas la séance, et sa
 * parole est retenue par les dates de ses fonctions.
 *
 * Sous un mot recherché ou une période, la section garde sa liste d'avant :
 * c'est elle que la recherche sait réduire. */
function ParolesComptees({ government }) {
  const [sujets, setSujets] = useState(undefined);
  const [ouvert, setOuvert] = useState(null);
  const [choisi, setChoisi] = useState(null);
  const [detail, setDetail] = useState(null);
  const carte = useRef(null);
  useReplieAuClicDehors(carte, ouvert !== null, () => { setOuvert(null); setChoisi(null); });

  useEffect(() => {
    let vivant = true;
    setSujets(undefined);
    setOuvert(null);
    setChoisi(null);
    setDetail(null);
    getSujetsComptesDuGouvernement(government.id)
      .then((s) => { if (vivant) setSujets(s); })
      .catch(() => { if (vivant) setSujets(null); });
    return () => { vivant = false; };
  }, [government.id]);

  // Le détail d'un sujet — qui, sous quel portefeuille, quand — ne se charge
  // qu'au premier sujet ouvert : 4,1 Mo sur Borne.
  useEffect(() => {
    if (ouvert === null || detail !== null) return undefined;
    let vivant = true;
    getParolesDuGouvernement(government.id).then((d) => { if (vivant) setDetail(d || {}); });
    return () => { vivant = false; };
  }, [ouvert, detail, government.id]);

  const cleOuvert = ouvert === null ? null : `${government.id}:${paquetDe(ouvert)}`;
  const paquet = usePaquetExtraits(cleOuvert, () => getPaquetExtraitsGouvernement(government.id, paquetDe(ouvert)));

  if (sujets === undefined) return <p className="gvp-attente">Chargement des prises de parole…</p>;
  if (!sujets || !sujets.liste.length) {
    return (
      <p className="gvp-vide">
        Aucune prise de parole n’est lisible pour les membres de ce gouvernement — voir
        « Ce qu’on n’a pas pu lire ».
      </p>
    );
  }

  const { denominateur } = government.paroles;
  const max = Math.max(1, ...sujets.liste.map((l) => l.tours));
  const ouvrir = (label, nom = null) => {
    if (ouvert === label && nom === null) { setOuvert(null); setChoisi(null); return; }
    setOuvert(label);
    setChoisi(nom);
  };

  return (
    <div ref={carte}>
      <span className="gvp-facette">Débat <i>— {formatNumber(sujets.liste.length)} sur {formatNumber(sujets.debats)}</i></span>
      <div className="gvp-mat">
        <div className="gvp-mr gvp-mr--tete">
          <span />
          <span />
          <span className="gvp-mr-n">prises de parole</span>
          <span className="gvp-mr-n">membres</span>
        </div>
        {sujets.liste.map((l) => {
          // « Intitulé non publié » s'ouvre comme les autres lignes (#1178) ;
          // l'italique dit seulement que ce libellé n'est pas un intitulé.
          const sansIntitule = l.label === SUJET_NON_PUBLIE;
          const ouverte = ouvert === l.label;
          const designe = ouverte ? (choisi || l.segments[0][0]) : null;
          const pointe = designe;
          const montre = pointe ? { nom: pointe, n: l.segments.find(([n]) => n === pointe)?.[1] ?? 0 } : null;
          const entrees = ouverte && detail ? (detail[l.label] || []).filter((e) => e.membre === designe) : null;
          const extraits = ouverte && paquet ? extraitsDuDebat(paquet[l.label], { mots: [], debut: null, parIntitule: true }) : [];
          const siens = (e) => extraits.filter((x) => x.orateur === e.membre && x.date >= e.premiere && x.date <= e.derniere);
          return (
            <div className={`gvp-mr-bloc${sansIntitule ? ' gvp-mr-bloc--nd' : ''}`} key={l.label}>
              <div className="gvp-mr">
                <button aria-expanded={ouverte} className="gvp-mr-lib gvp-mr-lib--cliquable" onClick={() => ouvrir(l.label)} title={l.label} type="button">
                  <span aria-hidden="true" className="gvp-chevron">{ouverte ? '▾' : '▸'}</span>
                  {l.label}
                </button>
                <span className="gvp-mr-rail">
                  <span className="gvp-segments" style={{ width: `${((100 * l.tours) / max).toFixed(2)}%` }}>
                    {l.segments.map(([nom, n]) => (
                      <button
                        aria-label={`${nom} — ${formatNumber(n)} prise${n > 1 ? 's' : ''} de parole`}
                        aria-pressed={pointe === nom}
                        className={pointe === nom ? 'gvp-segment--choisi' : undefined}
                        key={nom}
                        onClick={() => ouvrir(l.label, nom)}
                        style={{ flex: `${n} 1 0` }}
                        type="button"
                      />
                    ))}
                  </span>
                </span>
                <span className="gvp-mr-n">{formatNumber(l.tours)}</span>
                <span className="gvp-mr-n gvp-mr-n--sur">{formatNumber(l.membres)} / {formatNumber(denominateur)}</span>
              </div>
              {/* Le membre désigné se nomme ici, avec son nombre : jamais vingt
                  nombres à la fois. */}
              {montre && (
                <p aria-live="polite" className="gvp-chemin">
                  <b>{montre.nom}</b> · {formatNumber(montre.n)} prise{montre.n > 1 ? 's' : ''} de parole sur {formatNumber(l.tours)} dans « {l.label} »
                </p>
              )}
              {ouverte && (
                <div className="gvp-interventions gvp-interventions--b">
                  {entrees === null ? (
                    <p className="gvp-attente">Chargement des prises de parole…</p>
                  ) : entrees.length === 0 ? (
                    <p className="gvp-attente">Aucune prise de parole détaillée pour ce membre.</p>
                  ) : entrees.map((e) => (
                    <div className="gvp-membre-b" key={`${e.membre}-${e.portefeuille}-${e.premiere}`}>
                      <div className="gvp-membre-b-tete">
                        <span className="gvp-intervention-membre">{e.membre}</span>
                        {e.portefeuille && <span className="gvp-intervention-qualite">{e.portefeuille}</span>}
                        <span className="gvp-intervention-date">
                          {e.premiere === e.derniere ? jour(e.premiere) : `du ${jour(e.premiere)} au ${jour(e.derniere)}`}
                        </span>
                      </div>
                      {siens(e).length > 0 ? (
                        <ProposDuMembre extraits={siens(e)} mots={[]} saisie="" />
                      ) : paquet === undefined ? (
                        <p className="gvp-attente">Chargement des propos…</p>
                      ) : e.url ? (
                        <a className="gvp-source" href={e.url} rel="noreferrer" target="_blank">
                          <VerifiedIcon /> {SOURCE_BADGE_VERIFIED}
                        </a>
                      ) : null}
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function SurQuoiIlsOntPrisLaParole({ government, mot = '', debut = null }) {
  const actif = useFiltreActif(mot);
  const { liste, total, denominateur, membres } = government.paroles;
  const [ouvert, setOuvert] = useState(null);
  const [detail, setDetail] = useState(null);

  /* La projection ne se télécharge qu'au premier clic — 4,1 Mo sur Borne, là
     où la fiche entière en pèse 1. Elle ne se recharge pas ensuite. */
  useEffect(() => {
    setOuvert(null);
    setDetail(null);
  }, [government.id]);

  useEffect(() => {
    if (ouvert === null || detail !== null) return undefined;
    let vivant = true;
    getParolesDuGouvernement(government.id).then((sujets) => {
      if (vivant) setDetail(sujets || {});
    });
    return () => { vivant = false; };
  }, [ouvert, detail, government.id]);

  /* CE QUI A ÉTÉ DIT (#1029) : le paquet d'extraits du débat ouvert, rangé
     sous chaque membre — ses propos sous sa ligne, jamais une liste à part. */
  const mots = motsDuFiltre(mot);
  const cleOuvert = ouvert === null ? null : `${government.id}:${paquetDe(ouvert)}`;
  const paquet = usePaquetExtraits(cleOuvert, () => getPaquetExtraitsGouvernement(government.id, paquetDe(ouvert)));

  const interventionsDe = (sujet) => {
    if (!detail) return null;
    const tous = detail[sujet] || [];
    if (!debut) return tous;
    // Sous une période, chaque membre ne garde que ses séances dans la fenêtre.
    return tous.map((i) => {
      const dedans = (i.seances || []).filter(([d]) => d >= debut);
      if (!dedans.length) return null;
      return { ...i, premiere: dedans[0][0], derniere: dedans.at(-1)[0], tours: dedans.reduce((n, [, t]) => n + t, 0) };
    }).filter(Boolean);
  };

  return (
    <section className="gvp-section" data-section="Sur quoi ils ont pris la parole" id="section-paroles">
      <div className="gvp-section-tete">
        <span className="gvp-section-numero">03</span>
        <span className="gvp-section-trait" />
      </div>
      <TitreDeSection bulle={BULLES.paroles} titre="Sur quoi ils ont pris la parole" />

      {!actif && !debut ? (
        <div className="gvp-carte"><ParolesComptees government={government} /></div>
      ) : (
      <div className="gvp-carte">
        <EtiquetteFiltre mot={mot} />
        {liste.length === 0 && actif ? (
          <p className="cp-filtre-vide">Aucun débat<Condition critere="dont l’intitulé contient" mot={mot} />.</p>
        ) : liste.length === 0 ? (
          <p className="gvp-vide">
            Aucun débat ne porte d’intitulé pour les membres de ce gouvernement — voir
            « Ce qu’on n’a pas pu lire ».
          </p>
        ) : liste.map((sujet) => {
          const choisi = ouvert === sujet.label;
          const parIntitule = sujet.parIntitule !== false;
          // Les extraits du débat, dans la fenêtre ; sous un mot que l'intitulé
          // ne porte pas, ceux-là seuls qui le portent.
          const extraits = choisi && paquet
            ? extraitsDuDebat(paquet[sujet.label], { mots, debut, parIntitule })
            : [];
          // Une ligne de membre garde les siens : même nom, et une date dans
          // l'intervalle de la ligne — deux portefeuilles, deux lignes.
          const siens = (i) => extraits.filter((e) => e.orateur === i.membre && e.date >= i.premiere && e.date <= i.derniere);
          const toutes = choisi ? interventionsDe(sujet.label) : null;
          // Retenu par ses propos seuls : seuls les membres qui ont porté le mot.
          const interventions = toutes && !parIntitule && paquet !== undefined
            ? toutes.filter((i) => siens(i).length > 0)
            : toutes;
          return (
            <div className="gvp-sujet-bloc" key={sujet.label}>
              <button
                type="button"
                className="gvp-sujet"
                aria-expanded={choisi}
                onClick={() => setOuvert(choisi ? null : sujet.label)}
              >
                <span className="gvp-sujet-lib">
                  <span className="gvp-chevron" aria-hidden="true">{choisi ? '▾' : '▸'}</span>
                  {sujet.label}
                  {/* Retenu par les propos seuls (#1029) : l'intitulé ne porte
                      pas le mot, le lecteur doit le savoir avant d'ouvrir. */}
                  {sujet.parIntitule === false && <span className="gvp-sujet-via"> · le mot est dans les propos</span>}
                </span>
                <span className="gvp-sujet-n">
                  <b>{sujet.porteurs}</b> <small>/ {denominateur}</small>
                </span>
                <span className="gvp-sujet-barre">
                  <i style={{ width: `${((100 * sujet.porteurs) / Math.max(1, denominateur)).toFixed(1)}%` }} />
                </span>
              </button>

              {choisi && (
                <div className="gvp-interventions">
                  {interventions === null ? (
                    <p className="gvp-attente">Chargement des interventions…</p>
                  ) : interventions.length === 0 ? (
                    <p className="gvp-attente">Aucune intervention détaillée pour ce débat.</p>
                  ) : (
                    <>
                      {interventions.map((i) => (
                        <div className="gvp-membre-bloc" key={`${i.membre}-${i.premiere}`}>
                          {/* FORME A (maquette du 22/09/2026) : le membre à
                              gauche, ses propos datés à droite. */}
                          <div className="gvp-membre-tete">
                            <span className="gvp-intervention-membre">{i.membre}</span>
                            {/* En qualité de quoi : le portefeuille exercé À LA
                                DATE de ses prises de parole, lu sur la fiche et
                                jamais déduit. */}
                            {i.portefeuille && (
                              <span className="gvp-intervention-qualite">{i.portefeuille}</span>
                            )}
                            <span className="gvp-intervention-date">
                              {i.premiere === i.derniere
                                ? jour(i.premiere)
                                : `du ${jour(i.premiere)} au ${jour(i.derniere)}`}
                            </span>
                            <span className="gvp-intervention-type">
                              {i.tours > 1 ? `${formatNumber(i.tours)} prises de parole` : '1 prise de parole'}
                              {i.types.length > 0 && ` · ${i.types.map((t) => LIBELLE_TYPE_PAROLE[t] || t).join(', ')}`}
                            </span>
                          </div>
                          {siens(i).length > 0 ? (
                            <ProposDuMembre extraits={siens(i)} mots={mots} saisie={mot} />
                          ) : i.url ? (
                            // Sans extraits servis : le lien de la ligne, seul.
                            <a className="gvp-source" href={i.url} target="_blank" rel="noreferrer">
                              <VerifiedIcon /> {SOURCE_BADGE_VERIFIED}
                            </a>
                          ) : null}
                        </div>
                      ))}
                    </>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
      )}
      {/* Sous un mot ou une période, le pied dit ce que la liste compte. */}
      {(actif || debut) && liste.length > 0 && (
        <p className="gvp-section-pied">
          {mot
            ? `${formatNumber(liste.length)} débat${liste.length > 1 ? 's' : ''} · membres qui y sont intervenus, sur ${denominateur} des ${membres} membres dont la parole est collectée`
            : `${liste.length} sur ${formatNumber(total)} débats · membres qui y sont intervenus, sur ${denominateur} des ${membres} membres dont la parole est collectée`}
        </p>
      )}
    </section>
  );
}

/* ── 04 · Ce qu'il a fait déposer ────────────────────────────────────────── */

/*
 * UN CARRÉ PAR PROJET DE LOI (revue d'ergonomie du 04/10/2026, forme B).
 *
 * La fiche de gouvernement était la seule à garder un diagramme de flux : les
 * fiches candidat et de groupe montrent un carré par texte, rangé à l'étape
 * atteinte et teinté par sa commission. Même figure ici, avec les étapes d'un
 * projet de loi.
 *
 * CINQ COLONNES. « Adoptés » réunit les trois adoptions — vote, commission
 * mixte paritaire, 49.3 —, comme la colonne unique de la fiche candidat ;
 * l'étape exacte se lit en toutes lettres dans la liste, jamais sous le sigle
 * « CMP » seul. La première colonne, « déposés », est propre au gouvernement :
 * le dépôt est son acte, là où candidat et groupe partent de l'examen en
 * commission.
 *
 * LE 49.3 N'A PAS DE COLONNE : c'est un fait de procédure (§2 règle 4), dit
 * par la pastille. Au survol de la pastille, les carrés adoptés sans vote
 * s'allument et les autres s'estompent — demandé sur maquette. Aucune pastille
 * pour la commission mixte paritaire : « adopté » y est exact, il n'y a aucune
 * lecture fausse à prévenir.
 *
 * Un statut que la source ajouterait reçoit sa propre colonne, sous le libellé
 * de la source : rien ne disparaît faute de place prévue (§2 règle 5).
 */
const COLONNES_PROJETS = [
  { cle: 'deposes', statuts: ['depose'], un: 'déposé', plusieurs: 'déposés' },
  { cle: 'navette', statuts: ['navette_en_cours'], un: 'en navette', plusieurs: 'en navette' },
  { cle: 'adoptes', statuts: ['adopte', 'adopte_cmp', 'adopte_49_3'], un: 'adopté', plusieurs: 'adoptés' },
  { cle: 'promulgues', statuts: ['promulgue'], un: 'promulgué', plusieurs: 'promulgués' },
  { cle: 'rejetes', statuts: ['rejete', 'rejete_49_3'], un: 'rejeté', plusieurs: 'rejetés' },
];
const STATUT_493 = 'adopte_49_3';

/** Les colonnes de la figure : les cinq prévues, puis une par statut imprévu.
 *  Dans une colonne, les carrés se rangent par ministère, dans l'ordre des
 *  cartes de « Qui le composait » : les teintes voisinent au lieu de se mêler. */
export function colonnesDesProjets(textes, poles = []) {
  const prevus = new Set(COLONNES_PROJETS.flatMap((c) => c.statuts));
  const imprevus = [...new Set(textes.map((t) => t.statut).filter((st) => !prevus.has(st)))];
  const rang = (t) => {
    const cles = clesDuTexte(poles, t);
    const k = poles.findIndex((p) => p.cle === cles[0]);
    return k < 0 ? Number.MAX_SAFE_INTEGER : k;
  };
  const trier = (liste) => [...liste].sort((x, y) => rang(x) - rang(y)
    || String(x.dateDepot || '').localeCompare(String(y.dateDepot || '')));
  return [
    ...COLONNES_PROJETS,
    ...imprevus.map((st) => {
      const libelle = (LIBELLE_COURT_SORT[st] || st).toLowerCase();
      return { cle: st, statuts: [st], un: libelle, plusieurs: libelle };
    }),
  ].map((c) => ({ ...c, textes: trier(textes.filter((t) => c.statuts.includes(t.statut))) }));
}

/* Ce que la légende écrit pour un projet qu'aucun ministère de la fiche ne
   présente : le Premier ministre seul, ou une source qui ne nomme personne. */
const SANS_MINISTERE = 'Aucun ministère nommé';

function retenu(selection, texte, poles = []) {
  if (!selection) return true;
  if (selection.ministere) return clesDuTexte(poles, texte).includes(selection.ministere);
  if (selection.texte) return selection.texte === texte.dossierId;
  if (selection.colonne) return selection.statuts.includes(texte.statut);
  if (selection.p493) return texte.statut === STATUT_493;
  return true;
}

function CarresDesProjets({ textes, selection, onSelection, poles = [], teintes = new Map() }) {
  // Les ministères qui présentent au moins un projet, dans l'ordre des cartes.
  const presentes = poles.filter((p) => teintes.has(p.cle) && textes.some((t) => clesDuTexte(poles, t).includes(p.cle)));
  const sansMinistere = textes.filter((t) => !clesDuTexte(poles, t).some((c) => teintes.has(c))).length;
  const colonnes = useMemo(() => colonnesDesProjets(textes, poles), [textes, poles]);
  const n493 = textes.filter((t) => t.statut === STATUT_493).length;
  /* LE TEXTE SURVOLÉ SE NOMME DANS UNE INFOBULLE, celle des carrés des fiches
   * candidat et groupe (`.cp-car-bulle`) : posée d'après le carré, ancrée par
   * le bas, hors du flux. Une ligne écrite sous la grille décalait tout ce
   * qui la suit à chaque carré survolé. */
  const ref = useRef(null);
  const idBulle = useId();
  const [bulle, setBulle] = useState(null);
  const montrer = (texte, cible) => {
    const cadre = ref.current?.getBoundingClientRect();
    if (!cadre) return;
    const b = cible.getBoundingClientRect();
    const largeur = Math.min(300, cadre.width);
    const gauche = Math.max(0, Math.min(b.left - cadre.left - 20, cadre.width - largeur));
    setBulle({ texte, gauche, bas: cadre.bottom - b.top + 12, fleche: b.left - cadre.left + b.width / 2 - gauche });
  };
  const cacher = () => setBulle(null);
  const [eclaire493, setEclaire493] = useState(false);
  const meme = (a) => JSON.stringify(a) === JSON.stringify(selection);
  const choisir = (nouvelle) => onSelection(meme(nouvelle) ? null : nouvelle);
  const voile = (texte) => (eclaire493 ? texte.statut !== STATUT_493 : !retenu(selection, texte, poles));

  return (
    <div className="cp-car gvp-car" ref={ref}>
      <div className="cp-car-cols" style={{ gridTemplateColumns: `repeat(${colonnes.length}, minmax(0, 1fr))` }}>
        {colonnes.map((col) => {
          const tete = (
            <>
              <span className="cp-car-n">{formatNumber(col.textes.length)}</span>
              <span className="cp-car-lib">{col.textes.length > 1 ? col.plusieurs : col.un}</span>
            </>
          );
          const sel = { colonne: col.cle, statuts: col.statuts, intitule: col.plusieurs };
          return (
            <div className="cp-car-col" key={col.cle}>
              {col.textes.length > 0 ? (
                <button aria-pressed={meme(sel)} className="cp-car-tete cp-car-tete--cliquable" onClick={() => choisir(sel)} type="button">
                  {tete}
                </button>
              ) : <div className="cp-car-tete">{tete}</div>}
              <div className="cp-car-grille">
                {col.textes.map((t) => (
                  <button
                    aria-describedby={bulle?.texte === t ? idBulle : undefined}
                    aria-label={t.titre}
                    aria-pressed={selection?.texte === t.dossierId}
                    className={[
                      'cp-car-carre',
                      selection?.texte === t.dossierId ? 'cp-car-carre--choisi' : '',
                      voile(t) ? 'cp-car-voile' : '',
                    ].filter(Boolean).join(' ')}
                    key={t.dossierId}
                    onBlur={cacher}
                    onClick={() => { cacher(); choisir({ texte: t.dossierId, intitule: t.titre }); }}
                    onFocus={(e) => montrer(t, e.currentTarget)}
                    onMouseEnter={(e) => montrer(t, e.currentTarget)}
                    onMouseLeave={cacher}
                    style={{ background: fondDuTexte(poles, teintes, t) }}
                    type="button"
                  />
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {bulle && (
        <div
          className="cp-car-bulle"
          id={idBulle}
          role="tooltip"
          style={{ left: bulle.gauche, bottom: bulle.bas, '--fleche': `${bulle.fleche}px` }}
        >
          <b>{bulle.texte.titre}</b>
          <span>{[...clesDuTexte(poles, bulle.texte).map((c) => nomCourtDuMinistere(poles.find((p) => p.cle === c)?.titre)), bulle.texte.commission || MATIERE_ABSENTE, LIBELLE_SORT_TEXTE[bulle.texte.statut] || bulle.texte.statut].join(' · ')}</span>
        </div>
      )}

      {/* La légende nomme les ministères, plus les commissions : la couleur d'un
          carré est celle du ministère qui présente le texte. La commission se
          lit dans l'infobulle et dans la liste. */}
      <div className="cp-car-legende">
        {presentes.map((p) => {
          const sel = { ministere: p.cle, intitule: nomCourtDuMinistere(p.titre) };
          return (
            <button
              aria-pressed={meme(sel)}
              className={['cp-car-cle', selection?.ministere && !meme(sel) ? 'cp-car-voile' : ''].filter(Boolean).join(' ')}
              key={p.cle}
              onClick={() => choisir(sel)}
              type="button"
            >
              <i aria-hidden="true" style={{ background: teintes.get(p.cle) }} />
              {nomCourtDuMinistere(p.titre)}
            </button>
          );
        })}
        {sansMinistere > 0 && (
          <span className="cp-car-cle gvp-cle-muette">
            <i aria-hidden="true" style={{ background: GRIS_SANS_MINISTERE }} />
            {SANS_MINISTERE}
          </span>
        )}
      </div>

      {n493 > 0 && (
        <p className="cp-ter-493">
          <button
            aria-pressed={Boolean(selection?.p493)}
            className="cp-ter-493-bouton"
            onBlur={() => setEclaire493(false)}
            onClick={() => choisir({ p493: true, intitule: 'adoptés sans vote (49.3)' })}
            onFocus={() => setEclaire493(true)}
            onMouseEnter={() => setEclaire493(true)}
            onMouseLeave={() => setEclaire493(false)}
            type="button"
          >
            <span className="cp-ter-493-marque">49.3</span>
            <b>{formatNumber(n493)}</b> de ces textes
            {n493 > 1 ? ' ont été adoptés' : ' a été adopté'} sans vote
            <span className="cp-ter-493-quoi">(fait procédural)</span>
          </button>
        </p>
      )}
    </div>
  );
}

function CeQuIlAFaitDeposer({ government, mot = '' }) {
  const actif = useFiltreActif(mot);
  const { poles, teintes } = useMinisteres(government);
  const couverture = government.textesCouverture || {};
  const horsCouverture = couverture.statut === 'hors_couverture';
  const partielle = couverture.statut === 'partielle';

  return (
    <section className="gvp-section" data-section="Ce qu’il a fait déposer" id="section-textes">
      <div className="gvp-section-tete">
        <span className="gvp-section-numero">04</span>
        <span className="gvp-section-trait" />
      </div>
      <TitreDeSection bulle={BULLES.textes} titre="Ce qu’il a fait déposer" />
      <div className="gvp-carte">
        <EtiquetteFiltre mot={mot} />
        {government.textes.length === 0 && actif ? (
          <p className="cp-filtre-vide">Aucun texte déposé<Condition critere="dont l’intitulé contient" mot={mot} />.</p>
        ) : government.textes.length === 0 ? (
          <p className="gvp-vide">
            {horsCouverture || partielle
              ? 'Aucun texte lisible sur cette période — voir « Ce qu’on n’a pas pu lire ».'
              : `Aucun projet de loi n’a été déposé entre le ${jour(government.periode.debut)} et le ${jour(government.periode.fin)} : un zéro mesuré, pas une absence de source.`}
          </p>
        ) : (
          <FluxEtListe mot={mot} poles={poles} teintes={teintes} textes={government.textes} />
        )}
      </div>
    </section>
  );
}

/* La liste ne s'ouvre qu'au clic : 282 cartes sous la figure étaient un mur. */
function FluxEtListe({ textes, mot = '', poles = [], teintes }) {
  const actif = useFiltreActif(mot);
  const [selection, setSelection] = useState(null);
  const racine = useRef(null);
  useReplieAuClicDehors(racine, selection !== null, () => setSelection(null));
  /* Sous un mot, la liste est DÉPLIÉE : les textes retenus s'affichent sans
     qu'il faille cliquer, et un clic les restreint encore. */
  const choisis = selection ? textes.filter((t) => retenu(selection, t, poles)) : actif ? textes : [];

  return (
    <div ref={racine}>
      <CarresDesProjets onSelection={setSelection} poles={poles} selection={selection} teintes={teintes} textes={textes} />
      {selection ? (
        <div className="gvp-selection">
          <p className="gvp-selection-tete">
            <span className="gvp-nombre">{choisis.length}</span>
            {choisis.length === 1 ? ' texte · ' : ' textes · '}
            <span className="gvp-fort">{selection.intitule}</span>
            <button type="button" className="gvp-raz" onClick={() => setSelection(null)}>Tout refermer</button>
          </p>
          <ListeDesTextes textes={choisis} />
        </div>
      ) : actif ? (
        <div className="gvp-selection">
          <p className="gvp-selection-tete">
            <span className="gvp-nombre">{choisis.length}</span>
            {choisis.length === 1 ? ' texte' : ' textes'}
          </p>
          <ListeDesTextes textes={choisis} />
        </div>
      ) : (
        <p className="gvp-invite">Cliquez un carré, une étape ou un ministère pour lire les textes.</p>
      )}
    </div>
  );
}

const TEXTES_AFFICHES = 30;

function ListeDesTextes({ textes }) {
  const [tout, setTout] = useState(false);
  const visibles = tout ? textes : textes.slice(0, TEXTES_AFFICHES);

  return (
    <div className="gvp-liste">
      {visibles.map((texte) => (
        <div className="gvp-texte" key={texte.dossierId}>
          <span className="gvp-texte-date">{texte.meta}</span>
          <div className="gvp-texte-corps">
            <p className="gvp-texte-titre">{texte.titre}</p>
            <div className="gvp-texte-meta">
              <span className="gvp-sort">
                <span
                  className={`gvp-pastille${TEINTE_SORT[texte.statut] ? '' : ' gvp-pastille--procedure'}`}
                  style={TEINTE_SORT[texte.statut] ? { background: TEINTE_SORT[texte.statut] } : undefined}
                />
                {LIBELLE_SORT_TEXTE[texte.statut] || texte.statut}
              </span>
              <span>{`Déposé au ${texte.chambre === 'Assemblée nationale' ? 'Assemblée' : 'Sénat'}`.replace('au Assemblée', 'à l’Assemblée')}</span>
              <span className={texte.commission ? undefined : 'gvp-nd'}>{texte.commission || MATIERE_ABSENTE}</span>
              {texte.sourceUrl ? (
                <a className="gvp-source" href={pageDuJeuDeDonnees(texte.sourceUrl)} target="_blank" rel="noreferrer">
                  <VerifiedIcon /> {SOURCE_BADGE_VERIFIED}
                </a>
              ) : (
                <span className="gvp-nd">Source non renseignée</span>
              )}
            </div>
          </div>
        </div>
      ))}
      {textes.length > TEXTES_AFFICHES && (
        <button type="button" className="gvp-plus" onClick={() => setTout((v) => !v)}>
          {tout ? 'Replier la liste' : `Voir les ${textes.length - TEXTES_AFFICHES} autres textes`}
        </button>
      )}
    </div>
  );
}

/* ── 04 · Ce qu'on n'a pas pu lire ──────────────────────────────────────── */

/*
 * Ce que CETTE fiche ne peut pas lire, et pourquoi — jamais le corpus entier,
 * qui a sa page (`/couverture`). Deux absences ne se confondent pas
 * (DESIGN_SYSTEM §7 règle 7) : une archive que la source ne publie pas, une
 * position que la source ne déclare pas encore, et une activité qui n'existe pas au
 * niveau d'un gouvernement sont trois lignes distinctes.
 */
function limitesDeLaFiche(government) {
  const lignes = [];
  const couverture = government.textesCouverture || {};

  if (couverture.statut === 'hors_couverture') {
    lignes.push({
      quoi: 'Textes déposés',
      /* LA BORNE SE LIT, ELLE NE S'ÉCRIT PAS DEUX FOIS. Elle a reculé du
         21 juin 2017 au 20 juin 2012 le jour où l'archive de la XIVe a été
         lue (#1019) : trois phrases la citaient en dur, et elles ont menti
         jusqu'à ce commit. Elle vient désormais de `textesCouverture.borne`,
         d'où `governmentTextsCoverage` la tire aussi. */
      texte: government.textes.length
        ? `Les archives de dossiers de l’Assemblée nationale commencent au ${jour(couverture.borne)}, après la fin de ce gouvernement. ${government.textes.length === 1 ? 'Le texte affiché vient' : 'Les textes affichés viennent'} de la traîne d’une archive plus récente : la liste n’est pas complète.`
        : `Les archives de dossiers de l’Assemblée nationale commencent au ${jour(couverture.borne)}, après la fin de ce gouvernement. Rien n’en est lisible, et ce n’est pas « aucun texte déposé ».`,
    });
  } else if (couverture.statut === 'partielle') {
    lignes.push({
      quoi: 'Textes déposés',
      texte: `Les archives de dossiers de l’Assemblée nationale commencent au ${jour(couverture.borne)}. Ce gouvernement était en fonction depuis le ${jour(government.periode.debut)} : ${duree(government.periode.debut, couverture.borne)} de son activité n’est pas couvert.`,
    });
  }

  if (!government.majorite.length) {
    lignes.push({
      quoi: 'Majorité à l’Assemblée',
      texte: 'Nous ne collectons les groupes parlementaires qu’à partir de 2017 : pour ce gouvernement, la position déclarée des groupes n’est pas lisible.',
    });
  } else if (government.majorite.some((m) => !m.declaree)) {
    lignes.push({
      quoi: 'Majorité à l’Assemblée',
      texte: `${NOTE_MAJORITE_NON_DITE} Aucun n’est donc déclaré majoritaire, et nous ne désignons pas le plus nombreux à sa place.`,
    });
  }

  /* L'étiquetage des débats est plus fin sur les années récentes : sur
     Philippe II, 329 interventions sur 48 370 portent un intitulé (mesuré le
     19/09/2026). Sans cette ligne, 61 sujets contre 1 738 chez Borne se
     lisent comme un gouvernement silencieux. */
  if (government.paroles.total === 0) {
    lignes.push({
      quoi: 'Prises de parole',
      texte: government.paroles.membres
        ? 'Aucun débat auquel ses membres ont participé ne porte d’intitulé dans la source : leurs prises de parole ne sont pas classables par sujet ici.'
        : 'Les prises de parole de ses membres ne sont pas collectées.',
    });
  } else {
    lignes.push({
      quoi: 'Prises de parole',
      texte: `Une prise de parole dont le compte rendu ne donne pas l’intitulé est comptée sous « Intitulé non publié », sans ses propos. Les intitulés sont plus fins sur les années récentes : ${government.paroles.denominateur} des ${government.paroles.membres} membres portent au moins un débat nommé.`,
    });
  }

  lignes.push({
    quoi: 'Votes',
    texte: 'Un gouvernement ne vote pas : ce que ses membres ont voté se lit sur leur propre fiche.',
  });

  return lignes;
}

/* MENTION TEMPORAIRE — POSÉE À LA MAIN, À RETIRER À LA MAIN (#1199).
 *
 * Le service qui diffuse le Journal officiel refuse toute requête depuis le
 * 02/10/2026 : les actes parus depuis n'arrivent plus, et la fiche du
 * gouvernement en place s'arrêtait au 1er octobre sans le dire. La
 * propriétaire a arbitré le 04/10/2026 : une mention de circonstance, sur
 * cette fiche seulement (pas sur la page Sources), texte et forme validés sur
 * maquette — l'encre pleine, parce que le gris du bandeau n'alertait pas.
 *
 * Ce n'est PAS une borne de couverture : rien ne la calcule, rien ne l'efface.
 * La constante vaut `null` quand aucune source n'est interrompue, et la
 * mention ne s'affiche pas.
 *
 * RETIRÉE LE 06/10/2026 : le service répond de nouveau depuis le 05/10. Le
 * texte affiché du 04 au 06/10 était « Données incomplètes depuis le 2 octobre
 * 2026. Le service qui diffuse le Journal officiel ne répond plus : les actes
 * parus depuis cette date n’apparaissent pas encore ici. » */
export const SOURCE_INTERROMPUE = null;

/* 05 — Ce qu'il a fait entrer en vigueur (#1029 voie 1). La section ne porte
   que son cadre : tout le reste vit dans `ActesDuGouvernement`. */
function CeQuIlAFaitEntrerEnVigueur({ government }) {
  const { poles, teintes } = useMinisteres(government);
  // Seul le gouvernement en place peut manquer d'actes récents.
  const interrompue = SOURCE_INTERROMPUE && !government.periode.fin;
  return (
    <section className="gvp-section" data-section="Ce qu’il a fait entrer en vigueur" id="section-actes">
      <div className="gvp-section-tete">
        <span className="gvp-section-numero">05</span>
        <span className="gvp-section-trait" />
      </div>
      <TitreDeSection bulle={BULLES.actes} titre="Ce qu’il a fait entrer en vigueur" />
      <div className="gvp-carte">
        {interrompue && (
          <p className="gvp-mention" role="note">
            <span aria-hidden="true" className="gvp-mention-point" />
            <span><strong>{SOURCE_INTERROMPUE.titre}</strong> {SOURCE_INTERROMPUE.texte}</span>
          </p>
        )}
        <ActesDuGouvernement id={government.id} poles={poles} teintes={teintes} />
      </div>
    </section>
  );
}

function CeQuOnNaPasPuLire({ government }) {
  const lignes = limitesDeLaFiche(government);

  return (
    <section className="gvp-section" data-section="Ce qu’on n’a pas pu lire" id="section-limites">
      <div className="gvp-section-tete">
        <span className="gvp-section-numero">06</span>
        <span className="gvp-section-trait" />
      </div>
      <TitreDeSection bulle={BULLES.couverture} titre="Ce qu’on n’a pas pu lire" />
      <div className="gvp-carte">
        <dl className="gvp-limites">
          {lignes.map((l) => (
            <div className="gvp-limite" key={l.quoi}>
              <dt>{l.quoi}</dt>
              <dd>{l.texte}</dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}

/* ── La fiche ────────────────────────────────────────────────────────────── */

export default function GovernmentProfile({ government, chronologie = [], mot = '', debut = null }) {
  const actif = useFiltreActif(mot);
  // « Première ministre » quand la source l'écrit ainsi : le libellé se lit, il
  // ne s'accorde pas à la main.
  const titreDuChef = government.membres.find((m) => m.nom === government.premierMinistre
    && /^premi[èe]re? ministre$/i.test(m.portefeuille || ''))?.portefeuille || 'Premier ministre';
  return (
    <main className="gvp-main">
      <div className="gvp-breadcrumb">
        Gouvernement / <strong>{government.title}</strong>
      </div>

      {/* Même en-tête que les fiches candidat et de lignée : un sourcil, le
          nom, puis UNE ligne d'identité — qui l'a dirigé et pendant combien de
          temps. Pas de carte ni de filet de couleur : l'en-tête n'est pas un
          bloc de contenu. */}
      <header className="gvp-entete">
        <p className="gvp-sourcil">Gouvernement</p>
        <h1>{government.title}</h1>
        <p className="gvp-qui">
          {government.premierMinistre ? (
            <span>
              {government.premierMinistreId ? (
                <Link className="gvp-lien" to={`/candidats/${government.premierMinistreId}`}>
                  {government.premierMinistre}
                </Link>
              ) : (
                <span className="gvp-fort">{government.premierMinistre}</span>
              )}
              {`, ${titreDuChef} · `}
            </span>
          ) : (
            <span><span className="gvp-nd">Premier ministre non publié</span>{' · '}</span>
          )}
          <span>
            {government.periode.fin
              ? `du ${jour(government.periode.debut)} au ${jour(government.periode.fin)} · ${duree(government.periode.debut, government.periode.fin)}`
              : `depuis le ${jour(government.periode.debut)} · ${duree(government.periode.debut, null)}`}
          </span>
        </p>
      </header>

      {!actif && <EnBref chronologie={chronologie} government={government} />}
      {!actif && <QuiLeComposait government={government} />}
      <SurQuoiIlsOntPrisLaParole debut={debut} government={government} key={`paroles-${mot}-${debut}`} mot={mot} />
      <CeQuIlAFaitDeposer government={government} key={`textes-${mot}`} mot={mot} />
      <CeQuIlAFaitEntrerEnVigueur government={government} />
      <CeQuOnNaPasPuLire government={government} />
    </main>
  );
}
