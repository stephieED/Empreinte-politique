<a id="rattachement-par-periode-fiche-candidat-1329"></a>

# La fiche candidat relie chaque rôle à sa législature et à son gouvernement, par la période qu'il recouvre (#1329) (2026-10-26)

`2026-10-26`

> **En bref** — Dans « Détails du parcours » de la fiche candidat, chaque siège de député mène désormais à la fiche de sa législature, et chaque fonction gouvernementale à celle de son gouvernement, nommé comme sur sa fiche (« Gouvernement Philippe II » au lieu de « gouvernement PHILIPPE 2 »). Les mandats d'un profil ne portent ni l'identifiant de leur législature ni celui de leur gouvernement ; or ni deux législatures ni deux gouvernements ne se chevauchent : un rôle se rattache à **la période qu'il recouvre le plus longtemps** (`src/utils/rattachement.js`), un fait de calendrier et non une lecture de l'intitulé (`regrouper-nest-pas-joindre-639`). Mesuré le 26/10/2026 sur les 34 candidats du manifeste : les 20 appartenances à un gouvernement sont rattachées, le gouvernement trouvé étant chaque fois celui que nomme l'intitulé ; 27 des 35 sièges à l'Assemblée, les 8 autres étant antérieurs à la XIVe.

## Ce qui a écarté la date de début

La première règle rattachait un rôle à la période qui contenait sa date de
début. Un mandat de député commence le jour de l'élection, avant l'ouverture de
la législature : Gabriel Attal, élu le 18/06/2017, tombait dans la XIVe, close
le 20/06/2017, et son siège de juin 2022 dans la XVe. Relevé au rendu, avant la
PR ; `tests/test_rattachement_par_periode_1329.py` garde ses trois sièges.

## Ce qui reste

- La règle doit être écrite en méthodologie, avec les autres règles de
  rattachement (#1329, « Comment les objets sont reliés ») : le texte reste à
  valider avec la propriétaire.
- Le groupe d'un siège (« LaREM », « RE ») n'est pas relié : la fiche relie déjà
  le groupe affiché dans son en-tête.
