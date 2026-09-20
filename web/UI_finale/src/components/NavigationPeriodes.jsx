/* ── La navigation par période politique, partagée (#328) ─────────────────────
 *
 * Deux sections de la fiche découpent le temps de la même façon — « Ce qu'il a
 * voté » et « Ce qu'il a dit » —, et la propriétaire a demandé le 09/09/2026
 * qu'elles se manœuvrent à l'identique. Deux copies du même mécanisme, c'est
 * deux mécanismes qui divergeront : il n'y en a donc qu'un, ici.
 *
 * Le rail donne à voir d'un coup ce qu'une navigation séquentielle perd : un
 * segment par période, LARGE EN PROPORTION de son poids, dans l'ordre du temps.
 * L'année n'est écrite qu'au-dessus de 12 % de la largeur — en dessous, une
 * date tronquée se lirait comme une date fausse, ce qui est pire qu'une date
 * absente. Le segment garde alors sa taille, donc son information, et rend sa
 * date au titre et aux deux flèches.
 *
 * LES FLÈCHES DU CLAVIER SONT PORTÉES PAR LE CONTENEUR, pas par `window`
 * (#328). Tant qu'une seule section les écoutait, un écouteur global marchait ;
 * à deux, une flèche déplaçait les deux sections à la fois. Elles n'agissent
 * donc que si le focus est dans la navigation — ce qui est exactement l'état
 * où l'on vient de cliquer une flèche ou un segment.
 */
import { formatNumber } from '../utils/lecture';
import './NavigationPeriodes.css';

const mois = (d) => (d ? `${d.slice(0, 4)}/${d.slice(5, 7)}` : '');

const PART_MINIMALE_ETIQUETTE = 12;

export default function NavigationPeriodes({
  periodes,
  index,
  onIndex,
  poids,
  libelle,
  // `unite` porte ses deux formes : « 1 textes » est une faute que le lecteur
  // voit avant le chiffre.
  unite,
  uniteSingulier = unite,
  // « Toutes les périodes » : `index === null`. Absent par défaut — « Ce qu'il
  // a voté » n'en a pas, parce qu'y cumuler deux périodes reformerait le total
  // de carrière que la vue refuse.
  avecTout = false,
  libelleTout = 'Voir toutes les périodes',
  libelleRetour = 'Revenir à une seule période',
}) {
  const tout = index === null;
  const total = periodes.reduce((n, p) => n + poids(p), 0) || 1;
  const mot = (n) => (n > 1 ? unite : uniteSingulier);

  const aller = (i) => {
    if (i < 0 || i >= periodes.length) return;
    onIndex(i);
  };

  const fleche = (k, sens, quoi, bout) => {
    const p = tout ? null : periodes[k];
    return (
      <button
        type="button"
        className={`np-fleche np-fleche--${sens}`}
        onClick={() => aller(k)}
        disabled={!p}
      >
        <span className="np-fleche-quoi">{quoi}</span>
        <span className="np-fleche-lib">
          {p ? `${p.debut.slice(0, 4)} · ${libelle(p)}` : bout}
        </span>
      </button>
    );
  };

  /* Les deux flèches désactivées ne disent PAS la même chose : à droite, on est
     au bout le plus RÉCENT de la période couverte, pas à son début. */
  const surTouche = (e) => {
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
    if (tout) return;
    const cible = e.target;
    if (cible instanceof HTMLElement && cible.closest('input, textarea, select')) return;
    aller(index + (e.key === 'ArrowLeft' ? -1 : 1));
  };

  return (
    <div className="np" onKeyDown={surTouche}>
      <div className="np-nav">
        {fleche(tout ? -1 : index - 1, 'precedent', '← période précédente', 'début de la période couverte')}
        <div className={`np-rail${tout ? ' np-rail--tout' : ''}`}>
          {periodes.map((p, i) => {
            const part = (poids(p) / total) * 100;
            return (
              <button
                type="button"
                key={p.cle}
                className={`np-rail-seg${p.sansRepere ? ' np-rail-seg--absent' : ''}`}
                style={{ flex: `${part} 1 0` }}
                aria-current={!tout && i === index}
                onClick={() => aller(i)}
                title={`${mois(p.debut)} → ${mois(p.fin)} · ${libelle(p)} · ${formatNumber(poids(p))} ${mot(poids(p))}`}
              >
                {part >= PART_MINIMALE_ETIQUETTE && (
                  <span className="np-rail-an">{p.debut.slice(0, 4)}</span>
                )}
              </button>
            );
          })}
        </div>
        {fleche(tout ? -1 : index + 1, 'suivant', 'période suivante →', 'fin de la période couverte')}
      </div>
      <p className="np-position">
        {tout
          ? `Toutes les périodes · ${formatNumber(total)} ${mot(total)}`
          : `Période ${index + 1} sur ${periodes.length} · ${formatNumber(poids(periodes[index]))} ${mot(poids(periodes[index]))} · les flèches ← → du clavier naviguent aussi`}
        {avecTout && (
          <button
            type="button"
            className="np-tout"
            onClick={() => onIndex(tout ? periodes.length - 1 : null)}
          >
            {tout ? libelleRetour : libelleTout}
          </button>
        )}
      </p>
    </div>
  );
}
