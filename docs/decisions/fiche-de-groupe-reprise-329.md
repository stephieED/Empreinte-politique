<a id="fiche-de-groupe-reprise-329"></a>
# La fiche de groupe reprise de bout en bout : l'ordre des questions, pas celui du schéma (#329) (2026-09-01)

`2026-09-01`

> **En bref** — la version livrée par #681 est **éditorialement irréprochable et structurellement inutilisable** : ses sections s'appellent « Cohésion de vote », « Empreinte thématique », « Amendements déposés », le vocabulaire du schéma et non les questions d'un électeur, et son fait le plus important — **sur 3 843 scrutins, la cohésion de `AN:SOC` n'est mesurable que sur 341** — était enterré en fin de section « Vérification » ; six sections dans l'ordre des questions (qui sont-ils · sur quoi ils travaillent · ce qu'ils proposent · comment ils votent · comment ils se situent · ce que la fiche ne dit pas), une seule focale à la fois, l'interne d'abord et la comparaison à la fin, le **quorum ouvrant la section des votes et non la page** ; les **absences ne franchissent plus l'écran sous aucun libellé** — « Sans trace de vote » était un libellé prudent sur une donnée interdite, et aucune largeur affichée ne se rapporte plus à `membres_eligibles` (§2 règle 3) ; les **fonctions exercées**, que rien n'affichait, sont réunies en quatre familles plus `autre`, **affiché avec ses intitulés d'origine** — 40 libellés distincts sur les 7 fiches, et la maquette en perdait un : 1 351 sièges simples publiés pour `AN:SOC` là où la fiche en porte **1 352**, un « représentant suppléant » rangé nulle part, tandis que `AN:REN` y révèle 9 intitulés ministériels ; sa prose se trompait aussi (« LFI en compte 3 » rapports contre 17 : avec la même règle des deux côtés, **9**), d'où le retrait de toute comparaison chiffrée entre groupes à cet endroit ; les convergences se publient en **trois natures** parce que « nuance » n'est pas « opposé » — SOC et RN ne sont opposés que **46** fois sur 231 mais en nuance **106**, là où un décompte brut afficherait « 152 divergences » —, ordonnées par nombre de scrutins comparables et jamais par accord, avec une quatrième nature `autres` mesurée à **0** et publiée pour que ce zéro reste vérifiable ; les **grandes lois** ne reconstruisent aucune clé de dossier (`texte_lie_id` nul sur **4 105 / 4 105** scrutins de la XVIe, `AGENTS.md` §4 l'interdit) mais regroupent les scrutins **dont l'intitulé officiel nomme le même texte**, ce que le compte publié dit mot pour mot, avec sa borne (51 intitulés n'en nomment aucun) — et la maquette annonçait un « top 8 » qui n'en était pas un, omettant trois textes mieux classés pour retenir le pouvoir d'achat à 67 ; un texte adopté sans vote n'y figure pas (le PLFSS rectificatif 2023, **172** scrutins, 3ᵉ de la législature, §2 règle 4) ; `position_politique` (#686) **n'est portée par aucune des 7 fiches** et le composant le déclare plutôt que de la simuler ou de la dériver d'un comportement de vote, `non_declaree` restant distincte d'un champ absent, et une fiche du Sénat disant qu'aucune source équivalente n'y est collectée ; la comparaison entre groupes passe par une **projection de build** (`scripts/comparaison-groupes.mjs`, **51 Ko contre 15,1 Mo** de fiches voisines, 2 415 positions au-dessus du quorum sur 19 832 entrées) — règle #628 appliquée au navigateur —, non bloquante : son absence se DIT, section par section ; réunie **par posture** et jamais alignée sur une échelle unique, sans aucun pourcentage (REN fait adopter **30 686** amendements, les quatre autres fiches **21 558** en en déposant **386 810** contre 142 143) ; vérifié par **rendu SSR réel** (`react-dom/server`, harnais hors dépôt) sur trois fiches et sur le chemin sans comparaison — ce qui ne couvre ni la mise en page, ni le responsive, ni le contraste, ni le clavier, le dépôt n'ayant aucun harnais de test JS.

Reprise du lot 3 de #324. La version livrée par #681 — dont les arbitrages sont
consignés dans [`profil-de-groupe-lecture-329.md`](profil-de-groupe-lecture-329.md) — est
**éditorialement irréprochable** : aucun taux interdit n'y est publié,
`taux_coherence` et `taux_participation` restent dans le fichier sans en sortir.
Elle est **structurellement inutilisable pour un électeur**. Ses sections
s'appellent « Cohésion de vote », « Empreinte thématique », « Amendements
déposés » : le vocabulaire du schéma, pas les questions de quelqu'un qui cherche
à comprendre un groupe.

