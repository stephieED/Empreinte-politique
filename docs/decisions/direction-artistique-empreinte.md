<a id="direction-artistique-empreinte"></a>
# Direction artistique de `web/UI_finale` : brief, itérations et alternatives écartées (2026-08-14)

`2026-08-14`

> **En bref** — direction artistique de `web/UI_finale` : brief, itérations, et les alternatives écartées.

**Contexte** : refonte de la direction artistique de `web/UI_finale` (CONTRECHAMP),
pensée pour trois cibles emboîtées — des citoyens français en âge de voter,
engagés et avec une appétence tech/data/analytics (cœur de cible ayant guidé
les choix), jusqu'au grand public français. Le brief demandait une DA moderne,
orientée tech & analytics, en **rupture explicite** avec les codes
médias/presse et avec `web/old/v3` en particulier (masthead, police Archivo
Black, kickers datés, rayon de bordure zéro).

Socle retenu dès le départ : un « produit SaaS analytique » (sidebar, cartes
blanches, hairlines) avec un vocabulaire « instrumentation scientifique » pour
les chiffres (nombres tabulaires stricts, `font-variant-numeric: tabular-nums`) ;
un graphe de réseau a été explicitement mis de côté pour une éventuelle vue
avancée future, pas retenu dans ce socle. Le brief demandait aussi une
composante user-friendly, dynamique jeu/appli mobile façon Revolut — mais
**forme et geste uniquement, jamais le ton** : poser un score, un streak, un
badge, un classement ou une félicitation aurait directement contredit la règle
1 de `AGENTS.md §2` (aucun jugement de valeur, aucun score, aucun classement) —
posé dès le brief comme une règle fondatrice du projet, pas une préférence
esthétique.

Une première itération inspirée de Revolut a ensuite été **explicitement
corrigée** pour s'en éloigner visuellement : abandon du violet, des chips
pastel par catégorie, des avatars multicolores. Réintroduction du code
jaune fluo / noir — l'acide `#DFFF00` déjà présent dans `web/old/v3` — mais
cette fois en usage strictement fonctionnel (accent de sélection/action/source
vérifiée, jamais décoratif, jamais en texte sur fond clair — voir la table de
contraste WCAG dans `web/UI_finale/DESIGN_SYSTEM.md` §2, ratio 1.05:1 = échec
AA). Ajustements de détail en revue de maquette : texte noir sur fond jaune
(pas l'inverse) ; carte héro finalement en noir/texte blanc plutôt qu'en
jaune ; fond non neutre — filigrane d'arcs concentriques façon empreinte
digitale, en transparence, couvrant tout le fond (explicitement pas une
mosaïque répétée du logo — implémenté dans `src/styles/shell.css`, `.app-shell`).

**Décision** : livrer des maquettes mobile puis web sur les deux fiches
existantes (Candidat, Groupe) sans modifier le socle analytique déjà validé,
en intégrant les retours de revue : surbrillance au survol des cartes KPI
(`.kpi-caveat`), flyouts au clic pour mandats et responsabilités, reprise des
infographies de la page Gabriel Attal dans l'onglet Textes, correction de
l'alignement logo/wordmark. Le design system a ensuite été généré à partir de
ces maquettes App Web, publié en artifact Claude (« Empreinte — Direction
artistique · v1 »,
`claude.ai/code/artifact/d48b7554-0af3-45bd-904e-94367577ff4a`), puis
réconcilié ligne à ligne avec le code réel de `web/UI_finale/src` pour produire
`web/UI_finale/DESIGN_SYSTEM.md` (v2) — voir ce fichier pour l'état final
détaillé (palette, typographie, composants) et sa section 8 pour les écarts
constatés entre la cible et l'implémentation.

*Alternative rejetée* : conserver la direction visuelle façon Revolut (violet,
chips pastel par catégorie, avatars multicolores) et son registre ludique
(score/streak/badge/classement/félicitation) — rejetée non pas pour goût
esthétique mais parce qu'elle réintroduirait un jugement de valeur explicitement
interdit par la règle 1 de `AGENTS.md §2`. Toute proposition future de
gamification de l'interface doit être évaluée à l'aune de cette même règle, pas
seulement d'une préférence de design.
