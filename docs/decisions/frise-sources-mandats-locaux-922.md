<a id="frise-sources-mandats-locaux-922"></a>

# La frise de /sources dessine les mandats locaux au lieu de « aucune source » (#922) (2026-09-16)

`2026-09-16`

> **En bref** — la ligne « Mandats locaux » de la frise de `/sources` portait une hachure pleine et « aucune source », écrite quand #922 n'avait encore rien collecté. Les fiches publiées portaient pourtant **34 mandats locaux sur 14 candidats déclarés** (mesuré le 16/09/2026, `couverture.json` du build local). `scripts/couverture-corpus.mjs` les compte désormais dans `institutions[]` sous la clé `local`, avec une **`borne` lue dans la donnée** (`mandats_locaux_couverture.borne_couverture`, 2020), jamais écrite dans le code. La ligne suit la grammaire des autres rails : **hachure avant la borne**, un **segment gris** de la première donnée à la collecte (la teinte des mandats locaux sur la fiche candidat), le compte et le nombre de candidats à droite ; la clé « Données collectées » gagne ce gris. Les mandats locaux **restent une ligne unique**, pas une institution à listes : ils n'ont qu'une liste. Sans aucune donnée collectée, la ligne retrouve la hachure pleine et « aucune source ». **Alternative écartée** : ajouter les mandats locaux à la hiérarchie à listes — une institution à une seule liste est un niveau de trop.
