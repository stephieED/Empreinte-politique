<a id="collecte-interventions-reduite-au-theme-657"></a>
# La collecte d'interventions des membres de roster est réduite au thème (#657) (2026-08-31)

`2026-08-31`

> **En bref** — l'« empreinte thématique » d'une fiche de groupe était celle d'UNE personne (470 étiquettes sur `AN:RN` portées par Marine Le Pen, 382 sur `AN:SOC` par Jérôme Guedj, 0 sur `AN:LFI` et `AN:LR`), parce que `tags_thematiques` dérive intégralement d'`interventions[]` et que les 468 membres de roster publiaient `interventions: []` — le motif écrit de #357, « aucun agrégat ne les consomme », était faux ; `--interventions-theme-seul` collecte les débats **sans leur verbatim** et laisse les questions officielles (qui ne portent aucun thème), chaque entrée publiée déclarant sa forme par `collecte: "theme_seul"` — les champs absents le sont, jamais publiés à `null`, un `"texte": null` étant un fait sur la personne là où le fait porte sur le run ; mesuré sur les 468 membres, législatures 16+17 : **139,0 Mio publiés au lieu de 413** (383 o/entrée contre 1 138), index de cache **194,2 Mio au lieu de 798**, parcours **38,9 s au lieu de ~93**, et **aucune étiquette perdue** — `sujet` vient du titre de point, les deux modes indexant 287 789 et 305 862 entrées au nombre près ; l'empreinte de `AN:LFI` passe de 0 à 1 981 étiquettes portées par 76 membres sur 76, celle d'`AN:REN` de 197 (1 porteur) à 3 943 (192 sur 193) ; six garde-fous, dont l'index réduit dans un répertoire DISTINCT (#447 transposé au contenu d'une entrée), l'exemption des candidats déclarés (la fusion additive gèlerait leur forme complète) et le repli par provenance de `couverture_profil` qui ne s'applique plus qu'aux 19 profils sans `meta.collecte_ecartee` ; la réduction des 16 242 entrées déjà publiées est **mesurée et non faite** (21,3 → 5,5 Mio) parce que 665 de leurs 1 331 étiquettes viennent exclusivement du repli `mots_cles` ; la 15e législature n'étant pas mesurable, tous ces volumes sont un plancher (204 des 468 membres y ont voté).

Arbitrage rendu le 31/08/2026 : ni retirer la section « empreinte thématique »
des fiches de groupe, ni la requalifier — **peupler la donnée qui lui manque**,
sans en payer le prix complet.

## Le constat, mesuré

`tags_thematiques` dérive **intégralement** d'`interventions[]`
(`normalize_profil` : `theme_officiel` du compte rendu quand l'intervention en
porte un, `mots_cles` sinon), et `tags_thematiques_agreges` de chaque fiche de
groupe en dérive à son tour. Or les **468 membres de roster publiaient
`interventions: []`**, la collecte en étant écartée en dur par #357.

L'« empreinte thématique » d'un groupe était donc celle d'**une seule
personne** :

| Fiche | Étiquettes publiées | Membres porteurs |
| --- | ---: | ---: |
| `AN:RN` | 470 | 1 / 90 |
| `AN:SOC` | 382 | 1 / 31 |
| `AN:REN` | 197 | 1 / 193 |
| `AN:LFI` | 0 | 0 / 76 |
| `AN:LR` | 0 | 0 / 62 |

Le motif écrit de #357 — « les interventions ne sont consommées par aucun
agrégat de groupe » — était **faux**. Il l'est resté trois mois parce que la
dérivation traverse deux étages : personne ne relit `normalize_profil` en
décidant ce qu'un job d'extraction collecte.

## La décision

**Collecter, pour les membres de roster, ce qui porte le thème — pas le
verbatim.** Un drapeau, `--interventions-theme-seul`, et une entrée publiée qui
**déclare** sa forme.

```json
{"intervention_id": "syceron_CRSANR5L17S2026O1N187_000399",
 "date": "2026-03-31", "type_detail": "loi",
 "theme_officiel": "Projet de loi de finances rectificative",
 "source_url": "https://data.assemblee-nationale.fr/.../syseron.xml.zip",
 "source": {"type": "syceron", "url": null, "source_id": null, "legislature": "17"},
 "collecte": "theme_seul"}
```

Les champs absents ne sont **pas publiés à `null`** : ils sont absents, et
`collecte` dit pourquoi. Un `"texte": null` se lirait « cette prise de parole
n'a pas de verbatim » — un fait sur la personne — là où le fait porte sur le
run (AGENTS.md §2 règle 5). Mesuré : 90 octets de `null` par entrée × 380 800
entrées, pour une phrase fausse. `collecte` est une valeur **fermée**
(`KNOWN_COLLECTES_INTERVENTION`), et son **absence** est la forme complète : une
clé toujours présente rendrait les 16 242 entrées déjà publiées rétroactivement
« non déclarées ».

## Ce que ça coûte, mesuré le 31/08/2026

