<a id="donnees-versionnees-integrite"></a>
# Pourquoi les données vivent dans git : l'intégrité de ce que le site montre (2026-08-30)

`2026-08-30`

> **En bref** — la propriété protégée est que toute modification de ce que le site montre soit un événement public, attribué et daté ; `raw_data/` est une archive, pas un cache (38 mandats irrécupérables mesurés sur #484).

## Ce que cette entrée corrige

**Ce choix n'avait jamais été écrit.** Recherche du 30/08/2026 dans `docs/decisions/`, `AGENTS.md` et `ROADMAP.md` sur « piratage », « stockage externe », « hébergement », « bucket », « pourquoi versionner » : aucune occurrence.

L'épic volumétrie #429 a été recadrée **quatre fois**. La décision #434 a arbitré **comment borner l'historique** — quatre options pesées, mesurées, tranchées — mais ses quatre options partaient toutes de la même hypothèse implicite : *la donnée est dans git, comment limite-t-on la casse*. Sortir la donnée du dépôt n'a jamais figuré parmi elles.

Conséquence : chaque lot de volumétrie repousse contre une contrainte **sans savoir ce qu'elle protège**. C'est le pire état pour une contrainte — on la subit sans pouvoir la peser, et un jour quelqu'un la lève sans connaître l'enjeu.

## La décision

**Les données restent versionnées dans le dépôt.** `pivot_data/` (0,9 Go) et `raw_data/profiles/` (7,5 Go).

## Le pourquoi : une propriété, pas un mécanisme

L'énoncé usuel — « les données sont dans git » — nomme le moyen. La propriété est :

> **Toute modification de ce que le site montre est un événement public, attribué et daté.**

Le sujet la rend nécessaire. Ce dépôt publie des CV politiques de candidats à une présidentielle. La menace n'est pas la perte de données : c'est **l'altération**. Quelqu'un qui modifierait discrètement une position de vote ou un mandat changerait ce qu'un lecteur croit d'une personne, à quelques mois d'un scrutin.

Avec la donnée dans le dépôt, altérer un profil exige **un commit** : visible, permanent, attribué, dans le même historique que le code qui l'a produit. Une seule surface d'attaque, pas deux — les droits d'écriture sur la donnée *sont* les droits d'écriture sur le code.

Un magasin externe rendrait ça faux sur trois points :

| | Dans le dépôt | Dans un magasin externe |
| --- | --- | --- |
| Trace d'une modification | commit public et permanent | aucune, sauf à la construire |
| Identifiants à protéger | ceux du dépôt | **ceux du dépôt + ceux du magasin** |
| Effet d'une altération | exige un commit, donc visible | servie immédiatement, silencieusement |

## Ce n'est pas « le seul moyen », et il faut le dire

On pourrait signer les données, publier des empreintes, journaliser les écritures d'un magasin externe. **Ces mécanismes existent ; ils sont simplement à construire, et ils auraient leurs propres modes de défaillance** — une clé à protéger, un journal à surveiller, une vérification qui peut être désactivée sans bruit.

Git donne la propriété **gratuitement**, comme effet de bord de ce qu'il est. C'est ce qui rend l'échange favorable, pas une impossibilité théorique de faire autrement.

La pièce complémentaire est déjà en place : l'**archivage Software Heritage** (#568, outillé par `src/verifier_archivage_swh.py`) fournit une copie externe et indépendante. Le dépôt n'est donc pas le point unique de défaillance qu'il serait sans elle.

## `raw_data/profiles` est une ARCHIVE, pas un cache — mesuré le 30/08/2026

L'objection naturelle : `pivot_data` (0,9 Go) est ce que le site montre ; `raw_data/profiles` (7,5 Go) ne l'est pas. Les 7,5 Go méritent-ils la même garantie ?

**Oui, et la mesure qui le prouve date du 30/08/2026**, en instruisant #484.

Une collecte fraîche de `jean-luc-melenchon` comparée à son profil publié :

| | |
| --- | ---: |
| Mandats rendus par une collecte AN neuve | 36 |
| Mandats publiés | 74 |
| **Perdus si le brut était recollecté à neuf** | **38** |

Dont le **mandat sénatorial 2004-09-26 → 2010-01-07**. `archive.nossenateurs.fr` a été retirée du pipeline (#529) et son certificat a expiré (#516) : **aucune source vivante ne peut rendre ce mandat**. Il n'existe plus que parce que la fusion additive l'a conservé, run après run.

`raw_data/profiles` n'est donc pas reconstructible depuis les sources. C'est une **archive de ce que les sources ont dit à un moment donné** — et pour certains faits, la seule qui subsiste. La perdre ou la voir altérée serait irréversible.

L'argument d'intégrité couvre les 8,4 Go, pas seulement les 0,9.

## Ce que cette décision coûte, et qu'il faut assumer

Mesuré au 30/08/2026 :

| | |
| --- | ---: |
| Corpus versionné | 8,4 Go |
| Dépôt après `gc --prune=now` | 627 Mo *(seuil déconseillé : 5 Go)* |
| Coût d'un push de données | 204 Mo *(refus à 2 Go)* |
| Durée d'un run complet | 66 min |

Plus trois mécanismes qui n'existent que pour cette contrainte :

- le **sparse-checkout** de `tests.yml`, qui évite de télécharger le corpus à chaque test — 4 min 30 → 41 s, et qui a piégé trois personnes (#434, #520, `CLAUDE.md` le 30/08) ;
- le **garde-fou de blob** (#580) : avertit à 50 Mio, bloque à 80 ;
- le **bornage d'historique** (#434, #551, épic #566), armé mais jamais déclenché — le gain mesuré est aujourd'hui de **1 Mo, 0 %**.

**Ce coût est le prix de la propriété, pas un défaut à corriger.** Un lot de volumétrie qui le rencontre doit le peser contre l'intégrité, jamais contre le confort.

## Condition de réouverture

Cette décision se rediscute si **l'une** des trois conditions est réunie :

1. **Une grandeur mesurée franchit un seuil dur de GitHub** — pas un seuil recommandé, pas une projection : le push refusé à 2 Go, ou un blob refusé à 100 Mo. Les marges actuelles sont de ×10 et ×2.
2. **Un mécanisme d'intégrité équivalent est établi**, pas supposé : signature des données publiées, empreintes vérifiables par un tiers, et un chemin de vérification qu'un lecteur peut exécuter lui-même. « Le magasin a des journaux » n'est pas un mécanisme d'intégrité.
3. **`raw_data/profiles` cesse d'être une archive** — c'est-à-dire que toutes les sources redeviennent capables de rendre ce qu'il porte. Aujourd'hui c'est faux, et #484 le mesure.

Tant qu'aucune n'est réunie, **le rapport reste favorable**, et une proposition de sortir la donnée du dépôt doit d'abord répondre au tableau ci-dessus.

## Ce que cette décision ne dit pas

Elle ne dit **pas** que le volume est indifférent. Le partitionnement des profils bruts (#580), l'écriture JSON compacte (#433), la normalisation des votes et des amendements (#432, #431) ont tous réduit le corpus **sans rien en retirer** — c'est le principe directeur de #429 : *normaliser, jamais supprimer*.

Réduire ce qu'on stocke reste souhaitable. **Le sortir du dépôt, non.**
