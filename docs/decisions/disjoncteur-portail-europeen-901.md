<a id="disjoncteur-portail-europeen-901"></a>
# Un portail muet coûtait 2 h 20 de run pour rien (#901) (2026-09-16)

`2026-09-16`

> **En bref** — Le 16/09/2026, `data.europarl.europa.eu` a cessé de répondre sur
> `/documents` : pas un `429` avec son `Retry-After`, que ce module sait
> attendre, mais un **silence** de 30 s par requête. `except Exception: return
> None` ne comptait rien, donc une passe sur 279 documents aurait payé le
> `TIMEOUT` pour chacun — **2 h 20** — pour finir sans un seul titre. Après cinq
> silences consécutifs, la passe cesse d'interroger et le dit.

## Le diagnostic, et comment il a été fait

La question posée était : est-ce le portail qui tombe, ou nous qu'on bloque ?
Trois mesures y répondent, le 16/09/2026 :

| Mesure | Résultat |
| --- | --- |
| `/api/v2/` et `/meps` depuis notre machine | **200**, en 5 s et 12 s |
| `/api/v2/documents/RC-9-2024-0227` depuis notre machine | **timeout**, trois essais de 30 s |
| La même URL **depuis un autre réseau** | **200** — titre français rendu, 11 concepts |

Le portail allait bien. La limitation visait notre adresse, sur cette ressource,
après une trentaine de requêtes de mesure enchaînées en quelques minutes.

**Le mode de blocage a changé depuis #827.** À l'époque, le portail refusait par
`HTTP 429` + `Retry-After: 60` — une réponse, qu'on attend. Aujourd'hui il ne
répond rien. Un code qui ne gère que le refus poli ne voit pas le silence.

## Ce que le code en faisait, et pourquoi c'était coûteux

`_interroger` attrapait toute exception et rendait `None`. La valeur est
**juste** — « question non posée » n'est pas « ce document n'existe pas »,
§2 règle 5 — mais rien ne la comptait. La passe suivante repartait, pour 30 s de
plus, sur le document suivant.

Le coût n'est pas théorique : 279 documents distincts × `TIMEOUT` = **2 h 20**
de job, pour zéro titre et zéro matière, sans échec et sans message. Un lecteur
verrait la couverture s'effondrer et n'aurait aucun moyen de savoir pourquoi.

## Décision

Un compteur d'échecs **consécutifs**. À `MAX_ECHECS_CONSECUTIFS = 5`, la passe
cesse d'interroger : `_entree` rend `None` sans requête, et `statistiques`
publie `disjoncte: true`.

Trois propriétés qui comptent autant que le disjoncteur lui-même :

1. **Un succès remet le compteur à zéro.** Un aléa isolé ne doit pas rapprocher
   la passe de l'arrêt.
2. **Le cache répond encore après l'arrêt.** Ce qui a été obtenu reste acquis ;
   seule l'interrogation s'arrête.
3. **Un échec n'entre jamais au cache.** Sinon la panne d'un jour se figerait en
   fait pour tous les runs suivants.

Un `404` n'est pas un échec : le portail qui répond « inconnu » répond.

Le seuil est bas exprès. Cinq silences d'affilée ne sont plus un aléa, et la
donnée manquante se déclare aussi bien après 5 échecs qu'après 279.

## Pourquoi pas une pause plus longue

C'était la réponse intuitive, et elle est mauvaise. `PAUSE_ENTRE_REQUETES = 0.6`
vient d'une **mesure** — #827, 1 320 requêtes, 13 refus malgré la pause — pas
d'une intuition. L'allonger à l'aveugle rallongerait tous les runs, y compris
les 99 % qui se passent bien, sans rien garantir : le blocage d'aujourd'hui est
arrivé à un débit que cette pause respecte.

Et re-mesurer la bonne pause demanderait de se faire bloquer à nouveau, depuis
une adresse qui l'est déjà. Le disjoncteur, lui, ne suppose rien sur le débit
toléré : il constate le silence et arrête les frais.

## Ce que cela ne résout pas

La couverture réelle du titre français et des matières reste inconnue tant que
le portail ne répond pas depuis la machine qui collecte. **La CI n'est pas
concernée** — GitHub Actions sort par d'autres adresses — mais rien ne le
garantit à l'avance, et c'est précisément pourquoi `disjoncte` est publié dans
les statistiques : une couverture faible doit pouvoir se lire comme « la passe
s'est arrêtée », jamais comme un fait sur la source.
