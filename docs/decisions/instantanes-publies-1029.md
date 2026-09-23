<a id="instantanes-publies-1029"></a>

# Les instantanés thématiques ont leur dossier publié (#1029) (2026-09-23)

`2026-09-23`

> **En bref** — #1029 devait servir la **communication** : montrer sur un cas ce que l'outil permet. Le rapport « carburant » existait en artefact, hors du dépôt, donc impartageable depuis le site et invérifiable dans une revue. Arbitré le 23/09/2026 : un instantané est une **page statique** de `web/UI_finale/public/rapports/`, nommée `<date des données>-<sujet>.html`, servie telle quelle par GitHub Pages — elle répond 200 sans dépendre du repli de routage (#756, #969), et son adresse ne bouge plus une fois partagée. **Un instantané n'est jamais mis à jour** : il dit l'état du corpus à sa date ; un sujet repris plus tard en donne un nouveau, à une nouvelle adresse. L'index `/rapports` était écrit à la main — il se **construit depuis le dossier** (`scripts/index-rapports.mjs`), en lisant la date dans le nom, le `<title>`, la `<meta name="description">` et la `<meta name="instantane:periode">` de chaque page ; `tests/test_rapports_publies.py` refuse un index qui a dérivé. La barre du site gagne une cinquième entrée, **« Instantanés »**, en lien statique et non en route React.

## Le contexte

Le premier instantané — le prix des carburants, du 23 mars au 23 septembre 2026
— répond à la question que #1029 pose depuis le début : qu'est-ce qui s'est dit
et qu'est-ce qui s'est fait sur un sujet, ces six derniers mois. Il ne dit rien
que les fiches ne disent pas : onze séances de questions au Gouvernement, quatre
textes déposés et restés au dépôt, vingt actes parus au Journal officiel, aucune
loi promulguée. Chaque fait y mène à sa source — l'ancre exacte du compte rendu
(#1087), le dossier à l'Assemblée, le texte sur Légifrance.

## La décision

- **Une page statique, hors des routes React.** L'application route côté client ;
  une page d'instantané n'a pas besoin d'elle, et une route de plus l'aurait
  rendue dépendante du build de l'application pour un contenu figé.
- **La date du nom est celle des DONNÉES**, jamais celle de la publication : deux
  instantanés du même sujet à un mois d'écart ne disent pas la même chose parce
  que le corpus a bougé, et le lecteur d'un vieux lien doit le savoir.
- **L'index se génère.** Un index tenu à la main oublie un fichier le jour où on
  est pressé, et un instantané publié sans être listé n'est trouvable par
  personne. Le test compare la version committée à ce que le générateur produit.
- **Le mot est « instantané »**, retenu par la propriétaire contre « rapport » :
  il dit que la page est une prise de vue datée, pas un document qui vivra.

## Les limites, écrites sur les pages

- Un instantané lit les **intitulés** : un débat ou un acte qui traite du sujet
  sans le nommer n'y est pas.
- Les nombres d'un groupe ne s'additionnent pas d'un débat à l'autre — un député
  peut intervenir dans plusieurs — et un total sans doublon demanderait de
  publier les dates de parole de chaque membre, ce que §2 règles 3 et 7
  interdisent.
- Les colonnes « ce qui a été dit » et « ce qui a été publié au Journal
  officiel » ne se répondent pas : un décret applique le plus souvent une loi
  antérieure, et Légifrance ne qualifie ce lien qu'avec un retard qu'elle ne
  publie pas.

## Les alternatives écartées

- **Garder l'instantané en artefact** : impartageable depuis le site, invisible
  d'une revue, et deux copies du même texte dès la première correction.
- **Une route React `/instantanes/<slug>`** : le contenu est figé, la route
  aurait lié sa publication au build de l'application.
- **Un index écrit à la main** : tenu jusqu'au deuxième instantané.
