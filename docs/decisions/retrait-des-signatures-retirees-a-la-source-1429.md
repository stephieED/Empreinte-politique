# Une signature de cosignataire retirée à la source sort du profil, aux deux étages (#1429) (2026-11-04)

`2026-11-04`

> **En bref** — complète [la liste du premier signataire](cosignataires-de-la-copie-du-premier-signataire-1429.md), qui corrigeait l'index mais pas les profils. Un retrait nommé, `src/cosignatures_retirees.py`, retire du profil brut et du pivot toute signature de cosignataire que la copie du premier signataire ne porte plus. Il tourne à chaque passe pivot, juste après l'index. Mesuré le 04/11/2026 sur la XVIIe : 10 518 des 3 550 610 signatures de cosignataire des tranches, sur 505 profils et 1 247 amendements ; vérifié contre l'archive sur le profil le plus touché.

## Contexte

Piste 1 de #1429, demandée par la propriétaire le 04/11/2026 (« 1429 », après la fusion de la piste 2, #1431). Un cosignataire qui retire sa signature reste publié comme tel : la collecte ne lui rend plus l'amendement, et la fusion additive ne retire rien, ni au brut ni au pivot. Sa fiche le compte cosignataire, et les signatures de son groupe aussi.

## Décision

| Question | Réponse | Raison |
| --- | --- | --- |
| Quelle preuve ? | la liste de la copie du **premier signataire**, celle qui fait foi dans l'index depuis #1431 | positive : l'absence d'un amendement dans la collecte d'un député ne prouve rien, une collecte peut être partielle — c'est ce que la fusion additive protège |
| Sans copie du premier signataire ? | rien n'est retiré | pas de preuve, pas de retrait (§2 règle 5) |
| Où ? | `generate_all_profiles._rafraichir_index_amendements`, après `rafraichir` | la CI ne passe que par là (#1101) ; l'index vient d'établir les listes ; les fiches de groupe, recomposées à l'étape suivante, en héritent |
| Quels étages ? | le profil brut (`profil_brut.ecrire_profil_brut`, avec l'acteur, pour garder les tranches dérivées de #691) **et** le pivot | la fusion additive protège les deux : un retrait au seul brut serait réintroduit par le pivot au run suivant |
| Un run à pertes déclarées ? | non | `amendements` est une liste **signalée** du contrôle de perte (`audit_diff_profils`) : la baisse est relevée sans bloquer |

L'index des amendements est fusionné avec le précédent ; le repère `listes_du_premier_signataire` traverse désormais cette fusion, pour que le retrait lise l'index qui sera publié.

## Mesure (04/11/2026, tranches `raw_data/profiles/*/17.json` de `main`)

| Population : signatures de cosignataire des tranches de la XVIIe | Nombre |
| --- | ---: |
| Toutes | 3 550 610 |
| À retirer (absentes de la liste du premier signataire) | **10 518**, sur 505 profils et 1 247 amendements |
| Sans copie du premier signataire, donc laissées | 47 |

Les profils les plus touchés : Estelle Youssouffa (394), Jean-Luc Warsmann (375), David Habib (369), Christophe Naegelen (357), Éric Gérard (346), Jean Bodart (338) ; Charles de Courson, le cas tiré par #1425, 291. **Vérifié contre la source** sur Estelle Youssouffa : de ses 1 935 cosignatures publiées, l'archive du 03/11/2026 en porte 1 541 et n'en porte plus 394 — le compte que donne la règle.

## Ce qui n'a pas été vérifié

- Le temps ajouté à la passe pivot : une lecture de plus des amendements de tous les profils bruts. Estimé à une ou deux minutes par passe à partir de la mesure locale (deux passes sur les 4,2 Go de la XVIIe en 170 s), non mesuré en CI.
- Les XVe et XVIe : leurs tranches sont dérivées des archives figées (#691), donc déjà conformes à la source au moment du gel ; aucun retrait n'y est attendu, aucun n'a été compté.
- Pourquoi certains députés ont tant de signatures retirées : un fait de la source, non instruit.
