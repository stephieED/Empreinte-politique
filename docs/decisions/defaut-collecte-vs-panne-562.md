<a id="defaut-collecte-vs-panne-562"></a>
# Une exception n'est pas une preuve, et un défaut de notre code n'est pas une panne de l'Assemblée nationale (#562) (2026-08-28)

`2026-08-28`

> **En bref** — un `TypeError` du dépôt, attrapé, était publié comme un état de la source.

Sur les **481 profils publiés** au 28/08/2026 (`f5e20b6`, run `33165786207`),
**99** publiaient `amendements: []` avec, pour preuve de leur état de
couverture :

```
amendements indisponibles : '<' not supported between instances of 'dict' and 'str'
```

Un `TypeError` du dépôt, attrapé, converti en « la source n'a pas répondu »,
puis republié verbatim dans le champ qui est censé distinguer une affirmation
sourcée d'une affirmation nue. **99 profils sur 481, soit 20,6 %** — le plus
gros écart de contenu publié, et aucune source n'était en défaut.

Deux défauts s'y superposaient, et ils sont indépendants : corriger le premier
laissait le second armé pour la prochaine exception.

## Défaut 1 — huit dates absentes, 99 profils vidés

L'open data AN est du XML converti en JSON, et un élément vide n'y devient pas
`null` : il devient un **objet**.

```json
"dateDepot": {"@xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance", "@xsi:nil": "true"}
```

`_parse_amendement_entry` recopiait `cycleDeVie.dateDepot` tel quel, et
`fetch_amendements_officiels` triait la liste par `a.get("date") or ""`. Un
`dict` face à une `str` : `TypeError`.

Mesuré sur les trois index de législatures figées committés
(`raw_data/amendements_an_figes/`) :

| | |
| --- | ---: |
| Amendements dans les index 14/15/16 | 624 180 |
| Dont `date` porte le marqueur `xsi:nil` | **8** (4 en XV, 4 en XVI) |
| Acteurs AN atteints par ces 8 (auteur + cosignataires) | **115** |
| Profils publiés parmi eux | **89** |
| Profils publiés touchés au total | **99** |

Huit amendements suffisent parce qu'ils sont **cosignés** : un seul d'entre eux
porte 75 signataires. Les 10 profils restants (`alexandra-martin`,
`patrick-hetzel`, `thibault-bazin`…) ne s'expliquent par aucun des trois index
figés — leur cause est dans la XVIIe, la seule législature encore reconstruite
par la CI, dont aucun index n'existe hors runner. C'est la seule part du constat
qu'un run CI reste à confirmer.

Reproduit et corrigé localement, sur le cache figé committé :

```
avant : adrien-quatennens EXCEPTION TypeError '<' not supported between instances of 'dict' and 'str'
après  : adrien-quatennens OK 14151 amendements (législature 16 seule)
```

Rejoué sur les 99 : **99/99 se remplissent**, 0 exception, 1 841 257
amendements collectés — et ce n'est qu'un **plancher**, la XVIIe n'étant pas
dans le cache local.

**La normalisation a lieu à la lecture, pas seulement au parsing.** Les index
des trois législatures figées sont committés et ne sont **pas** reconstruits par
la CI : les 8 enregistrements fautifs y sont déjà. Corriger le seul parseur
aurait laissé les 89 profils cassés jusqu'à un rejeu manuel de
`build_amendements_index_figees.py` sur 350 à 650 Mo d'archives. Les deux bouts
sont donc corrigés — `_texte_an` au parsing pour que les futurs index soient
propres, `_texte_an` à la matérialisation de chaque enregistrement pour que les
index déjà écrits redeviennent lisibles.

C'est la **troisième** fois que cet idiome mord ici : #539 l'avait trouvé dans
`identite.uri_hatvp` (186 profils sur 476 portaient le marqueur au lieu d'une
URI). D'où un helper nommé plutôt qu'un `isinstance` de plus.

## Défaut 2 — `except Exception` transformait un bug en panne de source

```python
except Exception as exc:
    warnings.append(f"{WARNING_PREFIX_AMENDEMENTS_INDISPONIBLES} : {exc}")
```

Une branche unique pour deux faits qui n'ont rien à voir : « l'Assemblée
nationale n'a pas répondu » et « notre code a échoué ». Le préfixe est ensuite
mappé vers `cause: "panne"` par `couverture_profil`, et le produit accusait donc
la source d'une faute qui était la nôtre — la même faute de classe que #484 (un
échec réseau lu comme une donnée) et que ce que #539 a dû trancher sur
`WARNING_PREFIX_VOTES_INTROUVABLES` (un préfixe couvrant une panne *et* un
constat).

