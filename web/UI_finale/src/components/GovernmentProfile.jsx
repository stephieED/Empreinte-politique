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
import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Condition, EtiquetteFiltre, useFiltreActif } from './Recherche';
import { getPaquetExtraitsGouvernement, getParolesDuGouvernement } from '../data';
import { ProposDuMembre, usePaquetExtraits } from './ExtraitsDuDebat';
import { extraitsDuDebat, paquetDe } from '../utils/extraits';
import { motsDuFiltre } from '../utils/filtreIntitule';
import { sankey, sankeyLinkHorizontal } from 'd3-sankey';
import '../styles/shell.css';
import './GovernmentProfile.css';
import {
  LIBELLE_SORT_TEXTE, SOURCE_BADGE_VERIFIED, formatNumber, pageDuJeuDeDonnees,
} from '../utils/lecture';
import { teinteMatiere } from '../utils/matiere';
import {
  MATIERE_ABSENTE,
  chargeDuPortefeuille,
  fluxMatiereSort,
  matiereDeFigure,
  organigramme,
} from '../utils/gouvernement';

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
      <h2 className="gvp-section-titre"><span>En bref</span></h2>
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
      <p className="gvp-methodo">
        <Link to="/methodologie#fonctions">Majorité, minorité et opposition, selon l’Assemblée →</Link>
      </p>
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

