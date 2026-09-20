<a id="resolution-legislature-votes"></a>
# Où vit la liste dédupliquée des scrutins : un fichier partagé, pas un par entité (#432) (2026-08-19)

`2026-08-19`

> **En bref** — la liste dédupliquée des scrutins vit dans un fichier partagé, pas un par entité.

La normalisation des votes (#432) sépare un scrutin — identique pour tous ses
votants — du mapping qui, seul, est propre au membre. Restait à trancher **où
vit la liste dédupliquée** : un fichier partagé, ou un par entité (candidat,
groupe, gouvernement) à l'image de `pivot_data/groupes/` et
`pivot_data/gouvernements/`, qui dédupliquent déjà chacun dans leur périmètre.

## Ce que la mesure a montré

Les 4 104 scrutins portés par les profils de groupe sont **intégralement
inclus** dans les 17 422 portés par les profils individuels : **aucun scrutin
n'est propre à un groupe**. Les ensembles sont strictement emboîtés, pas
disjoints.

C'est la conséquence directe de ce qu'est un scrutin : un vote de séance
publique auquel participent les membres de **tous** les groupes. Stocker la
liste par groupe réécrirait donc le même scrutin dans les sept fichiers — on
reconstruirait la duplication que #429 existe pour supprimer, au lieu de la
supprimer.

## La décision

Une liste partagée `pivot_data/scrutins.json`, et dans chaque profil le seul
mapping :

```json
"votes": [{"legislature": "16", "numero_scrutin": 3210, "position": "contre"}]
```

## La réserve qui a motivé la question, et pourquoi elle est levée

L'inquiétude était qu'une liste globale laisse croire que tout membre est
rattaché à l'ensemble des scrutins. Elle ne se matérialise pas : **le
rattachement est porté par le mapping, pas par la liste**. Un profil ne
référence que les scrutins où ce membre a voté, avec sa position. Le fichier
partagé est une table de **résolution**, jamais une affirmation de couverture.

Deux garde-fous en découlent, et ils sont contraignants :

- **§2.8** — la liste partagée ne doit jamais être lue comme un périmètre. Un
  consommateur qui inférerait la couverture d'un profil depuis elle produirait
  un regroupement trompeur.
- **§2.5** — chaque profil garde un champ de couverture explicite (les
  législatures réellement collectées), pour qu'une absence de vote ne se lise
  jamais comme « n'a pas voté ». C'est le sens de rendre `votes_source`
  dérivable du mapping plutôt que de le maintenir en texte libre.

Rappel de clé, cf. §*Résoudre la `legislature` d'un vote* : `numero_scrutin`
repart à 1 à chaque législature. L'identité d'un scrutin est la paire
`(legislature, numero_scrutin)` — même leçon que le `numero` des amendements
avant #440.

## Le coût assumé

Un profil **cesse d'être auto-portant** : lu seul, il ne dit plus de quel
scrutin il parle. C'est un vrai renoncement, qui touche #434 (versionnement) et
tout consommateur d'un fichier isolé. Il est accepté parce que l'alternative —
répliquer 6,1 Mo de scrutins dans chaque entité — annule le gain recherché.

## Séquencement

Le fichier **n'arrive pas avant le mapping qui le consomme**. Le poser d'abord
ajouterait ~8,7 Mo dupliquant ce que les profils portent déjà, le temps que la
migration suive. C'est aussi là que vit le vrai risque : la fusion additive
devra fusionner mapping et liste sans perdre une position.

