# Relire à la source les signataires de quelques amendements, à chaque run (#1248, lot 3) (2026-11-02)

`2026-11-02`

> **En bref** — complète `relecture-des-votes-a-la-source-1248` et `relecture-des-mandats-a-la-source-1248`. À chaque run, dix amendements sont tirés (sept des trente derniers jours, trois sur tout le corpus, XVe à XVIIe législature), et leurs signataires sont relus sur la page de l'amendement : l'index publié (premier signataire, cosignataires), puis le rôle porté par le profil de chaque signataire. Même régime que les lots 1 et 2. Deux tirages d'essai, le 02/11/2026 : 712 signatures concordantes, 0 écart.

## Contexte

La propriétaire a choisi les signatures d'amendement pour le lot 3, le 02/11/2026 (« ok avec les signatures d'amendement »). Le corpus publie un amendement de deux façons : l'index de la législature (`pivot_data/amendements/<n>.json`, avec `premier_signataire`, et `<n>.cosignatures.json`), et sur chaque profil, l'amendement avec le rôle de la personne (`auteur_principal` ou `cosignataire`). C'est ce que lit la section amendements d'une fiche. La collecte lit les archives open data des amendements.

La seconde route est la page de l'amendement sur le site de l'Assemblée. Demandée par son identifiant (`/dyn/17/amendements/AMANR5L17…`), elle redirige vers son adresse lisible (`/dyn/17/amendements/3018/AN/1222`). Son bloc « Déposé par » nomme les signataires dans l'ordre, premier signataire d'abord, chacun avec le lien vers sa fiche.

## Ce qui a été mesuré, le 02/11/2026

| Mesure | Résultat |
| --- | --- |
| Page d'un amendement, XVe, XVIe, XVIIe (dont un amendement de rapporteur) | répond, premier signataire conforme à l'index |
| Page d'un amendement de la XIVe, par identifiant | **404** : la XIVe est exclue du tirage |
| Types de déposant dans l'index de la XVIIe | 132 116 `depute`, 8 441 `commission_rapporteur` ; aucun amendement du gouvernement |
| Deux tirages d'essai (graines 1 et 2, 20 amendements) | 712 signataires lus, 712 concordants (index et profil), 0 écart, 0 hors périmètre |
| Coût | 2 min et 448 Mio en local, en ne chargeant les cosignataires que des amendements tirés ; 1,1 Gio s'ils sont tous gardés |

## Décision

`src/relecture_amendements_source.py`, dans `merge-and-pivot`, après la relecture des mandats :

- **Le tirage reprend le partage arbitré pour les votes** : sept amendements des trente derniers jours, trois sur tout le corpus. La propriétaire ne l'a pas arbitré pour les amendements ; il se change dans le module (`NB_RECENTS`, `NB_TOTAL`).
- **Deux comparaisons** : la page contre l'index (même premier signataire, mêmes cosignataires), puis la page contre les profils. Chaque signataire qui a un profil doit y porter l'amendement avec le bon rôle, et un profil qui le porte sans que la page le nomme est un écart. Les profils se retrouvent par `raw_data/correspondance_acteurs_an.json`. Un signataire sans profil est « hors périmètre ».
- La lecture s'arrête à la première section du texte de l'amendement : un lien vers une fiche de député plus bas sur la page n'est pas un signataire.
- Une issue à part, étiquette `amendements-en-ecart-avec-la-source`, tenue comme les deux autres ; le run ne la ferme jamais.

## Alternatives écartées

- **Comparer seulement l'index** : la fiche lit le profil. Un rôle faux sur un profil passerait inaperçu.
- **Inclure la XIVe** en cherchant l'adresse lisible de ses amendements : elle ne se déduit pas de l'identifiant (`AMANR5L14SEA644420B4271P0D1N596`), et la XIVe est close.

## Non vérifié

- La forme de la page pour un amendement retiré avant publication, ou déposé par le gouvernement (absent de l'index aujourd'hui).
- Le coût sur le runner : mesuré en local seulement.
