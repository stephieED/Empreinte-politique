# Un `groupe_id` porte toujours sa législature, et `succede_a` est une liste (#815)

`2026-09-10`

> **En bref** — préalable à la continuité des groupes XVe→XVIIe : **sept identifiants sur dix-huit ne portaient pas leur législature** (`AN:REN`, `AN:SOC`, `AN:RN`, `AN:LFI`, `AN:LR`, `AN:EPR`, `AN:DR`), héritage de l'ère NosDéputés où `groupes_reels.json` ne décrivait qu'une seule législature — **le format est une convention du dépôt, pas un champ de la source ; c'est le contexte qui rendait le suffixe inutile** —, et ça cesse de tenir dès qu'un sigle revient : déclarer `LR` de la XVe rend `AN:LR` ambigu et `DR-17.succede_a` pointe sur un sigle à deux fiches ; **un test figeait l'incohérence** (« le constat, figé plutôt que corrigé »), remplacé par l'invariant vérifié sur **toutes** les entrées ; `succede_a` passe en **liste non vide**, parce qu'une fusion a deux prédécesseurs et qu'une **scission** — `AD` quitte `DR` le 11/09/2024 pendant que `DR` poursuit — n'est pas un remplacement ; **le fichier porte deux listes** (`groupes[]`, seule à décider de ce qu'un run écrit, et `correspondance_sigles_an.groupes`) et n'en corriger qu'une ne se voyait pas — c'est le test de recopie qui l'a montré ; l'ancienne forme est **refusée nommément** aux deux étages plutôt que tolérée, et **le contrôle du portail a dû suivre** : il testait `isinstance(succede_a, dict)` et, laissé tel quel, n'aurait plus rien vérifié — un garde-fou muet, pas tolérant. Effet **prouvé** en rejouant `generate_group_profiles.py` sur `DR-17` : `AN:DR:17` + liste, schéma OK ; le portail rend **7 échecs durs** sur le corpus committé, état d'avant-run déjà connu de LaREM XVe. **Écarté** : accepter les deux formes — deux écritures du même fait dans un fichier relu à la main, et un validateur qui ne peut plus dire laquelle est la bonne. Suite complète à 4 372, 0 échec.

## Contexte

La propriétaire demande, le 10/09/2026, une **continuité par groupe entre la XVe
et la XVIIe** : une fiche par lignée, portant les étiquettes successives. La
session UI s'était arrêtée à deux maillons (`DR-17 → LR-16`) — non par erreur,
mais parce que le corpus s'arrête là.

Deux formes empêchaient d'aller plus loin, et aucune n'était un défaut tant que
personne ne remontait une lignée.

## Le premier : sept identifiants sans législature

`AN:REN`, `AN:SOC`, `AN:RN`, `AN:LFI`, `AN:LR`, `AN:EPR`, `AN:DR` — contre onze
autres qui portent la leur. Le suffixe n'a jamais été ajouté par principe,
seulement quand il fallait départager.

**C'est un héritage de l'ère NosDéputés**, et la datation le montre :
`groupes_reels.json` est créé avec cinq entrées XVIe et un `_meta` qui dit
encore « les données sources (NosDéputés.fr, NosSénateurs.fr) reflètent la
dernière composition connue avant la dissolution du 9 juin 2024 ». Le fichier ne
décrivait **qu'une** législature ; le sigle suffisait.

La nuance vaut d'être posée : ce n'est pas le **format** qui vient de
NosDéputés — `AN:REN` est une convention de ce dépôt, pas un champ de la source
— c'est le **contexte** qui rendait le suffixe inutile.

Ça cesse de tenir dès qu'un sigle revient. Déclarer `LR` de la XVe rend `AN:LR`
ambigu, et `DR-17.succede_a` pointe alors sur un sigle à deux fiches.

**Un test figeait l'incohérence** — `test_le_groupe_id_de_la_17e_casse_le_patron_chambre_sigle`,
« le constat, figé plutôt que corrigé ». Il était honnête tant que rien ne
remontait une lignée ; il est remplacé par l'invariant, vérifié sur **toutes**
les entrées et non sur les seules cinq de la XVIIe.

