import { useEffect, useState } from 'react';
import { articlesDeLaPeriode, dateEnClair, getArticles } from '../data/articles';
import './ArticlesDeLaPeriode.css';

/* ── « Articles sur cette période » (#1329) ──────────────────────────────────
 *
 * Sur une fiche de législature ou de gouvernement : les articles dont la date
 * tombe dans sa période. Un article publié ne se modifie jamais (AGENTS.md §1) :
 * c'est la fiche qui renvoie à l'article. Aucun article dans la période, aucun
 * encart — un encart vide se lirait comme un manque (§2 règle 5).
 */
export default function ArticlesDeLaPeriode({ debut, fin }) {
  const [articles, setArticles] = useState(null);
  useEffect(() => {
    let vivant = true;
    getArticles().then((l) => vivant && setArticles(l));
    return () => { vivant = false; };
  }, []);
  const retenus = articlesDeLaPeriode(articles, debut, fin);
  if (!retenus.length) return null;
  return (
    <section aria-labelledby="articles-periode-titre" className="adp">
      <h2 className="adp-titre" id="articles-periode-titre">Articles sur cette période</h2>
      <ul className="adp-liste">
        {retenus.map((a) => (
          <li key={a.fichier}>
            <a className="adp-article" href={`/rapports/${a.fichier}`}>
              <span className="adp-date">{dateEnClair(a.date)}</span>
              <b className="adp-t">{a.titre}</b>
            </a>
          </li>
        ))}
      </ul>
    </section>
  );
}
