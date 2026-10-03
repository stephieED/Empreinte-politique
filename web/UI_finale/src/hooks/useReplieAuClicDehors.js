import { useEffect, useRef } from 'react';

/* ── Ce qui s'ouvre au clic se replie au clic ailleurs (02/10/2026) ───────────
 *
 * La bulle d'information le faisait déjà. Les listes ouvertes sous une figure
 * et les plis, non : un texte ouvert en section 2 restait à l'écran pendant
 * qu'on en ouvrait un autre en section 3, et la fiche s'allongeait à mesure
 * qu'on la lisait. La propriétaire a posé la règle pour tout ce qui s'ouvre :
 * un clic HORS du bloc le replie — donc un seul bloc ouvert à la fois, puisque
 * ouvrir le suivant est un clic hors du précédent.
 *
 * « HORS DU BLOC » se juge sur `ref` : la carte entière, figure et liste
 * comprises. Cliquer un lien de la liste, ou un autre carré de la même figure,
 * ne replie rien.
 *
 * LA BARRE DE DÉFILEMENT N'EST PAS UN CLIC AILLEURS. Elle appartient à la
 * page, pas à un bloc : la saisir pour lire la suite d'une liste longue ne doit
 * pas la refermer. Le navigateur la rapporte comme un clic sur l'élément
 * racine.
 *
 * AU CLIC, PAS À L'APPUI — et l'élément cliqué ne bouge pas. Replier un bloc
 * retire de la hauteur AU-DESSUS de ce que le lecteur vient de viser. Fait à
 * l'appui (`mousedown`), le repli déplaçait la page entre l'appui et le
 * relâchement : le clic tombait à côté, et la ligne d'amendements visée ne
 * s'ouvrait pas (mesuré le 02/10/2026 sur la fiche de François Ruffin). Le
 * repli attend donc le clic lui-même, puis rend au défilement ce que la page a
 * perdu : l'élément cliqué reste sous le curseur.
 *
 * `fermer` est lu par une référence : il change d'identité à chaque rendu, et
 * l'écouteur n'a pas à être reposé pour autant.
 */
export function useReplieAuClicDehors(ref, ouvert, fermer) {
  const dernierFermer = useRef(fermer);
  dernierFermer.current = fermer;

  useEffect(() => {
    if (!ouvert) return undefined;
    const surClic = (e) => {
      const cible = e.target;
      if (cible === document.documentElement) return;
      if (!ref.current || ref.current.contains(cible)) return;
      const avant = cible.getBoundingClientRect().top;
      dernierFermer.current();
      requestAnimationFrame(() => {
        if (!cible.isConnected) return;
        const ecart = cible.getBoundingClientRect().top - avant;
        if (ecart) window.scrollBy(0, ecart);
      });
    };
    document.addEventListener('click', surClic);
    return () => document.removeEventListener('click', surClic);
  }, [ouvert, ref]);
}
