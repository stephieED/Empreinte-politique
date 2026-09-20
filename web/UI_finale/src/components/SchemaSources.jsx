import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { DONNEES_SCHEMA, FICHES_SCHEMA, SOURCES_SCHEMA } from '../data/schemaSources';
import sourcesConfig from '../data/sources.config';
import './SchemaSources.css';

/* ── Le flux des sources : source → ce qu'elle apporte → où cela se lit (#951) ──
 *
 * Un dessin, pas un graphique : aucune épaisseur ne porte de quantité. Un trait
 * épais se lirait comme « cette source compte plus », ce que rien ne mesure ici.
 *
 * LE NŒUD PORTE LES INFORMATIONS DE SA SOURCE — cadence, couverture, licence —
 * à la place des cartes repliées qui étaient dessous (16/09/2026). Deux gestes,
 * choisis sur maquette, et choisis selon le POINTEUR, pas selon la largeur :
 *
 *   - une souris (`hover: hover` et `pointer: fine`) : le survol montre une
 *     infobulle, et le clic ouvre la source dans un nouvel onglet ;
 *   - un doigt : le toucher ouvre le nœud en BANDE sur toute la largeur, qui
 *     pousse le schéma vers le bas, et le lien vers la source est dans la bande.
 *     Une tablette tactile large a le geste du doigt : elle n'a pas de survol.
 *
 * La figure garde sa largeur et défile sur mobile : la replier en colonne
 * casserait le trajet, qui est ce qu'elle montre. */

const PAS = 42;
const HAUT = 30;
const HAUT_ENTETE = 34;
const LARGEUR = 880;
const COLONNES = { source: [0, 210], donnee: [330, 262], fiche: [712, 168] };
const REQUETE_SOURIS = '(hover: hover) and (pointer: fine)';

const CARTES = Object.fromEntries(sourcesConfig.map((c) => [c.id, c]));

const courbe = (x1, y1, x2, y2) => {
  const m = (x1 + x2) / 2;
  return `M${x1},${y1} C${m},${y1} ${m},${y2} ${x2},${y2}`;
};

function useSouris() {
  const lire = () => typeof window !== 'undefined' && Boolean(window.matchMedia?.(REQUETE_SOURIS).matches);
  const [souris, setSouris] = useState(lire);
  useEffect(() => {
    const requete = window.matchMedia?.(REQUETE_SOURIS);
    if (!requete) return undefined;
    const suivre = () => setSouris(requete.matches);
    requete.addEventListener('change', suivre);
    return () => requete.removeEventListener('change', suivre);
  }, []);
  return souris;
}

function Details({ source, avecLien }) {
  const carte = CARTES[source.config];
  return (
    <>
      <p className="ss-detail-titre">{carte.nom}</p>
      <dl className="ss-detail-liste">
        <div>
          <dt>Ce qu’elle couvre</dt>
          <dd>{carte.contenuCouvert}</dd>
        </div>
        <div>
          <dt>Mise à jour</dt>
          <dd>{carte.cadenceMiseAJour}</dd>
        </div>
        <div>
          <dt>Licence</dt>
          <dd>
            {carte.licence} — {carte.implication}
          </dd>
        </div>
        {carte.couverturePeriode && (
          <div>
            <dt>Couverture limitée</dt>
            <dd>{carte.couverturePeriode}</dd>
          </div>
        )}
      </dl>
      {avecLien && (
        <a className="ss-detail-lien" href={source.url} target="_blank" rel="noopener noreferrer">
          Ouvrir {source.nom} ↗
        </a>
      )}
    </>
  );
}

