import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { getCandidatesList } from '../../data';
import { useAsyncData } from '../../hooks/useAsyncData';
import { FIN_EVENEMENT_CANDIDATS as FIN_EVENEMENT, dateEnClair as enClair, getArticles } from '../../data/articles';
import { useEcranEtroit } from '../../hooks/useLargeur';
import './landing.css';

/* L'ÉVÉNEMENT EN TÊTE DU CARROUSEL (#1329, arbitré le 22/10/2026) : tant que le
 * volet des candidats est ouvert, il est la première diapositive, celle que le
 * lecteur voit en arrivant ; sa tuile sous la carte héro a été retirée. La
 * vignette dit la borne (« Mai 2027 »), 2027 un cran au-dessus de Mai. Le
 * nombre de candidats est lu dans le manifeste, jamais écrit ici. La date de
 * fin est celle du bandeau « Articles », qui ouvre sur la même carte. */

/* ── LES ANALYSES THÉMATIQUES, AU BAS DE L'ACCUEIL (15/10/2026) ──────────────
 *
 * Arbitré sur maquette, étape par étape : un carrousel plutôt qu'un bandeau
 * (le défilement continu a été écarté), AU-DESSUS DU PIED DE PAGE plutôt que
 * sous la barre du site, À LA LARGEUR DES BLOCS de l'accueil et non de bord à
 * bord, haut d'environ la moitié du bloc sombre, avec la description de
 * l'article sous son titre (forme A) pour que le bloc ne reste pas vide.
 *
 * L'ORDRE EST CELUI DE LA DATE, le plus récent d'abord : jamais un classement
 * (§2 règle 1). La liste vient de `public/rapports.json`, écrit par
 * `scripts/index-rapports.mjs` depuis le dossier — rien n'est recopié ici.
 *
 * LE MOUVEMENT SE COUPE : pause au survol et au clavier, et aucune rotation
 * pour qui a demandé moins d'animations — les flèches et les points restent.
 */
const DELAI = 6000;

const moinsDAnimations = () =>
  typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

