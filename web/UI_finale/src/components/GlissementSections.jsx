import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { useLocation, useNavigate } from 'react-router-dom';
import './GlissementSections.css';

/* ── Au téléphone, une section par écran, on glisse de l'une à l'autre (#1372) ─
 *
 * Une fiche de candidat faisait 13,6 écrans de défilement à 390 px, sans moyen
 * d'aller à une section. Arbitré le 28/10/2026 sur prototype (forme A, base A′) :
 * sous 720 px, la fiche montre UNE section à la fois ; on passe à la voisine en
 * glissant le doigt, ou en touchant son titre dans la rangée d'onglets, qui
 * reste en haut. Au-delà de 720 px, rien ne change : ce composant ne rend rien
 * et ne touche pas à la page.
 *
 * LE COMPOSANT LIT LA PAGE, comme `SommaireSections` : les quatre fiches —
 * candidat, groupe, gouvernement, législature — rangent leurs blocs dans un
 * seul `<main>`, et chaque section porte `data-section`. Aucune fiche n'a à le
 * connaître. Une « page » du glissement, c'est :
 *   - la première, « En bref » : tout ce qui précède la première section qui
 *     n'est pas « En bref » — fil d'Ariane, en-tête, et l'« En bref » lui-même ;
 *   - puis une page par section, avec ce qui la suit jusqu'à la section
 *     suivante (le partage, le pied de fiche, les articles vont avec la
 *     dernière).
 * Les blocs des autres pages reçoivent `data-glisse-cache` et sont masqués en
 * CSS. Le DOM de React n'est pas déplacé : un `MutationObserver` repose les
 * marques quand une fiche re-rend ses blocs (données arrivées, période changée).
 *
 * LE DOCUMENT DÉFILE TOUJOURS VERTICALEMENT, comme avant : pas de conteneur
 * qui défile dans la page, donc pas de hauteur à calculer, et la barre du
 * navigateur se replie normalement.
 *
 * LE TITRE DE SECTION S'EFFACE, SA BULLE PASSE CONTRE L'ONGLET (forme F2,
 * arbitrée le 28/10/2026) : l'onglet courant dit déjà la section, le titre
 * redisait la même chose en haut de l'écran. L'en-tête reste dans la page pour
 * les lecteurs d'écran, invisible ; le « i » suit l'onglet courant et ouvre, sous
 * la rangée, la bulle de la section — son texte est repris tel quel de
 * l'en-tête, rien n'est écrit ici.
 *
 * LE FIL D'ARIANE ET LES CASES DE PÉRIODE RESTENT AU-DESSUS DES ONGLETS, sur
 * toutes les sections (28/10/2026) : ils valent pour toute la fiche, et le
 * lecteur doit pouvoir changer de fiche ou de période d'où qu'il soit. Le bloc
 * du fil est le premier de chaque fiche ; il ne se masque pas, et la rangée
 * d'onglets est rendue juste après lui, dans un emplacement que ce composant
 * pose dans le `<main>` (un portail : React ne gère pas ce nœud, il n'y touche
 * pas).
 *
 * UNE FIGURE QUI DÉFILE ELLE-MÊME DE CÔTÉ GARDE LE GESTE : un glissement qui
 * commence dessus la fait défiler, il ne change pas de section. Arbitré le
 * 28/10/2026 en attendant que le lot 3 de #1372 redessine ces figures.
 */

const REQUETE = '(max-width: 720px)';
const EN_BREF = 'En bref';
/* Le geste devient horizontal quand il l'est nettement : 10 px parcourus, et
 * une fois et demie plus en largeur qu'en hauteur. En deçà, la page défile. */
const SEUIL_DECISION = 10;
const RAPPORT_HORIZONTAL = 1.5;
/* Changer de section : un quart de l'écran, ou un coup rapide. */
const PART_ECRAN = 0.25;
const VITESSE = 0.45; // px par ms

/* Le bloc du fil d'Ariane et des cases de période, sur les quatre fiches. */
const FIL = ':scope > :is(.cp-breadcrumb, .lp-fil, .gvp-breadcrumb)';
const EMPLACEMENT = 'glisse-emplacement';

