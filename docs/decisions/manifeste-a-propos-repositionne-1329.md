<a id="manifeste-a-propos-repositionne-1329"></a>

# Le manifeste de /a-propos ne se dit plus agrégateur : le texte de la propriétaire, écrit pour un lecteur qui ne connaît rien au projet (#1329) (2026-10-26)

`2026-10-26`

> **En bref** — Le premier paragraphe du manifeste de `/a-propos` disait que le site « rassemble ce que les institutions publient sur les candidats à la présidentielle 2027 […] et le donne à lire tel quel » : un discours d'agrégateur, contraire au repositionnement de #1329 (relier et donner à voir), et qui plaçait les candidats avant les groupes et les gouvernements (`coeur-permanent-groupes-et-gouvernements`). Il est remplacé par le texte de la propriétaire, arbitré le 26/10/2026 après quatre rondes de propositions refusées. Les trois paragraphes suivants ne bougent pas : « non on ne touche pas au reste ». Livré dans #1351.

## Le texte retenu

> Qui siège aujourd'hui à l'Assemblée ? Quelles lois chaque gouvernement a-t-il
> fait adopter ? Entre les données brutes et les publications techniques,
> difficile de s'y retrouver. Empreinte politique les met en images, pour qu'on
> les comprenne d'un coup d'œil. Les infographies proposées ici donnent une vue
> d'ensemble sur l'activité parlementaire et gouvernementale (mandats, votes,
> textes, prises de parole).

Sur la base qu'elle a écrite, deux corrections seulement, faites avec son
accord : « Mais » retiré en tête de la troisième phrase, qui ne s'opposait plus à
rien ; « proposé ici donne » accordé en « proposées ici donnent ». La parenthèse
finale est son ajout.

## Ce qu'elle a demandé en route

| Consigne | Ses mots |
| --- | --- |
| Le lecteur | « monsieur tout le monde […] qui ne connait rien du projet, qui n'est ni plitiste, ni journaliste, ni analyste, ni développeur » |
| La voix | « moins AI-generated » |
| L'effet | « donner envie à monsieur tout le monde de cliquer » |
| Le fond | « on est pas un agrégateur mais une des valeurs ajouté est la lisibilité des données présentées » |

## Ce qui a été écarté

| Proposition | Pourquoi |
| --- | --- |
| « Empreinte politique est un tableau de bord de la vie parlementaire et gouvernementale. […] Le site les relie et les donne à voir. » | refusée ; relue contre `docs/regles/textes-publies.md`, elle échouait à la règle du concret : « relie et donne à voir » ne dit pas ce que le lecteur trouvera |
| La même, suivie d'un exemple (« Ici, chaque fiche mène aux autres… ») | refusée (« non ») : écrite pour qui connaît déjà le site |
| Deux versions sans mot d'initié (« montre ce que font les députés et les gouvernements… », « Les députés votent les lois… ») | refusées (« aucune ») |
| Deux versions qui s'ouvrent sur des questions, avec « remet ces informations ensemble » | rejetées sur le fond : « remettre ensemble » redisait l'agrégateur |
| Une phrase finale, « Et chaque page mène aux autres. » | refusée (« non à la phrase finale ») |

Le nom du genre arbitré le 22/10, « tableau de bord de la vie parlementaire et
gouvernementale », n'apparaît pas dans le texte retenu.

## Ce qui reste

- **Le deuxième paragraphe** garde « Tout est collecté et mis en forme par un
  programme » : « collecté » est un mot que `docs/regles/textes-publies.md`
  déconseille, et « mis en forme » redit « met en images ». Arbitré : on n'y
  touche pas.
- **La description de `/a-propos` pour les moteurs de recherche**
  (`scripts/metadonnees-pages.mjs`) dit encore « publie ce que les institutions
  publient, collecté par un programme ». Texte à valider avec la propriétaire.
- **Non vérifié** : le rendu en ligne, qui attend le commit de publication du
  prochain run.
