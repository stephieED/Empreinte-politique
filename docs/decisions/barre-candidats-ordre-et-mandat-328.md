<a id="barre-candidats-ordre-et-mandat-328"></a>

# La barre des candidats : ordre alphabétique, et ce que la fiche peut montrer (#328) (2026-09-09)

`2026-09-09`

> **En bref** — **le tri est fait à la source** (`sync-data.mjs`) et l'UI n'en refait aucun, deux tris pour une même liste étant deux listes qui divergeront ; il porte sur `nom`, **ce que le lecteur lit**, et non sur un patronyme reconstruit — découper « Le Pen » ou « Dupont-Aignan » demanderait une règle que la source ne donne pas —, avec `sensitivity: 'base'` pour que « Édouard Philippe » se range avec les E ; **une pastille grisée dit que la fiche ne porte ni mandat à l'Assemblée ni fonction gouvernementale**, donc ni vote ni intervention ni amendement à publier — un fait sur CE QUE LA FICHE MONTRE et jamais un rang (§2 règle 1), tenu par trois choses : la pastille reste cliquable et sélectionnable (ni `disabled`, ni retrait), son infobulle écrit ce que le grisé veut dire, et la teinte est celle des métadonnées (5,5:1, AA) et non une couleur de jugement ; **deux faits, aucun deviné** — `chambres` contient `"AN"` (champ dérivé, #493) ou un mandat de catégorie `fonction_gouvernementale` —, et **le Parlement européen n'est pas l'Assemblée** : quatre candidats y ont toute leur carrière et aucun intitulé ne le dirait ; mesuré sur les 30 candidats du manifeste, **16 ont l'un des deux, 14 n'ont ni l'un ni l'autre**, et **Ségolène Royal n'est pas grisée** malgré zéro vote publié parce que le critère porte sur ce qu'elle a EXERCÉ et non sur ce que nous avons COLLECTÉ ; coût mesuré : `sync-data.mjs` lit les 30 profils (39,8 Mo) et passe de 6 à **8,4 s** ; **alternative écartée** — les masquer comme une candidature déclinée, ce qui ferait porter à l'interface un jugement de pertinence et rendrait invisible un fait publiable. 9 tests neufs.

## Le contexte

Deux demandes de la propriétaire, le 09/09/2026 : ranger les pastilles par ordre
alphabétique, et griser les candidats sans mandat à l'Assemblée ni au
gouvernement.

## L'ordre

`raw_data/candidats.json` suit l'ordre de collecte, que rien ne rend lisible :
une barre de trente pastilles où l'œil ne peut pas prédire la place d'un nom se
parcourt en entier à chaque fois.

**Le tri est fait à la source**, dans `sync-data.mjs`, et l'UI n'en refait
aucun : deux tris pour une même liste sont deux listes qui divergeront. Il porte
sur `nom` — **ce que le lecteur lit** — et non sur un patronyme reconstruit :
découper « Le Pen » ou « Dupont-Aignan » demanderait une règle que la source ne
donne pas. `sensitivity: 'base'` range « Édouard Philippe » avec les E, et non
après les Z.

## Le grisé, et pourquoi ce n'est pas un classement

Une pastille grisée dit que la fiche ne porte **ni mandat à l'Assemblée
nationale, ni fonction gouvernementale** — donc ni vote, ni intervention, ni
amendement à publier. C'est un fait sur **ce que la fiche montre**, jamais un
rang entre des personnes (§2 règle 1). Trois choses le tiennent :

- la pastille reste **cliquable, lisible et sélectionnable** : ni `disabled`, ni
  retrait de la liste — la fiche existe et s'atteint ;
- son infobulle **écrit ce que le grisé veut dire**, parce qu'une pastille plus
  pâle sans légende se lit comme un rang ;
- la teinte est celle des **métadonnées** (`--muted`), jamais une couleur de
  jugement, et le jaune signal reste réservé à la sélection. Contraste vérifié :
  `#6f6b78` sur blanc, 5,5:1 (AA).

## Deux faits, aucun deviné

| Fait | Où il est lu |
| --- | --- |
| Mandat à l'Assemblée | `chambres` contient `"AN"` — champ **dérivé** des mandats (#493) |
| Fonction gouvernementale | un mandat de catégorie `fonction_gouvernementale` |

**Le Parlement européen n'est pas l'Assemblée**, et `chambres` est la seule
chose qui les distingue : quatre candidats ont toute leur carrière au PE
(Bardella, Glucksmann, Philippot, Massard) et un intitulé de mandat ne le dirait
pas.

Mesuré sur les 30 candidats du manifeste : **16 ont l'un des deux, 14 n'ont ni
l'un ni l'autre** — dont six sans aucun mandat collecté. **Ségolène Royal n'a
aucun vote publié mais sept fonctions gouvernementales : elle n'est pas
grisée**, parce que le critère porte sur ce qu'elle a **exercé**, et non sur ce
que nous avons **collecté**. C'est toute la différence entre un fait sur la
personne et un fait sur notre corpus.

## Le coût, mesuré

`sync-data.mjs` lit désormais les 30 profils du manifeste pour en dériver le
drapeau — **39,8 Mo**, dont 6,8 pour le plus gros. Le script passe de 6 à
**8,4 s**. C'était le prix d'un fait sourcé plutôt que d'une heuristique sur un
nom de parti.

## L'alternative écartée

**Masquer ces fiches au lieu de les griser.** C'est ce que fait déjà
`STATUTS_MASQUES` pour une candidature déclinée, et la mécanique existait. Mais
une candidature déclarée dont nous n'avons rien à montrer reste une candidature
déclarée : la retirer ferait porter à l'interface un jugement de pertinence que
la source ne pose pas, et rendrait invisible le fait — publiable — qu'un
candidat n'a jamais siégé à l'Assemblée.
