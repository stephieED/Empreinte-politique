import { useDeferredValue, useMemo } from 'react';
import { Navigate, useParams, useSearchParams } from 'react-router-dom';
import { getDebatsLignee, getDonneesAu, getIndexExtraitsLignee, getLigneeProfile, getTablesAmendementsLignee, ligneeDeLaFiche } from '../data';
import { PeriodeContext } from '../components/Recherche';
import { debutDeFenetre, periodeValide } from '../utils/filtrePeriode';
import { useAsyncData } from '../hooks/useAsyncData';
import LigneeProfile from '../components/LigneeProfile';
import NotFoundProfile from '../components/NotFoundProfile';
import { filtrerLignee } from '../utils/filtreLignee';

/* Une page par LIGNÉE (#329, sur le socle #836). L'identifiant est celui de la
 * lignée déclarée (`AN-SOC`). Une adresse d'avant — celle d'une fiche de
 * législature, `AN-SOC-17` — mène à sa lignée plutôt qu'à une page vide : un
 * lien partagé ne casse pas parce que le découpage a changé. */
export default function GroupProfilePage() {
  const { groupId } = useParams();
  const { data, loading } = useAsyncData(async () => {
    const lignee = await getLigneeProfile(groupId);
    if (lignee) return { lignee };
    return { redirection: await ligneeDeLaFiche(groupId) };
  }, [groupId]);

  /* LA RECHERCHE (#979) : le mot vit dans l'adresse, comme sur la fiche
   * candidat, et le champ dans le bandeau depuis #1025 — la page lit `?mot=`,
   * elle ne l'écrit plus. Les débats complets ne se chargent qu'au premier mot
   * tapé. */
  const [params] = useSearchParams();
  const saisie = params.get('mot') ?? '';
  const motDiffere = useDeferredValue(saisie);
  /* LA PÉRIODE (#1074) : sous une case, la parole se lit dans les fenêtres que
   * Backend a comptées (#1077), qui ne vivent que dans la liste complète — elle
   * se charge donc aussi sous une période. */
  const periode = periodeValide(params.get('periode'));
  const { data: donneesAu } = useAsyncData(getDonneesAu, []);
  const debut = debutDeFenetre(donneesAu, periode);
  const cherche = motDiffere.trim().length > 0 || Boolean(periode);
  const { data: debats } = useAsyncData(
    () => (cherche && data?.lignee ? getDebatsLignee(data.lignee.id) : null),
    [data?.lignee?.id, cherche],
  );
  /* CE QUI A ÉTÉ DIT (#1029) : le vocabulaire des extraits, par maillon, que
   * le filtre interroge aussi. Chargé au premier mot tapé seulement. */
  const avecMot = motDiffere.trim().length > 0;
  const { data: extraits } = useAsyncData(
    () => (avecMot && data?.lignee ? getIndexExtraitsLignee(data.lignee.id) : null),
    [data?.lignee?.id, avecMot],
  );
  /* LES AMENDEMENTS UN PAR UN (#1029, voie 2) : la table de chaque maillon,
   * chargée avec les débats — au premier mot ou à la première période. */
  const { data: tables } = useAsyncData(
    () => (cherche && data?.lignee ? getTablesAmendementsLignee(data.lignee.id) : null),
    [data?.lignee?.id, cherche],
  );
  const lignee = useMemo(
    () => filtrerLignee(data?.lignee, motDiffere, debats, debut ? periode : null, debut, extraits, tables),
    [data, motDiffere, debats, periode, debut, extraits, tables],
  );

  if (loading) return null;
  if (data?.redirection) return <Navigate to={`/groupes/${data.redirection}`} replace />;
  if (!lignee) {
    return <NotFoundProfile message={`Aucun groupe trouvé pour l'identifiant « ${groupId} ».`} />;
  }
  return (
    <PeriodeContext.Provider value={debut}>
      <LigneeProfile key={lignee.id} lignee={lignee} mot={motDiffere.trim()} />
    </PeriodeContext.Provider>
  );
}
