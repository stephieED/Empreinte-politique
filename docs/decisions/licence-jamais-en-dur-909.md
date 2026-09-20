<a id="licence-jamais-en-dur-909"></a>
# Une étiquette de licence écrite en dur survit à la source qu'elle décrit (#909) (2026-09-13)

`2026-09-13`

> **En bref** — `src/mep_profile.py` inscrivait `meta.licence_donnees = "Open Data — Parltrack (CC0 / Open Database License)"`. C'est faux : les dumps JSON de ParlTrack sont sous **ODbL v1.0**, avec partage à l'identique, et le CC0 annoncé l'efface. Le plus notable n'est pas l'erreur — [`licences`](licences.md) l'avait **relevée nommément** en instruisant #530, et l'avait laissée « à corriger dans un ticket dédié » qui n'a jamais été ouvert. Elle a donc survécu quatre lots. Mesuré le 13/09/2026 sur `origin/main` `0a919cb67` : **0 des 1 177 profils publiés** (32 candidats déclarés, 1 145 membres de roster) ne porte cette étiquette, parce que tout profil européen atteint le corpus par un chemin qui repasse par `appliquer_licence_donnees`. Le défaut est donc **latent**, pas publié — et il le reste tant que personne n'utilise le `--out` que le module documente lui-même. La correction tient en un appel ; ce qui se décide ici, c'est le **gel**, qui porte sur la famille et non sur le cas.

## 1. Pourquoi la dérivation de #530 ne suffisait pas

[`licence-lot-6-530`](licence-lot-6-530.md) a fait de `meta.licence_donnees` un champ dérivé : `src/licences.py` tient les cinq étiquettes canoniques, et `appliquer_licence_donnees(profil)` recompose la chaîne depuis `sources[]` après chaque étape qui les touche. Huit modules l'appellent.

`mep_profile.py` n'est pas l'un d'eux — il n'importait même pas `licences`. Et il est le seul constructeur de profil qui soit un **script CLI autonome** : aucun module ne l'importe, son `main()` écrit là où l'appelant le demande, et son propre docstring documente le chemin qui contourne tout :

```
python src/mep_profile.py --name "…" --out pivot_data/profiles/<slug>.pivot.json
```

`pivot_data/profiles/` est la seule couche que `web/` lit. Ce chemin ne recompose rien.

## 2. Ce que la mesure dit, et ce qu'elle ne dit pas

| Étiquette portée par un profil publié | Profils |
| --- | ---: |
| contenant `CC0` | **0** |
| `… + ODbL v1.0 (ParlTrack — https://parltrack.org/dumps)` | 6 |

**« Zéro publié » n'est pas « corrigé ».** C'est la mesure d'un chemin d'écriture non emprunté, et elle a la durée de vie de cette abstention. Un tel constat ne clôt rien : il dit seulement que la correction n'a pas d'effet sur le corpus du jour, ce qui la rend sûre à faire.

## 3. La décision : geler la famille, pas le cas

Le correctif est un import et un appel. Le test aurait pu être « `normalize_parltrack` produit `LICENCE_PARLTRACK` » — il l'est, et il ne suffit pas : il ferme le module par lequel on est entré, et laisse ouverte la porte par laquelle le prochain constructeur de profil entrera.

`tests/test_licence_jamais_en_dur_909.py` parcourt donc **l'AST de chaque module de `src/`** et refuse toute affectation de `licence_donnees` à une chaîne littérale. Trois conséquences voulues :

- **`licences.py` est le seul module exempté**, nommément. L'exempter par une liste ferait de chaque nouvel exempté un référentiel concurrent — précisément ce que #530 a démonté.
- **Une f-string compte comme un littéral.** Composer l'étiquette sur place est la même faute par un autre chemin.
- **Un appel n'en est pas une**, et une constante importée de `licences` non plus : c'est le référentiel qui parle.

Le test est paramétré par module — 97 cas — pour que l'échec nomme le fichier fautif et sa ligne, et non « un module quelque part ».

## 4. L'alternative rejetée : étendre le gel à toute mention de licence

`src/couverture_profil.py:856` compose une phrase de preuve qui cite « dumps ParlTrack (parltrack.org/dumps, ODbL v1.0) ». C'est du texte, il est **exact**, et il n'est pas une étiquette de champ. Un gel qui interdirait toute occurrence d'un nom de licence hors `licences.py` l'attraperait, avec dix-sept commentaires et docstrings qui expliquent la règle — et il rendrait la règle impossible à documenter dans le code qu'elle gouverne.

Le gel porte donc sur ce qui est **écrit dans la donnée**, jamais sur ce qui est écrit à côté. La prose publiée a son propre garde-fou, et c'est un autre problème : [`mesure-publiee-devenue-fausse-886`](mesure-publiee-devenue-fausse-886.md) l'a posé la veille.

## 5. Ce que l'incident dit du reste

Un point de dette relevé dans un fichier de décision, sans issue pour le porter, **n'existe pas**. Celui-ci était écrit noir sur blanc, avec son numéro de ligne, dans un document que le dépôt indexe et que les sessions relisent. Il a tenu quatre lots. La même semaine, #908 a été ouverte pour la raison inverse et explicite : « aucune issue ne portait ce reste — il ne vivait que dans un docstring de module et dans une passation, c'est-à-dire nulle part où on le cherche. »
