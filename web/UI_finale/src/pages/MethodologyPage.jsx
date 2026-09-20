import StaticPage from '../components/StaticPage';
import HowItWorks from '../components/landing/HowItWorks';
import WhatYouWontFind from '../components/landing/WhatYouWontFind';
import { LAST_READING_RULE, STATED_REFUSALS, WHOLE_TEXT_VOTE_BOUND } from '../utils/lecture';
import { REFUS_FICHE_GROUPE } from '../utils/groupe';

/* ── Une ancre par section de la fiche candidat (#328) ───────────────────────
 *
 * `DESIGN_SYSTEM.md` §7 règle 2 : « une limite tient en deux mots, une
 * explication en paragraphe ». La fiche garde donc la limite et le renvoi ; le
 * paragraphe vit ici. Pour que ce renvoi dépose le lecteur devant SA règle et
 * non en haut d'une page de douze sections, chaque section de la fiche a son
 * ancre, et une seule :
 *
 *   fonctions · propose · votes · ecarts · interventions · couverture
 *
 * « Textes portés » et « Amendements » étaient deux sections pour un seul
 * emplacement de la fiche : elles sont réunies sous « Ce qui est proposé »,
 * chacune gardant son sous-titre. Une section de méthodologie qui ne
 * correspond à rien d'affichable est une section que personne n'atteint.
 *
 * LA FICHE DE GROUPE A LES SIENNES (#329), une par section de la fiche de
 * lignée : lignee · paroles · depots · cohesion · convergences. Elles
 * reçoivent ce que l'ancienne fiche écrivait en notes encadrées et en
 * « Ce que cette fiche ne dit pas » : la règle de forme 2 veut la limite sur
 * la fiche, le paragraphe ici.
 */
/* ── LE PLAN SUIT LES TYPES DE FICHE (#328) ──────────────────────────────────
 *
 * Quinze sections se suivaient à plat, et l'appartenance de chacune se devinait
 * au préfixe « Groupes : » — ou pas du tout. Elles sont désormais rangées sous
 * quatre familles, dans l'ordre des onglets de la navigation.
 *
 * DEUX CHOSES QUE LE RANGEMENT A RÉVÉLÉES, et qu'il ne faut pas défaire :
 *
 * 1. La fiche de gouvernement n'a AUCUNE section de méthode, alors que
 *    `GovernmentProfile.jsx` publie trois blocs. Sa famille est donc vide et le
 *    déclare. Supprimer cette famille rendrait le trou invisible sans le
 *    combler (§2 règle 5) : le lecteur chercherait sans savoir pourquoi il ne
 *    trouve pas.
 * 2. « Ce qu'on n'a pas pu lire » s'affiche sur la fiche candidat ET sur la
 *    fiche de lignée. La ranger sous l'une des deux serait faux — d'où la
 *    quatrième famille, qui n'était pas dans la demande initiale.
 *
 * Le préfixe « Groupes : » disparaît des cinq titres concernés : sous un titre
 * de famille il se répétait, et un titre qui se répète cesse d'être lu.
 * Les `id` ne bougent PAS : ce sont des ancres visées depuis les fiches.
 */
/* L'ADN DU PROJET, en tête de la méthode (#951). Texte écrit par la propriétaire
   le 16/09/2026 : l'automatisation y est dite en toutes lettres. Deux affirmations
   corrigées le même jour, parce qu'elles étaient fausses : « la source officielle »
   (Wikipédia et ParlTrack n'en sont pas), et « la fiche le mentionne
   explicitement » (aucune fiche n'affiche qu'un rapprochement a été relu). */
/* L'INTRODUCTION EST PARTIE SUR /a-propos (#1032, arbitré le 18/09/2026).
 * Elle disait ici ce que le site est ; cette page dit comment les fiches sont
 * faites. Le manifeste n'existe donc qu'à un seul endroit, et ce qui reste ici
 * est le renvoi vers lui — la duplication était le défaut à éviter, mesuré sur
 * #1026 : la `meta description` et cette introduction ne disaient déjà pas la
 * même chose. */
const INTRODUCTION = [
  'Cette page dit comment chaque fiche est faite : ce que chaque chiffre mesure, ce qu’il ne mesure pas, et ce que le site refuse de publier.',
];

