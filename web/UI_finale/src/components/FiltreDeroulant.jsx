import { useId, useState } from 'react';
import { formatNumber } from '../utils/lecture';
import './FiltreDeroulant.css';

/* ── Un filtre en pastilles, au téléphone : une ligne qu'on déroule (#1372) ───
 *
 * Forme B, arbitrée le 28/10/2026. Sous 720 px, les rangées de pastilles
 * s'empilaient de façon irrégulière : sept natures sur 200 px de haut à 390.
 * Chaque filtre devient UNE boîte pleine largeur — l'état à gauche (« Toutes »,
 * ou les choix faits, à la suite), le nombre et ▾ à droite. Touchée, elle
 * déroule la liste DANS LE FLUX, sous elle : une ligne par choix, sa case, son
 * libellé, son nombre. Les choix à 0 sont retirés au lieu d'être grisés.
 *
 * Le composant ne décide rien : la sélection reste celle des pastilles de
 * l'ordinateur, que l'appelant garde telles quelles au-delà de 720 px
 * (`useEcranEtroit()`). Il reçoit les choix et leur état, et rend la main par
 * `onChoisir(cle)` — le même geste qu'un clic sur la pastille.
 *
 * `choix` : [{ cle, libelle, n, choisi, marque? }] — `marque`, la pastille de
 * couleur ou de trame que porte la pastille d'ordinateur, quand elle sert de
 * légende à la figure.
 * `unique` : un seul choix à la fois (boutons radio), la liste se referme.
 * `tout` : rien n'est retenu en particulier — la boîte dit `libelleTout`.
 * `nombre` : ce que la boîte écrit à droite ; à défaut, la somme des choix
 * retenus, ou de tous quand `tout`.
 * `pied` : ce qui suit la liste dans le déroulé (« Tout retirer »). */
export default function FiltreDeroulant({ choix, etiquette, libelleTout, nombre, onChoisir, pied, tout, unique = false }) {
  const [ouvert, setOuvert] = useState(false);
  const id = useId();
  // Un choix à 0 n'est plus proposé ; il reste s'il est retenu, pour qu'on
  // puisse le retirer.
  const proposes = choix.filter((c) => c.n > 0 || (c.choisi && !tout));
  const retenus = proposes.filter((c) => c.choisi);
  const etat = tout ? libelleTout : retenus.map((c) => c.libelle).join(', ') || libelleTout;
  const total = nombre ?? formatNumber((tout ? proposes : retenus).reduce((s, c) => s + c.n, 0));
  const choisir = (cle) => {
    onChoisir(cle);
    if (unique) setOuvert(false);
  };
  return (
    <div className="fd">
      <button
        aria-controls={id}
        aria-expanded={ouvert}
        aria-label={`${etiquette} : ${etat}`}
        className="fd-boite"
        onClick={() => setOuvert((o) => !o)}
        type="button"
      >
        <b className="fd-etat">{etat}</b>
        <span className="fd-n">
          {total} <span aria-hidden="true">{ouvert ? '▴' : '▾'}</span>
        </span>
      </button>
      {ouvert && (
        <div className="fd-liste" id={id} role="group" aria-label={etiquette}>
          {proposes.map((c) => (
            <label className="fd-choix" key={c.cle ?? 'tous'}>
              <input
                checked={c.choisi}
                name={unique ? id : undefined}
                onChange={() => choisir(c.cle)}
                type={unique ? 'radio' : 'checkbox'}
              />
              {c.marque}
              <span className="fd-lib">{c.libelle}</span>
              <span className="fd-choix-n">{formatNumber(c.n)}</span>
            </label>
          ))}
          {pied && <div className="fd-pied">{pied}</div>}
        </div>
      )}
    </div>
  );
}
