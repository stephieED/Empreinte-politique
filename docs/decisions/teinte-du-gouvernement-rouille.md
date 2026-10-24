<a id="teinte-du-gouvernement-rouille"></a>

# Le gouvernement passe du brun à la rouille (2026-10-23)

`2026-10-23`

> **En bref** — la teinte du gouvernement devient la **rouille `#A84B12`**, à la place du brun `#85510D` que la propriétaire trouvait laid. Elle avait d'abord proposé de **permuter** gouvernement et Sénat, pour garder le jeu de quatre couleurs (Assemblée, Sénat, gouvernement, Europe) qu'il avait été difficile de trouver ; la permutation a été écartée parce que la sarcelle (3,0 à 3,3:1 sur fond clair) ne peut pas écrire de texte, et que le gouvernement est l'institution la plus souvent écrite dans sa couleur. Neuf teintes chaudes ont été montrées sur la frise de l'accueil et les rayonnages de la XVIIe ; la rouille est retenue : texte **5,7:1** sur blanc, et le validateur de la compétence `dataviz` (`validate_palette.js`, `--pairs all`, les quatre institutions) passe la pire paire de tritanopie de **ΔE 5,6 à 10,4** et le plancher en vision normale de **15,3 à 15,7**. Les **articles publiés** gardent le brun : un instantané ne se met pas à jour.

## Contexte

Le brun `#85510D` portait le gouvernement sur les fiches, la frise de
couverture, le schéma des sources, la frise de l'accueil et les rayonnages de
la fiche de législature, ainsi que les hachures du 49.3. Trois contraintes
tenaient la place : du texte en couleur (4,5:1 au moins sur fond clair), un
écart suffisant avec l'Assemblée, le Sénat et l'Europe sous les trois formes de
daltonisme, et rien qui se lise comme une couleur de vote.

## Décision

- `--gouv`, `--fc-gouv`, `--ss-gouv` et la couleur des textes du gouvernement
  sur la fiche de législature valent `#A84B12`.
- La rampe est dérivée aux mêmes proportions que l'ancienne (blanc + 10, 15 et
  25 %) : `--gouv-wash` `#F6EDE7`, `--gouv-pale` `#F2E4DB`, `--gouv-line`
  `#E9D2C4` ; le fond de survol du menu de la frise de l'accueil, `#F7EFEA`.
- Le bleu de l'Europe reste hors de la bande de clarté du validateur, comme
  avant : c'est le bleu officiel de l'emblème.

## Alternatives écartées

- **Permuter gouvernement et Sénat** : la sarcelle n'écrit pas de texte lisible,
  et Assemblée/gouvernement, la paire la plus souvent côte à côte, se serait
  rapprochée en deutéranopie.
- **Bleus et violets** (indigo, ardoise, bleu pétrole) : confondus avec l'Europe
  sous daltonisme.
- **Ocre, moutarde, olive** : l'ocre virait au vert à l'écran (« vert morve ») ;
  l'olive est proche du vert « pour / promulgué » et du rouge « contre » en
  protanopie.
- **Orange brûlé, cuivre, cannelle** : conformes, moins lisibles en texte
  (4,6:1) ou plus proches du brun.
