<a id="audit-sediment-inventaire-839"></a>
# Le sédiment se compte avant de se juger : sept familles, deux couches, aucun retrait (#839, lot A) (2026-09-12)

`2026-09-12`

> **En bref** — `src/audit_sediment.py` compte ce que le corpus publié garde d'une source que le pipeline n'interroge plus, **sans rien retirer** : sept familles, chacune définie par une **signature de forme** et non par un nom de source, sur **les deux couches** — un sédiment retiré du seul brut ne descend jamais au pivot (#729) ; mesuré le 12/09/2026 sur `origin/main` : au pivot, **511** interventions à identifiant entier (5 profils), **406** mandats sans `categorie_source` (45 profils : 7 à provenance `candidat_declare` — dont **1 candidat qui a décliné**, `laurent-wauquiez`, collecte gelée par #760 — et 38 membres de roster), **13** mandats actifs sans aucune date (2 profils), **476** entrées `sources[]` sous licence Regards Citoyens (475 profils), **47** avertissements hérités (19 profils), **75** preuves de couverture citant la source retirée (15 profils) ; **deux refus délibérés** — une couche qui ne porte pas `meta.provenance` n'est **pas ventilée** (le brut rendrait « 1 181 candidats déclarés », faux, #630) et une famille dont le champ est absent de la couche affiche **`champ absent`, jamais `0`**, l'absence de champ n'étant pas l'absence de sédiment (§2 règle 5) ; **ce que le compte des mandats mélange, et qui aurait faussé le lot B** : **21 des 406 sont des organes du Parlement européen** sur 2 profils, que le référentiel AMO30 déclarerait introuvables — le verdict de reproductibilité devra interroger les deux référentiels ; les types de source retirés et les formulations d'avertissement héritées sont **dérivés** de `licences.py` et `avertissements.py`, jamais recopiés ; 12 tests sur fixtures, aucun ne lit le corpus réel.

## 1. Pourquoi un compteur avant tout le reste

Le 12/09/2026, deux mesures successives ont été remontées à la propriétaire avec
des familles différentes, parce que chacune avait été cherchée à la main. Une
troisième a affirmé « non reproductible » là où elle avait mesuré « l'entrée ne
revient pas telle quelle ».

Un inventaire n'est pas un préalable de forme : c'est ce qui empêche qu'une
famille apparaisse en cours de nettoyage, et ce qui rend le contrôle de perte
lisible. Le script se relance après chaque run — une famille revenue à zéro qui
remonte est une régression, et c'est la seule façon de la voir.

## 2. Sept signatures de forme, jamais un nom de source

Ce que le pipeline vivant produit se reconnaît ; ce qu'il ne produit plus aussi.
Un identifiant **entier** dans `interventions[]` n'appartient à aucune source
vivante : Syceron rend `syceron_…`, les questions officielles `question_…`, le
Parlement européen `europarl_…`.

Les deux tables qui nomment réellement la plateforme retirée restent **où elles
sont** : `licences.LICENCE_PAR_TYPE_SOURCE` (l'attribution ODbL encore due) et
`avertissements.AVERTISSEMENTS_HERITES` (les avertissements publiés d'avant,
#642). L'audit les **dérive**. Les recopier en aurait fait une seconde vérité,
et `tests/test_retrait_nosdeputes_529.py` n'admet la mention que dans les
emplacements qu'il nomme.

## 3. La mesure, au 12/09/2026 sur `origin/main`

| Famille | Pivot | Brut |
| --- | ---: | ---: |
| `interventions[]` à identifiant entier | 511 (5 profils) | 511 (5) |
| `interventions[]` dont l'URL cite la source retirée | 511 (5) | 511 (5) |
| `mandats[]` sans `categorie_source` | 406 (45) | 393 (45) |
| `mandats[]` actifs et sans aucune date | 13 (2) | 13 (2) |
| `sources[]` sous licence Regards Citoyens | 476 (475) | *champ absent* |
| `meta` — avertissement hérité | 47 (19) | 28 (19) |
| `couverture[].preuve` citant la source retirée | 75 (15) | *champ absent* |

Au pivot, les 45 profils portant un mandat sans estampille se ventilent en **7 à
provenance `candidat_declare` et 38 membres de roster** ; les 475 portant le
marqueur de source en **10 et 465**.

**`candidat_declare` n'est pas « candidat déclaré aujourd'hui ».** La provenance
dit quelle population a fait collecter le profil, jamais où en est la
candidature : `raw_data/candidats.json` porte 34 entrées, 32 `declare` et 2
`decline`, et les 32 profils de cette provenance comptent les **2 déclinés**
(`laurent-wauquiez`, `jordan-bardella`). L'un des 7 porteurs de mandats sans
estampille est `laurent-wauquiez`. Le compte juste s'écrit donc « 6 déclarés et
1 décliné », et un compteur qui dit « 7 candidats déclarés » se lit comme un
fait faux sur la candidature.

**Le gel de #760 ne change rien au nettoyage** — arbitrage de la propriétaire,
12/09/2026 : il ne vaut que pour la **collecte en CI**. Un profil gelé se
corrige comme les autres.

**L'écart 406 / 393 tient à un seul profil**, `yannick-vaugrenard` : 19 au pivot
contre 6 au brut. Ses 13 mandats européens arrivent au pivot par
`mandat_europeen` et n'y portent pas d'estampille.

## 4. Deux refus délibérés

**Une couche sans `meta.provenance` n'est pas ventilée.** `raw_data/profiles/`
ne porte pas ce champ ; `provenance_du_profil()` rend alors
`candidat_declare` par rétro-compatibilité, ce qui est juste au pivot et faux au
brut — « 1 181 candidats déclarés » quand le corpus en compte 32. L'audit
affiche le total et dit où lire la ventilation (#630).

**Un champ absent n'est pas un compte nul.** `sources[]` et `couverture`
n'existent pas au brut. Y afficher `0` se lirait comme un constat sur le
sédiment, alors que c'est un constat sur le schéma (§2 règle 5).

## 5. Ce que le compte des mandats mélange

**21 des 406 mandats sans estampille sont des organes du Parlement européen**,
sur 2 profils : commissions parlementaires, délégations, groupe politique
européen. Les confronter à AMO30 les déclarerait « introuvables » — un faux
verdict, dans le sens le plus grave puisqu'il autoriserait un retrait.

Le lot B interrogera donc **les deux référentiels**, AMO30 et le bloc
`mandat_europeen` du profil brut.

## 6. L'alternative écartée

**Un compteur par famille, écrit au fil des lots.** C'est ce qui se passait :
trois mesures, trois définitions, aucun moyen de dire si une quatrième famille
attendait. Un script unique, relançable, rend le même nombre deux jours de
suite — et c'est lui qui, au lot E, dira si le nettoyage a atteint la couche que
`web/` lit.
