import { useDeferredValue, useMemo } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { getDonneesAu, getGovernmentProfile, getGovernmentsList, getIndexExtraitsGouvernement, getParolesDuGouvernement } from '../data';
import { PeriodeContext } from '../components/Recherche';
import { dansLaFenetre, debutDeFenetre, periodeValide } from '../utils/filtrePeriode';
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
  const periode = periodeValide(params.get('periode'));
  /* CE QUI A ÉTÉ DIT (#1029) : le vocabulaire des extraits de chaque débat, que
   * le filtre interroge aussi. Chargé au premier mot tapé, jamais avant. */
  const cherche = motDiffere.trim().length > 0;
  const { data: extraits } = useAsyncData(
    () => (cherche && government ? getIndexExtraitsGouvernement(government.id) : null),
    [government?.id, cherche],
  );
  const parMot = useMemo(
    () => filtrerGouvernement(government, motDiffere, extraits, periode),
    [government, motDiffere, extraits, periode],
  );

  /* LA PÉRIODE (#1074). La parole se recompte depuis le détail par membre
   * (`paroles.json`) : un membre compte sur un débat s'il y a au moins une
   * séance dans la fenêtre. EXACT, parce que le détail porte désormais la date
   * de chaque séance (`seances`, écrit par `vue-parole-gouvernement.mjs`) —
   * avec la seule première et dernière date, un intervalle qui chevauchait le
   * début de la fenêtre ne disait pas combien de tours tombaient dedans (26
   * couples membre × débat sur 1 427 chez Lecornu II, pour six mois). */
  const { data: donneesAu } = useAsyncData(getDonneesAu, []);
  const debut = debutDeFenetre(donneesAu, periode);
  const { data: detail } = useAsyncData(
    () => (debut && government ? getParolesDuGouvernement(government.id) : null),
    [government?.id, debut],
  );
  const filtre = useMemo(() => {
    if (!debut || !parMot || !detail) return parMot;
    const liste = (parMot.paroles?.tous || parMot.paroles?.liste || [])
      .map((s) => ({ ...s, porteurs: (detail[s.label] || []).filter((m) => (m.seances || []).some(([d]) => dansLaFenetre(d, debut))).length }))
      .filter((s) => s.porteurs > 0);
    return {
      ...parMot,
      paroles: { ...parMot.paroles, liste, tous: liste, total: liste.length },
      textes: (parMot.textes || []).filter((t) => dansLaFenetre(t.date_depot ?? t.date, debut)),
    };
  }, [parMot, detail, debut]);

  if (loading) return null;

  if (!government) {
    return <NotFoundProfile message={`Aucun gouvernement trouvé pour l'identifiant « ${governmentId} ».`} />;
  }

  return (
    <PeriodeContext.Provider value={debut}>
      <GovernmentProfile
        chronologie={chronologie || []}
        debut={debut}
        government={filtre}
        key={government.id}
        mot={motDiffere.trim()}
      />
    </PeriodeContext.Provider>
  );
}
