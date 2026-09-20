<a id="profil-de-groupe-lecture-329"></a>
# La fiche de groupe se lit en nombres datés, jamais en barres ni en compteurs nus (#329) (2026-08-31)

`2026-08-31`

> **En bref** — troisième lot d'implémentation de #324, posé sur les six fondations du lot 1 (#326) : les règles propres au groupe vivent dans `web/UI_finale/src/utils/groupe.js`, qui **consomme** `ratio`/`truncation`/`emptyListMessage`/`sourceBadge`/`styleForPosition` et n'en réécrit aucune ; la **barre de cohérence** (`.gp-coherence-track`/`.gp-coherence-fill`) est **retirée** au profit des six décomptes, parce qu'une barre place des catégories sur une échelle du pire au meilleur (§2 règle 1) et que la partition est exacte — `pour + contre + abstention + non_votant + absents + excuses == membres_eligibles` sur **19 832 / 19 832** entrées des 5 fiches AN, `taux_participation` retrouvé 19 832 / 19 832 et `taux_coherence` 19 687 / 19 832, les 145 restantes étant celles à `position_majoritaire: null` et 0 vote exprimé ; `absents` s'affiche **« Sans trace de vote »** parce que le pipeline y compte les éligibles pour qui AUCUN vote n'a été trouvé — une absence de donnée, pas une absence constatée, et « absents » publierait le taux de présence qu'interdit §2 règle 3 ; `excuses` n'est **pas publié**, valant 0 sur les 19 832 entrées faute de position `excuse` dans le corpus (le cas d'`absent` dans les 1 312 951 positions de #326), et la décision est prise à l'échelle de la **fiche**, jamais de l'entrée ; le KPI « **Effectif actuel** » disait faux deux fois — il affichait `roster_total` (76 sur `AN:LFI`) et se disait « actuel » sur une législature close — et devient « Membres du groupe au 09/06/2024 », 75 sur 76, avec l'origine de `date_reference` publiée ; **les deux jeux de noms sont lus** (#653/#656 et leurs anciens noms), sans quoi les 17 cartes de mandats des 2 fiches Sénat gelées rendaient `undefined membre y a siégé au moins une fois` et « Aucun membre n'y siégeait » sur une donnée absente (§2 règle 5) — « Sénat · Législature null » corrigé au passage ; les `slice(0, 12)` et `slice(0, 20)` déclarent enfin leur dénominateur (3 832 à 4 099 scrutins, 1 554 à 4 303 étiquettes) et leur règle, **vérifiée** : `cohesion_votes` est trié par date décroissante sur les 5 fiches, contrôlé après jointure sur `pivot_data/scrutins.json` (19 832 / 19 832 résolues, 19 832 / 19 832 avec `source_url`) ; `meta.couverture_roster.etat`/`preuve`, publiés sur 7/7 fiches et lus par personne, ouvrent une section « Vérification » — 15 profils sur 235 sur `groupe-Senat-LR` est un **périmètre**, pas une perte, et `hors_perimetre` est traduit en `non_collecte` et non `hors_couverture`, parce que ce vide vient de NOTRE décision et pas d'une période que la source ne publierait pas ; l'**empreinte thématique** passe de la case D à la case A sur décision de la propriétaire, le motif de son report (« 0 / 468 membres portent une intervention ou un tag ») étant périmé par #657 — re-mesuré à `c6edee05` : **448 / 468** profils `roster_groupe` portent une étiquette, les 5 fiches AN en publient 1 554 à 4 303 avec `nb_membres_porteurs` jusqu'à **99**, et chaque étiquette part avec son porteur sur `len(membres)` (jamais `roster_total`), sous une phrase qui rappelle que ce sont des sujets d'intervention et non des positions (§2 règle 8) ; la fiche déclare enfin ce qu'elle ne publie pas — elle ne nomme jamais qui s'est écarté de la ligne, l'écart individu/groupe restant un contrôle interne ; 22 cas Python lisant le **code exécuté** (commentaires retirés) verrouillent le tout, faute de runner JS ; `meta.avertissements[]` absent des fiches de groupe, `mandats_agreges` non tronqué (535 à 1 153 cartes) et la 6ᵉ vue (#672) sont nommés et laissés hors lot.

