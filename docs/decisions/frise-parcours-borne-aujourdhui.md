<a id="frise-parcours-borne-aujourdhui"></a>

# La frise du parcours s'arrête aujourd'hui pour tous les candidats (2026-09-16)

`2026-09-16`

> **En bref** — la frise « En bref » de la fiche candidat finissait à la **fin du dernier mandat** quand aucun n'était en cours, et à aujourd'hui sinon ; rien ne distinguait les deux axes, et le lecteur concluait que la carrière courait jusqu'à maintenant — signalé par la propriétaire le 16/09/2026. Mesuré ce jour-là sur les **23 candidats déclarés qui ont une frise** : **4** axes s'arrêtaient avant aujourd'hui (Bernard Cazeneuve et Ségolène Royal en 2017, Florian Philippot en 2019, Jean-Luc Mélenchon en 2022). La borne droite est désormais **la date du jour, lue à l'affichage** — jamais écrite dans le code — sauf fin postérieure, qui n'est pas rognée. Le blanc à droite dit « rien de collecté depuis ». **Conséquence traitée dans le même lot** : l'année de fin s'écrivait à côté du dernier repère rond (« 2025 2026 ») ; un repère à moins de 30 % du pas d'une borne s'efface à son profit. **Alternative écartée** : garder la fin du dernier mandat et marquer l'axe « jusqu'en 2017 » — un texte pour corriger une forme qui ment.

## Le contexte

`bornesDuParcours` posait la borne droite sur la fin la plus tardive, au motif
qu'« un axe qui déborde de la carrière laisserait croire à des années sans
rien ». L'effet inverse s'est produit : un axe qui s'arrête en 2017 se lit comme
un axe qui s'arrête aujourd'hui, et le dernier segment touche le bord droit.

## La décision

- `bornesDuParcours(roles, aujourdhui = aujourdhuiISO())` : la fin est la date du
  jour, ou une fin postérieure si un mandat en porte une.
- `anneesDeLAxe` (`CandidateProfile.jsx`) écrit toujours les deux bornes, et
  efface un repère rond à moins de 30 % du pas de l'une d'elles.

`tests/test_frise_borne_aujourdhui.py` exécute la fonction sous node ; deux de
ses cinq tests échouent sur le code d'avant.
