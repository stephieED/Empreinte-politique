<a id="purge-mandats-dupliques-prudence"></a>
# Purge des mandats hérités dupliqués : appariement prudent (#387) (2026-08-17)

`2026-08-17`

> **En bref** — purge des mandats hérités dupliqués par appariement prudent : la fusion additive ne remplace jamais.

**Contexte** : après [[taxonomie-mandats-typeorgane-an]] (#384), l'AN fournit
les mandats correctement catégorisés, mais les entrées héritées de l'ère
NosDéputés subsistent — la fusion additive ne remplace jamais. Le même organe
apparaît deux fois, dont une sous une étiquette fausse.

**Arbitrage retenu (utilisatrice) : prudence.** Un faux négatif laisse un
doublon visible — bénin ; un faux positif supprime un mandat réel —
irréversible hors git.

**Règle implémentée** (`src/purge_mandats_dupliques.py`) — une entrée n'est
retirée que si les 4 conditions sont réunies :
1. catégorie couverte par le référentiel AN ;
2. elle n'est pas elle-même une entrée AN ;
3. son libellé normalisé correspond à celui d'une entrée AN **présente dans
   le profil** ;
4. sa période **recouvre** celle de cette entrée.

**Deux obstacles mesurés, qui ont façonné la règle** :

*Nommage divergent* — l'AN nomme l'organe par son seul thème
(« Trufficulture »), NosDéputés préfixe la nature (« Groupe d'études
trufficulture »). Aucun appariement exact ne rapproche les doublons : d'où la
normalisation par retrait de préfixe (`_PREFIXES_NATURE`, liste établie **par
mesure** sur les profils réels — un préfixe non listé produit une
non-correspondance, donc une conservation, jamais une suppression à tort).

*Datation divergente* — les deux référentiels ne datent jamais un même mandat
identiquement (écart de quelques jours à plusieurs semaines). Un appariement
par date exacte ne rapprocherait rien ; mais un même organe héberge aussi des
périodes réellement distinctes (entrée/sortie/remplacement). D'où le test de
**recouvrement**, ni exact ni absent.

**Défaut détecté à la mise au point, et corrigé** : la première version
comparait à l'extraction AN *fraîche* au lieu des entrées AN *présentes dans
le profil*. Sur un profil pas encore régénéré, cela retirait l'entrée héritée
sans que son équivalent soit là — **18 organes distincts perdus sur
`benjamin-haddad`, 16 sur `pascale-boyer`**, détecté par une vérification
indépendante comptant les organes distincts avant/après. La correction rend
le script sans effet tant que le profil n'est pas régénéré, ce qui *est* la
garantie « ne jamais retirer avant que l'équivalent soit présent » posée par
#387. Écart entre les deux versions : 599 suppressions sur 43 profils
(fautive) contre **193 sur 23** (correcte).

**Garde-fous** : `--dry-run` par défaut (`--apply` requis pour écrire) ;
profil sans acteurRef ignoré ; extraction AN vide ignorée (indiscernable d'un
échec transitoire, résilience #241) ; idempotent (vérifié : 0 suppression au
second passage).

**Résultat** : 193 doublons retirés sur 23 profils, **0 organe distinct
perdu** (vérifié par comptage indépendant), `gabriel-attal` passe de 10
doublons commission/groupe_etudes à 0.

**Tests** : 15 tests dédiés — normalisation (retrait de préfixe, casse/accents,
et garde-fou vérifiant qu'elle ne rapproche PAS deux organes distincts),
recouvrement de périodes (nominal, disjoint, bornes ouvertes jamais
substituées par aujourd'hui), et la règle complète (doublon avéré retiré,
période distincte conservée, entrée sans équivalent conservée, entrée AN
jamais retirée, catégories hors périmètre ignorées, idempotence, extraction
vide sans effet, et le cas du défaut ci-dessus). Suite complète : 1175/1175.

