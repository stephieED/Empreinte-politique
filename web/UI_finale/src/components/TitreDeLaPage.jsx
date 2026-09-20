import { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';

/* LE TITRE DE L'ONGLET SUIT LA NAVIGATION (#969).
 *
 * Chaque adresse publiée a son titre, écrit au build dans son propre fichier
 * par `scripts/pages-par-adresse.mjs`. Au premier affichage, le navigateur l'a
 * déjà lu. Mais une navigation dans l'application ne recharge rien : sans ce
 * composant, l'onglet garderait le titre de la première page ouverte.
 *
 * Le titre est RELU dans ce fichier, jamais recalculé ici : une seule
 * rédaction, celle du build. Une adresse sans fichier (serveur de
 * développement, fiche inconnue) garde le titre en place. */
const cache = new Map();

export default function TitreDeLaPage() {
  const { pathname } = useLocation();
  const premier = useRef(true);

  useEffect(() => {
    if (premier.current) {
      premier.current = false;
      return undefined;
    }
    let annule = false;
    if (!cache.has(pathname)) {
      cache.set(pathname, fetch(pathname)
        .then((r) => (r.ok ? r.text() : null))
        .then((html) => {
          const m = html?.match(/<title>([^<]*)<\/title>/);
          if (!m) return null;
          const t = document.createElement('textarea');
          t.innerHTML = m[1];
          return t.value;
        })
        .catch(() => null));
    }
    cache.get(pathname).then((titre) => {
      if (titre && !annule) document.title = titre;
    });
    return () => { annule = true; };
  }, [pathname]);

  return null;
}
