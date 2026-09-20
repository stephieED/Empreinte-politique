import { useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import SchemaSources from '../components/SchemaSources';
import EnTeteSite from '../components/EnTeteSite';
import FriseCouverture from '../components/FriseCouverture';
import PiedDeSite from '../components/PiedDeSite';
import { useAsyncData } from '../hooks/useAsyncData';
import { loadCouverture } from '../data';
import '../styles/shell.css';
import '../components/StaticPage.css';
import './CoveragePage.css';

/* CE QUE CONTIENT CE CORPUS — la page commune aux 59 fiches.
 *
 * POURQUOI ELLE EXISTE. Les deux tiers de « ce qu'on n'a pas pu lire » étaient
 * recopiés à l'identique sur chaque fiche : les bornes de source, les
 * rapprochements qui n'aboutissent pas, les institutions non couvertes. Rien de
 * tout cela ne parle du candidat affiché. La page les dit UNE FOIS, pour les
 * trois populations publiées, et la fiche ne garde que ce qui est vrai de cette
 * personne-là.
 *
 * AUCUN CHIFFRE N'EST ÉCRIT ICI. Effectifs, bornes, noms des fiches où une
 * liste manque : tout vient de `public/data/couverture.json`, mesuré au build
 * par `scripts/couverture-corpus.mjs`. Un chiffre recopié dans du JSX est un
 * chiffre qui aura vieilli au run suivant.
 */

const nb = (n) => n.toLocaleString('fr-FR').replace(/ | /g, ' ');
const jour = (d) => (d ? d.split('-').reverse().join('.') : '');

export default function CoveragePage() {
  const { data, loading, error } = useAsyncData(loadCouverture, []);
  const { hash } = useLocation();

  /* L'ANCRE ATTEND LES DONNÉES. Les renvois des fiches mènent à `#frise`, et la
   * frise n'existe qu'une fois la couverture chargée : le routeur ne suit pas
   * l'ancre de lui-même, et un saut au montage ne trouverait rien. */
  useEffect(() => {
    if (data && hash) document.getElementById(hash.slice(1))?.scrollIntoView();
  }, [data, hash]);

  return (
    <div className="app-shell">
      <div className="static-page">
        <EnTeteSite />
        <main className="static-main cv-main">

          <div className="static-banner">
            <span className="static-banner-tag">Vue d'ensemble</span>
            <h1>Sources</h1>
            <p>Commun à toutes les fiches — candidats, gouvernements, groupes parlementaires.</p>
          </div>

          {loading && <p className="cv-etat">Chargement…</p>}
          {error && (
            <p className="cv-etat">
              La couverture n'a pas pu être chargée. Rien n'est affiché plutôt qu'approché.
            </p>
          )}

          {data && (
            <>
              <p className="static-updated">
                {nb(data.reperes.fichesPubliees)} fiches publiées — {nb(data.reperes.candidats)}{' '}
                candidats, {nb(data.reperes.gouvernements)} gouvernements, {nb(data.reperes.groupes)}{' '}
                groupes. Collecte du {jour(data.collecteLe)}.
              </p>

              {/* LES SOURCES D'ABORD (forme B, retenue le 16/09/2026) : d'où
                  viennent les données, avant depuis quand. Le schéma dit ce que
                  chaque source apporte, et chaque nœud porte sa licence et sa
                  cadence : les cartes repliées n'y sont plus. */}
              <section className="static-card cv-card" id="sources">
                <h2>Les sources</h2>
                <SchemaSources />
              </section>

              <section className="static-card cv-card" id="frise">
                <h2>Ce que le dépôt porte, et depuis quand</h2>
                {/* La légende de la frise dit ce que chaque encre veut dire : ce
                    paragraphe le répétait (règle de forme 3). */}
                <p className="cv-sous">Chaque ligne se déplie sur ses champs.</p>
                <FriseCouverture couverture={data} />
                <p className="cv-note">
                  Les blancs entre deux segments sont des mois sans rien : le plus souvent des
                  mois sans séance. Ils ne disent pas qu'une donnée manque.
                </p>
                <MandatsHorsCouverture fiches={data.accueil?.horsCouverture?.anterieurs} />
              </section>

              <section className="static-card cv-card" id="manquants">
                <h2>Ce qui manque, et sur quelles fiches</h2>
                <p className="cv-sous">
                  Le dénominateur n'est pas le nombre de fiches : une fiche sans mandat à
                  l'Assemblée n'a pas de vote à porter, et sa liste vide est un fait sur elle.
                  Rapporté aux <b>{data.couvertureFiches.siege} fiches qui y ont siégé</b>, un
                  manquant se nomme — et celui dont le mandat est antérieur à la borne n'est pas un
                  trou, l'autre si.
                </p>
                <TableManquants couverture={data.couvertureFiches} />
              </section>

              <p className="cv-renvoi">
                Ce que ces bornes veulent dire, et pourquoi elles existent :{' '}
                <Link to="/methodologie#couverture">la méthodologie</Link>.
              </p>
            </>
          )}
        </main>
        <PiedDeSite />
      </div>
    </div>
  );
}

/* LES MANDATS HORS COUVERTURE, SOUS LA FRISE (#951). La liste vivait sur
 * l'accueil, dans sa frise simplifiée ; la forme C l'avait emportée avec elle.
 * Remise ici le 16/09/2026, et RÉDUITE à la seule rubrique encore vraie : les
 * candidats dont un mandat précède ce que publie l'Assemblée. Les deux autres —
 * « Mandat au Sénat collecté mais non exploitable », « Mandats locaux et
 * autres » — étaient devenues fausses avec #885 et #922.
 *
 * Les noms viennent de `couverture.json` (`accueil.horsCouverture.anterieurs`),
 * calculés sur `mandats_anterieurs` de chaque fiche : une fiche non relue n'y
 * figure pas, absent n'est pas « aucun ». */
function MandatsHorsCouverture({ fiches }) {
  if (!fiches?.length) return null;
  return (
    <div className="cv-hc">
      <p className="cv-hc-titre">Les mandats hors couverture</p>
      <dl>
        <div>
          <dt>Mandat antérieur à la publication des données de l'Assemblée nationale</dt>
          <dd>
            {fiches.map((p, i) => (
              <span key={p.id}>
                {i > 0 && ', '}
                <Link to={`/candidats/${p.id}`}>{p.nom}</Link>
              </span>
            ))}
          </dd>
        </div>
      </dl>
    </div>
  );
}

function TableManquants({ couverture }) {
  return (
    <div className="cv-tableau">
      <table className="cv-grille">
        <thead>
          <tr>
            <th>Liste</th>
            <th>Fiches qui en portent</th>
            <th>Manquent, mandat antérieur à la borne</th>
            <th>Manquent, et c'est un trou</th>
          </tr>
        </thead>
        <tbody>
          {couverture.listes.map((l) => (
            <tr key={l.cle}>
              <td className="cv-liste">
                {l.titre}
                <small>{l.borne ? `publiée à partir du ${jour(l.borne)}` : 'aucune borne déclarée'}</small>
              </td>
              <td>
                <b>{l.porte}</b> / {couverture.siege}
                <span className="cv-jauge">
                  <i style={{ width: `${(l.porte / couverture.siege) * 100}%` }} />
                </span>
              </td>
              {/* NOMMÉS, JAMAIS SEULEMENT COMPTÉS (#510) : une fiche dont la
                  liste est vide parce que son mandat précède la borne ne se
                  confond pas avec une fiche où la donnée manque sans cause
                  connue. Deux absences, deux colonnes. */}
              <td>{l.horsBorne.length ? l.horsBorne.join(', ') : '—'}</td>
              <td>
                {l.trous.length ? (
                  <span className="cv-trou">{l.trous.join(', ')}</span>
                ) : (
                  <span className="cv-aucun">aucun</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