function lirePages(main) {
  const pages = [{ titre: EN_BREF, blocs: [] }];
  for (const el of main.children) {
    if (el.hasAttribute('data-glisse-fixe')) continue;
    const titre = el.dataset.section;
    if (titre && titre !== EN_BREF) pages.push({ titre, blocs: [] });
    pages[pages.length - 1].blocs.push(el);
  }
  return pages;
}

/* L'en-tête d'une section, sur les quatre fiches : le titre et sa bulle. */
const TETES = ':scope > :is(.cp-section-tete, .lp-section-tete, .gvp-section-titre-rang)';

function lireBulle(page) {
  for (const bloc of page.blocs) {
    const tete = bloc.querySelector(TETES);
    if (!tete) continue;
    const bulle = tete.querySelector('.ib-bulle');
    const bouton = tete.querySelector('.ib-bouton');
    return bulle && bouton ? { html: bulle.innerHTML, libelle: bouton.getAttribute('aria-label') } : null;
  }
  return null;
}

function defileDeCote(depart, borne) {
  for (let el = depart; el && el !== borne; el = el.parentElement) {
    if (el.scrollWidth > el.clientWidth + 2 && /(auto|scroll)/.test(getComputedStyle(el).overflowX)) {
      return true;
    }
  }
  return false;
}

