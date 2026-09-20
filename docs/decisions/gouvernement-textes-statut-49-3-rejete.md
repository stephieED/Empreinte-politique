<a id="gouvernement-textes-statut-49-3-rejete"></a>
# `KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL` : ajout de `rejete_49_3` (#208, réouverte) (2026-08-14)

`2026-08-14`

> **En bref** — `rejete_49_3` ajouté à la nomenclature fermée : le 49.3 n'est pas qu'une voie d'adoption.

**Contexte** : la nomenclature fermée des statuts de texte gouvernemental
(#208, fusionnée dans `main`) n'anticipait le 49.3 (art. 49 al. 3 de la
Constitution) que comme voie d'**adoption** (`statut = "adopte_49_3"`). En
implémentant la collecte réelle (#210), un cas non anticipé est apparu sur
des données AN réelles : `fam_code` `TSORTF24` = « rejeté via 49.3, motion de
censure adoptée » — c'est le sort effectivement survenu au budget 2025 sous
le gouvernement Barnier (décembre 2024). Ce n'est pas un cas hypothétique
qu'on choisirait d'anticiper par prudence : c'est un fait déjà survenu, donc
certain de réapparaître dans la donnée historique. `gouvernement_textes.py`
mappait ce cas à `statut = "rejete"` + `sort_49_3 = True`, une combinaison
que `validate_profil_gouvernement` rejetait (seul `"adopte_49_3"` était
autorisé avec `sort_49_3 = True`) — ce qui aurait fait échouer dur
l'agrégation (#211) dès le premier gouvernement réel touché par ce cas.

**Décision** : ajout de `"rejete_49_3"` à `KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL`,
symétrique d'`"adopte_49_3"` — même exigence d'appariement avec
`sort_49_3 = True`, même interdiction de collapse silencieux (cette fois vers
`"rejete"` simple plutôt que vers `"adopte"`). Alternative rejetée : assouplir
le validateur pour rendre `sort_49_3` orthogonal au `statut` (autorisé avec
n'importe quelle valeur) — écartée car elle affaiblirait la garantie actuelle
que le 49.3 reste toujours visible comme son propre statut explicite plutôt
que comme un simple booléen surimposé (règle AGENTS.md §2.4). Cohérent avec
le principe déjà acté en #208 : le 49.3 est un fait procédural distinct de
l'issue du vote, jamais fusionné avec elle — cette règle s'applique
symétriquement au rejet, pas seulement à l'adoption.