function Ministere({ pole, ouvert, onBasculer }) {
  const enfants = pole.enfants;
  const basculer = (ev) => {
    ev.stopPropagation();
    onBasculer();
  };
  return (
    <div
      className={`gvp-pole${pole.connu ? '' : ' gvp-pole--absent'}${enfants.length ? ' gvp-pole--cliquable' : ''}`}
      onClick={enfants.length ? basculer : undefined}
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
  const poles = useMemo(() => {
    /* La source publie parfois DEUX mandats d'appartenance pour la même
       personne, dont un sans portefeuille — Damien Abad et Yaël Braun-Pivet
       sous Borne (#996). L'entrée muette ne dit rien de plus que celle qui
       nomme le ministère, et en faire un bloc « Portefeuille non renseigné »
       ferait apparaître la personne deux fois. Elle est donc écartée
       UNIQUEMENT quand la personne est déjà placée ailleurs. */
    const nommes = new Set(government.membres.filter((m) => m.portefeuille).map((m) => m.nom));
    const membres = government.membres.filter((m) => m.portefeuille || !nommes.has(m.nom));
    return organigramme(membres, government.premierMinistre, government.periode);
  }, [government]);
  const piles = colonnes(poles, 3);

  return (
    <section className="gvp-section" data-section="Qui le composait" id="section-composition">
      <div className="gvp-section-tete">
        <span className="gvp-section-numero">02</span>
        <span className="gvp-section-trait" />
      </div>
      <h2 className="gvp-section-titre"><span>Qui le composait</span></h2>
      <div className="gvp-carte">
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
      <h2 className="gvp-section-titre"><span>Sur quoi ils ont pris la parole</span></h2>

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
      {/* Sous un mot, « N sur M » n'a plus de sens : M serait le nombre de
          débats qui portent le mot, c'est-à-dire N. Le pied dit alors ce qu'il
          compte, et rien de plus. */}
      {liste.length > 0 && (
        <p className="gvp-section-pied">
          {mot
            ? `${formatNumber(liste.length)} débat${liste.length > 1 ? 's' : ''} · membres qui y sont intervenus, sur ${denominateur} des ${membres} membres dont la parole est collectée`
            : `${liste.length} sur ${formatNumber(total)} débats · membres qui y sont intervenus, sur ${denominateur} des ${membres} membres dont la parole est collectée`}
        </p>
      )}
      <p className="gvp-methodo">
        <Link to="/methodologie#paroles">D’où viennent ces intitulés →</Link>
      </p>
    </section>
  );
}

/* ── 04 · Ce qu'il a fait déposer ────────────────────────────────────────── */

/*
 * LE FLUX MATIÈRE → ÉTAPE. À gauche la commission saisie au fond, à droite
 * l'étape où le texte s'est arrêté. L'épaisseur d'un ruban est un NOMBRE DE
 * TEXTES, jamais une part, et aucun seuil ne fait disparaître un texte seul.
 *
 * Les commissions spéciales, créées pour un seul texte, sont regroupées dans la
 * figure — une dizaine de rubans d'un texte y superposent leurs étiquettes. La
 * liste en dessous nomme chacune.
 */
function FluxDesTextes({ textes, selection, onSelection }) {
  const { matieres, sorts, liens } = useMemo(() => fluxMatiereSort(textes, ORDRE_SORTS), [textes]);

  const disposition = useMemo(() => {
    if (!liens.length) return null;
    const noeuds = [
      ...matieres.map((m) => ({ id: `m:${m.nom}`, nom: `${m.nom} (${m.n})`, teinte: teinteMatiere(m.nom === MATIERE_ABSENTE ? MATIERE_ABSENTE : m.nom, m.rang), matiere: m.nom })),
      ...sorts.map((s) => ({ id: `s:${s.statut}`, nom: `${LIBELLE_COURT_SORT[s.statut] || s.statut} (${s.n})`, teinte: TEINTE_SORT[s.statut], statut: s.statut })),
    ];
    const index = new Map(noeuds.map((n, i) => [n.id, i]));
    const graphe = {
      nodes: noeuds.map((n) => ({ ...n })),
      links: liens.map((l) => ({
        source: index.get(`m:${l.matiere}`),
        target: index.get(`s:${l.statut}`),
        value: l.valeur,
        matiere: l.matiere,
      })),
    };
    const hauteur = Math.max(260, Math.min(560, noeuds.length * 26));
    return {
      hauteur,
      graphe: sankey()
        .nodeWidth(12)
        .nodePadding(13)
        .extent([[2, 8], [810, hauteur - 8]])(graphe),
    };
  }, [matieres, sorts, liens]);

  if (!disposition) return null;
  const { graphe, hauteur } = disposition;
  const teinteDe = new Map(graphe.nodes.map((n) => [n.matiere, n.teinte]));

  return (
    <figure className="gvp-flux">
      <svg viewBox={`0 0 1000 ${hauteur}`} role="img"
        aria-label="Les textes déposés, de leur matière à l’étape où ils se sont arrêtés">
        <g>
          {graphe.links.map((l) => {
            const choisi = selection
              && selection.matiere === l.matiere
              && selection.statut === l.target.statut;
            const eteint = Boolean(selection) && !choisi;
            return (
              <path
                key={`${l.source.id}-${l.target.id}`}
                className="gvp-brin"
                d={sankeyLinkHorizontal()(l)}
                fill="none"
                stroke={teinteDe.get(l.matiere)}
                strokeOpacity={choisi ? 0.75 : (eteint ? 0.1 : 0.38)}
                strokeWidth={Math.max(1, l.width)}
                role="button"
                tabIndex={0}
                aria-pressed={Boolean(choisi)}
                onClick={() => onSelection(choisi ? null : { matiere: l.matiere, statut: l.target.statut })}
                onKeyDown={(ev) => {
                  if (ev.key !== 'Enter' && ev.key !== ' ') return;
                  ev.preventDefault();
                  onSelection(choisi ? null : { matiere: l.matiere, statut: l.target.statut });
                }}
              >
                <title>{`${l.source.nom} → ${l.target.nom} : ${l.value} — cliquez pour lire ces textes`}</title>
              </path>
            );
          })}
        </g>
        <g>
          {graphe.nodes.map((n) => (
            <g key={n.id}>
              <rect
                x={n.x0} y={n.y0} width={n.x1 - n.x0} height={Math.max(n.y1 - n.y0, 1)}
                fill={n.teinte || 'var(--card)'}
                stroke={n.teinte ? 'none' : 'var(--ink)'}
                strokeWidth={n.teinte ? 0 : 1}
              />
              <text x={n.x1 + 6} y={(n.y0 + n.y1) / 2} dy="0.35em" className="gvp-flux-etiquette">{n.nom}</text>
            </g>
          ))}
        </g>
      </svg>
    </figure>
  );
}

function CeQuIlAFaitDeposer({ government, mot = '' }) {
  const actif = useFiltreActif(mot);
  const couverture = government.textesCouverture || {};
  const horsCouverture = couverture.statut === 'hors_couverture';
  const partielle = couverture.statut === 'partielle';

  return (
    <section className="gvp-section" data-section="Ce qu’il a fait déposer" id="section-textes">
      <div className="gvp-section-tete">
        <span className="gvp-section-numero">04</span>
        <span className="gvp-section-trait" />
      </div>
      <h2 className="gvp-section-titre"><span>Ce qu’il a fait déposer</span></h2>
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
          <FluxEtListe mot={mot} textes={government.textes} />
        )}
      </div>
      {/* Ce qui reste n'explique pas la figure — l'épaisseur d'un ruban se lit
          sans qu'on l'écrive : c'est le 49.3 qu'aucune forme ne peut porter
          seule, et que §2 règle 4 veut nommé à côté. */}
      <p className="gvp-section-pied">
        Le 49.3 est un fait de procédure, jamais une position de vote.
      </p>
      <p className="gvp-methodo">
        <Link to="/methodologie#propose">Ce que la figure compte, et ce qu’elle refuse de compter →</Link>
      </p>
    </section>
  );
}

