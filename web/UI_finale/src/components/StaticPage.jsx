import { Fragment } from 'react';
import EnTeteSite from './EnTeteSite';
import PiedDeSite from './PiedDeSite';
import '../styles/shell.css';
import './StaticPage.css';

// Page statique partagée (Méthodologie, Mentions légales, FAQ) : bannière + sections,
// hors ExplorerLayout — ces pages n'ont pas de candidat/groupe sélectionné, les
// bandeaux Groupes/Gouvernements/Candidats n'ont donc pas de sens ici. La rangée
// collée (#951) remplace le fil « ← Retour à l'accueil » : le logo y ramène, et
// les pages du site sont à côté. Une section sans `heading` n'a pas de titre :
// la page /faq n'en porte qu'une, que la bannière nomme déjà.
export default function StaticPage({ eyebrow, title, tagline, intro, updated, sections }) {
  return (
    <div className="app-shell">
      <div className="static-page">
        <EnTeteSite />
        <main className="static-main">

          <div className="static-banner">
            {eyebrow && <span className="static-banner-tag">{eyebrow}</span>}
            <h1>{title}</h1>
            {tagline && <p>{tagline}</p>}
          </div>

          {/* L'INTRODUCTION (#951) : quelques phrases sous la bannière, sans titre ni
              carte — ce que le projet est, avant la méthode détaillée. */}
          {intro && (
            <div className="static-intro">
              {intro.map((phrase) => (
                <p key={phrase}>{phrase}</p>
              ))}
            </div>
          )}

          {updated && <p className="static-updated">{updated}</p>}

          <div className="static-sections">
            {sections.map((section) =>
              /* UNE ENTRÉE `famille` N'EST PAS UNE SECTION, c'est le titre du
                 groupe qui suit (#328). Le tableau reste PLAT : les ancres
                 (`/methodologie#votes`) ne bougent pas, et une page qui ne
                 déclare aucune famille — les mentions légales — se rend
                 exactement comme avant.

                 Une famille peut être VIDE et porter un `note` : la fiche de
                 gouvernement n'a aucune section de méthode, et le dire est
                 préférable à un lecteur qui cherche sans savoir pourquoi il ne
                 trouve pas (§2 règle 5). */
              /* UNE ENTRÉE `element` EST UN BLOC DÉJÀ COMPOSÉ (#951) : « Comment ça
                 marche » et « Ce que vous ne trouverez pas ici » portent leur propre
                 carte et leur titre, rendus tels que l'accueil les rendait. */
              section.element ? (
                <Fragment key={section.id}>{section.element}</Fragment>
              ) : section.famille ? (
                <div className="static-famille" key={`famille-${section.famille}`}>
                  <h2>{section.famille}</h2>
                  {section.note}
                </div>
              ) : (
                // `id` optionnel : il rend une section ATTEIGNABLE depuis une
                // fiche (`/methodologie#votes`). Sans lui, un renvoi posé sous une
                // figure dépose le lecteur en haut d'une page de dix sections.
                <section className="static-card" key={section.heading || section.id} id={section.id}>
                  {section.heading && <h2>{section.heading}</h2>}
                  {section.body}
                </section>
              ),
            )}
          </div>
        </main>
        <PiedDeSite />
      </div>
    </div>
  );
}
