# Les articles des textes lus, publiés dans `articles_votes.json` (#1352) (2026-10-26)

`2026-10-26`

> **En bref** — la session COM (article « Le parcours du budget 2027 ») range trois figures article par article : il lui faut l'intitulé de **tous** les articles du PLF 2027, pas des seuls 12 votés par scrutin. `articles_votes.json` publie désormais, sous `textes`, les articles de chaque texte lu qui porte des intitulés : désignation normalisée, intitulé, partie, titre, chapitre, section. Arbitré le 26/10/2026 (option A, dans le fichier existant). Mesuré le 26/10/2026 : 101 textes, 6 101 articles, dont les 90 du PLF 2027 ; le fichier passe de 1,4 à 4,1 Mo, scrutins inchangés.

## Contexte

`intitule-des-articles-votes-1352` publie l'intitulé de l'article **voté**. Une
figure rangée par article (les amendements de séance par article et par
groupe, les articles nouveaux, les votes sur les articles) vise d'autres
articles : les amendements de séance du PLF 2027 portent sur 56 articles
distincts (au 19/10/2026, mesure de la session COM). Le texte est pourtant déjà
lu, et sa structure est en cache.

## Décision

1. **`textes`**, une clé de plus dans `articles_votes.json` :
   `texte → {source_url, articles: {désignation → {intitule, regroupe, partie,
   titre, chapitre, section}}}`. Le texte de l'article n'y est pas : l'extrait
   reste propre aux scrutins.
2. **Seuls les textes lus qui portent au moins un intitulé** : un texte ordinaire
   n'apporterait que ses divisions, déjà publiées sur ses scrutins. « Lus » veut
   dire lus par le rattachement des scrutins : un texte sans scrutin d'article
   n'y est pas.
3. **La désignation est celle de `normaliser_article`**, comme pour les
   scrutins : « 15 », « 1er », « liminaire », « 4 bis a ». Celle d'un amendement
   (« Article 15 », « ARTICLE 15 ») s'y joint après la même normalisation. Les
   articles gardent l'ordre du texte.
4. `SCHEMA_VERSION` passe à `articles-votes-v3`. Le workflow ne change pas.

## Alternative écartée

**Un fichier à part** (`pivot_data/articles_des_textes.json`, un fichier par
objet comme pour #1314) : une modification de plus de `generate-data.yml`, au
même endroit que #1358, et une publication à la main de plus avant l'échéance du
17/11. Ce sont les articles des textes que le même module lit déjà.

## Non vérifié

- La jointure avec les amendements, faite côté COM : la désignation d'un
  amendement peut porter une forme que `normaliser_article` ne réduit pas
  (« Après l'article 15 », un article additionnel). Ce cas n'a pas été mesuré.
