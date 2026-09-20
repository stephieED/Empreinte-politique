<a id="populations-profils-portees-par-les-outils-630"></a>
# Les deux populations de `pivot_data/profiles/` sont portées par les outils, pas par une consigne (#630, 2026-08-30)

`2026-08-30`

> **En bref** — `check_quality_gate.py` ne contenait pas une occurrence de `provenance` et intitulait « Candidats » des sections portant sur les 481 profils (13 candidats déclarés, 468 membres de roster) ; tout compte affiché passe désormais par `Ventilation`, et la §2 cesse de nommer les 468 membres de roster « Inattendus » un par un (rapport de 1 054 à 592 lignes).

## Contexte

`pivot_data/profiles/` porte **deux populations** que rien ne distingue sur le
disque — un répertoire, un motif de nommage, 481 fichiers (mesuré le
30/08/2026) :

| `meta.provenance` | Profils | À quoi elle sert |
| --- | ---: | --- |
| `candidat_declare` | **13** | leur fiche publiée — ce qu'un lecteur ouvre |
| `roster_groupe` | **468** | alimenter les agrégats de groupe et de gouvernement |

`src/group_profile.py` **ne lit pas le bloc `identite`** — zéro occurrence,
mesuré. Il consomme `nom`, `mandats`, `votes`, `interventions`, `amendements`,
qui sont des listes. Un membre de roster existe pour être agrégé.

**Tous les agents confondent les deux.** L'épic #598 a été cadrée sur 481
profils avant d'être recadrée sur 13, et c'est la propriétaire qui l'a rattrapé,
pas un agent — alors que l'agent en cause portait déjà en mémoire la règle
« nommer la population d'un chiffre ».

## Pourquoi une consigne n'y peut rien, et c'est mesuré

**1. Le système de fichiers ne donne aucun signal.** Un agent qui mesure quoi
que ce soit lance un `glob("*.pivot.json")` et obtient 481. Cette énumérabilité
est délibérée — #580 l'a préservée : un répertoire par profil aurait rendu
**zéro** slug, et les audits auraient conclu « aucun écart » sans rien
rapprocher. Séparer `candidats/` et `roster/` rendrait la distinction
structurelle, mais casserait les six modules qui énumèrent le répertoire.

**2. Le vocabulaire des outils enseignait l'erreur.** `check_quality_gate.py` —
l'outil que tout le monde lance avant chaque commit — ne contenait **pas une
occurrence** du mot `provenance`, et ses sections s'appelaient « Candidats
générés vs attendus » et « Candidats avec peu d'interventions », alors qu'elles
portent sur les 481. Un agent qui lit « Candidats : 481 » apprend que les 481
sont des candidats, et le libellé le lui apprend **à chaque exécution**.

