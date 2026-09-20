# La liste des candidats pilote le périmètre du run, elle ne le documente plus (#757)

`2026-09-07`

> **En bref** — #753 livrait la liste mais pas la **boucle** : une entrée neuve entrait avec `slug: null`, donc sans shard, donc jamais collectée, et le périmètre n'avançait que lorsqu'une main mintait le slug **et** écrivait l'entrée de correspondance qu'exige la §5b ; d'ici avril 2027 la liste bougera des dizaines de fois, et un périmètre suspendu à une corvée est un périmètre en retard (51 jours, 19 déclarés absents au lot précédent) ; la boucle se referme **dans le run** — job `rafraichir-candidats` sans `needs:` → artifact `candidats-a-jour` → matrice → correspondance écrite **hors ligne** avant le portail → commit de la liste **avec** les données —, forme déjà donnée deux fois au même problème par #518 (construction unique publiée en artifact) et #715 (correspondance écrite dans le run, parce que le remède manuel était inerte) ; **l'acteur AN se résout par un identifiant et jamais par un nom** : la correspondance par nom rapprocherait un candidat n'ayant jamais siégé d'un ancien député homonyme et publierait sur sa fiche les votes de quelqu'un d'autre (§2 règle 2), d'où la chaîne `article → wikibase_item → P4123 → PA…`, **validée 13/13** contre les entrées relues, positifs **et** négatifs (les 9 acteurs connus, les 4 `hors_an`), plus 3 recoupements sur Ruffin/Brun/Faure ; couverture des 19 entrées neuves : **8** avec acteur, **8** en fait négatif, **3** sans article qui restent **sans slug et nommées** — la file d'attente devient visible, ce que #539 reprochait à `slug: null` d'être muette ; trois issues distinguées (`ACTEUR`/`HORS_AN`/`INDETERMINE`) parce que « Wikidata ne dit rien de cette personne » et « Wikidata la décrit et ne lui connaît aucun mandat » ne sont pas la même affirmation, et **aucune panne ne rend `HORS_AN` par défaut** (le patron de #511 appliqué à une affirmation) ; l'entrée n'est écrite que si **deux sources s'accordent** — l'identifiant externe et le profil produit depuis AMO30 — et le fait négatif exige que les **deux se taisent**, un désaccord n'écrivant rien, nommant le slug et laissant la §5b bloquer ; troisième valeur d'`origine`, **`sourcee`**, parce que `derivee` signifie « n'établit rien » quand le slug sort de l'acteur, ce qui n'est pas le cas d'un `slugify(nom)` ; le réseau vit dans le job de tête **et nulle part ailleurs** (#524), et ce job **ne pousse rien** — `GENERATION_CODE_CHANGED_DURING_RUN` annulerait le commit —, son repli sur code 1 gardant la liste **committée** plutôt qu'une liste vide ; **prix assumé** : un déclaré entre dans le périmètre sans qu'un humain l'ait regardé, la garantie passant de « relue » à « sourcée et corroborée », arbitré sur l'asymétrie des modes d'échec — publier un candidat de trop se corrige en une ligne, ne pas publier un déclaré pendant six semaines est le défaut mesuré ; **coût CI** 13 → **29 shards** en série, +12 min de chemin critique dans le régime observé. 49 tests neufs, suite complète à 3 960, 0 échec.

## Contexte

