#!/usr/bin/env python3
"""verifier_transport_artifacts.py — une panne de transport n'est pas une source absente (#786).

## Le défaut

Le run `34241352524` est **vert et n'a collecté personne**. Ses quatre
téléchargements d'artifacts d'extraction sont partis dans la même seconde et ont
tous reçu la même réponse sur `ListArtifacts` :

    [Response] - 403
    "You have exceeded a secondary rate limit. Please wait a few minutes..."
    ##[error]Unable to download artifact(s): Received non-retryable error

`download-artifact` ne rejoue pas un 403 — il le déclare non-retryable — et les
quatre steps portent `continue-on-error: true`, parce qu'une source en échec ne
doit pas bloquer les autres. `merge_raw_dirs` a donc vu quatre répertoires vides
et écrit `0 profil(s)` là où le run précédent, sur le même code, en écrivait
636. Les 40 artifacts AN et les 8 artifacts roster étaient là, non expirés.

## Pourquoi aucun garde-fou ne pouvait le voir

Ils mesurent tous la collecte **après** la fusion. Sans profil brut, le contrôle
de perte ne voit aucune perte (#460), celui de #511 n'a rien de
collecté-non-publié à signaler, et la §5b ne réclame d'entrée de correspondance
pour personne. Le run est vert **par absence** — le motif que #484 nomme déjà
ailleurs : *une panne rend le même vide qu'une absence*.

## Ce que ce module ajoute, et pourquoi lui seul le peut

Il est le seul endroit du run à connaître les **deux** termes de la comparaison :

- l'**inventaire** — ce que les jobs d'extraction ont effectivement publié,
  lisible par l'API du run ;
- le **disque** — ce qui est arrivé jusqu'ici.

Un artifact inventorié et absent du disque est une **panne** : on rattrape par
`gh run download`, qui n'emprunte pas le chemin de l'action, et on échoue si le
rattrapage échoue. Un artifact qu'aucun job n'a publié reste **silencieux**,
exactement comme avant : une source qui n'a rien produit n'est pas une panne, et
la faire échouer supprimerait le repli que #412 §2.1 a posé exprès.

## Les deux asymétries, et leur raison

**`parltrack-dumps` est rattrapé, jamais bloquant.** Son repli est déclaré, le
portail §5 le mesure, et `--enrich-parltrack` sait tourner sans lui. Bloquer
dessus ferait échouer un run pour une dégradation que le dépôt publie déjà.

**Un inventaire illisible n'échoue pas.** Si l'API refuse de répondre, ce module
ne sait pas ce que le run a publié — et « je ne peux pas vérifier » n'est pas
« il n'y a rien » (§2 règle 5, et le `indetermine` de #757). Il l'annonce et
rend la main. Ce que le run fait ensuite est ce qu'il faisait avant ce module :
ni pire, ni fabriqué.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence

#: Nombre de tentatives de rattrapage. Trois, parce que la limite qui a produit
#: #786 a duré moins de trois secondes : ce qu'on attend n'est pas une panne
#: durable, c'est une rafale.
TENTATIVES = 3

#: Attente entre deux tentatives, en secondes. La documentation GitHub demande
#: « a few minutes » sur une limite secondaire ; on ne les prend pas, parce que
#: le step tient dans un job à `timeout-minutes: 60` déjà chargé — on prend de
#: quoi laisser passer la rafale.
ATTENTES = (20, 60)


@dataclass(frozen=True)
class Source:
    """Une source d'extraction, du point de vue du transport.

    `prefixe` sert deux fois : à reconnaître les artifacts de cette source dans
    l'inventaire, et à les redemander. `shards` dit lequel des deux sens : un
    job shardé publie `prefixe` + une clé (#344, #394), un job unique publie
    `prefixe` tel quel.
    """

    libelle: str
    prefixe: str
    repertoire: str
    shards: bool
    bloquant: bool

    def reconnait(self, nom: str) -> bool:
        return nom.startswith(self.prefixe) if self.shards else nom == self.prefixe

    @property
    def motif(self) -> str:
        return f"{self.prefixe}*" if self.shards else self.prefixe


#: Les quatre téléchargements de `merge-and-pivot`, dans leur ordre du workflow.
#: `candidats-a-jour` n'y est pas : son absence a déjà un sens publié — le run
#: normalise le périmètre d'hier et le warning `CANDIDATS_ARTIFACT_ABSENT` le
#: dit (#757).
SOURCES: tuple[Source, ...] = (
    Source("AN", "raw-profiles-an-", "_artifacts/an", shards=True, bloquant=True),
    Source("UE", "raw-profiles-ue-officiel", "_artifacts/ue", shards=False, bloquant=True),
    Source("ParlTrack", "parltrack-dumps", ".cache/parltrack", shards=False, bloquant=False),
    Source(
        "roster",
        "raw-profiles-roster-groupes-",
        "_artifacts/roster",
        shards=True,
        bloquant=True,
    ),
)

Executeur = Callable[[Sequence[str]], subprocess.CompletedProcess]


def _executer(commande: Sequence[str]) -> subprocess.CompletedProcess:
    return subprocess.run(commande, capture_output=True, text=True, check=False)


def inventaire(
    depot: str, run_id: str, executeur: Executeur = _executer
) -> list[str] | None:
    """Les noms des artifacts que ce run a publiés, ou `None` si illisible.

    `None` n'est pas une liste vide, et c'est tout l'objet du type de retour :
    « l'API n'a pas répondu » et « le run n'a rien publié » mènent à deux
    conduites opposées, et les confondre est précisément le défaut qu'on corrige.
    """
    resultat = executeur(
        [
            "gh",
            "api",
            f"repos/{depot}/actions/runs/{run_id}/artifacts",
            "--paginate",
            "-q",
            ".artifacts[] | select(.expired == false) | .name",
        ]
    )
    if resultat.returncode != 0:
        return None
    return [ligne.strip() for ligne in resultat.stdout.splitlines() if ligne.strip()]


def fichiers(repertoire: str | Path) -> int:
    """Le nombre de fichiers arrivés, à n'importe quelle profondeur."""
    chemin = Path(repertoire)
    if not chemin.is_dir():
        return 0
    return sum(1 for f in chemin.rglob("*") if f.is_file())


def aplatir(source: str | Path, destination: str | Path) -> int:
    """Déplace tous les fichiers de `source` à plat dans `destination`.

    `gh run download` range chaque artifact dans son propre sous-répertoire là
    où l'action, elle, aplatit (`merge-multiple: true`). `merge_raw_dirs` lit à
    plat : sans ce recollement, un rattrapage réussi ne servirait à rien.
    """
    cible = Path(destination)
    cible.mkdir(parents=True, exist_ok=True)
    deplaces = 0
    for fichier in sorted(Path(source).rglob("*")):
        if fichier.is_file():
            shutil.move(str(fichier), str(cible / fichier.name))
            deplaces += 1
    return deplaces


def rattraper(
    source: Source,
    depot: str,
    run_id: str,
    executeur: Executeur = _executer,
    dormir: Callable[[float], None] | None = None,
) -> int:
    """Redemande les artifacts de `source` par `gh run download`. Rend le nombre
    de fichiers posés.

    Le chemin est volontairement autre que celui de l'action : `gh` passe par
    l'API REST du dépôt quand `download-artifact` interroge le service
    `results-receiver`, et c'est ce dernier qui a rendu le 403 de #786. Deux
    chemins pour une même donnée, c'est la seule redondance disponible ici.
    """
    if dormir is None:
        import time

        dormir = time.sleep
    for tentative in range(TENTATIVES):
        if tentative:
            dormir(ATTENTES[min(tentative - 1, len(ATTENTES) - 1)])
        with tempfile.TemporaryDirectory() as tampon:
            resultat = executeur(
                [
                    "gh",
                    "run",
                    "download",
                    run_id,
                    "--repo",
                    depot,
                    "--pattern" if source.shards else "--name",
                    source.motif,
                    "--dir",
                    tampon,
                ]
            )
            if resultat.returncode == 0:
                poses = aplatir(tampon, source.repertoire)
                if poses:
                    return poses
    return 0


def annoter(niveau: str, message: str) -> None:
    """Annotation GitHub sur stdout — ce module n'a pas de sortie machine."""
    print(f"::{niveau}::{message}")


def controler(
    sources: Iterable[Source],
    depot: str,
    run_id: str,
    executeur: Executeur = _executer,
    dormir: Callable[[float], None] | None = None,
) -> int:
    """Le contrôle complet. Rend le code de sortie du step.

    Trois issues par source, et elles sont nommées séparément parce qu'elles se
    ressemblent sur le disque et pas du tout dans les faits : rien de publié
    (silence), publié et arrivé (rien à dire), publié et non arrivé (panne).
    """
    noms = inventaire(depot, run_id, executeur)
    if noms is None:
        annoter(
            "warning",
            "TRANSPORT_INVENTAIRE_INDISPONIBLE — l'API du run n'a pas listé ses "
            "artifacts ; ce run ne peut pas distinguer une panne de transport "
            "d'une source vide, et ne l'invente pas (#786).",
        )
        return 0

    pannes: list[str] = []
    for source in sources:
        publies = [nom for nom in noms if source.reconnait(nom)]
        arrives = fichiers(source.repertoire)
        if not publies:
            print(f"  · {source.libelle} : aucun artifact publié par ce run.")
            continue
        if arrives:
            print(
                f"  ✓ {source.libelle} : {len(publies)} artifact(s) publié(s), "
                f"{arrives} fichier(s) dans {source.repertoire}."
            )
            continue
        annoter(
            "warning",
            f"TRANSPORT_ARTIFACTS_RATTRAPAGE — {source.libelle} : "
            f"{len(publies)} artifact(s) publié(s) et 0 fichier reçu. "
            "Nouvelle tentative par `gh run download` (#786).",
        )
        poses = rattraper(source, depot, run_id, executeur, dormir)
        if poses:
            print(f"  ✓ {source.libelle} : {poses} fichier(s) rattrapé(s).")
            continue
        message = (
            f"TRANSPORT_ARTIFACTS_PERDUS — {source.libelle} : "
            f"{len(publies)} artifact(s) publié(s) par ce run, aucun reçu après "
            f"{TENTATIVES} tentatives. La collecte a eu lieu et n'atteint pas la "
            "fusion (#786)."
        )
        if source.bloquant:
            annoter("error", message)
            pannes.append(source.libelle)
        else:
            annoter(
                "warning",
                message + " Source non bloquante : le repli déclaré s'applique.",
            )

    if pannes:
        annoter(
            "error",
            "TRANSPORT_ARTIFACTS_PERDUS — fusion abandonnée : "
            f"{', '.join(pannes)}. Committer 0 profil ferait passer une panne "
            "pour une absence, et le run suivant repartirait du même corpus.",
        )
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    depot = os.environ.get("GITHUB_REPOSITORY", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    if not depot or not run_id:
        annoter(
            "warning",
            "TRANSPORT_HORS_CI — GITHUB_REPOSITORY ou GITHUB_RUN_ID absent ; "
            "le contrôle de transport n'a rien à comparer.",
        )
        return 0
    print("Transport des artifacts d'extraction :")
    return controler(SOURCES, depot, run_id)


if __name__ == "__main__":
    sys.exit(main())
