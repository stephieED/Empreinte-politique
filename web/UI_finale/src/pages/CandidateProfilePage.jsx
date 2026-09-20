import { useDeferredValue, useMemo } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { chargerSourcesCandidat, vueCandidat } from '../data';
import { useAsyncData } from '../hooks/useAsyncData';
import CandidateProfile from '../components/CandidateProfile';
import NotFoundProfile from '../components/NotFoundProfile';

export default function CandidateProfilePage() {
  const { candidateId } = useParams();
  const { data: sources, loading } = useAsyncData(() => chargerSourcesCandidat(candidateId), [candidateId]);

  /* LE MOT VIT DANS L'ADRESSE (#979), ET LE CHAMP DANS LE BANDEAU (#1025) :
   * la page LIT `?mot=finances`, elle ne l'écrit plus — c'est le tiroir de
   * l'en-tête qui le fait (ExplorerLayout). Un lien partagé, un rechargement
   * ou le bouton précédent la ramènent donc au même filtre. */
  const [params] = useSearchParams();
  const mot = params.get('mot') ?? '';
  /* La fiche se recalcule sur le mot DIFFÉRÉ : le champ suit la frappe, le
   * recalcul suit quand il peut. */
  const motDiffere = useDeferredValue(mot);
  const candidate = useMemo(() => vueCandidat(sources, motDiffere), [sources, motDiffere]);

  if (loading) return null;

  if (!candidate) {
    return <NotFoundProfile message={`Aucun candidat trouvé pour l'identifiant « ${candidateId} ».`} />;
  }

  return (
    <CandidateProfile key={candidate.id} candidate={candidate} mot={motDiffere.trim()} />
  );
}
