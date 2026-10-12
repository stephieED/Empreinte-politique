<a id="finances-sociales-collecte-1053"></a>

# Les comptes des caisses sociales : collectés à côté du budget de l'État, sans les y joindre (#1053) (2026-10-12)

`2026-10-12`

> **En bref** — Le budget de l'État ne porte ni la Sécurité sociale, ni les
> retraites, ni le chômage. `src/finances_sociales.py` lit ce que la Drees et
> l'Unédic en publient — ressources par nature, prestations par régime, recettes de
> l'assurance chômage — dans un fichier à part, par année civile. Les ressources
> caisse par caisse ne sont publiées par aucune des deux, et ne sont pas déduites.

## Contexte

La maquette de la section budget d'une fiche de gouvernement (#1053) montrait le
budget général de l'État. Question de la propriétaire, le 12/10/2026 : où sont la
Sécurité sociale et les retraites ? Elles n'y sont pas : elles ont leurs propres
comptes, alimentés par des cotisations et des impôts affectés. Sa demande ensuite :
« une vue séparée qui montre comment se constitue les fonds des caisses
principales », sans chercher la jonction avec le budget de l'État. Puis, la vue
dessinée sur des fichiers téléchargés à la main : étendre la collecte.

## Décision

1. **Un fichier à part**, `raw_data/finances_sociales.json`, et un module à part.
   Ce ne sont pas des finances de l'État, les sources sont autres, l'unité aussi :
   l'année civile, là où le budget se lit par exercice et par mois.
2. **Pas de job nouveau** : une seconde étape du job `extract-finances-etat`,
   `if: always()`. Quatre requêtes et deux secondes ne justifient ni un nœud de
   plus dans le graphe, ni un artifact de plus.
3. **Tout est relu à chaque run.** La source révise ses années récentes (définitif,
   semi-définitif, provisoire) ; figer une année demanderait de savoir laquelle ne
   bougera plus, pour une économie nulle.
4. **Les libellés et les montants de la source, tels quels**, en millions d'euros.
   Aucun regroupement de lignes, aucun renommage de régime : c'est le pivot qui en
   décidera, une fois la forme de la vue arrêtée.
5. **Une garde par partie, tirée d'une égalité que la source respecte** : le total
   des ressources vaut ses lignes, le total des prestations vaut ses secteurs, les
   recettes de l'Unédic valent leurs composantes. Une partie qui ne la tient plus
   n'est pas écrite, et celle déjà publiée reste.
6. **Ce qui manque est déclaré** : pas de ressources par caisse, pas de détail des
   cotisations en année provisoire, pas de régimes complets avant 1990.

## Alternative écartée

- **Reconstituer les ressources de chaque caisse** à partir des cotisations
  encaissées par l'Urssaf : le jeu est sous ODbL, il n'a pas été mis à jour depuis
  2023, et il ne couvre pas les impôts affectés. Ce serait une estimation publiée
  comme un fait (§2 règles 2 et 5).
- **Relier ces comptes au budget de l'État** (ce que l'État verse aux caisses) :
  écarté par la propriétaire pour cette vue. Les « contributions publiques » de la
  Drees ne se rattachent à aucune ligne du budget général par un identifiant.
- **Garder la garde sur la somme des régimes** : la source elle-même ne la tient pas
  de 1981 à 1989 ; une garde que la source enfreint refuserait le jeu entier.

## Ce qui reste

Rien n'est lu par le pivot ni par le site. La forme de la vue — camemberts
additionnés ou une barre par année, quelles caisses, depuis quelle année — n'est
pas arbitrée.
