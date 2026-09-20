# Reconstruire une tranche d'amendements depuis l'archive figée (#691, lot 1)

`2026-09-09`

> **En bref** — `raw_data/profiles/` pèse **9,7 Gio dont 8,6 (89 %) de tranches d'amendements**, et **aucun champ n'est gros** : `co_signataires` fait **79,5 %** du poids parce qu'un amendement à 74 cosignataires est écrit dans **75 fichiers** (vérifié par `grep -rl`) portant chacun les 75 identifiants — **5 625 identifiants pour une information qui en compte 75**, et 74 cosignataires est la **médiane**, pas un cas extrême ; c'est la duplication que #431 a supprimée au niveau **pivot** (index partagé à 284 Mo) et jamais au niveau **brut** ; la donnée est pourtant déjà là **et déjà inversée** — `raw_data/amendements_an_figes/` porte 624 180 amendements en **38 Mo** gzippés *plus* un `index_par_acteur.json.gz` qui rend exactement `{uid, role_signataire}`, c'est-à-dire la forme que le pivot consomme depuis #431 ; **mesuré : 120 profils, 568 771 amendements, trois législatures, ZÉRO écart** champ par champ entre la tranche committée et sa reconstruction, les deux seuls champs dérivés étant ceux que #691 avait nommés (`role_signataire` vient de l'index, `legislature` du nom de fichier) ; le premier essai avait rendu **un** écart sur 16 915 — un résidu de conversion XML (`{"@xsi:nil": "true"}`) que la collecte normalise en `null`, recensé à **8 entrées sur 624 180**, assez rares pour passer inaperçues et assez réelles pour écrire un objet XML là où le corpus porte `null` (§2 règle 5) ; `mapping_pivot()` va de l'archive à la forme d'arrivée **sans passer par la tranche** — **alternative écartée** : le chemin naïf archive dédupliquée → tranche re-dupliquée → index re-dédupliqué, qui paierait la duplication en calcul après l'avoir ôtée du disque ; `None` ≠ `[]` (l'un dit « on ne sait pas », l'autre est un fait) et une archive à moitié présente est déclarée **absente** (#484) ; **ce lot ne supprime rien et rien ne l'appelle encore** — il publie l'inventaire des **sept** consommateurs du champ `amendements` du brut et laisse deux questions au lot 2 : le **filet de `merge_profile`** (la tranche committée est ce qui protège d'une collecte vide, or la collecte lit un cache CI non versionné) et l'**ordre** (ensemble identique, **16 915 positions sur 16 915 différentes**, quand le manifeste de #580 entrelace les tranches) ; portée : **5,55 Go** des 9,2 Go, la XVIIe étant vivante et sans archive. 16 tests neufs, suite complète à 4 202, 0 échec.

## Contexte

`raw_data/profiles/` pèse **9,7 Gio, dont 8,6 Gio (89 %) de tranches
d'amendements**. Mesuré champ par champ sur `mathilde-panot/16.json`
(21,8 Mo, 16 915 amendements, 1 289 octets par amendement), puis vérifié sur un
échantillon aléatoire de 12 tranches (37 618 amendements) :

| Champ | Part du poids |
| --- | ---: |
| `co_signataires` | **79,5 %** |
| `uid` | 3,0 % |
| les dix autres réunis | 17,5 % |

**Aucun champ n'est gros — le poids vient d'une multiplication.** L'amendement
`AMANR5L16PO791932BTC2723P0D1N000008` compte 74 cosignataires ; il est écrit dans
**75 fichiers** (vérifié par `grep -rl`), et chaque copie porte la liste complète
des 75 identifiants : **5 625 identifiants stockés pour une information qui en
compte 75**. La médiane est de 74 cosignataires par amendement — c'est le cas
courant, pas un cas extrême.

C'est la duplication que #431 a supprimée au niveau **pivot** — un profil publié
n'y garde qu'un `{amendement_id, role_signataire}`, et l'index partagé pèse
284 Mo — et qui n'a jamais été touchée au niveau **brut**.

## La donnée est déjà là, et déjà inversée

`raw_data/amendements_an_figes/` porte les **624 180** amendements des trois
législatures closes en **38 Mo** gzippés. Et il porte aussi, ce qui rend ce lot
court, l'inversion par acteur **déjà faite** :

```
amendements.json.gz        uid → l'amendement, une seule fois
index_par_acteur.json.gz   acteur → [{uid, role_signataire}, …]
```

Reconstruire la tranche d'un membre est une jointure, pas un calcul. Et le
second fichier porte **exactement** la forme que le pivot consomme depuis #431.

## Ce qui a été mesuré

| Législature | Profils | Amendements comparés | Écarts |
| --- | ---: | ---: | ---: |
| XIV | 40 | 104 693 | **0** |
| XV | 40 | 290 554 | **0** |
| XVI | 40 | 173 524 | **0** |
| **total** | **120** | **568 771** | **0** |