**Décision : l'exception ne remonte pas, elle change de nom.** Remonter aurait
fait échouer `build_profile_any_chambre`, donc n'aurait rien publié du tout pour
ces profils — un silence, précisément ce que #539 a passé un lot à retirer.
`_tracer_echec_collecte` classe l'exception une fois, et une seule :

- une exception de `ERREURS_SOURCE` (`AmendementsIndexError`, `OSError`,
  `zipfile.BadZipFile`, `json.JSONDecodeError`, `requests.RequestException`) dit
  quelque chose **de la source** → préfixe de panne, inchangé ;
- toute autre exception ne dit rien de la source, seulement de nous →
  `WARNING_PREFIX_DEFAUT_COLLECTE` et `traceback.print_exc()`.

La règle s'applique aux **quatre** étapes de `build_profile` dont le warning
alimente `MOTIFS_PANNE` (amendements, textes portés, interventions Syceron,
questions), pas au seul incident constaté : le défaut est une classe.

`cause` a donc **trois** valeurs et non plus deux : `panne`, `par_decision`, et
`defaut_collecte`. Un lecteur n'a pas à savoir laquelle des deux premières s'est
produite, mais le produit n'a pas le droit de se tromper de coupable. Quand les
deux sont signalés pour la même liste, `defaut_collecte` gagne : de ce que nous
savons, le fait dont nous sommes sûrs est le nôtre.

**La preuve d'un `defaut_collecte` est construite, jamais recopiée.**
`_preuve_defaut_collecte` écrit une phrase qui ne contient aucun texte
d'exception ; le message technique reste dans `meta.warnings` et au journal de
run. C'est ce qui rend le garde-fou ci-dessous inatteignable en régime normal.

## Le garde-fou — ce que `preuve` refuse désormais

`valider_couverture` ne se contentait que d'une chaîne non vide. C'est ce seul
contrôle qui a laissé publier un `TypeError` comme preuve.
`marqueur_defaut_code` refuse maintenant les marqueurs qui ne peuvent venir que
d'un **défaut de programmation** : `Traceback (most recent call last)`,
`not supported between instances`, `unsupported operand type`,
`object has no attribute`, `TypeError`, `KeyError`, `AttributeError`,
`IndexError`, `NameError`… et la forme `File "…", line 42`.

**Ce qu'il ne refuse pas est aussi important.** Une preuve de `panne` cite
légitimement ce que la source a renvoyé, nom d'erreur réseau compris —
`ConnectionError`, `IncompleteRead`, `SSLError`. C'est un fait **sur la
source**, et il est publiable. Un garde-fou qui casserait le chemin normal des
pannes serait désarmé au premier incident, et le défaut reviendrait sous une
autre forme. La liste bannit donc les classes d'erreur de programmation, pas la
mention d'une exception.

Vérifié sur les 3 766 entrées de couverture (2 405 couples profil/liste) des
481 profils publiés : **99 rejetées, toutes de la même famille, aucune autre**. Le garde-fou vit dans
`schema_pivot`, donc du côté du **contrat**, ce qui le fait s'appliquer aux deux
bouts — la fabrique se contrôle elle-même avec lui (`ecrire_couverture` lève)
comme `validate_profil` contrôle ce qui est publié.

## Ce qu'un run CI doit confirmer

Les profils publiés **ne sont pas régénérés dans ce lot** : un corpus reconstruit
depuis un cache local n'a pas la couverture d'un run CI (la XVIIe législature en
particulier n'y est pas). Restent à confirmer par un run complet :

1. les **10 profils sur 99** dont la cause est en XVIIe législature se
   remplissent aussi ;
2. la relation `amendements` d'`audit_collecte_vs_publie` (#545) tient toujours
   à **+0** : elle rapproche le brut du publié, et remplir 99 profils fait
   monter les **deux** côtés — mesure du 28/08 avant correction :
   3 076 176 = 3 076 176 ;
3. la volumétrie : le plancher local est de +1 841 257 entrées d'amendements sur
   les seules législatures figées, à comparer aux 3 076 176 publiées. Les métas
   vivent dans `pivot_data/amendements/` et non dans les profils (#431), donc
   c'est l'index partagé qui grossit, pas les 481 fichiers.

## Ce qui reste ouvert

- Les **99 profils publiés portent encore la preuve fautive** tant qu'un run
  n'a pas régénéré le corpus. Le garde-fou est côté écriture : il empêche d'en
  produire de nouveaux, il ne réécrit pas l'existant.
- Les trois autres `except Exception` de `build_profile` (identité, positions
  dans l'hémicycle, et le niveau `build_profile_any_chambre`) n'ont pas de motif
  dans `MOTIFS_PANNE` : leur message n'atteint aujourd'hui aucune `preuve`. Ils
  restent à traiter le jour où l'un d'eux y entre.

---

