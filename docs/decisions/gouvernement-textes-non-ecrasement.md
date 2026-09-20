<a id="gouvernement-textes-non-ecrasement"></a>
# Profils de gouvernement : ne jamais réécrire sur une collecte incomplète, et cache dossiers dédié (#427) (2026-08-18)

`2026-08-18`

> **En bref** — ne jamais réécrire un profil de gouvernement sur une collecte incomplète ; cache dossiers dédié.

**Contexte** : `merge-and-pivot` était le seul job de `generate-data.yml` sans
aucun `actions/cache`. Il re-téléchargeait les trois archives de dossiers
(~33 Mo) à chaque run — repéré en validant [[cache-cle-amendements-separee]]
(#424), qui avait supprimé les 438 Mo des jobs d'extraction et rendu ce résidu
visible.

**Mais le coût réseau n'était pas le problème.** `generate_gouvernement_profiles.py`
**écrase** les profils (`out_path.write_text`) ; `preserve_stable_freshness_timestamps`
(#343) ne préserve que les horodatages. Or `fetch_dossiers_gouvernementaux()`
est non-fatal : en cas de coupure réseau il rend `{"dossiers": []}` avec un
warning. L'enchaînement complet était donc :

1. coupure réseau sur `data.assemblee-nationale.fr` — observée 5 fois sur la
   seule archive XV lors du run `32136438841` ;
2. les 10 profils réécrits avec `textes: []` ;
3. le quality gate ne traitant ce cas qu'en **avertissement**, le commit reste
   autorisé ;
4. commit, push, puis publication par le déploiement automatique de #416.

**725 textes** auraient été perdus et mis en ligne — dont les 282 de Philippe II
et les 195 de Castex, que #400 venait de faire apparaître. Aucun incident ne
s'était produit (vérifié sur l'historique de `gouvernement-CASTEX.json` : les
`textes=0` antérieurs au 18/08 datent d'avant #400), mais les deux conditions
coexistaient.

## Correctif 1 — refus de réécrire (le vrai)

`fetch_dossiers_gouvernementaux()` retourne désormais `legislatures_ingerees`.
Ce n'est pas une information d'affichage : c'est **le seul moyen pour l'appelant
de distinguer « zéro dossier constaté » de « collecte incomplète »**. Sans elle,
les deux cas sont indiscernables.

`generate_all()` abandonne alors toute écriture si une archive manque, et rend
la sentinelle `COLLECTE_INCOMPLETE`. Les profils déjà committés restent en
place, intacts. Un zéro non mesuré n'est pas une donnée (AGENTS.md §2.5).

Le contrôle porte sur **toute** archive manquante, pas seulement sur l'échec
total : perdre la seule XV, c'est perdre les 282 textes de Philippe II.

Deux pièges rencontrés :

- **Sentinelle, pas code de retour.** `generate_all()` retourne un *compte*
  d'échecs. Une première version signalait la collecte incomplète par la valeur
  `2` — exactement deux gouvernements en échec l'aurait alors déclenchée à tort.
  D'où un objet dédié, converti en code de sortie `2` seulement dans `main()`.
- **Un test existant assertait le comportement dangereux.**
  `test_generate_all_dossier_fetch_failure_reported_via_warnings` vérifiait que
  le profil ÉTAIT écrit avec `textes == []`. Il fallait le réécrire, pas
  l'adapter.

Côté workflow, le step est `continue-on-error: true` : faire échouer tout le
job priverait le run du commit des profils de candidats et de groupes, qui eux
sont corrects. L'échec reste visible dans la liste des steps.

## Correctif 2 — filet du quality gate

Le refus de réécrire supprime la cause connue. Le gate attrape la **signature**,
quelle qu'en soit l'origine — bug de collecte, régression de parsing, fusion
fautive : **tous** les gouvernements couverts à `textes[] == 0` simultanément
devient un échec **dur**.

Le critère porte sur la simultanéité, jamais sur un gouvernement isolé : un
gouvernement couvert peut légitimement n'avoir porté aucun texte — Philippe I
n'en a qu'un. Et il exige au moins deux gouvernements couverts, faute de quoi
« tous à zéro » ne distingue plus rien.

C'est un contrôle **sans accès à l'historique git** : le gate ne compare rien à
l'état précédent, et lui ajouter cette plomberie pour ce seul besoin n'était pas
justifié.

## Correctif 3 — clé de cache dédiée aux dossiers

`.cache/dossiers_an` sort de `public-data-cache-an-*` et reçoit
`public-data-cache-dossiers-<semaine>`, partagée par `extract-an`,
`extract-roster-groupes` et `merge-and-pivot` (qui gagne au passage le step
`week` qui lui manquait).

Restaurer `public-data-cache-an-*` depuis `merge-and-pivot` aurait embarqué
`scrutins_an` : plusieurs centaines de Mo pour en utiliser 46.

Contrairement au défaut de #424, il n'y a ici **aucune dissociation** entre
producteur de contenu et écrivain de clé — les trois jobs téléchargent et
consomment les mêmes archives, donc le premier qui sauvegarde suffit.

`tests/test_ci_cache_paths.py` s'étend en conséquence : les jobs lisant les
dossiers doivent tous les cacher, et la clé dédiée ne doit pas retomber sous la
clé AN.

**Vérification** : les trois protections ont été neutralisées une à une, chacune
fait échouer ses tests. 1310 tests verts.

---

