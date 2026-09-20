# Un lien publié ne déclenche jamais un téléchargement (#1039)

`2026-09-20`

> **En bref** — la propriétaire a relevé le 20/09 que cliquer « Source » sous une intervention de la fiche candidat **téléchargeait** l'archive des comptes rendus. Mesuré : **27 007 des 33 823 interventions** des 32 candidats déclarés portaient cette adresse, pour **trois fichiers** — un `syseron.xml.zip` par législature, répété vingt-sept mille fois ; la légende « Selon l'Assemblée nationale » de la fiche de lignée menait de même à l'archive AMO30. La règle vit désormais dans `utils/lecture.js` et tient en trois gestes : `lienDocumentaire()` ne garde un lien par ligne **que s'il mène à un document** — sinon l'entrée reste du texte, l'absence se disant plutôt que de se combler (§2 règles 2 et 5) ; `pageDuJeuDeDonnees()` renvoie une légende qui doit rester un lien vers **la page** du jeu de données, qui porte le téléchargement, et n'a aucun effet sur une URL qui n'est pas une archive ; et la fiche candidat **nomme l'archive une fois** en pied de section. Vérifié en navigateur : plus aucun lien `.zip` sur `/sources`, `/couverture`, `/methodologie`, une fiche de gouvernement, une fiche candidat et une fiche de lignée. Une garde refuse tout `href={…sourceUrl}` non filtré dans un composant — c'est elle qui a révélé trois autres points d'exposition (`VotesParPeriode`, `EcartsGroupe`, `GovernmentProfile`), dont les URL ne sont pas des archives aujourd'hui mais rien ne l'empêchait demain.

## Ce que la source publie, et ce que nous en faisions

L'Assemblée nationale publie les comptes rendus de séance en **archive** :
`syseron.xml.zip`, un fichier par législature, plus de 100 Mo. C'est cette
adresse que `source_url` porte sur la quasi-totalité des interventions, parce
que c'est là que la donnée a été lue.

La fiche candidat en faisait un badge « Source · Assemblée nationale » sous
chaque intervention. Le badge disait vrai — la donnée vient bien de là — mais
il ne faisait pas ce qu'un lecteur attend d'un lien de source : il ne montrait
rien, il téléchargeait.

## La règle, et pourquoi elle est à trois étages

Une seule fonction ne suffisait pas, parce que les trois usages n'ont pas la
même issue :

| Usage | Fonction | Ce qui se passe quand l'URL est une archive |
| --- | --- | --- |
| Un lien **par ligne** (une intervention, un texte) | `lienDocumentaire()` | Le lien disparaît. L'entrée reste du texte, et rien ne prétend l'attester |
| Une **légende de figure** qui doit rester cliquable | `pageDuJeuDeDonnees()` | Le lien mène à la page du jeu de données, qui porte le téléchargement |
| La **mention de section** | texte fixe | Elle nomme l'archive une fois, avec le lien vers la page |

## Ce que la garde a trouvé en plus

`tests/test_liens_sans_telechargement.py` refuse tout `href={…sourceUrl}` qui
ne passe pas par l'une des deux fonctions. Elle a échoué sur trois composants
que le relevé initial ne visait pas — `VotesParPeriode`, `EcartsGroupe`,
`GovernmentProfile`. Leurs URL sont aujourd'hui des pages de scrutin ou de
dossier, jamais des archives : aucun défaut visible, donc, mais aucune
protection non plus le jour où une source changerait de forme. Les trois
passent désormais par `pageDuJeuDeDonnees()`, sans effet sur l'affichage.

## Alternative écartée : garder le lien et prévenir du téléchargement

« Source (archive, 100 Mo) » aurait laissé le lecteur décider. C'est un
texte explicatif posé sur un lien qui se comporte mal — l'aveu d'échec que
DESIGN_SYSTEM §7 règle 2 refuse —, et cela n'aurait rien changé au fait que
vingt-sept mille badges pointent trois fichiers.
