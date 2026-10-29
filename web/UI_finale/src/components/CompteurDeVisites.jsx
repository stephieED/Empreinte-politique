import { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';

/* ── Le compteur de visites (GoatCounter, 29/10/2026) ────────────────────────
 *
 * Choisi par la propriétaire pour suivre le nombre de visites : sans cookie, sans
 * donnée personnelle (il ne garde que des totaux), hébergé chez Hetzner en
 * Finlande et en Allemagne. Le script est posé dans `index.html` ; il compte
 * de lui-même la page où le lecteur arrive.
 *
 * L'APPLICATION CHANGE DE PAGE SANS RECHARGER : le script ne le voit pas. Ce
 * composant compte donc chaque adresse suivante, une fois : une adresse égale à
 * la dernière comptée ne l'est pas de nouveau (la première est celle que le
 * script compte en se chargeant). Si le script n'est pas encore là, ou qu'un
 * bloqueur l'a retiré, rien ne se passe.
 *
 * Il ne compte pas en local : GoatCounter ignore `localhost` de lui-même. */
export default function CompteurDeVisites() {
  const { pathname, search } = useLocation();
  // L'adresse déjà comptée : au départ, celle que le script compte au chargement.
  const derniere = useRef(pathname + search);

  useEffect(() => {
    const chemin = pathname + search;
    if (chemin === derniere.current) return;
    derniere.current = chemin;
    window.goatcounter?.count?.({ path: chemin });
  }, [pathname, search]);

  return null;
}
