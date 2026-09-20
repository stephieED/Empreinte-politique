#!/usr/bin/env python3
"""
audit_integrite_referentielle.py — Vérifie que chaque clé publiée par une
couche de `pivot_data/` résout dans l'index partagé qu'elle référence (#485).

**Un contrôle d'invariance dans un état donné, pas de variation dans le temps.**
C'est ce qui le distingue d'`audit_diff_profils.py` ([[controle-de-perte-avant-commit]],
#460/#470), et c'est pourquoi il ne peut pas y être versé : ce dernier compare
un **avant** et un **après**. Il verrait une chute du nombre d'entrées d'un
index, mais pas une rupture de correspondance entre deux couches du **même**
état — un run où les profils et l'index seraient tous deux régénérés de façon
cohérente-mais-fausse (convention de clé changée des deux côtés) lui paraîtrait
irréprochable. Sa section « ce qu'il ne couvre pas » nommait ce trou comme le
plus sérieux qui restait.

## Pourquoi ce contrôle existe

#432 a normalisé les votes et #431 les amendements : le détail a quitté les
profils pour un index partagé, et les profils n'en gardent qu'une **clé**. La
donnée est passée d'un état **auto-suffisant** (chaque profil portait sa copie
complète) à un état **référentiel** : un vote n'a de sens que si sa clé résout.

Trois façons de casser cette correspondance, dont aucune ne bouge un compteur :

  - une clé de profil qui ne résout pas → un vote **publié sans objet** ;
  - un index régénéré avec une autre convention de clé → **toutes** les
    références cassées d'un coup ;
  - un index publié partiellement (échec de shard, artifact tronqué) → une
    fraction des références orpheline, silencieusement. Ce n'est pas théorique :
    c'est ce que #450 faisait aux profils, et #465 a montré qu'une sous-collecte
    en échec s'écrit comme une collecte vide.

## Ce qui bloque, ce qui est seulement rapporté

**Bloque** (AGENTS.md §2.5 : jamais de valeur par défaut sur une donnée non
résolue — échouer bruyamment) :

  - une **référence orpheline** : la clé est là, l'entrée d'index n'y est pas.
    Le fichier et la clé sont nommés. Zéro faux positif possible par
    construction : la propriété vérifiée est binaire, pas un seuil ;
  - un **index ou un shard absent** alors que des références le visent. Rapporté
    à part parce que le remède n'est pas le même — ce n'est pas une clé à
    corriger, c'est un fichier à publier ;
  - une clé **absente sans son enregistrement de repli** (`scrutin_non_resolu`,
    `amendement_non_resolu`). `validate_profil()` l'interdit déjà : un vote
    qu'on ne sait pas rattacher garde son enregistrement complet, il n'est ni
    supprimé ni doté d'une clé inventée.

**Rapporté sans bloquer :**

  - les **entrées d'index que personne ne référence**. Elles sont à 0 aujourd'hui,
    et ce n'est pas une coïncidence : les deux index sont **construits depuis**
    `raw_data/profiles` (`build_scrutins_index.py`, `build_amendements_index_pivot.py`),
    donc toute entrée vient d'un profil. Mais leur fusion est **additive par
    contrat** — « a partial run must never drop ballots that other profiles'
    mappings still point at » (AGENTS.md §3). Cette additivité implique qu'une
    entrée survive légitimement à son référent : profil corrigé, membre sorti du
    corpus, tranche non retraitée. Bloquer dessus reviendrait à interdire la
    propriété de sûreté principale du pipeline. C'est donc un **compteur de
    dérive**, pas une règle ;
  - les clés **absentes avec** leur enregistrement de repli : c'est la forme
    normale d'un amendement du Parlement européen, que ParlTrack livre sans uid
    AN.

## Le drapeau, et pourquoi il n'est pas celui du contrôle de perte

`--tolerer-orphelins` est **distinct** de `--tolerer-pertes` d'`audit_diff_profils`
(input `allow_declared_losses` du workflow), et les deux ne doivent jamais
fusionner. #470 a documenté le piège : rendre bloquant un contrôle grossier
force l'opérateur à relancer avec la tolérance, ce qui **désarme du même coup**
les contrôles précis. Une perte peut être légitime et se déclare ; une référence
orpheline, elle, n'a aucune explication légitime — ce drapeau n'existe que pour
qu'une panne de cet outil ne puisse pas bloquer indéfiniment toute publication,
jamais comme un mode d'exploitation.

## Dimensionnement

Ce script tourne AVANT le commit : s'il meurt, rien n'est publié, et un
garde-fou qui meurt est pire qu'un garde-fou absent. `audit_diff_profils` s'est
déjà fait tuer par l'OOM killer une fois (#460).

Une seule règle y suffit, et elle rend le diagnostic de #470 (« hors de portée
d'un contrôle à mémoire bornée : il faudrait tenir les deux ensembles de clés en
mémoire simultanément ») inutilement pessimiste : **un seul des deux côtés est
tenu en mémoire**, et c'est le petit. Les clés d'index tiennent dans un `set` ;
le côté référençant — profils et groupes, c'est-à-dire les 102 Mo qui grossiront
avec le corpus — est parcouru **un document à la fois** et jamais retenu.

Mesuré sur les 209 profils et 7 groupes de `01ffa7f` (`/usr/bin/time`, médiane
de trois exécutions, même machine que #470) :

  - contrôle de perte seul, pour repère    : 4,76 s / 186,6 Mio
  - ce contrôle, les deux index            : **3,02 s / 162,0 Mio**
  - ce contrôle, `--sans-amendements`      : 1,79 s /  74,9 Mio

Sous les 236 Mio actés par #460, et **sous** le contrôle de perte lui-même. Ce
sont deux processus successifs, pas un seul : le pic du pipeline reste celui du
plus coûteux des deux, et ne bouge donc pas.

La RSS est **invariante au nombre de profils**. Elle est fixée par le plus gros
shard d'index (`15.json`, 24,7 Mo → ~102 Mio à parser) et par le `set` de clés ;
le côté référençant ne coûte qu'un document (le plus gros profil pèse 2,5 Mo,
la médiane 0,44 Mo). Or les deux index sont déjà à pleine échelle — 17 535
scrutins et 207 238 amendements distincts, construits depuis les archives AN
figées et non depuis les 209 membres actuels. Le passage à 752 membres
multiplie les **références**, pas l'index.

Seule la durée suit, linéairement, et le détail le montre : 0,79 s de lecture
d'index (fixe : 0,10 s scrutins + 0,69 s amendements) + 9,1 ms par profil. Soit
**~7,7 s projetées à 752 profils**, dans un job dont le budget est de 60 min et
la mesure de 47,4.

Usage :
    python3 src/audit_integrite_referentielle.py
    python3 src/audit_integrite_referentielle.py --pivot-dir pivot_data \\
        --out audit/integrite.md --out-json audit/integrite.json
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from amendements_index import legislature_de_id  # noqa: E402
from scrutins_index import decomposer_id as decomposer_scrutin_id  # noqa: E402

#: Nom des deux index partagés. Sert de clé dans le rapport et les messages.
INDEX_SCRUTINS = "scrutins"
INDEX_AMENDEMENTS = "amendements"

#: `*.cosignatures.json` n'est pas un shard d'index : c'est le compagnon de
#: #431, que personne ne référence et qu'ouvrir coûterait 222 Mio de RSS pour le
#: seul `15.cosignatures.json` (#470). Motif **négatif** et non positif :
#: `fnmatch`/`glob` laissent `*` traverser le point, si bien qu'un `[0-9]*.json`
#: censé ne retenir que `14.json` attraperait aussi `14.cosignatures.json` —
#: écrit dans l'autre sens, l'exclusion serait silencieusement annulée.
SUFFIXE_COSIGNATURES = ".cosignatures.json"


@dataclass(frozen=True)
class Renvoi:
    """Un champ publié qui porte une clé vers un index partagé.

    `declaration` nomme le champ qui doit porter l'enregistrement complet quand
    la clé est absente (`scrutin_non_resolu`, `amendement_non_resolu`). `None`
    signifie qu'aucune absence n'est prévue par le schéma : `cohesion_votes` est
    construit **depuis** des scrutins déjà résolus, une entrée sans clé y serait
    un dénominateur publié sur un objet inconnu (AGENTS.md §2.7).
    """

    couche: str
    liste: str
    cle: str
    index: str
    declaration: Optional[str] = None

    @property
    def champ(self) -> str:
        return f"{self.liste}[].{self.cle}"


#: Les seuls renvois de `pivot_data/`. Mesuré sur les 209 profils, 7 groupes,
#: 3 partis et 8 gouvernements de `01ffa7f` : `partis/` et `gouvernements/` ne
#: portent aucune clé d'index — leurs agrégats sont des compteurs, pas des
#: références. Ajouter une couche ici suffit à l'inclure au contrôle.
RENVOIS: tuple[Renvoi, ...] = (
    Renvoi("profiles", "votes", "scrutin_id", INDEX_SCRUTINS, "scrutin_non_resolu"),
    Renvoi("profiles", "amendements", "amendement_id", INDEX_AMENDEMENTS,
           "amendement_non_resolu"),
    # LA couche de #470 : une rupture y produit un **dénominateur faux**
    # (AGENTS.md §2.7, mécanisme de la perte SOC-16) plutôt qu'une fiche
    # incomplète. 12 546 références aujourd'hui.
    Renvoi("groupes", "cohesion_votes", "scrutin_id", INDEX_SCRUTINS),
)

#: Répertoire de chaque couche sous `--pivot-dir`.
REPERTOIRES: dict[str, str] = {"profiles": "profiles", "groupes": "groupes"}


# ---------------------------------------------------------------------------
# Les index, côté « petit » : seules les clés sont retenues
# ---------------------------------------------------------------------------

@dataclass
class Index:
    """Les clés d'un index partagé, et rien d'autre.

    `present=False` distingue « index jamais construit » de « index vide » :
    dans le premier cas les références ne sont pas orphelines une à une, c'est
    le fichier entier qui manque, et le remède n'est pas le même.

    `shards` est vide pour un index tenu dans un seul fichier (`scrutins.json`)
    et porte les législatures présentes pour un index shardé (`amendements/`) —
    ce qui permet de nommer un shard manquant au lieu de rapporter des dizaines
    de milliers de clés orphelines pour un seul fichier absent.
    """

    nom: str
    cles: set[str] = field(default_factory=set)
    present: bool = False
    entrees_par_fichier: dict[str, int] = field(default_factory=dict)
    shards: set[str] = field(default_factory=set)
    #: Clés effectivement rencontrées. Second `set` plutôt qu'une suppression
    #: destructive dans `cles` : une clé référencée deux fois doit rester
    #: résoluble la seconde fois. Coût mesuré : +4 Mio sur les 207 238 clés.
    vues: set[str] = field(default_factory=set)

    def resout(self, cle: str) -> bool:
        if cle in self.cles:
            self.vues.add(cle)
            return True
        return False

    @property
    def jamais_referencees(self) -> int:
        return len(self.cles) - len(self.vues)


def charger_index_scrutins(chemin: Path) -> Index:
    """Clés de `pivot_data/scrutins.json`, sans en retenir le méta.

    Le document est parsé en entier — 8,5 Mo, ~37 Mio de pointe — puis libéré :
    seul le `set` d'identifiants survit. Le méta d'un scrutin (date, texte,
    sort…) n'intéresse pas ce contrôle, qui ne vérifie que l'existence.
    """
    index = Index(nom=INDEX_SCRUTINS)
    if not chemin.is_file():
        return index
    try:
        doc = json.loads(chemin.read_bytes())
    except (OSError, ValueError):
        return index
    entrees = doc.get("scrutins")
    if not isinstance(entrees, list):
        return index
    index.present = True
    index.cles = {s.get("id") for s in entrees if isinstance(s, dict)} - {None}
    index.entrees_par_fichier[chemin.name] = len(entrees)
    return index


def charger_index_amendements(repertoire: Path) -> Index:
    """Clés de `pivot_data/amendements/<legislature>.json`, shard par shard.

    Chaque shard est parsé, ses clés extraites, puis **libéré avant le
    suivant** : la pointe est celle du plus gros shard (`15.json`, 24,7 Mo →
    ~102 Mio), pas celle de leur somme. C'est le seul endroit coûteux du
    contrôle, et il ne grossit pas avec le corpus (#470 : les 207 238
    amendements distincts sont déjà le chiffre de pleine échelle, construits
    depuis les archives AN figées).
    """
    index = Index(nom=INDEX_AMENDEMENTS)
    if not repertoire.is_dir():
        return index
    index.present = True
    for chemin in sorted(repertoire.iterdir()):
        if not chemin.is_file() or chemin.name.endswith(SUFFIXE_COSIGNATURES):
            continue
        if chemin.suffix != ".json":
            continue
        try:
            doc = json.loads(chemin.read_bytes())
        except (OSError, ValueError):
            continue
        entrees = doc.get("amendements")
        if not isinstance(entrees, dict):
            del doc
            continue
        index.cles |= set(entrees)
        index.entrees_par_fichier[chemin.name] = len(entrees)
        legislature = doc.get("legislature")
        if isinstance(legislature, str) and legislature:
            index.shards.add(legislature)
        else:
            index.shards.add(chemin.stem)
        del doc, entrees
    return index


def _shard_attendu(index: Index, cle: str) -> Optional[str]:
    """Législature qu'une clé vise, si son index est shardé.

    `None` quand l'index n'est pas shardé, ou quand la clé est trop mal formée
    pour qu'on sache où elle aurait dû tomber — dans ce cas on ne devine pas
    (AGENTS.md §2.5), la référence est simplement orpheline.
    """
    if index.nom != INDEX_AMENDEMENTS:
        return None
    return legislature_de_id(cle)


def _cle_malformee(index_nom: str, cle: str) -> bool:
    """La clé ne suit pas la forme de son index — un diagnostic, pas un verdict.

    Une clé mal formée est de toute façon orpheline ; le distinguer ne change
    pas le blocage, seulement le message : « corrige la convention de clé »
    plutôt que « publie l'entrée manquante ».
    """
    if index_nom == INDEX_SCRUTINS:
        legislature, numero = decomposer_scrutin_id(cle)
        return legislature is None or numero is None
    return legislature_de_id(cle) is None


# ---------------------------------------------------------------------------
# Le côté « grand » : parcouru un document à la fois, jamais retenu
# ---------------------------------------------------------------------------

def verifier_document(
    doc: Any,
    fichier: str,
    couche: str,
    index_par_nom: dict[str, Index],
    renvois: tuple[Renvoi, ...] = RENVOIS,
) -> list[dict[str, Any]]:
    """Constats d'un seul document. Fonction pure hors mutation des `Index.vues`.

    Rend un constat par référence **fautive**, jamais un par référence : sur un
    corpus sain la liste est vide, et c'est le cas nominal.

    `renvois` est un paramètre et non la constante globale : `--sans-amendements`
    retire un renvoi du périmètre, et le retirer ici est la seule façon honnête
    de ne pas le vérifier — filtrer les constats après coup reviendrait à
    déclarer sain ce qu'on n'a pas regardé.
    """
    constats: list[dict[str, Any]] = []
    if not isinstance(doc, dict):
        return [{"motif": "document_illisible", "couche": couche,
                 "fichier": fichier, "champ": None, "cle": None,
                 "detail": None, "position": None}]

    for renvoi in renvois:
        if renvoi.couche != couche:
            continue
        entrees = doc.get(renvoi.liste)
        if not isinstance(entrees, list):
            continue
        index = index_par_nom[renvoi.index]
        for position, entree in enumerate(entrees):
            if not isinstance(entree, dict):
                continue
            cle = entree.get(renvoi.cle)
            if cle is None:
                # Clé absente. Deux états très différents : déclarée
                # non résolue (l'enregistrement complet est là, la donnée n'est
                # pas perdue — forme normale d'un amendement UE), ou absente
                # tout court, ce que `validate_profil()` interdit déjà.
                if renvoi.declaration and isinstance(
                        entree.get(renvoi.declaration), dict):
                    constats.append({
                        "motif": "non_resolue_declaree", "couche": couche,
                        "fichier": fichier, "champ": renvoi.champ,
                        "cle": None, "detail": renvoi.declaration,
                        "position": position,
                    })
                else:
                    constats.append({
                        "motif": "cle_absente_sans_declaration", "couche": couche,
                        "fichier": fichier, "champ": renvoi.champ,
                        "cle": None, "detail": renvoi.declaration,
                        "position": position,
                    })
                continue
            if not isinstance(cle, str):
                # Une clé qui n'est pas une chaîne ne peut résoudre nulle part,
                # et `resout()` la compterait à tort comme « vue ».
                constats.append({
                    "motif": "orpheline", "couche": couche,
                    "fichier": fichier, "champ": renvoi.champ,
                    "cle": repr(cle), "detail": "clé qui n'est pas une chaîne",
                    "position": position,
                })
                continue
            if index.resout(cle):
                continue
            if not index.present:
                motif, detail = "index_absent", index.nom
            else:
                shard = _shard_attendu(index, cle)
                if shard is not None and shard not in index.shards:
                    motif, detail = "shard_absent", f"{index.nom}/{shard}.json"
                elif _cle_malformee(index.nom, cle):
                    motif, detail = "orpheline", "clé mal formée"
                else:
                    motif, detail = "orpheline", None
            constats.append({
                "motif": motif, "couche": couche, "fichier": fichier,
                "champ": renvoi.champ, "cle": cle, "detail": detail,
                "position": position,
            })
    return constats


def _documents(repertoire: Path) -> Iterator[tuple[str, Any]]:
    """Chaque `*.json` d'un répertoire, un à la fois.

    Le document est rendu puis abandonné par l'appelant : c'est ce qui rend la
    RSS indépendante du nombre de profils. Ne jamais accumuler ici.
    """
    if not repertoire.is_dir():
        return
    for chemin in sorted(repertoire.iterdir()):
        if not chemin.is_file() or chemin.suffix != ".json":
            continue
        try:
            yield chemin.name, json.loads(chemin.read_bytes())
        except (OSError, ValueError):
            yield chemin.name, None


#: Nombre d'exemples nommés dans le rapport et sur stderr. Au-delà, seuls les
#: compteurs par fichier subsistent : un index absent produirait 524 353 lignes
#: identiques, illisibles là où le total et trois exemples suffisent.
PLAFOND_EXEMPLES = 20

#: Motifs qui annulent le commit. `non_resolue_declaree` en est absent par
#: choix : l'enregistrement complet est conservé, la donnée n'est ni perdue ni
#: inventée — c'est exactement le repli que §2.5 prescrit, pas une violation.
MOTIFS_BLOQUANTS = frozenset({
    "orpheline", "index_absent", "shard_absent",
    "cle_absente_sans_declaration", "document_illisible",
})


def auditer(
    pivot_dir: Path,
    *,
    avec_amendements: bool = True,
    plafond_exemples: int = PLAFOND_EXEMPLES,
) -> dict[str, Any]:
    """Relève l'intégrité référentielle de `pivot_data/` telle qu'elle est sur le disque.

    Pas de git ici, contrairement à `audit_diff_profils` : ce contrôle porte sur
    **un** état, celui qu'on s'apprête à committer. Il n'a pas de point de
    comparaison, et c'est le fond du sujet.
    """
    renvois_actifs = tuple(r for r in RENVOIS
                           if avec_amendements or r.index != INDEX_AMENDEMENTS)
    index_actifs = {r.index for r in renvois_actifs}
    index_par_nom = {
        INDEX_SCRUTINS: (charger_index_scrutins(pivot_dir / "scrutins.json")
                         if INDEX_SCRUTINS in index_actifs
                         else Index(nom=INDEX_SCRUTINS)),
        INDEX_AMENDEMENTS: (charger_index_amendements(pivot_dir / "amendements")
                            if INDEX_AMENDEMENTS in index_actifs
                            else Index(nom=INDEX_AMENDEMENTS)),
    }

    references: dict[str, int] = {r.champ: 0 for r in renvois_actifs}
    constats: list[dict[str, Any]] = []
    par_motif: dict[str, int] = {}
    par_champ: dict[str, int] = {r.champ: 0 for r in renvois_actifs}
    par_fichier: dict[str, int] = {}
    fichiers_lus: dict[str, int] = {}

    for couche, sous_repertoire in REPERTOIRES.items():
        actifs = tuple(r for r in renvois_actifs if r.couche == couche)
        if not actifs:
            continue
        fichiers_lus[couche] = 0
        for nom, doc in _documents(pivot_dir / sous_repertoire):
            fichiers_lus[couche] += 1
            if isinstance(doc, dict):
                for renvoi in actifs:
                    entrees = doc.get(renvoi.liste)
                    if isinstance(entrees, list):
                        references[renvoi.champ] += len(entrees)
            for constat in verifier_document(doc, nom, couche, index_par_nom, actifs):
                motif = constat["motif"]
                par_motif[motif] = par_motif.get(motif, 0) + 1
                if motif not in MOTIFS_BLOQUANTS:
                    continue
                par_fichier[nom] = par_fichier.get(nom, 0) + 1
                champ = constat["champ"]
                if champ in par_champ:
                    par_champ[champ] += 1
                # Seuls les constats BLOQUANTS sont retenus en exemple : un
                # plafond partagé avec les non-bloquants laisserait 20 clés
                # légitimement non résolues évincer la seule qui annule le
                # commit, et le message perdrait ce qui le rend actionnable.
                if len(constats) < plafond_exemples:
                    constats.append(constat)
            del doc

    bloquants = sum(n for motif, n in par_motif.items() if motif in MOTIFS_BLOQUANTS)
    return {
        "references": references,
        "total_references": sum(references.values()),
        "fichiers_lus": fichiers_lus,
        "constats_par_motif": par_motif,
        "constats_par_champ": par_champ,
        "constats_par_fichier": par_fichier,
        "exemples": constats,
        "plafond_exemples": plafond_exemples,
        "nb_bloquants": bloquants,
        "bloquant": bloquants > 0,
        "index": {
            nom: {
                "present": index.present,
                "entrees": len(index.cles),
                "entrees_par_fichier": index.entrees_par_fichier,
                "shards": sorted(index.shards),
                "referencees": len(index.vues),
                "jamais_referencees": index.jamais_referencees,
            }
            for nom, index in index_par_nom.items()
        },
        "avec_amendements": avec_amendements,
    }


# ---------------------------------------------------------------------------
# Rapport
# ---------------------------------------------------------------------------

_LIBELLES = {
    "orpheline": "référence orpheline — la clé est publiée, l'entrée d'index n'existe pas",
    "index_absent": "index entier absent alors que des références le visent",
    "shard_absent": "shard d'index absent alors que des références le visent",
    "cle_absente_sans_declaration": "clé absente sans son enregistrement de repli",
    "document_illisible": "document JSON illisible",
    "non_resolue_declaree": "clé absente, enregistrement complet conservé (non bloquant)",
}


def generate_markdown_report(rapport: dict[str, Any]) -> str:
    """Rapport Markdown, joint au résumé de job à chaque run."""
    lignes = [
        "# Intégrité référentielle de `pivot_data/`",
        "",
        "> Contrôle d'**invariance dans un état donné** : chaque clé publiée "
        "résout-elle dans l'index qu'elle référence ? À ne pas confondre avec le "
        "contrôle de perte (#460/#470), qui compare un avant et un après et ne "
        "verrait pas deux couches devenues incohérentes ensemble.",
        "",
    ]
    if rapport["bloquant"]:
        lignes += [f"**{rapport['nb_bloquants']} référence(s) non résolue(s)** — "
                   "commit à annuler : un vote ou un amendement publié sans objet "
                   "(AGENTS.md §2.5).", ""]
    else:
        lignes += [f"**Intégrité intacte** sur "
                   f"{rapport['total_references']} référence(s).", ""]

    lignes += ["| Renvoi | Références | Non résolues |",
               "| --- | ---: | ---: |"]
    for champ, total in rapport["references"].items():
        fautives = rapport["constats_par_champ"].get(champ, 0)
        lignes.append(f"| `{champ}` | {total} | {fautives} |")
    lignes.append("")

    lignes += ["## Index partagés", "",
               "| Index | Entrées | Référencées | Jamais référencées |",
               "| --- | ---: | ---: | ---: |"]
    for nom, info in rapport["index"].items():
        etat = "**absent**" if not info["present"] else str(info["entrees"])
        lignes.append(f"| `{nom}` | {etat} | {info['referencees']} | "
                      f"{info['jamais_referencees']} |")
    lignes += [
        "",
        "Une entrée que personne ne référence n'est **pas** une anomalie : la "
        "fusion des index est additive par contrat (AGENTS.md §3), donc une "
        "entrée survit légitimement à son référent — profil corrigé, membre "
        "sorti du corpus, tranche non retraitée. Compteur de dérive, jamais un "
        "verdict.",
        "",
    ]

    par_motif = rapport["constats_par_motif"]
    if par_motif:
        lignes += ["## Constats", "", "| Motif | Nombre | Bloquant |",
                   "| --- | ---: | --- |"]
        for motif, nombre in sorted(par_motif.items()):
            bloque = "oui" if motif in MOTIFS_BLOQUANTS else "non"
            lignes.append(f"| {_LIBELLES.get(motif, motif)} | {nombre} | {bloque} |")
        lignes.append("")

    exemples = rapport["exemples"]
    if exemples:
        lignes += [f"### {len(exemples)} exemple(s) nommé(s)", "",
                   "| Fichier | Champ | Clé | Motif |", "| --- | --- | --- | --- |"]
        for e in exemples:
            detail = f" ({e['detail']})" if e["detail"] else ""
            lignes.append(f"| `{e['fichier']}` | `{e['champ']}` | `{e['cle']}` | "
                          f"{_LIBELLES.get(e['motif'], e['motif'])}{detail} |")
        total = rapport["nb_bloquants"]
        if total > len(exemples):
            lignes.append(f"| … | | | {total - len(exemples)} de plus |")
        lignes.append("")

    if not rapport["avec_amendements"]:
        lignes += ["> `--sans-amendements` : l'index des amendements n'a pas été "
                   "lu, ses références ne sont donc **pas** vérifiées.", ""]

    lignes += [
        "## Hors périmètre de ce contrôle",
        "",
        "- la **valeur** d'une entrée d'index : seule son existence est vérifiée. "
        "Un scrutin dont le `texte` deviendrait `null` résout toujours ;",
        "- les `*.cosignatures.json`, que personne ne référence et qui coûtent "
        "222 Mio de RSS à ouvrir (#470) ;",
        "- la **variation** entre deux états, qui est le sujet "
        "d'`audit_diff_profils.py` (#460, #470) et pas celui-ci.",
        "",
    ]
    return "\n".join(lignes)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--pivot-dir", default="pivot_data", metavar="REP",
                        help="Racine de la couche publiée (défaut : pivot_data).")
    parser.add_argument("--sans-amendements", action="store_true",
                        help="Ne pas lire l'index des amendements (la couche la "
                             "plus coûteuse : ~102 Mio pour le shard 15). Ses "
                             "références ne sont alors PAS vérifiées, et le "
                             "rapport le dit.")
    parser.add_argument("--out", metavar="FICHIER", help="Rapport Markdown.")
    parser.add_argument("--out-json", metavar="FICHIER", help="Rapport JSON.")
    parser.add_argument(
        "--tolerer-orphelins", action="store_true",
        help="Ne pas sortir en erreur malgré une référence non résolue. "
             "DISTINCT de --tolerer-pertes d'audit_diff_profils : une perte "
             "peut être légitime, une référence orpheline non. N'existe que "
             "pour qu'une panne de cet outil ne bloque pas toute publication.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    pivot_dir = Path(args.pivot_dir)

    print(f"→ intégrité référentielle : {pivot_dir}…", file=sys.stderr)
    rapport = auditer(pivot_dir, avec_amendements=not args.sans_amendements)
    markdown = generate_markdown_report(rapport)

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(markdown, encoding="utf-8")
        print(f"→ Rapport écrit : {args.out}", file=sys.stderr)
    else:
        print(markdown)
    if args.out_json:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(
            json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    if rapport["bloquant"]:
        # Nommer le fichier ET la clé : sans les deux, le constat n'est pas
        # actionnable — c'est le critère d'acceptation de #485.
        for exemple in rapport["exemples"]:
            detail = f" ({exemple['detail']})" if exemple["detail"] else ""
            print(f"[!] {exemple['couche']} · {exemple['fichier']} · "
                  f"{exemple['champ']} = {exemple['cle']!r} : "
                  f"{_LIBELLES.get(exemple['motif'], exemple['motif'])}{detail}",
                  file=sys.stderr)
        if rapport["nb_bloquants"] > len(rapport["exemples"]):
            print(f"[!] … et {rapport['nb_bloquants'] - len(rapport['exemples'])} "
                  "autre(s), non détaillé(s).", file=sys.stderr)
        print(f"[!] {rapport['nb_bloquants']} référence(s) non résolue(s) sur "
              f"{rapport['total_references']}.", file=sys.stderr)
        return 0 if args.tolerer_orphelins else 1

    print(f"✓ {rapport['total_references']} référence(s) résolvent toutes.",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
