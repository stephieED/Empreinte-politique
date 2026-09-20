<a id="mandat-electif-perdu-fausse-le-denominateur"></a>
# Un mandat électif perdu ne manque pas seulement sur la fiche : il sort le membre du dénominateur de son groupe (#465) (2026-08-20)

`2026-08-20`

> **En bref** — un mandat électif perdu sort le membre du dénominateur de son groupe — la perte se propage à un chiffre publié.

Les 355 `mandats` et 49 `textes_portes` restés perdus après [[restauration-interventions]]
ont été restaurés par la **même méthode** — champ seul, réinjecté dans le brut,
pivot re-dérivé par le code du jour. Rien de neuf de ce côté : ce qui suit est ce
que la restauration a révélé **en aval**, et qui ne s'était pas présenté en #463
ni en #464.

## Ce qui est nouveau

Les 355 mandats se répartissent en 301 commissions, 29 groupes d'amitié,
1 extra-parlementaire… et **24 mandats électifs**. Ces 24-là ne sont pas une
ligne de plus sur une fiche : `mandats[].categorie == "mandat_electif"` est ce
qui définit, dans `group_profile.py`, **la période pendant laquelle un membre est
éligible à un scrutin** (`_member_eligibility_intervals`). Les perdre revient à
déclarer le membre non éligible, donc à le retirer du **dénominateur** d'un ratio
publié (AGENTS.md §2.7).

Mesuré sur les trois groupes concernés :

| groupe | membres restaurés | effet |
| --- | --- | --- |
| `groupe-AN-REN-16` | 18 | `membres_eligibles` 63 → **69** sur les 4 099 scrutins ; `mandats_agreges` 646 → 729 entrées |
| `groupe-AN-RN-16` | 1 | 3 405 scrutins recalculés |
| `groupe-AN-SOC-16` | 1 | `cohesion_votes` **0 → 814 scrutins** |

Le cas de `groupe-AN-SOC-16` est le plus net. Son unique membre couvert,
`jerome-guedj`, n'avait plus que son mandat de la XVII (2024-07-07) : la XVI
(2022-06-22 → 2024-06-09) était partie avec les mandats perdus. Le groupe
publiait donc **zéro scrutin de cohésion**, et le quality gate le signalait
comme « données incomplètes ? ». Ce n'était pas une lacune de collecte : la
donnée était là, c'est la clé de lecture qui manquait.

Même effet sur `membres[].debut_dans_groupe`, dérivé du premier mandat électif :
10 des 23 profils affichaient une entrée dans le groupe trop tardive de deux ans.

**La leçon** : une perte sur `mandats` ne se lit pas au nombre d'entrées. Selon
la `categorie`, elle est soit une ligne manquante, soit un **dénominateur faux** —
et un dénominateur faux est publié sans avertissement, parce que rien, dans le
profil de groupe, ne distingue « ce membre n'était pas élu ce jour-là » de « on a
perdu son mandat ».

## Le patch de groupe, et son contrôle

Patch chirurgical, comme en #464 : régénérer les profils de groupe écraserait
`meta.couverture_roster`, qui vient d'un fetch réseau. Les cinq champs qui
dépendent de `mandats[]` — `membres`, `effectif`, `periode`, `cohesion_votes`,
`mandats_agreges` — sont recalculés par les fonctions du pipeline elles-mêmes et
réinjectés ; `tags_thematiques_agreges`, `amendements_agreges`, `sources` et
`meta` ne sont pas touchés (vérifié : `_aggregate_amendements` ne lit pas
`mandats`, `parti_profile.py` non plus, et `gouvernement_roster.py` ne lit que
les mandats `fonction_gouvernementale` — dont **aucun** n'a été restauré).

Ce recalcul ne vaut que si l'on prouve qu'il reproduit le pipeline. **Contrôle
préalable** : recalculer ces cinq champs à partir des pivots d'**avant** la
restauration doit rendre les profils de groupe committés **à l'identique**. Fait
sur les 7 groupes, y compris les 4 sans membre restauré — zéro écart. Sans ce
contrôle, un écart après restauration serait indiscernable d'un artefact de la
méthode de recalcul.

Même logique côté profils : re-dériver les 32 pivots par `--pivot-only
--no-merge` **avant** de toucher au brut rend les 32 fichiers committés
octet pour octet. La re-dérivation est donc un no-op vérifié, et tout écart
constaté après coup est imputable à la restauration seule.

## Ce que ça n'a pas rattrapé

`audit_diff_profils.py` compte des **listes**. Un scalaire qui régresse lui est
invisible, et il y en a : `parti` est passé de renseigné à `null` depuis
`a125e9e^` sur `jean-luc-melenchon`, `edouard-philippe` et `laurent-wauquiez` —
trois candidats déclarés, dont `raw_data/candidats.json` porte pourtant le parti.
Quatre autres (`jerome-guedj`, `gabriel-attal`, `bruno-retailleau`,
`marine-le-pen`) ne l'ont jamais eu dans leur pivot, pour la même raison
probable : la passe pivot roster-driven repasse après la passe candidats et, en
`--no-merge`, réécrit le pivot sans le `parti` que seule la première connaît.

Non corrigé ici : c'est un défaut de pipeline, pas une donnée à restaurer, et le
réparer dans un commit de restauration mélangerait deux sujets. Consigné pour
qu'il ne se reperde pas.

