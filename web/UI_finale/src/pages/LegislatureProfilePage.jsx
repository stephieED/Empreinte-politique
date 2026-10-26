import { useParams, useSearchParams } from 'react-router-dom';
import { useDeferredValue, useMemo } from 'react';
import { contientLesMots, motsDuFiltre } from '../utils/filtreIntitule';
import { dansLaFenetre, debutDeFenetre, periodeValide } from '../utils/filtrePeriode';
import { getDonneesAu, getGovernmentsList, getLegislature, nomDeLegislature } from '../data';
import { PeriodeContext } from '../components/Recherche';
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
  /* LA RECHERCHE (#1329) : le mot vit dans l'adresse, le champ dans le bandeau.
   * Les dossiers sans le mot dans leur titre quittent la vue AVANT les
   * sections : figures et listes suivent ensemble, comme sur les autres fiches. */
  const [params] = useSearchParams();
  const mot = useDeferredValue(params.get('mot') ?? '').trim();
  /* LA PÉRIODE (#1074, étendue le 26/10/2026) : sur la seule législature EN
   * COURS — pour une législature close, une fenêtre comptée depuis la date des
   * données tombe après sa fin et viderait toute la fiche. Un dossier compte
   * par sa date de dépôt, comme un texte sur la fiche de gouvernement ; sans
   * date, il ne passe pas une fenêtre active (§2 règle 5). */
  const { data: donneesAu } = useAsyncData(getDonneesAu, []);
  const enCours = Boolean(vue?.periode?.debut) && !vue?.periode?.fin;
  const debut = enCours ? debutDeFenetre(donneesAu, periodeValide(params.get('periode'))) : null;
  const filtree = useMemo(() => {
    const mots = motsDuFiltre(mot);
    if (!vue || (!mots.length && !debut)) return vue;
    return {
      ...vue,
      dossiers: vue.dossiers.filter((d) => contientLesMots(d.titre, mots) && (!debut || (d.depot && dansLaFenetre(d.depot, debut)))),
    };
  }, [vue, mot, debut]);
  if (loading) return null;
  if (!vue) {
    return <NotFoundProfile message={`Aucune fiche publiée pour la ${nomDeLegislature(legislatureId)}.`} />;
  }
  return (
    <PeriodeContext.Provider value={debut}>
      <LegislatureProfile enCours={enCours} key={legislatureId} mot={motsDuFiltre(mot).length ? mot : ''} vue={filtree} />
    </PeriodeContext.Provider>
  );
}
