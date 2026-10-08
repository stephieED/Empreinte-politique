<a id="majorite-d-en-face-non-nommee-770"></a>

# « Ce qu'il a voté » ne nomme pas le groupe majoritaire d'en face (#770) (2026-10-07)

`2026-10-07`

> **En bref** — `docs/decisions/votes-par-periode-politique-328.md` laissait ouvert un point : nommer, sur chaque période de votes d'un candidat, le groupe majoritaire face auquel il votait (« majorité REN »). La propriétaire l'a refusé le 07/10/2026, et #770 est fermée sans suite. **À ne pas reproposer**, même si la donnée existe désormais pour deux législatures.

## Le contexte

#770 (07/09/2026) constatait que la donnée manquait. Remesuré le 07/10/2026 sur
`main` 3c43be5c1, sur les 31 fiches de groupe publiées :

| Législature | Position des groupes dans les fiches |
| --- | --- |
| XVe | renseignée sur les 10 fiches, dont un `majorite` (LAREM) |
| XVIe | renseignée sur les 10 fiches, dont un `majorite` (REN) |
| XVIIe | `non_declaree` sur les 11 fiches : l'Assemblée ne la déclare pas |
| XIVe | aucune fiche de groupe |

Deux des constats de l'issue ne tenaient donc plus : la donnée existe pour la
XVe, et couvre tous les groupes de la XVIe.

## La décision

À la question « voulez-vous que la section nomme le groupe majoritaire d'en face
là où l'Assemblée le déclare, ou ferme-t-on #770 ? », la propriétaire :
« non. ferme ».

La fiche dit toujours depuis quels bancs la personne votait : les votes sont
regroupés par gouvernement, « pour distinguer ceux émis dans la majorité, la
minorité ou l'opposition ».

## Ce qui n'a pas été vérifié

La raison du refus n'a pas été donnée. La section a été lue dans le code, pas à
l'écran.
