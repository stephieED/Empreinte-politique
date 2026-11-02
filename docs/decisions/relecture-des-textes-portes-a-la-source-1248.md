# Relire à la source le stade et les dates de quelques textes portés, à chaque run (#1248, lot 4) (2026-11-02)

`2026-11-02`

> **En bref** — complète les lots 1 à 3 de #1248. À chaque run, dix dossiers législatifs sont tirés (sept récents, trois sur tout le corpus), et chaque profil qui en publie un texte porté est confronté à la frise d'étapes de la page du dossier : quatre règles, toutes des inégalités, car `date_min` n'est pas la date de dépôt et la page ne date que le début de chaque étape. Le rôle de la personne n'est pas relu. Une étape plus récente que nos dossiers n'est pas un écart. Mesuré le 02/11/2026 : 40 dossiers tirés au hasard concordent (14 de la XVIIe, 9 de la XVIe, 7 de la XVe, 10 de la XIVe) ; deux tirages d'essai, 25 textes portés concordants sur 25.

## Contexte

Lot choisi et périmètre validé par la propriétaire le 02/11/2026 : « oui, valide le lot 4 », sur la proposition « limité au stade et aux dates (le rôle de la personne n'est pas relu), avec 10 textes par run, 7 récents et 3 sur tout le corpus ». La page d'un dossier législatif sur le site de l'Assemblée (le `source_url` de chaque texte porté) donne une frise d'étapes : chaque étape a un code (`L17-AN1-…`, `L17-PROM-…`), un titre (« Dépôt à l'Assemblée nationale », « Promulgation de la loi ») et une date de début, parfois suivie de son issue (« Texte adopté ✅ », « adopté définitivement »). Un texte seulement déposé n'a pas de frise ; la page le dit en une phrase (« déposée le jeudi 23 juillet 2026 »). La page ne nomme aucun député.

## Ce que les mesures ont corrigé dans la règle

| Règle d'abord envisagée | Ce que la mesure a montré | Règle retenue |
| --- | --- | --- |
| `date_min` égale à la date de dépôt | 39 sur 40 ; le 40e est le budget de la Sécurité sociale 2026 (`date_min` au 02/07/2025, dépôt au 14/10/2025) : `date_min` est le plus ancien acte du dossier (`_collect_acteur_roles`), et un rapporteur est nommé avant le dépôt | `date_min` pas postérieure au dépôt |
| `date_max` égale à la dernière date de la page | la page date le **début** des étapes, pas leurs actes | aucune étape de la page après `date_max` |
| la même, sans tolérance | au premier essai, le projet de loi constitutionnelle sur la Corse : une deuxième lecture commencée le 28/10/2026, nos dossiers à jour au 26/10 (`an.dossiers`, fichier de fraîcheur, #1389). Une étape pas encore relue, pas une erreur | une étape postérieure à `an.dossiers` est comptée à part, jamais en écart |

S'y ajoutent deux règles d'issue : une promulgation présente des deux côtés ou d'aucun (40 sur 40), et une adoption définitive de la page qui doit être publiée comme une adoption. La seconde attrapera les `sort` non résolus que la page résout : **147 des 10 882 dossiers** publiés portent `sort_non_resolu.motif = fam_code_inconnu` (mesuré le 02/11/2026). La résolution sur les allocations chômage des frontaliers en est un exemple, « adopté définitivement » selon la page. Ces cas ne reviendront qu'un tirage sur huit environ, et chacun est un vrai manque : ils restent des écarts.

## Décision

`src/relecture_textes_source.py`, dans `merge-and-pivot`, après la relecture des amendements, sur le modèle des trois autres : rien ne bloque, une page muette est « non vérifiée », le rapport part dans le résumé et dans l'artifact `relecture-textes`, et une issue (`textes-en-ecart-avec-la-source`) est tenue sans jamais être fermée par le run. **Chaque profil qui publie le dossier est relu**, pas seulement le dossier : un profil resté sur une ancienne version du dossier est exactement ce que la fusion additive peut produire. Les textes européens, qui n'ont pas de page de dossier de l'Assemblée, sont écartés par leur adresse.

## Alternatives écartées

- **Relire le rôle de la personne** : une seconde page par texte (le document déposé), écartée pour ce lot sur la validation de la propriétaire.
- **Relire le stade fin (commission, séance)** : la frise ne donne au premier niveau que les lectures, pas leurs sous-étapes.

## Non vérifié

- La forme de la page d'un dossier retiré, ou caduc en fin de législature.