export default function AnalysesThematiques({ dansHero = false }) {
  const [analyses, setAnalyses] = useState(null);
  const { data: candidats } = useAsyncData(getCandidatesList, []);
  const evenement = candidats?.length && new Date().toISOString().slice(0, 10) < FIN_EVENEMENT ? candidats.length : null;
  const [i, setI] = useState(0);
  const pause = useRef(false);
  const fenRef = useRef(null);
  /* Au téléphone (#1372, 28/10/2026), le titre d'une diapositive ne se coupe
   * plus : la fenêtre prend la hauteur de la plus haute, rien n'est rogné. */
  const etroit = useEcranEtroit();

  useEffect(() => {
    let vivant = true;
    getArticles().then((l) => vivant && setAnalyses(Array.isArray(l) ? l : []));
    return () => { vivant = false; };
  }, []);

  const diapos = analyses ? [...(evenement ? [{ fichier: 'evenement', evenement: true }] : []), ...analyses] : [];
  const n = diapos.length;
  useEffect(() => {
    if (n < 2 || moinsDAnimations()) return undefined;
    const t = setInterval(() => { if (!pause.current) setI((k) => (k + 1) % n); }, DELAI);
    return () => clearInterval(t);
  }, [n]);

  /* LA CARTE HÉRO A LA HAUTEUR DE LA DIAPOSITIVE LA PLUS COURTE (23/10/2026) :
   * elle ne bouge pas au défilement, et ne garde pas de vide sous les plus
   * courtes. Une diapositive plus haute perd d'abord des lignes de sa
   * description, puis, s'il le faut, de son titre (« … »), jamais sa première
   * ligne. Mesuré à la largeur réelle, donc refait quand elle change. */
  useLayoutEffect(() => {
    const fen = fenRef.current;
    if (!dansHero || !fen || !n) return undefined;
    const lignes = (el) => {
      const lh = parseFloat(getComputedStyle(el).lineHeight) || parseFloat(getComputedStyle(el).fontSize) * 1.25;
      return Math.max(1, Math.round(el.offsetHeight / lh));
    };
    const couper = (el, k) => {
      if (!el) return;
      if (k === null) { el.style.removeProperty('display'); el.style.removeProperty('-webkit-line-clamp'); el.style.removeProperty('-webkit-box-orient'); el.style.removeProperty('overflow'); return; }
      if (k === 0) { el.style.display = 'none'; return; }
      el.style.display = '-webkit-box';
      el.style.webkitBoxOrient = 'vertical';
      el.style.webkitLineClamp = String(k);
      el.style.overflow = 'hidden';
    };
    const ajuster = () => {
      const diapos = [...fen.querySelectorAll('.analyses-sl')];
      fen.style.height = '';
      fen.classList.add('analyses-fen--mesure');
      diapos.forEach((d) => { couper(d.querySelector('.analyses-t'), null); couper(d.querySelector('.analyses-desc'), null); });
      if (etroit) {
        fen.classList.remove('analyses-fen--mesure');
        fen.style.height = `${Math.max(...diapos.map((d) => d.offsetHeight))}px`;
        return;
      }
      const min = Math.min(...diapos.map((d) => d.offsetHeight));
      diapos.forEach((d) => {
        const titre = d.querySelector('.analyses-t'), desc = d.querySelector('.analyses-desc');
        let nd = desc ? lignes(desc) : 0, nt = lignes(titre);
        while (d.offsetHeight > min + 1) {
          if (nd > 0) { nd -= 1; couper(desc, nd); } else if (nt > 1) { nt -= 1; couper(titre, nt); } else break;
        }
      });
      fen.classList.remove('analyses-fen--mesure');
      fen.style.height = `${min}px`;
    };
    ajuster();
    let largeur = fen.offsetWidth;
    const ro = typeof ResizeObserver === 'undefined' ? null : new ResizeObserver(() => {
      if (fen.offsetWidth !== largeur) { largeur = fen.offsetWidth; ajuster(); }
    });
    ro?.observe(fen);
    document.fonts?.ready?.then(ajuster);
    return () => ro?.disconnect();
  }, [dansHero, n, etroit]);

  /* Rien à montrer, rien d'affiché : un encart vide dirait qu'il manque
   * quelque chose (§2 règle 5) là où il n'y a simplement pas d'article. */
  if (!n) return null;
  const voir = (k) => setI(((k % n) + n) % n);
  const arreter = () => { pause.current = true; };
  const reprendre = () => { pause.current = false; };

  return (
    <section
      className={`landing-section analyses${dansHero ? ' analyses--hero' : ''}`}
      aria-roledescription="carrousel"
      aria-label="Analyses thématiques"
      onMouseEnter={arreter}
      onMouseLeave={reprendre}
      onFocus={arreter}
      onBlur={reprendre}
    >
      {n > 1 && (
        <div className="analyses-nav">
          <button type="button" className="analyses-b" aria-label="Analyse précédente" onClick={() => voir(i - 1)}>‹</button>
          <span className="analyses-pos">{i + 1} / {n}</span>
          <button type="button" className="analyses-b" aria-label="Analyse suivante" onClick={() => voir(i + 1)}>›</button>
        </div>
      )}
      <div className="analyses-fen" ref={fenRef}>
        <div className="analyses-piste" style={{ transform: `translateX(-${i * 100}%)` }}>
          {diapos.map((a, k) => (
            <article
              key={a.fichier}
              className="analyses-sl"
              aria-roledescription="diapositive"
              aria-label={`${k + 1} sur ${n}`}
              aria-hidden={k !== i}
            >
              {a.evenement ? (
                <Link className="analyses-lien" to="/candidats" tabIndex={k === i ? 0 : -1}>
                  <span className="analyses-img analyses-img--evenement" aria-hidden="true">
                    <small>Mai</small><b>2027</b>
                  </span>
                  <span className="analyses-txt">
                    <span className="analyses-lab">Événement</span>
                    <span className="analyses-d">Jusqu’en mai 2027</span>
                    <span className="analyses-t">Focus sur les candidats à la présidentielle</span>
                    <span className="analyses-desc">{evenement} candidats déclarés : leurs mandats, leurs votes, leurs textes et leurs prises de parole, sourcés.</span>
                    <span className="analyses-lire">Voir les fiches →</span>
                  </span>
                </Link>
              ) : (
              <a className="analyses-lien" href={`/rapports/${a.fichier}`} tabIndex={k === i ? 0 : -1}>
                <span className="analyses-img">
                  {a.vignette && <img src={`/rapports/${a.vignette}`} alt="" loading="lazy" />}
                </span>
                <span className="analyses-txt">
                  <span className="analyses-lab">Analyse thématique</span>
                  <span className="analyses-d">{enClair(a.date)}</span>
                  <span className="analyses-t">{a.titre}</span>
                  <span className="analyses-desc">{a.description}</span>
                  <span className="analyses-lire">Lire l’analyse →</span>
                </span>
              </a>
              )}
            </article>
          ))}
        </div>
      </div>
      {n > 1 && (
        <div className="analyses-pts">
          {diapos.map((a, k) => (
            <button
              key={a.fichier}
              type="button"
              className={`analyses-pt${k === i ? ' on' : ''}`}
              aria-label={a.evenement ? 'Événement' : `Analyse ${k + 1}`}
              aria-current={k === i}
              onClick={() => voir(k)}
            />
          ))}
        </div>
      )}
    </section>
  );
}
