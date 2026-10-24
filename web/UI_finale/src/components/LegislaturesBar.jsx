import { useNavigate, useParams } from 'react-router-dom';
import { getLegislaturesList } from '../data';
import { useAsyncData } from '../hooks/useAsyncData';
import ScrollRow from './ScrollRow';
import './GovernmentsBar.css';

/* Le choix de la législature dans le tiroir (#1314), au même dessin que celui
 * des gouvernements. Absente tant qu'aucun fichier de législature n'est publié :
 * une barre vide serait du mobilier. */
export default function LegislaturesBar() {
  const { data } = useAsyncData(getLegislaturesList, []);
  const legislatures = data || [];
  const navigate = useNavigate();
  const { legislatureId } = useParams();
  if (!legislatures.length) return null;
  return (
    <div className="gvb-bar">
      <span className="gvb-bar-label">Législature</span>
      <ScrollRow replie ariaLabel="Liste des législatures">
        {legislatures.map((l) => {
          const active = legislatureId === l.id;
          return (
            <button
              aria-pressed={active}
              className={`gvb-chip ${active ? 'active' : ''}`}
              key={l.id}
              onClick={() => navigate(`/legislatures/${l.id}`)}
              role="listitem"
              title={l.title}
              type="button"
            >
              <span className="gvb-chip-label">{l.court}</span>
            </button>
          );
        })}
      </ScrollRow>
    </div>
  );
}
