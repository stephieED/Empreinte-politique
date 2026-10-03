/*
 * LES TEXTES PORTÉS EUROPÉENS, UNE LIGNE PAR THÈME — la figure de la fiche
 * candidat, versant européen (arbitrée le 02/10/2026, forme D de la maquette).
 *
 * Une ligne par thème, une colonne par étape présente, et dans chaque case un
 * carré par texte qui touche ce thème et qui en est à cette étape. Elle
 * remplace ici la cascade en rubans : un ruban au prorata valait des parts de
 * textes ; un carré EST un texte, qui se nomme au survol et s'ouvre au clic.
 *
 * LE MÊME TEXTE EST SUR PLUSIEURS LIGNES, ET C'EST LE SURVOL QUI LE DIT. Un
 * texte à trois thèmes a trois carrés. Survolé — ou atteint au clavier —, il
 * entoure d'encre TOUTES ses occurrences : c'est par ce geste que la
 * répétition se lit, sans légende ni phrase (demande de la propriétaire).
 *
 * Le rangement vit dans `utils/carresThemesUe.js`, la liste reste
 * `ListeCascade`, et l'infobulle, l'en-tête de colonne et le voile sont ceux de
 * `CarresTextes` (`.cp-car-*`) : une seule façon d'écrire ces objets sur la
 * fiche. Ce que cette figure ajoute est dans `CarresThemesUe.css`.
 *
 * TROIS GESTES, UN ÉTAT — ceux des carrés français. Un carré ouvre son texte ;
 * l'en-tête d'une colonne, les textes de l'étape ; le nom d'une ligne, les
 * textes qui touchent le thème. Ce qui n'est pas retenu s'estompe et reste
 * tracé.
 *
 * PAS DE LÉGENDE DE COULEURS : chaque ligne porte son nom, et la teinte ne
 * fait que suivre la ligne. PAS DE MENTION 49.3 non plus : la procédure est
 * française.
 */
import { useId, useMemo, useRef, useState } from 'react';
import './CarresTextes.css';
import './CarresThemesUe.css';
import { formatNumber } from '../utils/lecture';
import { memeSelection, selectionDeLEtape, selectionDuCarre } from '../utils/carresTextes';
import {
  carreThemeEclaire,
  faitDuTexteUe,
  rangerParTheme,
  selectionDuTheme,
} from '../utils/carresThemesUe';

// La largeur de l'infobulle (`.cp-car-bulle`), pour la garder dans la carte.
const LARGEUR_BULLE = 300;

/* LA LARGEUR D'UNE COLONNE : `minmax(150px, Nfr)`, N suivant la racine du
 * nombre de textes — et le plancher cède quand la carte est trop étroite pour
 * le tenir. Cinq étapes à 150 px débordent d'une carte de 700 px, et la page
 * ne défile jamais horizontalement : le plancher est donc borné par la part
 * que la grille peut réellement donner à chaque colonne. Les trois longueurs
 * (`--cth-plancher`, `--cth-nom`, `--cth-ecart`) sont dans la feuille, qui les
 * change sous 560 px. */
function gabarit(colonnes) {
  const n = colonnes.length;
  const part = `max(0px, calc((100% - var(--cth-nom) - ${n} * var(--cth-ecart)) / ${n}))`;
  return colonnes
    .map((col) => `minmax(min(var(--cth-plancher), ${part}), ${col.largeur.toFixed(2)}fr)`)
    .join(' ');
}