/* La liste ne s'ouvre qu'au clic sur un brin : 282 cartes sous la figure
   étaient un mur, et la figure servait d'index sans qu'on puisse y entrer. */
function FluxEtListe({ textes, mot = '' }) {
  const actif = useFiltreActif(mot);
  const [selection, setSelection] = useState(null);
  /* Sous un mot, la liste est DÉPLIÉE : les textes retenus s'affichent sans
     qu'il faille cliquer un brin, et un clic les restreint encore. */
  const choisis = selection
    ? textes.filter((t) => matiereDeFigure({ commission: t.commission }) === selection.matiere
      && t.statut === selection.statut)
    : actif ? textes : [];

  return (
    <>
      <FluxDesTextes textes={textes} selection={selection} onSelection={setSelection} />
      {selection ? (
        <div className="gvp-selection">
          <p className="gvp-selection-tete">
            <span className="gvp-nombre">{choisis.length}</span>
            {choisis.length === 1 ? ' texte · ' : ' textes · '}
            <span className="gvp-fort">{selection.matiere}</span>
            {' → '}
            <span className="gvp-fort">{LIBELLE_COURT_SORT[selection.statut] || selection.statut}</span>
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
        <p className="gvp-invite">Cliquez un brin de la figure pour lire les textes qu’il porte.</p>
      )}
    </>
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
 * position que la source ne déclare plus, et une activité qui n'existe pas au
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
      texte: 'Depuis 2024, l’Assemblée nationale ne déclare plus la position de ses groupes. Aucun n’est donc déclaré majoritaire, et nous ne désignons pas le plus nombreux à sa place.',
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
      texte: `Un débat n’apparaît que si la source publie son intitulé, et cet étiquetage est plus fin sur les années récentes : ${government.paroles.denominateur} des ${government.paroles.membres} membres y portent un sujet.`,
    });
  }

  lignes.push({
    quoi: 'Votes',
    texte: 'Un gouvernement ne vote pas : ce que ses membres ont voté se lit sur leur propre fiche.',
  });

  return lignes;
}

function CeQuOnNaPasPuLire({ government }) {
  const lignes = limitesDeLaFiche(government);

  return (
    <section className="gvp-section" data-section="Ce qu’on n’a pas pu lire" id="section-limites">
      <div className="gvp-section-tete">
        <span className="gvp-section-numero">05</span>
        <span className="gvp-section-trait" />
      </div>
      <h2 className="gvp-section-titre"><span>Ce qu’on n’a pas pu lire</span></h2>
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
      <p className="gvp-methodo">
        <Link to="/methodologie#couverture">Pourquoi ces limites se déclarent au lieu de se combler →</Link>
      </p>
    </section>
  );
}

/* ── La fiche ────────────────────────────────────────────────────────────── */

export default function GovernmentProfile({ government, chronologie = [], mot = '', debut = null }) {
  const actif = useFiltreActif(mot);
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
              {', Premier ministre · '}
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
      <CeQuOnNaPasPuLire government={government} />
    </main>
  );
}
