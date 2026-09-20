"""Budget de temps mur pour une phase de collecte réseau (#498).

Pourquoi un budget INTERNE alors qu'un `timeout-minutes` existe déjà.
`timeout-minutes` borne le *job*, pas la collecte : il couvre aussi
`actions/checkout`, `setup-python`, `pip install`, la restauration des caches
et le téléchargement de l'artifact d'amendements. Mesuré sur les 32 shards
`extract-an` des runs 32233766814, 32288588518, 32302557156 et 32379928098,
ce préambule va de **30 s à 193 s** — soit, sur un timeout de 5 min, entre
107 s et 270 s réellement laissés à l'extraction, sans que rien ne le dise.
Un budget exprimé en secondes de collecte est stable là où le timeout de job
ne l'est pas.

Et surtout : un dépassement de `timeout-minutes` tue le process. GitHub
affiche `##[error]The operation was canceled`, qui ne dit ni combien avait été
collecté, ni où la collecte en était — et `generate_all_profiles.py` n'atteint
jamais son écriture de profil, donc le shard publie **zéro** profil (constaté
sur les 4 shards tués du run 32302557156 et les 8 du run 32379928098, vérifiés
un par un : « Publication : 0 profil(s) écrits par ce job »). Un budget interne, lui, rend
la main : ce qui est collecté est écrit, et ce qui ne l'est pas est déclaré
dans `meta.warnings[]` (règle éditoriale 2.5 — une collecte tronquée ne doit
jamais se lire comme une collecte complète).

Même famille que les watchdogs de `download_watchdog.py` (#370) et de
`candidate_profile._get_with_watchdog` (#340), à un étage au-dessus : ceux-là
bornent UNE requête, celui-ci borne l'agrégat d'une phase.

#514 — la phase bornée n'était pas la seule qui en avait besoin. Le budget
de #498 ne couvrait que les interventions, et `build_profile_any_chambre` le
rendait `None` dès `--skip-interventions`. Quand #502 a levé ce drapeau en dur
sur `extract-senat`, le job s'est retrouvé sans aucun budget : identité, votes
et dossiers n'en avaient jamais eu. Le 20/08/2026, run 32421439590, il a
consommé ses 15 minutes de `timeout-minutes` pour **un** profil écrit.

D'où trois portées, et non plus une :

- **par phase** (`libelle="collecte d'interventions"`, #498) — le temps ne
  court que dans les sections de cette phase ;
- **par candidat** (`libelle="collecte"`, #514) — toute la collecte réseau
  d'un candidat, partagée entre ses chambres ;
- **par process** (`libelle="collecte du job"`, #514) — la boucle de candidats
  entière, pour qu'une source à terre rende la main au lieu d'être coupée par
  `timeout-minutes` sans résumé ni annotation.

Elles s'emboîtent sans se connaître : ce sont trois instances distinctes, donc
trois compteurs distincts, et une seconde passée dans la collecte
d'interventions d'un candidat est facturée aux trois.
"""

from __future__ import annotations

import os
import sys
import threading
import time
from contextlib import ExitStack, contextmanager
from typing import Iterator, Optional


