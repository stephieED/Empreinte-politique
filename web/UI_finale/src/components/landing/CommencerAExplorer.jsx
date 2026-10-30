import { useState } from 'react';
import { Link } from 'react-router-dom';
import { getCandidatesList, getGroupsList, getGovernmentsList, getLegislaturesList } from '../../data';
import { useAsyncData } from '../../hooks/useAsyncData';
import '../CandidatesBar.css';
import '../GroupsBar.css';
import '../GovernmentsBar.css';
import './landing.css';

/* ── COMMENCER À EXPLORER : deux portes permanentes, un encart daté ──────────
 *
 * Remplace « Les candidats déclarés » (#951, forme C), qui ouvrait l'accueil sur
 * la grille des 31 candidats. Deux choses l'ont rendu caduc le 30/09/2026 : le
 * recadrage éditorial — les groupes et les gouvernements sont le cœur permanent,
 * les candidats un volet borné par l'élection — et le geste en deux temps
 * demandé par la propriétaire : choisir une famille, puis une fiche.
 *
 * UNE PORTE EST UN OBJET, PAS UN FILTRE. Les onglets ont été écartés en
 * maquette pour cette raison : ils font lire trois familles comme trois vues
 * d'une même liste, alors qu'un gouvernement et un candidat ne sont pas deux
 * façons de regarder la même chose. Chaque porte annonce son volume.
 *
 * LES LISTES SONT MASQUÉES À L'ARRIVÉE et n'apparaissent qu'au clic ; un second
 * clic referme, sans quoi on ne revient pas à l'état d'arrivée sans recharger.
 * Le coût est assumé : le premier écran ne montre plus aucun nom, et ce sont les
 * volumes annoncés qui le compensent.
 *
 * → `docs/decisions/accueil-deux-portes-et-le-concept-en-mots-cles.md`
 */

/* LE VOLET CANDIDATS EST UN ÉVÉNEMENT QUI PORTE SA BORNE (arbitré le
   30/09/2026, sur maquette). Il a d'abord porté la borne seule — « Jusqu'à
   l'élection d'avril 2027 » —, puis la propriétaire a demandé que le bloc
   NOMME SON SUJET : l'étiquette et la liste disent quoi, la pastille dit
   jusqu'à quand.

   L'ÉTIQUETTE EST SUR SA LIGNE ET LE SUJET EST UNE LISTE, parce qu'il pourra y
   en avoir plusieurs : « Événement : … » se casse au deuxième, une liste
   s'allonge d'un élément. Le jour où un second s'y pose, l'étiquette passe au
   pluriel — pas avant, ce serait faux.

   LA PASTILLE DIT LA BORNE, PAS LA FIABILITÉ. « Provisoire » a été écarté : posé
   au-dessus d'une liste de fiches, il se lit sur les FAITS, qui sont sourcés
   comme ceux des groupes (§2 règle 2). C'est le volet qui est borné. */
const EVENEMENTS = ['L’élection présidentielle 2027'];
const BORNE_CANDIDATS = 'Jusqu’en mai 2027';

/* LA DATE VIENT DE LA LOI, PAS DE WIKIPÉDIA (01/10/2026). L'article 3 de la loi
   du 6 novembre 1962 borne la publication de la liste officielle des candidats,
   et `/sources` l'écrit déjà sur son entrée « Conseil constitutionnel » : « la
   liste des candidats est publiée au plus tard le 26 mars 2027, pour un premier
   tour le 18 avril 2027 ».

   « AU PLUS TARD » SE GARDE : la loi dit une borne, pas une date. Écrire « le
   26 mars 2027 » affirmerait plus que la source.

   Un test tient les deux endroits ensemble, parce que la date est écrite ici ET
   dans `sources.config.js` : deux copies d'un même fait dérivent. */
const DATE_LISTE_OFFICIELLE = '26 mars 2027';

