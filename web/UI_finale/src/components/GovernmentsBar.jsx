import { useNavigate, useParams } from 'react-router-dom';
import { getGovernmentsList } from '../data';
import { useAsyncData } from '../hooks/useAsyncData';
import ScrollRow from './ScrollRow';
import './GovernmentsBar.css';

export default function GovernmentsBar() {
  const { data, loading } = useAsyncData(getGovernmentsList, []);
  const governments = data || [];
  const navigate = useNavigate();
  const { governmentId: activeGovernmentId } = useParams();

  return (
    <div className="gvb-bar">
      <span className="gvb-bar-label">Gouvernement</span>
      {loading ? (
        <ScrollRow replie ariaLabel="Gouvernements (chargement)">
          {Array.from({ length: 5 }).map((_, i) => (
            <div className="gvb-chip gvb-skeleton" key={i} />
          ))}
        </ScrollRow>
      ) : governments.length === 0 ? (
        <p className="gvb-empty">Aucun gouvernement disponible.</p>
      ) : (
        <ScrollRow replie ariaLabel="Liste des gouvernements">
          {governments.map((government) => {
            const active = activeGovernmentId === government.id;
            return (
              <button
                key={government.id}
                type="button"
                role="listitem"
                aria-pressed={active}
                className={`gvb-chip ${active ? 'active' : ''}`}
                onClick={() => navigate(`/gouvernements/${government.id}`)}
                title={government.title}
              >
                <span className="gvb-chip-label">
                  {government.title.replace(/^Gouvernement\s+/, '')}
                </span>
              </button>
            );
          })}
        </ScrollRow>
      )}
    </div>
  );
}
