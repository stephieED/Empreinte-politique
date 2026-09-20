<a id="pivot-freshness-timestamps-stables"></a>
# `genere_le`/`synchro_le` des pivots ne doivent avancer que si le contenu change réellement (#343) (2026-08-16)

`2026-08-16`

> **En bref** — `genere_le`/`synchro_le` n'avancent que si le contenu change réellement.

**Contexte** : en creusant les conséquences de l'angle mort `if: always()`
documenté ci-dessous ([[resilience-generate-data-shutdown-signal]]), constat
sur un run réel (`extract-an`/`extract-roster-groupes` en échec, aucune
donnée AN fraîche disponible) qu'un commit a quand même été poussé avec 123
fichiers modifiés — diff réel vérifié sur
`pivot_data/profiles/jean-luc-melenchon.pivot.json` : **zéro changement de
contenu**, seuls `meta.genere_le` et `sources[].synchro_le` avaient avancé.
Cause : `--pivot-only` (`generate_all_profiles.py`) re-dérive systématiquement
le pivot depuis le profil brut déjà présent sur disque (aucun appel réseau),
mais `schema_pivot.make_empty_profil` tamponne `meta.genere_le =
time.strftime(...)` inconditionnellement à chaque appel, et
`normalize_europarl`/`normalize_nosdeputes` retombent sur `time.strftime(...)`
dès que le profil brut source ne porte pas lui-même un horodatage exploitable
— sans jamais comparer au pivot déjà commité. Contraire à la règle de
traçabilité (AGENTS.md §2 règle 2) : ces champs sont censés refléter quand la
donnée a été *effectivement* collectée, pas la dernière exécution du script.

**Décision** : `merge_profile.preserve_stable_freshness_timestamps(old_pivot,
new_pivot)` compare une empreinte JSON du pivot en ignorant précisément
`meta.genere_le` et `sources[].synchro_le` (`_pivot_content_fingerprint`) ;
si le contenu est identique à l'ancien pivot committé, les anciens
horodatages sont restaurés sur `new_pivot` avant écriture (comparaison
`sources[]` par `type`, pas par index, pour rester robuste à un réordonnancement).
Appelée juste avant l'écriture disque dans les deux chemins de
`generate_all_profiles.py` qui écrivent un pivot (`--pivot-only` et
`--pivot` normal, après un éventuel `merge_pivot_profile`) — le mode normal
peut produire le même symptôme si un run réseau ne rapporte aucune donnée
nouvelle.

**Périmètre** : uniquement les pivots candidats (`pivot_data/profiles/`). Le
même motif (`meta.genere_le` re-tamponné inconditionnellement à chaque
régénération, `schema_groupe.py`/`schema_gouvernement.py`/`schema_parti.py`)
est probable pour `group_profile.py`/`gouvernement_profile.py`/
`parti_profile.py`, qui reconstruisent leur sortie sans jamais comparer à
l'ancienne version — pas de repro confirmé pour ces pivots, laissé en
`ROADMAP.md` plutôt que corrigé à l'aveugle ici.

