/*
 * LES TEXTES PORTÉS, UN CARRÉ PAR TEXTE — la figure de la fiche candidat,
 * versant français (arrêtée le 01/10/2026, forme B de la maquette).
 *
 * Quatre colonnes dans l'ordre de la procédure, et dans chacune un carré par
 * texte, à la teinte de sa commission. Elle remplace ici la cascade en rubans :
 * un ruban répondait « combien », et il fallait cliquer pour apprendre
 * « lesquels » ; un carré EST un texte, qui se nomme au survol et s'ouvre au
 * clic.
 *
 * Le rangement vit dans `utils/carresTextes.js`, la liste reste
 * `ListeCascade` : une seule liste pour les deux figures, donc une seule façon
 * d'écrire un texte, son stade et son sort. Le versant européen a sa grille
 * par thème (`CarresThemesUe.jsx`, 02/10/2026) ; la cascade
 * (`CascadeTextes.jsx`) reste la figure de la fiche de groupe.
 *
 * UNE LIGNE PAR RÔLE, SUR LA FICHE DE GROUPE (forme C, 02/10/2026). `lignes`
 * découpe chaque colonne en rangées — « Comme auteurs », « Comme
 * rapporteurs » — sans rien changer au rangement : les colonnes, leurs
 * comptes et la légende restent ceux de tous les textes. Un texte que le
 * groupe porte aux deux titres figure sur les deux lignes ; c'est le même
 * carré, et il s'allume aux deux endroits. Sans `lignes`, la figure est celle
 * de la fiche candidat, inchangée.
 *
 * TROIS GESTES, UN ÉTAT. Un carré ouvre son texte ; l'en-tête d'une colonne,
 * les textes de l'étape ; une entrée de légende, ceux de la commission. Ce qui
 * n'est pas retenu s'estompe et reste tracé — un texte hors sélection est
 * toujours un texte.
 */
import { Fragment, useId, useMemo, useRef, useState } from 'react';
import './CarresTextes.css';
import { formatNumber } from '../utils/lecture';
import {
  carreEclaire,
  faitDuTexte,
  memeSelection,
  rangerEnCarres,
  selectionDeLEtape,
  selectionDeLaFamille,
  selectionDuCarre,
} from '../utils/carresTextes';
import { Mention493 } from './CascadeTextes';

// La largeur de l'infobulle (`.cp-car-bulle`) : elle sert à la garder dans la
// carte quand le carré survolé est près du bord droit.
const LARGEUR_BULLE = 300;

