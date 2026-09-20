import { useRef } from 'react';
import { useDragScroll } from '../hooks/useDragScroll';
import './ScrollRow.css';

/* `replie` : les pastilles passent à la ligne au lieu de défiler.
 *
 * UN DÉFILEMENT HORIZONTAL CLASSE CE QU'IL CONTIENT. Trente candidats sur une
 * seule ligne, c'est la liste alphabétique qui décide de la visibilité : les
 * premiers sont là, les derniers demandent de faire défiler pour être trouvés.
 * Ce n'est pas un classement que nous publions — c'est un classement que la
 * forme fabrique (§2 règle 1). Repliées, les trente pastilles sont toutes à
 * l'écran, à égalité.
 *
 * Le glisser-déposer n'a plus d'objet quand rien ne défile : la référence n'est
 * pas attachée, le hook ne trouve rien et ne pose aucun écouteur. */
export default function ScrollRow({ children, ariaLabel, className = '', replie = false }) {
  const ref = useRef(null);
  useDragScroll(ref);

  return (
    <div
      className={`scroll-row${replie ? ' scroll-row--replie' : ''} ${className}`}
      ref={replie ? undefined : ref}
      role="list"
      aria-label={ariaLabel}
    >
      {children}
    </div>
  );
}
