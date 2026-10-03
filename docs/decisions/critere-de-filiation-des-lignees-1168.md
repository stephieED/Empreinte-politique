<a id="critere-de-filiation-des-lignees-1168"></a>
# Le critère qui pourrait relier deux groupes successifs : le plus petit des deux, à 50 % (#1168) (2026-10-02)

`2026-10-02`

> **En bref** — les 17 liens `succede_a` qui composent les 12 lignées sont écrits à la main, et aucune source ne les déclare : ni l'Assemblée (les 63 organes `GP` d'AMO30 ne portent aucune clé de succession, `organePrecedentRef` existant sur dix autres types), ni Wikidata (19 des 48 groupes AN portent « remplace », **tous sur des lignées historiques**, aucun sur la période publiée) ; **arbitré : la comparaison des membres, avec le PLUS PETIT des deux groupes pour base et un seuil de 50 %** — sur le corpus, **19 liens déclarés retrouvés sur 19, aucun proposé à tort**, les trois filiations refusées le 11/09 restant écartées. **Rien n'est implémenté** : la décision porte sur le critère, pas sur son usage.

## 1. Pourquoi un critère, et pas une source

Cherché le 02/10/2026, et consigné dans #1168 :

| Source | Ce qu'elle porte |
| --- | --- |
| Référentiel AMO30 | 63 organes `GP`, **aucune clé de succession**. `organePrecedentRef` existe sur dix autres types (758 ministères, 58 partis, 10 groupes du **Sénat**…) — et vaut `None` sur les dix groupes sénatoriaux |
| Wikidata | `P1365`/`P1366` sur **19 des 48** groupes de l'AN, mais uniquement sur les lignées historiques (`UNR → UDR → RPR → UMP → LR`, la chaîne socialiste). **Aucun groupe de la période publiée.** Et aucun identifiant d'organe AN pour relier : le rapprochement serait par nom, ce que #753 a refusé |
| Journal officiel | **0 acte sur 10 032** dans les six mois d'ouverture des trois législatures. Notre collecte porte les actes réglementaires ; les déclarations politiques de groupe sont ailleurs dans le JO, hors périmètre — **non instruit** |

La phrase de #700 — « l'Assemblée ouvre et ferme des organes, elle ne les chaîne
pas » — est donc confirmée **au-delà** de l'Assemblée.

## 2. Le critère arrêté

Pour chaque couple de groupes de deux législatures consécutives : les personnes
communes, divisées par l'effectif du **plus petit des deux**, et le lien est
retenu à partir de **50 %**. Tous les candidats qui passent le seuil, pas
seulement le meilleur.

| | Résultat sur les XVe-XVIIe |
| --- | --- |
| Liens déclarés retrouvés | **19 / 19** |
| Manqués | **0** |
| Proposés à tort | **0** |
| Plus bas retrouvé | 55 % (`SOC-15 → SOC-16`) |
| Plus haut écarté | 36 % (`UDI-AGIR-15 → LIOT-16`) |

## 3. Pourquoi cette base, et pas une autre

Deux critères ont été écartés **sur mesure**, et c'est la propriétaire qui a
trouvé celui qui marche :

| Base | Plus bas déclaré | Plus haut écarté | Marge | Fusions |
| --- | ---: | ---: | ---: | --- |
| les membres du groupe de départ | 33 % | 28 % | 5 pts | ratées |
| ses **réélus** | 87 % | 75 % | 12 pts | ratées |
| **le plus petit des deux** | **55 %** | **36 %** | **19 pts** | **retrouvées** |

**Son objection, qui a tout décidé** : *« un critère en pourcentage peut être
faussé si le nombre de membres bouge beaucoup d'une législature à l'autre. »*
Elle est fondée — le taux de réélection va de **38 % à 89 %** selon le groupe, et
LAREM, qui perd 62 % de ses sièges, sortait à 33 % sans qu'aucune rupture de
filiation l'explique.

Prendre le plus petit des deux **règle le défaut à la racine au lieu de le
compenser** : quand un groupe s'effondre, c'est l'arrivée qui devient la base, et
l'arrivée ne contient que des élus. Plus besoin de la notion de réélection.

Et **le seuil de 50 % est le sien**, choisi pour sa défendabilité publique :
*« plus de la moitié du plus petit des deux groupes se retrouve dans l'autre »* se
dit en une phrase dans la méthodologie, là où un seuil calibré demande un
paragraphe.

## 4. Deux effets qu'aucun des autres critères n'avait

**Les successions multiples passent.** En retenant tous les candidats au-delà du
seuil, les deux fusions que la table déclare sortent d'elles-mêmes :
`DEM-15` **et** `MODEM-15` → `DEM-16` (59 % chacun), et les deux organes
`SOC`/`SOC-A` de la XVIe → `SOC-17` (87 %).

**Le même calcul vaut DANS une législature, et il y est plus net.** 26 couples
d'organes consécutifs d'une même législature : les renommages sortent à
**81-100 %** (`AD → UDR`, `SOC → SOC-A`, `MODEM → DEM`), les scissions à **43 %
et moins** — **38 points** de marge, contre 19 entre législatures. C'est
structurel : sans élection entre les deux organes, un renommage ne perd personne.

## 5. Aucune exemption par le sigle

Question posée, et **écartée** : ne mesurer que les liens dont les sigles
diffèrent. Nos sigles sont stables **parce que la table relue les a normalisés**
(`LFI-NUPES → LFI-NFP` devient `LFI → LFI`) : exempter un lien parce que le sigle
ne change pas revient à se fier à la table pour décider qu'on n'a pas besoin de la
vérifier. Et ça désarmerait la détection d'un lien déclaré que la composition ne
soutient plus — personne ne va rouvrir `RN → RN`.

**Le sigle reste un signal de lecture** : un lien à sigle identique qui rate le
seuil est ce qu'un audit doit signaler en premier.

## 6. Ce que la décision ne tranche pas

**Proposer ou publier.** La mesure fonde la proposition ; publier demanderait de
trancher ce qu'écrit `etabli_par` — ni `relecture_humaine`, qui deviendrait faux,
ni une `source_url`, que `validate_profil_groupe` refuse (#700). Ouvert dans
#1168.

**Et ce qui n'est pas démontré** : 19 liens sur 3 législatures. La séparation est
parfaite sur ce corpus, pas au-delà. Quatre liens reposent sur moins de 20
personnes, où une défection vaut 9 points — le dénominateur devra s'afficher
partout où le taux s'affiche (§2 règle 7).

**Un constat de passage, sur la table** : `NG → SOC` est un renommage **dans** la
XVe (organes contigus, 91 %) déclaré comme une succession entre groupes. Rien de
publié n'est faux ; les deux notions sont mélangées sur ce cas.
