<a id="balisage-schema-org-1008"></a>

# Chaque fiche porte ses faits typés en JSON-LD (#1008) (2026-09-18)

`2026-09-18`

> **En bref** — mesuré le 18/09/2026 : aucune des 64 pages publiées ne portait `application/ld+json`. #1003 avait rendu les fiches **lisibles** sans JavaScript ; ce lot les rend **interprétables** — au lieu d'une phrase à analyser, une machine reçoit un objet typé : une personne, un rôle, ses dates, son organisation, sa source. **60 pages balisées** : 30 `Person`, 17 `GovernmentOrganization`, 12 `Organization` (lignées, avec leurs maillons en `subOrganization`), 1 `WebSite` sur l'accueil. Écrit au build par `scripts/donnees-structurees.mjs`, dans le `<head>`, depuis le manifeste et les projections — rien à maintenir à la main. **Ce que le balisage ne porte jamais** : `ClaimReview` (note de véracité, §2 règle 1, déjà écarté en #969), aucun agrégat d'activité, aucune date qu'on n'a pas (un mandat local clos sans fin n'a pas d'`endDate`, #922/#966), aucune adresse qui ne soit pas déjà une source de la page — `sameAs` n'accepte que les pages de personne des institutions, jamais une archive de jeu de données ni Wikipédia —, et **ni date de naissance, ni profession, ni circonscription**, que `identite` porte mais que la fiche n'affiche pas. **L'éditeur est « Empreinte politique »**, jamais une personne : les mentions légales déclarent une édition non professionnelle par une personne physique qui ne se nomme pas. Le contrôle `verifier-referencement.mjs` échoue désormais sur une fiche sans balisage ou dont le JSON est illisible. 11 tests sur entrées copiées du corpus, trois mutations vérifiées échouantes.

Ancres : `donnees-structurees.mjs`, `pages-par-adresse.mjs`, `verifier-referencement.mjs`.

## Décision

| Page | Type | Ce qu'il porte |
| --- | --- | --- |
| Candidat | `Person` | `name`, `url`, `sameAs` (pages officielles), `affiliation` (étiquette), un `OrganizationRole` daté par mandat |
| Gouvernement | `GovernmentOrganization` | période, et un `OrganizationRole` par membre avec son portefeuille |
| Lignée de groupe | `Organization` | `parentOrganization` = l'Assemblée nationale, période, `subOrganization` par maillon |
| Accueil | `WebSite` | nom, langue, description, `publisher` |

**Un mandat local nomme sa collectivité, pas son rôle.** Le libellé d'un mandat
local est « Hénin-Beaumont » : il nomme l'organisation, et le rôle s'écrit
« Mandat local » — sinon la même chaîne est publiée deux fois, comme rôle et
comme organisation.

**`</script>` est neutralisé dans le JSON.** C'est la seule séquence qui, dans
une donnée, referme la balise et permet d'injecter du HTML.

## Ce que le lot ne fait pas

- **Pas de `Dataset` sur `/sources`** : le site n'offre aucun téléchargement, et
  les mentions légales rappellent que la clause de partage à l'identique vise un
  jeu de données dérivé **téléchargeable**. Déclarer une distribution que le site
  ne sert pas présenterait le dépôt comme une distribution du site. À rouvrir si
  un export est un jour publié.
- **Les quatre pages fixes** ne portent pas de balisage propre : leur contenu
  n'est pas de la donnée.

## Alternative écartée

**Décrire les mandats en `hasOccupation`** : `Occupation` ne porte pas de dates,
et la carrière perdrait sa chronologie. `memberOf` avec des `OrganizationRole`
datés dit la même chose sans rien perdre.
