<a id="publication-dun-job-annule"></a>
# Un préfixe de flux est valide, un préfixe de profil est faux (#460) (2026-08-20)

`2026-08-20`

> **En bref** — un préfixe de flux est valide, un préfixe de profil est faux : ce qu'un job annulé a le droit de publier.

> ⚠️ **Diagnostic corrigé le 20/08/2026 — voir [[collecte-vide-necrase-jamais]] (#465).**
> Cette entrée attribue la destruction du run `32302557156` à la publication
> d'un job **annulé** et au `if: always()` de l'étape de publication. C'est
> faux. Le profil de `jean-luc-melenchon` a été écrit **deux minutes après le
> lancement**, bien avant l'annulation de son job, et celui de `marine-le-pen`
> ne portait aucune trace d'interruption. La cause réelle est qu'une
> **sous-collecte en échec** rend un `[]` que `--no-merge` ne distingue pas d'un
> zéro constaté.
>
> Ce qui reste juste ici : le constat chiffré des pertes, la restauration, et la
> remarque sur la transposition abusive du principe de #443 — un préfixe de flux
> est exact, un profil partiel est faux. Elle vaut toujours, elle n'explique
> simplement pas ce cas-ci.

Le run `32302557156`, lancé pour **réparer** la perte d'interventions de #460, a
détruit davantage qu'il n'a réparé. Il s'est terminé `cancelled` — 4 de ses 8
shards `extract-an` annulés de l'extérieur — mais `merge-and-pivot` a réussi et
a committé (`e4d71cf`).

| profil | champ | avant | après |
| --- | --- | --- | --- |
| `jean-luc-melenchon` | `amendements` | 18 721 | **0** |
| | `votes` | 1 016 | **0** |
| | `textes_portes` | 33 | **0** |
| | `mandats` | 68 | 29 |
| `bruno-retailleau` | `textes_portes` | 36 | **0** |
| `marine-le-pen` | `textes_portes` | 23 | **0** |
| | `mandats` | 53 | 52 |

Restauré : **121 interventions sur 789**. Les trois profils sinistrés sont
parmi les quatre dont le shard a été annulé.

## La cause est dans #450, et elle vient d'une transposition abusive

L'étape de publication introduite par #450 porte `if: always()`. Elle publie
donc ce qu'un job **annulé** avait écrit — y compris un profil collecté à
moitié. Avec `--no-merge`, ce demi-profil écrase le bon.

Ce `if: always()` était délibéré, et justifié par [[telechargement-an-trois-modes-defaillance]]
(#443) : *ne jamais jeter un préfixe valide*. Les préemptions sont fréquentes
ici (#228), et un job interrompu ne devait pas perdre son travail.

**La transposition était fausse.** Sur un flux de téléchargement, un préfixe est
un préfixe : les octets déjà reçus sont exacts, et la reprise complète. Sur un
profil, un « préfixe » n'est pas un profil incomplet — c'est un profil **faux** :
rien ne distingue « ce membre n'a aucun amendement » de « la collecte s'est
arrêtée avant les amendements ». Le manifeste consigne l'écriture, pas sa
complétude.

Le principe de #443 reste juste dans son domaine. Il ne se transpose pas à un
enregistrement structuré, dont la validité n'est pas croissante avec le nombre
d'octets écrits.

## Ce qui aurait dû l'arrêter

[[controle-de-perte-avant-commit]] (#461) : le contrôle aurait vu −18 721
amendements, écrit `PERTE_PROFILS_NON_DECLAREE` et annulé le commit. Il était
ouvert en PR au moment du run, non mergé — le run tournait sur `280faa8`.
Mergé depuis (`81e36e8`).

## La restauration

Faite **à la main**, par fusion additive depuis `e4d71cf^` :

1. les trois profils **bruts** sont fusionnés (`merge_raw_profile`) avec leur
   version d'avant — additif, donc rien de ce que le run aurait légitimement
   ajouté n'est écarté ;
2. les index partagés sont reconstruits — sans ça, les 18 721 amendements
   restaurés ne seraient référencés par aucune entrée d'index ;
3. les trois pivots sont re-dérivés par le code d'aujourd'hui (`--pivot-only
   --no-merge`), donc au **schéma courant** (#431/#432).

Le brut ne pouvait pas être copié depuis le pivot d'avant : `e4d71cf^` porte
l'**ancien** schéma pivot, et le recopier annulerait #431 et #432. Le brut, lui,
n'est pas normalisé — c'est la couche source-near — donc son schéma est stable
d'un commit à l'autre. C'est ce qui rend la restauration possible, et c'est un
argument de plus pour [[normalisation-votes]] : ne pas normaliser le brut, ce
n'est pas de la place perdue, c'est la seule copie depuis laquelle reconstruire.

Vérification : `audit_diff_profils.py --ref e4d71cf^` rend « aucune perte sur
les champs stables », et les totaux du corpus retrouvent l'état d'avant —
524 353 votes, 810 552 amendements, 423 textes portés, 16 498 mandats — **plus**
les 121 interventions que le run avait légitimement rendues.

## Ce qui reste ouvert

Le `if: always()` de l'étape de publication **n'est pas corrigé ici**. Le
corriger demande de trancher : ne rien publier depuis un job annulé (on perd
alors le travail d'un job préempté en fin de course), ou marquer l'artifact
comme partiel pour que la fusion le refuse en mode écrasement. Les deux se
défendent, et ce n'est pas une décision à prendre dans un commit de
restauration.

