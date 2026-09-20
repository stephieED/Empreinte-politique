import { useDeferredValue, useMemo } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { getGovernmentProfile, getGovernmentsList } from '../data';
import { useAsyncData } from '../hooks/useAsyncData';
import GovernmentProfile from '../components/GovernmentProfile';
import NotFoundProfile from '../components/NotFoundProfile';
import { filtrerGouvernement } from '../utils/filtreGouvernement';

export default function GovernmentProfilePage() {
  const { governmentId } = useParams();
  const { data: government, loading } = useAsyncData(() => getGovernmentProfile(governmentId), [governmentId]);
  // « En bref » situe le gouvernement parmi les autres : la chronologie vient
  // du manifest, déjà chargé pour la barre de sélection (#330).
  const { data: chronologie } = useAsyncData(getGovernmentsList, []);

  /* LA RECHERCHE (#979) : le mot vit dans l'adresse, la barre est celle du
   * tiroir de l'explorateur. La fiche porte déjà tout ce que le filtre lit —
   * les intitulés des débats et des textes —, donc rien ne se recharge. */
  const [params] = useSearchParams();
  const motDiffere = useDeferredValue(params.get('mot') ?? '');
  const filtre = useMemo(() => filtrerGouvernement(government, motDiffere), [government, motDiffere]);

  if (loading) return null;

  if (!government) {
    return <NotFoundProfile message={`Aucun gouvernement trouvé pour l'identifiant « ${governmentId} ».`} />;
  }

  return (
    <GovernmentProfile
      chronologie={chronologie || []}
      government={filtre}
      key={government.id}
      mot={motDiffere.trim()}
    />
  );
}
