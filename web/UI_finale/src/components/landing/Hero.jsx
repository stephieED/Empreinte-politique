import Baseline from '../Baseline';
import AnalysesThematiques from './AnalysesThematiques';
import { useEcranEtroit } from '../../hooks/useLargeur';
import './landing.css';

/* ── La carte héro de l'accueil (#1329, arbitrée le 22/10/2026) ──────────────
 *
 * LE TEXTE NE CHANGE PAS : le titre et la baseline (#1026) restent mot pour mot.
 *
 * « LE CONCEPT » EST RETIRÉ : les trois cases (sources officielles → collecte et
 * agrégation → l'empreinte) prenaient la moitié de la carte, et disaient le
 * procédé d'un agrégateur que #1329 abandonne. Ce que le site fait — croiser et
 * donner à voir — se montre désormais sous la carte, dans les tuiles de
 * « Commencer l'exploration ».
 *
 * LE CARROUSEL DES ANALYSES EST DANS LA CARTE, à droite du titre : c'est la
 * première chose qu'on voit, et l'événement des candidats en est la première
 * diapositive tant que son volet est ouvert. Il fermait la page avant.
 *
 * Le titre descend à 26 px environ sur téléphone (landing.css) : à 34 px, il
 * prenait quatre lignes à 400 px de large.
 *
 * → `docs/decisions/accueil-deux-portes-et-le-concept-en-mots-cles.md` pour la
 *   forme précédente. */
export default function Hero() {
  /* Au téléphone (#1372, forme C du 28/10/2026), le carrousel quitte la carte :
   * l'accueil le pose après les tuiles, pour que « Commencer l'exploration »
   * paraisse dès l'ouverture. */
  const etroit = useEcranEtroit();
  return (
    <section className="landing-section landing-hero landing-hero--une" aria-label="Présentation">
      <div className="hero-texte">
        <h1>Explorez l’action politique à partir des données officielles.</h1>
        <Baseline className="baseline--bandeau" />
      </div>
      {!etroit && <AnalysesThematiques dansHero />}
    </section>
  );
}