Sur les **468 membres de roster**, législatures 16 et 17 (la 15e n'est pas
mesurable : son cache local est un téléchargement interrompu, et **204 des 468
membres y ont voté** — les volumes ci-dessous sont donc un **plancher**).

| | Forme complète | Réduite au thème |
| --- | ---: | ---: |
| Volume publié, 380 800 entrées | 413 Mio (1 138 o/entrée) | **139,0 Mio (383 o/entrée)** |
| Index de cache, législatures 16+17 | 798 Mio (1 410 o/entrée) | **194,2 Mio (343 o/entrée)** |
| Parcours + écriture d'index, 16+17 | ~93 s | **38,9 s** |
| Lecture des tranches + normalisation, 468 membres | 18,0 s | **5,2 s** |
| RSS de pointe de la construction (16+17 cumulés) | non remesuré | 326 Mo |

`pivot_data/profiles/` passe de **622,2 à 763,4 Mio** (+22,7 %) et le plus gros
profil de 6,8 à **11,39 Mio** — le seuil bloquant de `garde_fou_blobs` est à
80 MiB, il n'est pas approché.

**Le ×35 redouté par l'arbitrage n'existe pas.** L'index Syceron se construit
**une fois par législature**, sous verrou réentrant, et se lit **une tranche par
membre** : le parcours ne dépend pas du nombre de membres. Ce que la réduction
achète n'est donc pas du temps de collecte, c'est du **volume publié** et de
l'**index**.

## Ce que ça rend

| Fiche | Étiquettes avant | Porteurs avant | Étiquettes après | Porteurs après |
| --- | ---: | ---: | ---: | ---: |
| `AN:REN` | 197 | 1 / 193 | **3 943** | 192 / 193 |
| `AN:RN` | 470 | 1 / 90 | **2 567** | 90 / 90 |
| `AN:LR` | 0 | 0 / 62 | **2 267** | 62 / 62 |
| `AN:LFI` | 0 | 0 / 76 | **1 981** | 76 / 76 |
| `AN:SOC` | 382 | 1 / 31 | **1 401** | 31 / 31 |
| `Senat:LR`, `Senat:SER` | 0 | — | inchangé | — |

