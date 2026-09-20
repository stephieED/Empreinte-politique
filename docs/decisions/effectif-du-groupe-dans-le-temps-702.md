# L'effectif d'un groupe dans le temps : `min_historique` et `max_historique` portent leur date (#702) — 01/09/2026

`2026-09-01`

> **En bref** — les deux champs valaient `null` sur les **7 fiches** depuis l'origine du schéma ; ils publient désormais `{valeur, date}`, balayés à chaque `debut_dans_groupe` et au **lendemain** de chaque `fin_dans_groupe` (borne de fin inclusive, `_appartenance_couvre`), sur la **fenêtre de la fiche** — `periode.debut` → `periode.fin`, `date_reference.date` prenant le relais tant que la période est ouverte, jamais au-delà. Mesuré sur les 5 fiches AN de la XVIe : **REN 167 → 175**, **RN 87 → 89**, **LFI 74 → 75**, **LR 61 → 61**, **SOC 31 → 31** — l'écart `membres[]` / `a_la_date_de_reference` (24 sur REN) est de la **rotation**, pas une amplitude, et le lire comme telle aurait publié un chiffre trois fois trop grand. **Seuil 0** : une seule entrée sans `debut_dans_groupe` laisse les deux bornes à `null` avec son motif — ce membre n'est comptable à aucune date (#653), et les bornes obtenues sans lui sont des bornes inférieures (0 / 452 sur les 5 fiches AN, 14 / 15 et 4 / 5 sur les 2 fiches Sénat gelées, #516, qui gardent `null`). Limite nommée et non mesurée : `membres[]` ne porte qu'**un intervalle par membre** (périodes recollées, #526), donc un départ suivi d'un retour reste invisible et l'amplitude est un minorant. Trois formes lues (`null`, entier nu hérité, objet), une seule produite ; ni série, ni taux, ni classement (§2 règle 1).

## Contexte

Une fiche de groupe publiait un effectif **à une date** pour décrire une
législature de deux ans. `effectif.min_historique` et `effectif.max_historique`
existaient dans le schéma depuis l'origine (`schema_groupe.py`, « null si non
calculé ») et valaient `null` sur les **7 fiches publiées** ; le code le déclarait
tel quel — `group_profile.py` : `# non calculé (nécessiterait une analyse de
timeline)`.

Remesuré le 01/09/2026 sur `pivot_data/groupes/` à `1db5c051` :

| Fiche | `a_la_date_de_reference` | entrées `membres[]` | `min`/`max` avant |
| --- | ---: | ---: | --- |
| `groupe-AN-REN-16` | 169 | 193 | `null` |
| `groupe-AN-RN-16` | 88 | 90 | `null` |
| `groupe-AN-LFI-16` | 75 | 76 | `null` |
| `groupe-AN-LR-16` | 61 | 62 | `null` |
| `groupe-AN-SOC-16` | 31 | 31 | `null` |
| `groupe-Senat-LR` · `groupe-Senat-SER` | 1 · 0 (`actuel`) | 15 · 5 | `null` |

**L'écart entre `membres[]` et l'effectif à la date de référence est de la
rotation, pas une amplitude** — et c'est la première chose que ce lot mesure.
Sur `AN:REN-16`, 193 − 169 = 24 entrées, mais l'effectif réel oscille entre
**167 et 175** : 9 membres sont partis avant le pic, 9 sont entrés après. Lire
l'écart comme une amplitude aurait publié un chiffre trois fois trop grand.

## Décision

### 1. La forme : `{valeur, date}`, jamais un entier nu

```json
"effectif": {
  "a_la_date_de_reference": 169,
  "min_historique": {"valeur": 167, "date": "2024-03-09"},
  "max_historique": {"valeur": 175, "date": "2023-01-30"}
}
```

Un minimum sans sa date est un nombre sans fait (AGENTS.md §2 règle 2). L'objet
est préféré à deux champs voisins (`min_historique` + `min_historique_date`)
pour une raison mécanique : deux champs voisins se recopient l'un sans l'autre,
et le champ orphelin qui survit est le nombre — exactement celui qui ne doit
jamais voyager seul. Imbriqués, ils ne peuvent pas se séparer.

