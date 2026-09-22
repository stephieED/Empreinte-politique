import { useDeferredValue, useMemo } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { chargerSourcesCandidat, getAmendementsMotsCandidat, getDonneesAu, vueCandidat } from '../data';
import { PeriodeContext } from '../components/Recherche';
import { debutDeFenetre, periodeValide } from '../utils/filtrePeriode';
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
  /* LA PÉRIODE (#1074) vit dans l'adresse, comme le mot, et se compte depuis la
   * date des données, pas depuis le jour. */
  const { data: donneesAu } = useAsyncData(getDonneesAu, []);
  const debut = debutDeFenetre(donneesAu, periodeValide(params.get('periode')));
  /* LES MOTS DES EXPOSÉS DE SES AMENDEMENTS (#1029, voie 2) : chargés au
   * premier mot tapé, jamais avant. Le filtre retient alors un amendement dont
   * l'exposé porte le mot, même si l'intitulé de son dossier ne le porte pas. */
  const avecMot = motDiffere.trim().length > 0;
  const { data: amendementsMots } = useAsyncData(
    () => (avecMot ? getAmendementsMotsCandidat(candidateId) : null),
    [candidateId, avecMot],
  );
  const candidate = useMemo(
    () => vueCandidat(sources && { ...sources, amendementsMots }, motDiffere, debut),
    [sources, amendementsMots, motDiffere, debut],
  );

  if (loading) return null;

  if (!candidate) {
    return <NotFoundProfile message={`Aucun candidat trouvé pour l'identifiant « ${candidateId} ».`} />;
  }

  return (
    <PeriodeContext.Provider value={debut}>
      <CandidateProfile key={candidate.id} candidate={candidate} mot={motDiffere.trim()} />
    </PeriodeContext.Provider>
  );
}
