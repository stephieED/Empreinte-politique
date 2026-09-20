<a id="reduction-nommee-collecte-vs-publie-888"></a>
# Une somme de longueurs suppose que chaque entrée collectée est distincte, et le portail européen le dément (#888) (2026-09-13)

`2026-09-13`

> **En bref** — le run `34712936188` a **bloqué avant commit** sur la troisième garde de §3c : **29 couples (profil, liste), 45 entrées**, toutes sur `mandats`, tous les profils nommés portant un mandat européen. Rien n'était perdu. `normalize_europarl.dedupliquer_appartenances`, arrivé avec #879 entre les deux runs, reconnaît que le portail européen publie **la même appartenance deux fois** — l'une classée, l'autre non — et n'en publie qu'une ; le brut garde les deux, parce qu'il dit ce que la source a rendu. `audit_collecte_vs_publie` sommait des longueurs et lisait donc 45 entrées « collectées et jamais publiées » là où 45 entrées avaient été reconnues comme les doublons de 45 autres. Une relation peut désormais déclarer, à côté de ses sources, une **réduction nommée** : la fonction de la normalisation, **rejouée** sur le brut par le contrôle, jamais réimplémentée. Le seuil du déficit reste **0**. Mesuré le 13/09/2026 sur `origin/main` `7e48b4b05`, sur les **1 196 profils publiés** : la réduction rend **46 entrées écartées sur 30 profils**, et le déficit passe de 45 à **0**.

## 1. Ce qui a changé entre les deux runs

| Run | Heure de Paris | Verdict | Ce qui avait été mergé avant |
| --- | --- | --- | --- |
| `34701437741` | 12/09/2026, 17 h 10 | **succès** | purge #839 (`#875`) |
| `34712936188` | 13/09/2026, ~02 h | **échec**, garde §3c | + #879, qui introduit `dedupliquer_appartenances` |

La garde comptait juste. C'est sa **relation** qui était devenue fausse : elle
déclarait `mandats` du pivot comme la somme de `mandats[]` et de
`mandat_europeen.mandats_europeens[]` du brut, ce qui suppose que chaque entrée
collectée est une entrée distincte. Depuis #879 elle ne l'est plus.

## 2. La mesure, reproduite avant d'être corrigée

Rejouée sur `origin/main` `7e48b4b05`, sans rien changer au corpus :

| Ce qui est compté | Profils | Entrées |
| --- | ---: | ---: |
| couples (profil, `mandats`) en déficit | **29** | **45** |
| appartenances que `dedupliquer_appartenances` écarte | **30** | **46** |
| profils en déficit sans réduction correspondante | **0** | — |

Les deux populations coïncident, à un profil près : `yannick-vaugrenard` porte
une réduction sans déficit, parce que la fusion additive lui a conservé un
mandat qu'une collecte antérieure avait rendu. Il sort donc en **excédent de
1**, rapporté, non bloquant — exactement ce que §3c prévoit pour la dérive de
fusion.

Les 29 profils sont ceux de l'issue, à l'entrée près : `jean-louis-bourlanges`
−4, `marielle-de-sarnez` −4, `marine-le-pen` −3, puis huit à −2 et dix-huit à
−1.

## 3. La décision

`Relation` porte un champ `reduction` optionnel, `Reduction(libelle,
justification, compter)`. `compter(raw_dir, slug)` rend le nombre d'entrées que
la normalisation écarte pour ce profil, et ce nombre se **soustrait** au compte
collecté.

Trois propriétés font que ce n'est pas une tolérance déguisée :

1. **C'est la même fonction, importée.** `audit_collecte_vs_publie` importe
   `dedupliquer_appartenances` et l'appelle. Un contrôle qui réimplémenterait le
   critère de #879 dériverait le jour où ce critère bouge — le mode de
   défaillance que `merge_profile._repli_texte_key` décrit déjà pour les clés de
   repli.
2. **Le seuil reste 0.** Une entrée qui n'est le doublon de rien reste un
   déficit, et bloque. Deux appartenances toutes deux classées sur la même
   période — membre et vice-président d'une commission — ne sont jamais
   réduites : ce sont deux faits (§2 règle 2).
3. **Elle se lit dans le rapport.** Le libellé de la relation devient
   `mandats + mandat_europeen.mandats_europeens − doublons du portail européen
   (#879)`, et la justification de la réduction est reprise dans la table des
   relations. Un garde-fou qui soustrait doit dire ce qu'il soustrait.

Le coût mémoire est borné et mesuré : la réduction est le seul endroit du module
où un fragment de document est matérialisé, et le crochet ne garde que les neuf
clés dont `dedupliquer_appartenances` a besoin. Sur le plus gros socle brut du
corpus — `helene-laporte.json`, 8,3 Mo — la lecture rend **26 entrées** en 0,1 s
pour un pic de 35 Mo de RSS.

## 4. L'alternative rejetée : `allow_declared_losses`

C'était le geste le plus court, et c'est le mauvais.
[`nettoyage-sediment-839`](nettoyage-sediment-839.md) §5 l'interdit
explicitement — « un écart, même d'une entrée, doit arrêter le run plutôt que
d'être déclaré ». Une tolérance de 45 aurait fait un trou de 45 entrées, de la
taille exacte de la marge, et aveugle à ce qui s'y serait glissé ensuite : c'est
la nature du trou dans lequel #540 a vécu, et que #545 a été écrit pour fermer.

## 5. L'alternative rejetée : dédupliquer à la collecte

Faire écarter les doublons par `candidate_profile_ue` avant l'écriture du brut
rendrait la somme exacte sans rien soustraire. Deux raisons de ne pas le faire.
Le brut est **source-near** : il dit ce que la source a rendu, y compris quand
elle se répète, et c'est ce qui permet de re-mesurer #879 plus tard. Et la
fusion des profils **bruts** est additive elle aussi
(`merge_profile.py:1515`) : les doublons déjà écrits ne partiraient jamais,
donc la correction ne corrigerait que les profils neufs — un corpus à deux
régimes, ce qui est pire que la soustraction.

## 6. Ce que ça laisse ouvert

La table `RELATIONS` ne porte qu'**une** réduction, et le test
`test_une_seule_relation_porte_une_reduction` le gèle : en ajouter une seconde
demande de la mesurer d'abord. Une réduction qu'on ajouterait sans mesure serait
la marge non attribuée que #545 refuse, avec un nom plus élégant.
