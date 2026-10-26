import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getArticles, FIN_EVENEMENT_CANDIDATS, dateEnClair } from '../data/articles';
import './BandeauArticles.css';

/* ── « Articles » ouvre un bandeau sous celui du site (#1329) ─────────────────
 *
 * Arbitré sur maquette le 26/10/2026 (« Le bandeau de l'article est bien ») :
 * une bande sombre, de la teinte de la carte héro de l'accueil, d'un bord à
 * l'autre ; les articles en cartes — vignette, date, titre —, du plus récent au
 * plus ancien, et « Tous les articles → » vers l'index. Écarté : un menu
 * déroulant sous le bouton.
 *
 * LA PREMIÈRE CARTE EST L'ÉVÉNEMENT DES CANDIDATS, comme la première diapositive
 * du carrousel de l'accueil, et jusqu'à la même date : même vignette (« Mai
 * 2027 »), mêmes mots, même destination.
 *
 * Au-delà de ce que la largeur porte, la rangée défile de côté. La liste vient
 * de `public/rapports.json`, écrit depuis le dossier des articles : rien n'est
 * recopié ici.
 */
export default function BandeauArticles({ id, ouvert }) {
  const [articles, setArticles] = useState(null);

  useEffect(() => {
    if (!ouvert || articles) return undefined;
    let vivant = true;
    getArticles().then((l) => vivant && setArticles(l));
    return () => { vivant = false; };
  }, [ouvert, articles]);

  const evenement = new Date().toISOString().slice(0, 10) < FIN_EVENEMENT_CANDIDATS;

  return (
    <section aria-label="Les articles" className="bandeau-articles" hidden={!ouvert} id={id}>
      {ouvert && (
        <div className="bandeau-articles-interieur">
          <div className="bandeau-articles-tete">
            <span className="bandeau-articles-titre">Les articles</span>
            <a className="bandeau-articles-tous" href="/rapports">Tous les articles →</a>
          </div>
          <ul className="bandeau-articles-rangee">
            {evenement && (
              <li>
                <Link className="bandeau-article" to="/candidats">
                  <span aria-hidden="true" className="bandeau-article-img bandeau-article-img--evenement">
                    <small>Mai</small><b>2027</b>
                  </span>
                  <span className="bandeau-article-date">Jusqu’en mai 2027</span>
                  <b className="bandeau-article-t">Focus sur les candidats à la présidentielle</b>
                </Link>
              </li>
            )}
            {(articles || []).map((a) => (
              <li key={a.fichier}>
                <a className="bandeau-article" href={`/rapports/${a.fichier}`}>
                  <span className="bandeau-article-img">
                    {a.vignette && <img alt="" loading="lazy" src={`/rapports/${a.vignette}`} />}
                  </span>
                  <span className="bandeau-article-date">{dateEnClair(a.date)}</span>
                  <b className="bandeau-article-t">{a.titre}</b>
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
