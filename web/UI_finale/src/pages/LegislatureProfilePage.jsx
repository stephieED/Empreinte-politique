import { useParams } from 'react-router-dom';
import { useMemo } from 'react';
import { getGovernmentsList, getLegislature, nomDeLegislature } from '../data';
import { vueLegislature } from '../utils/legislature';
import { useAsyncData } from '../hooks/useAsyncData';
import LegislatureProfile from '../components/LegislatureProfile';
import NotFoundProfile from '../components/NotFoundProfile';

/* La fiche d'une législature (#1314) : le travail de l'Assemblée dans son
 * ensemble. Elle lit un seul fichier, construit par le run. */
export default function LegislatureProfilePage() {
  const { legislatureId } = useParams();
  const { data: legislature, loading } = useAsyncData(() => getLegislature(legislatureId), [legislatureId]);
  const { data: gouvernements } = useAsyncData(getGovernmentsList, []);
  const vue = useMemo(() => vueLegislature(legislature, legislatureId, gouvernements || []), [legislature, legislatureId, gouvernements]);
  if (loading) return null;
  if (!vue) {
    return <NotFoundProfile message={`Aucune fiche publiée pour la ${nomDeLegislature(legislatureId)}.`} />;
  }
  return <LegislatureProfile key={legislatureId} vue={vue} />;
}
