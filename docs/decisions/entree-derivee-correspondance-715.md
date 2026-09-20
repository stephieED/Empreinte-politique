<a id="entree-derivee-correspondance-715"></a>
# Une entrée dérivée gèle un slug fabriqué, elle ne prouve plus rien (#715) (2026-09-02)

`2026-09-02`

> **En bref** — le premier run à profiter de la porte ouverte par #708 a collecté **160 profils neufs** et **n'a rien committé** : la §5b du portail exige une entrée de `raw_data/correspondance_acteurs_an.json` pour tout profil publié, et le remède qu'elle imprime est **inerte** — `build_correspondance_acteurs_an.py` part des profils **publiés**, que le commit bloqué empêche d'exister ; #708 a levé la circularité à la **collecte**, elle restait entière à la **table**, et le run n'est pas rejouable (`actions/checkout` fige le SHA au déclenchement d'un `workflow_dispatch`) ; la cause est que la table fait **deux métiers** dont un a disparu — pour les 481 slugs hérités de NosDéputés, l'acteur AN était à *découvrir*, et une découverte se prouve ; pour un slug **fabriqué depuis** l'acteur (`slugify(état civil AMO30)`), il n'y a rien à prouver, ce que deux mesures recoupent (**160 / 160** des slugs fabriqués sont collectés depuis `.../fiche/OMC_PA######` portant **exactement** leur `acteur_ref`, et **477 des 481** entrées committées portent cette même URL en `preuve`, **476** à la même date : produites en lot, seules les **10** entrées à écart ayant été arbitrées) ; ce que l'entrée apporte encore est **réel et unique** — le **gel** de l'identifiant, sans lequel un changement de nom d'usage déplacerait le slug au run suivant (#487, #668 ; 4 des 10 écarts de #525 en sont) — d'où une clé `origine` fermée (`relue` | `derivee`), **facultative en lecture** avec un défaut qui est un fait daté (la porte de fabrication n'existait pas avant), `ECARTS_CONNUS` ne pouvant pas la porter puisqu'une entrée dérivée n'a **aucun** écart — le validateur refuse les deux ensemble ; la passe `--completer-derivees` est **additive** (elle reconduit le document **brut**, pas la table normalisée, et ne réécrit pas le fichier quand il n'y a rien à ajouter), **hors ligne** (un second téléchargement AMO30 avant le commit ferait qu'une panne de source coûte un run valide, #524 ; l'état civil vient du pivot du run, lu par projection, #628) et **disjointe** de `construire()` ; trois filtres l'empêchent d'être un tampon — la table passe devant (#708 §3), le profil doit être **publié**, et son `identifiants.an` doit valoir **exactement** l'`acteur_ref` que le roster déclare, un désaccord n'écrivant rien et sortant en 1 (#540 sur le seul identifiant du dépôt) — l'autorité de « qui est fabriqué » étant `slug_origine` et jamais autre chose, ce qui laisse entier le refus de #525 §6 ; câblée dans `merge-and-pivot` **après** les pivots et **avant** le portail, avec la moitié qui manquait : `raw_data/correspondance_acteurs_an.json` entre dans le `git add` du workflow — il n'y était pas, et sans lui le gel serait une illusion, la panne que `AGENTS.md` §3a nomme déjà pour les index partagés ; la §5b publie désormais le nombre d'entrées `derivee`, qui est la **file d'attente de relecture** que #708 §8 nommait sans la rendre visible — un compteur, pas un seuil ; **la condition de retrait de #525 §7 est inchangée**, les 160 restent `derivee` jusqu'à relecture humaine (elle seule remplit `prenom`/`nom`, qu'AMO30 sépare et que la passe hors ligne laisse à `null`), et ce lot **ne relance pas** le run bloqué.

Suite immédiate de [[slug-fabrique-membre-de-roster-708]], dont la §8 laissait
ce geste en suspens. Le run `33613535746` du 02/09/2026 en a fait une urgence.