export default function GlissementSections() {
  const { pathname } = useLocation();
  const [actif, setActif] = useState(
    () => typeof window !== 'undefined' && window.matchMedia(REQUETE).matches,
  );
  const [titres, setTitres] = useState([]);
  const [courant, setCourant] = useState(0);
  const courantRef = useRef(0);
  /* La section en cours se suit par son TITRE : choisir « 12 derniers mois »
     peut retirer une section de la fiche, et l'index glissait alors sur la
     voisine. */
  const titreRef = useRef(null);
  const [bulles, setBulles] = useState([]);
  const [emplacement, setEmplacement] = useState(null);
  const [bulleOuverte, setBulleOuverte] = useState(false);
  const onglets = useRef(null);
  const barre = useRef(null);
  const aller = useRef(() => {});
  const naviguer = useNavigate();

  useEffect(() => {
    const mq = window.matchMedia(REQUETE);
    const suivre = () => setActif(mq.matches);
    mq.addEventListener('change', suivre);
    return () => mq.removeEventListener('change', suivre);
  }, []);

  // Une autre fiche s'ouvre sur sa première page.
  useEffect(() => {
    courantRef.current = 0;
    titreRef.current = null;
    setCourant(0);
  }, [pathname]);

  useEffect(() => {
    if (!actif) return undefined;
    let main = null;
    let pages = [];

    const marquer = () => {
      main = document.querySelector('.explorer-profile-zone > main');
      if (!main) {
        setTitres([]);
        return;
      }
      pages = lirePages(main);
      // Une fiche sans section (page de choix, fiche introuvable) ne glisse pas.
      if (pages.length < 2) {
        main.classList.remove('glisse');
        setTitres([]);
        return;
      }
      main.classList.add('glisse');
      // Le fil reste visible partout ; la rangée d'onglets vient juste après.
      const fil = main.querySelector(FIL);
      let place = main.querySelector(`:scope > .${EMPLACEMENT}`);
      if (!place) {
        place = document.createElement('div');
        place.className = EMPLACEMENT;
        place.setAttribute('data-glisse-fixe', '');
      }
      const apres = fil ? fil.nextSibling : main.firstChild;
      if (place.previousSibling !== fil || place.parentNode !== main) main.insertBefore(place, apres);
      if (fil) {
        fil.setAttribute('data-glisse-fixe', '');
        fil.removeAttribute('data-glisse-cache');
      }
      main.style.setProperty('--glisse-gouttiere', getComputedStyle(main).paddingLeft);
      setEmplacement((avant) => (avant === place ? avant : place));
      pages = lirePages(main);
      const voulu = titreRef.current === null
        ? Math.min(courantRef.current, pages.length - 1)
        : pages.findIndex((p) => p.titre === titreRef.current);
      const i = voulu < 0 ? 0 : voulu;
      if (i !== courantRef.current) {
        courantRef.current = i;
        setCourant(i);
      }
      pages.forEach((page, i) => page.blocs.forEach((bloc) => {
        if (i === courantRef.current) bloc.removeAttribute('data-glisse-cache');
        else bloc.setAttribute('data-glisse-cache', '');
      }));
      const lus = pages.map((p) => p.titre);
      setTitres((avant) => (avant.join('|') === lus.join('|') ? avant : lus));
      const lues = pages.map(lireBulle);
      setBulles((avant) => (JSON.stringify(avant) === JSON.stringify(lues) ? avant : lues));
    };

    aller.current = (i, sens = 0) => {
      if (!pages.length || i < 0 || i >= pages.length || i === courantRef.current) return;
      courantRef.current = i;
      titreRef.current = pages[i].titre;
      setCourant(i);
      marquer();
      window.scrollTo({ top: 0 });
      if (sens && main && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        main.classList.remove('glisse-entre-droite', 'glisse-entre-gauche');
        void main.offsetWidth; // relance l'animation
        main.classList.add(sens > 0 ? 'glisse-entre-droite' : 'glisse-entre-gauche');
      }
    };

    // La page qui contient l'ancre demandée (#section-3, lien partagé).
    const suivreAncre = () => {
      const cible = window.location.hash && document.getElementById(window.location.hash.slice(1));
      if (!cible || !pages.length) return;
      const i = pages.findIndex((p) => p.blocs.some((b) => b.contains(cible)));
      if (i > 0 && i !== courantRef.current) {
        aller.current(i);
        cible.scrollIntoView();
      }
    };

    marquer();
    suivreAncre();
    const observateur = new MutationObserver(() => {
      const avant = pages.length;
      marquer();
      if (avant < 2 && pages.length >= 2) suivreAncre();
    });
    observateur.observe(document.querySelector('.explorer-profile-zone') ?? document.body, {
      childList: true,
      subtree: true,
    });
    window.addEventListener('hashchange', suivreAncre);

    /* ── Le geste ── */
    let geste = null;
    const debut = (e) => {
      if (!main || !main.contains(e.target) || e.touches.length !== 1) return;
      if (defileDeCote(e.target, main)) return;
      const t = e.touches[0];
      geste = { x: t.clientX, y: t.clientY, t: e.timeStamp, dx: 0, sens: null };
    };
    const bouger = (e) => {
      if (!geste) return;
      const t = e.touches[0];
      const dx = t.clientX - geste.x;
      const dy = t.clientY - geste.y;
      if (geste.sens === null) {
        if (Math.abs(dx) < SEUIL_DECISION && Math.abs(dy) < SEUIL_DECISION) return;
        geste.sens = Math.abs(dx) > Math.abs(dy) * RAPPORT_HORIZONTAL ? 'h' : 'v';
        if (geste.sens === 'h') main.classList.add('glisse-tire');
      }
      if (geste.sens !== 'h') return;
      e.preventDefault();
      // Au bout de la fiche, la page résiste au lieu de suivre le doigt.
      const voisine = courantRef.current - Math.sign(dx);
      const bord = voisine < 0 || voisine >= pages.length;
      geste.dx = dx;
      main.style.setProperty('--glisse-dx', `${bord ? dx * 0.25 : dx}px`);
    };
    const fin = (e) => {
      if (!geste) return;
      const { sens, dx, t } = geste;
      geste = null;
      if (sens !== 'h') return;
      main.classList.remove('glisse-tire');
      main.style.removeProperty('--glisse-dx');
      const vitesse = Math.abs(dx) / Math.max(1, e.timeStamp - t);
      if (Math.abs(dx) > window.innerWidth * PART_ECRAN || (Math.abs(dx) > 40 && vitesse > VITESSE)) {
        aller.current(courantRef.current - Math.sign(dx), -Math.sign(dx));
      }
    };
    document.addEventListener('touchstart', debut, { passive: true });
    document.addEventListener('touchmove', bouger, { passive: false });
    document.addEventListener('touchend', fin);
    document.addEventListener('touchcancel', fin);

    return () => {
      observateur.disconnect();
      window.removeEventListener('hashchange', suivreAncre);
      document.removeEventListener('touchstart', debut);
      document.removeEventListener('touchmove', bouger);
      document.removeEventListener('touchend', fin);
      document.removeEventListener('touchcancel', fin);
      if (main) {
        main.classList.remove('glisse', 'glisse-tire', 'glisse-entre-droite', 'glisse-entre-gauche');
        main.style.removeProperty('--glisse-dx');
        main.style.removeProperty('--glisse-gouttiere');
        main.querySelectorAll(':scope > [data-glisse-fixe]').forEach((b) => b.removeAttribute('data-glisse-fixe'));
        main.querySelector(`:scope > .${EMPLACEMENT}`)?.remove();
        main.querySelectorAll(':scope > [data-glisse-cache]').forEach((b) => b.removeAttribute('data-glisse-cache'));
      }
      setTitres([]);
      setBulles([]);
      setEmplacement(null);
    };
  }, [actif, pathname]);

  // La bulle se referme quand on change de section, à Échap, au toucher dehors.
  useEffect(() => {
    setBulleOuverte(false);
  }, [courant, pathname]);

  useEffect(() => {
    if (!bulleOuverte) return undefined;
    const dehors = (e) => {
      if (barre.current && !barre.current.contains(e.target)) setBulleOuverte(false);
    };
    const touche = (e) => {
      if (e.key === 'Escape') setBulleOuverte(false);
    };
    document.addEventListener('mousedown', dehors);
    document.addEventListener('touchstart', dehors, { passive: true });
    document.addEventListener('keydown', touche);
    return () => {
      document.removeEventListener('mousedown', dehors);
      document.removeEventListener('touchstart', dehors);
      document.removeEventListener('keydown', touche);
    };
  }, [bulleOuverte]);

  // L'onglet courant reste visible dans la rangée.
  useEffect(() => {
    const rangee = onglets.current;
    const bouton = rangee?.children[courant];
    if (!rangee || !bouton) return;
    rangee.scrollTo({ left: bouton.offsetLeft - 16, behavior: 'smooth' });
  }, [courant, titres]);

  if (!actif || titres.length < 2 || !emplacement) return null;

  const bulle = bulles[courant];

  return createPortal(
    <div className="glisse-barre" ref={barre}>
      <nav aria-label="Sections de cette fiche" className="glisse-onglets" ref={onglets}>
        {titres.map((titre, i) => (
          <span className="glisse-place" key={`${i}-${titre}`}>
            <button
              aria-current={i === courant ? 'true' : undefined}
              className="glisse-onglet"
              onClick={() => aller.current(i, Math.sign(i - courant))}
              type="button"
            >
              {titre}
            </button>
            {i === courant && bulle && (
              <button
                aria-controls="glisse-bulle"
                aria-expanded={bulleOuverte}
                aria-label={bulle.libelle}
                className="ib-bouton glisse-info"
                onClick={() => setBulleOuverte((v) => !v)}
                type="button"
              >
                <span aria-hidden="true">i</span>
              </button>
            )}
          </span>
        ))}
      </nav>
      {bulle && (
        /* Le texte de la bulle est celui de l'en-tête de la section, recopié du
           DOM : un lien vers une autre page du site y reste une navigation de
           l'application, pas un rechargement. */
        <div
          className="ib-bulle glisse-bulle"
          dangerouslySetInnerHTML={{ __html: bulle.html }}
          hidden={!bulleOuverte}
          id="glisse-bulle"
          onClick={(e) => {
            const lien = e.target.closest('a');
            const vers = lien?.getAttribute('href');
            if (!vers || !vers.startsWith('/') || lien.target === '_blank') return;
            e.preventDefault();
            setBulleOuverte(false);
            naviguer(vers);
          }}
        />
      )}
    </div>,
    emplacement,
  );
}
