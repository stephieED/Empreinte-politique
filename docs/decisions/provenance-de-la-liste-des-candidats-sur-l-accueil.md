<a id="provenance-de-la-liste-des-candidats-sur-l-accueil"></a>

# La liste des candidats dit d'où elle vient, et elle vient de Wikipédia (2026-10-01)

`2026-10-01`

> **En bref** — La propriétaire a demandé le 30/09/2026 une mention de provenance
> sous la liste des candidats déclarés de l'accueil, « du genre : liste issue de
> Wikidata, en attendant la publication sur le journal officiel ».
> **La liste ne vient pas de Wikidata, elle vient de Wikipédia** — `/sources` et
> `AGENTS.md` §7 le disent tous deux, et Wikidata a été essayée pour découvrir
> les candidatures puis écartée sur mesure. Le nom de la source est corrigé, le
> reste de sa formulation est repris au mot près, et un test refuse le retour de
> « Wikidata » dans ce composant.

## Ce qui a décidé

La liste des candidats déclarés est **la seule liste publiée du site qui ne vienne
pas d'une source institutionnelle**. Les groupes et les gouvernements sortent de
l'open data de l'Assemblée ; celle-ci est tenue à la main dans
`raw_data/candidats.json`, d'après l'article Wikipédia « Candidatures à l'élection
présidentielle française de 2027 ». Rien ne le disait sur l'accueil, alors que
c'est là que la liste s'affiche.

## Pourquoi Wikipédia et pas Wikidata

| Source | Ce qu'elle apporte réellement |
| --- | --- |
| **Wikipédia** | **La liste elle-même** — un nom, une étiquette de parti, jamais de texte. C'est ce qu'écrit `/sources` (`sources.config.js`, `id: 'wikipedia-fr'`) |
| **Wikidata** | **Une seule propriété, `P4123`** : l'identifiant du candidat à l'Assemblée, qui relie sa candidature à sa fiche |

**Wikidata a été essayée pour découvrir les candidatures, et écartée sur mesure
(#753)** : `P3602` rend **1 personne** pour l'élection de 2027, contre plus de
trente déclarées. Ce n'est pas une préférence, c'est un constat chiffré.

**Écrire « issue de Wikidata » sur l'accueil aurait contredit `/sources` sur la
provenance d'une liste publiée.** C'est la traçabilité — §2 règle 2 — et non une
question de style : c'est la seule raison pour laquelle le mot de la propriétaire
n'a pas été repris tel quel. Le reste de sa phrase l'est.

## Ce que la mention dit, et où elle est

> Liste issue de **Wikipédia**, en attendant sa publication au Journal officiel,
> **au plus tard le 26 mars 2027**.

**La date vient de la loi, pas de Wikipédia.** L'article 3 de la loi du 6 novembre
1962 borne la publication de la liste officielle, et `/sources` l'écrit déjà sur
son entrée « Conseil constitutionnel » : « *les parrainages sont rendus publics au
moins deux fois par semaine … jusqu'au 12 mars 2027 à 18 h ; la liste des
candidats est publiée au plus tard le 26 mars 2027, pour un premier tour le
18 avril 2027* ». **« Au plus tard » se garde** : la loi dit une borne, pas une
date, et écrire « le 26 mars 2027 » affirmerait plus que la source.

Une date de consultation de Wikipédia a été proposée à la place, et écartée :
elle aurait dit quand **nous** avons regardé, pas quand la liste officielle
arrive — ce qui n'est pas ce que la mention promet.

**Elle vit AVEC la liste**, et disparaît quand la porte se referme
(`hidden={ouverte !== 'candidats'}`). Posée au-dessus du bloc, elle aurait
qualifié les trois portes alors qu'elle ne vaut que pour une — les deux autres
sont institutionnelles.

**« Wikipédia » est un lien vers `/sources`**, où la licence (CC BY-SA 4.0) et ce
qu'on en reprend sont écrits. Le gris est celui des métadonnées : ce n'est pas un
avertissement sur la donnée, c'est d'où elle vient.

## Un écart assumé avec la FAQ, à connaître

La FAQ dit la même chose autrement : « *en attendant la liste officielle que
publiera le Conseil constitutionnel* », et l'entrée `/sources` qui porte la date
l'attribue elle aussi au **Conseil constitutionnel**. L'accueil dit « *au Journal
officiel* », qui est la formulation de la propriétaire. **Les trois sont vraies** —
le Conseil arrête la liste, le Journal officiel la publie — mais le site nomme
désormais deux choses à trois endroits. **Non tranché** : aligner est un arbitrage
éditorial, pas une correction.

## Le test, et pourquoi il existe

`test_la_liste_des_candidats_dit_d_ou_elle_vient` refuse que « Wikidata »
reparaisse dans `CommencerAExplorer.jsx`, hors commentaires, et vérifie que la
mention reste attachée à la seule liste des candidats. **L'erreur a été proposée
une fois** ; une instruction sans garde se périme, et celle-ci porte sur du texte
publié qui nomme une source.

Le même test **tient la date aux deux endroits où elle est écrite** — la constante
du composant et la prose de `sources.config.js`. Deux copies d'un même fait
dérivent, et le site annoncerait alors deux dates pour la même publication.
