<a id="licence-parlement-europeen-cc-by-983"></a>
# Le Parlement européen n'a qu'une licence dans ce dépôt : CC BY 4.0 (#983) (2026-09-16)

`2026-09-16`

> **En bref** — Le dépôt donnait deux licences à la même source :
> **CC BY 4.0** dans le code et le README, **« EP Legal Notice »** dans
> `AGENTS.md` §7, la fiche de la source et l'interface. Vérifié : toutes nos
> requêtes vont au portail `data.europarl.europa.eu`, sous CC BY 4.0 depuis une
> décision du Bureau du 16/12/2024. `www.europarl.europa.eu`, que couvre l'avis
> juridique, n'est jamais interrogé. Un seul libellé reste : CC BY 4.0.

## Contexte

Signalé par la session interface le 16/09/2026 :

| Libellé | Où |
| --- | --- |
| CC BY 4.0 | `src/licences.py` (`LICENCE_EUROPARL`), `src/candidate_profile_ue.py`, `README.md` |
| EP Legal Notice | `AGENTS.md` §7, `docs/sources/parltrack-et-europarl.md`, `web/UI_finale/src/data/sources.config.js`, `LegalNoticePage.jsx` |

Le libellé « Legal Notice » vient de [`licences`](licences.md), qui constatait
une licence pour les deux domaines ensemble, avec des « fiches et photos » lues
sur les pages MEP. Ce n'est plus ce que fait le pipeline.

## Ce qui a été vérifié

| Domaine | Ce que le pipeline en fait | Licence |
| --- | --- | --- |
| `data.europarl.europa.eu` | **Toutes** les requêtes européennes : mandats (`candidate_profile_ue.py`), existence et titre français des documents (`europarl_documents.py`) | **CC BY 4.0** |
| `www.europarl.europa.eu` | **Aucune requête.** Le site est derrière un pare-feu anti-robot (voir [`titre-francais-lu-dans-source-url-901`](titre-francais-lu-dans-source-url-901.md)). On y écrit seulement des liens | Avis juridique du site, sans licence Creative Commons |

Sources primaires, lues le 16/09/2026 :

- **Décision du Bureau du Parlement européen du 16/12/2024** « laying down Rules on
  the European Parliament's Open Data », [EUR-Lex C/2025/341](https://eur-lex.europa.eu/eli/C/2025/341/oj).
  Article 4 : « The re-use of Parliament's open data is subject to the conditions
  laid down in the Creative Commons Attribution 4.0 International License
  (CC BY 4.0) ». Les données brutes peuvent aussi être en CC0 1.0. L'article 5
  institue le portail.
- **Documentation OpenAPI de l'API v2** (`https://data.europarl.europa.eu/api/v2/`) :
  `info.license` vaut « CC BY 4.0 - Attribution 4.0 International ».
- **Avis juridique** de `www.europarl.europa.eu/legal-notice/fr/` : conditions
  maison (intégrité, « © Union européenne, [année] - Source : Parlement européen »),
  sans licence Creative Commons. Il couvre le contenu du site, que nous ne
  reproduisons pas.

Aucune photo n'est téléchargée ni affichée : le profil brut européen porte une
URL de photo que rien ne lit.

## Décision

1. **Un seul libellé, CC BY 4.0.** `LICENCE_EUROPARL` est juste et ne change pas ;
   `meta.licence_donnees` non plus.
2. **`AGENTS.md` §7 et `docs/sources/parltrack-et-europarl.md` sont corrigés** :
   un seul domaine, `data.europarl.europa.eu`, et la décision du Bureau comme
   source.
3. **L'interface reprend le même libellé** dans `sources.config.js` et les
   mentions légales, où « et photos » est faux lui aussi. Ces deux fichiers
   appartiennent à la session interface.

## Alternative rejetée

**Deux libellés dans `src/licences.py`**, un par domaine. Un libellé de licence
dit sous quelles conditions on réutilise une donnée. Or aucune donnée publiée ne
vient de `www.europarl.europa.eu` : un lien n'est pas une réutilisation de
contenu. Un second libellé ferait apparaître dans `licence_donnees` une clause
que rien ne déclenche.

Le jour où le pipeline lira réellement une page du site (ce que le pare-feu
empêche aujourd'hui), la question se reposera, et elle se tranchera dans une
nouvelle décision.
