import { Link } from 'react-router-dom';
import { getCandidatesList } from '../../data';
import { useAsyncData } from '../../hooks/useAsyncData';
import '../CandidatesBar.css';
import './landing.css';

/* ── Les candidats déclarés, en accès direct (#951, forme C) ─────────────────
 *
 * Retenu le 16/09/2026 : un visiteur arrive pour une personne. « Voir un profil
 * candidat » l'envoyait sur une fiche prise par défaut ; l'accueil lui donne le
 * choix dès l'arrivée, et c'est la seule forme où il ne duplique pas la barre
 * des pages du site.
 *
 * LA LISTE SE LIT DANS LE MANIFESTE, jamais écrite à la main : un candidat qui
 * se déclare entre au run suivant. L'ordre est
 * celui du manifeste, alphabétique — l'accueil ne retrie pas.
 *
 * Les pastilles sont celles de la barre de l'explorateur, grisé compris : une
 * fiche sans mandat à l'Assemblée, au Sénat, au Parlement européen ni au
 * gouvernement reste atteignable, et l'infobulle dit ce que le gris veut dire
 * (§2 règle 1 — un fait sur la fiche, jamais un rang). */
export default function CandidatsDeclares() {
  const { data: candidats } = useAsyncData(getCandidatesList, []);

  return (
    <section className="landing-section landing-candidats" aria-labelledby="landing-candidats-titre">
      {/* SANS NOMBRE dans le titre (16/09/2026) : la liste se compte d'un coup
          d'œil, et un nombre y vieillirait à chaque déclaration. */}
      <h2 id="landing-candidats-titre">Les candidats déclarés</h2>
      <ul className="landing-candidats-liste">
        {(candidats || []).map((c) => (
          <li key={c.id}>
            <Link
              to={`/candidats/${c.id}`}
              className={`cb-chip${c.aSiegeOuGouverne ? '' : ' cb-chip--sans-mandat'}`}
              title={
                c.aSiegeOuGouverne
                  ? undefined
                  : 'Aucun mandat à l’Assemblée nationale, au Sénat, au Parlement européen ni au gouvernement : sa fiche existe, mais elle ne porte ni vote, ni intervention, ni amendement.'
              }
            >
              <span className="cb-chip-label">{c.nom}</span>
            </Link>
          </li>
        ))}
      </ul>
      <p className="landing-candidats-aussi">
        Aussi : <Link to="/groupes">les groupes parlementaires</Link> ·{' '}
        <Link to="/gouvernements">les gouvernements</Link>
      </p>
    </section>
  );
}
