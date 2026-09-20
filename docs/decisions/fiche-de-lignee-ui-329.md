# La page de groupe devient une fiche de lignée, construite en maquette avec la propriétaire (#329)

`2026-09-11`

> **En bref** — l'interface publie **une fiche par lignée déclarée** (#836), et plus une par législature : 13 pages au lieu de 30 fiches, l'adresse d'un groupe vient de son `lignee_id` et une adresse de fiche par législature (`/groupes/AN-SOC-17`) mène à sa lignée. La page a été **construite en maquette avec la propriétaire le 11/09/2026** — seize versions, vingt fils d'annotation —, et chaque arbitrage y est venu d'un rendu, jamais d'un texte. **`sync-data.mjs` ne rechaîne plus `succede_a`** : il trouvait 13 lignées, maillon pour maillon les mêmes que les 13 déclarées, mais seulement parce qu'aucune scission n'était encore écrite. La page lit une **projection de build** (`scripts/vue-lignee.mjs`, 6,9 Mo pour les 13, 1,1 Mo au plus pour une lignée, contre 5 Ko à 7,7 Mo de fiche de lignée et jusqu'à 11 Mo de maillons), calculée par les **mêmes règles** que le navigateur importe (`utils/groupe.js`, `utils/lignee.js`) : Node exige l'extension `.js` dans les imports, Vite l'accepte, et c'est tout ce qu'il a fallu changer. Deux recalculs y sont **vérifiés, pas crus** : l'effectif jour par jour retombe sur `effectif.a_la_date_de_reference` pour les **28 maillons AN sur 28**, et les amendements par commission retombent sur `amendements_agreges.par_type_deposant` pour les **56 couples (maillon AN, type de déposant) sur 56** — un type qui s'en écarte n'est pas servi. Six sections — qui sont-ils · sur quoi ils ont pris la parole · ce qu'ils ont proposé · ce qu'ils ont voté · avec qui ils votent · ce qu'on n'a pas pu lire —, la dernière réduite à ce que chaque fiche signale d'elle-même, le reste du corpus renvoyé à `/couverture` (#328), la navigation par période de la fiche candidat maillon par maillon, et les sept règles de forme appliquées : le paragraphe en méthodologie derrière cinq ancres, la limite en pied de section. **Retirés, chacun pour sa raison** : « Ce que cette fiche ne dit pas » et les sept notes (règle 2), la ligne « déposés par le gouvernement : 0 » et la comparaison des amendements groupe contre groupe (règle 1), les instances et fonctions (donnée fausse, #853), les grandes lois (relecture). **Un écart assumé avec la fiche candidat** : la frise de lignée garde des motifs de posture le jour où celle du candidat perd les siens (#328), parce qu'elle ne porte qu'un encodage. Coût : `sync-data` passe à 59 s et 1,2 Gio de RSS à froid. Suite complète à **4 525**, 0 échec.

## Le point de départ : deux définitions du même objet

Le backend déclare les lignées depuis #836 : `lignee_id` sur chaque entrée de
`raw_data/groupes_reels.json`, une fiche par lignée dans `pivot_data/lignees/`.
L'interface, elle, les **recalculait** en chaînant `succede_a` dans
`sync-data.mjs`, et ne lisait jamais `pivot_data/lignees/` : son bouton menait à
la fiche la plus récente d'une chaîne qu'elle avait reconstruite seule.

Mesuré le 11/09/2026 sur `origin/main` `32c6102e5` : **13 chaînes côté UI, 13
lignées déclarées, identiques maillon pour maillon**. Le brief de lot annonçait
10 : le chiffre datait d'avant MoDem, Horizons et LIOT (#815). L'écart n'était
donc pas dans les nombres — il était dans le fait d'en avoir deux sources. Une
chaîne et une partition déclarée coïncident tant qu'aucune **scission** n'est
écrite ; `UDR` quittant `DR` (#815) est exactement le cas où elles divergent.

`sync-data.mjs` lit désormais les lignées et n'en calcule plus aucune. Une
fiche de groupe qu'aucune lignée ne déclare se **nomme** au build plutôt que de
disparaître de l'interface en silence (#510) ; le portail la refuse déjà (§4c).

## Une projection de build, calculée par les règles de l'interface

La page n'a besoin que d'une fraction de ce que portent la fiche de lignée et
ses maillons. `scripts/vue-lignee.mjs` en écrit, au build, une projection par
lignée — le motif de `comparaison-groupes.mjs` et de `couverture.json` (#628
appliqué au navigateur) :

| Lignée | Projection servie | Fiche de lignée | Maillons |
| --- | ---: | ---: | ---: |
| `AN-SOC` | 0,96 Mo | 5,3 Mo | 10,9 Mo |
| `AN-LFI` | 1,1 Mo | 5,2 Mo | 8,3 Mo |
| les 13 | 6,9 Mo | 50 Mo | — |

Le poids restant est surtout fait des **intitulés de scrutins** que les listes
dépliables affichent (207 Ko pour SOC XVIIe) ; l'ancienne page téléchargeait
`scrutins.json` entier, 9,9 Mo.

**La projection ne calcule rien qui lui soit propre.** Chaque nombre sort d'une
fonction de `src/utils/groupe.js` ou de `src/utils/lignee.js` — les mêmes que le
navigateur importe. Pour que Node puisse les importer, `groupe.js` écrit
désormais `from './lecture.js'` ; `legislatureDeAmendementId` quitte
`pivotAdapter.js` (que Node n'importe pas) pour `lecture.js`, et l'adaptateur la
réexporte.

## Deux recalculs, et ce qui les rend tolérables

**L'effectif jour par jour** (`serieEffectif`) se recompte depuis
`membres[].periodes` (#809), la fin d'appartenance comptant encore ce jour-là.
Sa valeur à la date de référence retrouve `effectif.a_la_date_de_reference`
**au membre près, sur les 28 maillons AN**. La frise ne trace un effectif que
s'il est **daté** : les deux fiches Sénat gelées ne portent que l'ancien
compteur, rapporté à aucune date (#653), et leur bande devient un contour
tireté.

**Les amendements par commission saisie au fond** n'existent sur aucune fiche
de groupe. `scripts/amendements-lignees.mjs` les reconstitue depuis
l'`amendements[]` des membres, l'index par législature et
`commissions_dossiers.json` — une **seconde écriture de la règle de #821**
(législature lue sur l'identifiant, un amendement une fois quel que soit le
nombre de cosignataires). Elle n'est tolérable qu'à une condition, et le script
la vérifie à chaque build : chaque type de déposant recompté est comparé à
`amendements_agreges.par_type_deposant[type].nb_amendements`, et **un type qui
s'en écarte n'est pas servi**. Mesuré : 56 couples (maillon AN, type) sur 56 au
chiffre près ; le prototype Python et le script JS rendent les mêmes lignes.

Le reste que la source ne range sous aucun type se **dit** en pied de section
et ne se fond dans aucune barre : 3 991 des 10 987 amendements de `GDR-17`,
154 pour `FI-15`, 342 pour `RN-16` et pour `RN-17`.

## Ce que la maquette a tranché

Vingt fils d'annotation de la propriétaire sur l'artifact `edb442eb`, chacun
traité dans une version. Les arbitrages qui engagent :

| Sujet | Tranché | Pourquoi, en une ligne |
| --- | --- | --- |
| « Qui sont-ils » | un point par personne et par groupe, trois états, survol qui allume le chemin | forme B sur trois comparées ; cinq agrégats avaient été écartés la veille |
| La liste des personnes | une colonne par groupe de la lignée, dans l'ordre des points ; le survol d'un nom allume son chemin | une personne passée par trois groupes figure dans trois colonnes : c'est le chemin qui se lit |
| Motifs de posture | majoritaire aplat, opposition diagonales, minoritaire mauve clair uni, non déclarée points serrés | les motifs d'origine se ressemblaient trop ; choisi sur quatre jeux |
| « Ce qu'ils ont proposé » | le gabarit « amendements par matière » de la fiche candidat, textes au clic ; « comme députés » et « comme rapporteurs » se sélectionnent **ensemble**, et les comptes portent alors sur les deux réunis — amendements additionnés, textes réunis sur leur dossier (`cumulerTypes`) | même lecture à chaque niveau ; SOC XVIIe réuni : 15 599 amendements, le total distinct publié, et 246 dossiers, pas 237 + 49 |
| Le lien de source | porté par l'intitulé, plus de badge « Source » | le badge répété sous chaque ligne |
| Scrutins listés | la dernière lecture de chaque texte en tête (#711), le reste replié | « un texte, une position » |
| « Avec qui ils votent » | comptes ET listes sur la seule dernière lecture | SOC XVIIe face au RN : 627 scrutins → 50 textes |
| Ordre de « Avec qui ils votent » | par nombre de textes communs, puis — à base égale seulement — par votes dans le même sens | amende #329, qui écartait tout tri par accord : à dénominateur égal, l'accord se compare sans classer des parts calculées sur des bases différentes (§2 règle 1) ; SOC XVIIe, GDR passe devant DEM, 49 textes chacun |
| Barres de « Avec qui ils votent » | une seule échelle pour toutes les lignes : la longueur d'une barre est son nombre de textes communs | ramenées chacune à toute la largeur, 48 et 58 textes se lisaient comme la même base — une barre normalisée à effet visuel, que le DESIGN_SYSTEM §5 interdit |
| Barre de partage | trois parts, cliquables, qui filtrent la liste | « d'une seule voix » par date ; les parts partagées par voix minoritaires, jamais affichées |
| Groupes voisins | liés à leur lignée | un lien de sigle survit au renouvellement |
| Liste datée de « En bref » | du plus récent au plus ancien, chaque ligne gardant le numéro de son repère | le groupe d'aujourd'hui se lit d'abord ; la frise, elle, court dans l'ordre du temps |
| Les textes portés | la cascade de la fiche candidat, **extraite dans `CascadeTextes.jsx`** et importée par les deux fiches, sur la règle `textesPortes` ; population : les dossiers portés par les membres dans la législature du maillon, **un dossier une fois** au stade le plus avancé (`textesDuMaillon`) ; deux qualités, auteur et rapporteur, qui se réunissent sans doublon ; `initiateur_projet_de_loi` écarté ; une teinte par commission pour toute la section, fixée par le volume d'amendements du maillon tous types réunis | collecte des textes portés des membres au run du 11/09/2026 (#835) : 993 profils de membres sur 1 148, 10 092 entrées ; SOC XVIIe, 203 textes publiés dont 6 portés aux deux titres ; la cascade et les barres d'amendements coloriaient la même commission de deux teintes |
| « Ce qu'on n'a pas pu lire » | la section de la fiche candidat, réduite à ce que **chaque fiche de groupe signale d'elle-même** — membres déclarés sans profil, interventions sans législature gardées, amendements sans identifiant, votes sans scrutin écartés, Sénat hors périmètre —, rangé par liste dans l'ordre des sections, maillon par maillon ; deux renvois, `/couverture` et `/methodologie#couverture` (`signalementsDuMaillon`) | le partage de `page-couverture-commune-328` : trois avertissements sont identiques en nature sur les 28 fiches AN (source AMO30, date de référence et effectif, carrière écartée des agrégats) et relèvent de `/couverture` ; restent cinq signalements sur **14 fiches sur 30**, soit 9 lignées sur 13 — les 4 autres le disent en une ligne. Deux signalements ne vivent que dans `meta.warnings` : leur motif est ancré sur le gabarit de `group_profile.py`, relu par un test |

**Deux propositions de la réponse automatique de l'artifact ont été
corrigées** avant d'être appliquées : une couleur par groupe (un marquage
politique, §2 règle 1) et un histogramme des voix minoritaires (le « nombre de
dissidents » de §2 règle 7). La leçon est celle d'`AGENTS.md` §10 : une
réponse écrite sans regarder la donnée n'est pas une réponse.

## L'écart avec la fiche candidat, et pourquoi il tient

La fiche candidat a retiré ses motifs de posture le **même jour** (#328, « la
frise dit l'institution, et rien d'autre »), une heure après la validation de
ceux-ci : sa bande portait **deux** encodages, l'institution en teinte et la
posture en motif. La frise d'une lignée n'en porte **qu'un** — la teinte est
toujours celle de l'Assemblée — et le motif y est la seule chose qui change
d'un maillon à l'autre. La raison ne s'applique pas ; la forme validée reste.

Deuxième écart, de même nature : l'intitulé porte le lien de source sur la fiche
de lignée, et la fiche candidat garde son badge. **L'aligner revient à la
propriétaire**, et ce lot ne touche pas à la fiche candidat.

## Retiré, et pourquoi

| Retiré | Règle ou cause |
| --- | --- |
| « Ce que cette fiche ne dit pas », les sept notes encadrées | règle de forme 2 — le raisonnement va en méthodologie, sous `lignee`, `paroles`, `depots`, `cohesion`, `convergences` |
| « Déposés par le gouvernement : 0 » | règle 1 — un groupe ne dépose jamais au nom du gouvernement |
| Amendements déposés / adoptés, groupe contre groupe, par posture | règle 1 — « la majorité fait adopter ses amendements » est la définition d'une majorité |
| Instances et fonctions exercées | donnée fausse : `mandats_agreges` compte la carrière des membres, 38 835 entrées sur 82 233 hors appartenance (#853) — les règles de `groupe.js` restent, la section reviendra |
| « Sur les grandes lois » | retiré à la relecture ; `grandesLois` reste dans `groupe.js` |
| La `preuve` de couverture des fiches Sénat | un paragraphe technique n'a pas sa place sur la fiche (règle 2) ; elle reste dans la donnée, et la phrase des listes vides ne renvoie plus à la section « Vérification » disparue |
| Les `comparaison-*.json` servis | plus aucune page ne les télécharge ; ils sont lus en mémoire au build |

## Trouvé en route, et corrigé ou ouvert

- **Le filtre des candidats par groupe ne retenait personne** :
  `getCandidatesList` perdait `groupIds`, que le manifeste servait. Corrigé.
- **`mandats_agreges` n'est pas borné à l'appartenance** : #853.
- **La dernière lecture d'un texte se dédouble** quand l'Assemblée écrit
  « relatif » puis « relative » (JO 2030) : la clé de #711 est l'intitulé.
  Un seul cas dans le corpus ; #854, sans toucher à la règle, qui sert aussi à la
  fiche candidat.
- **Le lien d'un dossier amendé** : l'index ne porte que `dossier_id`.
  L'Assemblée résout `/dyn/{législature}/dossiers/{identifiant}` — vérifié sur
  cinq dossiers des XIVe à XVIIe législatures, chaque page portant le titre que
  l'index publie —, et `urlDossierAN` ne construit rien sur une autre forme.

## Ce que ce lot ne fait pas

- **La frise à 400 px** se lit en entier mais petit : aucune mise en page propre
  au téléphone n'a été faite. Aucun débordement horizontal, mesuré.
- **Nommer les membres déclarés sans profil** : 7 entrées de roster sur 5 fiches AN
  (GDR XVIe et XVIIe, LAREM XVe, LIOT XVIe, LR XVe). La fiche n'en porte que le
  compte — `group_profile.py` n'écrit leurs identifiants que sur la sortie
  d'erreur du run —, et la section 6 dit donc « 1 membre sur 24 » sans le
  nommer. Les nommer demande un champ du pipeline, pas une règle d'interface.
- **Le contraste et le clavier** n'ont pas été audités par un outil ; les
  boutons portent un contour de focus et des libellés `aria-label`.

## Alternative écartée

**Garder le chaînage de l'interface et y ajouter la lecture des fiches de
lignée.** Il rendait le même résultat le 11/09/2026 ; il aurait gardé deux
définitions du même objet, et la première scission déclarée les aurait fait
diverger sans qu'aucune étape n'échoue.

**Faire publier la répartition par commission par le pipeline.** Plus juste en
principe — la règle de #821 n'y serait écrite qu'une fois —, mais c'est un lot
backend, et le contrôle d'égalité au build rend la seconde écriture sûre : elle
ne peut pas publier un chiffre que la fiche ne confirme pas.
