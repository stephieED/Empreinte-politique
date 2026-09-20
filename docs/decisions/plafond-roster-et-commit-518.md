<a id="plafond-roster-et-commit-518"></a>
# Le plafond de lecture du roster, et le commit qui ne paie plus pour une source lente (#518, second incident) (2026-08-24)

`2026-08-24`

> **En bref** — le plafond était placé dans la distribution de réponse de la source.

**Ce que #519 a corrigé, c'est le nombre d'essais. Ce que celui-ci corrige,
c'est la valeur qui décide de l'issue de chaque essai — et le fait qu'une
donnée non écrite pouvait annuler la publication d'une donnée écrite.**

## 1. Ce qui s'est passé

Run [`32750929942`](https://github.com/stephieED/Empreinte-politique-src/actions/runs/32750929942),
le premier après la fusion de #519. **22 jobs verts**, dont les 8 shards roster
(contre 4/8 avant) : ils ne fetchent plus rien, ils téléchargent l'artifact
`roster-candidats`, et dans `merge-and-pivot` le step de repli est bien
**skippé**. Le transit fonctionne.

Mais l'artifact ne couvrait pas le **dernier** appel réseau du job.
`generate_group_profiles.py` fetche son **propre** roster complet, et c'est lui
qui est tombé : step `Générer les profils de groupe parlementaire réel`,
17:01:55 → 17:02:51, **56 s**, `exit 1`. Tout ce qui suit — `Quality gate`, les
trois garde-fous, **`Committer et pousser`**, le déploiement — skippé. Ce n'est
pas le garde-fou de #511 cette fois : il n'a pas eu l'occasion de tourner.

Le mécanisme tient en trois lignes (`src/generate_group_profiles.py`) : les
5 groupes AN actifs partagent la clé de fetch `('deputes','16')` — les 2 groupes
Sénat sont suspendus (#516) —, donc **un** fetch raté vaut 5 échecs, donc
`exit 1`, donc pas de commit. Pour ~452 profils de candidats et les profils de
parti qui, eux, étaient corrects.

Le budget de temps confirme la cause : une passe complète réussie mesurée sur
l'arbre committé coûte ~25 s de travail utile, et le step a duré 56 s **sans
écrire une seule fiche** — soit 3 × 15 s de timeout + 2 s + 4 s de backoff, plus
le démarrage. Les trois tentatives de #519 avaient été **épuisées**.

## 2. La mesure qui tranche : le plafond était *à l'intérieur* de la distribution

`fetch_full_roster` héritait de `candidate_profile.TIMEOUT` (15 s), une
constante dimensionnée pour les pages **par candidat** : quelques Ko, servies
depuis un cache. Or `https://www.nosdeputes.fr/deputes/json` fait **814 Ko** et
est **généré à la volée** — son coût est presque tout entier du
*time-to-first-byte*.

24 appels mesurés le 24/08/2026 :

| Plafond | Résultat |
| --- | --- |
| `timeout=30` | 3 succès / 8 — **10,7 s · 16,7 s · 18,1 s** |
| **`timeout=15` (production)** | **0 succès / 8** |
| `timeout=(15, 60)` | 3 succès / 8 — ttfb **12,2 s · 16,7 s · 17,7 s** |

**Aucune réponse sous 10 s sur 24 essais. La plus rapide : 10,7 s. La médiane
des succès : ~16,7 s. Le plafond de production : 15 s.** Ce n'était donc pas une
panne de la source — `prepare-roster-matrix` avait fetché la **même URL avec
succès** 7 minutes plus tôt dans le même run. C'était de la variance autour d'un
seuil mal placé, et **retenter trois fois sous un plafond trop bas ne rachète
pas le plafond**.

*(Réserve : ces latences ont été mesurées derrière un proxy, pas sur un runner
GitHub. Ce qui est robuste est la forme — le ttfb de cet endpoint vit autour de
15 s, pas en dessous — pas le chiffre absolu.)*

**Décision** : `group_roster._ROSTER_TIMEOUT = (TIMEOUT, 90)`, en
`(connect, read)` comme le font déjà `gouvernement_textes.TIMEOUT` et
`syceron_debates.TIMEOUT` pour leurs gros dumps. Le **connect reste à 15 s**,
délibérément : c'est lui qu'emprunte la détection déterministe de #516
(poignée de main TLS → `SSLError`), et un verdict qui fonde une suspension
d'extraction doit remonter vite. Pire cas ajouté : 3 × 90 s + 6 s ≈ 4,5 min sur
un job qui en a 60.

**Écarté — relever `candidate_profile.TIMEOUT`.** Il gouverne jusqu'à ~250
requêtes par candidat : le passer à 90 s ferait payer six fois plus cher chaque
page morte, sur un job déjà borné par `--budget-collecte-secondes`.

## 3. Supprimer le fetch, pas seulement le fiabiliser

Il restait **deux** fetchs de la même liste par run : `prepare-roster-matrix`
(→ artifact) et `generate_group_profiles.py`. Le second est supprimé par le même
patron que #519 : `generate_roster_candidats.py --rosters-bruts-out` publie la
liste **brute** (avant filtrage par sigle) dans le **même** artifact,
`generate_group_profiles.py --rosters-bruts` la lit.

Ce n'est pas qu'une économie de requête, et c'est le même défaut de correction
que #518 : la fiche de groupe était bâtie sur une composition lue **~7 min
après** celle qui avait servi à collecter les profils. Une entrée ou une sortie
de groupe entre les deux, et la composition publiée diverge du corpus collecté,
**sans qu'aucune étape n'échoue**.

Quatre points de conception, tous verrouillés par des tests :

- **les deux fichiers partent ensemble, sous la même autorisation d'écriture.**
  Publier le brut malgré les anomalies de #511 rendrait au consommateur une
  composition qui n'est pas celle du corpus collecté ;
- **une clé en échec n'est jamais sérialisée.** Écrite en liste vide, elle
  deviendrait chez le consommateur une composition de **0 membre mesurée** — la
  forme même de l'incident de #511. Son absence le fait retomber sur son propre
  fetch, ce qui est le mode dégradé voulu ;
- **le repli est par clé, pas par fichier** : le Sénat suspendu n'a pas à faire
  refetcher l'AN ;
- **`None` se sérialise en chaîne vide**, jamais en `"None"` ni `"courante"` —
  qui sont des valeurs de législature possibles au relire.

Un fichier annoncé mais illisible ne fait **pas** échouer : il fait retomber sur
le fetch, avec un `::warning::`. Un transit qui cesserait de fonctionner en
silence redeviendrait deux fetchs à des instants différents, c'est-à-dire le
défaut de départ.

## 4. Une donnée non écrite n'annule plus la publication d'une donnée écrite

Quand le fetch de roster échoue, **aucune fiche de groupe n'est touchée** : les
7 fiches committées restent en place, intactes. Faire tomber tout le job prive
alors le run du commit des profils de candidats et de parti, qui sont corrects.
C'est mot pour mot l'argument déjà écrit dans `generate-data.yml` pour le step
gouvernement (#427).

`generate_group_profiles.py` distingue donc les deux échecs par son code de
sortie — `EXIT_ROSTER_INDISPONIBLE = 2` (même valeur que
`generate_gouvernement_profiles.EXIT_COLLECTE_INCOMPLETE`, pour que le workflow
les traite pareil) quand **tous** les échecs sont « roster indisponible », `1`
dès qu'une génération de groupe a réellement planté. Un mélange des deux rend
`1` : rendre `2` ferait passer un plantage de code pour un aléa de source.
`generate_all` retourne pour cela un `ResultatGeneration` et non un compte — un
compte agrégé ne dit pas si le run a manqué de réseau ou de code.

**Le filtrage se fait dans le step, sur le code, et non par un
`continue-on-error: true`.** C'est le seul écart à la solution telle qu'elle
avait été proposée, et il en préserve l'intention : `continue-on-error`
avalerait **aussi** le code 1, ce qui annulerait la distinction que le code 2
vient d'introduire et laisserait committer une fiche périmée sans que rien ne
bloque. Le prix est que le step reste **vert** sur un code 2 ; ce qui rend
l'incident lisible n'est de toute façon pas la couleur d'un step — elle ne dit
jamais *laquelle* des fiches a manqué — mais les annotations du §5, plus une
ligne dans `$GITHUB_STEP_SUMMARY`.

**Aucune tolérance ajoutée** : la section 4 du quality gate continue de
hard-failer sur une fiche de groupe absente ou invalide.

## 5. L'échec se lit sans télécharger le log

Diagnostiquer ce run a demandé de **rejouer le script localement** : la seule
annotation exposée par l'API était `Process completed with exit code 1`. C'est
l'illisibilité que #518 devait fermer, dans un script que #518 n'avait pas
couvert.

`generate_group_profiles.py` émet donc, via `src/gha.py` :

| Situation | Annotation |
| --- | --- |
| Clé de roster tombée | une `::error:: ROSTER_INDISPONIBLE` nommant la clé et le type d'exception — **une seule par clé**, pas une par groupe : 5 groupes AN la partagent, et répéter la cause la noierait sous ses conséquences |
| Fiches non régénérées | une `::error::` de récapitulation par clé, **nommant chaque `groupe_id` sauté** |
| Génération qui plante | une `::error:: GROUPE_EN_ECHEC` nommant le `groupe_id` et l'exception |
| Rosters bruts illisibles | une `::warning:: ROSTER_BRUT` — le run continue en refetchant, donc rien d'autre ne le dirait |

Un groupe **suspendu** (#516) n'annote rien : c'est une décision écrite, pas une
panne, et l'annoter à chaque run userait le canal.

## 6. Ce que ce chantier ne fait pas

- **Il ne relance pas le run.** Relancer passe souvent — 3 succès sur 8 par
  tentative dans les mesures du §2, et le step en fait 3 — mais c'est un pari
  qui se rejoue à chaque run, pas un correctif.
- **Il ne touche pas au budget de `extract-roster-groupes`** ni à l'ordre
  d'`extract-senat` : deux items de `ROADMAP.md` sans rapport.
- **Il ne migre pas les trois annotateurs privés** vers `gha.py`, pour la même
  raison qu'à #519.

Verrouillé par `tests/test_roster_timeout_lecture.py` (6),
`tests/test_rosters_bruts_transit.py` (13),
`tests/test_groupes_roster_indisponible.py` (18) et 3 tests ajoutés à
`tests/test_ci_roster_unique_par_run.py`. Suite complète : **2 109 tests**.

---