## 1. Le défaut : la porte s'ouvre à la collecte, elle reste fermée à la table

#708 a levé une circularité — pour avoir un profil il fallait un slug, pour
avoir un slug il fallait un profil — en fabriquant le slug d'un membre de
roster depuis l'état civil AMO30 de son acteur. Le premier run qui en a
profité a collecté **160 profils neufs**, et **rien n'a été committé** :

```
┌─ 5b/6  Correspondance slug ↔ acteur AN
│  Profils publiés : 641   (13 candidats déclarés · 628 membres de roster)
│  Entrées : 481   Sans acteur AN (déclaré) : 4   Sans entrée : 160
```

Aucun autre contrôle du portail n'a bloqué. Les 57 minutes de collecte, l'index
des amendements, les fiches de groupe et de gouvernement sont partis avec le
commit refusé.

**Le remède que le portail imprime est inerte.** Il dit « `python3
src/build_correspondance_acteurs_an.py` la propose » ; ce constructeur énumère
`_slugs_publies(pivot_data/profiles)`, c'est-à-dire les profils **publiés**. Les
160 ne le sont pas, et ne le seront jamais tant que le commit est bloqué. #708
a levé la circularité à la collecte ; elle est restée entière à la table.

**Et le run n'est pas rejouable.** `merge-and-pivot` fait `actions/checkout@v5`
sans `ref:` : sur `workflow_dispatch`, le SHA est figé au déclenchement — le
workflow l'écrit lui-même à son étape de commit. Un « re-run failed jobs »
relirait la même table à 481 entrées et échouerait à l'identique. Les artefacts
survivent, aucun checkout ne portera le correctif : le seul chemin est de faire
atterrir la correction sur `main`, puis de relancer.

## 2. La cause : la table fait deux métiers, et l'un a disparu

`raw_data/correspondance_acteurs_an.json` existe parce que les slugs de profil
du dépôt **venaient d'ailleurs**. Ce sont les slugs NosDéputés, hérités, et
AMO30 ne publie ni eux ni aucun identifiant externe : il fallait *découvrir*
quel `PA######` décrivait chacun. Une découverte se prouve, et #525 a eu raison
d'en faire un artefact relu plutôt qu'une heuristique.

Depuis #708, un membre neuf n'a pas ce problème : son slug est
`slugify(état civil AMO30)` **de son acteur**. Il n'y a pas de rapprochement à
établir — le slug est sorti de cet acteur-là et ne pouvait pas en désigner un
autre.

| Population | Ce que l'entrée de table établit |
| --- | --- |
| 481 slugs hérités de NosDéputés | un **rapprochement** entre un slug venu d'ailleurs et un acteur AMO30 |
| 160 slugs fabriqués par #708 | rien — le slug **dérive** de l'acteur |

Deux mesures tranchent, et elles se recoupent :

- sur l'artefact `roster-candidats` du run bloqué, **160 / 160** des slugs
  fabriqués sont collectés depuis `.../deputes/fiche/OMC_PA######` portant
  **exactement** l'`acteur_ref` que le roster leur attribue ;
- dans la table committée, **477 des 481** entrées portent comme `preuve` cette
  même URL de fiche, et **476** la même date de vérification (26/08/2026) :
  elles ont été produites en lot par le constructeur, pas relues une par une.
  Les seules réellement arbitrées sont les **10** entrées à écart de #525 §2.

Autrement dit, ce que la §5b réclamait pour ces 160, c'était une entrée dont le
constructeur aurait rempli les cinq champs mécaniquement, depuis un fichier
(`raw_data/rosters_bruts.json`) qui existait déjà dans le run.

## 3. Ce que l'entrée apporte quand même, et c'est réel