Troisième lot d'implémentation de #324, posé sur les six fondations du lot 1
(#326, `web/UI_finale/src/utils/lecture.js`). Les règles propres au groupe
vivent dans un module unique, `web/UI_finale/src/utils/groupe.js` : elles
**consomment** `ratio`, `truncation`, `emptyListMessage`, `sourceBadge`,
`styleForPosition` et `formatNumber`, elles n'en écrivent pas de seconde
version — six règles réécrites trois fois divergent trois fois.

Une fiche de groupe agrège les **468 profils `roster_groupe`**, qui n'ont pas de
page à eux. Aucun chiffre de ce lot ne parle des 13 `candidat_declare`.

Toutes les mesures ci-dessous sont prises au commit `c6edee05`, le 31/08/2026,
sur les **7 fiches publiées** : 5 pour l'Assemblée nationale (XVIe législature,
**19 832** entrées de `cohesion_votes`) et 2 pour le Sénat, conservées et jamais
régénérées (#516/#528).

## 1. La cohésion se publie en six nombres, jamais en barre

`GroupProfile.jsx` rendait `taux_coherence` en **barre pleine**, teintée de la
couleur de la position majoritaire. Une barre de progression se lit comme une
échelle du pire au meilleur ; `pour`, `contre` et `abstention` sont des
**catégories**, et les placer sur un dégradé fabrique un jugement (AGENTS.md §2
règle 1). `.gp-coherence-track` et `.gp-coherence-fill` sont **retirées**, pas
masquées.

Ce qui les remplace tient parce que la partition est **exacte** :

| Vérification | Résultat |
| --- | ---: |
| `pour + contre + abstention + non_votant + absents + excuses == membres_eligibles` | **19 832 / 19 832** |
| `taux_participation == (pour + contre + abstention + non_votant) / membres_eligibles` | **19 832 / 19 832** |
| `taux_coherence == <position majoritaire> / membres_eligibles` | **19 687 / 19 832** |
| … les 145 restantes | `position_majoritaire` **`null`**, 0 vote exprimé, `taux_coherence` `null` |
| `scrutin_id` résolu dans `pivot_data/scrutins.json` | **19 832 / 19 832** |
| `source_url` publié sur le scrutin joint | **19 832 / 19 832** |

Le ratio de cohésion est donc recomposé à partir de ses **deux nombres** — le
décompte de la position majoritaire sur `membres_eligibles` — et jamais depuis
le taux pré-divisé. Le dénominateur est **borné par chambre depuis #492** : une
union sur tous les mandats électifs comptait un membre absent sur des scrutins
où il ne pouvait plus voter. Les 145 entrées sans position exprimée rendent
`N/D`, jamais `0` (§2 règle 5).

**Le quorum ne se publie pas sans son seuil.** `meta.seuil_quorum` vaut 0,5 sur
les 7 fiches, et **2 415 des 19 832** entrées l'atteignent. « Quorum non
atteint » seul se lirait comme un seuil réglementaire ; la phrase publiée porte
la participation (deux nombres) et le seuil retenu.

### Deux des six ne sont pas des positions

- **`absents` s'affiche « Sans trace de vote », jamais « Absents ».** Le
  pipeline compte là les membres éligibles pour lesquels **aucun vote n'a été
  trouvé** sur ce scrutin (`group_profile.py` : « implicite = pas de vote trouvé
  pour ce scrutin »). C'est une absence de **donnée**, pas une absence
  constatée : la nommer « absents » publierait le taux de présence individuel
  qu'interdit §2 règle 3, agrégé mais fabriqué quand même. Elle ne porte donc
  aucune teinte, comme `non_votant` depuis #326.
- **`excuses` n'est pas publié**, parce qu'il vaut **0 sur les 19 832 entrées**
  publiées : aucune position collectée ne vaut `excuse`, exactement comme
  `absent` dans les 1 312 951 positions individuelles (#326). Afficher « 0
  excusés » affirmerait « personne n'était excusé » là où la source ne renseigne
  rien (§2 règle 5). La décision est prise **à l'échelle de la fiche**
  (`excusesRenseignees`), jamais de l'entrée : une entrée à 0 ne distingue pas
  les deux cas, un 0 partout sur 3 973 scrutins si. Le jour où la source
  renseigne la valeur, le sixième décompte réapparaît sans qu'on y touche.

La fiche affiche donc aujourd'hui **cinq** des six décomptes, et **écrit
pourquoi** le sixième manque. C'est un écart assumé à la formulation de #329.

## 2. Aucun compteur ne dit « aujourd'hui »

#653 a daté les compteurs côté données ; l'interface ne les lisait qu'à moitié.

| Avant | Après |
| --- | --- |
| KPI « **Effectif actuel** » affichant `meta.couverture_roster.roster_total` (76 sur `AN:LFI`) | « Membres du groupe au 09/06/2024 », `effectif.a_la_date_de_reference` **sur** `len(membres)` — 75 sur 76 |
| Aucune mention de `date_reference` hors des cartes de mandats | Une phrase publiée sous le bandeau, avec l'origine (`cloture_legislature` → « clôture de la législature ») |
| KPI « Taux d'adoption (député⋅es) » : `3 %` | « 3 924 sur 131 202 amendements distincts déposés » (§2 règle 7) |

Le premier disait faux **deux fois** : ce n'était ni l'effectif (c'était le
roster, membres sans profil compris) ni « actuel » (la XVIe est close).

**Les deux formes de chaque nom sont lues**, et c'est la moitié la plus
importante de la décision. Les 2 fiches Sénat sont gelées, ne seront pas
régénérées, et gardent `effectif.actuel`, `mandats_agreges[].nb_membres_actifs`,
`nb_membres` et `membres[].actif`. En ne lisant que les noms longs,
`GroupProfile.jsx` rendait sur leurs **17 cartes de mandats** :

```
Aucun membre n'y siégeait            ← sur une donnée absente, pas sur un zéro
undefined membre y a siégé au moins une fois
```

Un `undefined` en production, et un zéro fabriqué sur une donnée manquante
(§2 règle 5). Le repli lit l'ancien nom **et déclare que le compte n'est
rapporté à aucune date** — la fiche ne s'invente pas de date de référence.

Même règle sur `membres[].present_a_la_date_de_reference` / `actif`, et
`null` y reste distinct de `false` : « appartenance non renseignée » n'est pas
« parti avant ».

Corrigé au passage : les 2 fiches Sénat n'ont pas de `legislature`, et le
bandeau affichait **« Sénat · Législature null »**.

## 3. Commissions : « y siège » ≠ « y est passé »

#656 avait séparé les deux quantités et l'interface les affichait déjà ; ce lot
les fait passer par `siegeEtPasse`, qui lit les deux jeux de noms, et par le
même vocabulaire numérateur/dénominateur que le reste de la page. Le tri traite
désormais une donnée **absente** comme absente (`-1`) et non comme un zéro, ce
qui la range en fin de catégorie au lieu de la mêler aux mandats réellement
vides.

## 4. Les listes coupées déclarent leur règle, avec leur dénominateur

`slice(0, 12)` et `slice(0, 20)` étaient dans l'adaptateur, sans dénominateur :
le lecteur croyait voir une sélection, il voyait une coupe. Les fiches publient
de **3 832 à 4 099** scrutins de cohésion et de **1 554 à 4 303** étiquettes.

La règle affichée est **vérifiée, pas supposée** : `cohesion_votes` est trié par
**date de scrutin décroissante** sur les 5 fiches AN, contrôlé entrée par entrée
après jointure sur `pivot_data/scrutins.json`. « Les 12 plus récents, par date
de scrutin » est donc un fait ; « les 12 plus importants » aurait été un
jugement (§2 règle 1).

## 5. `meta` se lit, et rien ne le lisait

`meta.couverture_roster.etat` et `preuve` sont publiés sur **7 / 7** fiches et
aucun composant n'en ouvrait un seul. Un ratio seul ne dit pas de quoi il est le
ratio : `groupe-Senat-LR` publie **15 profils sur 235** — 6,4 % — et, lu sans son
état, ce chiffre se lit comme une **perte**. C'est un **périmètre** : le Sénat
est hors du périmètre éditorial depuis #528, et la `preuve` le dit en toutes
lettres, avec ses références de runs et sa condition de reprise.

Une section « Vérification » porte donc, en bas de fiche : la couverture du
roster avec son état et sa preuve **verbatim**, le seuil de quorum retenu, les
avertissements que le pipeline a écrits dans le fichier, la date de génération,
et ce que la fiche refuse de publier.

`hors_perimetre` est traduit en `non_collecte` et **non** en `hors_couverture` :
ce vide vient de **notre** décision de ne plus interroger la source, pas d'une
période que la source ne publierait pas. Les quatre causes du lot 1 n'affirment
pas la même chose, et les confondre publierait un zéro là où rien n'a été
collecté. La `preuve` verbatim n'est publiée **qu'une fois**, sous
« Vérification » : elle fait un paragraphe, et la répéter sous chacune des trois
listes vides d'une fiche Sénat noierait la page — les listes vides portent une
phrase courte qui renvoie à elle.

## 6. Les écarts individu / groupe restent internes, et la fiche l'écrit

L'écart entre un vote individuel et la ligne du groupe est une donnée de
**contrôle interne** (`--rapport-interne`), volontairement absente du schéma de
groupe. La publier désignerait qui s'est écarté de la ligne : un classement à
l'intérieur du groupe (§2 règles 1 et 7).

Une page qui se contente de ne pas répondre laisse croire qu'elle n'y a pas
pensé. `REFUS_FICHE_GROUPE` est donc du **contenu publié**, sur le patron des
`STATED_REFUSALS` du lot 1 : la fiche déclare qu'elle ne nomme jamais qui s'est
écarté de la position majoritaire, et que « Sans trace de vote » n'est pas un
taux d'absence.

## 7. L'empreinte thématique : jamais une étiquette sans son porteur

**Cette vue était classée hors lot par #329, en case D, sur le motif de
« 0 / 468 membres de roster portant une intervention ou un tag ». Ce constat est
périmé depuis #657.** Re-mesuré au commit `c6edee05` :

| Mesure | Valeur |
| --- | ---: |
| Profils `roster_groupe` portant au moins une `tags_thematiques` | **448 / 468** |
| … portant au moins une `interventions[]` | **448 / 468** |
| `tags_thematiques_agreges` publiés, `AN:SOC` → `AN:REN` | **1 554 → 4 303** |
| `nb_membres_porteurs` maximal (`AN:REN`) | **99** |
| Étiquettes portées par **au moins 2** membres, `AN:SOC` → `AN:REN` | **558 → 2 356** |
| Les 2 fiches Sénat | **0**, conservées et jamais régénérées (#528) |

Ce ne sont plus les étiquettes d'une seule personne, et la vue passe en case A
sur décision de la propriétaire, le 31/08/2026.

**Une étiquette ne se publie jamais seule.** `nb_membres_porteurs` est le
garde-fou de §2 règle 7 : une étiquette portée par 1 membre sur 76 ne dit pas ce
que dit une étiquette portée par 60, et l'afficher nue donnerait l'empreinte
d'**une personne** pour celle d'un groupe — le défaut exact que #657 a corrigé
côté données. Le dénominateur est **`len(membres)`**, la population que
l'agrégation a réellement lue (76, 62, 193, 90, 31 sur les 5 fiches AN,
retrouvés à partir de `poids_relatif`), jamais `roster_total`, qui compte des
membres dont aucun profil n'est publié. `poids_relatif` n'est pas publié : la
fiche donne ses deux nombres, comme `mandats_agreges` depuis #656.

**Ce ne sont pas des positions (§2 règle 8).** Ces étiquettes viennent de
`interventions[].theme_officiel` — l'intitulé que le compte rendu de l'Assemblée
donne au débat —, avec repli sur `mots_cles`. Elles disent sur quoi les membres
sont **intervenus**, et intervenir sur un texte, c'est aussi bien le combattre
que le défendre. La phrase publiée le dit, plutôt que de laisser la liste se
lire comme un programme.

**Une empreinte vide dit pourquoi.** Les 2 fiches Sénat sont à 0 étiquette parce
qu'elles sont conservées et jamais régénérées, et c'est `ListeVide` qui le dit —
jamais un `0`, jamais un blanc.

## Comment ces choix sont verrouillés

Le dépôt n'a **pas de runner JS** (`oxlint` seul). Comme #326, #529 et #530,
les arbitrages sont verrouillés par un test Python qui lit le **code exécuté**,
commentaires retirés : `tests/test_profil_de_groupe_329.py`, 22 cas. Un
commentaire qui parle de « barre de cohérence » ne doit ni faire passer ni faire
échouer le test qui vérifie qu'elle a disparu. Ajouter un runner JS reste nommé
et hors lot, comme dans #326.

## L'alternative écartée : ajouter ces règles à `utils/lecture.js`

`utils/lecture.js` porte les six règles **communes aux trois types de profil**.
Y verser la date de référence, la partition en six décomptes et le siège-vs-passé
aurait mis des règles de groupe sur le chemin des fiches de candidat et de
gouvernement, qui n'ont ni l'une ni les autres. Un second module, qui **importe**
le premier, garde la frontière lisible : ce qui est commun est commun, ce qui est
propre au groupe est nommé comme tel.

## Ce qui reste ouvert, nommé plutôt que corrigé en passant

- **Une fiche de groupe ne porte pas `meta.avertissements[]`**, le jumeau typé
  de `warnings[]` introduit par #642 sur les profils pivot. Faute du champ
  `destinataire`, l'interface ne peut pas distinguer un avertissement écrit pour
  le lecteur d'un avertissement écrit pour la trace : celui des fiches Sénat cite
  `_member_matches_legislature/senat_periode_debut (group_roster.py)`. Ils sont
  donc publiés **verbatim**, sous « Vérification », précédés d'une phrase qui dit
  à qui ils s'adressent d'abord.
- **`mandats_agreges` n'est pas tronqué** : 535 à 1 153 cartes sont rendues d'un
  coup. Ce n'est pas une question éditoriale mais une question de volume, et
  aucune règle de coupe défendable ne se déduit des données lues ici.
- **La 6ᵉ vue de #329 — « N lois sous quorum, position majoritaire,
  couverture » — n'est pas dans ce lot** : elle repose sur la sélection des votes
  « sur l'ensemble d'un texte », qui appartient à #672.