448 des 468 membres reçoivent au moins une intervention ; 4 623 étiquettes
distinctes sur l'ensemble. Les deux fiches sénatoriales ne bougent pas : leur
extraction est suspendue (#516) et le Sénat est hors périmètre (#528).

`theme_officiel` est renseigné sur **91,8 % des 380 800 entrées** des membres de
roster, contre 45,6 % des 16 242 entrées publiées des 13 candidats. Les deux
populations ne se contredisent pas : celle des candidats contient 4 299
questions officielles, qui ne portent aucun thème.

**Ce sont des libellés bruts, pas une taxonomie** — « projet de loi de
financement rectificative… », « a69 », « abattement ». Les huit thèmes stables
de `STABLE_THEMES` restent un chantier distinct, différé par #324. Une collecte
élargie donne plus de libellés bruts, pas un classement.

## Les six garde-fous, et pourquoi chacun existe

**1. Les questions officielles ne sont pas collectées en mode réduit.** Elles ne
portent ni `seance_ref` ni `session_ref`, donc `theme_officiel` y est `None`, et
leur `mots_cles` est vide par construction : elles ne rendent **pas une seule**
étiquette. Elles sont en revanche le seul poste réseau du chemin interventions
qui grandisse avec le nombre de membres.

**2. `format` tombe à `null`, pas à `"reaction_courte"`.** Il se déduit du
nombre de mots du verbatim ; sans verbatim, la valeur par défaut serait un
défaut déguisé en mesure, sur la totalité du corpus réduit.

**3. Les deux index vivent dans deux répertoires** (`index_par_acteur` et
`index_par_acteur_theme`). C'est #447 — « un répertoire qui existe n'est pas la
preuve de ce qu'il contient » — transposé du format d'une clé au contenu d'une
entrée. La lecture est **asymétrique** : le mode réduit sait lire l'index
complet et en jeter les champs lourds, l'inverse est interdit. C'est ce qui
évite toute reconstruction en CI, `extract-an` publiant l'index complet avant
que la matrice roster ne démarre (`needs:`). Le mémo de process porte la forme
dans sa clé, pour la même raison.

**4. Un candidat déclaré n'est jamais collecté en réduit.** Un candidat qui
siège dans un groupe figure dans les **deux** listes — `generate_roster_candidats`
ne l'en retire pas, et `merge_pivot_profile` ne rétrograde jamais sa provenance
(#189). Le réduire ici gèlerait ses interventions à cette forme pour toujours
(fusion additive, l'**ancienne** entrée gagne sur la même `intervention_id`), et
pourrait remplacer la forme complète déjà publiée si son artifact l'emporte au
`merge-multiple` (#450, encore ouvert pour les slugs des deux populations). Le
run les **écarte** donc plutôt que de les réduire, et le dit ligne par ligne.

**5. `couverture` cesse de mentir sur une liste pleine.** `couverture_profil.deriver`
repliait sur la provenance — un profil `roster_groupe` héritait de
`DECISIONS_ROSTER`, donc de `non_collecte`/`par_decision` sur ses interventions.
Sur une liste désormais peuplée, la preuve aurait nommé un drapeau que le run
n'a pas passé : le contresens exact que #539 combat, retourné. Le repli ne
s'applique plus que si le run **n'a rien déclaré**, c'est-à-dire si
`meta.collecte_ecartee` est absent — 19 des 468 profils publiés, ceux d'avant
#539. La condition porte sur la **présence** de la clé : `[]` est une
déclaration (« ce run n'a rien écarté »), son absence n'en est pas une.

**6. La clé de cache du job roster porte l'empreinte de complétude.** Elle ne
portait que la semaine, alors qu'`extract-an` en mode interventions ne sauvegarde
que sous `-interv-<empreinte>` : la clé nue de la semaine, écrite par n'importe
quel run en mode par défaut, faisait un *exact key hit* — et `restore-keys`
n'est pas consulté après un hit exact. Les 8 shards seraient repartis d'une
entrée **sans contenu Syceron** et auraient reconstruit les trois index chacun.
C'est #424/#505 sous une troisième forme ; elle n'avait pas de coût tant que ce
job ne lisait pas l'index, elle en a un maintenant.

## Ce qui n'est pas fait, et pourquoi

**La forme publiée des 16 242 interventions des 13 candidats n'est pas touchée.**
Mesuré : la même règle de réduction les ferait passer de **21,3 à 5,5 Mio**
(−74,0 %). Ce n'est pas fait, et ce n'est pas seulement une question de
périmètre :

- **665 des 1 331 étiquettes publiées de ces 13 profils viennent EXCLUSIVEMENT
  du repli `mots_cles`** (666 viennent de `theme_officiel`). Réduire ces entrées
  ferait tomber `tags_thematiques` de moitié — une **baisse sur une liste
  surveillée**, que `audit_diff_profils` bloque, et à raison ;
- `theme_officiel` n'y couvre que 45,6 % des entrées, contre 91,8 % côté
  roster ;
- le verbatim et les `reponse` des questions officielles y sont de la donnée
  publiée, collectée, et qu'aucune décision n'a demandé de retirer.

**Le poste dominant du volume n'est pas le verbatim.** Ventilation des 16 242
entrées publiées : `texte` 46,3 %, `dossier` 8,6 %, `source_url` 8,0 %, `source`
7,5 %, `reponse` 6,1 %, `sujet` 4,1 %. Sur les 380 800 entrées projetées pour
les membres de roster, `texte` ne pèse que **29,3 %** : les 70,7 % restants sont
de la **traçabilité recopiée à chaque entrée**. C'est le motif exact que
#431/#432 ont réglé pour les amendements et les scrutins — un mapping dans le
profil, un index partagé dans `pivot_data/`. Un tel index ramènerait l'entrée
réduite de 383 à ~246 octets (98,3 Mio au lieu de 139,0 pour les 468 membres, et
3,8 Mio au lieu de 5,5 pour les candidats). **Ce n'est pas ce lot** : il change
la forme d'un champ publié sur une liste surveillée, et rien ne l'a arbitré.

**`source_url` est donc conservée dans l'entrée réduite**, alors qu'elle pèse
112 octets et que l'archive est la même pour toute la législature. Elle est le
seul champ qui rende l'entrée publiée autosuffisante au sens de la règle 2 ; la
retirer laisserait le lecteur avec une règle de dérivation (`legislature` →
URL) qui ne vit que dans notre code, sans l'index publié qui justifie
l'indirection chez #431/#432.

**Rien n'est affiché.** #594 et #657 actent que la section ne doit pas être
montrée en l'état — 470 étiquettes portées par une personne sur 90 ne sont pas
l'empreinte d'un groupe, et une absence se lirait « ce groupe n'a pas de
thème ». Ce lot peuple la donnée ; l'affichage est un autre lot.

## Alternative écartée

**Collecter la forme complète pour les membres de roster.** 413 Mio au lieu de
139, un index de 798 Mio au lieu de 194, et 93 s de parcours au lieu de 39 —
pour un verbatim qu'aucun agrégat de groupe ne lit et qu'aucune fiche n'affiche.
La réduction n'a coûté **aucune étiquette** : `sujet` et `type_detail` viennent
du titre de point, jamais du texte, et les deux modes indexent exactement le
même nombre d'entrées (287 789 pour la 17e, 305 862 pour la 16e).

## La réserve qui reste

**La 15e législature n'est pas mesurée.** Son cache local est un
`syseron.xml.zip.part` de 3 Mo, téléchargement interrompu, et rien n'a été
retéléchargé pour ce lot. Elle porte à elle seule ~633 764 des 1 227 415
interventions indexables des trois archives, et **204 des 468 membres de roster
y ont voté** : tous les volumes de cette décision sont un **plancher**, à
remesurer au premier run réel qui l'engage.
