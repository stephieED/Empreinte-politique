<a id="dila-et-amo30-en-jobs-1129"></a>
# Les actes du Journal officiel et la liste des gouvernements sortent de la fusion (#1129) (2026-09-25)

`2026-09-25`

> **En bref** — Deux collectes réseau vivaient dans `merge-and-pivot`. Celle de la DILA y créait un défaut d'ordre : `textes_promulgues.py` posait `jorftext` en lisant une table que l'étape suivante mettait à jour, donc chaque run résolvait contre la table du run précédent. Les deux passent en jobs amont ; l'artifact des actes ne porte que ce que le run change, 0 ou 2 fichiers, et non les 196,4 Mo du fonds.

## Constat

Relevé en dessinant le graphe d'exécution du workflow — une figure recoupe ce
qu'une prose laisse passer. Quatre étapes de `merge-and-pivot` semblaient faire
du réseau ; vérification faite, **deux seulement** :

| Étape suspectée | Verdict |
| --- | --- |
| Index des dossiers européens | **non** — `--budget-secondes 0 --plafond-requetes 0`, aucun appel. La collecte est déjà dans `rechauffer-le-portail-europeen` (#1064) |
| « Reprendre les archives de dossiers vivantes » | **non** — présente dans trois jobs sous `cache-hit != 'true'`, c'est une réparation de rotation de clé (#762), pas une collecte |
| Actes réglementaires (DILA) | **oui** |
| Liste des gouvernements (AMO30) | **oui** |

`documents_europeens.py` interroge bien EuroVoc en SPARQL depuis la fusion ;
il réutilise les réponses du portail déjà téléchargées, mais EuroVoc est une
seconde source. Ce lot ne le déplace pas : ses libellés dérivent des concepts
que l'index vient de composer, donc du corpus.

## Ce qui décide, et qui n'est pas la propreté du graphe

`textes_promulgues.py` importe `lois_jorf` et appelle `lois_jorf.resoudre(...)`
pour poser `jorftext`, avec `--table-lois` par défaut sur la table committée.
Son étape était **avant** celle qui met cette table à jour
(`actes_reglementaires.py`). Chaque run résolvait donc les textes promulgués
contre la table du run **précédent**.

Ce n'est pas une perte — la table est committée, et les 1 015 textes promulgués
portaient tous leur `jorftext` au dernier run. C'est un décalage d'un run,
visible sur une loi promulguée depuis le run d'avant. **Sortir la DILA en amont
le règle par construction** : la table est fraîche quand la fusion la lit.

AMO30 n'avait pas ce défaut ; il n'avait simplement aucune raison d'être là.
`gouvernements_amo30.py` ne contient pas une occurrence de `pivot_data`.

## Décision

Deux jobs, `extract-actes-jo` et `extract-gouvernements`, tous deux en
`needs: epingler-le-code` et `continue-on-error: true`. `merge-and-pivot` les
attend et télécharge leurs artifacts en optionnel.

**L'artifact des actes ne porte pas le fonds.** Le répertoire publié pèse
196,4 Mo sur 238 fichiers — le transporter à chaque run aurait été un mauvais
échange. Mais un run ne relit que `MOIS_RELUS` mois : mesuré sur les trois
derniers commits de données, il en change **0 ou 2**. Le job n'emporte donc que
ce que `git status` déclare modifié, chemins conservés (`cp --parents`), et la
fusion le télécharge avec `path: .` directement sur son checkout.

**L'absence d'un artifact est une dégradation gracieuse, pas un échec.** Les
deux fichiers sont committés : la fusion retombe sur ceux du run précédent
plutôt que sur rien (§2 règle 5). C'est le même régime que les autres
téléchargements optionnels du job.

## Alternative écartée : transporter tout le répertoire des actes

`path: pivot_data/actes_reglementaires/` aurait été plus simple à lire et
n'aurait demandé aucun calcul de diff. Refusé sur la mesure : 196,4 Mo montés
puis redescendus à chaque run, pour 2 fichiers utiles — cela aurait fait le
deuxième artifact du run après `parltrack-dumps`, et l'aurait fait grossir avec
le fonds, qui ne cesse de croître.

## Ce que ce lot ne fait pas

Il ne déplace pas EuroVoc, ni les index européens, ni la réparation du cache de
dossiers — voir le tableau ci-dessus, qui dit pourquoi pour chacun. Et il ne
change rien au corpus : aucun champ, aucun schéma.
