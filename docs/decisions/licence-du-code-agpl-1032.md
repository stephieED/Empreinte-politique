<a id="licence-du-code-agpl-1032"></a>

# Le code sous AGPL-3.0, les textes et la charte tous droits réservés (#1032) (2026-09-18)

`2026-09-18`

> **En bref** — le dépôt était **public sans licence** : lisible, et tous droits réservés par défaut. `/a-propos` allait écrire « le code est public », qu'un lecteur lit comme une autorisation, pendant que les mentions légales disaient « le code source, la charte graphique et les textes rédigés pour ce site sont **à préciser** » — deux pages, deux réponses à la même question, et c'est la propriétaire qui l'a relevé. Arbitré le 18/09/2026, **trois régimes distincts** : le **code** sous **AGPL-3.0**, choisie pour sa section 13 — qui met en ligne un service fondé sur une version modifiée doit en publier le code, ce qui est exactement le mode de réutilisation d'un site ; les **textes rédigés pour le site et la charte graphique** **tous droits réservés**, une licence de logiciel ne couvrant ni la prose ni la marque ; les **données** sous les licences de leurs sources, que la licence du code ne touche pas (§7 — la clause de partage à l'identique de l'ODbL vit sur certains champs). Aucune dépendance ne s'y oppose : `requests` (Apache-2.0), `urllib3`, `beautifulsoup4` (MIT), `zstandard` (BSD), et côté web React, Vite, react-router, d3-sankey, tous permissifs — le permissif se combine dans une œuvre AGPL, l'inverse serait faux. **Ce que l'AGPL nous impose en retour** : le site déployé doit correspondre au code publié, et l'offre de source de sa section 13 est le lien vers le dépôt que porte `/a-propos`. **Écartées** : une licence permissive (MIT, Apache-2.0), qui laisserait refermer la méthode dans un produit propriétaire ; tout mettre sous AGPL, textes compris, qui applique une licence de logiciel à de la prose ; le statu quo « public sans licence », qui laisse une PR extérieure sans cadre — la clause « ce qui entre est sous la même licence que ce qui sort » de GitHub ne joue que si le dépôt porte une licence.

## Le contexte

Mesuré le 18/09/2026 :

| Endroit | Ce qui était écrit |
| --- | --- |
| Le dépôt | Public, **aucun fichier de licence** — donc tous droits réservés |
| `/mentions-legales` | « Le code source, la charte graphique et les textes rédigés pour ce site sont à préciser » |
| `/a-propos`, en cours d'écriture | « le code est public », avec le lien vers le dépôt |
| `web/UI_finale/package.json` | Aucun champ `license` |

« Public » et « open source » ne disent pas la même chose : le premier est un
fait de visibilité, le second une autorisation. Sans licence, on peut lire le
code et le dupliquer à l'intérieur de GitHub, dont les conditions le prévoient —
rien de plus.

## La décision

### 1. Le code : AGPL-3.0

`LICENSE` porte le texte officiel de la FSF, en entier (661 lignes). Ce qu'elle
oblige, dans l'ordre de ce qui compte ici :

- qui redistribue le code le fait sous la même licence ;
- **qui met en ligne un service fondé sur une version modifiée doit publier le
  code de cette version** (section 13) — c'est ce que la GPL ne fait pas, et le
  mode de réutilisation d'un site est précisément celui-là ;
- une PR extérieure arrive sous AGPL, ce qui donne un cadre à la contribution
  technique que #1033 veut encourager.

Ce que la propriétaire garde : elle reste titulaire des droits et peut
republier son propre code sous une autre licence. Cette liberté se réduit dès
qu'une contribution extérieure est fusionnée — il faudra alors l'accord de son
auteur, ou un accord de contribution demandé d'avance.

### 2. Les textes et la charte : tous droits réservés

Les pages éditoriales, les libellés, l'identité visuelle et le logotype sont
protégés par le droit d'auteur et ne sont pas couverts par l'AGPL. Appliquer une
licence de logiciel à de la prose est juridiquement bancal et difficile à faire
respecter.

### 3. Les données : rien ne change

Elles restent sous les licences de leurs sources, détaillées par
`/mentions-legales` et par §7. La licence du code ne les atteint pas, et la
clause de partage à l'identique de l'ODbL continue de vivre sur les champs
qu'elle concerne.

### 4. Ce que l'AGPL nous impose

**Le site déployé doit correspondre au code publié.** Déployer un correctif non
poussé serait exécuter une version modifiée sans en offrir la source. Aucun test
ne peut le vérifier depuis le dépôt : cela se tient en ne déployant que ce qui
est poussé.

L'offre de source de la section 13 est le lien vers le dépôt, porté par la carte
« Qui édite ce site » de `/a-propos`.

## Les alternatives écartées

| Option | Pourquoi écartée |
| --- | --- |
| MIT ou Apache-2.0 | Permissives : quelqu'un peut reprendre la méthode dans un service fermé sans rien publier. Pour un projet dont la valeur est la méthode, c'est ce qu'il s'agissait d'éviter |
| Tout sous AGPL, textes compris | Une licence de logiciel appliquée à de la prose et à une marque |
| Textes en CC BY-SA 4.0 | Cohérent si les textes doivent circuler ; ce n'est pas le choix de la propriétaire, et c'est une décision éditoriale, pas technique |
| Rester « public sans licence » | Une PR extérieure sans cadre, et une page qui promet ce que le droit n'accorde pas |

## Les garde-fous

`tests/test_licence_du_code_1032.py` : le dépôt porte le texte officiel et sa
section 13, les trois pages annoncent la même licence, les mentions légales
séparent le code de la prose et des données, `/a-propos` porte l'offre de
source, `package.json` déclare `AGPL-3.0-only`, et §7 continue de dire que la
licence du code ne touche pas celle des données.