**Le gel de l'identifiant.** `an_roster.resoudre_slugs` fait passer la table
**devant** la fabrication : dès qu'un acteur y a une entrée, son slug en vient,
quoi que dise l'état civil du jour. Sans entrée, un changement de nom d'usage
déplacerait le slug fabriqué au run suivant — la même personne publiée sous deux
noms de fichier, ce qui est #487 et #668 réunis. #525 mesure que **4 des 10**
écarts sont des noms d'usage : ce n'est pas un risque théorique.

C'est donc ce service-là, et lui seul, que l'entrée rend à cette population. La
décision est de l'écrire tel quel plutôt que de prétendre à une preuve.

## 4. La décision

Une clé `origine`, fermée, dans le schéma de la table :

- **`relue`** — le régime de #525, celui de tout ce qui précède ;
- **`derivee`** — le slug a été fabriqué depuis l'acteur ; l'entrée enregistre
  une dérivation, pas une preuve.

`ECARTS_CONNUS` ne pouvait pas porter la distinction : une entrée dérivée n'a
**aucun** écart, et l'y ranger aurait fait dire à `ecart` deux choses. Le
validateur refuse d'ailleurs les deux ensemble — *un écart s'arbitre, il ne se
dérive pas*.

**La clé est facultative en lecture, et son défaut est un fait daté, pas une
commodité** : une entrée écrite avant ce lot ne peut venir que de la passe relue
de #525, puisque la porte de fabrication n'existait pas. Condition de retrait du
défaut : le jour où plus aucune entrée committée n'est dépourvue de la clé,
l'exiger devient gratuit. `SCHEMA_VERSION` ne bouge pas — aucune entrée existante
ne change de forme, et la bumper aurait obligé à réécrire 481 entrées relues dans
le commit qui ajoute une clé.

## 5. La passe qui les écrit : additive, hors ligne, et disjointe

`build_correspondance_acteurs_an.py --completer-derivees --rosters-bruts <f>`.
Trois propriétés, chacune contre un défaut nommé :

