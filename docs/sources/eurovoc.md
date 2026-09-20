# EuroVoc — le thésaurus qui donne un nom aux matières européennes

> **Statut : vivant, interrogé depuis le 16/09/2026 (#901).** Une seule chose
> lui est demandée : le **libellé français** d'un concept dont le Parlement
> européen a déjà donné l'identifiant. Rien n'est découvert ici, rien n'est
> classé ici.

## Ce que le fournisseur publie

EuroVoc est le thésaurus multilingue et multidisciplinaire de l'Union
européenne, géré par l'**Office des publications**. Chaque concept porte un
identifiant numérique et un libellé dans une vingtaine de langues.

| | |
| --- | --- |
| Point d'accès | `https://publications.europa.eu/webapi/rdf/sparql` |
| Forme d'un concept | `http://eurovoc.europa.eu/2155` → « opposition politique » |
| Propriétés lues | `skos:prefLabel` du concept, filtrée sur `lang = "fr"` ; son **domaine** : `skos:inScheme` → microthésaurus (`eurovoc:MicroThesaurus`) → `eurovoc:domain` → `skos:notation` et `skos:prefLabel` en français |
| Licence | **CC BY 4.0** — attribution, et indication des modifications |

## Ce que nous en faisons, et ce que nous n'en faisons pas

**Nous ne collectons pas EuroVoc.** Les concepts d'un document viennent du
portail du Parlement (`is_about`), dans la réponse que `ResolveurDocuments`
télécharge déjà. EuroVoc n'est interrogé que pour **traduire un identifiant en
mot lisible** — sans quoi une fiche afficherait « 2155 ».

**Le portail classe des documents, pas des procédures, et pas tous les documents.**
Un dossier (`2010/0310M(NLE)`) n'a aucun concept EuroVoc ; son **texte adopté**
(`TA-8-2018-0286`) en a 8, son **rapport de commission** (`A-8-2018-0224`) aucun.
Mesuré le 17/09/2026 sur les 367 dossiers amendés par les candidats déclarés : le
texte adopté porte les concepts dans 281 cas, le rapport dans 11 ; 59 dossiers,
surtout d'avant 2016, n'ont aucun document classé. C'est pourquoi un dossier reçoit
ses domaines de son document de séance, texte adopté d'abord.

**Nous ne classons rien nous-mêmes.** La matière d'un document est un fait du
Parlement, pas une lecture que nous ferions de son titre. C'est la condition
pour qu'elle soit publiable (§2 règles 2 et 8).

## Le domaine : un chemin dans le thésaurus, et un piège

Depuis le 17/09/2026, chaque concept publie aussi son **domaine**, le premier des
trois niveaux du thésaurus (21 domaines, « 08 RELATIONS INTERNATIONALES »). Le
chemin est lu, jamais déduit d'un libellé : concept → microthésaurus → domaine.

**Le piège** : `skos:inScheme` rend aussi le thésaurus racine
(`http://eurovoc.europa.eu/100141`), qui n'a pas de domaine. Seul le schéma typé
`MicroThesaurus` en porte un. Mesuré sur les 980 concepts publiés : **979**
résolus, **aucun** rattaché à deux domaines. Le seul sans domaine, `100145`, est
lui-même un domaine que le portail donne comme concept : il est déclaré
(`domaine_eurovoc_introuvable`), pas deviné.

## Le piège : une requête par concept, ou une pour cent

Le point SPARQL accepte `VALUES` : une requête rend une centaine de libellés
d'un coup. Mesuré le 16/09/2026 — **4 concepts en 0,22 s**. Interroger concept
par concept multiplierait les appels par cent pour le même résultat, et c'est ce
que `resoudre_libelles()` évite par construction (`LOT_SPARQL = 100`).

## Le second piège : un code sans libellé

Un identifiant que le thésaurus ne rend pas n'est **jamais inventé ni deviné**.
Le document garde les libellés trouvés et déclare les autres —
`matieres_non_resolu.motif = "libelle_eurovoc_introuvable"`, avec les codes
concernés. Une matière perdue en silence serait indétectable.

## Le troisième piège : un silence passager

Le point SPARQL peut se taire un moment. Le 17/09/2026, le run `35194727922` a
dépassé une fois le délai de 60 s sur la requête des domaines ; rejouée une heure
plus tard, elle répondait en 0,1 à 0,4 s. Chaque requête est donc **réessayée
deux fois** (après 5 puis 20 s) sur un délai dépassé, une coupure, un `429` ou une
erreur `5xx` ; un `400` ne l'est pas, la requête est fausse.

Si EuroVoc reste muet après ces essais, les deux lectures ne se traitent pas
pareil :

- **les libellés** : `resoudre_libelles()` **lève** au lieu de rendre des codes
  nus, et l'étape échoue. Un index de matières illisibles vaut moins que pas
  d'index ;
- **les domaines** : l'index est publié, chaque matière porte `domaine: null`, et
  chaque document déclare `domaines_non_resolu.motif = "eurovoc_injoignable"`. Le
  domaine sert un axe de couleur, son absence ne bloque pas le corpus.

## Attribution

Le fichier produit le dit dans son entête, et les deux sources y sont nommées
ensemble :

```
"licence_donnees": "Parlement européen (data.europarl.europa.eu, attribution) ;
                    EuroVoc — Office des publications de l'Union européenne, CC BY 4.0"
```

→ `docs/decisions/matieres-eurovoc-documents-901.md`, `AGENTS.md` §7.
