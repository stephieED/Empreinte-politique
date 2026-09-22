<a id="reprise-archive-figee-bornee-en-temps-1100"></a>
# La reprise d'une archive figée se borne en temps, et le message ne dit plus « indisponible » (#1100) (2026-09-22)

`2026-09-22`

> **En bref** — `extract-amendements-an` a abandonné l'archive de la XIVe après 5 minutes sur un job qui en a 30, en concluant « la source semble indisponible ». Remesuré : la source **coupe par intermittence**, et la troisième tentative sur la plage qui avait échoué rend la plage entière. La reprise se borne désormais sur le temps restant du job, et le message d'abandon nomme les octets obtenus et le temps écoulé.

## Constat

Run `35767700159` du 22/09/2026, job `extract-amendements-an` : la XVIIe se
construit entière (125 014 amendements, 35 064 mots), puis le contenu de la
XIVe échoue. `data.assemblee-nationale.fr` a servi 12 224 778 des 103 716 698
octets, puis plus rien — ni par plages `Range`, ni en `GET` séquentiel — pendant
trois cycles, et le job a rendu la main **à 18h42 pour un début à 18h37**.

Remesuré le même jour à 23h10 depuis un poste, sur la plage exacte qui avait
échoué (offset 12 224 778, 4 194 192 octets) :

| Tentative | Octets servis |
| --- | ---: |
| 1 | 722 945, coupée |
| 2 | 2 892 049, coupée |
| **3** | **4 194 192 — complète** |

`HEAD` répond 200 avec le `content-length` attendu. La source n'est donc pas
indisponible : elle coupe, et la reprise finit par passer.

## Décision

1. `_download_amendements_zip` accepte `budget_secondes`. Quand il est donné,
   **il remplace le compte de cycles** : tant qu'il reste du budget, on
   réessaie. L'attente entre deux cycles est plafonnée par ce qui reste, pour
   que la dernière sieste ne fasse pas dépasser le budget — un job tué n'écrit
   rien, un job qui échoue déclare.
2. Hors CI, `budget_secondes` reste `None` et le comportement d'avant ce lot
   tient : là, attendre longtemps est le seul remède qui marche, et personne ne
   tue le processus.
3. Le budget vient du **temps restant du job** :
   `build_amendements_index.budget_telechargement_secondes()` lit
   `JOB_START_EPOCH`, posé par `bootstrap-extraction`, retranche le plafond du
   job (`JOB_TIMEOUT_MINUTES = 30`) et une marge de 420 s pour construire le
   contenu et téléverser l'artifact. Plus de budget : la législature n'est pas
   tentée, et le run suivant la reprend.
4. **Le message d'abandon change**, parce que c'est lui qui a induit en erreur :
   il nomme les octets obtenus sur le total, le temps écoulé, la borne atteinte,
   et dit que la source **coupe** au lieu d'être indisponible.

Le plafond du job est **recopié** dans le module, et `tests/test_budget_archive_figee_1100.py`
compare la copie au `timeout-minutes` du YAML : le workflow est lu sur le dépôt
public et se publie à la main, donc il ne peut pas être la source à l'exécution.

## Alternative rejetée

**Augmenter `AMENDEMENTS_SOURCE_STALL_MAX_CYCLES`** : une constante en nombre de
cycles ne sait pas combien de temps un cycle prend — 5 minutes ici, plusieurs
dizaines ailleurs selon la taille des segments et le débit du runner. C'est la
leçon du budget réseau du portail européen (#1064) : ce qui est borné en temps se
borne en temps.