- **additive** — elle ne réécrit aucune entrée existante, et reconduit le
  document **brut** plutôt que la table normalisée : réécrire la forme
  normalisée ajouterait `acteur_ref` en doublon d'`identifiants.an` et `origine`
  sur les 481, c'est-à-dire réécrire du travail relu pour une passe qui n'a rien
  à y dire (#525 §6). Quand il n'y a rien à ajouter, **le fichier n'est pas
  touché** : `genere_le` bougerait à chaque run et le step de commit verrait un
  changement là où il n'y en a pas ;
- **hors ligne** — elle tourne dans `merge-and-pivot`, juste avant le portail.
  Un second téléchargement AMO30 à cet endroit ferait qu'une panne de source
  coûte le commit d'un run dont la donnée est bonne, ce que
  [[cloisonnement-branche-roster-524]] interdit. L'état civil vient donc du
  profil pivot que le run vient d'écrire, lu **par projection** (1,3 Mio en
  médiane, 14,6 Mio au pire : lu, réduit à cinq valeurs, relâché — #628) ;
- **disjointe** — elle sort de `main()` avant que quoi que ce soit ne touche au
  réseau ou aux entrées relues. Ce n'est pas une variante de `construire()`.

Trois filtres, et ce sont eux qui l'empêchent d'être un tampon :

| Filtre | Ce qu'il empêche |
| --- | --- |
| La table passe devant | qu'un changement de nom d'usage déplace l'identifiant d'une personne déjà collectée (#708 §3) |
| Le profil doit être **publié** | qu'on pose l'entrée de quelqu'un que le run n'a pas collecté — la §5b ne bloque que sur les publiés |
| L'`identifiants.an` du profil doit valoir **exactement** l'`acteur_ref` déclaré par le roster | qu'un profil décrive un acteur pendant que son slug en désigne un autre : le défaut de clé collante de #540, sur le seul identifiant du dépôt |

Un désaccord n'écrit rien, nomme le slug et sort en **1**. La §5b bloquerait de
toute façon trois steps plus bas ; échouer ici nomme la cause.

**L'autorité de « qui est fabriqué » est `slug_origine`, jamais autre chose.**
Un slug publié que le roster du run ne déclare pas fabriqué ne reçoit rien —
c'est ce qui laisse entier le refus de #525 §6 de combler une entrée relue
depuis `identite.source_url`.

## 6. Le câblage, dont la moitié qui manquait

L'étape est posée dans `merge-and-pivot` **après** l'écriture des pivots et
**avant** le portail : les deux conditions comptent. Écrire l'entrée dans le run
même qui crée le profil est aussi la seule façon de rendre le gel effectif —
la table passe devant la fabrication, donc elle doit exister *avant* la
publication, pas après.

**Et `raw_data/correspondance_acteurs_an.json` entre dans le `git add` du
workflow.** Il n'y était pas. Sans ça, l'entrée dérivée serait réécrite à chaque
run et le gel qu'elle est censée produire n'existerait pas : c'est exactement la
panne que `AGENTS.md` §3a nomme déjà pour les index partagés — *un index non
committé laisse chaque mapping pointer dans le vide, en silence*.

Le `if:` porte sur `hashFiles('raw_data/rosters_bruts.json')`, sur le **fichier**
et non sur le succès d'un step (#524) : sans roster il n'y a aucun slug fabriqué,
et la branche est sautée sans que rien n'échoue.

## 7. Le portail publie la file d'attente

La §5b affiche désormais, à côté du total, le nombre d'entrées `derivee`. Elles
couvrent le commit — le slug est gelé, ce qui est tout ce que la table doit à
cette population — mais **personne ne les a relues**. #708 §8 nommait cette file
d'attente sans la rendre visible, et une file qu'on ne voit pas ne se résorbe
pas. Ce n'est pas un seuil : c'est un compteur.

## 8. Ce que ce lot ne fait pas

- **La condition de retrait de la table est inchangée** (#525 §7 : elle
  disparaît le jour où la source publie elle-même la correspondance). Une entrée
  dérivée n'est pas une correspondance publiée par AMO30 — c'en est une que
  *nous* dérivons, faute que la source en publie une.
- **Le refus de #525 §6 est inchangé** : combler une entrée relue depuis
  `identite.source_url` reste interdit.
- **Les 160 restent `derivee`** jusqu'à ce que quelqu'un les relise. Le lot ne
  les convertit pas, et rien ne le fait automatiquement : passer à `relue` est
  un geste humain, qui remplit `prenom`/`nom` — les deux champs d'état civil
  qu'AMO30 sépare et que cette passe, hors ligne, laisse à `null`.
- **Il ne relance pas le run bloqué**, qui n'est pas rejouable (§1). Les 8
  artefacts `raw-profiles-roster-groupes-*` du run `33613535746` restent la
  seule copie des 160 profils bruts déjà collectés ; un nouveau run les
  recollecte.

## 9. L'alternative écartée

**Assouplir la §5b** — la faire tolérer un profil dont le slug est déclaré
fabriqué. Écartée : c'est le seul mécanisme qui force l'entrée à exister avant
la publication, donc le seul qui gèle l'identifiant. La tolérance aurait rendu
la table facultative pour toute la population qui grossit, et #525 §7 aurait
cessé d'être une condition de retrait pour devenir un vœu.

**Faire tourner le constructeur complet dans le workflow** — avec AMO30, donc
l'état civil complet. Écartée : un téléchargement de plus avant le commit, sur
une source dont l'indisponibilité a déjà bloqué trois chantiers, ferait qu'une
panne coûte le commit d'un run valide (#524). L'état civil partiel, déclaré, est
préférable à une entrée complète qu'une panne peut empêcher d'écrire.

**Relancer avec `add_uncovered_members=false`** — le run repasserait, sans les
160. Écartée comme solution, retenue comme constat : ça débloque le pipeline
sans rien régler, et la couverture des fiches de la XVIIᵉ resterait à 305/461.