**3. Une règle en prose ne suffit pas.** L'avertissement sur le sparse-checkout
de `tests.yml` est écrit **deux lignes au-dessus** de la liste qu'on oublie de
compléter ; il a piégé trois personnes (#434, #520, `CLAUDE.md` le 30/08/2026).
Une règle ne s'applique qu'à qui se souvient de la lire **au bon moment**, et le
bon moment est la seconde où l'on lance un `glob`.

## Décision

**La distinction est portée par la sortie des outils, `AGENTS.md` §3 ne venant
qu'en complément.** Si la sortie qu'un agent vient de lire affiche la
ventilation, il ne peut plus écrire « 481 profils » sans l'avoir vue.

Un module unique, `src/population_profils.py`, nomme les deux populations et
rend la forme affichée. **Tout compte de profils affiché passe par
`Ventilation`** :

```
Profils publiés : 481   (13 candidats déclarés · 468 membres de roster)
```

`Ventilation.total` est la **somme des postes**, jamais un compte tenu à part :
un fichier illisible reste dans le total, sous son propre poste, pour que « 481 »
et « 13 + 468 » ne puissent pas diverger en silence. Un pivot sans
`meta.provenance` vaut `candidat_declare` (rétro-compatibilité de
[`provenance-pivot`](provenance-pivot.md)) ; une valeur hors
`KNOWN_PROVENANCES` est comptée sous un poste `provenance inconnue`, jamais
rangée d'office dans l'un des deux camps (AGENTS.md §2 règle 5).

Quatre outils, plus la ventilation des libellés qui mentaient :

| Module | Avant | Après |
| --- | --- | --- |
| `check_quality_gate.py` | 0 occurrence de `provenance` | §2, §3, §3b, §3c, §5b ventilent, et cinq libellés sont corrigés |
| `audit_collecte_vs_publie.py` | 0 occurrence | « Population : 481 profil(s) » ventilée, console et Markdown |
| `audit_volumetrie_profils.py` | 0 occurrence | « Population : 481 profils » ventilée — **hors profils bruts**, voir ci-dessous |
| `audit_pivot_dataset.py` | 25 occurrences, ventilation **calculée** | la ventilation est désormais **affichée** à côté de chaque total |

`audit_pivot_dataset.py` illustre le point : il **connaissait** la répartition
par provenance depuis toujours, dans une table située deux sections plus bas que
le total. Une ventilation calculée mais non affichée à côté du chiffre n'empêche
personne d'écrire « 481 profils » — et la ligne que tout le monde lit
réellement, `→ 481 profil(s) chargé(s)` sur stderr, ne la portait pas du tout.

### Les libellés qui mentaient

« Candidats générés vs attendus » rapprochait **deux populations différentes** :
13 candidats déclarés attendus dans `raw_data/candidats.json`, contre 481
profils sur le disque. Conséquence mesurée : les 468 membres de roster étaient
comptés « Inattendus » et **nommés un par un**, soit 468 lignes de fausse alerte
sur les 1 054 du rapport. Un garde-fou qui crie pour rien finit désactivé. Les
membres de roster sont désormais comptés comme la population attendue qu'ils
sont, et « inattendu » ne désigne plus qu'un profil qui se **dit**
`candidat_declare` sans figurer dans la liste éditoriale — 0 aujourd'hui. Le
rapport passe de 1 054 à 592 lignes.

Renommés : §2 « Profils générés vs candidats déclarés attendus », §3 « Profils
avec peu d'interventions », §3b « Profils AN avec législature Syceron », §3c
« Profils AN avec identité » (477 profils, dont 468 membres de roster), et les
colonnes « Candidat » des tableaux.

### Le brut n'est pas ventilable, et il le dit

`raw_data/profiles/<slug>.json` ne porte pas `meta.provenance` — mesuré : `meta`
y tient `genere_le`, `licence_donnees`, `synchro_sources`, `warnings`,
`collecte_ecartee`, et rien d'autre. Lui appliquer le repli « absente vaut
`candidat_declare` » afficherait « 481 candidats déclarés » : un chiffre juste
sur la mauvaise population, exactement le défaut que ce lot corrige. La règle de
rétro-compatibilité vaut pour un **pivot** d'avant #189, pas pour une couche qui
n'a jamais porté le champ. `ventiler_chemins()` ne ventile donc que les
`*.pivot.json` et rend les autres à part, que le rapport **nomme** :
« 481 profils bruts, sans meta.provenance ».

## Ce que ce lot ne dit pas

**Que les 468 profils de roster comptent moins.** Leur qualité compte autant :
c'est là que se trouvaient les 191 marqueurs HATVP publiés comme des URI et les
28 lieux de naissance faits de plomberie XML (#556). **Ce qui diffère est
l'usage, pas l'exigence** — un correctif de *fusion* d'identité porte sur 13
profils, un correctif de *qualité* d'identité porte sur 481.

Aucune donnée publiée ne change : ce lot ne touche que ce que les outils
affichent.

## Alternatives rejetées

**Séparer les répertoires** (`profiles/candidats/`, `profiles/roster/`) — la
distinction deviendrait structurelle, donc impossible à rater. Rejeté : cela
casse les six modules qui énumèrent le répertoire et surtout la propriété
d'énumérabilité que #580 a préservée délibérément (`glob("*.pivot.json")` doit
rendre les 481 slugs).

**Se contenter d'une entrée dans `AGENTS.md`** — rejeté par le point 3
ci-dessus : la règle y est bien, et elle est nécessaire, mais elle n'aide que
l'agent qui lit avant de mesurer. La sortie des outils rattrape celui qui mesure
avant de lire, et c'est le cas le plus fréquent.

**Un test qui refuserait tout compte de profils affiché sans sa ventilation, par
analyse du source** — rejeté comme mécanique fragile : un tel test devrait
reconnaître un « compte de profils » dans une f-string, crierait sur les
compteurs qui n'en sont pas (`len(rows_mixtes)`, `Entrées : 481`) et finirait
désactivé. Ce qui est verrouillé à la place : les rendus eux-mêmes, sur
fixtures, dans `tests/test_population_profils_630.py` — les quatre outils y sont
appelés et leur sortie doit porter la ventilation. La régression est fermée sur
les comptes qui existent aujourd'hui ; un compte **ajouté** demain sans passer
par `Ventilation` n'est pas détecté, et c'est écrit ici plutôt que présumé.
