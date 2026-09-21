<a id="code-du-prive-dans-le-run-1059"></a>
# Le run prend son code sur le dépôt privé et publie code + données en un commit (#1059) (2026-09-21)

`2026-09-21`

> **En bref** — les données viennent du dépôt public, le code du privé épinglé une fois, et le commit de fin de run dépose les deux ensemble ; la garde de #390 disparaît, devenue sans objet.

**Contexte** : depuis la bascule à deux dépôts, publier du code et produire des
données sont deux gestes séparés. Rien ne garantit qu'ils correspondent : le
code est poussé à la main à un moment, les données arrivent à un autre,
produites par ce qui se trouvait publié entre-temps. Le dépôt public peut donc
porter des données que son propre code ne reproduit pas.

**Décision : le run prend ses données sur le public et son code sur le privé,
et publie les deux dans le même commit.**

| | d'où | poids |
| --- | --- | ---: |
| `raw_data/`, `pivot_data/` | le **public**, par le `checkout` habituel | 7,3 Go |
| tout le reste | le **privé**, superposé | ~42 Mo |

Le partage est celui de [[repertoire-config-1057]] et la constante est la même
qu'en [[rituel-de-publication]] côté script : `DONNEES=(pivot_data raw_data)`.
Les données ne sont **jamais** superposées — la fusion est additive, et repartir
d'une copie périmée écraserait ce que le run précédent a produit.

## Le SHA est épinglé une fois, et c'est tout l'intérêt

Un job de tête, `epingler-le-code`, résout `main` du privé et publie son SHA ;
tous les autres jobs en dépendent et superposent **ce** SHA.

Résolu par job, le montage serait faux : les extractions démarrent à t=0,
`merge-and-pivot` ~27 min plus tard, et un merge pendant le run donnerait des
extractions faites avec un code et une fusion faite avec un autre. C'est
exactement l'option que [[ne-jamais-committer-un-build-perime]] avait écartée —
« le job dériverait avec du code neuf à partir d'artifacts extraits avec du
code ancien : un état mixte, plus cohérent qu'aujourd'hui mais toujours pas
cohérent ».

## Ce qui disparaît : le garde-fou de #390

`GENERATION_CODE_CHANGED_DURING_RUN` annulait le commit quand `src/` ou un
`raw_data/*.json` avait bougé pendant le run. Sa prémisse était que la donnée
produite allait être committée sur un `main` portant un **autre** code, et que
« le cas dangereux est celui où git merge proprement : la donnée périmée est
publiée en silence » (run `#266`, 17/08/2026).

Cette situation ne peut plus se produire : le code publié **est** celui qui a
produit la donnée, dans le même commit. La cohérence devient vraie par
construction au lieu d'être vérifiée à la fin — ce que la décision de #390
appelait déjà le bon mécanisme, et qu'elle n'avait écarté que faute d'être
câblée. Le retrait est donc la conséquence du lot, pas un assouplissement.

Ce qui reste couvert autrement : un autre run qui committerait entre le
checkout et le push relève du rebase de la boucle de relance, et les quatre
garde-fous d'avant-commit comparent la donnée produite à l'état committé, pas
au code. La branche `code_change` de `retry-generate-data.yml` devient
inatteignable ; elle est laissée en place et partira quand ce fichier sera
retouché, plutôt qu'à moitié démontée ici.

## Effet de bord voulu : le site suit

`web/UI_finale` voyage avec le reste du code. Le déploiement déclenché par le
commit de fin de run prend donc la **dernière interface**, et non celle qui
avait été publiée à la main.

## Le jeton

Un jeton à portée fine, **lecture seule** sur `Empreinte-politique-src`
(`Contents: Read-only`), déposé en secret `SRC_READ_TOKEN` sur le dépôt
**public** le 21/09/2026. `WORKFLOW_PAT` n'est pas réutilisé : c'est un jeton
en **écriture**, fait pour l'action Claude interactive, et ce chemin n'a besoin
que de lire. **Son expiration cassera la superposition**, comme celle de
`WORKFLOW_PAT` casse `claude.yml` — le symptôme sera un job en échec au premier
pas, ce qui est le bon endroit pour le voir.

## Ce que le lot ne fait pas

**Publier le fichier de workflow.** GitHub lit `generate-data.yml` sur le dépôt
public, jamais celui qu'on superpose : ce mécanisme ne prend effet qu'au run
**suivant** sa publication, et cette publication-là reste manuelle. C'est la
dernière.

**Alternative écartée : un job de synchronisation en tête de workflow**, qui
publierait le code sur le public avant que les autres jobs ne tournent. Elle
publie le code même quand le run échoue ensuite — exactement ce que ce lot
cherche à empêcher, un dépôt public portant du code sans les données qui vont
avec.
