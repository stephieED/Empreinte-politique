# Les dix lignées sont écrites, et une mesure corrige le motif du recalcul (#836)

`2026-09-11`

> **En bref** — #836 avait posé le schéma et la composition, sans ce qui les appelle : `pivot_data/lignees/` était vide. Ce lot livre `generate_lignee_profiles.py`, son step CI, la §4c du portail, la collection `lignees` du contrôle de perte, et les **dix `lignee_id`** déclarés dans `raw_data/groupes_reels.json`. **La mesure a corrigé le motif** : la somme des maillons et le recalcul depuis les profils coïncident **exactement sur neuf lignées sur dix** — `88 709 → 60 897` amendements distincts sur la seule socialiste, et `20 524 → 16 420` scrutins sur la seule socialiste également. Le ×2,82 de l'issue datait d'**avant #821** ; depuis que chaque maillon ne compte que sa période, deux maillons de législatures différentes portent des `amendement_id` disjoints **par construction**, et le seul recouvrement du corpus vient des deux maillons d'une **même** législature, `NG:15` et `SOC:15`. Le recalcul n'est donc pas un correctif, c'est ce qui **vérifie à chaque run** que la propriété tient — et la seule voie correcte le jour où deux maillons se partagent à nouveau une législature. L'identifiant est **déclaré** sur chaque entrée de `groupes[]`, la chaîne reste écrite **une seule fois** dans `succede_a`, et un contrôle refuse qu'elles se contredisent : c'est cette porte qui tient la **scission** `AD`/`DR` tant que sa forme n'est pas tranchée (#815). Deux défauts trouvés en écrivant l'appelant : `recalculer_agregats` publiait `nb_amendements_sans_identifiant` là où toute la chaîne lit `nb_sans_identifiant`, sans `signatures` ni `taux_adoption` — **elle n'était couverte par aucun test** —, et elle chargeait tous les profils d'une lignée avant d'agréger, soit l'OOM de #377 un étage plus haut sur les **660** couples de la lignée macroniste. Coût mesuré : **104 s et 1 453 Mio de RSS** pour les dix, **37 Mo** sur disque en écriture compacte contre 53 indentée. Suite complète à **4 492**, 0 échec.

## Ce que la mesure a changé au motif

L'issue #836 annonçait un facteur **×2,82** sur `amendements_agreges` — 281 301
pour la somme des quatre maillons socialistes contre 99 577 en union. Mesuré ici
sur le corpus du 11/09/2026, celui qui porte #821 et #825 :

| Lignée | Somme des maillons | Recalcul depuis les profils |
| --- | ---: | ---: |
| `NG:15 → SOC:15 → SOC:16 → SOC:17` | 88 709 | **60 897** |
| `LR:15 → LR:16 → DR:17` | 133 665 | 133 665 |
| `LAREM:15 → REN:16 → EPR:17` | 129 429 | 129 429 |
| `FI:15 → LFI:16 → LFI:17` | 119 763 | 119 763 |
| `GDR:15 → GDR:16 → GDR:17` | 42 974 | 42 974 |
| `RN:16 → RN:17` | 34 150 | 34 150 |
| `ECOLO:16 → ECOS:17` | 31 363 | 31 363 |
| `EDS:15` | 25 903 | 25 903 |
| `Senat:LR`, `Senat:SER` | 0 | 0 |

**Neuf lignées sur dix coïncident au chiffre près.** Ce n'est pas une propriété
de la lignée, c'est un acquis de #821 : la législature se lit sur
l'`amendement_id`, et deux maillons de législatures différentes ne peuvent pas
porter le même. Le seul recouvrement du corpus est celui de deux maillons d'une
**même** législature — `NG:15` et `SOC:15`, la XVe scindée en deux organes — et
c'est exactement là que la somme se trompe, de 27 812 amendements.

La cohésion dit la même chose : `20 524 → 16 420` sur la socialiste, **somme =
union sur les neuf autres**.

**Ce qui aurait été faux, et que la mesure a interdit** : conclure du ×2,82 de
l'issue que l'agrégat des maillons est structurellement inutilisable, et
retirer `amendements_agreges` des fiches de groupe. Il est juste ; c'est la
somme *entre maillons* qui ne l'est qu'à une condition, et cette condition se
vérifie au lieu de s'espérer.

## L'identifiant est déclaré, la chaîne est écrite une fois

`lignee_id` est déclaré sur chacune des 23 entrées de `groupes[]`, pour dix
valeurs ; `lignees[]` porte l'identité de chaque lignée — nom de lecture,
chambre, fichier, date de relecture. La **chaîne**, elle, reste écrite une seule
fois, dans `correspondance_sigles_an.groupes[].succede_a`.

Les deux disent le même fait par deux chemins, et rien n'obligerait un humain à
les garder d'accord — sinon `verifier_partition`, qui refuse qu'une succession
traverse deux lignées, et le test qui recalcule les composantes connexes sur la
configuration committée. **23 fiches publiées, 10 composantes**, soit exactement
les dix lignées déclarées.

C'est le défaut de #815, où le fichier portait deux listes et où n'en corriger
qu'une ne se voyait pas. La réponse n'est pas de n'écrire qu'une seule des deux
— l'identifiant ne se dérive pas de la chaîne, sous peine de bouger le jour où
un maillon antérieur est ajouté — mais de les **confronter**.

