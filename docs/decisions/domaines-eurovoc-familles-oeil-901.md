<a id="domaines-eurovoc-familles-oeil-901"></a>
# La cascade européenne se colore par domaine EuroVoc, lu dans le thésaurus (#901) (2026-09-17)

`2026-09-17`

> **En bref** — L'interface colore la cascade des textes portés européens par
> **domaine EuroVoc**, complété par la **famille OEIL** pour les textes à dossier
> (arbitré le 17/09/2026 ; l'axe « commission au fond », qui ne couvrait que 17
> textes sur 383, est abandonné). Les deux index européens publient désormais ce
> premier niveau, **lu dans la source** : 979 des 980 concepts ont leur domaine,
> les 389 dossiers leur famille. Libellés de domaine en français, libellés de
> famille en anglais — arbitré.

## Le besoin

Mesuré par la session interface sur les 32 candidats déclarés : 383 textes portés
européens ; commission au fond résolue pour 17 ; concepts EuroVoc pour 345 ;
matières OEIL, via le dossier, pour 56 ; au moins l'une des deux pour 382.

## Décision

1. **`documents_europeens.json` v2** — chaque matière porte
   `domaine: {code, libelle}`. Le chemin est celui du thésaurus : concept →
   `skos:inScheme` microthésaurus (typé `MicroThesaurus`, ce qui écarte le
   thésaurus racine) → `eurovoc:domain` → `skos:notation` et `skos:prefLabel`
   français, verbatim (« 08 RELATIONS INTERNATIONALES »). Une requête par lot de
   100 concepts, comme les libellés.
2. **`dossiers_europeens.json` v3** — chaque dossier porte
   `familles: [{code, libelle}]`, le premier segment du code de chacune de ses
   matières. Le libellé est lu sur **tout** le dump, parce que le premier niveau
   n'apparaît que sur 437 occurrences de 23 885 dossiers ; quand il a changé
   (« Internal market, SLIM » en 2013, « … single market » depuis), le dossier mis
   à jour le plus récemment l'emporte.
3. **Rien n'est déduit.** Un concept rattaché à deux domaines n'en publierait
   aucun (aucun ne l'est) ; un domaine ou une famille introuvable est `null` ou
   absent **et déclaré** — `domaines_non_resolu`, `familles_non_resolu` — avec
   ses codes (§2 règle 5).
4. **Données au prochain run** : les deux index se reconstruisent entièrement à
   chaque run, aucune reprise n'est nécessaire.

## Mesuré avant de publier

- Le vrai point SPARQL, sur les 980 concepts de l'index committé : **979**
  domaines, **21** domaines distincts, **0** concept à deux domaines. Le seul
  absent, `100145`, est lui-même un domaine.
- Le dump `ep_dossiers` en cache (17/08), sur les 389 références de l'index
  committé : **389** dossiers avec famille, **8** familles, **0** non résolue.

## Alternatives rejetées

- **Libellés de famille en français, lus sur le site OEIL** : il répond `307` à
  une requête simple, et le lot aurait dépendu d'un contournement non garanti.
  L'anglais a été arbitré, comme pour les commissions.
- **Un index des domaines à part** : un second fichier à tenir d'accord pour un
  couple `{code, libelle}` par matière. L'interface compte par document ; le
  domaine sur la matière est la forme qu'elle lit directement.
- **Déduire le domaine du libellé du concept, ou la famille du titre du
  dossier** : une classification de notre fait (§2 règles 2 et 8).