/* LA PROVENANCE DE CETTE LISTE-LÀ, ET D'ELLE SEULE (arbitré le 30/09/2026).
   Les groupes et les gouvernements viennent des sources institutionnelles ; la
   liste des candidats déclarés est repérée sur Wikipédia par chaque run, puis
   croisée avec la presse (relecture du 15/10/2026, #1251, #1297), et elle le
   dit là où elle s'affiche. La mention disait « issue de Wikipédia » : vrai de la
   collecte, faux de la liste publiée, dont les sources sont des articles datés. Le lien mène au tableau des candidats et de leurs sources
   (`/sources#candidats`, #1298).

   WIKIPÉDIA, PAS WIKIDATA — et l'erreur est facile, elle a été faite. Wikidata
   ne fournit qu'une propriété, `P4123`, l'identifiant du candidat à l'Assemblée,
   qui relie sa candidature à sa fiche ; elle a été ESSAYÉE pour découvrir les
   candidatures et écartée sur mesure (#753), la propriété qui les déclare
   rendant 1 personne pour 2027 contre plus de trente déclarées. Écrire
   « issue de Wikidata » contredirait `/sources` sur la provenance d'une liste
   publiée, ce qui est la traçabilité et non une question de style (§2 règle 2).

   La FAQ dit la même chose autrement — « en attendant la liste officielle que
   publiera le Conseil constitutionnel ». Les deux sont vraies : le Conseil
   arrête la liste, le Journal officiel la publie. */
function Porte({ cle, libelle, n, borne = null, ouverte, onOuvrir }) {
  return (
    <button
      type="button"
      className={`porte${ouverte ? ' porte--ouverte' : ''}`}
      aria-expanded={ouverte}
      aria-controls={`liste-${cle}`}
      onClick={() => onOuvrir(ouverte ? null : cle)}
    >
      {/* À CHEVAL SUR LE COIN DE LA CARTE, et non au-dessus du bloc : une
          étiquette posée sur l'objet qu'elle qualifie n'a pas à dire lequel.
          Elle est DANS le bouton, donc dans son libellé accessible — « Jusqu'en
          mai 2027, Candidats déclarés, 31 fiches » : la borne s'annonce avant le
          nom de la porte, ce qui est exact et informe plutôt que de décorer. */}
      {borne && <span className="porte-borne">{borne}</span>}
      <span className="porte-nom">{libelle}</span>
      <span className="porte-n">{n === null ? '…' : `${n} fiches`}</span>
    </button>
  );
}

