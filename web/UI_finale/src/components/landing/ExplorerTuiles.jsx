import { getAssembleeAujourdhui, getGovernmentsList, getLegislaturesList } from '../../data';
import { useAsyncData } from '../../hooks/useAsyncData';
import CommencerAExplorer from './CommencerAExplorer';
import FriseMetro from './FriseMetro';
import HemicycleAccueil from './HemicycleAccueil';
import './landing.css';

/* ── « Commencer l'exploration », en deux tuiles (#1329, arbitré le 22/10/2026) ─
 *
 * Le site croise des objets que les sources publient séparément, et l'accueil le
 * montre au lieu de l'annoncer : la première tuile croise les législatures et
 * les gouvernements depuis 2012, la seconde donne l'Assemblée d'aujourd'hui par
 * groupe. Chaque segment, chaque station, chaque groupe ouvre sa fiche : elles
 * remplacent les trois portes « activité législative », « activité exécutive »
 * et « par groupe parlementaire ». L'événement des candidats est passé en tête du
 * carrousel de la carte héro, et sa tuile a été retirée.
 *
 * TANT QU'AUCUNE LÉGISLATURE N'EST PUBLIÉE (les fichiers de #1325 arrivent avec
 * un run), l'accueil garde ses portes : une tuile vide dirait qu'il manque
 * quelque chose là où les données ne sont simplement pas encore là. */
export default function ExplorerTuiles() {
  const { data: legislatures } = useAsyncData(getLegislaturesList, []);
  const { data: gouvernements } = useAsyncData(getGovernmentsList, []);
  const { data: assemblee } = useAsyncData(getAssembleeAujourdhui, []);

  if (legislatures && !legislatures.length) return <CommencerAExplorer />;
  if (!legislatures || !gouvernements) return null;
  const aujourdhui = new Date().toISOString().slice(0, 10);
  const depuis = [...legislatures].sort((a, b) => a.debut.localeCompare(b.debut))[0]?.debut.slice(0, 4);

  return (
    <section className="landing-section landing-tuiles" aria-labelledby="landing-explorer-titre">
      <h2 className="explorer-titre" id="landing-explorer-titre">Commencer l’exploration</h2>
      <div className="tuiles">
        <div className="tuile tuile-temps">
          <h3>Législatures et gouvernements <span>depuis {depuis}</span></h3>
          <div className="tuile-frise">
            <FriseMetro legislatures={legislatures} gouvernements={gouvernements} aujourdhui={aujourdhui} />
          </div>
        </div>
        {assemblee && (
          <div className="tuile tuile-assemblee">
            <h3>L’Assemblée aujourd’hui par groupe <span>{assemblee.court} législature</span></h3>
            <HemicycleAccueil groupes={assemblee.groupes} />
          </div>
        )}
      </div>
    </section>
  );
}
