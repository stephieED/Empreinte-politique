<a id="fusion-conserve-les-champs-absents-997"></a>
# Un champ qu'une contribution ne porte pas n'est plus effacé (#997) (2026-09-19)

`2026-09-19`

> **En bref** — `merge_raw_profile` construisait son résultat par `dict(new)` :
> tout champ que la contribution ne portait pas était **effacé**. Invisible
> tant que chaque artifact publiait le profil entier. Depuis les contributions
> réduites, une source qui parle en dernier efface ce qu'une source précédente
> a apporté. Mesuré sur le run 35442990475, corpus entier : **`mandat_senatorial`
> perdu sur 2 profils**, Bruno Retailleau et Jean-Luc Mélenchon.

## Ce qui s'est passé

[`contribution-par-champs-997`](./contribution-par-champs-997.md) a fait que
`extract-senat` ne publie plus que `mandat_senatorial` et
`extract-mandats-locaux` que `mandats_locaux`. Le correctif a bien atteint son
but — les stades corrigés traversent enfin, Édouard Philippe passe de 127 à
**9** `examine_commission` — mais il a révélé un défaut plus ancien, et cette
fois à ses dépens.

`--dirs` place `_artifacts/senat` **avant** `_artifacts/mandats-locaux`. La
contribution des mandats locaux ne porte pas `mandat_senatorial` ; `dict(new)`
l'a donc effacé, juste après que le Sénat l'eut posé.

**`mandats_locaux` n'a survécu que parce que sa source passe en dernier.** Ces
deux champs sont les seuls que le traitement explicite de `merge_raw_profile`
ne rattrape pas : c'était de la chance, pas un contrat.

## Décision

`merged = {**old, **new}` au lieu de `dict(new)`. **On part de ce qu'on sait,
la contribution écrit par-dessus.**

Ce que cela ne change pas : un champ que `new` porte gagne, **y compris vide** —
vider délibérément reste possible, et les protections du vide vivent ailleurs
(`CHAMPS_PROTEGES_DU_VIDE`, `_prefer_non_empty`). Seuls les champs **absents**
de `new` sont désormais conservés.

## Garde

`tests/test_contribution_par_champs_997.py` : le cas Retailleau — le Sénat
apporte, les mandats locaux parlent après, le champ survit — et sa réciproque,
une contribution peut toujours vider un champ qu'elle porte. Le premier échoue
sur le code d'avant, vérifié en le restaurant.

## Ce qu'il reste à faire, et qui ne se fait pas par du code

Le corpus publié au commit `de60956d2` **ne porte plus** `mandat_senatorial`
sur ces 2 profils. Un correctif de code n'atteint pas le corpus : il faut un
run pour que la collecte le repose. Tant qu'il n'a pas tourné, la fiche de ces
deux profils ne peut pas dire leur passage au Sénat.