export default function CommencerAExplorer() {
  const [ouverte, setOuverte] = useState(null);
  const { data: candidats } = useAsyncData(getCandidatesList, []);
  const { data: lignees } = useAsyncData(getGroupsList, []);
  const { data: gouvernements } = useAsyncData(getGovernmentsList, []);
  const { data: legislatures } = useAsyncData(getLegislaturesList, []);
  /* LA PORTE DES LÉGISLATURES (#1314, demandée le 22/10/2026) n'apparaît que si
     le manifeste en porte : avant le premier run qui publie leurs fichiers, elle
     mènerait à une liste vide. Le nombre de colonnes suit le nombre de portes,
     pour que la carte de l'événement garde leur largeur (01/10/2026). */
  const avecLegislatures = (legislatures || []).length > 0;
  /* LES TROIS PORTES DISENT L'ACTIVITÉ (arbitré le 22/10/2026), avec ses mots :
     « L'activité législative », « … par groupe parlementaire », « L'activité
     exécutive par gouvernement ». « Groupe parlementaire » garde le mot du
     lecteur, jamais « lignée » (01/10/2026). */

  const compte = (l) => (l ? l.length : null);

  return (
    <section className="landing-section landing-explorer" aria-labelledby="landing-explorer-titre" style={{ '--portes': avecLegislatures ? 3 : 2 }}>
      <h2 className="explorer-titre" id="landing-explorer-titre">Commencer l’exploration</h2>
      {/* LE SEUL TEXTE EXPLICATIF DE L'ACCUEIL, et il est à sa place : il
          n'accompagne pas une figure (règle de forme 2), il dit ce qu'est le
          site à qui ne le connaît pas. Son ordre — groupe, gouvernement,
          candidat — dit le recadrage.

          C'EST SA PHRASE, AU MOT PRÈS. Une réserve a été signalée une fois et
          écartée par elle : « l'intégralité des publications institutionnelles »
          est plus large que ce que `/sources` déclare couvrir — rien avant
          juillet 2012, le Sénat sans vote ni prise de parole, dossiers et
          interventions à partir de la XVe. Ne pas la réécrire ici. */}
      <p className="explorer-amorce">
        Retrouvez l’intégralité des publications institutionnelles par groupe,
        gouvernement ou candidat&#8239;: mandats, votes, textes et interventions.
      </p>

      <div className={`portes${ouverte ? ' portes--touche' : ''}`}>
        <Porte cle="groupes" libelle="L’activité législative par groupe parlementaire" n={compte(lignees)}
          ouverte={ouverte === 'groupes'} onOuvrir={setOuverte} />
        <Porte cle="gouvernements" libelle="L’activité exécutive par gouvernement" n={compte(gouvernements)}
          ouverte={ouverte === 'gouvernements'} onOuvrir={setOuverte} />
        {avecLegislatures && (
          <Porte cle="legislatures" libelle="L’activité législative" n={compte(legislatures)}
            ouverte={ouverte === 'legislatures'} onOuvrir={setOuverte} />
        )}
      </div>

      <ul className="landing-explorer-liste" id="liste-groupes" hidden={ouverte !== 'groupes'}>
        {(lignees || []).map((l) => (
          <li key={l.id}>
            <Link className="gb-chip" to={`/groupes/${l.id}`}>
              <span className="gb-chip-label">{l.title}</span>
            </Link>
          </li>
        ))}
      </ul>

      <ul className="landing-explorer-liste" id="liste-gouvernements" hidden={ouverte !== 'gouvernements'}>
        {(gouvernements || []).map((g) => (
          <li key={g.id}>
            <Link className="gvb-chip" to={`/gouvernements/${g.id}`}>
              <span className="gvb-chip-label">{g.title}</span>
            </Link>
          </li>
        ))}
      </ul>

      <ul className="landing-explorer-liste" id="liste-legislatures" hidden={ouverte !== 'legislatures'}>
        {(legislatures || []).map((l) => (
          <li key={l.id}>
            <Link className="gvb-chip" to={`/legislatures/${l.id}`}>
              {/* LES ANNÉES D'ABORD (22/10/2026) : « XVIe législature » ne se date pas
                  de tête ; « 2022–2024 » si. La législature en cours dit « depuis ». */}
              <span className="gvb-chip-label">{`${l.fin ? `${l.debut.slice(0, 4)}–${l.fin.slice(0, 4)}` : `Depuis ${l.debut.slice(0, 4)}`} · ${l.title}`}</span>
            </Link>
          </li>
        ))}
      </ul>

      <div className="explorer-evenement">
        <p className="explorer-etiquette">Événement</p>
        <ul className="explorer-evenements">
          {EVENEMENTS.map((e) => <li key={e}>{e}</li>)}
        </ul>
        <div className={`portes portes--une${ouverte ? ' portes--touche' : ''}`}>
          <Porte cle="candidats" libelle="Candidats déclarés" n={compte(candidats)} borne={BORNE_CANDIDATS}
            ouverte={ouverte === 'candidats'} onOuvrir={setOuverte} />
        </div>
        <ul className="landing-explorer-liste" id="liste-candidats" hidden={ouverte !== 'candidats'}>
          {(candidats || []).map((c) => (
            <li key={c.id}>
              <Link className="cb-chip" to={`/candidats/${c.id}`}>
                <span className="cb-chip-label">{c.nom}</span>
              </Link>
            </li>
          ))}
        </ul>
        {/* La mention vit AVEC la liste, pas au-dessus du bloc : au-dessus, elle
            qualifierait les trois portes alors qu'elle ne vaut que pour une.
            Voir l'en-tête du fichier pour la presse, et jamais Wikidata. */}
        <p className="explorer-provenance" hidden={ouverte !== 'candidats'}>
          Liste repérée sur Wikipédia et croisée avec <Link to="/sources#candidats">la presse</Link>, en
          attendant sa publication au Journal officiel, <strong>au plus tard le {DATE_LISTE_OFFICIELLE}</strong>.
        </p>
      </div>
    </section>
  );
}