export function CarresThemesUe({ cascade, selection, onSelection }) {
  const { colonnes, lignes } = useMemo(() => rangerParTheme(cascade), [cascade]);
  const ref = useRef(null);
  const idBulle = useId();
  /* UN SEUL ÉTAT POUR LE SURVOL : le texte désigné (`index`), la ligne du
   * carré qui le désigne (`theme`), et où poser l'infobulle. L'entourage des
   * occurrences lit `index` ; l'infobulle, elle, peut se taire (`muette`) sans
   * que l'entourage tombe. */
  const [survol, setSurvol] = useState(null);

  const choisir = (nouvelle) => onSelection(memeSelection(selection, nouvelle) ? null : nouvelle);

  /* L'infobulle est posée d'après le carré, pas d'après la souris : elle
   * s'ouvre aussi au focus. Ancrée par le bas, elle n'a pas à connaître sa
   * hauteur — même calcul que `CarresTextes`. */
  const montrer = (carre, cible) => {
    const cadre = ref.current?.getBoundingClientRect();
    if (!cadre) return;
    const b = cible.getBoundingClientRect();
    const largeur = Math.min(LARGEUR_BULLE, cadre.width);
    const gauche = Math.max(0, Math.min(b.left - cadre.left - 20, cadre.width - largeur));
    setSurvol({
      index: carre.index,
      theme: carre.theme,
      gauche,
      bas: cadre.bottom - b.top + 12,
      fleche: b.left - cadre.left + b.width / 2 - gauche,
      muette: false,
    });
  };
  const quitter = () => setSurvol(null);
  const survole = survol && !survol.muette ? cascade.textes[survol.index] : null;
  const themeChoisi = selection?.texte == null && selection?.matiere ? selection.matiere : null;

  return (
    <div className="cp-car cp-cth" ref={ref}>
      <div className="cp-cth-grille" style={{ '--cth-cols': gabarit(colonnes) }}>
        <div aria-hidden="true" className="cp-cth-coin" />
        {colonnes.map((col) => (
          <div className="cp-cth-tete" key={col.cle}>
            {/* Le nombre est celui des TEXTES de l'étape, pas celui des carrés
                de la colonne : un texte à trois thèmes y est dessiné trois
                fois, et compté une. */}
            <button
              aria-pressed={memeSelection(selection, selectionDeLEtape(col))}
              className="cp-car-tete cp-car-tete--cliquable"
              onClick={() => choisir(selectionDeLEtape(col))}
              type="button"
            >
              <span className="cp-car-n cp-num">{formatNumber(col.n)}</span>
              <span className="cp-car-lib">{col.libelle}</span>
            </button>
          </div>
        ))}

        {lignes.map((ligne) => {
          const sel = selectionDuTheme(cascade, ligne.theme);
          const choisie = memeSelection(selection, sel);
          return (
            <div className="cp-cth-ligne" key={ligne.theme}>
              {/* Le nom de la ligne, et rien d'autre : aucun compte par thème
                  (arbitrage du 17/09/2026). Tronqué quand il ne tient pas, il
                  reste entier dans `title`. */}
              <button
                aria-pressed={choisie}
                className={[
                  'cp-cth-nom',
                  themeChoisi && !choisie ? 'cp-car-voile' : '',
                ].filter(Boolean).join(' ')}
                onClick={() => choisir(sel)}
                title={ligne.theme}
                type="button"
              >
                {ligne.theme}
              </button>
              {ligne.cases.map((carres, k) => (
                <div className="cp-cth-case" key={colonnes[k].cle}>
                  {carres.map((c) => {
                    const choisi = selection?.texte === c.index;
                    const ici = survol?.index === c.index && survol.theme === c.theme;
                    return (
                      <button
                        aria-describedby={ici && survole ? idBulle : undefined}
                        aria-label={c.texte.titre}
                        aria-pressed={choisi}
                        className={[
                          'cp-car-carre',
                          // Survolé ou choisi : le texte s'entoure PARTOUT où
                          // il est dessiné, pas seulement sous le pointeur.
                          choisi || survol?.index === c.index ? 'cp-cth-jumeau' : '',
                          carreThemeEclaire(selection, c, cascade) ? '' : 'cp-car-voile',
                        ].filter(Boolean).join(' ')}
                        key={c.index}
                        onBlur={quitter}
                        // Au clic, la liste prend le relais : l'infobulle se
                        // tait — un écran tactile, où le toucher vaut survol,
                        // la garderait posée sur la figure. L'entourage reste.
                        onClick={() => {
                          setSurvol((s) => (s ? { ...s, muette: true } : s));
                          choisir(selectionDuCarre(c));
                        }}
                        onFocus={(e) => montrer(c, e.currentTarget)}
                        onMouseEnter={(e) => montrer(c, e.currentTarget)}
                        onMouseLeave={quitter}
                        style={{ background: c.teinte }}
                        type="button"
                      />
                    );
                  })}
                </div>
              ))}
            </div>
          );
        })}
      </div>

      {survole && (
        <div
          className="cp-car-bulle"
          id={idBulle}
          role="tooltip"
          style={{ left: survol.gauche, bottom: survol.bas, '--fleche': `${survol.fleche}px` }}
        >
          <b>{survole.titre}</b>
          <span>{faitDuTexteUe(survole)}</span>
        </div>
      )}
    </div>
  );
}
