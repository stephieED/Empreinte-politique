import { useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import './GlissementSections.css';
import './RangeeSections.css';

/* ── À l'ordinateur, la rangée des sections, collée sous la barre du site ─────
 *
 * Arbitré le 29/10/2026 sur maquette (forme B5) : la rangée de pastilles du
 * téléphone (`GlissementSections`, #1372) vient aussi à l'ordinateur, collée
 * sous la barre du site. Elle dit dans quelle section on est, même au milieu
 * d'une section longue, et mène à chacune. Elle REMPLACE le sommaire de gauche
 * sur les quatre fiches (#324) ; les pages de texte gardent le leur.
 *
 * À l'ordinateur les sections restent empilées : rien n'est masqué, la page
 * défile. Un clic fait défiler jusqu'à la section ; l'onglet courant suit le
 * défilement. Sous 720 px, ce composant ne rend rien : le téléphone a sa propre
 * rangée, qui fait glisser une section à la fois.
 *
 * LE COMPOSANT LIT LA PAGE, comme le sommaire qu'il remplace : chaque section
 * des quatre fiches porte `data-section` et une ancre stable (`id`). « En bref »
 * est le haut de la fiche ; il est toujours le premier onglet.
 *
 * Le titre de section reste dans la page (trait court épais, B5) : à
 * l'ordinateur les sections se suivent sur un même écran, et c'est lui qui
 * marque où l'une finit et où l'autre commence.
 */

const REQUETE = '(min-width: 721px)';
const EN_BREF = 'En bref';
const HAUT = 'haut-de-fiche';

/* La barre du site (80 px) et la rangée (52 px), plus une marge de lecture : une
 * section est « en cours » dès que son titre est passé dessous. */
const SEUIL_LECTURE = 160;
/* L'avance prise au clic, pour que la rangée ne recouvre pas le titre demandé. */
const AVANCE_ANCRE = 150;

function lireSections() {
  const main = document.querySelector('.explorer-profile-zone main');
  if (!main) return [];
  const lues = [...main.querySelectorAll('[data-section]')]
    .map((el) => ({ id: el.id, titre: el.dataset.section }))
    .filter((s) => s.id && s.titre && s.titre !== EN_BREF);
  return lues.length ? [{ id: HAUT, titre: EN_BREF }, ...lues] : [];
}

export default function RangeeSections() {
  const { pathname } = useLocation();
  const [actif, setActif] = useState(
    () => typeof window !== 'undefined' && window.matchMedia(REQUETE).matches,
  );
  const [sections, setSections] = useState([]);
  const [courant, setCourant] = useState(HAUT);
  /* La gouttière de la fiche : les pastilles s'alignent sur son contenu, pas
   * sur le bord de la colonne. Elle est lue, chaque fiche ayant la sienne. */
  const [gouttiere, setGouttiere] = useState(null);
  const rangee = useRef(null);

  useEffect(() => {
    const mq = window.matchMedia(REQUETE);
    const suivre = () => setActif(mq.matches);
    mq.addEventListener('change', suivre);
    return () => mq.removeEventListener('change', suivre);
  }, []);

  /* Observer, pas lire une fois : la rangée est montée avant la fiche, dont les
   * données arrivent en réseau, et une période choisie peut retirer une section. */
  useEffect(() => {
    if (!actif) return undefined;
    const lire = () => {
      const main = document.querySelector('.explorer-profile-zone main');
      if (main) {
        const style = getComputedStyle(main);
        const g = `${style.paddingLeft} ${style.paddingRight}`;
        setGouttiere((avant) => (avant === g ? avant : g));
      }
      const lues = lireSections();
      setSections((avant) => (
        avant.length === lues.length && avant.every((s, i) => s.id === lues[i].id && s.titre === lues[i].titre)
          ? avant
          : lues
      ));
    };
    lire();
    const observateur = new MutationObserver(lire);
    observateur.observe(document.querySelector('.explorer-profile-zone') ?? document.body, {
      childList: true,
      subtree: true,
    });
    return () => observateur.disconnect();
  }, [actif, pathname]);

  /* La section en cours est la DERNIÈRE dont le haut a franchi le seuil, pas la
   * plus visible : ce qui compte est où le lecteur en est. */
  useEffect(() => {
    if (sections.length < 2) return undefined;
    const suivre = () => {
      let id = HAUT;
      for (const s of sections.slice(1)) {
        const el = document.getElementById(s.id);
        if (el && el.getBoundingClientRect().top <= SEUIL_LECTURE) id = s.id;
      }
      setCourant(id);
    };
    suivre();
    window.addEventListener('scroll', suivre, { passive: true });
    return () => window.removeEventListener('scroll', suivre);
  }, [sections]);

  // L'onglet courant reste visible quand la rangée défile de côté (vers 1 024 px).
  useEffect(() => {
    const nav = rangee.current;
    const lien = nav?.querySelector('[aria-current="true"]');
    if (!nav || !lien || nav.scrollWidth <= nav.clientWidth) return;
    // Seulement s'il est caché, et jusqu'à la gouttière : la rangée ne bouge pas pour rien.
    const marge = parseFloat(getComputedStyle(nav).paddingLeft) || 0;
    const gauche = lien.offsetLeft - nav.scrollLeft;
    const droite = gauche + lien.offsetWidth;
    if (gauche >= marge && droite <= nav.clientWidth - marge) return;
    nav.scrollTo({ left: Math.max(0, lien.offsetLeft - marge), behavior: 'smooth' });
  }, [courant, sections]);

  if (!actif || sections.length < 2) return null;

  return (
    <div className="rangee-sections">
      <nav
        aria-label="Sections de cette fiche"
        className="glisse-onglets rangee-onglets"
        ref={rangee}
        style={gouttiere ? { paddingInline: gouttiere } : undefined}
      >
        {sections.map((s) => (
          <a
            aria-current={s.id === courant ? 'true' : undefined}
            className="glisse-onglet rangee-onglet"
            href={s.id === HAUT ? pathname : `#${s.id}`}
            key={s.id}
            onClick={(e) => {
              e.preventDefault();
              const el = s.id === HAUT ? null : document.getElementById(s.id);
              const haut = el ? el.getBoundingClientRect().top + window.scrollY - AVANCE_ANCRE : 0;
              const doux = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
              window.scrollTo({ top: Math.max(0, haut), behavior: doux ? 'smooth' : 'auto' });
            }}
          >
            {s.titre}
          </a>
        ))}
      </nav>
    </div>
  );
}