const SECTIONS = [
  /* EN TÊTE, AVANT LES FAMILLES (#951) : les deux blocs que l'accueil portait.
     Ils disent la méthode en quatre étapes et ce que le site refuse de publier,
     avant le détail fiche par fiche. Leur famille, « Les principes », est
     retenue le 16/09/2026 : « Le concept » légende déjà l'illustration du Hero. */
  { famille: 'Les principes' },
  { id: 'comment-ca-marche', element: <HowItWorks key="comment" /> },
  { id: 'ce-que-vous-ne-trouverez-pas', element: <WhatYouWontFind key="refus" /> },
  { famille: 'Fiche candidat' },
  {
    id: 'fonctions',
    heading: 'Fonctions exercées',
    body: (
      <>
        <p>
          Chaque catégorie montre ses <strong>trois fonctions les plus longues</strong>. Ce n'est
          pas un palmarès : la durée est un fait daté, publié par la source, et rien n'est calculé
          par-dessus — ni total, ni rang, ni comparaison entre personnes.
        </p>
        <p>
          Un filet marque la fonction qui dépasse la moitié du temps de mandat, quand il y en a
          une. Là encore, c'est une proportion de temps, pas une importance : une présidence de
          trois mois ne devient pas plus légère qu'une appartenance de cinq ans.
        </p>
        <p>
          Le rôle n'est précisé que lorsqu'il n'est pas celui de membre. Écrire « membre » partout
          ferait lire une distinction là où la source n'en pose aucune.
        </p>
        <p>
          À côté d'un mandat de député ou de députée, la fiche indique si le groupe était{' '}
          <strong>majoritaire, minoritaire ou d'opposition</strong>. Ces trois qualifications sont
          publiées par l'Assemblée nationale elle-même, législature par législature : elles ne sont
          ni calculées ni interprétées ici. Quand l'Assemblée n'en déclare aucune, la fiche le dit
          plutôt que de choisir.
        </p>
      </>
    ),
  },
  {
    id: 'propose',
    heading: 'Ce qui est proposé',
    body: (
      <>
        <h3>Textes portés</h3>
        <p>
          Un texte est affiché seulement si le pivot lui attribue un rôle factuel parmi{' '}
          <code>auteur</code>, <code>rapporteur</code> ou <code>co-rapporteur</code>, à un stade attestant
          qu'il a réellement été débattu.
        </p>
        <p>
          Les stades retenus commencent à <code>examine_commission</code>, puis incluent l'inscription à
          l'ordre du jour, la discussion en séance, l'adoption et la promulgation. Un dépôt seul, un rôle
          non retenu ou un volume d'interventions ne suffisent pas.
        </p>
        <h3>Amendements</h3>
        <p>Les issues sont publiées en comptes bruts : adoptés, rejetés, retirés, tombés, irrecevables et non soutenus.</p>
        <p>
          Aucun taux d'adoption isolé n'est présenté. Ces issues dépendent du texte, de la procédure, de la
          recevabilité et du rôle du déposant ; elles ne constituent pas une mesure d'efficacité.
        </p>
        <h3>Pourquoi la cascade et la chute se cliquent</h3>
        <p>
          Les deux figures sont des <strong>entrées de lecture</strong>, pas des illustrations : un
          ruban, une barre ou une étiquette ouvre la liste des textes ou des dossiers qui la
          composent, avec leur date et leur source. Aucun seuil ne s'y applique, et la branche basse
          d'une cascade n'est pas un rejet — c'est un stade que le texte n'a pas encore atteint.
        </p>
      </>
    ),
  },
  {
    id: 'votes',
    heading: 'Votes de texte',
    body: (
      <>
        <p>
          L'univers retenu comprend les scrutins publics disponibles, ordinaires et solennels, portant sur
          l'ensemble d'un texte. Les votes sur un article, sur une partie de texte ou sur un amendement en
          sont exclus, de même que les motions de censure, qui sont des faits de procédure. Pour un même
          texte, une seule lecture est conservée dans la synthèse : la plus récente par sa date.
        </p>
        <p>
          <strong>{LAST_READING_RULE.phrase}</strong> {LAST_READING_RULE.pourquoi}
        </p>
        <p>
          <strong>{WHOLE_TEXT_VOTE_BOUND.phrase}</strong> {WHOLE_TEXT_VOTE_BOUND.pourquoi}
        </p>
        <p>
          Le choix de ne pas se limiter aux seuls scrutins solennels évite d'écarter des votes publics sur
          des textes entiers.
        </p>
        <h3>Pourquoi ces positions sont découpées en périodes</h3>
        <p>
          Un même vote ne dit pas la même chose selon d'où il est émis : depuis la majorité, voter contre
          n'arrive presque jamais ; depuis l'opposition, c'est le vote pour qui se remarque. La fiche ne
          totalise donc pas une carrière entière, elle la découpe en <strong>périodes politiques</strong> —
          une nouvelle dès que le banc ou le gouvernement en place change.
        </p>
        <p>
          Les deux repères sont <strong>déclarés, jamais déduits</strong>, et ils se complètent. Le banc
          vient de <code>position_dans_hemicycle</code>, que la validation du pivot refuse sans{' '}
          <code>source_url</code> ; le gouvernement vient des dates des fiches de gouvernement. De 2012 à
          2017, l'Assemblée publie le banc mais le corpus ne porte aucune fiche de gouvernement ; depuis
          2024, c'est l'inverse. Sur les 1 160 positions de dernière lecture des candidats déclarés, le banc
          seul en couvre 719 et le gouvernement seul 916 — <strong>le banc ou le gouvernement les couvre
          toutes les 1 160</strong>. Une période sans aucun des deux serait affichée comme telle, jamais
          rattachée à sa voisine.
        </p>
        <h3>D'où viennent la matière et l'origine d'un texte</h3>
        <p>
          La <strong>matière</strong> est la commission chargée d'examiner le texte, celle qui l'amende
          et rédige le rapport. Le Parlement l'appelle la « commission saisie au fond ». Elle est lue dans
          l'archive de l'Assemblée. Un scrutin ne porte aucune référence législative : le rattachement se
          fait dans l'autre sens, depuis les actes du dossier qui nomment les scrutins tenus. Il aboutit
          pour 711 des 1 160 positions. Les autres restent en « matière non établie » : c'est une absence
          de source, jamais une absence de commission, et elle n'est jamais comblée en devinant la matière
          depuis l'intitulé du scrutin.
        </p>
        <p>
          L'<strong>origine</strong> — texte du gouvernement ou du Parlement — est lue dans l'intitulé
          officiel du scrutin, qui nomme lui-même la catégorie juridique : « projet de loi » pour un texte
          du gouvernement, « proposition de loi » ou « proposition de résolution » pour un texte du
          Parlement. Ce n'est pas un rapprochement entre deux corpus, c'est un mot que la source pose ; il
          est reconnu sur les 1 160 positions.
        </p>
        <p>
          Le <strong>sort final du texte</strong> est celui du dossier, et il n'est pas dérivé du vote
          affiché : un texte peut être adopté en dernière lecture puis rejeté au terme de la navette. Il
          est publié pour 722 des 1 160 positions, et un texte adopté par engagement de responsabilité est
          nommé comme tel, jamais fondu dans les adoptions ordinaires.
        </p>
      </>
    ),
  },
  {
    heading: '49.3 et censure',
    body: (
      <>
        <p>
          Un texte adopté sans vote après engagement de responsabilité au titre de l'article 49.3 est
          signalé comme fait de procédure, jamais comme position de vote du candidat.
        </p>
        <p>
          Une motion de censure est un scrutin distinct. Elle est présentée séparément et reliée au texte
          concerné lorsque <code>texte_lie_id</code> est disponible.
        </p>
      </>
    ),
  },
  {
    heading: 'Présence',
    body: (
      <>
        <p>
          Empreinte politique ne publie aucun taux individuel d'assiduité, de présence ou d'absence. Un
          scrutin manqué ne décrit ni l'ensemble du travail parlementaire ni les motifs de non-participation.
        </p>
        <p>
          Les périodes d'incompatibilité liées à une fonction gouvernementale sont signalées comme faits
          institutionnels et ne sont pas assimilées à des absences.
        </p>
      </>
    ),
  },
  {
    id: 'ecarts',
    heading: 'Divergences avec son groupe',
    body: (
      <>
        <p>
          La fiche d'un candidat pose sa position à côté de celle de son groupe,{' '}
          <strong>scrutin par scrutin</strong>. Elle ne les totalise jamais : le nombre de
          divergences, son rapport aux scrutins comparables ou un taux de cohésion seraient un
          indice individuel mesuré contre la moyenne d'un groupe, qui reste un contrôle interne.
          « A voté contre son groupe 47 fois » serait une note, pas un fait.
        </p>
        <h3>Quels scrutins sont retenus</h3>
        <p>
          Quatre conditions, toutes nécessaires : la personne y a une position publiée, la fiche de
          son groupe aussi, la position majoritaire du groupe est établie, et le scrutin porte sur
          l'<strong>ensemble d'un texte</strong>. Cette dernière restriction n'est pas un défaut de
          collecte : sur un article ou un amendement, la position majoritaire d'un groupe se déplace
          d'un vote à l'autre pour des raisons de négociation que la source ne porte pas.
        </p>
        <p>
          Le nombre de scrutins <em>communs toutes natures confondues</em> n'est pas publié. Posé à
          côté des divergences, il servirait de dénominateur à une division que rien ne justifie —
          et les deux nombres ne portent pas sur la même population.
        </p>
        <h3>Ce que veut dire « son groupe s'est divisé »</h3>
        <p>
          Le critère est brut et sans seuil : le groupe est compté comme divisé dès que ses membres
          exprimés n'ont pas tous voté de la même façon. Un membre qui s'abstient quand soixante-sept
          votent pour suffit. Les absents et les non-votants sont hors du critère — ne pas voter
          n'est pas voter autrement — et le dénominateur reste les membres éligibles, pas les
          exprimés.
        </p>
        <p>
          C'est un fait de <strong>groupe</strong>, publié avec son dénominateur, et il donne son
          sens à une divergence : se séparer d'un groupe uni et se ranger dans l'une des deux
          moitiés d'un groupe partagé ne sont pas le même geste.
        </p>
        <h3>Quand la position du groupe repose sur peu de membres</h3>
        <p>
          Un scrutin où <strong>moins de la moitié</strong> des membres éligibles se sont exprimés
          est signalé comme tel. La « position majoritaire » y repose sur une poignée de votes, et
          un ratio sans couverture suffisante ne se publie pas sans le dire. Le scrutin n'est pas
          écarté pour autant : choisir les faits qui arrangent serait pire que les publier avec leur
          réserve.
        </p>
        <h3>Trois vides, trois causes</h3>
        <p>
          Une section sans divergence peut dire <strong>trois choses différentes</strong>, et elles
          ne se confondent pas : aucune fiche de groupe n'est publiée pour les groupes où la
          personne a siégé (rien n'est comparable) ; des fiches existent mais ne recouvrent aucun de
          ses votes sur l'ensemble d'un texte (la comparaison est vide de base) ; ou la comparaison
          est possible et aucune divergence n'y figure. Seule la troisième est un fait sur la
          personne.
        </p>
      </>
    ),
  },
  {
    id: 'interventions',
    heading: 'Interventions en séance',
    body: (
      <>
        <p>
          La fiche publie les interventions elles-mêmes — le verbatim du compte rendu intégral —,
          et jamais un extrait choisi : le fil affiche <strong>toutes</strong> les interventions du
          sujet retenu, dans l'ordre. Il reste fermé tant qu'aucun sujet n'est choisi, pour
          qu'aucune phrase ne se trouve mise en avant par le seul fait d'être la première.
        </p>
        <h3>Pourquoi le sujet ne se lit pas au même endroit selon le type</h3>
        <p>
          L'Assemblée écrit son ordre du jour en <strong>chemin</strong> — « racine &rsaquo; étape
          &rsaquo; article » —, et la grammaire de ce chemin change avec le type d'intervention.
          Sur une question au gouvernement, « Questions au Gouvernement &rsaquo; Réforme des
          retraites », le sujet est la <strong>feuille</strong> et la racine n'est que le créneau de
          séance. Sur l'examen d'un texte, « Projet de loi de finances pour 2023 &rsaquo; Première
          partie &rsaquo; Après l'article 3 », le sujet est la <strong>racine</strong> et la feuille
          est une étape de procédure.
        </p>
        <p>
          Prendre partout le même bout rangerait 2 885 des 3 660 questions sous un seul libellé —
          « Questions au Gouvernement », qui est un créneau de séance et non un sujet — ou bien
          ferait des textes examinés autant de « Suspension et reprise de la séance ». Le niveau se
          choisit donc par type,
          ce qui revient à <em>lire</em> la structure que la source pose. Deux intitulés voisins ne
          sont jamais rapprochés pour autant : « Motion de censure » et « Motions de censure »
          restent deux entrées.
        </p>
        <h3>La qualité de l'orateur</h3>
        <p>
          Le compte rendu ne publie la qualité que pour une fonction particulière — ministre,
          rapporteur. Son absence n'est pas « cette personne parlait comme député » : c'est un
          silence de la source, et la fiche l'écrit intervention par intervention, jamais en
          totalisant une carrière.
        </p>
        <h3>Ce qui n'est pas publié</h3>
        <p>
          La distinction entre « réaction courte » et « prise de parole développée » existe dans nos
          données, sur 16 242 lignes, mais elle est <strong>notre</strong> déduction : un seuil de
          cinquante mots posé à la collecte, jamais un fait du compte rendu. La publier ferait
          passer un choix d'implémentation pour une donnée.
        </p>
        <p>
          Aucune densité par jour de séance n'est dessinée : un creux s'y lirait comme une absence
          individuelle, que la source ne publie pas et que nous ne publions jamais. Aucun total de
          carrière non plus — une intervention portée depuis le banc du gouvernement et une
          intervention portée depuis les bancs ne se comptent pas dans la même unité.
        </p>
        <h3>Quand la collecte s'est arrêtée au thème</h3>
        <p>
          Une partie des interventions relève d'un régime de collecte déclaré : la date, la nature
          et le thème, et rien d'autre. Aucun verbatim, aucune qualité, souvent aucun intitulé. Ce
          n'est pas une donnée manquante à combler, et surtout pas un silence de la personne : la
          fiche le nomme sous chaque entrée concernée et le compte sous la figure.
        </p>
      </>
    ),
  },
  {
    heading: 'Ordre des catégories',
    body: (
      <>
        <p>
          <code>position_dans_hemicycle</code> n'est utilisée que lorsqu'elle possède une source primaire
          (<code>source_url</code>). Elle permet de répartir les textes portés et les amendements d'un
          candidat en trois lots : <strong>Majorité</strong>, <strong>Opposition</strong> et{' '}
          <strong>Non distingué</strong> (éléments à cheval sur les deux périodes, ou dont la date ne
          correspond à aucune période sourcée).
        </p>
        <p>
          Sur le profil d'un candidat, l'onglet « Textes » affiche cette répartition sous forme de barres de
          comparaison (nombre de textes portés et d'amendements par catégorie). Le lot « Non distingué » est
          toujours affiché séparément, même à zéro : l'absence de donnée sourcée reste visible, conformément
          à la règle 6. Cette répartition n'est pour l'instant présentée que sur les profils candidat, pas
          sur les profils de groupe.
        </p>
      </>
    ),
  },
  {
    heading: 'Responsabilités',
    body: (
      <p>
        Les responsabilités sont dédupliquées par intitulé. Les fonctions de présidence ou de rapport
        peuvent servir à ordonner le détail, mais ce classement interne n'est jamais publié comme total ou
        score.
      </p>
    ),
  },
  { famille: 'Fiche de groupe parlementaire' },
  {
    id: 'lignee',
    heading: 'Une fiche par lignée',
    body: (
      <>
        <p>
          L'Assemblée ouvre et ferme des groupes à chaque législature ; elle ne dit pas lequel
          succède à lequel. Une <strong>lignée</strong> réunit les groupes successifs d'une même
          formation — « Nouvelle Gauche », puis « Socialistes et apparentés » sous trois
          législatures. Ce rattachement est une <strong>relecture humaine, datée</strong>, jamais
          une ressemblance de sigle : un groupe qui prend la suite d'un autre sans le déclarer n'y
          est pas rattaché.
        </p>
        <p>
          La frise trace le nombre de membres jour par jour, depuis les dates d'entrée et de sortie
          de chacun ; le nombre écrit au bout de chaque bande est celui que la fiche du groupe
          publie à sa date de référence. Le motif dit comment l'Assemblée qualifie le groupe pour
          cette législature : majoritaire, d'opposition, minoritaire — ou rien, quand elle ne le
          déclare pas.
        </p>
        <p>
          Un point par personne et par groupe : « nouveau dans la lignée » ne veut pas dire
          « nouveau député ». La personne a pu siéger ailleurs avant ; la donnée ne porte que la
          lignée, et la fiche n'en dit pas plus. Aucun taux de renouvellement n'est calculé : il
          deviendrait une note comparée d'un groupe à l'autre.
        </p>
      </>
    ),
  },
  {
    id: 'paroles',
    heading: 'Sur quoi ils ont pris la parole',
    body: (
      <>
        <p>
          Les intitulés sont ceux que le compte rendu de l'Assemblée donne aux débats, recopiés tels
          quels. Chacun porte le nombre de membres du groupe qui y sont intervenus, sur le nombre de
          membres passés par le groupe pendant la législature. Ce sont des <strong>sujets
          abordés</strong>, jamais des positions du groupe : intervenir sur un texte ne dit pas ce
          qu'on en pense.
        </p>
      </>
    ),
  },
  {
    id: 'depots',
    heading: 'Ce qu’ils ont proposé',
    body: (
      <>
        <p>
          Un amendement compte <strong>une fois</strong>, quel que soit le nombre de membres qui
          l'ont signé, et seulement s'il a été déposé sous la législature du groupe. Déposer comme
          député et déposer comme rapporteur de commission sont deux actes différents : ils se lisent
          séparément, et ne se réunissent que si le lecteur sélectionne les deux — un texte amendé
          au titre des deux ne compte alors qu'une fois. Aucun taux d'adoption commun n'est publié.
        </p>
        <p>
          La matière est la commission chargée d'examiner le texte, comme sur la fiche d'un candidat.
          Les textes se rangent du plus récemment amendé au plus ancien, jamais par volume : déposer
          beaucoup sur un texte peut être un travail de fond comme une obstruction, et le nombre ne
          les distingue pas. Le sort d'un texte n'est affiché que lorsqu'un scrutin le rattache à
          son dossier.
        </p>
        <p>
          Les textes portés se lisent avec la même cascade que sur la fiche d'un candidat : jusqu'où
          chaque texte est allé, de l'examen en commission à la promulgation. Un texte compte
          <strong> une fois</strong> pour le groupe, quel que soit le nombre de membres qui l'ont
          déposé ou rapporté, et seulement s'il relève de la législature du groupe. Deux qualités se
          lisent séparément ou ensemble — auteur d'une proposition, rapporteur d'un texte — et un
          dossier qui porte les deux ne compte qu'une fois. Un projet de loi n'y figure pas : il est
          signé par un membre du gouvernement, pas au nom d'un groupe. Sous l'examen en commission,
          rien n'est publié.
        </p>
      </>
    ),
  },
  {
    id: 'cohesion',
    heading: 'Ce qu’ils ont voté',
    body: (
      <>
        <p>
          Un groupe ne vote pas : ses membres votent. Pour dire s'il s'est exprimé d'une seule voix,
          il faut qu'au moins la moitié de ses membres aient pris part au scrutin. En dessous, deux
          ou trois voix ne décrivent pas le groupe, et rien n'est publié. Ce n'est pas une lacune de
          collecte : les autres scrutins sont là, ils ne permettent simplement pas cette mesure.
        </p>
        <p>
          « D'une seule voix » signifie que toutes les positions exprimées allaient dans le même
          sens. Les absences ne sont jamais comptées, et aucune largeur affichée ne s'y rapporte :
          ce serait un taux de présence sur des personnes nommées.
        </p>
        {REFUS_FICHE_GROUPE.map((refus) => (
          <p key={refus.id}>
            <strong>{refus.phrase}</strong> {refus.pourquoi}
          </p>
        ))}
      </>
    ),
  },
  {
    id: 'convergences',
    heading: 'Avec qui ils votent',
    body: (
      <>
        <p>
          La position majoritaire du groupe est comparée à celle de chaque autre groupe de la même
          législature, sur la <strong>dernière lecture de chaque texte</strong>, et seulement là où
          les deux atteignent leur quorum. Les dénominateurs diffèrent donc d'une ligne à l'autre,
          et chacun est publié. L'ordre est d'abord celui du nombre de textes communs ; à nombre
          égal seulement, l'accord départage, parce que les deux groupes se comparent alors sur la
          même base. Trier sur l'accord seul rangerait des parts calculées sur des bases
          différentes, et ferait un classement des alliés.
        </p>
        <p>
          <strong>Voter dans le même sens n'est pas s'entendre.</strong> Deux groupes peuvent
          rejeter un texte pour des raisons opposées, et la donnée ne dit rien de ces raisons. Et
          « nuance » n'est pas « opposé » : une abstention face à une position exprimée n'est pas un
          vote contraire.
        </p>
      </>
    ),
  },
  {
    famille: 'Fiche de gouvernement',
    note: (
      <p>
        Aucune section de méthode ne décrit encore cette fiche, alors qu'elle publie trois blocs :
        les comptages de textes portés par statut, les textes suivis et les membres du gouvernement.
        C'est un manque de cette page, pas une absence de règle — les règles de traçabilité et de
        non-notation s'y appliquent comme partout ailleurs.
      </p>
    ),
  },
  { famille: 'Ce qui vaut pour toutes les fiches' },
  {
    id: 'couverture',
    heading: 'Ce qu\u2019on n\u2019a pas pu lire',
    body: (
      <>
        <p>
          L'absence de donnée reste une absence de donnée, jamais un zéro. Chaque fait sensible doit remonter
          à une source primaire ; les classifications thématiques par mots-clés sont des aides de lecture, pas
          des positions déclarées.
        </p>
        <h3>Ce que les trois refus veulent dire</h3>
        <p>
          La fiche les écrit en une phrase chacun, parce qu'une page qui se contente de ne pas
          répondre laisse croire qu'elle n'y a pas pensé. Le raisonnement est ici.
        </p>
        {STATED_REFUSALS.map((refus) => (
          <p key={refus.id}>
            <strong>{refus.phrase}</strong> {refus.pourquoi}
          </p>
        ))}
        <h3>La qualification d'un groupe n'est pas déductible</h3>
        <p>
          L'Assemblée nationale déclare elle-même si un groupe est majoritaire, minoritaire ou
          d'opposition. Quand elle ne l'a pas fait — et elle ne l'a fait sur aucun groupe de la
          législature en cours —, la fiche l'écrit et s'arrête là. Le déduire d'un comportement de
          vote serait un jugement, pas une lecture.
        </p>
        <h3>Sur une fiche de groupe : ce qui est écarté, ce qui est gardé</h3>
        <p>
          Un vote sans identifiant de scrutin est <strong>écarté</strong> : sans scrutin, il ne se
          rattache à aucun texte ni à aucune législature, et n'entre dans aucun décompte. Une
          intervention dont l'identifiant ne porte pas de législature est <strong>gardée</strong> :
          rien ne prouve qu'elle soit hors de la période, et l'écarter ferait passer une ignorance
          pour un fait. Un amendement sans identifiant ne peut pas être reconnu d'un cosignataire à
          l'autre : il est compté une fois par signataire. Un membre déclaré par l'Assemblée dont
          le profil manque n'entre dans aucune section. Chaque fiche dit lesquels de ces cas la
          concernent, et combien.
        </p>
        <h3>Pourquoi un siège peut porter deux enregistrements</h3>
        <p>
          La source rend parfois plusieurs enregistrements de mandat électif pour un même siège :
          l'un d'eux est antérieur à l'estampillage de la chambre. Ils sont regroupés sur leur date
          de fin, et <strong>aucun n'est supprimé</strong> — un enregistrement écarté est une
          collecte qu'on ne peut plus vérifier.
        </p>
      </>
    ),
  },
];

export default function MethodologyPage() {
  return (
    <StaticPage
      eyebrow="Empreinte politique"
      title="Méthode éditoriale"
      tagline="Des faits sourcés, sans note de performance."
      intro={INTRODUCTION}
      sections={SECTIONS}
    />
  );
}