Les **noms de clés ne changent pas**. `min_historique`/`max_historique` ne
mentent pas sur leur ancrage temporel — le défaut que #653 a corrigé sur
`actuel`. Ce qui manquait à leur nom, c'est la fenêtre : elle est publiée par
ailleurs (`periode`), et le point 2 la fixe.

### 2. La fenêtre : celle de la fiche, jamais au-delà

`periode.debut` → `periode.fin`, bornes incluses. Quand la période est encore
ouverte (`periode.fin` à `null`, au moins une appartenance sans fin), la borne
haute est `date_reference.date` — la date de génération, seul instant où « qui
siège » a un sens sur une législature qui court (#653). Le lecteur reconstitue
donc la fenêtre depuis la fiche seule : `periode.fin` sinon
`date_reference.date`. Aucun champ de fenêtre n'est ajouté : il dupliquerait
`periode`.

Si les deux bornes hautes manquent, la fenêtre n'existe pas et les deux champs
sortent `null` (`fenetre_non_bornee`). Une fenêtre non bornée couvrirait toutes
les dates — l'inverse exact de la règle du point 3.

### 3. Les dates évaluées : entrées et **lendemains** de sortie

L'effectif est une fonction en escalier : il monte le jour d'un
`debut_dans_groupe`, et descend **le lendemain** d'un `fin_dans_groupe`, parce
que la borne de fin est inclusive (`_appartenance_couvre`, #653 : « un mandat de
groupe qui se termine le jour de la clôture couvre ce jour »). Balayer
`{periode.debut} ∪ {debut_i} ∪ {fin_i + 1 jour}`, intersecté avec la fenêtre,
suffit : tout palier de la fonction commence à l'une de ces dates.

**Qui est présent à une date est décidé par `_appartenance_couvre`**, la même
fonction que `present_a_la_date_de_reference` — jamais une seconde
implémentation de la même règle. Une borne de début absente rend donc
l'appartenance ouverte **à aucune date, jamais à toutes** : cette règle est
reprise de #653, pas réinventée.

À valeur égale, **la première date** où la borne est atteinte est retenue. Sans
convention écrite, deux runs sur la même donnée dateraient différemment la même
valeur.

### 4. Ce que le calcul ne peut pas établir

**Une seule entrée `membres[]` sans `debut_dans_groupe` interdit la
publication**, seuil **0**, les deux bornes à `null` et le motif en clair dans
`meta.warnings`. Ce membre n'est comptable à aucune date : les bornes obtenues
sans lui sont des **bornes inférieures**, et une borne inférieure publiée sous le
nom « minimum » est un chiffre faux. `null` est une réponse, un chiffre faux n'en
est pas une (AGENTS.md §2 règle 5).

Mesuré au 01/09/2026 — la règle sépare exactement les deux populations :

| Population | entrées sans `debut_dans_groupe` | amplitude |
| --- | ---: | --- |
| 5 fiches AN de la XVIe | **0 / 452** | publiée |
| 2 fiches `groupe-Senat-*` gelées (#516) | **14 / 15** et **4 / 5** | `null`, motivée |

**La limite qui subsiste, et qu'aucun `null` ne couvre** : `membres[]` ne porte
qu'**un intervalle par membre**. `an_roster._fusionner_periodes` recolle les
périodes successives d'un acteur — début le plus ancien, fin la plus tardive,
`None` l'emportant (#526). Un membre parti puis revenu est donc publié présent
en continu, et son absence n'entre dans aucune borne. L'amplitude publiée est un
**minorant de l'amplitude réelle**. Le corriger demanderait de changer le
contrat du roster (`mandat_debut`/`mandat_fin`), pas ce calcul ; l'avertissement
lecteur le dit, et `test_un_depart_suivi_d_un_retour_est_invisible_et_c_est_dit`
l'épingle plutôt que de le masquer. **Non mesuré** : combien de membres sont dans
ce cas — l'archive AMO30 n'est pas committée, et aucun test ne va au réseau
(§3b).

### 5. Ce qui rendrait cette amplitude fausse

Elle est **pré-calculée**, donc elle survit à la correction de sa source. Trois
événements la rendent fausse sans qu'elle change :

1. **les dates d'appartenance bougent** — c'est déjà arrivé deux fois, #647 puis
   #653 ; l'amplitude serait alors juste au sens du calcul et fausse au sens du
   fait ;
2. **un membre est ajouté ou retiré de `membres[]`** sans que la fiche soit
   régénérée — impossible aujourd'hui, les deux sortent du même appel ;
3. **le recollage du roster change** (point 4).

La parade appliquée : le calcul est fait **dans `build_groupe_profile`, sur la
même liste `membres[]` et par la même fonction de présence** que
`a_la_date_de_reference`. Les trois compteurs ne peuvent pas se désynchroniser
sans que les trois soient faux ensemble, et
`test_les_bornes_encadrent_l_effectif_a_la_date_de_reference` le vérifie.

### 6. Les 2 fiches gelées, et la double forme en lecture

Les `groupe-Senat-*` ne seront pas régénérées (#516) : leurs deux champs
resteront `null`, comme leur `effectif.actuel` reste un entier nu et leur
`date_reference` reste absente. `validate_profil_groupe` accepte donc **trois
formes** — `null`, un entier nu (forme héritée, jamais produite depuis ce lot),
l'objet `{valeur, date}` — et refuse la seule qui trompe : un objet dont la
valeur ou la date manque. `schema_groupe.valeur_borne_effectif` rend l'entier des
trois, et `audit_groupe_dataset.compute_effectifs` le lit — un audit qui
n'aurait suivi que la nouvelle forme publierait « 0 groupe renseigné » là où la
donnée existe, sans que rien ne le dise. Même arbitrage que #653 pour
`actuel` / `a_la_date_de_reference`, et que #686 pour `position_politique`.

## Ce qui n'est pas fait, et pourquoi

- **La série complète des paliers n'est pas publiée.** 14 points sur `AN:REN-16`,
  2 sur `AN:SOC-16` : le coût serait nul. Mais une courbe est un objet
  d'affichage, et l'affichage relève de #329, dont l'issue reste ouverte.
  Publier une liste que rien ne lit, sans contrat de lecture, c'est le champ
  jamais rempli que ce lot vient précisément de corriger.
- **Aucun taux, aucun classement, aucune moyenne entre groupes** (AGENTS.md §2
  règle 1). Une amplitude d'effectif n'est pas une performance, et « le groupe
  qui a le plus fondu » est un classement.
- **L'amplitude n'est pas un scalaire surveillé du contrôle de perte.**
  `audit_diff_profils.COLLECTION_GROUPES` exclut tout champ d'`effectif`, et
  `test_l_effectif_reste_ecarte` (#649) l'exige explicitement. Le motif écrit
  vise `effectif.actuel`, « qui baisse légitimement » — or une régression
  `renseigné → null` de `min_historique` n'est pas une baisse, c'est une perte,
  la catégorie bloquante qui existe déjà. **Réviser cette exclusion est un
  arbitrage distinct**, qui touche une décision déjà rendue et testée : il n'est
  pas pris ici.

## Alternative écartée

**Deux champs voisins `min_historique` (entier) + `min_historique_date`.** Coût
nul en migration — `audit_groupe_dataset` continuait de lire un entier sans une
ligne de changement. Écartée pour la raison du point 1 : le nombre survit seul à
une recopie, et c'est le nombre qui ne doit jamais voyager sans sa date. Le coût
réel de l'objet s'est révélé être une fonction de lecture partagée
(`valeur_borne_effectif`), soit dix lignes.

**Publier l'amplitude en tolérant les membres sans date, avec un compteur de
couverture.** C'est ce que fait §2 règle 7 pour un ratio (numérateur,
dénominateur, couverture). Écartée parce qu'une borne n'est pas un ratio : un
ratio avec une couverture de 6 % reste lisible comme « 6 % de couverture », alors
qu'un minimum reste lu comme un minimum quoi qu'on écrive à côté. Sur
`groupe-Senat-LR` (1 entrée datée sur 15), la « couverture » aurait accompagné un
chiffre qui n'a aucun rapport avec le groupe.
