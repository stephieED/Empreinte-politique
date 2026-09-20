# La couverture européenne n'atteignait pas la fiche (#683, lot 4)

`2026-09-09`

> **En bref** — constaté sur le **run `34377413730`**, vert et committé, en lisant les profils un par un : **3 profils sur 6** (`raphael-glucksmann`, `florian-philippot`, `lydie-massard`) publiaient leurs votes du Parlement européen **sans la borne de fraîcheur** arbitrée le matin même, et **6 sur 6** portaient « ParlTrack (fallback) : dumps absents ce run » à côté de 1 977 votes venus de ces dumps ; **le garde-fou de #602 n'a pas échoué, il manquait un cas** — `extract-ue-officiel` écrit une couverture sans volet européen, `merge-and-pivot` en écrit une avec, même jour et même rang, donc la règle 4 conservait la couverture déjà publiée et les profils le déclaraient sous « couverture divergente non tranchée » ; d'où une **cinquième règle, avant la non-décision** : à date et rang égaux, l'écrivain qui couvre **strictement plus de sources** l'emporte — un sur-ensemble strict n'est pas une contradiction, il dit tout ce que l'autre dit plus une source de plus —, avec la borne explicite et testée que deux jeux de sources simplement **différents** restent non tranchables, sans quoi la règle redeviendrait le « dernier qui parle a raison » que #602 a retiré ; la source se lit sur `couverture[].source`, **facultatif et dont l'absence signifie « Assemblée nationale »** (100 % des entrées d'avant ce lot), jamais sur le texte de la preuve ; et la reprise de la veille est étendue au **troisième** constat ParlTrack — l'énumération était incomplète, pas la règle. **Aucun des deux n'aurait fait échouer un run**, et aucun n'a été trouvé par un test : seulement en relisant les profils committés. Suite complète à 4 366, 0 échec.

## Contexte

Constaté sur le **run `34377413730`**, le premier à publier du matériau européen
pour de bon. Il est vert, les données sont committées, et six profils portent
leurs votes du Parlement européen. Deux choses n'ont pas suivi.

## Le premier défaut : la borne de fraîcheur ne survit pas à la fusion

Mesuré sur les six profils enrichis :

| Profil | Couverture européenne publiée |
| --- | --- |
| `emmanuel-maurel`, `marine-le-pen`, `jean-luc-melenchon` | oui |
| `raphael-glucksmann`, `florian-philippot`, `lydie-massard` | **non** |

Trois profils sur six publient donc leurs votes européens **sans la borne qui
les date** — précisément ce que la propriétaire a arbitré le matin même :
« on accepte le retard de la source et on l'écrit ».

**Le mécanisme est celui de #602, et il a fait son travail.**
`extract-ue-officiel` écrit une couverture sans volet européen — il n'interroge
pas ParlTrack —, `merge-and-pivot` en écrit une avec. Même jour, même rang
d'interrogation, contenus différents : la règle 4 refuse de trancher et
**conserve la couverture déjà publiée**. Les trois profils le déclarent
d'ailleurs, sous « couverture divergente non tranchée ».

Ce n'est pas le garde-fou qui a échoué : c'est la règle qui manquait un cas.

### Décision — une cinquième règle, avant la non-décision

**À date et rang égaux, l'écrivain qui couvre strictement plus de sources
l'emporte.**

Un sur-ensemble strict n'est pas une contradiction : il dit tout ce que l'autre
dit, **plus une source de plus**. Le préférer ne choisit pas entre deux vérités,
il retient la plus complète.

La borne est explicite et testée : deux jeux de sources simplement **différents**
restent non tranchables. Sans elle, la règle deviendrait un « le dernier qui
parle a raison » déguisé — exactement ce que #602 a retiré.

La source se lit sur un champ, jamais sur le texte de la preuve :
`couverture[].source`, **facultatif, dont l'absence signifie « Assemblée
nationale »**. C'est le cas de 100 % des entrées écrites avant ce lot ; l'écrire
partout aurait été un backfill sans fait nouveau, et le test le verrouille — la
clé explicite ne crée pas une source de plus.

## Le second : un troisième constat ParlTrack périmé

Les **6 profils enrichis sur 6** publient

> ParlTrack (fallback) : dumps absents ce run — données ParlTrack issues du
> cache/dépôt précédent.

à côté de 1 977 votes qui viennent précisément de ces dumps. Le constat vient
d'un run où il était vrai.

C'est le mécanisme corrigé la veille — un avertissement dont la famille n'est
pas représentée par le nouvel écrivain survit —, mais la reprise ne visait que
**deux** des trois familles ParlTrack. L'énumération était incomplète, pas la
règle. `retirer_constats_parltrack_perimes` couvre désormais les trois.

## Ce que ces deux défauts disent du reste

Aucun des deux n'aurait fait échouer un run : le premier omet une borne, le
second publie une phrase fausse. La suite était verte à 4 361 et le portail
rendait 0.

**Ils n'ont été trouvés qu'en lisant les profils committés**, un par un, après
un run réel — pas par un test, pas par le portail. C'est le cinquième cas de la
journée, et le troisième dont le déclencheur est une question de la propriétaire
plutôt qu'une mesure planifiée.

## Alternative écartée

**Faire que `extract-ue-officiel` n'écrive pas de couverture du tout**, ce qui
supprimerait la divergence à la racine. Écarté : ce job interroge réellement le
portail du Parlement européen et sait des choses sur `mandats` que personne
d'autre ne sait. Le faire taire pour éviter un conflit reviendrait à choisir
l'écrivain par son nom plutôt que par ce qu'il a interrogé — le défaut même que
#602 a corrigé, repris à l'envers.
