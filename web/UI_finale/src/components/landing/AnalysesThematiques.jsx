import { useEffect, useRef, useState } from 'react';
import './landing.css';

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
const MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'];
const enClair = (iso) => `${Number(iso.slice(8, 10)) === 1 ? '1er' : Number(iso.slice(8, 10))} ${MOIS[Number(iso.slice(5, 7)) - 1]} ${iso.slice(0, 4)}`;

function chargerAnalyses() {
  return fetch('/rapports.json').then((r) => (r.ok ? r.json() : []), () => []);
}

const moinsDAnimations = () =>
  typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

export default function AnalysesThematiques() {
  const [analyses, setAnalyses] = useState(null);
  const [i, setI] = useState(0);
  const pause = useRef(false);

  useEffect(() => {
    let vivant = true;
    chargerAnalyses().then((l) => vivant && setAnalyses(Array.isArray(l) ? l : []));
    return () => { vivant = false; };
  }, []);

  const n = analyses?.length || 0;
  useEffect(() => {
    if (n < 2 || moinsDAnimations()) return undefined;
    const t = setInterval(() => { if (!pause.current) setI((k) => (k + 1) % n); }, DELAI);
    return () => clearInterval(t);
  }, [n]);

  /* Rien à montrer, rien d'affiché : un encart vide dirait qu'il manque
   * quelque chose (§2 règle 5) là où il n'y a simplement pas d'article. */
  if (!n) return null;
  const voir = (k) => setI(((k % n) + n) % n);
  const arreter = () => { pause.current = true; };
  const reprendre = () => { pause.current = false; };

  return (
    <section
      className="landing-section analyses"
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
      <div className="analyses-fen">
        <div className="analyses-piste" style={{ transform: `translateX(-${i * 100}%)` }}>
          {analyses.map((a, k) => (
            <article
              key={a.fichier}
              className="analyses-sl"
              aria-roledescription="diapositive"
              aria-label={`${k + 1} sur ${n}`}
              aria-hidden={k !== i}
            >
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
            </article>
          ))}
        </div>
      </div>
      {n > 1 && (
        <div className="analyses-pts">
          {analyses.map((a, k) => (
            <button
              key={a.fichier}
              type="button"
              className={`analyses-pt${k === i ? ' on' : ''}`}
              aria-label={`Analyse ${k + 1}`}
              aria-current={k === i}
              onClick={() => voir(k)}
            />
          ))}
        </div>
      )}
    </section>
  );
}