Champ par champ, entre la tranche committée et sa reconstruction. Deux champs
sont dérivés et non stockés — `role_signataire`, qui vient de l'index par
acteur, et `legislature`, que porte déjà le nom du fichier : exactement les deux
que #691 avait identifiés.

## Les nils XML : 8 entrées sur 624 180, et elles suffisaient

Le premier essai a rendu **un** écart sur 16 915 amendements :

```
date: attendu None / obtenu {"@xmlns:xsi": "…XMLSchema-instance", "@xsi:nil": "true"}
```

L'archive garde un résidu de la conversion XML → JSON que la collecte normalise.
Recensé sur tout le corpus : **8 entrées sur 624 180**, toutes sur `date`,
quatre en XV et quatre en XVI, aucune en XIV. Assez rares pour passer inaperçues,
assez réelles pour écrire un objet XML là où le corpus porte `null` (§2 règle 5).
`_normaliser_nil` les traite, et le test porte la forme exacte du défaut.

## Décision

`src/tranches_amendements_figees.py` sait rendre, pour un acteur et une
législature close :

- `reconstruire_tranche()` — la tranche au format que la collecte écrit ;
- `mapping_pivot()` — directement `{amendement_id, role_signataire}`, **sans
  passer par la tranche**. Reconstruire une liste dupliquée pour la dédupliquer
  trois lignes plus loin serait payer la duplication en calcul après l'avoir
  ôtée du disque.

**`None` et `[]` ne disent pas la même chose**, et le type de retour le porte :
`[]` est un fait — l'acteur est dans l'archive et n'a rien signé — quand `None`
dit qu'on ne sait pas. Une archive à moitié présente est déclarée absente : le
store sans l'index ne dit pas qui a signé quoi, et la traiter autrement
produirait des tranches vides pour un fichier manquant (#484).

## Ce que ce lot ne fait pas, et pourquoi

**Il ne supprime rien, et rien ne l'appelle encore.** L'ordre du découpage est
la seule garantie qui compte ici : aucune suppression avant que le lot suivant
ait tranché les deux questions ci-dessous.

### Les sept consommateurs du champ `amendements` d'un profil brut

| Consommateur | Ce qu'il en fait |
| --- | --- |
| `amendements_index.py` → `build_amendements_index_pivot.py` | construit `pivot_data/amendements/` |
| `generate_all_profiles.py` | la passe pivot |
| **`merge_profile.py`** | **`old["amendements"]` — le filet anti-écrasement** |
| `audit_collecte_vs_publie.py` | garde-fou « collecté = publié » (#511) |
| `audit_diff_profils.py` | contrôle de perte (#460) |
| `audit_volumetrie_profils.py` | mesure de volumétrie |
| `scripts/audit_fusion_blocs_599.py` | audit ponctuel |

### Question ouverte 1 — le filet de `merge_profile`

```python
# un echec/vide transitoire de l'open data amendements ne doit pas
# effacer des amendements deja collectes lors d'une regeneration precedente.
merged["amendements"] = merge_dossier_records(old.get("amendements"), …)
```

La tranche committée est **ce qui protège d'une collecte vide**, et la collecte
lit ses amendements depuis `.cache/amendements_an/` — un cache CI, pas du
contenu versionné. Cache froid ⇒ collecte vide ⇒ aujourd'hui la tranche sauve,
demain il n'y aurait plus rien à sauver (`collecte-vide-necrase-jamais.md`).
Deux voies, à trancher au lot 2 : l'archive devient le `old` pour 14/15/16, ou
la fusion refuse d'écrire une liste vide quand l'archive en connaît une non
vide. La seconde ne déplace pas la responsabilité du garde-fou.

### Question ouverte 2 — l'ordre

L'index par acteur range les amendements autrement que la collecte : sur
`mathilde-panot/16.json`, l'ensemble est identique et **les 16 915 positions
diffèrent**. Le manifeste de #580 porte un `ordre` qui entrelace les tranches à
la recomposition. Basculer sans traiter ce point produirait un diff sur tous les
profils au premier run, que le contrôle de perte lirait comme un changement.

## Portée

L'archive ne couvre que les trois législatures **closes** : **5,55 Go** des
9,2 Go de tranches. La XVIIe (3,64 Go) est vivante, n'a pas d'archive figée, et
la reconstruire depuis l'index pivot serait circulaire — cet index est construit
à partir des tranches.

## Alternative écartée

**Supprimer les tranches et les reconstruire à la volée pour alimenter l'index
pivot.** C'est le chemin naïf, et il fait un aller-retour :
archive dédupliquée → tranche re-dupliquée → index re-dédupliqué. D'où
`mapping_pivot()`, qui va de l'archive à la forme d'arrivée sans détour.