### La scission échoue au lieu d'être absorbée

`AD` quitte `DR` le 11/09/2024 pendant que `DR` poursuit. Aucun des deux ne
succède à l'autre au sens d'un remplacement, et la façon de l'écrire n'est pas
tranchée (#815, #836). Déclarer `UDR` avec un `succede_a` vers `DR:17` produit
aujourd'hui un **refus nommé** plutôt qu'une lignée qui absorberait un groupe
n'ayant succédé à personne. La porte est là avant le cas, et non après.

## Deux défauts de la brique, trouvés en écrivant ce qui l'appelle

`recalculer_agregats`, livrée la veille, n'était appelée par rien et **testée
par rien** — le fichier de tests de #836 ne la nomme pas.

1. **Un même fait sous deux noms.** Elle publiait
   `nb_amendements_sans_identifiant` là où la fiche de groupe, l'audit et le
   contrôle de perte lisent `nb_sans_identifiant` ; et ni `signatures` (§6), ni
   `taux_adoption`, ni les deux compteurs d'écartés de #821. Elle est
   réécrite pour **déléguer à `_aggregate_amendements`**, la fonction même de la
   fiche de groupe : un second calcul publierait les mêmes chiffres sous
   d'autres noms.
2. **Tout charger avant d'agréger.** Sa signature prenait les profils déjà
   lus, par maillon. La lignée macroniste en compte **660** couples (membre,
   législature) pour 446 personnes, et garder les documents entiers coûtait
   0,9 à 1,1 Gio pour **une seule** fiche de groupe (#635) : c'est l'OOM de
   #377 reconstitué un étage plus haut. Elle reçoit désormais des profils
   **projetés**, chargés un à un avec le cumul partagé de la lignée.

Le cumul partagé est aussi ce qui rend le compte en amendements **distincts** et
non en signatures (#643).

## Un couple (membre, législature) par lecture

Deux maillons d'une même législature ne doivent pas faire lire deux fois les
mêmes amendements ; deux maillons de législatures différentes doivent au
contraire être lus deux fois, chacun avec **sa** législature, sans quoi le
filtre de #821 ne s'arme pas. D'où la déduplication sur le couple, et non sur le
membre : 140 lectures pour 170 entrées de maillon sur la socialiste.

## Compact, parce que le critère est « relu à la main »

Une fiche de lignée est l'union de ses maillons : `AN:LIGNEE:REN` pèse **11,5
Mo** indentée, dont 5,0 de `cohesion_votes` et 2,7 de `mandats_agreges` — 53 Mo
pour les dix, **37 en compact**. #433 range `pivot_data/groupes` en indenté
parce que ces fiches sont « effectivement relues à la main lors des audits » :
personne n'ouvre un document de 11 Mo, et son diff est « une seule ligne
changée » dans les deux formats. Ranger la nouvelle collection avec sa voisine
aurait appliqué la **liste** au lieu du **critère**.

## Ce qui bloque, et ce qui ne bloque pas

Le step CI est `continue-on-error`, même arbitrage que le step gouvernement
(#427) : un défaut de lignée ne doit pas coûter au run le commit des profils et
des fiches de groupe, qui sont corrects. Le prix en est qu'une fiche **périmée**
resterait committée sans que rien ne bloque — le contrôle de perte ne voit que
les disparitions, et un fichier périmé n'a pas disparu.

C'est pourquoi la **§4c du portail hard-faile** sur une fiche de lignée absente,
illisible ou invalide, et pourquoi le script **refuse une lignée amputée** : un
maillon déclaré sans fiche publiée sort des chiffres plus petits sans que rien
ne le dise. Une configuration ou une partition fausse n'écrit **aucune** fiche —
écrire les neuf autres laisserait croire que la déclaration tient.

## Écarté

- **Un dernier tour dans `generate_group_profiles.py`.** Économiserait le
  rechargement de l'index des amendements — 4,3 s et 745 Mio mesurés. Mais ce
  script sort en 2 quand un roster tombe, et il faudrait décider au milieu d'une
  fonction si la lignée se calcule quand même. Deux sorties, deux répertoires,
  deux codes de retour : c'est déjà la règle de `generate_gouvernement_profiles.py`.
- **Dériver `lignee_id` des composantes de `succede_a`.** Supprimerait la
  confrontation… en supprimant l'un des deux témoins. L'identifiant bougerait le
  jour où MoDem, Horizons, LIOT ou UDR sont déclarés, et un identifiant qu'une
  collecte déplace casse les liens du site.
- **Publier `lignee_nom` par maillon plutôt qu'une fois par lignée.** Le nom
  serait écrit quatre fois pour la socialiste, dans un fichier relu à la main.

## Ce que ce lot ne fait pas

- **Les quatre lignées manquantes** — MoDem, Horizons, LIOT, UDR (#815). La
  dernière est une scission, et sa forme reste à trancher.
- **Le §1 « qui sont-ils » de la maquette**, qui est un sujet de vue.
- **Les fiches elles-mêmes ne sont pas committées ici** : elles paraissent au
  prochain run, comme toute donnée du dépôt.