#753 a livré la liste à jour, et pas la **boucle**. Une entrée neuve entrait
avec `slug: null` ; sans slug, `prepare-an-matrix` ne construit pas de shard,
donc rien n'est collecté. Le périmètre n'avançait donc que lorsqu'une main
mintait le slug **et** écrivait l'entrée de correspondance qu'exige la §5b du
portail (hard fail à seuil 0, #525).

L'outil détectait, il ne pilotait pas. D'ici avril 2027 la liste bougera des
dizaines de fois — déclarations, retraits, primaires qui tranchent — et un
périmètre suspendu à une corvée manuelle est un périmètre en retard : le défaut
mesuré au lot précédent valait **51 jours** et **19 déclarés absents**.

## Décision

Une boucle fermée : **liste → slug → correspondance → collecte**, qui se referme
**dans le run**.

| Étage | Avant | Après |
| --- | --- | --- |
| Liste | fichier committé, rafraîchi à la main | job `rafraichir-candidats`, sans `needs:`, artifact `candidats-a-jour` |
| Périmètre | `prepare-an-matrix` lit le fichier committé | il lit l'**artifact** : le run collecte la liste du jour |
| Slug | `null`, en attente d'une main | `text_utils.slugify(nom)` quand un identifiant externe le corrobore |
| Correspondance | écrite à la main, sinon §5b bloque | écrite **hors ligne** dans `merge-and-pivot`, `origine: "sourcee"` |
| Commit | — | `merge-and-pivot` commite `candidats.json` **avec** les données |

La forme est celle que le dépôt a déjà donnée deux fois au même problème :
[un roster par run](roster-unique-par-run-518.md) pour la construction unique
publiée en artifact, et [l'entrée dérivée](entree-derivee-correspondance-715.md)
pour la correspondance écrite dans le run — parce que le remède manuel y était
**inerte**.

## L'acteur AN se résout par un identifiant, jamais par un nom

`candidate_profile._resolve_acteur_ref_par_slug` sait déjà retomber sur une
correspondance **par nom** : elle normalise le slug et cherche l'acteur AMO30 qui
porte ce nom complet. Elle refuse l'homonymie *interne* à AMO30 — deux acteurs
pour une clé, elle renonce — mais elle ne peut rien contre l'homonymie qui compte
ici : **un candidat qui n'a jamais siégé et qui porte le nom d'un ancien
député**. Elle rapprocherait les deux, et la fiche du candidat publierait les
votes, les amendements et les interventions de quelqu'un d'autre. C'est la pire
erreur que ce produit puisse commettre (§2 règle 2).

La chaîne retenue part donc d'un identifiant, et son premier maillon était déjà
écrit par #753 — l'URL de l'article de la personne :

```
source (article Wikipédia) → pageprops.wikibase_item → P4123 → "PA" + valeur
```

**Validée 13/13 contre les entrées relues à la main**, positifs *et* négatifs :
les 9 candidats déclarés qui ont un acteur (Mélenchon `PA2150`, Guedj `PA1567`,
Royal `PA2650`, Philippe `PA345619`, Attal `PA722190`, Bertrand `PA267080`,
Retailleau `PA2538`, Wauquiez `PA267285`, Le Pen `PA720614`) et les 4 déclarés
`hors_an` (Arthaud, Tondelier, Lisnard, Bardella), pour qui Wikidata ne porte pas
non plus la propriété. Plus 3 recoupements sur les candidats déjà collectés par
la voie du roster : Ruffin `PA722142`, Brun `PA793624`, Faure `PA609332`.

Couverture sur les 19 entrées neuves, mesurée le 07/09/2026 :

| Cas | Nombre | Ce qui se passe |
| --- | --- | --- |
| `P4123` présent | **8** | slug fabriqué, acteur AN connu — Cazeneuve `PA785`, Batho `PA335999`, Dupont-Aignan `PA1206`, Faure `PA609332`, Roussel `PA720692`, Ruffin `PA722142`, Maurel `PA842271`, Brun `PA793624` |
| Article présent, `P4123` absent | **8** | slug fabriqué, fait négatif à corroborer — Asselineau, Philippot, Glucksmann, Lalanne, Kazib, Bouamrane, Massard, Durif |
| Aucun article | **3** | **aucun slug**, et l'entrée est nommée — Labib, Mathieu, Verdier |

Les 3 derniers restent hors périmètre par construction : sans élément Wikidata,
rien ne corroborera leur acteur hors ligne, et leur fabriquer un slug les ferait
collecter puis publier — la §5b bloquerait alors le run entier sur une entrée que
la passe hors ligne ne peut pas écrire.

## Trois issues, et « indéterminé » n'est pas « hors AN »

`identifiants_wikidata` distingue **`ACTEUR`**, **`HORS_AN`** (l'élément existe et
ne porte pas la propriété) et **`INDETERMINE`** (pas d'article, pas d'élément).
« Wikidata ne dit rien de cette personne » et « Wikidata décrit cette personne et
ne lui connaît aucun mandat AN » sont deux affirmations différentes, et une seule
est un fait (§2 règle 5).

Toute défaillance — réseau, HTTP, JSON illisible, erreur d'API — lève
`ResolutionIndisponible`. **Aucun chemin ne rend `HORS_AN` par défaut** : un
timeout qui se lirait « cette personne n'a jamais siégé » écrirait une entrée
`hors_an` fausse dans un artefact relu, et la publierait. C'est le patron de
#511, appliqué à une affirmation au lieu d'une liste.

## L'entrée n'est écrite que si deux sources s'accordent

`--completer-candidats` reprend les trois filtres de #715 §5 — la table passe
devant, le profil doit être publié, le recoupement doit tomber juste — et change
**ce que le recoupement compare** : là-bas le roster déclarait l'acteur d'où le
slug avait été fabriqué ; ici un identifiant externe déclare l'acteur, et le
profil publié, dont l'identité vient d'AMO30 par un tout autre chemin, doit dire
la même chose.

Le fait négatif obéit à la même exigence, en miroir : `ecart: "hors_an"` n'est
écrit que si **Wikidata ne connaît aucun mandat AN** *et* que le profil produit
depuis AMO30 ne porte aucun acteur. C'est le raisonnement que #539 a écrit à la
main pour Arthaud, Tondelier et Lisnard, rendu reproductible.

**En désaccord, aucune entrée.** Le slug est nommé, la §5b bloquera en le
désignant, un humain arbitre. Deux sources qui divergent s'arbitrent, elles ne
se moyennent pas.

## Une troisième valeur d'`origine`

`relue` (#525) est un arbitrage humain ; `derivee` (#715) signifie « n'établit
rien », parce que le slug d'un membre de roster **sort** de son acteur. Le slug
d'un candidat sort de `slugify(nom)`, un nom saisi dans un fichier éditorial :
l'entrée établit bien quelque chose. D'où **`sourcee`** — un rapprochement porté
par un identifiant externe, avec sa `preuve` (l'URL de l'élément) et sa date.

Le validateur n'a pas eu à changer : il n'interdisait `ecart` qu'à `derivee`, et
pour la bonne raison — « un écart s'arbitre, il ne se dérive pas ». Un écart
**sourcé**, lui, est exactement ce qu'un fait négatif corroboré doit produire.

## Où vit le réseau, et pourquoi il ne vit pas ailleurs

Toute la résolution a lieu dans `rafraichir-candidats`, en tête de run, et son
résultat voyage dans l'artifact. La passe qui écrit les entrées reste **hors
ligne** : un téléchargement dans `merge-and-pivot` ferait qu'une panne de source
tierce coûte le commit d'un run dont la donnée est bonne, ce que
[le cloisonnement de la branche roster](cloisonnement-branche-roster-524.md)
interdit et ce que #715 a inscrit dans la forme de sa propre passe.

Le job de tête **ne pousse rien**, pour une raison mécanique :
`merge-and-pivot` annule le commit si `raw_data/*.json` a bougé sur la branche
*pendant* le run (`GENERATION_CODE_CHANGED_DURING_RUN`, #390/#413). Le fichier
voyage donc en artifact et il est committé à la fin, avec les données qu'il a
produites — et `raw_data/candidats.json` entre dans le `git add`, sans quoi les
slugs seraient refabriqués à chaque run, donc **jamais gelés** : la panne que
#715 a corrigée pour la table.

Il ne porte **pas** de `continue-on-error` — il rendrait vert un échec. Le repli
est explicite dans le shell : sur un code 1, le run garde la liste **committée**,
qui est un état connu, et le dit en `::warning::`. Jamais une liste vide.

## Le prix, assumé

**Un candidat déclaré entre dans le périmètre — collecté, publié, fiche en ligne
— sans qu'un humain l'ait regardé.** La garantie passe de « relue par une
personne » (#525) à « sourcée par un identifiant externe et corroborée contre
AMO30 ». Wikidata reste un wiki : une valeur fausse ou vandalisée entrerait dans
un commit de données que personne n'a ouvert, et le filet serait la corroboration
d'état civil et la §5b, pas un regard.

Arbitrage rendu le 07/09/2026, et la raison tient en une ligne : le mode d'échec
est **asymétrique**. Publier un candidat de trop se corrige en une ligne ; ne pas
publier un déclaré pendant six semaines est le défaut qu'on venait de mesurer.

**Coût CI** : 13 → **29 shards** `extract-an`, en série (`max-parallel: 1`), donc
au-delà du seuil d'avertissement de 16. Dans le régime observé (run
`34053322456` : 13 shards, 606 s cumulés, moyenne 46,6 s), +16 shards ≈ **+12 min**
de chemin critique ; plafond dur 16 × 5 min = +80 min. Le job de tête ajoute
~1 min, hors chemin critique puisqu'il démarre au premier étage.

## Ce que la décision ne fait pas

**Le retrait du périmètre.** Une candidature déclinée passe `statut: decline`
(#753), mais son profil publié reste en ligne : le dépublier est une décision
éditoriale distincte, et supprimer un fichier publié est une disparition
qu'`audit_diff_profils` bloque (#460/#470).

**La détection automatique du retrait.** La source porte pourtant deux sections
qui le nomment — « Candidatures retirées » (2 entrées) et « Candidats pressentis
ayant décliné » (24, dont Wauquiez et Bardella). Les lire est un lot à part, et
il pose sa propre question : le script doit-il **écrire** la transition de
statut, ou seulement la nommer ?

**Les 3 sans article Wikipédia.** Labib, Mathieu et Verdier restent sans slug et
sans collecte, nommés à chaque run par `CANDIDATS_SANS_SLUG`. C'est la file
d'attente humaine, et elle est **visible** — ce que #539 reprochait précisément à
l'état `slug: null` d'être : muet.

## Alternative écartée

**Étendre `--completer-derivees` aux candidats.** C'est le geste minimal, et il
serait faux : #715 §2 tranche que l'entrée dérivée n'établit rien *parce que* le
slug sort de l'acteur. Chez un candidat il sort d'un nom tapé à la main, donc
l'entrée établit un rapprochement — l'appeler « dérivée » lui ferait dire le
contraire de ce qu'elle fait.

**Proposer les entrées hors ligne et laisser une main les committer.** C'était la
recommandation initiale, et elle répondait à côté : un outil qu'il faut relancer
à la main ne tient pas un périmètre à jour, il le tient à jour aussi souvent que
quelqu'un y pense. C'est exactement le défaut que ce lot corrige.
