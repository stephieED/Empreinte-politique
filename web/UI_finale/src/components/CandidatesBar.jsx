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
 * TOUTES LES PASTILLES ONT LA MÊME FORME (07/10/2026). Celles des fiches sans
 * mandat étaient grisées, avec une infobulle ; la propriétaire a retiré le
 * grisé. Ce que la fiche ne porte pas se lit sur la fiche.
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
                className={`cb-chip ${active ? 'active' : ''}`}
                onClick={() => navigate(`/candidats/${candidate.id}`)}
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