export function CarresTextes({ cascade, selection, onSelection, lignes = null }) {
  const { colonnes, legende } = useMemo(() => rangerEnCarres(cascade), [cascade]);
  const ref = useRef(null);
  const idBulle = useId();
  const [bulle, setBulle] = useState(null);

  const choisir = (nouvelle) => onSelection(memeSelection(selection, nouvelle) ? null : nouvelle);

  /* L'INFOBULLE EST POSÉE D'APRÈS LE CARRÉ, PAS D'APRÈS LA SOURIS : elle
   * s'ouvre aussi au focus, et le clavier n'a pas de pointeur. Ancrée par le
   * bas, elle n'a pas à connaître sa hauteur — un titre de trois lignes monte,
   * il ne recouvre pas le carré qu'il nomme. */
  const montrer = (carre, cible) => {
    const cadre = ref.current?.getBoundingClientRect();
    if (!cadre) return;
    const b = cible.getBoundingClientRect();
    const largeur = Math.min(LARGEUR_BULLE, cadre.width);
    const gauche = Math.max(0, Math.min(b.left - cadre.left - 20, cadre.width - largeur));
    setBulle({
      index: carre.index,
      gauche,
      bas: cadre.bottom - b.top + 12,
      fleche: b.left - cadre.left + b.width / 2 - gauche,
    });
  };
  const cacher = () => setBulle(null);
  const survole = bulle ? cascade.textes[bulle.index] : null;

  /* L'en-tête d'une colonne : un bouton quand elle porte des textes. Une
   * colonne à zéro garde son en-tête, et n'est pas un bouton — il n'y a aucun
   * texte à ouvrir derrière un « 0 ». */
  const teteDe = (col) => {
    const tete = (
      <>
        <span className="cp-car-n cp-num">{formatNumber(col.n)}</span>
        <span className="cp-car-lib">{col.libelle}</span>
      </>
    );
    return col.n > 0 ? (
      <button
        aria-pressed={memeSelection(selection, selectionDeLEtape(col))}
        className="cp-car-tete cp-car-tete--cliquable"
        onClick={() => choisir(selectionDeLEtape(col))}
        type="button"
      >
        {tete}
      </button>
    ) : (
      <div className="cp-car-tete">{tete}</div>
    );
  };
  const carreDe = (c) => {
    const choisi = selection?.texte === c.index;
    return (
      <button
        aria-describedby={bulle?.index === c.index ? idBulle : undefined}
        aria-label={c.texte.titre}
        aria-pressed={choisi}
        className={[
          'cp-car-carre',
          choisi ? 'cp-car-carre--choisi' : '',
          carreEclaire(selection, c, cascade) ? '' : 'cp-car-voile',
        ].filter(Boolean).join(' ')}
        key={c.index}
        onBlur={cacher}
        // Au clic, la liste prend le relais : l'infobulle se retire, sinon un
        // écran tactile — où le toucher vaut survol — la garderait posée sur
        // la figure.
        onClick={() => { cacher(); choisir(selectionDuCarre(c)); }}
        onFocus={(e) => montrer(c, e.currentTarget)}
        onMouseEnter={(e) => montrer(c, e.currentTarget)}
        onMouseLeave={cacher}
        style={{ background: c.teinte }}
        type="button"
      />
    );
  };

  return (
    <div className="cp-car" ref={ref}>
      {lignes ? (
        <div className="cp-car-lignes">
          <span className="cp-car-coin" />
          {colonnes.map((col) => <div className="cp-car-col" key={col.cle}>{teteDe(col)}</div>)}
          {lignes.map((l) => {
            const n = colonnes.reduce((somme, col) => somme + col.carres.filter((c) => l.porte(c.texte)).length, 0);
            return (
              <Fragment key={l.cle}>
                <span className="cp-car-ligne">{l.libelle} <b className="cp-num">{formatNumber(n)}</b></span>
                {colonnes.map((col) => (
                  <div className="cp-car-case" key={col.cle}>
                    <div className="cp-car-grille">{col.carres.filter((c) => l.porte(c.texte)).map(carreDe)}</div>
                  </div>
                ))}
              </Fragment>
            );
          })}
        </div>
      ) : (
        <div className="cp-car-cols">
          {colonnes.map((col) => (
            <div className="cp-car-col" key={col.cle}>
              {teteDe(col)}
              <div className="cp-car-grille">{col.carres.map(carreDe)}</div>
            </div>
          ))}
        </div>
      )}

      {/* LA LÉGENDE NOMME CE QUE LA TEINTE RAPPELLE, et elle se clique : c'est
          par elle qu'on lit tous les textes d'une commission, toutes étapes
          confondues. Son texte reste en encre et en gris — jamais à la couleur
          de la commission. */}
      <div className="cp-car-legende">
        {legende.map((l) => {
          const sel = selectionDeLaFamille(cascade, l.famille);
          const choisie = memeSelection(selection, sel);
          return (
            <button
              aria-pressed={choisie}
              className={[
                'cp-car-cle',
                selection?.famille && !choisie ? 'cp-car-voile' : '',
              ].filter(Boolean).join(' ')}
              key={l.famille}
              onClick={() => choisir(sel)}
              type="button"
            >
              <i aria-hidden="true" style={{ background: l.teinte }} />
              {l.famille}
            </button>
          );
        })}
      </div>

      {survole && (
        <div
          className="cp-car-bulle"
          id={idBulle}
          role="tooltip"
          style={{ left: bulle.gauche, bottom: bulle.bas, '--fleche': `${bulle.fleche}px` }}
        >
          <b>{survole.titre}</b>
          <span>{faitDuTexte(survole)}</span>
        </div>
      )}

      <Mention493 cascade={cascade} onSelection={onSelection} selection={selection} />
    </div>
  );
}
