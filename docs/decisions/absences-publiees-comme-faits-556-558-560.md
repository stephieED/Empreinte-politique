<a id="absences-publiees-comme-faits-556-558-560"></a>
<a id="marqueur-nil-identite-556"></a>
<a id="groupe-gele-couverture-558"></a>
<a id="frontiere-vs-panne-560"></a>
# Trois absences publiées comme des faits (#556, #558, #560) (2026-08-29)

`2026-08-29`

> **En bref** — une absence décidée, bornée par la source ou marquée en XML n'est pas un fait ; filtrage à la lecture, pas champ par champ.

Un seul lot pour trois issues, et pas par commodité : elles partagent
`src/candidate_profile.py` et `src/couverture_profil.py`, et surtout la **même
faute de fond**. Une absence produite par une **décision**, par une **frontière
de source** ou par un **marqueur XML** était publiée comme un **fait** — le
contresens exact que [#couverture-listes-539](couverture-listes-539.md) existe
pour empêcher. Trois PR séparées seraient entrées en conflit sur les mêmes
lignes.

| Issue | Ce que la page disait | Ce qui est vrai |
| --- | --- | --- |
| #556 | `identite.uri_hatvp` = `{"@xsi:nil": "true"}` — **191 profils sur 481** | AMO30 dit « pas de déclaration HATVP » : c'est `null` |
| #558 | « couvert » sur les listes vides de **20 sénateurs** | l'extraction de leur groupe est gelée (#516/#528) |
| #560 | `non_collecte` / `panne` sur les interventions de **2 profils** | Syceron commence à la XVe, leurs mandats sont antérieurs |

---

## A. Le marqueur d'absence d'AMO30 était publié comme une valeur (#556)

### Ce que la mesure a changé à l'énoncé du problème

L'issue portait sur un champ. La mesure du 29/08/2026, en croisant
`raw_data/profiles` et `pivot_data/profiles` sur les 481 profils publiés, en a
trouvé **trois** :

| Champ publié | Profils | Forme publiée |
| --- | ---: | --- |
| `identite.uri_hatvp` | **191** | l'objet marqueur, tel quel |
| `identite.profession` | **20** | l'objet marqueur, tel quel |
| `identite.lieu_naissance` | **28** | le `repr` Python du marqueur, **en chaîne** |

Le troisième est le pire, et c'est lui qui a décidé de la forme du correctif.
`_format_lieu_naissance` **interpole** ses arguments : un marqueur qui l'atteint
ne ressort pas en `dict` repérable mais en **chaîne**, qu'aucun
`isinstance(..., str)` en aval ne peut plus rattraper. **18 profils publient un
lieu de naissance intégralement fait de plomberie XML** —
`"{'@xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance', '@xsi:nil': 'true'} ({…})"` —
et 10 autres une ville suivie d'un marqueur entre parenthèses.

Un dict truthy se repère. Une chaîne non vide se lit comme une donnée.

### La décision : filtrer à la LECTURE, pas champ par champ

Le convertisseur XML → JSON d'AMO30 **ne connaît pas le nom du champ** : il rend
le marqueur pour *n'importe quel* élément déclaré vide. Corriger `uri_hatvp`
seul aurait réparé le champ mesuré et laissé les autres — ce qui vient
littéralement d'arriver, puisque `_texte_an` existait déjà depuis #562 et
n'était appliqué qu'aux amendements.

`candidate_profile._champ_identite_an` (alias de `_texte_an`) passe donc sur
**tout** champ lu dans `json/acteur/*.json` et `json/organe/*.json` :
`uri_hatvp`, `profession`, `civ`/`prenom`/`nom`, `dateNais`/`villeNais`/
`depNais`/`paysNais`, `numDepartement`/`numCirco`/`placeHemicycle`,
`dateDebut`/`dateFin`, `valElec`/`typeLibelle`, `libelleAbrege`/`libelle`/
`codeType`. Et les deux fonctions qui **interpolent** — `_format_lieu_naissance`
et `_format_nom_complet` — portent la garde en propre : c'est là que le dict
devient indétectable, donc c'est là qu'il ne doit pas arriver.

### Le correctif appartient à l'extraction, pas au pivot

Réparer dans `normalize_profil` aurait laissé `raw_data/profiles` — la couche
*source-near* — porter une valeur qui n'a jamais existé chez la source. La
correction vit donc dans la lecture d'AMO30, et la migration applique la même
règle **aux deux couches**.

### Les index dérivés d'AMO30 deviennent versionnés

Conséquence non évidente, et qui aurait rendu le correctif inopérant : les index
`index_identite.json` / `index_organes.json` sont mis en cache sur disque **et**
restaurés d'un run à l'autre par le cache GitHub Actions
([#cache-completude-interventions-550](cache-completude-interventions-550.md),
[#cache-fraicheur-interventions-555](cache-fraicheur-interventions-555.md)).
Un correctif portant sur ce qui est *écrit* dans l'index reste sans effet tant
que l'ancien fichier est relu : **le code corrigé ne s'exécute jamais**. Ils
portent désormais un nom versionné (`NOM_INDEX_IDENTITE`, `NOM_INDEX_ORGANES`),
et la règle est écrite avec : on incrémente dès que le **contenu écrit** change,
jamais pour un changement de lecture.

### La contrainte censée signaler la divergence la NEUTRALISAIT

C'est le point que l'issue demandait de vérifier, et la réponse est celle qu'elle
craignait. `validate_profil` refusait que `identite.uri_hatvp` et
`identifiants.hatvp` divergent — mais la condition était
`if uri_hatvp and publie and uri_hatvp != publie`. Or `_uri_hatvp_publiable`
ramène le marqueur à `None` avant d'alimenter `identifiants.hatvp` (#539) : le
couple était **(marqueur, `None`)**, le second membre falsy, la comparaison
sautée. **191 profils passaient la validation en publiant un dict là où le
schéma annonce un lien.**

Le contrôle porte désormais sur la **forme du champ lui-même** :
`identite.uri_hatvp` est une URI ou `null`, jamais autre chose. Un champ ne peut
pas être validé par ce qu'un voisin en a fait. La règle de recopie est
conservée, et complétée par sa moitié manquante — une `uri_hatvp` renseignée
avec un `identifiants.hatvp` vide est aussi une divergence.

Vérification sur le corpus publié : la nouvelle règle rend **191 erreurs, et
aucune autre**. Elle nomme exactement la population du défaut.

---

## B. Le gel d'un groupe n'était pas une décision déclarée (#558)

### La cause

`DECISIONS_PIPELINE` ne connaissait que les deux drapeaux de #357
(`skip_interventions`, `skip_dossiers_legislatifs`). Le **gel d'un groupe**
(`extraction_suspendue`, #516) n'y figurait pas. Faute de décision déclarée, la
couverture retombait sur le défaut — « couvert », borné par le référentiel — et
`charles-guene` publiait :

> `{"etat": "couvert", "portee": {"debut": "2002-06-19"}, "preuve": "AMO30 — 3 117 acteurs…"}`

« Couvert depuis 2002, zéro mandat » se lit « cette personne n'a pas de mandat ».
C'est faux.

Une décision qui manque à la table n'est pas une décision **absente** : c'est une
décision publiée comme un **fait**.

### La forme de la table change, et c'est le fond

`DECISIONS_PIPELINE` associait un drapeau à **une** liste. `groupe_suspendu` en
écarte **cinq** — rien n'a été demandé à aucune source. La forme précédente ne
rendait pas seulement la décision malcommode à écrire : elle la rendait
**inexprimable**, donc invisible. Le second membre est désormais un tuple de
listes.

La preuve, elle, est **lue** dans le bloc `extraction_suspendue` du groupe, pas
codée ici. Les quatre champs exigés par `groupes_config.anomalies_suspension`
existent pour être relus ; une preuve recopiée à la main divergerait le jour où
la suspension serait levée.

### Deux pièges de mesure, tous deux évités dans le code ET dans les tests

1. **`chambre` ne dit pas la chambre.** Les 20 membres des deux fiches
   `groupe-Senat-*` publient `chambre: "AN"` — défaut réel et **distinct**, tenu
   par #486, délibérément non corrigé ici. Compter les sénateurs par ce champ en
   rend **zéro**, et fait conclure que la population a disparu.
2. **La provenance ne recouvre pas la population.** 19 des 20 sont
   `roster_groupe` ; le vingtième est `bruno-retailleau`, de provenance
   `candidat_declare` — et c'est le plus visible des vingt. Un correctif branché
   sur la seule provenance l'aurait manqué.

L'appartenance se lit donc au **groupe** :
`groupes_config.index_membres_de_groupes_suspendus` croise les entrées
suspendues de `groupes_reels.json` avec les `membres[]` de leurs fiches
publiées. C'est la seule source qui existe encore — un groupe suspendu n'est
plus interrogé, donc sa composition ne vit plus que dans la fiche gelée — et
c'est exactement celle sur laquelle #558 a mesuré sa population.

### Le gel prime sur les drapeaux de #357

Sur un profil `roster_groupe` d'un groupe gelé, les deux drapeaux sont vrais
aussi — mais ils n'expliquent que deux listes sur cinq. Le gel les englobe, et
c'est lui que le lecteur doit trouver en preuve, sur les cinq.

### `meta.couverture_roster` dit ce que son ratio veut dire

`groupe-Senat-LR.json` publie `{"roster_total": 235, "profils_disponibles": 15}`.
6,4 %, et rien à côté pour dire si les 220 manquants sont une collecte en retard
ou un périmètre assumé. Ce sont les seconds.

`meta.couverture_roster.etat` ∈ { `dans_le_perimetre`, `hors_perimetre` }, avec
une `preuve` **obligatoire** sur le second. `etat` reste facultatif au schéma —
les fiches publiées avant ce lot n'en portent pas, et les déclarer invalides ne
dirait rien de vrai sur elles (même précédent que `identifiants` et `couverture`
dans #539). `check_quality_gate` affiche « 6,4 % (périmètre) ».

---

## C. Une frontière de source n'est pas une avarie (#560)

### Le défaut était dans l'ordre des tests, pas dans le vocabulaire

Le modèle à quatre états savait déjà dire la différence :

| État | Ce que la page dit |
| --- | --- |
| `hors_couverture` | « nos archives ne remontent pas jusque-là » — un fait sur notre couverture |
| `non_collecte` / `panne` | « nous avons essayé et ça a échoué » — un incident |

Mais rien ne choisissait entre les deux **avant** de poser la cause. La preuve
publiée l'avouait : « identifiant absent des trois archives, **ou** archive
indisponible ». Le code prenait le pire des deux par défaut.

Pour Ségolène Royal, la disjonction n'avait pas lieu d'être : son mandat relève
de la XIIe, `SYCERON_AVAILABLE_LEGISLATURES = {15, 16, 17}`. La `panne` était
fausse **par construction**, et elle laissait croire qu'un prochain run
comblerait le silence. Il ne le pourra pas.

### L'étape 1ter de `deriver`

Si aucune législature du profil n'intersecte ce que la source publie, l'état est
`hors_couverture`, avec la borne pour preuve — **avant** tout test de panne ou de
défaut interne. Une panne survenue par ailleurs ne dit rien d'une liste qui
n'aurait jamais pu être remplie.

`legislatures_du_profil` dérive les législatures des dates de `mandats[]`, et la
moitié importante de son contrat est qu'elle rend **vide quand rien n'est
connu** : un profil sans mandat daté ne dit rien de sa carrière, donc rien ne
doit en être dérivé. La forme à deux entrées de #539 — qui ne dépend d'aucune
connaissance de la carrière — reste le cas par défaut, y compris pour les 9
profils dont `mandats` est vide.

### Le préfixe est scindé, pas contourné

`WARNING_PREFIX_INTERVENTIONS_SYCERON_INDISPONIBLES` était écrit par les **deux**
branches de l'étape 9 : l'exception (une panne) et la collecte qui aboutit à vide
(un constat). C'est la leçon déjà tirée pour `WARNING_PREFIX_VOTES_INTROUVABLES`
pendant #539, dont la table de causes a dû être indexée **par motif** parce qu'un
préfixe couvrait une panne *et* un constat.

Ici on ne rattrape pas l'ambiguïté en aval : on ne l'écrit plus.
`WARNING_PREFIX_INTERVENTIONS_SYCERON_AUCUNE` porte le constat, et son message
dit ce qui s'est passé — « les archives ont répondu et ne portent aucune
intervention pour cet acteurRef ». Un zéro constaté est publiable (AGENTS.md
§2.5), donc l'état est `couvert`.

Une seule concession, et elle est nommée : `MOTIFS_JAMAIS_PANNE` reconnaît
l'**ancien** message, parce que les 481 profils bruts committés le portent encore
sous le préfixe de panne et que la passe pivot les relit à chaque run. Sans ce
pont, « panne » serait republié sur un zéro constaté jusqu'à la prochaine
collecte complète. Le critère ne bouge pas pour autant : la phrase reconnue dit
explicitement que la source **a** répondu.

### Les preuves nomment la limite de la source, pas notre ingestion

Une preuve disait :

> `candidate_profile.AN_SCRUTINS_LEGISLATURES = 17, 16, 15, 14` — 17 748 scrutins ingérés

Elle décrivait **notre ingestion**, donc se lisait comme un choix de notre part,
révisable au prochain run. `Borne` porte désormais `limite_source` **puis**
`constante` :

> l'Assemblée nationale ne publie pas de scrutins avant la XIVe législature —
> vérifié le 28/08/2026 sur data.assemblee-nationale.fr — borne portée par
> `candidate_profile.AN_SCRUTINS_LEGISLATURES = 17, 16, 15, 14` — 17 748
> scrutins ingérés

Pour une page comme celle de Royal, la différence n'est pas cosmétique : l'une
suggère qu'on pourrait collecter davantage, l'autre dit qu'on ne le pourra
jamais. Et AGENTS.md §2.2 demande qu'un fait renvoie à sa source primaire — une
constante du code n'est la source que de notre configuration. Elle reste nommée,
en second, comme trace d'implémentation : c'est sur elle que porte le test qui
fait tomber la couverture publiée le jour où une archive est ajoutée.

### Ce que l'AN publie réellement, vérifié le 28/08/2026

| Jeu de données | Législature la plus ancienne publiée |
| --- | --- |
| Scrutins, amendements, questions, dossiers législatifs, agendas | **XIVe** |
| Comptes rendus de séance (Syceron) | **XVe** — absents de la page d'archives de la XIVe |
| État civil et mandats des députés | **XIe (juin 1997)** |

La dernière ligne est l'exception qui explique les pages comme celle de Royal :
**un profil peut légitimement publier 11 mandats et zéro vote**. Ce n'est pas une
incohérence, c'est la forme de la source. Le fait n'existait jusqu'ici que dans
`couverture_dossiers.py`, où il ne couvrait que les dossiers législatifs.

---

## Ce que le lot ne fait pas

- **Il ne corrige pas `chambre: "AN"` sur les 20 sénateurs.** Défaut réel,
  distinct, tenu par #486.
- **Il ne commite aucune donnée régénérée.** Le correctif de #556 est un
  correctif d'**extraction** : les 191 profils exigent une passe d'écriture, qui
  est un geste de la propriétaire du dépôt et non le contenu d'une PR de code.
  `src/migrer_absences_publiees_556_558_560.py` la porte, **sans réseau** :
  ramener un marqueur d'absence à `null` est une lecture des fichiers déjà
  collectés, pas une re-collecte. Il passe par `profil_brut` — jamais par un
  `json.load` direct sur `<slug>.json` (#580).
- **Il n'explique pas les 9 profils à `mandats: 0`.** Voir ci-dessous.

## La question laissée ouverte par #558, et sa réponse

*Pourquoi ces 9 profils ont-ils `mandats: 0` alors qu'ils portent un `acteur_ref`
résolvable ?* Investigué : **ce n'est ni une panne ni le gel du groupe**, et
c'est un défaut distinct.

Les 20 portent tous `identite.nb_mandats: 0` — c'est-à-dire **zéro mandat
`typeOrgane == "ASSEMBLEE"`** dans AMO30 : aucun n'a jamais siégé à l'Assemblée,
donc aucun `mandat_electif` n'est reconstruit. Restent les mandats d'organes, et
`_TYPE_ORGANE_NON_MAPPES` écarte explicitement `DELEGSENAT`, `COMSENAT`,
`GROUPESENAT` et `SENAT`, au motif — écrit dans #382 — d'un « volume négligeable
(4 mandats) ». Ce volume avait été mesuré sur une population de **députés**.

Les 11 qui ont des mandats les tiennent d'organes **bicaméraux** que l'AN
référence (délégations aux assemblées parlementaires internationales, offices
parlementaires : `API`, `OFFPAR`, `DELEG` → catégorie `delegation`), plus
`bruno-retailleau` qui a des mandats `MINISTERE`. Les 9 autres n'en ont aucun :
toute leur carrière est dans des organes du Sénat, que le périmètre écarte.

C'est la même famille que les trois défauts de ce lot — une absence produite par
une **décision de périmètre** publiée comme un fait —, mais son mécanisme est
autre, et l'absorber ici aurait mêlé deux corrections. Issue **#591** ouverte.

Ce lot en éteint la moitié visible : ces 9 profils ne publient plus « couvert »
sur `mandats`. Mais la preuve qu'ils publient nomme le **gel du groupe**, qui est
vrai sans être la cause de ce vide-là — le périmètre d'organes vaudrait même si
le groupe n'était pas gelé. C'est ce qui reste à #591.

---