class BudgetCollecte:
    """Budget de temps mur consommé par les sections déclarées avec `section()`.

    Le temps ne court QUE dans une section : le budget d'une phase n'est pas
    entamé par le travail des autres phases du même profil (votes, amendements,
    textes portés), qui n'ont rien à voir avec lui.

    Les unités non collectées sont comptées par `ignorer()` et restituées par
    `message()` : un budget épuisé sans trace de ce qu'il a coûté serait
    exactement la valeur par défaut silencieuse que la règle 2.5 interdit.

    Thread-safe : `epuise()` et `ignorer()` sont appelés depuis le pool de
    threads qui récupère les détails d'intervention (`max_workers=4`).

    **`parent` (#514)** — chaîne un budget plus large au-dessus de celui-ci.
    Une section ouverte ici ouvre aussi celle du parent (donc le parent est
    facturé du temps de ses enfants), et `epuise()` est vrai dès qu'un budget
    de la chaîne l'est. C'est ce qui permet au budget par candidat de borner la
    collecte d'interventions **sans toucher une ligne** du code de #500 : tous
    ses `budget_epuise(...)`/`budget_ignorer(...)` existants voient
    l'épuisement du parent par la même méthode qu'avant.
    """

    def __init__(
        self,
        secondes: float,
        libelle: str = "collecte",
        parent: Optional["BudgetCollecte"] = None,
    ) -> None:
        if secondes <= 0:
            raise ValueError(
                f"budget de {libelle} invalide : {secondes} s. Un budget nul ou négatif "
                "n'est pas 'pas de budget' — passer None à l'appelant pour cela."
            )
        self.secondes = float(secondes)
        self.libelle = libelle
        self.parent = parent
        self._lock = threading.Lock()
        self._consomme = 0.0
        self._profondeur = 0
        self._debut_racine: Optional[float] = None
        self._ignores: dict[str, int] = {}

    # -- Consommation ------------------------------------------------------

    @contextmanager
    def section(self, nom: str) -> Iterator["BudgetCollecte"]:
        """Compte le temps mur passé dans le bloc. Réentrant : seule la section
        la plus externe compte, pour qu'une section imbriquée ne facture pas
        deux fois la même seconde."""
        _ = nom  # nom conservé pour la lisibilité des appels, pas pour le calcul
        with ExitStack() as pile:
            # Le parent est facturé du temps de ses enfants : sans cela, un
            # budget par candidat ne verrait jamais passer les secondes de la
            # collecte d'interventions, qui est précisément la phase la plus
            # chère qu'il doit borner.
            if self.parent is not None:
                pile.enter_context(self.parent.section(nom))
            with self._lock:
                if self._profondeur == 0:
                    self._debut_racine = time.monotonic()
                self._profondeur += 1
            try:
                yield self
            finally:
                with self._lock:
                    self._profondeur -= 1
                    if self._profondeur == 0 and self._debut_racine is not None:
                        self._consomme += time.monotonic() - self._debut_racine
                        self._debut_racine = None

    def _ecoule_sans_verrou(self) -> float:
        ecoule = self._consomme
        if self._profondeur > 0 and self._debut_racine is not None:
            ecoule += time.monotonic() - self._debut_racine
        return ecoule

    def consomme(self) -> float:
        """Secondes déjà consommées, section en cours incluse."""
        with self._lock:
            return self._ecoule_sans_verrou()

    def restant(self) -> float:
        """Secondes restantes, jamais négatif."""
        return max(0.0, self.secondes - self.consomme())

    def epuise(self) -> bool:
        """Vrai dès qu'UN budget de la chaîne est épuisé (#514).

        Un budget par candidat qui déborde arrête aussi la phase
        d'interventions qu'il englobe, sans que celle-ci ait à connaître son
        existence."""
        return self._responsable() is not None

    def _responsable(self) -> Optional["BudgetCollecte"]:
        """Le budget de la chaîne qui est effectivement épuisé, du plus interne
        au plus externe — ou None si aucun ne l'est. Sert à ce que le message
        de troncature nomme le bon plafond : dire « budget de collecte
        d'interventions épuisé (plafond 240 s) » alors que c'est le budget du
        job qui a rendu la main serait un chiffre juste sur la mauvaise
        population."""
        if self.consomme() >= self.secondes:
            return self
        if self.parent is not None:
            return self.parent._responsable()
        return None

    # -- Ce qui n'a pas été collecté ---------------------------------------

    def ignorer(self, unite: str, nombre: int = 1) -> None:
        """Enregistre `nombre` unités non collectées faute de budget."""
        if nombre <= 0:
            return
        with self._lock:
            self._ignores[unite] = self._ignores.get(unite, 0) + nombre

    def unites_ignorees(self) -> dict[str, int]:
        with self._lock:
            return dict(self._ignores)

    def message(self) -> Optional[str]:
        """Description de la troncature, ou None si rien n'a été ignoré.

        None quand le budget a suffi — y compris s'il a été frôlé : ce qui doit
        être signalé, c'est une collecte incomplète, pas un budget serré.
        """
        ignores = self.unites_ignorees()
        if not ignores:
            return None
        details = ", ".join(f"{nombre} {unite}" for unite, nombre in ignores.items())
        responsable = self._responsable() or self
        if responsable is self:
            cause = (
                f"budget de {self.libelle} épuisé après {self.consomme():.0f} s "
                f"(plafond {self.secondes:.0f} s)"
            )
        else:
            cause = (
                f"budget de {self.libelle} interrompu par le budget de "
                f"{responsable.libelle}, épuisé après {responsable.consomme():.0f} s "
                f"(plafond {responsable.secondes:.0f} s)"
            )
        return f"{cause} — non collecté : {details}"


