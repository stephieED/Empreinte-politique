<a id="stade-procedural-europeen-901"></a>
# Le stade d'un dossier européen se publie dans sa propre nomenclature, jamais traduit en stade français (#901) (2026-09-13)

`2026-09-13`

> **En bref** — les 383 textes portés européens publiaient `stade_procedural: null`, et le seuil de `AGENTS.md` §6 les écartait **tous** : `raphael-glucksmann` affichait « 0 publiés · 0 promulgué » en portant 23 textes. La source le publie pourtant. Mesuré le 13/09/2026 sur le dump `ep_dossiers` entier : **20 442 des 23 885 dossiers** portent un `procedure.stage_reached` (85,6 %), sur **16 valeurs**. `build_dossiers_index` le lisait — il lit déjà `procedure` pour en tirer `reference` et `title` — puis le jetait. Ce lot le conserve et le traduit vers une nomenclature **européenne** préfixée `ue_`, ajoutée au frozenset plutôt que rabattue sur les six stades français.

## 1. Pourquoi étendre, et non traduire

`KNOWN_STADES_PROCEDURAUX` portait six valeurs calquées sur la procédure française : `depose`, `examine_commission`, `inscrit_ordre_jour`, `discute_seance`, `adopte`, `promulgue`. Rabattre les seize valeurs européennes dessus était l'option la moins coûteuse, et elle est refusée sur un contre-exemple :

**« Procedure completed » n'est pas `promulgue`.** C'est le stade de 17 278 dossiers, et il recouvre l'adoption comme l'échec — « Procedure rejected » est une procédure achevée elle aussi, et la source la range à part. Traduire publierait comme adopté un texte qui a pu être rejeté (§2 règle 2).

Le préfixe `ue_` porte la provenance **dans la valeur** : le seuil §6, qui est un rang dans la liste française, ne peut pas s'appliquer à l'une d'elles par distraction. Deux tests le gèlent — les deux ensembles ne se recouvrent pas, et aucune valeur européenne n'est orpheline de la table de correspondance.

C'est le patron qu'`AGENTS.md` §4 impose déjà : *extend the frozenset, never bypass it*.

## 2. Les trois cas, et ils se déclarent tous

| Ce que la source donne | Ce qui est publié |
| --- | --- |
| un libellé connu | la valeur pivot, sans motif |
| **rien** — 14,4 % des dossiers | `null` + `{"motif": "source_sans_stade"}` |
| un libellé **inconnu de la table** | `null` + `{"motif": "stade_source_inconnu", "valeur_source": …}` |

Le troisième cas est celui qui compte pour la suite. Deviner rangerait un fait sous une étiquette choisie par ressemblance ; lever ferait tomber un run entier sur un libellé ajouté en amont. Conserver le libellé reçu est ce qui permettra de l'ajouter à la table — l'absence est **déclarée**, avec de quoi la résoudre.

## 3. Le cache aurait menti, et l'empreinte ne le couvrait pas

`_empreinte_perimetre` portait le périmètre dans le nom du fichier d'index — une leçon de #510 : un index construit pour 3 personnes et relu pour 7 rendrait quatre listes vides, et quatre listes vides se lisent comme quatre constats.

Elle ne couvrait pas le **schéma**. Quand une entrée gagne un champ, un cache écrit par la version précédente reste parfaitement lisible : il se relit sans erreur et rend le nouveau champ **absent partout**. Un `stade_source` manquant se serait lu « la source ne publie pas de stade » — exactement le contraire de ce que ce lot établit, et sans une ligne d'erreur.

D'où `VERSION_SCHEMA_INDEX`, versé dans le nom du fichier, à incrémenter à chaque changement de forme d'une entrée. Même geste que l'empreinte : **faire rater le cache plutôt que le faire mentir**. Un test vérifie qu'un cache de schéma antérieur est ignoré.

## 4. Ce que ce lot ne fait pas

**Le seuil §6 lui-même.** Il est implémenté côté interface, et l'issue le disait : cette moitié du point 3 n'est pas pour le pipeline. Ce lot rend la donnée disponible ; ce que l'interface en fait — publier un texte européen dès qu'il a un stade, plutôt qu'au-delà d'un rang français qui ne s'applique pas à lui — reste à décider là-bas.

**Le `sort`.** Le stade encode l'avancement, le sort l'issue, et #743 les a séparés pour cette raison. Le dump ne porte toujours aucune issue de dossier : `sort_non_resolu` reste `source_sans_sort`.

**Les deux autres manques de #901** — le `scrutin_id` des 11 013 votes et le `texte_vise` des 7 303 amendements. L'instruction a montré qu'ils existent aussi dans les dumps, à 100 % : `voteid` sur les 44 648 scrutins, `id` et `reference` sur les amendements. Ce sont deux lots à part, et le second demande en plus un index européen des scrutins sur le modèle de `pivot_data/scrutins.json`.

## 5. La mesure qui a changé en cours de route

La première lecture, sur les 20 000 premiers dossiers, donnait **15 valeurs** et **91,3 %** de couverture. Le dump entier en porte **23 885**, pour **16 valeurs** et **85,6 %**. La seizième — `Awaiting Council decision, 2nd reading` — apparaît **une fois**.

Un échantillon pris au début d'un dump ordonné n'échantillonne pas : il lit un début. La table de correspondance est écrite sur la mesure complète, et le test qui compte ses lignes cite les deux chiffres pour que l'écart reste visible.