export default function SchemaSources() {
  const souris = useSouris();
  const [survol, setSurvol] = useState(null);
  const [ouverte, setOuverte] = useState(null);
  const [hauteurBande, setHauteurBande] = useState(0);
  const bandeRef = useRef(null);
  const defileRef = useRef(null);
  // La bande se cale sur ce que l'écran MONTRE du schéma, pas sur ses 880 px :
  // sinon, sur mobile, la licence et la cadence tombaient hors de l'écran.
  const [vue, setVue] = useState({ gauche: 0, largeur: LARGEUR });

  useEffect(() => {
    const defile = defileRef.current;
    if (!defile) return undefined;
    const lire = () =>
      setVue({ gauche: defile.scrollLeft, largeur: Math.min(LARGEUR, defile.clientWidth) });
    lire();
    defile.addEventListener('scroll', lire, { passive: true });
    window.addEventListener('resize', lire);
    return () => {
      defile.removeEventListener('scroll', lire);
      window.removeEventListener('resize', lire);
    };
  }, []);

  // Passer de la souris au doigt referme ce qui était ouvert dans l'autre geste.
  useEffect(() => {
    setOuverte(null);
    setSurvol(null);
  }, [souris]);

  useLayoutEffect(() => {
    setHauteurBande(ouverte && bandeRef.current ? bandeRef.current.offsetHeight + 12 : 0);
  }, [ouverte, vue.largeur]);

  const rangOuverte = ouverte ? SOURCES_SCHEMA.findIndex((s) => s.id === ouverte) : -1;
  const decalage = (rang) => (rangOuverte >= 0 && rang > rangOuverte ? hauteurBande : 0);
  const yLigne = (rang) => HAUT_ENTETE + rang * PAS + decalage(rang);
  const yDe = (liste, id) => yLigne(liste.findIndex((x) => x.id === id));
  const hauteur = HAUT_ENTETE + SOURCES_SCHEMA.length * PAS + 10 + hauteurBande;

  // Ce qu'on regarde : la source survolée à la souris, la source ouverte au doigt.
  const focale = survol || ouverte;
  const allumees = new Set();
  if (focale) {
    allumees.add(focale);
    for (const d of DONNEES_SCHEMA) {
      if (d.id === focale || d.de.includes(focale)) {
        allumees.add(d.id);
        d.de.forEach((s) => allumees.add(s));
      }
    }
    for (const f of FICHES_SCHEMA) {
      if (f.id === focale) f.de.forEach((d) => allumees.add(d));
      if (f.id === focale || f.de.some((d) => allumees.has(d))) allumees.add(f.id);
    }
  }
  const etat = (...cles) => (!focale ? '' : cles.every((c) => allumees.has(c)) ? ' ss-vif' : ' ss-estompe');
  const suivre = (id) => ({
    onMouseEnter: () => setSurvol(id),
    onMouseLeave: () => setSurvol(null),
    onFocus: () => setSurvol(id),
    onBlur: () => setSurvol(null),
  });

  const sourceSurvolee = souris && survol ? SOURCES_SCHEMA.find((s) => s.id === survol) : null;
  const rangSurvole = sourceSurvolee ? SOURCES_SCHEMA.indexOf(sourceSurvolee) : -1;

  return (
    <div className="ss">
      <div className="ss-defile" ref={defileRef}>
        <div className="ss-scene" style={{ height: hauteur }}>
          <svg
            className="ss-svg"
            width={LARGEUR}
            height={hauteur}
            viewBox={`0 0 ${LARGEUR} ${hauteur}`}
            // Pas de role="img" : il rendrait les onze sources muettes pour un
            // lecteur d'écran.
            aria-labelledby="ss-titre"
          >
            <title id="ss-titre">Ce que chaque source apporte, et sur quelle fiche cela se lit</title>
            <defs>
              <pattern id="ss-hachure" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
                <rect width="5" height="5" className="ss-hachure-fond" />
                <rect width="2" height="5" className="ss-hachure-trait" />
              </pattern>
            </defs>

            <text className="ss-entete" x={COLONNES.source[0]} y="14">SOURCE</text>
            <text className="ss-entete" x={COLONNES.donnee[0]} y="14">CE QU’ELLE APPORTE</text>
            <text className="ss-entete" x={COLONNES.fiche[0]} y="14">OÙ CELA SE LIT</text>

            {DONNEES_SCHEMA.flatMap((d) =>
              d.de.map((sid) => {
                const s = SOURCES_SCHEMA.find((x) => x.id === sid);
                return (
                  <path
                    key={`${sid}-${d.id}`}
                    className={`ss-lien ss-lien--${s.teinte} ss-lien--${s.statut}${etat(sid, d.id)}`}
                    d={courbe(
                      COLONNES.source[0] + COLONNES.source[1],
                      yDe(SOURCES_SCHEMA, sid) + HAUT / 2,
                      COLONNES.donnee[0],
                      yDe(DONNEES_SCHEMA, d.id) + HAUT / 2,
                    )}
                  />
                );
              }),
            )}
            {FICHES_SCHEMA.flatMap((f) =>
              f.de.map((did) => (
                <path
                  key={`${did}-${f.id}`}
                  className={`ss-lien ss-lien--fiche${etat(did, f.id)}`}
                  d={courbe(
                    COLONNES.donnee[0] + COLONNES.donnee[1],
                    yDe(DONNEES_SCHEMA, did) + HAUT / 2,
                    COLONNES.fiche[0],
                    yLigne(f.ligne) + HAUT / 2,
                  )}
                />
              )),
            )}

            {SOURCES_SCHEMA.map((s, rang) => {
              const y = yLigne(rang);
              const [x, w] = COLONNES.source;
              const classe = `ss-noeud ss-source ss-source--${s.teinte} ss-source--${s.statut}${
                ouverte === s.id ? ' ss-source--ouverte' : ''
              }${etat(s.id)}`;
              const contenu = (
                <>
                  <rect className="ss-pave" x={x + 0.75} y={y + 0.75} width={w - 1.5} height={HAUT - 1.5} rx="7" />
                  {s.statut === 'retiree' && (
                    <rect x={x + 5} y={y + 5} width="10" height={HAUT - 10} rx="2" fill="url(#ss-hachure)" />
                  )}
                  <text x={x + (s.statut === 'retiree' ? 22 : 10)} y={y + HAUT / 2 + 4.5}>{s.nom}</text>
                  <text className="ss-marque" x={x + w - 12} y={y + HAUT / 2 + 4.5} textAnchor="end" aria-hidden="true">
                    {souris ? '↗' : ouverte === s.id ? '−' : '+'}
                  </text>
                </>
              );
              // À la souris, un LIEN : le clic ouvre la source. Au doigt, un
              // BOUTON : le toucher ouvre la bande, qui porte le lien.
              return souris ? (
                <a
                  key={s.id}
                  href={s.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label={`${s.nom} — ouvrir la source dans un nouvel onglet`}
                  className={classe}
                  {...suivre(s.id)}
                >
                  {contenu}
                </a>
              ) : (
                <g
                  key={s.id}
                  className={classe}
                  role="button"
                  tabIndex={0}
                  aria-expanded={ouverte === s.id}
                  aria-label={`${s.nom} — ${ouverte === s.id ? 'refermer' : 'afficher'} ses informations`}
                  onClick={() => setOuverte((o) => (o === s.id ? null : s.id))}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      setOuverte((o) => (o === s.id ? null : s.id));
                    }
                  }}
                >
                  {contenu}
                </g>
              );
            })}
            {DONNEES_SCHEMA.map((d, rang) => {
              const y = yLigne(rang);
              const [x, w] = COLONNES.donnee;
              return (
                <g key={d.id} className={`ss-noeud ss-donnee${etat(d.id)}`} {...(souris ? suivre(d.id) : {})}>
                  <rect x={x} y={y} width={w} height={HAUT} rx="7" />
                  <text x={x + 10} y={y + HAUT / 2 + 4.5}>{d.nom}</text>
                </g>
              );
            })}
            {FICHES_SCHEMA.map((f) => {
              const y = yLigne(f.ligne);
              const [x, w] = COLONNES.fiche;
              return (
                <g key={f.id} className={`ss-noeud ss-fiche${etat(f.id)}`} {...(souris ? suivre(f.id) : {})}>
                  <rect x={x} y={y} width={w} height={HAUT} rx="7" />
                  <text x={x + 10} y={y + HAUT / 2 + 4.5}>{f.nom}</text>
                </g>
              );
            })}
          </svg>

          {/* LA BANDE, au doigt : sous la source, sur toute la largeur. */}
          {!souris && rangOuverte >= 0 && (
            <div
              ref={bandeRef}
              className="ss-detail ss-detail--bande"
              style={{
                top: HAUT_ENTETE + rangOuverte * PAS + HAUT + 6,
                left: vue.gauche,
                width: vue.largeur,
              }}
            >
              <Details source={SOURCES_SCHEMA[rangOuverte]} avecLien />
              <button type="button" className="ss-detail-fermer" onClick={() => setOuverte(null)}>
                Fermer
              </button>
            </div>
          )}

          {/* L'INFOBULLE, à la souris : à droite de la source, au-dessus d'elle
              dans la moitié basse pour ne pas sortir du cadre. */}
          {sourceSurvolee && (
            <div
              className={`ss-detail ss-detail--bulle${rangSurvole > 5 ? ' ss-detail--haut' : ''}`}
              style={{
                left: COLONNES.source[1] + 14,
                top: rangSurvole > 5 ? yLigne(rangSurvole) + HAUT + 8 : yLigne(rangSurvole) - 8,
              }}
              aria-hidden="true"
            >
              <Details source={sourceSurvolee} avecLien={false} />
            </div>
          )}
        </div>
      </div>

      <ul className="ss-legende">
        <li><i className="ss-cle ss-cle--a-venir" />À venir</li>
        <li><i className="ss-cle ss-cle--an" />Assemblée</li>
        <li><i className="ss-cle ss-cle--senat" />Sénat</li>
        <li><i className="ss-cle ss-cle--pe" />Europe</li>
        <li><i className="ss-cle ss-cle--gouv" />Gouvernement</li>
        <li><i className="ss-cle ss-cle--local" />Local</li>
        <li><i className="ss-cle ss-cle--candidat" />Qui est candidat</li>
        <li><i className="ss-cle ss-cle--citee" />Citée, relue à la main</li>
      </ul>
    </div>
  );
}
