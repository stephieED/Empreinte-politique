# Design system — Empreinte politique (UI_finale)

Version finale, réconciliée avec le code de production. Cette v2 part de la direction artistique préliminaire publiée en artifact Claude (« Empreinte — Direction artistique · v1 », [claude.ai/code/artifact/d48b7554-0af3-45bd-904e-94367577ff4a](https://claude.ai/code/artifact/d48b7554-0af3-45bd-904e-94367577ff4a), 2026-08-14) et la confronte ligne à ligne au code réel de `web/UI_finale/src`. Chaque valeur ci-dessous est soit **vérifiée** (présente telle quelle dans le code), soit signalée **cible** (présente dans la DA préliminaire mais pas encore strictement respectée par l'implémentation — voir §8 Écarts).

`docs/design_intent.md` (pistes cartographie/géologie/archéologie/architecture pour `web/v4`-`v7`) reste **obsolète et non retenu**, sans lien avec ce document.

Le brief et les itérations qui ont mené à cette DA (cibles, socle « SaaS analytique », pivot loin d'une première direction façon Revolut, alternatives explicitement écartées) sont documentés dans `docs/decisions/direction-artistique-empreinte.md`.

---

## 0. Principe directeur

*« Donner à lire l'activité parlementaire sans jamais la noter. »*

Un système au service d'une règle éditoriale, pas l'inverse : chaque décision de marque, couleur, typographie ou composant sert la neutralité et la traçabilité définies par [[ligne-editoriale-empreinte-politique]] (`AGENTS.md §2`). La section 6 (Voix) formalise ce lien — c'est la partie la plus originale de la DA préliminaire et la moins visible en lisant seulement le CSS.

---

## 1. Marque

**Symbole et lockup** — une empreinte de pas stylisée : la trace, pas le jugement porté sur elle. Le jaune signal ne marque jamais le texte du logo ; il reste réservé à l'arche du pas.

Trois formes, verified dans `src/components/Brand.jsx`/`Brand.css` et cotées dans `web/old/logo-propositions/exports/empreinte-lockup-2lignes-specs.md` :

| Forme | Usage | Cote |
|---|---|---|
| Signature courte (symbole + « Empreinte ») | Nav, en-têtes compacts, contextes à espace comptable | — |
| Lockup complet (symbole + « Empreinte politique ») | Réservé aux contextes ≥ 58px de haut | Sous ce seuil, la légende « POLITIQUE » (vectorisée à 12px de référence) devient illisible |
| Symbole seul | Favicon, app icon, avatar, nav réduite/mobile (< 480px) | Toujours carré, jamais étiré. **Traits encre `#17141f` sur fond clair** : `empreinte-symbol-light.svg` a porté jusqu'au 16/09/2026 les traits blancs de la variante pour fond sombre, et le logo mobile ne montrait plus que le point jaune |

**Zone de protection** : 16px minimum sur les 4 côtés, déjà intégrée dans le viewBox de chaque SVG maître — aucun élément de nav ne doit l'entamer. *Vérifié* : viewBox de référence `13.52 -0.73 329.27 87.26`, marge réelle 16px (specs.md).

**À faire** : dimensionner le SVG en `width`/`height` réels pour un rendu vectoriel natif — jamais de `transform: scale()` en CSS.

**À éviter** :
- Afficher le lockup complet sous 50px de haut — la légende devient un magma illisible (*vérifié* : `Brand.css` le rend à 58px précisément pour cette raison).
- Le jaune signal en texte ou trait fin sur fond clair — ratio de contraste **1.05:1, échec AA** (voir §2 pour la table complète). Réservé à l'accent graphique non textuel de jour.

---

## 2. Couleur

**Principe** : l'encre et le blanc cassé portent tout le texte. Le jaune signal ne sert jamais à indiquer un jugement — il marque la sélection, l'action, le lien vers la source. Les couleurs de vote sont **fonctionnelles, pas décoratives** : vert et rouge ne restituent qu'un scrutin réel, jamais une préférence éditoriale.

### Palette neutre — *vérifiée*, `src/index.css` `:root`

| Token | Valeur | Usage |
|---|---|---|
| Européen `--pe` | `#003399` | Le Parlement européen — **Pantone Reflex Blue de l'emblème**, la seule couleur officielle des quatre qui soit réutilisable |
| Gouvernemental `--gouv` | `#85510D` | Le gouvernement sur la fiche |
| Parlementaire `--parl` | `#803060` | L'Assemblée sur la fiche |
| Sénatorial `--fc-senat`, `--senat` | `#169E9E` | **Sarcelle, posée le 15/09/2026** sur /couverture, **le 16/09 sur la fiche candidat** — la collecte est rebranchée pour les appartenances (#885), et le Sénat prend sa ligne dans la frise. Retenue **malgré** le critère de famille : 67° du bleu de l'Union, sous le seuil de 72°. Ce qui l'a emporté : sous daltonisme, **Europe/Sénat est la paire la plus séparée des six** — ΔE 33,0 en protanopie, 29,7 en deutéranopie, 29,5 en tritanopie, quand Assemblée/Gouvernement tombe à 10,4 et Assemblée/Europe à 11,2. L'ajouter ne dégrade rien. Les 67° disent « elles se lisent comme parentes » ; chaque institution portant son titre au-dessus de ses lignes, la parenté n'induit pas de hiérarchie |
| Mandats locaux `--local` → `--neutre` | `#9A958D` | Le gris que le Sénat portait tant que sa collecte était hors périmètre. Il passe aux **mandats locaux**, qui ne sont pas une institution : sur la frise de la fiche candidat depuis le 16/09/2026, texte en encre (6,1:1). `--local` pointe sur `--neutre`, sans recopier la valeur |
| Données collectées de `/couverture` | `--fc-an` `#803060` · `--fc-gouv` `#85510D` · `--fc-pe` `#003399` | **Une seule catégorie, dans la teinte de son institution** — les valeurs de la fiche candidat. Les trois teintes de population (`--pop-cand`, `--pop-gouv`, `--pop-grp`) sont retirées le 11/09/2026 : le bleu ardoise des candidats se lisait comme le bleu de l'Union |

Chacune porte sa rampe de quatre valeurs — `--x`, `--x-wash`, `--x-pale`, `--x-line` —, en clair
seulement : l'UI n'a **pas** de mode nuit (`index.css` déclare `color-scheme: light`), et le
fragment qui en restait sur `.cp-gc` a été retiré
([`bloc-sombre-mort-retire-328`](../../docs/decisions/bloc-sombre-mort-retire-328.md)).

**« Trois teintes et pas quatre » tient toujours, et ce n'est plus une question de goût — c'est
une mesure.** Une fois retirées les familles qui portent déjà un sens (vert « pour », rouge
« contre », jaune d'emphase) et le bleu pris par l'Union, le cercle ne loge plus trois autres
institutions **sans parenté** : il ne reste que deux arcs, le chaud et le magenta. Zéro
combinaison sur les 32 teintes compatibles mesurées. La quatrième institution sort donc du
système de couleurs, et c'est le Sénat, dont aucune activité n'est collectée (#528).

**Une teinte n'est pas « distincte » parce que son ΔE passe.** Deux voisines de 42° se lisent
comme une famille, donc comme une hiérarchie entre deux institutions de même rang. Le critère est
double : l'écart mesuré **et** l'écart de famille — 72° minimum entre les trois retenues.

**La couleur se calcule, elle ne s'estime pas.** `scripts/validate_palette.js` de la compétence
`dataviz` rend cinq verdicts en une commande : bande de clarté, plancher de chroma, séparation
sous daltonisme (ΔE ≥ 8 en OKLab), plancher en vision normale (≥ 15), contraste. La palette
retenue donne 10,7 et 21,0 ; le seul échec porte sur `#003399`, plus sombre que la bande — c'est
la couleur officielle. **Le validateur ne compare pas les palettes entre elles** : vérifier qu'une
institution ne se lit pas comme une position de vote reste manuel, et cette vérification a écarté
une famille qu'il acceptait (un gouvernement en olive à ΔE 1,8 du rouge « contre » sous
protanopie).
→ [`teintes-des-institutions-328`](../../docs/decisions/teintes-des-institutions-328.md)

### Couleurs de vote & d'issue — *vérifiées*, `src/utils/lecture.js` (`VOTE_STYLE` / `OUTCOME_COLOR`)

| Sens | Hex | Constante code |
|---|---|---|
| Pour / Adopté | `#007A45` | `pour` / `adopté` |
| Contre / Rejeté | `#E53420` | `contre` / `rejeté` |
| Abstention / Tombé | `#8B8794` | `abstention` / `tombé` |
| **Non-votant** | **aucune** — contour tireté | `non_votant` |
| Retiré | `#F2A93B` | `retiré` |
| Irrecevable | `#B8B4AE` | `irrecevable` |
| Non soutenu | `#DCD9D3` | `non_soutenu` |

**Les positions de vote ne forment pas une échelle** (#326). Pour, Contre et Abstention sont des positions *exprimées* : elles portent une couleur. `non_votant` n'en est pas une — il se distingue par la **forme**, jamais par une teinte. Un dégradé chaud-froid sur les quatre fabriquerait un jugement (§2 règle 1 de `AGENTS.md`).

**Quatre valeurs, pas cinq.** « Absent » n'apparaît dans aucune des 1 312 951 positions publiées (mesuré au commit de données `245511b4`, 31/08/2026) : lui donner une catégorie publierait une absence comme un fait de vote, c'est-à-dire le taux de présence individuel qu'interdit §2 règle 3. Toute valeur inconnue tombe sur la forme sans teinte. Verrouillé par `tests/test_fondations_lecture_326.py`.

Ces couleurs vivaient en constantes JS **dupliquées** dans `CandidateProfile.jsx` et `GroupProfile.jsx`, sans `non_votant` — les 21 229 positions `non_votant` du corpus s'y affichaient sans couleur **ni libellé**. Elles sont désormais définies une seule fois, dans `src/utils/lecture.js`, que la fiche candidat et la fiche de lignée (`LigneeProfile.jsx`, depuis #329) importent.

### Table de contraste (WCAG AA, seuil 4.5:1)

| Paire | Premier plan | Fond | Ratio | Verdict |
|---|---|---|---|---|
| Texte principal, jour | `#14151A` | `#F7F6F4` | 16.88:1 | PASS |
| Texte principal, nuit | `#F7F6F4` | `#14151A` | 16.88:1 | PASS |
| Signal sur fond sombre | `#DFFF00` | `#14151A` | 16.01:1 | PASS |
| Signal sur fond clair | `#DFFF00` | `#F7F6F4` | **1.05:1** | **FAIL** |

C'est la justification chiffrée de la règle « accent jamais en texte sur fond clair » (§1, §5) — pas une convention arbitraire.

---

## 3. Typographie

**Manrope porte toute la hiérarchie — aucune deuxième famille.** C'est le poids et la taille qui font le travail, pas un contraste de style. Poids chargés : 400, 500, 600, 700, 800 (`index.html`, Google Fonts). Les nombres restent alignés en tabulaire (`font-variant-numeric: tabular-nums`) partout où ils se comparent — *vérifié* sur `.gp-kpi-value` et `.cp-num`.

### Échelle d'usage

| Usage | Exemple | Spécification | Statut |
|---|---|---|---|
| Titre profil (bannière h1) | « Jean-Luc Mélenchon » | 34px · 800 · -0.01em | Vérifié (`.banner h1`) |
| Valeur KPI | « 1 042 » | 26px · 800 · tabular-nums | Vérifié (`.gp-kpi-value`) |
| Grand nombre de fiche candidat | « 2 429 » | 22–28px · 800 · tabular-nums | Vérifié (`.cp-trace-nombre`, `.cp-bloc-nombre`, #328) |
| Titre de section | « Cohésion de vote » | 16px · 800 | Vérifié (`.gp-section-title`) |
| Titre de carte (vote/texte) | « L'ensemble du projet de loi » | 14px · 700 | **Partiel** — `.cp-ligne-titre` (14px/600, #328) et `.gp-vote-texte` (14px, poids hérité). Voir §8. |
| Libellé de chip/onglet | « Socialistes et apparentés » | 13px · 600 | Vérifié (`.cb-chip`, `.tab-btn`, `.cp-puce`) |
| Badge/pill | « Source » | 11–12px · 700 | Un lien de source est publié (`.vote-badge`, `.gp-verified-badge`) |
| Libellé de bande (majuscules) | « GROUPES » | 11px · 700 · +0.04em | Vérifié (`.cb-bar-label`, `.gb-bar-label`) |
| Métadonnée/caveat | « Mesure la durée, pas l'implication. » | 12–13px · 400–600 | Vérifié (`.gp-kpi-caveat`, `.cp-section-critere`) |

---

## 4. Espacements & formes

**Principe cible** : une seule gouttière de page (40px) et un vocabulaire de rayons à trois valeurs — le pilulier pour tout ce qui se choisit, la carte à 18px pour ce qui se lit, le cercle pour ce qui représente une personne.

### Espacements

Échelle cible (DA préliminaire) : `4 · 8 · 12 · 16 · 20 · 28 · 40 · 64`.
Échelle réellement observée dans `src/components/*.css` (relevé exhaustif) : `2, 3, 4, 5, 6, 8, 9, 10, 12, 14, 16, 18, 20, 22, 24, 28, 32, 40, 64` px. L'implémentation est plus dense que la cible — voir §8 pour la lecture de cet écart. `40px` reste bien la gouttière de page constante (`padding: 32px 40px 64px` sur `.main`, `.cp-main` et `.lp-main`).

### Rayons — *vérifiés*

| Rayon | Usage |
|---|---|
| 14–16px | Petit élément (membre, item de liste) |
| 18px | Carte |
| 999px | Chip / pilule |
| 50% | Avatar / donut |

### Élévation — *vérifiée*, correspond exactement aux `box-shadow` du CSS

| État | Valeur |
|---|---|
| Repos, petit item | `0 1px 8px rgba(20,15,40,.05)` |
| Repos, carte | `0 2px 12px rgba(20,15,40,.06)` |
| Survol, chip | `0 4px 14px rgba(20,15,40,.10)` |
| Survol, carte KPI | `0 6px 20px rgba(20,15,40,.14)` |

Toutes les ombres partagent la même teinte de base (`rgba(20,15,40,…)`, un noir-violet proche de `--ink`) — seule l'opacité varie avec le niveau d'élévation.

**Forme signature non couverte par la DA préliminaire** : les bandeaux d'en-tête (`.banner`, `.gp-banner`) ont un coin supérieur droit tranché à 28px (`clip-path: polygon(0 0, calc(100% - 28px) 0, 100% 28px, 100% 100%, 0 100%)`) — la seule rupture de forme rectangulaire du système, à traiter comme un élément de signature récurrent.

---

## 5. Composants

Vocabulaire vérifié dans `src/components/*.css` et `*.jsx` :

| Composant | Règle |
|---|---|
| **Carte KPI** | Survol → la mise en garde (« caveat ») recouvre la carte en overlay. Chaque métrique explique elle-même sa limite (`.gp-kpi-caveat`) — aucune n'est présentée comme un score. **Retirée de la fiche candidat depuis #328** : quatre KPI en tête de page classent avant qu'on ait lu un chiffre ; le critère de chaque section (`.cp-section-critere`) porte désormais la mise en garde, en permanence et non au survol. |
| **Carte de vote** | Point + libellé colorés selon la position (`VOTE_STYLE`). Le badge de source réutilise systématiquement le jaune signal — jamais une autre couleur pour ce badge précis. |
| **Badge de source** | **« Source »**, et rien de plus (`SOURCE_BADGE_VERIFIED`, #328). Le badge est vrai quand un `source_url` existe et qu'il est publié : il n'atteste **ni** une vérification que nous ne faisons pas, **ni** une autorité qu'il ne mesure pas. « Source officielle » a été écarté **sur mesure** — sur les 23 499 liens publiés des 32 fiches candidats, des 19 fiches de groupe et des 10 fiches de gouvernement, 22 988 pointent vers l'Assemblée ou le Parlement européen, mais **511 vers nosdeputes.fr**, un tiers : le mot aurait été faux 511 fois. Son pendant, « Lien de source non publié », ne bouge pas — il parle de NOUS, quand « non vérifié » ferait porter le doute sur la donnée. Que la source fasse foi **parce qu'elle est institutionnelle** est une phrase vraie et argumentée : elle se dit une fois, en méthodologie et dans le bloc Sources de l'accueil, jamais en trois mots répétés sous chaque fait. |
| **Pied du site** | **Un seul composant**, rendu par les quatre carcasses — accueil, explorateur, pages statiques, couverture (`PiedDeSite`, #328). Il y en avait trois, et celui des pages statiques n'existait pas : le contact était absent de la méthodologie, des mentions légales et de la couverture. Trois colonnes : la marque et la phrase éditoriale, les pages du site, « Nous joindre ». **L'adresse s'écrit en entier** — c'est ce qui la rend copiable, et ce qui a fait retenir ce rendu ; coût mesuré et assumé, le pied passe de 66 à 148 px sur toutes les pages. **Les pages sont des mots, les comptes sont des icônes** : la forme dit la nature du lien, un mot mène à une page du site, une icône ouvre autre chose. Chaque icône garde son `aria-label` en toutes lettres et une cible de 30 px — elle remplace le libellé **à l'écran**, jamais pour un lecteur d'écran ni pour le doigt. |
| **Onglets** | Fond plein jaune signal pour un onglet exclusif (`.tab-btn.active`). |
| **Pills de filtre** | Contour encre inversé pour un filtre multi-état (`.gb-chip.active` : fond `--dark`, texte blanc). Deux formes du même principe visuel, jamais confondues. |
| **Chip de sélection (groupe/candidat)** | Avatar à initiales + libellé. À l'état actif, l'avatar seul bascule au jaune signal — le fond de la chip passe à l'encre (`GroupsBar`) ou reste blanc à bordure encre (`CandidatesBar` — asymétrie assumée entre les deux barres, voir composants respectifs). |
| **Barre de répartition/comparaison** | Segments proportionnels au décompte réel, jamais normalisés à effet visuel — un groupe avec peu d'amendements produit une barre visiblement courte (`.cp-barre` et ses segments, #328).  Un segment **sans teinte** (motif hachuré, `.cp-barre-seg--sans-teinte`) est réservé à ce qui n'est pas une issue : un sort d'amendement non publié (§2 règle 5) et un texte adopté sans vote par l'article 49.3 (§2 règle 4). **Jamais pour une cohésion de vote** : `.gp-coherence-track`/`.gp-coherence-fill` sont retirées depuis #329, parce qu'une barre place des catégories sur une échelle du pire au meilleur (`AGENTS.md` §2 règle 1). |
| **Pastille de candidat sans mandat** | Fiche qui ne porte **ni mandat à l'Assemblée nationale ni fonction gouvernementale** : la pastille passe au gris des métadonnées (`.cb-chip--sans-mandat`, `#6f6b78` sur blanc, 5,5:1, AA) — jamais une couleur de jugement, et le jaune signal reste à la sélection (#328). Elle reste **cliquable, lisible et sélectionnable** : ni `disabled`, ni retrait de la liste, parce que la fiche existe et s'atteint. Son infobulle écrit ce que le grisé veut dire — une pastille plus pâle sans légende se lit comme un rang, et c'en serait un (§2 règle 1). Les deux faits sont lus, jamais devinés : `chambres` contient `"AN"` (champ dérivé, #493) ou un mandat de catégorie `fonction_gouvernementale`. |
| **Navigation par période politique** | **Un seul composant pour les deux sections qui découpent le temps** — `NavigationPeriodes.jsx/.css`, préfixe `np-` (#328). Deux flèches nommées portant l'année et le libellé court de la période visée, un **rail proportionnel** (un segment par période, large en proportion de son poids), l'année écrite seulement au-dessus de **12 %** de la largeur — en dessous, une date tronquée se lit comme une date fausse —, contour **tireté** quand aucun repère n'est publié (§2 règle 5). Les flèches du clavier sont portées par le conteneur, **jamais par `window`** : à deux sections, un écouteur global déplaçait les deux. « Toutes les périodes » est optionnel (`avecTout`) et « Ce qu'il a voté » ne le prend pas — y cumuler deux périodes reformerait le total de carrière que la vue refuse. |
| **Barre de sujet (fiche candidat)** | Barre d'encre pleine sous son libellé, jamais autour (`.pp-sujet-barre`, #328). Sa largeur vient du **plafond de la fiche**, pas du plus grand de la sélection courante : un filtre retire de la masse, il ne redimensionne pas. Le jaune signal marque le sujet **retenu**, et rien d'autre. Quand l'étendue passe à « toutes les périodes », le plafond change et le libellé le déclare non comparable — une échelle qui change sans le dire est le défaut que cette règle interdit. |
| **Verbatim** | Filet vertical + retrait (`.pp-verbatim`), sans guillemets typographiques ajoutés ni italique : le texte est celui du compte rendu, pas une citation mise en scène. Son absence prend le **motif hachuré** des vides déclarés (`.pp-sans-verbatim`) et nomme sa cause — collecte au thème seul, ou compte rendu sans verbatim —, jamais un fond vide qui se lirait comme un silence de la personne (§2 règle 5). |
| **Frise d'une lignée (fiche de groupe)** | L'effectif jour par jour, une bande par groupe successif (`LigneeProfile.jsx`, `.lp-frise`, #329). **La teinte est l'Assemblée, le motif est la posture** que l'Assemblée déclare pour la législature — retenu en maquette par la propriétaire le 11/09/2026 : majoritaire en aplat `--parl`, opposition en diagonales, minoritaire en mauve clair uni `--parl-mauve` `#c9a3b9`, non déclarée en petits points serrés (un grisé), toujours dans la teinte de l'Assemblée — un gris neutre se lirait comme le Sénat. La fiche candidat a retiré ses motifs le même jour (#328) parce que sa bande portait deux encodages ; celle d'une lignée n'en porte qu'un, la teinte ne variant pas. Le nombre au bout de chaque bande est l'effectif publié à la date de référence de la fiche ; la courbe recomptée depuis les appartenances y retombe au membre près. Sans effectif daté, la bande devient un contour tireté et la frise se réduit. |
| **Un point par personne (fiche de groupe)** | « Qui sont-ils » : un point par personne et par groupe de la lignée, en trois états — plein (déjà là au groupe précédent), pâle (revenu d'un groupe plus ancien), creux (nouveau dans la lignée) — et leurs trois comptes côte à côte, jamais un taux de renouvellement (§2 règle 1). Le survol ou le focus allume le chemin de la personne dans tous les groupes (`.lp-point--eclaire`). Forme B, retenue le 11/09/2026 après cinq agrégats écartés. |
| **Ce qui ressort d'une liste** | Un **filet d'encre** et le lavis `#fbfaf8` sur la ligne, jamais une teinte (`.cp-fonctions-item--marquee`, #328). Aucune couleur n'était libre : le jaune signal est pris par la sélection, l'action et le badge de source, le vert et le rouge par les positions de vote, le bleu et le bronze par les institutions de la frise — une quatrième aurait dilué les trois autres. La marque étant sans teinte, elle reste lisible en niveaux de gris et sous daltonisme **sans pictogramme de secours**. Deux états, jamais une graduation : une ligne la porte ou non, et rien ne hiérarchise les autres entre elles. |
| **Distinguer N matières dans une figure** | Une palette **catégorielle sans ordre** (Paul Tol, qualitative « muted »), attribuée par volume et par rien d'autre (`src/utils/matiere.js`, chute des dépôts). La ligne « aucune couleur n'était libre » ci-dessus reste vraie de son besoin — *marquer une ligne*, que la fiche résout par un filet d'encre. Distinguer des catégories est un besoin différent, et sans solution sans teinte : une rampe d'encre les placerait sur une échelle, ce que `AGENTS.md` §2 règle 1 interdit. La palette ne recouvre aucune teinte déjà attribuée, et le **gris** y est réservé à « matière non établie » — une absence de donnée (§2 règle 5), jamais une catégorie de plus. |
| **Distinguer les ÉTAPES d'une procédure** | Une **rampe d'encre** de quatre valeurs, du plus clair au plus foncé dans l'ordre que la source publie (`ENCRE_ETAPE`, cascade des textes portés, #328) — et c'est le cas où la rampe est **licite**, à l'inverse de la ligne ci-dessus. Les crans d'un stade procédural sont **ordonnés par la source** (`_STADE_RANKS` : déposé → examiné en commission → discuté en séance → adopté → promulgué), et une rampe ne fait que rendre visible un ordre qui existe. Elle ne dit **pas** qu'un texte promulgué vaut mieux qu'un texte en commission (§2 règle 1) : elle dit qu'il est allé plus loin dans une procédure, ce qui est un fait daté. La distinction avec les matières tient à ça, et à rien d'autre — des matières n'ont pas d'ordre, des étapes en ont un. La **barre de sortie** d'une porte (« non discuté », « non adopté ») est hors rampe, en gris `--ter-sortie` : elle ne marque aucune étape atteinte, elle constate qu'aucun acte au-delà n'est enregistré. **Un seul composant pour deux fiches** (`CascadeTextes.jsx`, #329) : la fiche candidat et la fiche de lignée dessinent la même cascade ; sur la seconde, une commission garde la même teinte dans la cascade et dans les barres d'amendements (prop `rangs`). |
| **Un fait procédural, pas une issue de vote** | Une **pastille d'encre pleine**, 999 px, texte blanc — `.gvp-texte-493` sur la fiche de gouvernement, `.cp-ter-493-marque` sur la fiche candidat (#743). Elle ne prend **aucune teinte de position** : ni le vert ni le rouge du vote, parce qu'un texte adopté par engagement de responsabilité l'a été **sans que l'Assemblée vote** (`AGENTS.md` §2 règle 4). Le sort correspondant s'écrit en encre pleine dans la liste (`.cp-ter-sort--493`) là où les autres restent en muted : c'est la seule issue qui ne soit pas une issue de vote, et elle doit se distinguer des huit autres sans être classée par rapport à elles. |
| **Titre de section surligné** | Un **dégradé jaune sur le tiers bas des lettres** — `linear-gradient(transparent 62%, var(--accent) 62%)` sur un `span` INTERNE au `h2` (`.cp-section-titre > span`, #328). Le `span` n'est pas un détail : posé sur le `h2`, bloc de la largeur de la colonne, le dégradé courrait jusqu'au bord et se lirait comme un fond de section. Le jaune ne porte **jamais** le texte (1,05:1 avec `--ink`) — il ne couvre que le bas des lettres, qui restent lues sur le fond de page. Le geste vient de la maquette de `/couverture` et vaut pour les deux pages : c'est la marque du **titre**, jamais un état ni une sélection, et rien d'autre ne la prend. |
| **« En bref » de la fiche candidat** | Deux figures (#328, maquette du 11/09/2026). **La frise du parcours** : la couleur dit l'institution, et un segment parlementaire ne porte que le **sigle du groupe et la place dans l'hémicycle** (« FI · opposition ») — un sigle se lit ou se retrouve sur les fiches de groupe, il ne se fabrique jamais ; sans lui, le segment se tait. **« En chiffres »** : une phrase par rang, le **total** du rang en gras au corps du texte, le détail dessous — aucun grand chiffre, pour qu'aucun nombre ne pèse plus que ce qu'il compte. |
| **Frise de couverture (`/couverture`)** | **Un rail, une encre** (`.fc-rail` / `.fc-couche`, #328). Les faits portés par les fiches de candidats, de gouvernement et de groupe vivent dans le même rail, **sous une seule catégorie « Données collectées », dans la teinte de leur institution** — Assemblée prune, Gouvernement ocre, Parlement européen bleu de l'Union, les valeurs de la fiche candidat (tranché par la propriétaire le 11/09/2026) ; la fiche d'origine n'est plus encodée, le survol d'un segment la nomme encore. Le Parlement européen porte une hachure avant la borne basse de ses dumps (votes 15/09/2004, amendements 01/02/2008) et après la dernière date parue à sa source, que le pipeline déclare (#683) ; la première donnée d'une personne n'est jamais une borne. Deux absences, deux motifs, jamais confondus (§6 bis règle 7) — la **hachure pâle** dit « la source ne publie pas » (un fait sur l'institution, immuable), le **jaune hachuré à filet d'encre** dit « nous ne l'avons pas collecté » (un fait sur NOUS, et l'accent marque l'action dans ce système). |
| **Recherche sur une fiche (candidat, groupe)** | **Une barre en pilule** sous l'en-tête de la fiche (`.cp-filtre`, #979) : un mot (« Rechercher sur cette page »), et la fiche se recalcule sur ce que les intitulés — et, pour les interventions, les verbatims — portent. Le mot est surligné dans le verbatim (`.pp-mot`). Tant qu'un mot est tapé, « En bref », « Les fonctions exercées » et « Ce qu'on n'a pas pu lire » se retirent, et **chaque figure porte en tête une étiquette** « Contenant « … » » (`.cp-filtre-etiquette`), le mot surligné sur le bas des lettres comme un titre de section — pour qu'une capture de la figure seule ne circule pas sans lui. Un mot sans résultat laisse la section en place avec une note du filtre (`.cp-filtre-vide`), jamais le « Non collecté » d'une collecte vide. Arbitré sur maquette le 17/09/2026 : `docs/decisions/filtre-par-intitule-fiche-candidat-979.md`. **Sur la fiche de gouvernement** (`recherche-fiche-gouvernement-979`, 20/09/2026) : « En bref » et « Qui le composait » se retirent, « Ce qu'on n'a pas pu lire » reste, les débats et les textes déposés se recalculent, et rien ne se télécharge en plus — la fiche porte déjà tous les intitulés. **Sur la fiche de groupe** (`recherche-fiche-groupe-979`) : « En bref » et « Qui sont-ils » se retirent, « Ce qu'on n'a pas pu lire » reste, et chaque section **empile les groupes de la lignée** où le mot trouve quelque chose, sans flèches. Barre, étiquette et note : `components/Recherche.jsx`, un seul composant pour les deux fiches. |
| **Intitulé trop long** | Coupé à **deux lignes** (`.cp-fonctions-ligne`, #328) — une seule perdait trop sur des libellés de 200 caractères. Ni `-webkit-line-clamp` ni `text-overflow` : ils peignent leurs propres points, et le « … » est un **vrai bouton** portant `aria-expanded`, posé uniquement sur ce qui déborde réellement. |
| **L'intitulé porte le lien de source (fiche de groupe)** | Sur la fiche de lignée, **plus de badge « Source »** sous chaque ligne (relecture du 11/09/2026) : l'intitulé du scrutin ou du dossier est souligné et mène à la source (`.lp-lien`). Sans URL publiée, il reste du texte et « lien de source non publié » le suit. La fiche candidat garde son badge : l'écart est consigné dans `docs/decisions/fiche-de-lignee-ui-329.md`, et la décision de l'aligner revient à la propriétaire. |
| **Ce qu'on n'a pas pu lire (fiche de groupe)** | La section 6 de la fiche de lignée reprend la grammaire de « Ce que la collecte signale » de la fiche candidat — l'intitulé de la liste à gauche, un signalement par groupe de la lignée à droite, du plus récent au plus ancien (`.lp-signal`). Elle ne porte que ce que **chaque fiche** signale d'elle-même ; ce qui vaut pour tout le corpus est dit une fois sur `/couverture` (#328) — une limite de source écrite sous le nom d'un groupe se lirait comme une limite de ce groupe. Sans signalement, une ligne le dit : une section absente se lirait comme un oubli. |

---

## 6. Voix — le ton fait partie de la direction artistique

*Empreinte documente, elle ne classe pas.* Cette règle se lit autant dans le vocabulaire que dans la couleur — section absente de ma première version de ce document, réintégrée depuis la DA préliminaire car elle formalise un lien direct avec [[ligne-editoriale-empreinte-politique]] :

- **Chaque métrique porte sa propre limite** : aucun chiffre n'est affiché seul. Une phrase de mise en garde accompagne systématiquement la valeur — au survol sur la fiche de groupe (`.gp-kpi-caveat`), **en permanence** sur la fiche candidat depuis #328 (`.cp-section-critere`, `.cp-note`), parce qu'une limite qu'il faut survoler n'est pas lue.
- **Précision plutôt qu'emphase** : « Lecture la plus avancée retenue pour chaque texte », pas « votes comptés ». Le vocabulaire nomme exactement ce qui est mesuré, jamais ce qu'on aimerait suggérer.
- **Aucun vocabulaire de classement** : pas de « score », « note », « rang » ou « performance » nulle part dans l'interface — jusque dans le texte d'aide du panneau latéral. Découle directement de la règle éditoriale 1 (`AGENTS.md §2`).
- **La couverture partielle s'assume** : « 14 / 66 membres » s'affiche tel quel, sans arrondi flatteur ni habillage en pourcentage seul — cohérent avec la règle éditoriale 7 (ratios toujours num/dénom).

**La baseline, depuis le 18/09/2026** (#1026) — *vérifiée*, `Baseline.jsx` :
> « 100 % automatisé • 100 % sourcé • 0 score • 0 filtre »

Deux places, arbitrées : le **bandeau de l'accueil** (`.baseline--bandeau`, 15 px, puces en accent — 16,01:1 sur l'encre) et le **pied de page**, sous la marque, sur toutes les pages (`.baseline--pied`, 13 px, puces en gris — le jaune tombe à 1,05:1 sur fond clair, §2). **Pas l'en-tête collé** : répétée en haut de chaque écran elle devient du décor, et la rangée est à hauteur fixe. Les quatre mentions sont définies **une seule fois** — `tests/test_baseline_1026.py` refuse qu'un composant les recopie. Elle remplace deux textes qui disaient la même chose à moitié : « Données publiques agrégées. Aucun score, aucun classement. » dans le pied, et « Des faits sourcés, sans note ni classement — à consulter par candidat, par groupe ou par gouvernement. » sous le titre de l'accueil.

L'autre texte permanent cité par la DA préliminaire :
> « Empreinte politique ne publie aucun taux individuel d'assiduité, de présence ou d'absence — un scrutin manqué ne décrit ni le travail parlementaire ni ses motifs. »

Il reste à vérifier au prochain audit — non confirmé dans le CSS/JSX lu pour cette version. Le pied du site, lui, est **un seul composant** depuis #328 (`PiedDeSite.jsx`), rendu par les trois carcasses.

---

## 6 bis. Ce qu'une vue doit au lecteur — sept règles de forme

La section 6 dit le **ton**. Celle-ci dit ce qu'une vue doit **au lecteur**, et
c'est ce qui manquait : ni ce document ni `AGENTS.md` §2 ne disqualifiait une
mesure **vraie, disponible et conforme** dont personne ne peut rien tirer.

Les sept règles ont été arbitrées en maquette les 01 et 02/09/2026 sur la fiche
candidat. **Elles valent pour toute vue** — la fiche de groupe (appliquées à la fiche de lignée par #329) et celle de
gouvernement ne les ont pas encore appliquées. Chacune est ici en une ligne ; ce
qui l'a tranchée, avec ses mesures et ce qui a été essayé puis écarté, est dans
[`regles-de-forme-des-vues-326`](../../docs/decisions/regles-de-forme-des-vues-326.md)
— **une règle sans son coût se rediscute**, donc on la lit là-bas avant de la
contester.

1. **Un chiffre dont le lecteur ne peut rien tirer ne se publie pas.** La seule
   règle sans équivalent dans §2, qui dit ce qui est interdit et jamais ce qui est
   inutile. Elle disqualifie une mesure dont on ne peut **rien conclure**, jamais
   une dont on n'aimerait pas la conclusion : le premier cas se démontre, le
   second se déclare.
2. **Le texte explicatif est un aveu d'échec.** Si une phrase doit expliquer un
   chiffre, c'est la forme qui a échoué. Vaut aussi pour les **noms** : un titre
   qui promet ce que le bloc ne délivre pas est la même faute. Ne dispense pas de
   la limite permanente exigée en §6 — une limite tient en deux mots, une
   explication en paragraphe.
   **Où va le paragraphe, depuis #328** : dans la page de méthodologie, qui porte
   **une ancre par section de la fiche** (`fonctions`, `propose`, `votes`,
   `ecarts`, `interventions`, `couverture`). La fiche garde la limite et le
   renvoi ; un renvoi sans fragment ferait rouvrir douze sections pour retrouver
   la règle qu'on vient de perdre de vue. `tests/test_pourquoi_en_methodologie_328.py`
   refuse un critère de section au-delà de 22 mots, et un renvoi vers une ancre
   qui n'existe pas.
3. **Un nombre sans son objet ne dit rien, et seuls les nombres sont en gros.**
   L'objet reste à l'échelle des libellés ; une différence de taille entre deux
   nombres appariés est une hiérarchie de valeur.
4. **Chaque mesure compte contre son propre total.** Deux natures ne partagent
   jamais un dénominateur, et un total commun ne s'affiche pas.
5. **Aucun seuil arbitraire ne décide qu'il y a un fait.** Une mise en évidence
   qui ne peut pas se taire ne dit rien quand elle parle.
6. **Quand le volume ne distingue pas deux intentions, c'est la date qui range.**
7. **Deux absences ne se confondent jamais** — un fait sur le métier, une valeur
   déclarée par la source, un trou chez nous : trois rendus distincts (§2 règle 5).

Ces règles **s'ajoutent** à `AGENTS.md` §2, elles ne l'amendent pas : §2 est
éditorial et non négociable, celles-ci sont de forme et s'affinent. Une vue peut
satisfaire les sept et violer §2 — c'est §2 qui tranche.

---

## 7. Grille & réponse

- **Une seule vraie rupture, sur la marque** : sous 480px, le lockup complet cède la place au symbole seul — la largeur ne suffit plus à garder « POLITIQUE » lisible. *Vérifié* : `Brand.css` `@media (max-width: 480px)`.
- **Grilles de cartes** : `auto-fit`/`minmax()` plutôt que des colonnes fixes — le nombre de colonnes se déduit de la largeur réelle, jamais fixé par point de rupture. *Vérifié* : `.kpi-grid`, `.votes-grid`, `.shelf-items`, `.gp-kpi-grid`, etc.
- **40px** : gouttière horizontale constante de la page — navigation, contenu, bandeau de marque partagent la même marge, jamais une marge indépendante. *Vérifié*.
- **1600px** : largeur maximale de la zone de contenu — au-delà, l'espace supplémentaire se redistribue dans les grilles plutôt que de laisser un vide. *Vérifié* : `.main` `max-width: 1600px` ; les fiches (`.cp-main`, `.lp-main`) plafonnent à 1 100 px.

---

## 8. Écarts entre la DA préliminaire (cible) et l'implémentation actuelle

À corriger ou à assumer explicitement lors d'un prochain passage sur `web/UI_finale` :

1. **Titres de carte vote/texte pas en 700** : `.vote-title` a disparu avec la refonte de la fiche candidat (#328), remplacée par `.cp-ligne-titre` en 14px/600 ; `.gp-vote-texte` est toujours à 14px sans `font-weight` explicite. Reste à harmoniser entre 600 et 700, sur une seule valeur.
2. **Échelle d'espacement plus dense que la cible** : la cible propose 8 valeurs (`4·8·12·16·20·28·40·64`), le code en utilise 19 (`2,3,4,5,6,8,9,10,12,14,16,18,20,22,24,28,32,40,64`). Pas nécessairement un bug — beaucoup de ces valeurs sont des ajustements fins légitimes (ex. `9px` padding tab) — mais si l'intention est de converger vers l'échelle à 8 valeurs, c'est un chantier de refactor CSS, pas une correction ponctuelle.
3. ~~**Couleurs de vote dupliquées sans partage de source**~~ — **corrigé par #326** : `VOTE_STYLE`/`OUTCOME_COLOR` vivent dans `src/utils/lecture.js`, avec les cinq autres primitives de lecture, et les deux composants les importent. Les règles propres à la fiche de groupe sont dans `src/utils/groupe.js` (#329), qui importe le premier.
4. **Chip active — asymétrie Candidats/Groupes** : `CandidatesBar` (`.cb-chip.active`) passe en fond blanc à bordure encre, `GroupsBar` (`.gb-chip.active`) passe en fond encre plein — la DA préliminaire ne documente qu'un seul comportement (« le fond de la chip passe à l'encre »). À vérifier si l'asymétrie est un choix voulu (différencier visuellement candidat vs groupe) ou une divergence non intentionnelle.
5. **Texte permanent du panneau latéral non retrouvé** dans le CSS/JSX lu pour cette version — à confirmer lors d'un prochain passage avant de le citer comme garantie de conformité. Le texte du pied de navigation est désormais implémenté (`ExplorerLayout.jsx` `.explorer-footer`).

---

## Sources de vérité (à relire avant toute modification de ce document)

- DA préliminaire (structure, ton, table de contraste, couleurs de vote) : artifact Claude [d48b7554-0af3-45bd-904e-94367577ff4a](https://claude.ai/code/artifact/d48b7554-0af3-45bd-904e-94367577ff4a)
- Couleurs/typo racine : `web/UI_finale/src/index.css`
- Couleurs de vote/issue et les six règles de lecture communes : `web/UI_finale/src/utils/lecture.js` (`VOTE_STYLE`/`OUTCOME_COLOR`, #326), rendues par `src/components/Lecture.jsx`
- Sélection des votes sur l'ensemble d'un texte (`isWholeTextVote`, #672) et **repli sur la dernière lecture** (`selectDerniereLectureVotes`, `LAST_READING_RULE`, #711) : même fichier, `web/UI_finale/src/utils/lecture.js`. La formule citée en §6 — « Lecture la plus avancée retenue pour chaque texte » — n'était appliquée par aucun code jusqu'à #711 ; c'est désormais la **date** qui choisit, sur le corpus entier des scrutins
- Règles de lecture propres à la fiche de groupe : `web/UI_finale/src/utils/groupe.js` (#329) ; celles de la LIGNÉE — effectif recompté, états de passage, amendements par commission, motif de posture — dans `web/UI_finale/src/utils/lignee.js`, importé aussi par la projection de build `scripts/vue-lignee.mjs`
- Durée de siège, règle de mise en avant et rôle distinctif de la section « Les fonctions exercées » : `web/UI_finale/src/utils/profilCandidat.js` (`joursCumules`, `dureeDeSiege`, `fonctionsExercees`, `roleDistinctif`, #328) — le nombre affiché est une **durée en union d'intervalles**, jamais un compte d'enregistrements, et ce qui ressort dépasse la **moitié du temps de mandat**. Voir `docs/decisions/fonctions-exercees-duree-de-siege-328.md`
- Règles de lecture propres à la fiche candidat : `web/UI_finale/src/utils/profilCandidat.js` (#328), rendues par `src/components/CandidateProfile.jsx` — la trame en **six** emplacements et la colormap de la frise (teinte = institution, motif = position). Sept jusqu'au 08/09/2026 : « les gouvernements dont il a été membre » a été retiré et l'ordre a changé — ce qu'il a **voté** et ses **divergences** passent avant ce qu'il a **dit** (`docs/decisions/six-emplacements-fiche-candidat-328.md`). Les **trois situations d'une année de vote** (`gouvernement`, `hors_mandat`, `en_mandat`) ont disparu avec l'axe des années : elles protégeaient un `0` d'être lu comme une absence individuelle (§2 règle 3), ce qui n'a de sens que sur un axe **continu** — la vue par période politique n'affiche aucune période sans vote (`docs/decisions/votes-par-periode-politique-328.md`)
- Motif de fond, layout : `web/UI_finale/src/styles/shell.css`, `ExplorerLayout.css` — depuis #951 (16/09/2026) **la rangée du logo reste collée** sur l'explorateur et l'accueil (`EnTeteSite.jsx`) (80 px, 56 px sous 480 px) avec les pages du site (`NavigationSite.jsx` : Explorateur · Méthodologie · Sources · FAQ, la page courante en encre soulignée de jaune). **Depuis #1025 (18/09/2026) les trois listes ont quitté la page** : elles ne vivent plus que dans un **tiroir**, qui porte aussi « Rechercher sur cette page » (`.explorer-tiroir`), et dont le bouton **prend la place de l'onglet « Explorateur »** là où cet onglet est la page courante — il y renvoyait à la fiche par défaut. Sous 720 px, les liens passent dans « Menu » et la barre ne porte plus que ce bouton, à droite de lui. La mise en page ne change jamais au défilement : l'en-tête de #324, qui retirait les listes au-delà de 180 px, ramenait le défilement à 0 en boucle (`docs/decisions/entete-colle-listes-qui-defilent-951.md`). Un **sommaire de sections** occupe 204 px de marge au-delà de 1 440 px de fenêtre — jamais sur le contenu, qui reste à 1 100 px (`docs/decisions/cadre-fiche-repli-et-sommaire-324.md`)
- Composants : `web/UI_finale/src/components/*.css`
- Cotes exactes du logo : `web/old/logo-propositions/exports/empreinte-lockup-2lignes-specs.md`
- Métadonnées PWA/SEO : `web/UI_finale/index.html`
- Règles éditoriales que la DA sert : `AGENTS.md §2`, mémoire [[ligne-editoriale-empreinte-politique]]
