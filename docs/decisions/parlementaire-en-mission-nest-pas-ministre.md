<a id="parlementaire-en-mission-nest-pas-ministre"></a>
# Le `label` d'un mandat `MINISTERE` ne dit pas si c'est un maroquin (#474) (2026-08-20)

`2026-08-20`

> **En bref** — le `label` d'un mandat `MINISTERE` ne dit pas si c'est un maroquin : un parlementaire en mission n'est pas ministre.

`pivot_data/gouvernements/gouvernement-BAYROU.json`, sur `main` à `ea6f0d5`,
publiait ceci :

```json
{
  "membre_id": "nosdeputes:astrid-panosyan-bouvet",
  "portefeuille": "Ministère de l'économie, des finances et de la souveraineté industrielle, énergétique et numérique",
  "debut": "2026-02-04", "fin": null, "actif": true
}
```

dans un document dont la période se referme le 2025-09-09, `actif: false`.
Trois faussetés en un enregistrement : un portefeuille jamais détenu, une date
postérieure à la fin du gouvernement, un `actif: true` dans un gouvernement
clos. C'est une affirmation factuelle fausse publiée dans le jeu de données
(§2).

## Pourquoi le label ne suffit pas

`categorie == "fonction_gouvernementale"` réunit deux `typeOrgane` du zip AMO30,
et #398 avait établi que le label les sépare (voir
[[gouvernement-premier-ministre-portefeuille]]). C'est vrai pour cette
séparation-là — et seulement pour elle. La docstring de
`_est_mandat_appartenance_gouvernement` en tirait implicitement une seconde
conclusion, fausse : qu'un mandat `MINISTERE` soit un portefeuille.

Un **parlementaire en mission** (art. LO144) porte lui aussi un mandat
`MINISTERE`, et son label est l'intitulé du ministère **auprès duquel** il est
missionné. « Ministère de l'économie… » désigne alors le ministère d'accueil de
la mission, pas un maroquin. Sur ce seul critère, les deux sont **strictement
indiscernables** — la personne missionnée reste députée, elle n'est pas membre
du gouvernement.

Ce que le label ne dit pas, `mandats[].fonction` le dit : il reprend
`infosQualite.libQualite` de la source AN (`candidate_profile`, renommé `type`
→ `fonction` par `normalize_nosdeputes`). `gouvernement_roster.py` ne le lisait
nulle part. Répartition mesurée sur les 209 profils du dépôt au 2026-08-20 :

| `fonction` sur un mandat `MINISTERE` | Occurrences |
| --- | --- |
| **`en mission`** | **92** |
| `Ministre délégué` | 48 |
| `Ministre` | 43 |
| `Secrétaire d'État` | 18 |
| `Ministre d'État, ministre` | 4 |
| `Premier ministre` | 4 |
| `Garde des sceaux, ministre de la justice` | 2 |
| `Ministre d'État, Garde des Sceaux, ministre de la justice` | 1 |

43 % des mandats traités comme des portefeuilles n'en étaient pas. Une seule
attribution fausse était publiée, parce qu'il faut de surcroît un chevauchement
— mais le vivier est de 92 mandats pour 209 profils ; à 752, il dépassera 330.

## Liste blanche, pas liste noire

Exclure `"en mission"` aurait suffi à corriger le fichier publié. C'est
précisément le geste que §2.5 interdit : une liste noire traite toute valeur
non prévue comme un maroquin, c'est-à-dire pose une valeur par défaut sur une
donnée non résolue. Les 7 qualités ministérielles observées le sont sur 209
profils du corpus cible de ~752 : une 8e apparaîtra.

`FONCTIONS_MINISTERIELLES` est donc une liste blanche, et
`_qualite_portefeuille` rend **trois** états, pas deux :

- **ministérielle** → portefeuille retenu ;
- **non ministérielle** (`en mission`) → écarté **sans warning** : c'est
  l'exclusion attendue, 92 occurrences, un warning par occurrence noierait les
  vraies alertes ;
- **inconnue** → écarté **avec un warning** nommant la personne, l'intitulé et
  la qualité rencontrée.

L'inconnu ne plante pas le pipeline et ne disparaît pas non plus : le membre
reste dans `membres[]` avec `portefeuille: null`, et le warning remonte dans
`meta.warnings` du profil de gouvernement (`gouvernement_profile`), donc dans
le jeu de données publié — traçable, pas seulement affiché en CI. Le geste de
maintenance attendu est d'ajouter la valeur à
`FONCTIONS_MINISTERIELLES_OBSERVEES` après vérification humaine : même
principe éditorial que `raw_data/gouvernements_reels.json`.

*Coût assumé* : une qualité ministérielle légitime mais non encore listée fait
temporairement retomber un portefeuille réel à `null`. Une donnée manquante et
signalée, plutôt qu'une donnée fausse et silencieuse — c'est l'arbitrage
constant de §2.5.