Une fiche de groupe agrège les **468 profils `roster_groupe`**, qui n'ont pas de
page à eux. Aucun chiffre de ce document ne parle des 13 `candidat_declare`.

Toutes les mesures sont prises au commit `e40d0d32`, le 01/09/2026, sur les
**7 fiches publiées** : 5 pour l'Assemblée nationale (XVIe législature, 19 832
entrées de `cohesion_votes`) et 2 pour le Sénat, conservées et jamais régénérées
(#516/#528).

## 1. Le fait le plus important était enterré

**Sur 3 843 scrutins, la cohésion de `AN:SOC` n'est mesurable que sur 341.** Il
apparaissait en fin de section « Vérification ».

| Groupe | Scrutins agrégés | Quorum atteint | D'une seule voix | Groupe partagé |
| --- | ---: | ---: | ---: | ---: |
| SOC | 3 843 | **341** | 293 | 48 (dont 23 pour-et-contre) |
| LFI | 3 973 | **615** | — | — |
| REN | 4 099 | **523** | — | — |
| RN | 4 108 | **751** | — | — |
| LR | 3 832 | **185** | — | — |

En dessous du seuil (`meta.seuil_quorum`, 0,5 sur les 7 fiches), rien n'est
publié — pas même approché. Ce n'est pas une lacune de collecte : les 3 502
autres scrutins sont là, ils ne permettent simplement pas cette mesure
(AGENTS.md §2 règle 5).

**Il ouvre la section des votes, pas la page.** « Tout ce qui suit porte sur les
341 » est utile juste avant des chiffres de cohésion, et décourageant en
première page.

## 2. Six sections, dans l'ordre des questions

Une seule focale à la fois — l'interne d'abord, la comparaison à la fin :

| § | Section | La posture y est-elle structurante ? |
| ---: | --- | --- |
| 1 | Qui sont-ils | **non** — un effectif est un effectif |
| 2 | Sur quoi ils choisissent de travailler | **oui**, sur les fonctions exercées |
| 3 | Ce qu'ils proposent, et ce qu'il en reste | **oui, décisif** |
| 4 | Comment ils votent | **oui, décisif** |
| 5 | Comment ils se situent | **oui** — la comparaison est réunie par posture (majorité : `AN:REN` ; opposition : les 4 autres) |
| 6 | Ce que cette fiche ne dit pas | — |

La posture apparaît **là où elle change le sens d'un chiffre, nulle part
ailleurs**. Répétée partout, elle devient un avertissement, et un avertissement
répété devient une excuse. Elle est **expliquée** en section 1, une fois, parce
que c'est là que le lecteur en a besoin pour lire la suite.

## 3. Les absences ne franchissent plus l'écran

La version précédente publiait les **six** décomptes d'une entrée de
`cohesion_votes`, sous des libellés prudents : `absents` s'affichait « Sans trace
de vote » et `excuses` était masqué quand il valait 0 partout.

**Un libellé prudent sur une donnée interdite reste la donnée interdite.** Ces
deux décomptes ne sortent plus du fichier, sous aucun nom : publiés, agrégés ou
non, ils constituent un taux de présence sur des personnes nommées (§2 règle 3).
`DECOMPTES_JAMAIS_PUBLIES` les déclare dans le code exécuté, et
`tests/test_profil_de_groupe_329.py` vérifie qu'ils ne traversent ni
l'adaptateur, ni la projection de comparaison, ni le composant.

Corollaire : **aucune largeur affichée ne se rapporte à `membres_eligibles`.**
La répartition d'un scrutin partagé se calcule sur les voix **exprimées**
(17 voix sur 31 membres éligibles s'écrit en toutes lettres à côté, comme
dénominateur nommé, jamais comme diviseur d'un pourcentage).

## 4. Aucun intitulé de fonction n'est perdu — la maquette en perdait un

Les **fonctions exercées** n'étaient affichées nulle part. C'est pourtant là que
la posture d'un groupe se voit le plus concrètement : *un rapport se confie, il
ne se prend pas*.

`mandats_agreges[].par_fonction` porte **40 libellés distincts** sur les 7
fiches, de `membre` (18 629 occurrences) à `ministre des outre-mer` (1). Les
réunir en quatre familles est un acte de lecture, donc il se déclare — et il ne
perd rien : ce que la table ne reconnaît pas tombe dans **« Autres fonctions »,
qui est AFFICHÉ avec ses intitulés d'origine**.

| `AN:SOC` | Maquette | Mesuré ici |
| --- | ---: | ---: |
| Présidences | 13 | 13 |
| Rapports | 17 | 17 |
| Secrétariats et vice-présidences | 16 | 16 |
| Sièges simples | **1 351** | **1 352** |

L'écart est un `représentant suppléant` que la maquette ne rangeait nulle part.
**Un libellé perdu ne se voit pas** : la somme des quatre familles vaut 1 398,
soit exactement la somme des `par_fonction` des 615 mandats agrégés du groupe.

Le bénéfice se voit sur `AN:REN`, où « Autres fonctions » publie **9 intitulés**
— six titres ministériels, un secrétariat d'État, deux chargés de mission —
qu'un rangement d'office aurait fait passer pour des sièges simples.

**La maquette se trompait aussi dans sa prose** : elle opposait « La France
insoumise, avec 75 membres, en compte 3 » aux 17 rapports de `AN:SOC`. Avec la
même règle des deux côtés, `AN:LFI` en compte **9** (3 `rapporteur` + 6
`co-rapporteur`) : le 3 ne comptait que l'un des deux libellés. Le constat
éditorial tient — 9 rapports pour 75 membres contre 17 pour 31 —, le chiffre non.
La page n'énonce donc plus de comparaison chiffrée entre deux groupes ici : elle
dit que **ces nombres ne se comparent pas en taux**, et s'en tient là.

## 5. « Nuance » n'est pas « opposé »

Position majoritaire du groupe comparée à celle de chaque autre, scrutin par
scrutin, et **uniquement là où les deux atteignent leur quorum** — les
dénominateurs diffèrent donc d'une ligne à l'autre, et chacun est publié.
L'ordre est celui du nombre de scrutins comparables, **jamais celui de
l'accord** : trier par accord ferait un classement des alliés (§2 règle 1).

| Depuis `AN:SOC` | Communs | Même sens | Sens opposé | Nuance |
| --- | ---: | ---: | ---: | ---: |
| LFI | 269 | 230 | 12 | 27 |
| REN | 237 | 36 | 177 | 24 |
| RN | 231 | 79 | **46** | **106** |
| LR | 123 | 22 | 81 | 20 |

**La décomposition renverse la lecture** : SOC et RN ne sont opposés que 46 fois,
mais en nuance 106 — une abstention face à une position exprimée n'est pas un
vote contraire. Un décompte brut aurait affiché « 152 divergences ».

Une quatrième nature, `autres`, compte les couples que les trois ne décrivent
pas. Elle vaut **0** sur les quatre paires, et elle existe pour que ce zéro
reste vérifiable plutôt que supposé : `position_majoritaire` pourrait valoir
`non_votant` un jour, et le ranger d'office en « nuance » affirmerait une
intention.

## 6. Les grandes lois : ce que la source ne porte pas, et ce qu'on publie à la place

Regrouper les scrutins par LOI demanderait une clé de dossier. **Elle n'existe
pas** : `texte_lie_id` est `null` sur **4 105 des 4 105** scrutins de la XVIe, et
`pivot_data/scrutins.json` ne porte pas de `dossier_id`. `AGENTS.md` §4 est
explicite — un `dossier_id` ne se reconstruit **jamais** depuis un titre.

Nous ne la reconstruisons donc pas, et la page ne prétend pas l'avoir. Elle
regroupe les scrutins **dont l'intitulé officiel nomme le même texte**, et c'est
exactement ce que le compte publié dit : *« N scrutins dont l'intitulé nomme ce
texte »*. Le lecteur peut le vérifier — les intitulés sont publics, l'un d'eux
est affiché, et chaque lecture porte son lien de source. La borne est publiée
avec la vue : **51 des 4 105** intitulés ne nomment aucun texte.

Les lectures sont les **votes sur l'ensemble du texte** au sens de
`selectWholeTextVotes` (#672) : la règle est sourcée pour moitié (`type_vote`) et
approchée pour moitié (l'intitulé), et le lot 1 publie déjà cette borne.

**La maquette annonçait un « top 8 par nombre de scrutins » qui n'en était pas
un.** Remesuré, six de ses huit comptes se reproduisent (237, 203, 164, 160, 125,
124) mais sa sélection ne tient pas : elle omettait trois textes mieux classés et
retenait le pouvoir d'achat, à **67**. La vue publie donc la vraie tête de liste.

| Texte | Scrutins le nommant | Lectures sur l'ensemble |
| --- | ---: | ---: |
| Souveraineté alimentaire et agricole | 237 | 1 |
| Programmation du ministère de la justice 2023-2027 | 203 | 2 |
| Finances rectificative pour 2022 | 164 | 4 |
| Accélération de la production d'énergies renouvelables | 160 | 2 |
| Programmation militaire 2024-2030 | 160 | 2 |
| Industrie verte | 142 | 2 |
| Plein emploi | 125 | 2 |
| Sécuriser et réguler l'espace numérique | 124 | 2 |

**Un texte peut manquer parce qu'il n'a jamais été voté.** Le projet de loi de
financement rectificative de la sécurité sociale pour 2023 réunit **172**
scrutins — le troisième de la législature — et n'apparaît pas : adopté sans vote,
il n'a aucune lecture sur son ensemble. C'est §2 règle 4 qui l'exclut, pas une
lacune, et la page l'écrit.

Le mouvement d'une lecture à l'autre est ce que la vue existe pour montrer. Sur
les quatre lectures du PLFR 2022, `AN:SOC` passe de **contre** à **abstention** et
`AN:LR` de **pour** à **abstention** ; deux cases restent vides, où le quorum du
groupe n'était pas atteint. **Un tiret n'est pas une abstention**, et la page le
dit.

Deux retraits, et deux seulement, sont opérés sur le titre affiché : l'ouverture
« l'ensemble du… », qui dit la place du vote et non le nom du texte, et la
mention de lecture — une carte qui annonce « 4 lectures » ne peut pas s'intituler
« (première lecture) ». Ils sont déclarés dans la page, l'intitulé complet reste
en infobulle, et chaque lecture porte son lien vers le scrutin.

## 7. La posture : recopiée, jamais déduite, et arrivée en cours de lot

`position_politique` (#686) a été ajoutée au schéma de groupe pendant l'écriture
de ce lot. **Le composant a d'abord été écrit et mesuré sans elle** — aucune des
7 fiches ne la portait — puis le commit de données `693b076d` (01/09/2026) l'a
fait atterrir. Remesuré sur les fiches publiées :

| Fiche | Posture | Source |
| --- | --- | --- |
| `AN:REN` | `majorite` | AMO30, `verifie_le: 2026-09-01`, organe `PO800538` / sigle AN `RE` |
| `AN:LFI`, `AN:LR`, `AN:RN`, `AN:SOC` | `opposition` | idem ; `AN:SOC` réunit ses deux organes successifs (`SOC`, `SOC-A`) |
| `groupe-Senat-LR`, `groupe-Senat-SER` | **absente** | fiches gelées depuis #516, jamais régénérées |

**Le composant n'a pas eu à changer, et c'est le contrôle qui vaut quelque
chose** : il lisait déjà le champ au lieu de coder son absence en dur. La
section 5, qui réunissait les cinq groupes sous « posture non publiée », les
sépare désormais en deux blocs réels — `majorite` : `AN:REN` seul ;
`opposition` : `AN:SOC`, `AN:RN`, `AN:LFI`, `AN:LR`. `minoritaire` reste une
posture que le vocabulaire connaît et qu'aucune fiche de cette législature ne
porte : elle est **nommée**, pas tue (§2 règle 5).

Ce que le cas « absente » garde de nécessaire : il n'est plus l'état par défaut,
mais il ne disparaît pas. Les 2 fiches du Sénat ne seront pas régénérées, et sur
elles la carte dit autre chose encore (voir plus bas). `postureDuGroupe` y rend
`declaree: false`, et la page l'écrit. Elle n'est **jamais** dérivée d'un
comportement de vote (§2 règle 1) — un test le vérifie sur le corps de la
fonction.

**La leçon, et elle est générale** : un constat chiffré écrit dans un
commentaire vieillit plus vite que le code qu'il décrit. Ici trois commentaires,
une docstring de test et un message d'assertion affirmaient « absente des 7
fiches » alors que le code, lui, était déjà correct. Ils ont été corrigés le
jour même — mais rien ne les surveillait.

`non_declaree` reste distincte d'un champ absent : « l'Assemblée ne l'a pas
déclaré » n'est pas « notre fiche ne porte pas le champ ».

Sur une fiche du Sénat, la carte dit autre chose encore : la qualification est
celle que l'**Assemblée nationale** donne à ses propres groupes, et **aucune
source équivalente n'est collectée pour cette chambre**.

## 8. Comparer sans télécharger : la projection

Les sections 4 et 5 comparent le groupe à ceux de la même législature. Les 5
fiches AN de la XVIe pèsent **15,1 Mo** ; ce dont ces sections ont besoin en pèse
**51 Ko**.

`web/UI_finale/scripts/comparaison-groupes.mjs` en écrit la projection au build,
une par (chambre, législature) : sigle, effectif, amendements agrégés, position
politique déclarée, et les positions majoritaires des **seuls** scrutins où le
quorum est atteint — **2 415** entrées sur les 19 832 publiées. En dessous du
quorum rien n'est publié, donc rien n'est transporté.

C'est la règle #628 appliquée au navigateur : on lit par projection, on ne garde
pas le document. Le fichier produit est un **artefact de build** (`public/data/`
est ignoré par git) ; il ne rejoint jamais `pivot_data/`, et aucun contrôle de
perte ne le surveille.

Le chargement est mémoïsé et non bloquant. Un échec rend `null`, et les trois
sections concernées **disent** que la comparaison manque plutôt que d'afficher
des tableaux vides, qui se liraient comme des zéros mesurés (§2 règle 5).

## 9. Ce qui reste refusé, et l'est par écrit

| Refus | Pourquoi |
| --- | --- |
| Un indice de cohésion | Un chiffre unique par groupe est une note, cinq notes un classement (§2 règle 1) |
| Les écarts d'un membre vis-à-vis de sa majorité de groupe | Les désigner produirait un classement à l'intérieur du groupe (§2 règles 1 et 7) |
| Les absences | Un taux de présence sur des personnes nommées (§2 règle 3) |
| Un taux d'adoption commun aux types de déposant | Deux actes différents (`AGENTS.md` §5) |
| Un pourcentage dans la comparaison entre groupes | Il mesurerait surtout la posture de chacun |
| Les thèmes | Aucune source ne classe les textes par sujet ; les construire est un acte éditorial différé |

**§2 règle 7 a été amendée le 01/09 pour le profil candidat** (#328) :
juxtaposer, sur un scrutin sourcé, la position d'un membre et celle de son
groupe est un fait publiable. Sur une **fiche de groupe**, la question ne se pose
pas de la même façon et la réponse ne change pas : nommer qui s'est écarté
désignerait des dissidents, sans qu'aucun scrutin ne soit pour autant mieux
sourcé. Les scrutins partagés se publient en **décomptes** — combien de membres
ont pris chaque position, jamais lesquels. Le nombre de voix minoritaires sert de
critère de tri et **ne s'affiche pas** : un « nombre de dissidents » publié serait
le même indice individuel par un autre chemin.

## Alternative écartée

**Charger les fiches voisines plutôt qu'une projection.** Le précédent existe —
`getCandidateProfile` télécharge déjà les fiches de groupe d'un candidat. Écarté
pour un facteur **296** sur le volume (15,1 Mo contre 51 Ko), et parce que la
projection rend explicite ce que les sections lisent réellement : trois champs
et les positions au-dessus du quorum. Une fiche entière chargée rendrait invisible
qu'on n'en lit qu'un centième.

**Publier la comparaison alignée sur une échelle unique.** Écarté : un groupe
majoritaire et un groupe d'opposition ne font pas le même métier, et les mettre
en concurrence sur une tâche qu'ils ne partagent pas est le classement que §2
règle 1 refuse. Mesuré, l'écart qu'un tel alignement afficherait comme une
performance : `AN:REN` fait adopter **30 686** amendements, les quatre autres
fiches **21 558** à elles toutes, alors qu'elles en déposent **386 810** contre
142 143.

## Non vérifié, et nommé

Le rendu est contrôlé par **rendu SSR réel** (`react-dom/server`, harnais gardé
hors dépôt) sur `AN-SOC-16`, `AN-REN-16`, `Senat-LR` et sur le chemin sans
comparaison, en lisant le HTML produit. **Ce contrôle ne couvre pas** la mise en
page (aucune CSS n'est appliquée), le comportement responsive, le contraste réel,
ni le parcours au clavier. Le dépôt n'a aucun harnais de test JS : `package.json`
n'expose que `dev`, `build` et `lint`.
