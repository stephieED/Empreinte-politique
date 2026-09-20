import { useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getCandidatesList, getGroupsList } from '../data';
import { useGroupFilter } from '../context/GroupFilterContext';
import { useAsyncData } from '../hooks/useAsyncData';
import ScrollRow from './ScrollRow';
import './CandidatesBar.css';

/* La barre suit l'ordre alphabétique du manifeste, et n'en refait aucun : deux
 * tris pour une même liste sont deux listes qui divergeront (#328).
 *
 * Une pastille GRISÉE dit que la fiche ne porte ni mandat à l'Assemblée ni
 * fonction gouvernementale — donc ni vote, ni intervention, ni amendement à
 * publier. C'est un fait sur CE QUE LA FICHE MONTRE, jamais un rang entre des
 * personnes (§2 règle 1) : l'infobulle l'écrit, et la pastille reste cliquable,
 * lisible et sélectionnable comme les autres.
 */
export default function CandidatesBar() {
  const { selectedGroupId } = useGroupFilter();
  const { data: candidates, loading } = useAsyncData(getCandidatesList, []);
  const { data: groups } = useAsyncData(getGroupsList, []);
  const navigate = useNavigate();
  const { candidateId: activeCandidateId } = useParams();

  /* LE FILTRE PORTE SUR LA LIGNÉE, PAS SUR SA TÊTE. « Socialistes » retient les
   * membres des trois fiches SOC, pas seulement de la plus récente : un député
   * de la XVe qui a quitté l'Assemblée en 2022 appartient au même groupe. */
  const fichesDuFiltre = useMemo(
    () => (groups || []).find((g) => g.id === selectedGroupId)?.fiches || [selectedGroupId],
    [groups, selectedGroupId],
  );

  const filtered = useMemo(
    () => (selectedGroupId
      ? (candidates || []).filter((c) => (c.groupIds || []).some((id) => fichesDuFiltre.includes(id)))
      : (candidates || [])),
    [candidates, selectedGroupId, fichesDuFiltre],
  );

  const filteredGroupTitle = useMemo(
    () => (selectedGroupId ? (groups || []).find((g) => g.id === selectedGroupId)?.title : null),
    [groups, selectedGroupId],
  );

  return (
    <div className="cb-bar">
      <span className="cb-bar-label">
        Candidats{filteredGroupTitle ? ` · ${filteredGroupTitle}` : ''}
      </span>
      {loading ? (
        <ScrollRow replie ariaLabel="Candidats (chargement)">
          {Array.from({ length: 6 }).map((_, i) => (
            <div className="cb-chip cb-skeleton" key={i} />
          ))}
        </ScrollRow>
      ) : filtered.length === 0 ? (
        <p className="cb-empty">Aucun candidat dans ce groupe.</p>
      ) : (
        <ScrollRow replie ariaLabel="Liste des candidats">
          {filtered.map((candidate) => {
            const active = activeCandidateId === candidate.id;
            return (
              <button
                key={candidate.id}
                type="button"
                role="listitem"
                aria-pressed={active}
                className={`cb-chip ${active ? 'active' : ''}${
                  candidate.aSiegeOuGouverne ? '' : ' cb-chip--sans-mandat'
                }`}
                onClick={() => navigate(`/candidats/${candidate.id}`)}
                title={
                  candidate.aSiegeOuGouverne
                    ? undefined
                    : 'Aucun mandat à l’Assemblée nationale, au Sénat, au Parlement européen ni au gouvernement : sa fiche existe, mais elle ne porte ni vote, ni intervention, ni amendement.'
                }
              >
                <span className="cb-chip-label">{candidate.nom}</span>
              </button>
            );
          })}
        </ScrollRow>
      )}
    </div>
  );
}