## Le second : un seul prédécesseur

`succede_a` décrit bien la succession simple. Il ne sait écrire ni une
**fusion** — deux groupes qui n'en font qu'un —, ni une **scission**, où le
sortant continue d'exister : mesuré, `AD` (`PO845520`) quitte `DR` le 11/09/2024
et devient `UDR`, pendant que `DR` poursuit. Aucun des deux ne succède à l'autre
au sens d'un remplacement.

## Décision

**`groupe_id` porte toujours `<chambre>:<sigle>:<législature>`**, et
**`succede_a` est une liste non vide de blocs**.

Deux choses valent d'être notées sur la mise en œuvre.

**Le fichier porte deux listes, et n'en corriger qu'une ne se voyait pas.**
`groupes_reels.json` a `groupes[]` — la seule qui décide de ce qu'un run écrit
(§4b) — et `correspondance_sigles_an.groupes`. Renommer dans la seconde laissait
la première désalignée ; c'est le test de recopie qui l'a montré, pas la
relecture.

**L'ancienne forme est refusée nommément**, à la configuration comme au schéma,
plutôt que tolérée. Un dict nu accepté en silence ferait cohabiter deux
écritures du même fait dans un fichier relu à la main.

**Le contrôle du portail a dû suivre.** `check_quality_gate` testait
`isinstance(succede_a, dict)` : laissé tel quel, il n'aurait plus rien vérifié
du tout — un garde-fou muet, pas un garde-fou tolérant. Il parcourt désormais la
liste, et **un seul** renvoi orphelin bloque.

## Effet vérifié

Le portail rend **7 échecs durs** sur le corpus committé : les sept fiches qui
portent un `succede_a` le publient dans l'ancienne forme, que le schéma refuse
désormais. **C'est un état d'avant-run, pas une régression** — le régime normal
d'une configuration changée, déjà connu de LaREM XVe la veille.

Prouvé plutôt qu'affirmé : `generate_group_profiles.py` rejoué sur `DR-17` et
son prédécesseur écrit

```
groupe_id : AN:DR:17
succede_a : [{"groupe_id": "AN:LR:16", "fichier": "groupe-AN-LR-16.json", …}]
validation : OK
```

Les fiches de groupe sont régénérées **à chaque run**, avant le portail — vérifié
sur le run `34377413730`, où `generate_group_profiles.py` réécrit les 20 fiches
à 17:41 et le portail les relit à 17:44.

## Ce que ce lot ne fait pas

- **Il ne déclare aucune fiche.** `LR-15`, `GDR-17` et `EcoS-17` sont le lot
  suivant ; celui-ci n'est que leur préalable.
- **Il ne touche pas `historique_noms`**, vide sur les 20 fiches publiées et
  décrit dans `group_profile.py` comme « laissé à renseigner manuellement ».
  C'est le champ qui porterait les renommages **à l'intérieur** d'une
  législature — `UMP` → `Les Républicains` en XIVe, `SOC` → `SER`, la série
  `LC` → `UDI-AGIR` → … en XVe. Distinct de `succede_a`, et à instruire à part.
- **Il ne corrige pas les commentaires de `web/UI_finale/src/utils/groupe.js`**,
  qui citent `AN:LR`, `AN:REN`, `AN:SOC` dans des docstrings. Aucun n'est du
  code — l'UI lit `groupe.groupe_id` et le compare à un manifeste issu des mêmes
  données, donc le renommage est cohérent de bout en bout — mais une autre
  session tient ces fichiers.

## Alternative écartée

**Accepter les deux formes**, chaîne et liste, pour éviter de toucher aux fiches
publiées. C'est le geste qui ne casse rien aujourd'hui et qui rend la règle
inapplicable demain : deux écritures du même fait dans un fichier relu à la
main, et un validateur qui ne peut plus dire laquelle est la bonne. Le corpus se
régénère à chaque run — il n'y a pas de dette à porter, seulement un run à
attendre.
