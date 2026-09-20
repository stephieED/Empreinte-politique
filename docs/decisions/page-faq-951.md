<a id="page-faq-951"></a>

# Une page /faq en accordéon, et les pages statiques prennent la rangée collée (#951) (2026-09-16)

`2026-09-16`

> **En bref** — première des trois pages de #951, avant `/sources` et la section en tête de méthodologie : la propriétaire a choisi le 16/09/2026 de **créer les pages avant de vider l'accueil**, pour que rien ne disparaisse du site entre deux lots. `/faq` reprend les **quatre questions** de l'accueil dans la coque des pages statiques, en **accordéon, la première question ouverte** — forme B, retenue entre trois maquettes rendues sur le site (une carte par question tout ouvert ; une seule carte à filets). Les questions restent **écrites une seule fois**, dans `landing/Faq.jsx`, que l'accueil porte encore. Le lien « FAQ » de la barre quitte sa cible provisoire `/#faq`. Les pages statiques et `/couverture` prennent **la rangée collée**, qui remplace le fil « ← Retour à l'accueil » : le logo ramène à l'accueil et les pages du site sont à côté. **Alternative écartée** : garder la FAQ sur l'accueil seulement et vider l'accueil d'abord — le lien « FAQ » aurait pointé sur une section disparue.

## La décision

- `pages/FaqPage.jsx`, route `/faq`, lit `QUESTIONS` exporté par `landing/Faq.jsx`.
- `StaticPage` : une section sans `heading` ne rend pas de titre — la bannière
  nomme déjà la page.
- `StaticPage` et `CoveragePage` rendent `EnTeteSite` ; `.static-breadcrumb`
  est retirée.
- « Sources » reste provisoirement sur `/couverture` jusqu'à `/sources`.

## Ce qui reste de #951

`/sources` et le sort de `/couverture`, la section en tête de `/methodologie`,
puis la forme C de l'accueil, qui retirera la FAQ de l'accueil.
