import { useNavigate } from 'react-router-dom';
import { getGroupsList } from '../data';
import { useGroupFilter } from '../context/GroupFilterContext';
import { useAsyncData } from '../hooks/useAsyncData';
import ScrollRow from './ScrollRow';
import './GroupsBar.css';

export default function GroupsBar() {
  const { selectedGroupId, toggleGroup } = useGroupFilter();
  const { data, loading } = useAsyncData(getGroupsList, []);
  const groups = data || [];
  const navigate = useNavigate();

  const handleClick = (group) => {
    const wasSelected = selectedGroupId === group.id;
    toggleGroup(group.id);
    if (!wasSelected) navigate(`/groupes/${group.id}`);
  };

  return (
    <div className="gb-bar">
      <span className="gb-bar-label">Groupes</span>
      {loading ? (
        <ScrollRow replie ariaLabel="Groupes (chargement)">
          {Array.from({ length: 5 }).map((_, i) => (
            <div className="gb-chip gb-skeleton" key={i} />
          ))}
        </ScrollRow>
      ) : groups.length === 0 ? (
        <p className="gb-empty">Aucun groupe disponible.</p>
      ) : (
        <ScrollRow replie ariaLabel="Liste des groupes">
          {groups.map((group) => {
            const active = selectedGroupId === group.id;
            return (
              <button
                key={group.id}
                type="button"
                role="listitem"
                aria-pressed={active}
                className={`gb-chip ${active ? 'active' : ''}${
                  group.chambre === 'Senat' ? ' gb-chip--gelee' : ''
                }`}
                title={
                  group.chambre === 'Senat'
                    ? 'Fiche gelée : la collecte au Sénat est suspendue depuis le 24/08/2026, et le Sénat est hors du périmètre éditorial. La fiche existe, mais elle ne porte aucun scrutin de cohésion.'
                    : undefined
                }
                onClick={() => handleClick(group)}
              >
                <span className="gb-chip-label">{group.title}</span>
              </button>
            );
          })}
        </ScrollRow>
      )}
    </div>
  );
}
