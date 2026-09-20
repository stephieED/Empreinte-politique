/* ── Le sommaire des sections, à gauche de la fiche (#324) ────────────────────
 *
 * Une fiche de candidat fait 7 968 px sur ordinateur et 12 122 px sur mobile —
 * neuf écrans. Rien n'y disait où l'on en était, ni comment sauter d'une section
 * à l'autre.
 *
 * Le sommaire tient en place pendant que la page défile, marque la section en
 * cours de lecture, et sert de raccourci. Il est posé À GAUCHE : un lecteur
 * commence par la gauche, et un sommaire s'y lit AVANT le contenu, comme une
 * table des matières. À droite, il devient une note de marge.
 *
 * IL N'APPARAÎT QU'À PARTIR DE 1 440 px DE FENÊTRE, et ce seuil est une mesure.
 * Parc France, Statcounter, août 2026 — la fenêtre vaut l'écran moins la barre
 * de défilement, ~15 px, et l'hypothèse « fenêtre plein écran » est généreuse :
 *
 *   1920 × 1080 · 25,0 % du bureau · fenêtre 1 905 px  → sommaire
 *   1600 × 900  ·  4,8 %           · fenêtre 1 585 px  → sommaire
 *   1536 × 864  ·  9,2 %           · fenêtre 1 521 px  → sommaire
 *   1366 × 768  ·  5,0 %           · fenêtre 1 351 px  → pas de sommaire
 *   1280 × 720  ·  5,0 %           · fenêtre 1 265 px  → pas de sommaire
 *
 * Soit 39 % du parc de bureau nommé, et 21 % de TOUTES les visites — le bureau
 * fait 52,98 % des visites françaises, le mobile 44,59 %.
 *
 * UN SEUIL À 1 600 px AURAIT EXCLU LES ÉCRANS 1 600 × 900 EUX-MÊMES, dont la
 * fenêtre fait 1 585 px : quinze pixels sous la barre. C'est une frontière qu'on
 * pose en pensant à des écrans et qui se règle sur des fenêtres.
 *
 * Le sommaire prend 204 px SUR LA MARGE, jamais sur le contenu : celui-ci reste
 * à 1 100 px, seuil franchi ou non.
 */
import { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import './SommaireSections.css';

/* La hauteur de la rangée collée (80 px, #951) plus une marge de lecture : une
 * section est « en cours » dès que son titre est passé dessous. */
const SEUIL_LECTURE = 144;

/* L'avance prise au clic : sans elle, la rangée collée recouvre exactement le
 * titre qu'on vient de demander. */
const AVANCE_ANCRE = 114;

export default function SommaireSections() {
  const [sections, setSections] = useState([]);
  const [actif, setActif] = useState(null);
  const { pathname } = useLocation();

  /* Le sommaire LIT la page au lieu de recevoir une liste : il sert les trois
   * types de fiche — candidat, groupe, gouvernement — sans qu'aucune ait à le
   * connaître, et une section ajoutée y apparaît d'elle-même.
   *
   * IL FAUT L'OBSERVER, pas seulement la lire une fois : le sommaire est monté
   * AVANT la fiche, dont les données arrivent en réseau. Une lecture unique au
   * montage ne trouve rien et le sommaire reste vide pour toujours — c'est le
   * défaut qu'a montré la première mesure en navigateur. */
  useEffect(() => {
    const lire = () => {
      const lues = [...document.querySelectorAll('[data-section]')]
        .map((el) => ({ id: el.id, titre: el.dataset.section }))
        .filter((s) => s.id && s.titre);
      setSections((avant) => (
        avant.length === lues.length && avant.every((s, i) => s.id === lues[i].id)
          ? avant
          : lues
      ));
    };
    lire();
    const observateur = new MutationObserver(lire);
    observateur.observe(document.body, { childList: true, subtree: true });
    return () => observateur.disconnect();
  }, [pathname]);

  useEffect(() => {
    if (!sections.length) return undefined;
    /* La section en cours est la DERNIÈRE dont le haut a franchi le seuil, pas
     * la plus visible : le lecteur descend, et ce qui compte est où il en est,
     * pas ce qui occupe le plus de place à l'écran. */
    const suivre = () => {
      let courant = sections[0].id;
      for (const s of sections) {
        const el = document.getElementById(s.id);
        if (el && el.getBoundingClientRect().top <= SEUIL_LECTURE) courant = s.id;
      }
      setActif(courant);
    };
    suivre();
    window.addEventListener('scroll', suivre, { passive: true });
    return () => window.removeEventListener('scroll', suivre);
  }, [sections]);

  /* Le `<nav>` est TOUJOURS rendu, même vide : il occupe la colonne de gauche de
   * la grille. Le retirer du DOM faisait glisser le contenu dans cette colonne
   * de 204 px — second défaut trouvé à la première mesure. Vide, il ne se voit
   * pas ; il ne prend que la marge. */
  return (
    <nav className="som" aria-label="Sections de cette fiche">
      {/* Un sommaire d'une seule entrée ne sert à rien : il n'y a nulle part où
          aller, et il occuperait la place d'un titre. */}
      {sections.length > 1 && <p className="som-quoi">Sur cette page</p>}
      <ul>
        {(sections.length > 1 ? sections : []).map((s) => (
          <li key={s.id}>
            <a
              href={`#${s.id}`}
              aria-current={actif === s.id ? 'true' : undefined}
              onClick={(e) => {
                const el = document.getElementById(s.id);
                if (!el) return;
                e.preventDefault();
                window.scrollTo({
                  top: el.getBoundingClientRect().top + window.scrollY - AVANCE_ANCRE,
                  behavior: 'smooth',
                });
              }}
            >
              {s.titre}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
}
