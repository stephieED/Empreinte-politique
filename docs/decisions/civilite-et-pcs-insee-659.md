<a id="civilite-et-pcs-insee-659"></a>
# La civilité et la nomenclature PCS de l'INSEE traversaient le pipeline sans y laisser de trace (#659) (2026-08-31)

`2026-08-31`

> **En bref** — `etatCivil.ident.civ` était rangée dans l'index d'identité depuis #556 et s'arrêtait là, `profession.socProcINSEE` n'était pas lue du tout : re-mesuré sur les 3 117 fiches AMO30, la civilité est renseignée **3 117/3 117** (M. 2 106, Mme 1 011) et les deux niveaux de la nomenclature PCS de l'INSEE **2 177/3 117**, toujours renseignés ou absents **ensemble** ; les trois champs atteignent `identite` (clés facultatives, comme `identifiants` et `provenance_champs`), publiés **verbatim** parce que c'est la source qui classe — une catégorisation construite ici serait un acte éditorial (§2 règle 1) —, avec « non classé » (940 fiches au marqueur `xsi:nil`) tenu distinct de la famille « Sans profession déclarée » (85 fiches), le contresens exact de #556 ; le regroupement des variantes typographiques est laissé à qui agrège, purement typographique et jamais sémantique ; `NOM_INDEX_IDENTITE` passe en `v4` sans quoi le cache restauré rendrait l'index d'avant, et `validate_profil()` refuse désormais un non-`str` sur `CHAMPS_IDENTITE_TEXTE_LIBRE`, seul contrôle capable de voir le marqueur là où `audit_diff_profils` ne compare que la présence du bloc (#649).

