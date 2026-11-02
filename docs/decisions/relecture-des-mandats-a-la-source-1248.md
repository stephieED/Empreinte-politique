# Relire à la source quelques mandats de député, à chaque run (#1248, lot 2) (2026-11-02)

`2026-11-02`

> **En bref** — complète `relecture-des-votes-a-la-source-1248`. À chaque run, cinq députés sont tirés (1 candidat déclaré, 3 députés de la XVIIe, 1 des législatures précédentes), et leurs périodes de mandat de député sont comparées une par une à la page « fonctions » de l'Assemblée. Même régime que le lot 1 : rien ne bloque, une issue est tenue en cas d'écart, et le run ne la ferme jamais. Le premier essai, sur les 18 candidats déclarés qui ont été députés, a trouvé les erreurs que #1412 a corrigées avant que le contrôle n'entre dans le run.

## Contexte

Le lot 1 relit les positions de vote. La propriétaire a choisi le lot 2 le 02/11/2026 : les mandats de député, ce que dessine la frise de chaque fiche. La seconde route est la page « fonctions » de chaque député sur le site de l'Assemblée. Elle donne, législature par législature, chaque période où la personne a siégé, avec sa cause de début et de fin (« Mandat du 20 juin 2012 (élections générales) au 21 juillet 2012 (Nomination comme membre du Gouvernement) »). La collecte, elle, lit l'archive AMO30.

## Décisions de la propriétaire, 02/11/2026

| Question | Réponse |
| --- | --- |
| Quel fait au lot 2 | les mandats de député |
| Tirage | d'abord « 4 au hasard parmi tous et 1 dans la liste des candidats », puis « 3 parmi les députés de la 17e et 1 sur les précédentes ». Lu ainsi : 1 candidat déclaré, 3 députés qui ont siégé dans la XVIIe, 1 qui n'y a pas siégé |
| Ce que le contrôle compare | chaque période, et non la première et la dernière date d'une législature : comparer l'enveloppe aurait masqué les erreurs. Elle l'a dit ainsi : « tu es en train de dire que les périodes de nos json sont fausses non ? » |

## Ce que le premier essai a établi

Sur les 18 candidats déclarés qui ont été députés, le corpus publiait des passages au gouvernement comme des mandats de député (Cazeneuve, Batho, Becht, Bertrand), datait des suppléants du jour de l'élection (Philippe, Guedj), et portait un doublon (Brun). Ces erreurs venaient de `mandats-electifs-liste-complete-640` et ont été corrigées par #1412 (`periodes-de-mandat-de-depute-1412`). Avec cette correction, 17 des 18 concordent ; le 18e est le mandat de Bertrand de 2002-2004, que l'archive AMO30 ne porte pas.

Sur le corpus d'avant #1412, deux tirages d'essai le 02/11/2026 (graines 1 et 2, 10 députés) : 8 députés concordent, et le contrôle retrouve deux cas que #1412 corrige (Batho, et Laurence Gardet, suppléante entrée en fonction le 08/10/2026 et datée du 07/07/2024).

## Décision

`src/relecture_mandats_source.py`, dans `merge-and-pivot`, après la relecture des votes :

- **La date de début lue sur la page suit la convention du corpus** (#1412) : celle de l'élection quand la période s'ouvre par une élection, celle de l'entrée en fonction sinon.
- **Seules les législatures à partir de la XIIe** sont comparées : AMO30 ne remonte pas avant le 19/06/2002, et les mandats plus anciens viennent d'une table citée à la main (#860).
- **Côté corpus, les `mandat_electif` de chambre `AN`**, estampillés ou non : une entrée non estampillée qui ne correspond à rien sur la page est aussi une erreur sur la frise.
- La page du mandat en cours d'un ancien député répond 404 : elle est tolérée, et l'archive suffit. Une page injoignable, ou sans aucune période lisible, rend le député « non vérifié ».
- Une issue à part, étiquette `mandats-en-ecart-avec-la-source`, tenue comme celle des votes. Elle n'envoie pas de notification (option A, arbitrée le 02/11/2026) : l'agent la relève en début de session.

## Alternatives écartées

- **Relire aussi les commissions**, que la page liste : des dizaines de courtes périodes de remplacement par député, qui demandent leur propre règle d'appariement. À instruire plus tard.
- **Compter le mandat manquant de Bertrand comme une divergence entre sources**, comme les non-votants du lot 1 : il manque bien sur la frise, et le cas ne revient qu'avec ce député.

## Non vérifié

- La forme de la page pour un député dont le mandat a été annulé (Bertrand Petit) n'a pas été relue.
- Le contrôle n'a pas encore tourné sur le corpus corrigé par #1412 : il le fera au premier run qui publie les deux.
