# Une baisse de tags agrégés bloque sur sa cause, lue dans les profils

`2026-10-14`

> **En bref** — le run planifié du 13/10/2026 a échoué au contrôle de perte sur **4 fiches agrégées à −1 tag** (groupes DR-17 et EPR-17, lignées LR et REN) : l'intitulé que la source avait renommé avait quitté 5 profils, que #1275 laissait déjà passer. Une baisse de `tags_thematiques_agreges` ne bloque plus quand **chaque** intitulé disparu de la fiche a aussi quitté un profil dans le même run, et qu'aucun profil n'a perdu de tag ni d'intervention en bloquant (`listes_des_tags_des_profils`). Complète `perte-de-tags-bloque-sur-sa-cause`, qui l'avait annoncé.

## Contexte

`perte-de-tags-bloque-sur-sa-cause` (12/10/2026) a fait bloquer la baisse de
`tags_thematiques` d'un profil sur sa cause : une intervention perdue, ou moins
d'interventions qui alimentent la liste. Elle écrivait elle-même sa limite : la
fiche de groupe ne porte pas les interventions, la cause ne s'y lit pas, et
« un renommage qui retire un intitulé de **tous** les membres d'un groupe
bloquera encore ».

C'est arrivé au run suivant. Mesuré dans l'artifact `diff-profils` du run
`38431031465` (planifié, 13/10/2026, fin à 20 h 30, heure de Paris) :

| Étage | Fiches | Intitulé disparu | Verdict du run |
| --- | --- | --- | --- |
| Profils | 5 (Bergé, Bonnivard, Kasbarian, Legrain, Braun-Pivet) | « … au phénomène des violences sexuelles… » ; et « accord multilatéral … globe » chez Braun-Pivet | passe, « sans perte en amont » |
| Groupes | DR-17 (1 040 → 1 039), EPR-17 (1 864 → 1 863) | les mêmes | **bloque** |
| Groupes | LFI-17 (996 → 996) | « … au phénomène des… » | nommé, compte égal |
| Lignées | LR (5 928 → 5 927), REN (8 500 → 8 499) | « … au phénomène des… » | **bloque** |

Sur les 1 403 profils du run, `interventions` passe de 1 309 363 à 1 309 492 :
rien n'est perdu en amont.

## Décision

**La cause d'une baisse agrégée se lit dans la collection des profils.**
`Collection.listes_des_tags_des_profils` nomme les listes d'une fiche agrégée
dont la matière est le `tags_thematiques` des profils — `tags_thematiques_agreges`
pour les groupes, les lignées et les partis. `comparer_tout`, qui voit toutes les
collections d'un run, lève le blocage d'une telle baisse quand :

1. aucun profil n'a perdu en bloquant sur `tags_thematiques` ou `interventions` ;
   **et**
2. **chaque** intitulé disparu de la fiche (comparé par `cle_tag_thematique`) a
   aussi disparu d'au moins un profil dans le même run.

La baisse est alors rapportée dans une section à part (« expliquée(s) par les
profils »), ses intitulés nommés par le relevé de #823. Un seul intitulé de la
fiche qui n'a quitté aucun profil, des profils non lus, des valeurs non relevées :
la baisse bloque.

| Cas | Profils | Fiche agrégée | Verdict |
| --- | --- | --- | --- |
| Le renommage du 13/10 | intitulé disparu, rien perdu en amont | −1, le même intitulé | signalé |
| Un membre sorti de la fenêtre, une règle d'agrégation changée | rien | −1 | **bloque** |
| Deux intitulés disparus, un seul expliqué | un intitulé | −2 | **bloque** |
| Interventions effacées (#470) | perte bloquante | −n | **bloque**, aux deux étages |
| `membres` qui baisse en même temps | — | −1 tag, −1 membre | **bloque**, sur `membres` |

Rejoué le 14/10/2026 sur `pivot_data/` au 12/10 (1 403 profils, 31 fiches de
groupe, 15 lignées) : les intitulés relevés par le run retirés des 5 profils, par
renommage de leurs interventions, et des 5 fiches agrégées. Avec la règle, aucun
constat ne bloque. Sans retirer « globe » des profils, EPR-17 bloque et les
quatre autres passent. C'est une **simulation** : la sortie d'un run en échec
n'est pas publiée.

## Ce que la décision ne couvre pas

- **Une coïncidence dans le même run.** Un intitulé quitte un profil par
  renommage pendant qu'il quitte un groupe pour une autre raison — la parole d'un
  autre membre sortie de la fenêtre d'appartenance (#1073). La règle lit les deux
  comme un seul renommage. Il faudrait que le même intitulé tombe des deux façons
  le même jour.
- **Les fiches de gouvernement** ne relèvent pas `tags_thematiques_agreges` au
  contrôle de perte : rien à étendre.

## Alternatives rejetées

- **Retirer `tags_thematiques_agreges` des listes stables.** C'est la liste qui a
  vu l'échange de #823 sur REN-16 et EPR-17 ; elle redeviendrait muette.
- **Ne lever le blocage que si la fiche n'a perdu aucun membre.** Nécessaire mais
  pas suffisant : une fenêtre d'appartenance qui bouge retire des intitulés sans
  retirer de membre. Le nom de l'intitulé est ce qui relie les deux étages.
- **Relancer avec `allow_declared_losses`.** Désarme le contrôle pour tout le
  run, et le cas reviendra au prochain intitulé réuni par la source.