Deux champs qu'AMO30 renseigne, que le pipeline lisait ou traversait, et qu'il
ne publiait pas. Trouvé en cherchant ce qu'une fiche de groupe peut dire de sa
composition (temps 2 de l'épic #324, issue #594) ; c'est le motif du
`dossier_id` des textes portés (#639) — un champ perdu à l'assemblage, sans
qu'aucun contrôle ne le voie.

## Ce que la source publie, re-mesuré le 31/08/2026

Sur `.cache/acteurs_historique_an/acteurs_historique.zip`, les **3 117 fiches**
`json/acteur/*.json` de l'archive
`AMO30_tous_acteurs_tous_mandats_tous_organes_historique.json.zip`.

| Champ AMO30 | Couverture mesurée | Lu avant ce lot | Publié avant ce lot |
| --- | ---: | --- | --- |
| `etatCivil.ident.civ` | **3 117 / 3 117** — « M. » 2 106, « Mme » 1 011, aucun `xsi:nil` | oui, `candidate_profile._build_acteur_identite_index` le rangeait en `civilite` | **non** |
| `profession.socProcINSEE.famSocPro` | **2 177 / 3 117** (70 %), 11 libellés distincts | non | **non** |
| `profession.socProcINSEE.catSocPro` | **2 177 / 3 117**, **37** libellés distincts | non | **non** |

Le bloc `socProcINSEE` existe sur les 3 117 fiches, avec exactement ses deux
clés, et les deux niveaux sont **toujours renseignés ou absents ensemble** :
2 177 couples de libellés, 940 marqueurs `xsi:nil` **aux deux niveaux à la
fois**, zéro fiche à un seul niveau. C'est ce qui autorise à publier `null` des
deux côtés d'un même geste.

## Pourquoi c'est publiable, alors qu'une catégorisation ne le serait pas

`socProcINSEE` est la **nomenclature des professions et catégories
socioprofessionnelles de l'INSEE**, appliquée par l'Assemblée nationale
elle-même et publiée sous Licence Ouverte. Le point est décisif et c'est le
seul qui rende ce lot recevable : une catégorisation socioprofessionnelle
**construite par ce dépôt** serait un acte éditorial contestable (AGENTS.md §2
règle 1) ; **reprendre celle de la source** ne l'est pas. La traçabilité suit
(règle 2) : la valeur publiée est celle de la fiche AN, mot pour mot.

Le champ `profession` reste ce qu'il est — du **texte libre**, et il le reste.
`PA794778` (Sandra Regol) montre les deux en un seul acteur : `libelleCourant`
y vaut `"(85) - Personne diverse sans activité professionnelle de moins de
60 ans…"`, que [#641](profession-code-nomenclature-641.md) refuse de publier comme
une profession, pendant que `famSocPro` dit « Sans profession déclarée ». La
même situation, dite par la nomenclature au lieu d'être devinée dans une
phrase.

## Les trois réserves, et ce qu'on en a fait

### 1. « Non classé » n'est pas « sans profession déclarée »

940 fiches portent le marqueur d'absence ; **85** portent la famille « Sans
profession déclarée », qui est une **valeur de la nomenclature**. Les
confondre publierait un fait — « cette personne n'a pas déclaré de
profession » — là où la source dit seulement qu'elle ne l'a pas classée : le
contresens exact de
[#marqueur-nil-identite-556](absences-publiees-comme-faits-556-558-560.md#marqueur-nil-identite-556).

Le filtrage passe donc par `candidate_profile._champ_identite_an`, **à la
lecture**, comme tout ce qui sort de `json/acteur/*.json`. Pas de correctif
champ par champ : le convertisseur XML → JSON d'AMO30 ne connaît pas le nom du
champ, et rend le marqueur pour n'importe quel élément déclaré vide.

Ce n'est pas une précaution de style. La fusion **ne fait jamais régresser un
scalaire vers `null`** ([#collecte-vide](collecte-vide-necrase-jamais.md)) :
un marqueur publié **une seule fois** y resterait indéfiniment, même après
correction de la collecte — c'est exactement ce qui a fait vivre les 191
`uri_hatvp` de #556. D'où un second filet, côté publié : `validate_profil()`
refuse désormais un non-`str` sur `CHAMPS_IDENTITE_TEXTE_LIBRE`
(`civilite`, `profession`, les deux niveaux PCS, `lieu_naissance`).

Ce contrôle est le seul qui puisse voir passer la chose. `identite` est un
**scalaire surveillé** d'`audit_diff_profils`, mais **seule sa présence est
comparée, pas son contenu** : une clé ajoutée, retirée ou changée ne déclenche
rien — ce que [#649](agregats-publies-controle-perte-649.md) vient de faire
payer sur les agrégats de groupe.

### 2. Les variantes typographiques ne sont pas harmonisées à la publication

La source écrit « Professions Intermédiaires » (107) **et** « Professions
intermédiaires » (58) ; « Artisans, commerçants et chefs d'entreprise » (125)
**et** « Artisans, commerçants, chefs d'entreprises » (47).

**Le libellé est publié verbatim, double espace compris** (`"Cadres de la
fonction publique, professions intellectuelles et  artistiques"` en porte un).
Un fait individuel publié est ce que la source dit ; ce n'est pas à ce dépôt de
décider qu'un espace est de trop.

**Le regroupement appartient à qui agrège**, et il est hors de ce lot :
`src/group_profile.py` n'est pas touché ici, et les agrégats de composition
(parité, familles socioprofessionnelles) s'instruiront une fois la donnée
présente. La règle pour ce jour-là est écrite maintenant, pour n'être pas
re-litigée : **purement typographique** — casse et espaces, sur le modèle de
`gouvernement_roster._normalise_fonction` — et **aucun rapprochement
sémantique**. Une clé qui replie « Professions Intermédiaires » sur
« Professions intermédiaires » est légitime ; une qui replie les deux variantes
« Artisans » l'une sur l'autre ne l'est pas par la typographie seule (elles
diffèrent d'un mot et d'un pluriel) et ne doit pas l'être autrement.

Aucune fonction de regroupement n'est livrée ici, et c'est délibéré : elle
n'aurait aucun appelant, et une clé écrite un lot trop tôt dérive de ce dont
l'agrégat a besoin.

### 3. `libelleCourant` reste du texte libre

Les deux champs coexistent et ne se remplacent pas. `profession` continue de
passer par `_profession_an` (#641), qui retire le code de nomenclature et
refuse de publier l'énoncé d'une absence ; `famille_socioprofessionnelle` porte
la nomenclature. Sur `PA794778`, le premier est `null` et le second dit « Sans
profession déclarée » : ce n'est pas une contradiction, c'est la raison d'être
du second.

## Ce que ça change dans les fichiers

| Étage | Changement |
| --- | --- |
| Index d'identité AMO30 | `civilite` inchangée ; `famille_socioprofessionnelle` et `categorie_socioprofessionnelle` ajoutées via `_socproc_insee_an` |
| `NOM_INDEX_IDENTITE` | `index_identite_v3.json` → **`index_identite_v4.json`** — le contenu écrit change, donc le nom change (#556), sinon le cache disque restauré par le cache GitHub Actions rendrait l'index d'avant et **le code ajouté ne s'exécuterait jamais** |
| Profil brut | `identite.civilite` + les deux niveaux PCS |
| Pivot | `normalize_profil()` recopie `identite.civilite`, `identite.famille_socioprofessionnelle` et `identite.categorie_socioprofessionnelle` |
| Schéma | les trois champs décrits ; `CHAMPS_IDENTITE_TEXTE_LIBRE` contrôlé par `validate_profil()` |

**Les trois clés sont facultatives**, comme `identifiants` (#539) et
`provenance_champs` (#603) l'ont été : les 477 profils publiés qui portent un
bloc `identite` (sur 481) ne les ont pas, et les déclarer invalides ne dirait
rien de vrai sur eux. Elles apparaissent à la régénération. Vérifié sur le
corpus committé : aucun des 477 blocs ne porte de valeur non-`str` sur les cinq
champs contrôlés, donc le nouveau contrôle n'échoue sur rien de déjà publié.

## Ce qui a été mesuré, et ce qui ne l'a pas été

Ventilation obtenue en rejouant l'appariement sur `groupe-AN-LFI-16.json`
(76 membres publiés, **76 appariés** via `raw_data/correspondance_acteurs_an.json`) :
**44 M., 32 Mme** · Cadres et professions intellectuelles supérieures 47 ·
Employés 10 · Professions intermédiaires 9 (7 + 2 sur les deux variantes) ·
Sans profession déclarée 4 · Ouvriers 3 · Retraités 2 · Artisans, commerçants,
chefs d'entreprises 1 · **aucun non classé**.

L'issue annonçait 75 appariés, 43 M. et 46 « Cadres ». L'écart est d'**un
membre**, apparié ici et pas là : la répartition tient, le compte de deux
lignes bouge de un. La méthode d'appariement de l'issue n'est pas consignée,
donc l'écart n'est pas explicable au-delà de ça.

**Non mesuré** : le coût de la reconstruction forcée de l'index d'identité
(le passage en `v4` la déclenche une fois, sur tous les runs, comme #556 et
#640 l'ont fait avant). L'archive est déjà en cache disque, donc aucune
requête réseau ne s'y ajoute, mais le temps de reparse n'est pas remesuré —
AGENTS.md §2 règle 5 vaut pour notre propre travail.

## L'alternative écartée

**Publier un libellé canonique plutôt que le libellé de la source.** Elle
supprimerait les variantes d'un coup, mais elle demande de **choisir** une
graphie — donc d'écrire, sous le nom de la source, une valeur que la source
n'écrit pas. Sur un champ dont tout l'intérêt est que « c'est la source qui
classe », c'est se retirer le seul argument qu'on avait.
