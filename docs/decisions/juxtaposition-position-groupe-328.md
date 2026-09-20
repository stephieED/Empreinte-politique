# Juxtaposer deux positions sourcées n'est pas mesurer un écart (#328) — 01/09/2026

`2026-09-01`

> **En bref** — §2 règle 7 interdisait « Individual-vs-group gaps », ce qui, lu à la lettre, interdisait d'afficher la position d'un membre à côté de celle de son groupe sur un scrutin donné ; or ce que la règle protège est nommé dans le code — `compute_ecarts_cohesion_internes` calcule des « écarts de cohésion/participation individuels **vs moyenne du groupe** », c'est-à-dire un **taux par personne rapporté à une moyenne**, dont `taux_participation` est exactement le taux d'assiduité que la règle 3 interdit déjà ; la règle distingue donc l'**indice** (jamais public, `--rapport-interne`) de la **juxtaposition d'un scrutin sourcé** (publique, jamais comptée ni notée), avec le garde-fou dans la règle même — « a voté contre son groupe 47 fois » est le même indice par un autre chemin — et le tableau §6 passe d'une ligne à deux ; aucune caractérisation n'est autorisée pour autant, ni « franc-tireur » ni « loyal », l'interprétation restant au lecteur ; le corps de #324 posait déjà cette frontière le 29/08 sans que §2 en tienne compte.

## Contexte

La trame du profil candidat publie, sur un scrutin donné, la position de la
personne **à côté** de la position majoritaire de son groupe. Deux faits sourcés,
côte à côte, sur un vote daté.

`AGENTS.md` §2 règle 7 disait : « Individual-vs-group gaps are **internal quality
control** only, never public », et le tableau §6 rangeait « Individual gaps vs
group cohesion » en interne. Lu à la lettre, cela interdisait la section.

## Ce que la règle interdit réellement

Le code le dit sans ambiguïté. `src/group_profile.py`, en tête :

> « Écarts de cohésion/participation individuels (`compute_ecarts_cohesion_internes`) :
> donnée de **CONTRÔLE INTERNE** uniquement, volontairement absente du schéma de
> groupe public — accessible via `--rapport-interne`, jamais via `--out`. »

Et l'aide de l'option : « **écarts de cohésion/participation individuels vs
moyenne du groupe** ».

Ce qui est calculé est donc un **taux par personne** — `taux_coherence`,
`taux_participation` — **rapporté à une moyenne de groupe**. C'est une note
individuelle. Et `taux_participation` est très exactement le taux d'assiduité que
la règle 3 interdit par ailleurs.

**La règle visait un indice, pas un affichage.** Elle n'a jamais eu pour objet la
mise côte à côte de deux positions publiées par l'Assemblée.

## Décision

La règle 7 distingue désormais les deux, et le tableau §6 porte deux lignes au
lieu d'une :

| | Statut |
| --- | --- |
| Indice individuel de cohésion ou de participation, rapporté à une moyenne de groupe | **jamais public** — `--rapport-interne` |
| Position d'un membre à côté de celle de son groupe, **un scrutin sourcé à la fois** | **public** — jamais compté, jamais noté |

Le garde-fou tient en une phrase, et il est dans la règle : **« a voté contre son
groupe 47 fois » est le même indice individuel par un autre chemin.** Un compte,
un taux ou une fréquence reconstitue la note que la règle interdit ; c'est la
limite, et elle ne dépend pas du nombre de scrutins affichés.

Le corps de l'épic #324 posait déjà cette frontière le 29/08/2026 — « c'est un
fait, pas un score… le garde-fou va avec : ne jamais en faire un compte, un taux
ni une fréquence » — sans que §2 règle 7 en tienne compte. Cet amendement met les
deux textes d'accord.

## Ce que la décision ne fait pas

Elle n'autorise **aucune caractérisation**. Publier les faits est permis ; écrire
que quelqu'un est « un franc-tireur » ou « loyal à son groupe » ne l'est pas, et
inviter le lecteur à le conclure non plus. La page montre des positions datées et
sourcées ; l'interprétation reste au lecteur, comme pour la convergence entre
groupes (`regrouper-nest-pas-joindre-639`).

Elle ne change rien au calcul interne : `compute_ecarts_cohesion_internes` reste
hors du schéma public, et `--rapport-interne` reste le seul chemin.

## Alternative écartée

**Retirer la section de la trame.** Elle aurait laissé la règle intacte au prix
d'un des sept emplacements — et surtout, elle aurait laissé le malentendu en
place : la prochaine personne à lire §2 règle 7 en aurait tiré la même
interdiction trop large, sur une donnée que le dépôt a toujours eu le droit de
publier.
