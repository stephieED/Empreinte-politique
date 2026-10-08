<a id="couverture-a-date-egale-source-par-source-1160"></a>
# À date égale, celui qui a lu la source l'emporte, comparé source par source (#1160) (2026-10-08)

`2026-10-08`

> **En bref** — complète `liste-sautee-garde-son-constat-1160`. Après le run planifié `37823704331` (08/10/2026, second run du jour), Emmanuel Maurel, Jean-Luc Mélenchon et Marine Le Pen publiaient encore leurs prises de parole « non collecté / par décision », alors que leur profil brut était réparé (`collecte_ecartee: []`, #1268). Les deux constats étaient datés du même jour. Le rang d'interrogation, calculé sur toute la liste, mettait l'ancien (`par_decision` pour l'AN, `couvert` pour le PE) à égalité avec le neuf (`couvert` partout), et la règle 4 gardait l'ancien. Arbitrage de la propriétaire, 08/10 : ajouter la règle. Règle **1ter** de `fusionner_couverture` : à date égale, un écrivain qui a lu une source que l'ancien déclarait « rien demandé » l'emporte, pourvu qu'il ne descende sur aucune autre source (`_rangs_par_source`).

Rejoué sur les trois profils publiés (privé `aa992c5367`) : Maurel et Le Pen passent en `couvert` ; Mélenchon en `non_collecte / panne`, parce que sa collecte du soir a été tronquée par le budget de temps, et qu'une panne prime (règle 2).

**Alternative écartée** : attendre le run du lendemain, qui répare par la date. Le défaut se reproduirait à chaque fois que deux runs tournent le même jour, ce qui est courant.