def creer(
    secondes: Optional[float],
    libelle: str,
    parent: Optional[BudgetCollecte] = None,
) -> Optional[BudgetCollecte]:
    """`BudgetCollecte(secondes, libelle)`, ou `None` si `secondes` est nul/absent.

    **Un seul critère, et c'est tout l'objet de cette fonction : la valeur.**
    #514 est né d'une condition supplémentaire glissée à l'endroit de la
    création — `if budget_secondes and not skip_interventions` — qui a
    désactivé le budget sur un mode où il restait pourtant tout à borner.

    Une condition de mode se pose sur la **valeur passée**, à l'endroit qui
    décide du mode (le job, ou l'appelant qui connaît ses phases), jamais ici :
    `creer(0 if skip else 240, ...)` se lit et se teste ; un `and not` enfoui
    dans la fabrique rend un `None` que plus rien en aval ne distingue d'un
    « aucun budget demandé ».

    `None` en sortie ne veut pas dire « plus aucun plafond » : c'est à
    l'appelant de retomber sur le budget englobant (voir
    `build_profile`, `budget_phase_interventions`). Rendre `parent` ici ferait
    porter au budget du dessus le *libellé* de la phase absente, et une
    troncature nommerait alors le mauvais plafond.
    """
    if not secondes:
        return None
    return BudgetCollecte(secondes, libelle=libelle, parent=parent)


# -- Helpers tolérants au budget absent ------------------------------------
# Un budget optionnel truffe sinon les appelants de `if budget is not None`,
# et c'est exactement le genre de garde qu'on oublie sur un chemin.


@contextmanager
def section(budget: Optional[BudgetCollecte], nom: str) -> Iterator[Optional[BudgetCollecte]]:
    """`budget.section(nom)`, ou un no-op si `budget` est None."""
    if budget is None:
        yield None
        return
    with budget.section(nom):
        yield budget


def epuise(budget: Optional[BudgetCollecte]) -> bool:
    """False si `budget` est None : pas de budget = pas d'épuisement."""
    return budget is not None and budget.epuise()


def ignorer(budget: Optional[BudgetCollecte], unite: str, nombre: int = 1) -> None:
    if budget is not None:
        budget.ignorer(unite, nombre)


def annoncer_troncature(budget: Optional[BudgetCollecte], contexte: str) -> Optional[str]:
    """Imprime la troncature (stderr + annotation GHA) et renvoie son message.

    Renvoie None si rien n'a été tronqué — l'appelant n'a alors aucun
    avertissement à consigner.
    """
    if budget is None:
        return None
    message = budget.message()
    if message is None:
        return None
    print(f"  [!] {contexte} : {message}", file=sys.stderr)
    if os.getenv("GITHUB_ACTIONS") == "true":
        propre = message.replace("\n", " ").replace("\r", "")
        print(f"::warning::{contexte} : {propre}", flush=True)
    return message
