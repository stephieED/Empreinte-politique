<a id="amendements-zero-silencieux-acteur-ref"></a>
# Zéro amendement silencieux quand l'acteurRef est introuvable (#265, fix 5) (2026-08-17)

`2026-08-17`

> **En bref** — un acteurRef introuvable ne rend plus zéro amendement en silence.

**Contexte** : re-check de #265 (« Zero amendments according to audit ») après
la résolution de [[cache-amendements-forme-dedupliquee]] (#377),
[[nettoyage-archive-brute-amendements]] (#264) et
[[verification-bout-en-bout-legislatures-figees]] (#273). Le fix 5 de son
investigation restait ouvert : déterminer si le zéro-sans-warning observé sur
les profils `candidat_declare` était une absence réelle ou un second bug
indépendant.

**Réponse : les deux à la fois.**
- *Absence réelle* pour `bruno-retailleau` (sénateur) et `jordan-bardella`
  (MEP) : `fetch_amendements_officiels` n'est jamais appelée pour eux, l'appel
  étant gardé par `if chambre == "deputes"` dans `build_profile`. Zéro
  correct, aucun warning attendu.
- *Bug indépendant réel* : quand `url_an_ou_senat` est absent ou non parsable,
  `fetch_amendements_officiels` retournait `[]` **sans aucun warning** — un
  zéro parfaitement silencieux, indiscernable d'une absence légitime.

**Ce n'était pas théorique** : `marine-le-pen` et `jean-luc-melenchon` avaient
tous deux `url_an_ou_senat: None` dans leur profil brut, écrit partiellement
par un run interrompu par l'OOM ([[oom-lecture-amendements-par-candidat]]),
accompagné du warning trompeur « aucun mandat français connu ». Leurs
amendements ne survivaient que par la fusion additive avec des runs
antérieurs — un `--no-merge`/`fresh_run=true` les aurait effacés en silence.
Régénération après correctifs : `url_an_ou_senat` correctement renseigné
(`.../OMC_PA720614`), 8 999 amendements, zéro warning.

**Décision** : émettre un warning `WARNING_PREFIX_AMENDEMENTS_INDISPONIBLES`
quand aucun acteurRef ne peut être extrait. Sans risque de bruit pour les
sénateurs/MEP puisqu'ils n'atteignent jamais ce chemin — le garde
`chambre == "deputes"` en amont fait que cette situation est *toujours* une
anomalie, jamais un cas nominal.

**État des 5 fixes de #265 après ce re-check** : fix 1 (séquencement
`needs: [extract-amendements-an]`) appliqué ; fix 2 caduc (alternative au
fix 1, explicitement conditionnée à « si le parallélisme doit être
préservé ») ; fix 3 (escalade en hard failure du quality gate) sorti dans
l'issue dédiée #378 — arbitrage produit (bloquer le commit vs. laisser passer
la panne CDN chronique de la législature 17), tranché depuis :
[[amendements-zero-pas-de-hard-fail]] (pas de blocage, mais signal affiché en
tête de rapport) ; fix 4 résolu par #268/#273 ; fix 5 tranché et
corrigé ici. #265 close : symptôme initial résolu, 32 279 amendements sur les
candidats déclarés contre 0 à son ouverture.

**Tests** : deux formes d'URL invalide (`None` et URL sans acteurRef)
produisent bien un warning ; non-régression quand `warnings` n'est pas
fourni par l'appelant (paramètre optionnel). Suite complète : 1153/1153.

