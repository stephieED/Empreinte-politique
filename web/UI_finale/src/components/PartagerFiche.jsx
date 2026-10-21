import { useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import './PartagerFiche.css';

/* ── LE BOUTON « PARTAGER CETTE FICHE » (#1033) ───────────────────────────────
 *
 * Arbitré sur maquette entre sept formes : le 19/10/2026 la forme D, un bouton
 * en bas de la fiche ; le 21/10/2026 la FORME E, qui la remplace — une PASTILLE
 * RONDE, l'icône seule, qui FLOTTE en bas à droite de l'écran pendant toute la
 * lecture des trois fiches (candidat, lignée de groupe, gouvernement). Même
 * forme à l'ordinateur et au téléphone. Le libellé « Partager cette fiche »
 * reste lu par les lecteurs d'écran (`aria-label`) et s'affiche au survol
 * (`title`).
 *
 * DEUX COMPORTEMENTS, SELON L'APPAREIL. Au téléphone, il ouvre le menu de
 * partage du téléphone (`navigator.share`) : le lecteur partage là où il
 * partage vraiment, souvent par message. À l'ordinateur, il ouvre un petit
 * menu — LinkedIn, X, copier le lien. Le critère est le POINTEUR grossier
 * (doigt), pas la seule présence de `navigator.share` : plusieurs navigateurs
 * d'ordinateur l'exposent, et la maquette validée y montre le menu.
 *
 * SEULE L'ADRESSE EST PARTAGÉE (§2 règle 1). Aucun message pré-écrit, qui
 * risquerait de qualifier la personne ou le groupe : LinkedIn et X affichent
 * l'aperçu que la page publie déjà (#1008). L'adresse est celle du site publié,
 * sans ancre ni paramètre — la fiche entière, telle qu'un moteur la connaît.
 *
 * RIEN N'EST CHARGÉ DE LINKEDIN NI DE X : ce sont leurs adresses de partage
 * nues, sans script, comme le lien vers Ko-fi de /nous-soutenir.
 * → docs/decisions/partage-des-fiches-1033.md
 */

export const SITE = 'https://empreinte-politique.fr';

const doigt = () =>
  typeof window !== 'undefined' &&
  typeof window.matchMedia === 'function' &&
  window.matchMedia('(pointer: coarse)').matches;

function IconePartage() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true" focusable="false">
      <path d="M12 3v13" />
      <path d="M7 8l5-5 5 5" />
      <path d="M5 13v6a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-6" />
    </svg>
  );
}

export default function PartagerFiche() {
  const { pathname } = useLocation();
  const adresse = `${SITE}${pathname}`;
  const [ouvert, setOuvert] = useState(false);
  const [message, setMessage] = useState('');
  const zone = useRef(null);

  useEffect(() => {
    if (!ouvert) return undefined;
    const surClic = (e) => {
      if (zone.current && !zone.current.contains(e.target)) setOuvert(false);
    };
    const surTouche = (e) => {
      if (e.key === 'Escape') setOuvert(false);
    };
    document.addEventListener('mousedown', surClic);
    document.addEventListener('keydown', surTouche);
    return () => {
      document.removeEventListener('mousedown', surClic);
      document.removeEventListener('keydown', surTouche);
    };
  }, [ouvert]);

  useEffect(() => {
    if (!message) return undefined;
    const t = setTimeout(() => setMessage(''), 2500);
    return () => clearTimeout(t);
  }, [message]);

  const partager = async () => {
    if (doigt() && typeof navigator.share === 'function') {
      try {
        await navigator.share({ url: adresse });
        return;
      } catch (e) {
        // Le lecteur a fermé le menu : rien à faire. Toute autre erreur
        // retombe sur le menu du site.
        if (e && e.name === 'AbortError') return;
      }
    }
    setOuvert((o) => !o);
  };

  const copier = async () => {
    setOuvert(false);
    try {
      await navigator.clipboard.writeText(adresse);
      setMessage('Lien copié');
    } catch {
      // Presse-papiers refusé : l'adresse s'affiche, elle se copie à la main.
      setMessage(adresse);
    }
  };

  const linkedin = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(adresse)}`;
  const x = `https://x.com/intent/post?url=${encodeURIComponent(adresse)}`;

  return (
    <div className="partage" ref={zone}>
      <button
        type="button"
        className="partage-bouton"
        aria-label="Partager cette fiche"
        title="Partager cette fiche"
        aria-expanded={ouvert}
        aria-controls="partage-menu"
        onClick={partager}
      >
        <IconePartage />
      </button>
      {ouvert && (
        <div className="partage-menu" id="partage-menu">
          <a href={linkedin} target="_blank" rel="noopener noreferrer" onClick={() => setOuvert(false)}>
            LinkedIn
          </a>
          <a href={x} target="_blank" rel="noopener noreferrer" onClick={() => setOuvert(false)}>
            X
          </a>
          <button type="button" onClick={copier}>
            Copier le lien
          </button>
        </div>
      )}
      <span className="partage-message" aria-live="polite">
        {message}
      </span>
    </div>
  );
}