*Normalisation* : la comparaison se fait sur casse et espaces normalisés
(`_normalise_fonction`). La source écrit déjà « Garde des sceaux » et « Garde
des Sceaux » pour la même qualité. Purement typographique : aucun rapprochement
par préfixe, aucune troncature — « Ministre » et « Ministre délégué » restent
deux qualités distinctes.

## Le second défaut : un mandat d'appartenance jamais clos

La qualité n'explique pas tout. Panosyan-Bouvet porte **deux** mandats
`Gouvernement (BAYROU)`, identiques en tout sauf leur fin :

```
fonction='membre' | 2024-12-24 -> 2025-09-09 | actif=False
fonction='membre' | 2024-12-24 -> None       | actif=True
```

Le second n'est jamais clos, alors que le gouvernement l'est depuis le
2025-09-09. `_portefeuilles_du_mandat` ne testait le chevauchement que contre
la période du **mandat** : un mandat sans fin accroche donc n'importe quel
mandat ministériel postérieur, indéfiniment. C'est ce qui a donné au
portefeuille fantôme de 2026 quelque chose à quoi s'accrocher.

Le chevauchement est désormais borné **aussi** par la période du gouvernement.
Le garde-fou de #398 — « un ministre entré en cours de mandature ne doit pas se
voir attribuer le portefeuille qu'il occupait avant » — reste entier : la
nouvelle condition est un ET, elle ne peut que restreindre, jamais rattraper un
portefeuille que la période du mandat écarte. Un test de non-régression le
vérifie explicitement (portefeuille antérieur chevauchant le gouvernement mais
pas le mandat : toujours exclu).

Cette borne rend par ailleurs structurellement impossibles les deux autres
faussetés du record : plus aucune entrée `membres[]` ne peut avoir un `debut`
postérieur au `fin` du gouvernement, ni être `actif` dans un gouvernement clos.

*Note* : #398 avait mesuré « aucun mandat `MINISTERE` ne déborde de la période
du mandat d'appartenance qu'il chevauche (0 cas sur 24) ». C'était vrai du
corpus d'alors. Le corpus a grandi, et le cas est apparu — illustration de la
raison pour laquelle une mesure sur corpus partiel ne fonde jamais un
invariant de code.

## `build_premier_ministre` : ce qui était en jeu n'était pas seulement un faux PM

Le même défaut y était latent, et plus grave. `nosdeputes:david-amiel` porte un
mandat de label **« Premier ministre »**, `fonction: "en mission"`, du
2024-01-12 au 2024-05-05 : une mission auprès de Matignon, pas Matignon. Sans
effet aujourd'hui — son seul mandat d'appartenance est postérieur (Lecornu II,
2025-10-13), donc aucun chevauchement.

Mais `build_premier_ministre` retourne `None` **avec un warning** quand
plusieurs candidats remplissent les conditions. Un missionné chevauchant
n'aurait donc pas seulement inventé un Premier ministre : il aurait *effacé* le
vrai. Le filtre de qualité amont l'écarte déjà ; la fonction exige en plus la
qualité exacte « Premier ministre », second verrou indépendant, pour qu'un
desserrement futur de la liste blanche ne rouvre pas ce chemin-là.

## Ce que la correction ne fait pas

Elle ne supprime **aucune donnée collectée**. Le mandat de parlementaire en
mission est un fait public et traçable : il reste dans `mandats[]` du profil,
un test le vérifie sur fixture figée. Ce qui est retiré, c'est une
**attribution** — l'entrée dans `membres[]` d'un gouvernement.

## Propagation aux fichiers déjà committés

`generate_gouvernement_profiles.py` réécrit intégralement
`pivot_data/gouvernements/*.json` à chaque run (`write_text`, jamais de fusion,
résultat entièrement déterministe à partir des pivots locaux). La correction se
propagera donc au prochain run réussi de `generate-data`, sans intervention.
Deux réserves à connaître :

- le garde-fou #427 : si une archive de dossiers législatifs manque, la
  fonction rend `COLLECTE_INCOMPLETE` et **aucun** profil n'est réécrit — le
  fichier fautif resterait alors en place ;
- `preserve_stable_freshness_timestamps` (#343) ne fige que `meta.genere_le` et
  `sources[].synchro_le` quand le contenu est par ailleurs identique ; un
  changement de contenu est toujours écrit.

D'ici là, `gouvernement-BAYROU.json` conserve l'entrée fausse : la correction
porte sur le code de dérivation, elle ne réécrit pas les données publiées.

## Défaut adjacent, hors périmètre

Le même mandat d'appartenance dupliqué produit aussi des **entrées `membres[]`
strictement identiques** : sous Bayrou, Panosyan-Bouvet et Marc Ferracci ont
chacun leur portefeuille réel publié deux fois. `build_premier_ministre`
déduplique ses candidats ; `build_gouvernement_roster` ne déduplique pas ses
entrées. Ce n'est pas une attribution fausse — c'est un doublon — et cela
touche au corollaire de [[test-adosse-au-corpus-vivant]] : `membres[]` dénombre
des entrées, pas des personnes. Laissé en l'état, à traiter séparément.

