"""Garde-fou #568 : la vérification d'archivage doit rendre vrai, et surtout
rendre le BON état — sans jamais joindre Software Heritage depuis la CI.

`src/verifier_archivage_swh.py` est le seul outil qui autorise la coupure
d'historique de #434/#551 : il répond « les SHA cités survivront-ils ? ». Deux
façons de se tromper coûtent cher et se ressemblent :

  - **rendre `absente` pour un SHA qu'on n'a pas pu interroger** (quota, réseau)
    ferait renoncer à une coupure légitime, ou pire, ferait relancer un
    archivage complet pour rien ;
  - **rendre `absente` pendant une visite en cours** ferait croire à un échec
    d'archivage là où l'ingestion n'est pas finie — et le contraire,
    **conclure sur une visite non `full`**, autoriserait une coupure sur une
    archive incomplète.

D'où des tests qui portent sur le VERDICT, pas seulement sur le code.

#575 y ajoute **deux façons de rendre un verdict confiant sur la mauvaise
chose**, l'une et l'autre trouvées en lançant le script pour de vrai le
28/08/2026 :

  - **le périmètre ignorait la coupure** — il vérifiait toute la population
    citée alors que la population à RISQUE est celle des ancêtres du point de
    coupure. Sur le banc de #569, fenêtre 5 : 38 SHA cités, 28 perdus et 10
    conservés, et un blocage sur un des 10 conservés ;
  - **l'origine était codée en dur** — lancé sur un banc, il interrogeait
    l'archive du dépôt réel sans le signaler.

**Aucun de ces tests ne sort sur le réseau** (AGENTS.md §3, et #551 : « aucune
mesure lourde en CI, la vérification d'archivage est un geste de pré-coupure,
pas un contrôle de run »). Toutes les dépendances externes du script — git,
`gh`, le disque, HTTP — sont injectables, et c'est précisément ce qui rend ce
fichier possible. La fixture `_reseau_coupe` de `conftest.py` reste le filet :
un appel réel échouerait bruyamment.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import verifier_archivage_swh as v  # noqa: E402
from audit_volumetrie_profils import MOTIF_COMMIT_DONNEES  # noqa: E402

SCRIPT_BORNAGE = RACINE / "scripts" / "borner_historique_donnees.sh"

# Des SHA de 40 caractères fabriqués, pour que rien ici ne dépende de
# l'historique réel du dépôt : la suite doit rester verte après la coupure
# qu'elle protège.
SHA_A = "a" * 40
SHA_B = "b" * 40


# ── Extraction ───────────────────────────────────────────────────────────────


def test_extraction_prend_sept_caracteres_au_minimum():
    """7 est la longueur d'abrégé que git rend par défaut, et celle des
    citations du dépôt. En dessous, on ratisserait les mots courants."""
    assert v.extraire_chaines("voir deb28a7 pour le détail") == ["deb28a7"]
    assert v.extraire_chaines("le champ abcdef reste vide") == []


def test_extraction_ignore_les_fragments_d_un_mot_plus_long():
    """Sans les gardes lookbehind/lookahead, une chaîne de 41 caractères
    rendrait ses 40 premiers et `deadbeefcafe` sortirait de `xdeadbeefcafe` —
    des SHA inventés qui ne résoudraient jamais et pollueraient le rapport."""
    assert v.extraire_chaines("xdeadbeefcafe") == []
    assert v.extraire_chaines("deadbeefcafez") == []
    assert v.extraire_chaines("a" * 41) == []


def test_extraction_attrape_un_sha_dans_une_url():
    """Une citation dans une URL d'archive est une citation : c'est même la
    forme que prend une vérification par un tiers."""
    url = "https://archive.softwareheritage.org/api/1/revision/deb28a7/"
    assert v.extraire_chaines(url) == ["deb28a7"]


def test_extraction_normalise_la_casse():
    assert v.extraire_chaines("DEB28A7") == []  # majuscules : pas un SHA git
    assert v.extraire_chaines("`deb28a7`") == ["deb28a7"]


def test_les_lieux_md_portent_le_numero_de_ligne():
    """« cité dans docs/technical_decisions.md » envoie chercher dans 2 000
    lignes ; « docs/technical_decisions.md:412 » s'ouvre."""
    fichiers = {"docs/x.md": "rien\nmesuré sur deb28a7\n"}
    citations = v.citations_des_fichiers_md(
        "/racine", lambda p: fichiers[p.removeprefix("/racine/")], fichiers
    )
    assert [(c.chaine, c.lieu) for c in citations] == [("deb28a7", "docs/x.md:2")]


def test_un_fichier_illisible_ne_stoppe_pas_le_balayage():
    """Un fichier suivi mais absent du disque ne doit pas faire renoncer à
    toute la vérification : c'est le genre d'échec qui pousse à sauter
    l'étape."""

    def lire(chemin):
        if chemin.endswith("absent.md"):
            raise OSError("pas là")
        return "voir deb28a7"

    citations = v.citations_des_fichiers_md(
        "/r", lire, ["absent.md", "present.md"]
    )
    assert [c.lieu for c in citations] == ["present.md:1"]


def test_les_lieux_d_issue_portent_le_numero():
    citations = v.citations_des_issues(
        [{"number": 429, "body": "mesuré sur deb28a7"}, {"number": 430, "body": None}]
    )
    assert [(c.chaine, c.lieu) for c in citations] == [("deb28a7", "#429")]


# ── Résolution ───────────────────────────────────────────────────────────────


def test_seuls_les_commits_sont_retenus_et_la_population_est_nommee():
    """Le chiffre qui compte est un rapport, pas un total : « 42 SHA cités sur
    124 chaînes extraites ». Un blob, un tree ou un nombre décimal fait de
    chiffres hexadécimaux passent l'extraction et doivent tomber ici."""
    citations = [
        v.Citation("aaaaaaa", "docs/a.md:1"),
        v.Citation("bbbbbbb", "#12"),
        v.Citation("1787931", "docs/a.md:9"),  # un horodatage, pas un commit
    ]
    commits, nb_chaines = v.resoudre_commits(
        citations,
        lambda chaines: {"aaaaaaa": SHA_A, "bbbbbbb": None, "1787931": None},
    )
    assert nb_chaines == 3
    assert [c.sha for c in commits] == [SHA_A]


def test_une_forme_abregee_et_une_forme_complete_fusionnent():
    """Sinon le même commit serait compté deux fois, et la moitié de ses lieux
    de citation disparaîtrait du rapport de manque."""
    citations = [
        v.Citation("aaaaaaa", "docs/a.md:1"),
        v.Citation(SHA_A, "#12"),
        v.Citation("aaaaaaa", "docs/a.md:1"),  # doublon exact
    ]
    commits, nb_chaines = v.resoudre_commits(
        citations, lambda chaines: {c: SHA_A for c in chaines}
    )
    assert nb_chaines == 2
    assert len(commits) == 1
    assert commits[0].lieux == ["docs/a.md:1", "#12"]


def test_le_rapport_est_ordonne_du_plus_ancien_au_plus_recent():
    """L'ordre dans lequel une coupure les emporte."""
    citations = [v.Citation(SHA_A, "a"), v.Citation(SHA_B, "b")]
    commits, _ = v.resoudre_commits(
        citations,
        lambda chaines: {SHA_A: SHA_A, SHA_B: SHA_B},
        dater=lambda shas: {SHA_A: "2026-08-28", SHA_B: "2026-08-12"},
    )
    assert [c.sha for c in commits] == [SHA_B, SHA_A]


# ── Interrogation de l'API, sans réseau ──────────────────────────────────────


def _quota_neuf():
    return v.Quota()


def test_200_donne_presente_et_404_donne_absente():
    quota = _quota_neuf()
    assert v.interroger_revision(
        SHA_A, lambda url: v.Reponse(200, {}), quota
    )[0] == "presente"
    assert v.interroger_revision(
        SHA_A, lambda url: v.Reponse(404, {}), quota
    )[0] == "absente"


def test_une_panne_reseau_ne_devient_jamais_absente():
    """LA confusion à ne pas faire : ne pas trouver et ne pas avoir regardé
    sont deux choses différentes. La première fait relancer un archivage, la
    seconde fait réessayer."""

    def fetch(url):
        raise ConnectionError("DNS")

    etat, detail = v.interroger_revision(SHA_A, fetch, _quota_neuf())
    assert etat == "indetermine"
    assert "ConnectionError" in detail


def test_un_429_temporise_puis_reessaie_et_le_dit():
    """La limite anonyme est de 120 requêtes/heure. Échouer en silence dessus
    rendrait « absent » un SHA parfaitement archivé."""
    reponses = [
        v.Reponse(429, None, {"X-RateLimit-Reset": "1000", "X-RateLimit-Limit": "120"}),
        v.Reponse(200, {}),
    ]
    dodos, dits = [], []
    etat, _ = v.interroger_revision(
        SHA_A,
        lambda url: reponses.pop(0),
        _quota_neuf(),
        dormir=dodos.append,
        horloge=lambda: 990.0,
        journal=dits.append,
    )
    assert etat == "presente"
    assert dodos == [11.0], "attente mal calculée (reset + 1 s de marge)"
    assert any("attente" in m for m in dits), "temporisation silencieuse"


def test_un_429_persistant_rend_indetermine_jamais_absente():
    etat, detail = v.interroger_revision(
        SHA_A,
        lambda url: v.Reponse(429, None, {"X-RateLimit-Reset": "10"}),
        _quota_neuf(),
        dormir=lambda s: None,
        horloge=lambda: 0.0,
        journal=lambda m: None,
    )
    assert etat == "indetermine"
    assert "429" in detail


def test_l_attente_est_bornee_plutot_que_de_veiller_une_heure():
    """Un lancement de pré-coupure ne doit pas pouvoir se transformer en veille
    silencieuse : au-delà de `--attente-max`, on rend INDÉTERMINÉ."""
    dodos = []
    etat, detail = v.interroger_revision(
        SHA_A,
        lambda url: v.Reponse(429, None, {"X-RateLimit-Reset": "3600"}),
        _quota_neuf(),
        dormir=dodos.append,
        horloge=lambda: 0.0,
        attente_max=60.0,
        journal=lambda m: None,
    )
    assert etat == "indetermine"
    assert dodos == [], "a dormi malgré le plafond d'attente"
    assert "attente-max" in detail or "quota" in detail


def test_le_quota_est_lu_dans_les_entetes_pas_compte_localement():
    """Un compteur local se désynchronise dès qu'un autre outil consomme le
    même quota depuis la même IP — ce qui arrive exactement le jour où l'on
    vérifie à la main en parallèle."""
    quota = _quota_neuf()
    quota.lire({"x-ratelimit-limit": "120", "X-RateLimit-Remaining": "67"})
    assert (quota.limite, quota.restant) == (120, 67)
    quota.lire({"X-RateLimit-Remaining": "pas un nombre"})
    assert quota.restant == 67, "une valeur illisible a écrasé la précédente"


def test_un_seau_vide_declenche_une_attente_preventive_annoncee():
    """Aller chercher le 429 quand la réponse précédente annonçait un seau vide
    gaspille une requête et une minute."""
    quota = v.Quota(limite=120, restant=0, reset=1000)
    dodos, dits = [], []
    etat, _ = v.interroger_revision(
        SHA_A,
        lambda url: v.Reponse(200, {}),
        quota,
        dormir=dodos.append,
        horloge=lambda: 995.0,
        journal=dits.append,
    )
    assert etat == "presente"
    assert dodos == [6.0]
    assert any("quota épuisé" in m for m in dits)


def test_le_seau_de_la_route_visite_ne_contamine_pas_celui_des_revisions():
    """Mesuré le 28/08/2026 : `/origin/.../visit/latest/` annonce 700
    requêtes/heure, `/revision/` en annonce 120. Recopier le premier ferait
    croire au script qu'il a six fois plus de marge qu'en réalité, et la
    temporisation n'arriverait qu'après un `429`."""
    quota = _quota_neuf()
    v.interroger_visite(
        "https://exemple/x",
        lambda url: v.Reponse(
            200,
            {"status": "full", "snapshot": "x", "visit": 1},
            {"X-RateLimit-Limit": "700", "X-RateLimit-Remaining": "699"},
        ),
        quota,
    )
    assert quota.requetes == 1, "la requête n'est pas comptée"
    assert quota.limite is None and quota.restant is None


def test_un_restant_perime_ne_declenche_pas_d_attente():
    """Observé en conditions réelles le 28/08/2026 : vingt « quota épuisé —
    attente de 1 s » d'affilée après un reset, chacun suivi d'une requête qui
    passait très bien.

    `restant` est une photographie de la réponse précédente ; passé
    l'horodatage `reset`, elle est périmée et la seule façon de connaître le
    nouveau compte est d'émettre une requête. Un garde-fou qui crie sans raison
    finit par n'être plus lu — et ce bavardage masquait les deux VRAIES
    temporisations de la même exécution (702 s et 1 504 s)."""
    quota = v.Quota(limite=120, restant=0, reset=1000)
    dodos, dits = [], []
    etat, _ = v.interroger_revision(
        SHA_A,
        lambda url: v.Reponse(200, {}),
        quota,
        dormir=dodos.append,
        horloge=lambda: 1500.0,  # le reset est PASSÉ
        journal=dits.append,
    )
    assert etat == "presente"
    assert dodos == [], "a dormi sur un compteur périmé"
    assert dits == [], "a crié « quota épuisé » sans raison"


def test_le_seau_vide_avant_son_reset_fait_bien_attendre():
    """Le pendant du test précédent : tant que le reset est à venir, le compteur
    est valide et l'attente est la bonne réponse. Sans les deux, la correction
    du bavardage supprimerait la temporisation elle-même."""
    assert v._seau_vide(v.Quota(restant=0, reset=1000), 900.0) is True
    assert v._seau_vide(v.Quota(restant=0, reset=1000), 1100.0) is False
    assert v._seau_vide(v.Quota(restant=5, reset=1000), 900.0) is False
    assert v._seau_vide(v.Quota(restant=None), 900.0) is False


def test_la_visite_est_lue_sans_confondre_inconnue_et_non_full():
    visite = v.interroger_visite(
        "https://exemple/x",
        lambda url: v.Reponse(200, {"status": "partial", "snapshot": None, "visit": 1}),
        _quota_neuf(),
    )
    assert visite["connue"] is True and visite["statut"] == "partial"

    inconnue = v.interroger_visite(
        "https://exemple/x", lambda url: v.Reponse(404, {}), _quota_neuf()
    )
    assert inconnue["connue"] is False


# ── Le verdict : la partie qui décide ────────────────────────────────────────

VISITE_FULL = {"connue": True, "statut": "full", "snapshot": "6ad9782", "visite": 1}
VISITE_EN_COURS = {"connue": True, "statut": "ongoing", "snapshot": None, "visite": 2}


def _commit(sha, etat, atteignable=None):
    return v.CommitCite(sha=sha, lieux=["#429"], etat=etat, atteignable=atteignable)


def test_visite_full_et_tout_resout_autorise_la_coupure():
    code, message = v.rendre_verdict(VISITE_FULL, [_commit(SHA_A, "presente")])
    assert code == v.VERIFIE
    assert "rituel" in message


def test_visite_full_et_sha_atteignable_absent_bloque():
    code, message = v.rendre_verdict(
        VISITE_FULL, [_commit(SHA_A, "presente"), _commit(SHA_B, "absente", True)]
    )
    assert code == v.MANQUANTS
    assert "NE PAS COUPER" in message


def test_visite_non_full_et_sha_absent_est_indetermine_pas_un_manque():
    """L'exigence explicite de #568 : une visite en cours n'est pas un échec
    d'archivage. Les confondre ferait renoncer à une coupure légitime — ou
    l'autoriser à tort."""
    code, message = v.rendre_verdict(
        VISITE_EN_COURS, [_commit(SHA_A, "absente", True)]
    )
    assert code == v.INDETERMINE
    assert "ingestion" in message and "NE PAS COUPER" in message


def test_visite_non_full_mais_tout_resout_reste_verifie():
    """Si tous les SHA cités résolvent déjà, la condition de l'étape 2b est
    remplie, que l'ingestion soit finie ou non : ce qu'on protège, ce sont les
    citations, pas la complétude du snapshot."""
    code, message = v.rendre_verdict(VISITE_EN_COURS, [_commit(SHA_A, "presente")])
    assert code == v.VERIFIE
    assert "ongoing" in message


def test_un_seul_indetermine_suffit_a_ne_pas_conclure():
    code, _ = v.rendre_verdict(
        VISITE_FULL, [_commit(SHA_A, "presente"), _commit(SHA_B, "indetermine")]
    )
    assert code == v.INDETERMINE


def test_une_citation_orpheline_est_signalee_sans_bloquer():
    """Un commit atteignable depuis aucune ref vient d'une branche de PR
    récrite : l'origine ne l'a jamais servi, Software Heritage n'a jamais pu le
    voir, et relancer l'archivage n'y changera rien. Il est déjà irrésolvable
    pour un tiers, donc la coupure ne lui fait rien perdre — le bloquer
    rendrait le garde-fou rouge en permanence, et un rouge permanent n'est plus
    lu.

    Ce n'est pas une hypothèse : `efed279`, cité dans
    `docs/technical_decisions.md`, est dans ce cas au 28/08/2026."""
    orpheline = _commit(SHA_B, "absente", atteignable=False)
    code, message = v.rendre_verdict(
        VISITE_FULL, [_commit(SHA_A, "presente"), orpheline]
    )
    assert orpheline.orpheline is True
    assert code == v.VERIFIE
    assert "orpheline" in message


def test_la_recherche_de_ref_ignore_ce_que_l_origine_ne_sert_pas():
    """« Atteignable » veut dire « atteignable depuis une ref que l'origine
    offre à un archiveur », pas « présent dans ce clone ».

    `refs/pull/<n>/head` en est exclue : GitHub la sert, Software Heritage ne
    l'archive pas. `refs/claude/*` et `refs/stash` aussi : elles n'existent que
    localement, et les compter ferait passer pour un trou d'archive un commit
    que l'origine n'a jamais porté — donc bloquer à tort une coupure légitime.
    """
    familles = v.FAMILLES_DE_REFS_DE_L_ORIGINE
    assert "refs/heads" in familles
    assert "refs/remotes/origin" in familles
    assert not [f for f in familles if f.startswith("refs/pull")]
    assert not [f for f in familles if "claude" in f or "stash" in f]


def test_une_population_vide_ne_vaut_pas_un_succes():
    """Si l'extraction rend zéro SHA, il n'y a rien à conclure — et surtout pas
    « tout va bien ». C'est le mode de panne d'une expression régulière cassée."""
    code, _ = v.rendre_verdict(VISITE_FULL, [])
    assert code == v.INDETERMINE


# ── Bout en bout, entièrement simulé ─────────────────────────────────────────


def _verifier_simule(reponses_par_sha, visite_corps, urls=None, **kwargs):
    """`urls` recueille les URL effectivement demandées : c'est la seule façon
    de voir QUELLE origine a été interrogée et COMBIEN de SHA l'ont été."""
    md = {"docs/journal.md": f"mesuré sur {SHA_A[:7]}\nvoir aussi {SHA_B[:7]}\n"}

    def fetch(url):
        if urls is not None:
            urls.append(url)
        if "/visit/latest/" in url:
            return v.Reponse(200, visite_corps)
        sha = url.rstrip("/").rsplit("/", 1)[-1]
        return v.Reponse(reponses_par_sha[sha], {})

    # Sans remote injecté, `verifier()` irait interroger le dépôt réel par
    # `git remote get-url origin` : le test dépendrait de la machine.
    kwargs.setdefault("remote", lambda: None)
    return v.verifier(
        "/r",
        fetch=fetch,
        lire=lambda p: md[p.removeprefix("/r/")],
        lister_md=lambda: list(md),
        lister_issues=lambda: [{"number": 429, "body": f"régression à {SHA_B[:7]}"}],
        batch_check=lambda chaines: {
            SHA_A[:7]: SHA_A, SHA_B[:7]: SHA_B,
        },
        dater=lambda shas: {SHA_A: "2026-08-12T00:00:00+02:00",
                            SHA_B: "2026-08-20T00:00:00+02:00"},
        journal=lambda m: None,
        **kwargs,
    )


def test_bout_en_bout_nomme_le_manquant_et_ou_il_est_cite():
    """La demande centrale de #568 : « 3 manquants » n'aide personne ;
    « `deb28a7`, cité dans #429, ne résout pas » se traite."""
    code, donnees, texte = _verifier_simule(
        {SHA_A: 200, SHA_B: 404},
        {"status": "full", "snapshot": "6ad9782", "visit": 1},
        ref_contenant=lambda sha: "refs/heads/main",
    )
    assert code == v.MANQUANTS
    assert SHA_B[:7] in texte
    assert "#429" in texte and "docs/journal.md:2" in texte
    assert SHA_A[:7] not in texte, "un SHA présent n'a pas à encombrer le rapport"
    assert donnees["population"]["sha_resolus_en_commit"] == 2


def test_bout_en_bout_nomme_la_population_de_chaque_chiffre():
    """Un total sans population est ininterprétable — c'est l'erreur que ce
    dépôt corrige le plus souvent."""
    _, donnees, texte = _verifier_simule(
        {SHA_A: 200, SHA_B: 200}, {"status": "full", "snapshot": "x", "visit": 1}
    )
    assert "chaînes hexadécimales extraites" in texte
    assert "fichier .md suivi" in texte and "corps d'issue" in texte
    assert "commentaires d'issues EXCLUS" in texte, (
        "la réserve de périmètre doit être dans la sortie, pas seulement dans "
        "le code : c'est la sortie qu'on lit avant de couper"
    )
    assert donnees["population"] == {
        "chaines_extraites": 2,
        "fichiers_md": 1,
        "issues": 1,
        "sha_resolus_en_commit": 2,
        # #575 : la population à RISQUE se compte à part de la population
        # citée. Sans coupure demandée, les deux coïncident — et c'est
        # justement ce que la sortie doit dire au lieu de le laisser croire.
        "sha_sous_la_coupure": 2,
        "sha_conserves_par_la_coupure": 0,
    }


def test_bout_en_bout_le_quota_apparait_dans_la_sortie():
    _, _, texte = _verifier_simule(
        {SHA_A: 200, SHA_B: 200}, {"status": "full", "snapshot": "x", "visit": 1}
    )
    assert "quota" in texte and "3 requêtes émises" in texte


def test_gh_indisponible_degrade_le_perimetre_sans_echouer():
    """`gh` absent ou non authentifié ne doit pas faire échouer la
    vérification : un demi-périmètre annoncé vaut mieux qu'un échec qui pousse
    à sauter l'étape juste avant une opération irréversible."""

    def lister_issues():
        raise FileNotFoundError("gh")

    code, donnees, _ = v.verifier(
        "/r",
        fetch=lambda url: v.Reponse(200, {"status": "full", "snapshot": "x", "visit": 1}),
        lire=lambda p: f"mesuré sur {SHA_A[:7]}",
        lister_md=lambda: ["docs/journal.md"],
        lister_issues=lister_issues,
        batch_check=lambda chaines: {SHA_A[:7]: SHA_A},
        dater=lambda shas: {},
        journal=lambda m: None,
    )
    assert code == v.VERIFIE
    assert donnees["population"]["issues"] == 0


# ── Branchement dans la procédure de bornage ─────────────────────────────────


def test_l_etape_2b_appelle_le_script_et_non_une_boucle_curl():
    """#568 : « la vérification est un geste manuel décrit en prose […] elle
    sera faite sous pression, juste avant une opération irréversible ». Une
    boucle `curl` à recopier n'est pas une commande à lancer.

    La boucle remplacée itérait de surcroît sur `git log --format=%H`, soit
    tout l'historique — 677 commits pour un quota de 120 requêtes/heure."""
    texte = SCRIPT_BORNAGE.read_text(encoding="utf-8")
    assert "verifier_archivage_swh.py" in texte, "étape 2b non branchée"
    assert "|| echo \"MANQUANT" not in texte, "boucle curl en prose toujours là"
    assert "for sha in $(git log --format=%H)" not in texte


def test_le_script_de_bornage_n_execute_pas_la_verification():
    """L'étape 2b vit dans le `cat <<FIN` d'instructions, jamais dans le code.

    Deux raisons. `--preparer` s'exécute AVANT que « Save Code Now » soit
    déclenché (étape 2a) : appelée là, la vérification échouerait toujours. Et
    faire sortir sur le réseau un script dont la garantie centrale est de ne
    rien pousser élargirait sa surface sans rien prouver."""
    lignes_de_code, dans_heredoc = [], False
    for ligne in SCRIPT_BORNAGE.read_text(encoding="utf-8").split("\n"):
        if dans_heredoc:
            dans_heredoc = ligne.strip() != "FIN"
            continue
        if "<<FIN" in ligne:
            dans_heredoc = True
            continue
        if not ligne.lstrip().startswith("#"):
            lignes_de_code.append(ligne)
    code = "\n".join(lignes_de_code)
    assert "verifier_archivage_swh" not in code, (
        "la vérification est exécutée par le script de bornage : elle doit "
        "rester une commande que l'humaine lance après l'archivage"
    )
    assert "curl" not in code, "le script de bornage sort sur le réseau"


def test_aucun_workflow_n_appelle_la_verification():
    """#551 a tranché : aucune mesure lourde en CI, et la vérification
    d'archivage est un geste de pré-coupure, pas un contrôle de run. La brancher
    dans un workflow consommerait le quota anonyme partagé de 120 requêtes/heure
    à chaque push, et ferait échouer des jobs sur l'état d'un service tiers."""
    for workflow in (RACINE / ".github" / "workflows").glob("*.yml"):
        assert "verifier_archivage_swh" not in workflow.read_text(encoding="utf-8"), (
            f"{workflow.name} invoque la vérification d'archivage"
        )


def test_le_script_ne_sort_sur_le_reseau_qu_en_un_seul_point():
    """Tout le reste est injectable — c'est ce qui rend ce fichier de tests
    possible sans jamais joindre l'API. Si un second `requests` apparaissait
    ailleurs, la suite pourrait se mettre à sortir sans qu'on le voie."""
    source = (RACINE / "src" / "verifier_archivage_swh.py").read_text(encoding="utf-8")
    imports = re.findall(r"^\s*(?:import|from) +requests\b.*$", source, re.MULTILINE)
    assert len(imports) == 1, f"import de requests attendu une fois : {imports}"
    # Et il doit être DANS `_fetch_reel`, pas au sommet du module : un import
    # de module rendrait l'unique point de sortie moins évident à retrouver.
    assert imports[0].startswith("    "), "requests importé au niveau du module"
    avant_fetch = source.split("def _fetch_reel")[0]
    assert "requests" not in avant_fetch.split("BASE_SWH")[-1]


@pytest.mark.parametrize("option", ["--sans-issues", "--attente-max", "--json"])
def test_les_options_citees_dans_l_etape_2b_existent(option):
    """L'étape 2b nomme `--sans-issues` et `--json` ; l'en-tête nomme
    `--attente-max`. Une option citée dans une procédure irréversible et
    absente du script ferait perdre le seul lancement disponible avant la
    coupure — et on ne le découvrirait qu'à ce moment-là."""
    aide = v.construire_parseur().format_help()
    assert option in aide, f"{option} annoncée mais absente du script"


def test_les_defauts_du_parseur_ne_font_rien_d_irreversible():
    """Un lancement sans argument lit et interroge ; il n'écrit nulle part.

    Et depuis #575, il ne PRÉSUPPOSE plus rien : ni l'origine — dérivée du
    remote, pas du code — ni le point de coupure, dont l'absence fait un audit
    d'archive et non un feu vert de coupure."""
    defauts = vars(v.construire_parseur().parse_args([]))
    assert defauts["json_out"] is None
    assert defauts["sans_issues"] is False
    assert defauts["origine"] is None, (
        "l'origine par défaut est de nouveau codée en dur : un banc, un fork "
        "ou un miroir obtiendrait un verdict qui ne parle pas de lui"
    )
    assert defauts["fenetre"] is None and defauts["coupure"] is None


# ── #575 · L'origine : celle du dépôt, pas celle du code ─────────────────────

BANC = "https://github.com/stephieED/test_procedure_bornage_issue_569"


@pytest.mark.parametrize(
    "ecriture",
    [
        "https://github.com/stephieED/Empreinte-politique-src",
        "https://github.com/stephieED/Empreinte-politique-src/",
        "https://github.com/stephieED/Empreinte-politique-src.git",
        "git@github.com:stephieED/Empreinte-politique-src.git",
        "git@github.com:stephieED/Empreinte-politique-src",
        "ssh://git@github.com/stephieED/Empreinte-politique-src.git",
        "https://stephieED@github.com/stephieED/Empreinte-politique-src.git",
        "  https://GitHub.com/stephieED/Empreinte-politique-src.git \n",
    ],
)
def test_les_ecritures_d_une_meme_origine_se_normalisent(ecriture):
    """Software Heritage indexe une origine PAR SON URL : ces huit écritures
    désignent le même dépôt pour l'archive, et huit dépôts différents pour une
    comparaison de chaînes.

    Sans cette normalisation, dériver l'origine du remote DÉPLACERAIT le défaut
    de #575 : un clone en SSH interrogerait une origine que l'archive ne
    connaît pas et rendrait « origine inconnue » sur un dépôt parfaitement
    archivé — un INDÉTERMINÉ permanent, à la place d'un VÉRIFIÉ trompeur."""
    assert (
        v.normaliser_origine(ecriture)
        == "https://github.com/stephieED/Empreinte-politique-src"
    )


def test_deux_origines_differentes_ne_se_confondent_pas():
    """Le pendant du test précédent : normaliser ne doit pas aplatir. Sans
    lui, « tout ramener à la même chaîne » passerait le test d'au-dessus."""
    assert v.normaliser_origine(BANC) != v.normaliser_origine(v.ORIGINE_PAR_DEFAUT)
    assert v.normaliser_origine("git@gitlab.com:o/r.git") == "https://gitlab.com/o/r"
    assert v.normaliser_origine("") is None and v.normaliser_origine(None) is None


def test_l_origine_est_derivee_du_remote_et_non_du_code():
    """LE défaut. Le 28/08/2026, lancé sur `test_procedure_bornage_issue_569`,
    le script a interrogé l'archive du dépôt RÉEL et rendu un « VÉRIFIÉ » qui
    ne parlait pas du banc."""
    origine, provenance = v.resoudre_origine(None, lambda: f"{BANC}.git")
    assert origine == BANC
    assert "remote" in provenance


def test_le_repli_sur_l_origine_codee_en_dur_est_annonce():
    """Le repli reste légitime — un dépôt sans remote existe. Ce qui ne l'est
    pas, c'est qu'il soit silencieux : c'est le silence qui a rendu le verdict
    du 28/08 inexploitable, pas la valeur."""
    origine, provenance = v.resoudre_origine(None, lambda: None)
    assert origine == v.ORIGINE_PAR_DEFAUT
    assert "REPLI" in provenance


def test_l_origine_explicite_l_emporte_et_est_normalisee_elle_aussi():
    origine, provenance = v.resoudre_origine(
        "git@github.com:autre/depot.git", lambda: f"{BANC}.git"
    )
    assert origine == "https://github.com/autre/depot"
    assert "--origine" in provenance


def test_l_origine_interrogee_et_sa_provenance_figurent_dans_la_sortie():
    """« Elle y est déjà — mais elle affichait celle du code, pas celle du
    dépôt, et personne ne pouvait le voir » (#575).

    Le test porte donc sur l'URL RÉELLEMENT demandée, pas sur ce que le rapport
    affirme : c'est l'écart entre les deux qui a coûté la journée du 28/08."""
    urls = []
    _, donnees, texte = _verifier_simule(
        {SHA_A: 200, SHA_B: 200},
        {"status": "full", "snapshot": "x", "visit": 1},
        urls=urls,
        remote=lambda: f"{BANC}.git",
    )
    visites = [u for u in urls if "/visit/latest/" in u]
    assert visites and BANC in visites[0], (
        "l'origine interrogée n'est pas celle du dépôt sous la main"
    )
    assert v.ORIGINE_PAR_DEFAUT not in visites[0]
    assert BANC in texte and "remote" in texte
    assert donnees["origine"] == BANC
    assert "remote" in donnees["origine_provenance"]


# ── #575 · Le périmètre suit la coupure ──────────────────────────────────────


def _coupure_simulee(ancetres):
    """Une coupure fabriquée, et l'oracle d'ascendance qui va avec.

    `ancetres` est l'ensemble des SHA que la coupure emporterait — c'est très
    exactement ce que `git merge-base --is-ancestor` répond sur un vrai dépôt,
    et `test_le_perimetre_de_coupure_est_celui_de_git` vérifie qu'il répond
    bien ça.
    """
    return {
        "commit_coupure": "de23b62",
        "resoudre_ref": lambda ref: "c" * 40,
        "est_ancetre": lambda sha, coupure: sha in ancetres,
    }


def test_un_sha_conserve_par_la_coupure_ne_bloque_pas_et_n_est_pas_interroge():
    """Le blocage du 28/08/2026, en miniature. `9100eb7` n'était pas ancêtre du
    point de coupure : après l'opération, le dépôt en restait la copie de
    référence, et que Software Heritage ne l'ait pas encore vu ne coûtait rien.

    Le script a bloqué pour une raison qui n'existait pas — et il l'aurait fait
    presque à chaque lancement, puisque SWH repasse tous les ~11 jours et que
    tout commit fusionné depuis apparaît comme « manquant »."""
    urls = []
    code, donnees, texte = _verifier_simule(
        {SHA_A: 200},  # SHA_B n'a pas à être interrogé : il ne tombe pas
        {"status": "full", "snapshot": "x", "visit": 1},
        urls=urls,
        ref_contenant=lambda sha: "refs/heads/main",
        **_coupure_simulee({SHA_A}),
    )
    assert code == v.VERIFIE, texte
    interrogees = [u for u in urls if "/revision/" in u]
    assert len(interrogees) == 1, "un SHA conservé a été interrogé pour rien"
    assert SHA_B not in "".join(interrogees)
    assert donnees["population"]["sha_conserves_par_la_coupure"] == 1
    assert donnees["population"]["sha_sous_la_coupure"] == 1
    assert [c["conserve"] for c in donnees["commits"] if c["sha"] == SHA_B] == [True]


def test_un_sha_sous_la_coupure_et_absent_bloque_toujours():
    """Le pendant obligatoire : sans lui, « ne jamais bloquer » passerait le
    test précédent et le garde-fou ne garderait plus rien."""
    code, _, texte = _verifier_simule(
        {SHA_A: 404, SHA_B: 200},
        {"status": "full", "snapshot": "x", "visit": 1},
        ref_contenant=lambda sha: "refs/heads/main",
        **_coupure_simulee({SHA_A, SHA_B}),
    )
    assert code == v.MANQUANTS
    assert "NE PAS COUPER" in texte
    assert SHA_A[:7] in texte


def test_la_sortie_ne_fait_jamais_croire_l_archive_facultative():
    """La nuance que #575 demande de ne pas perdre : un SHA conservé tombera
    sous une coupure FUTURE, et l'archive le couvrira d'ici là. Ce n'est pas
    « pas besoin d'archive », c'est « pas pour cette coupure-ci »."""
    _, _, texte = _verifier_simule(
        {SHA_A: 200},
        {"status": "full", "snapshot": "x", "visit": 1},
        **_coupure_simulee({SHA_A}),
    )
    assert "CONSERVÉS PAR LA COUPURE" in texte
    assert "pas pour cette coupure-ci" in texte
    assert "coupure FUTURE" in texte


def test_sans_coupure_le_perimetre_reste_tout_mais_la_sortie_le_dit():
    """« Une vérification sans coupure connue est un audit d'archive, pas un
    feu vert de coupure : les deux usages sont légitimes, ils ne rendent pas le
    même verdict » (#575).

    Le comportement d'avant est donc INTACT — les deux SHA sont interrogés —
    et c'est la sortie qui change."""
    urls = []
    code, donnees, texte = _verifier_simule(
        {SHA_A: 200, SHA_B: 404},
        {"status": "full", "snapshot": "x", "visit": 1},
        urls=urls,
        ref_contenant=lambda sha: "refs/heads/main",
    )
    assert len([u for u in urls if "/revision/" in u]) == 2
    assert code == v.MANQUANTS
    assert "AUDIT D'ARCHIVE" in texte
    assert "plus large que la population à risque" in texte
    assert donnees["coupure"] is None


def test_une_fenetre_non_contraignante_ne_perd_rien_et_ne_bloque_rien():
    """`--fenetre 30` sur un dépôt qui compte moins de 30 commits de données :
    `borner_historique_donnees.sh` répond « rien à borner », et la vérification
    doit répondre la même chose plutôt que d'interroger 47 SHA pour rien.

    C'est l'état du dépôt réel au 28/08/2026, et donc le cas le plus fréquent
    d'un lancement de contrôle."""
    urls = []
    code, donnees, texte = _verifier_simule(
        {},  # aucune interrogation attendue
        {"status": "full", "snapshot": "x", "visit": 1},
        urls=urls,
        fenetre=30,
        coupure_par_fenetre=lambda n: None,
        est_ancetre=lambda sha, coupure: pytest.fail(
            "ascendance calculée alors qu'il n'y a pas de coupure"
        ),
    )
    assert code == v.VERIFIE
    assert [u for u in urls if "/revision/" in u] == []
    assert "NON contraignante" in texte
    assert donnees["coupure"]["contraignante"] is False
    assert donnees["population"]["sha_conserves_par_la_coupure"] == 2


def test_une_coupure_qui_ne_resout_pas_refuse_de_conclure():
    """Vérifier silencieusement un autre périmètre que celui qu'on croit est la
    forme même du défaut corrigé ici : mieux vaut refuser."""
    with pytest.raises(ValueError, match="ne résout"):
        v.resoudre_coupure(None, "pas-un-commit", lambda n: None, lambda ref: None)


def test_le_quatrieme_cas_est_un_etat_a_part_pas_un_indetermine():
    """Un conservé n'est ni vérifié, ni manquant, ni orphelin, ni indéterminé :
    le confondre avec un indéterminé rendrait INDÉTERMINÉ au lieu de VÉRIFIÉ,
    c'est-à-dire bloquerait toujours, autrement."""
    conserve = v.CommitCite(sha=SHA_B, lieux=["#429"], etat="conserve")
    assert conserve.conserve is True and conserve.orpheline is False
    code, message = v.rendre_verdict(
        VISITE_FULL,
        [_commit(SHA_A, "presente"), conserve],
        v.Coupure(sha="c" * 40, demande="--fenetre 5", fenetre=5),
    )
    assert code == v.VERIFIE
    assert "conservé" in message


def test_les_conserves_sont_comptes_et_nommes_sans_noyer_le_rapport():
    """Une fenêtre non contraignante met TOUS les SHA cités dans ce cas — 47 au
    28/08/2026. Les nommer tous ferait 47 lignes que personne n'a à traiter, et
    noierait le seul groupe actionnable du rapport."""
    conserves = [
        v.CommitCite(sha=f"{i:040x}", lieux=[f"#{i}"], etat="conserve")
        for i in range(v.MAX_CONSERVES_AFFICHES + 5)
    ]
    texte = v.formater_rapport(
        BANC, VISITE_FULL, conserves, 20, 1, 1, v.Quota(),
        (v.VERIFIE, "rien à perdre"),
        coupure=v.Coupure(sha=None, demande="--fenetre 30", fenetre=30),
    )
    nommes = [l for l in texte.split("\n") if " — cité dans #" in l]
    assert len(nommes) == v.MAX_CONSERVES_AFFICHES
    assert "+5 autres" in texte
    assert "--json" in texte, "la liste entière doit rester joignable"


# ── #575 · La coupure, calculée par git et non par une approximation ─────────


def _depot_de_coupure(tmp_path, env):
    """Un dépôt minuscule : quelques commits de données et un commit de code
    entre eux, pour que le (N+1)-ième commit de données ne soit pas le
    (N+1)-ième commit tout court."""
    depot = tmp_path / "depot"
    subprocess.run(["git", "init", "--quiet", "-b", "main", str(depot)],
                   env=env, check=True, capture_output=True)

    def commit(sujet):
        subprocess.run(["git", "-C", str(depot), "commit", "--quiet",
                        "--allow-empty", "-m", sujet],
                       env=env, check=True, capture_output=True)
        return subprocess.run(["git", "-C", str(depot), "rev-parse", "HEAD"],
                              env=env, check=True, capture_output=True,
                              text=True).stdout.strip()

    shas = {"socle": commit("chore: socle")}
    for i in range(1, 6):
        shas[f"d{i}"] = commit(f"chore(données): {MOTIF_COMMIT_DONNEES} ({i})")
        if i == 3:
            shas["code"] = commit("feat: un commit de code")
    return depot, shas


def test_le_perimetre_de_coupure_est_celui_de_git(tmp_path):
    """Les deux fonctions qui décident du périmètre s'appuient sur git, et rien
    n'a jamais vérifié qu'elles lui demandaient la bonne chose.

    Deux vérifications, sur un dépôt réel monté dans `tmp_path` :
      - `_coupure_par_fenetre_git` rend EXACTEMENT ce que rend la fonction
        `_coupure()` de `scripts/borner_historique_donnees.sh` — le pipeline
        shell est rejoué ici, et l'égalité est le test. Une coupure calculée
        autrement ferait vérifier un périmètre qui n'est pas celui qui sera
        coupé, c'est-à-dire déplacerait le défaut de #575 d'un cran ;
      - `_est_ancetre_git` sépare bien ce que la coupure emporte de ce qu'elle
        garde.
    """
    env = dict(os.environ)
    for fuite in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        env.pop(fuite, None)
    config = tmp_path / "gitconfig"
    config.write_text(
        "[user]\n\tname = Banc 575\n\temail = banc-575@example.invalid\n",
        encoding="utf-8",
    )
    env.update({"HOME": str(tmp_path), "GIT_CONFIG_GLOBAL": str(config),
                "GIT_CONFIG_SYSTEM": str(config), "GIT_TERMINAL_PROMPT": "0"})
    depot, shas = _depot_de_coupure(tmp_path, env)

    par_fenetre = v._coupure_par_fenetre_git(str(depot))
    for fenetre in range(0, 6):
        # Le MÊME calcul que le script de bornage, rejoué en shell.
        attendu = subprocess.run(
            ["bash", "-c",
             f"git -C {depot} log --format=%H --grep='{MOTIF_COMMIT_DONNEES}' "
             f"main | sed -n '{fenetre + 1}p'"],
            env=env, check=True, capture_output=True, text=True,
        ).stdout.strip() or None
        assert par_fenetre(fenetre) == attendu, f"fenêtre {fenetre}"

    # Fenêtre 2 : d5 et d4 sont conservés, d3 est le point de coupure.
    coupure = par_fenetre(2)
    assert coupure == shas["d3"]
    est_ancetre = v._est_ancetre_git(str(depot))
    assert est_ancetre(shas["d1"], coupure) and est_ancetre(shas["d3"], coupure)
    assert not est_ancetre(shas["d4"], coupure)
    assert not est_ancetre(shas["code"], coupure)


def test_le_motif_de_commit_de_donnees_n_est_pas_recopie_ici():
    """La valeur vit dans `audit_volumetrie_profils.MOTIF_COMMIT_DONNEES`, et
    le script de bornage la répète déjà dans son `MOTIF=`. Une troisième copie
    ferait calculer une coupure différente de celle qui sera faite, sans que
    rien ne le signale — et #575 vient précisément de corriger un périmètre
    faux."""
    source = (RACINE / "src" / "verifier_archivage_swh.py").read_text(
        encoding="utf-8"
    )
    assert "from audit_volumetrie_profils import MOTIF_COMMIT_DONNEES" in source
    corps = source.split('"""', 2)[-1]  # hors docstring de module
    assert MOTIF_COMMIT_DONNEES not in corps, "motif recopié au lieu d'être importé"
    bash = SCRIPT_BORNAGE.read_text(encoding="utf-8")
    assert f'MOTIF="{MOTIF_COMMIT_DONNEES}"' in bash, (
        "le script de bornage et la vérification ne reconnaissent plus les "
        "mêmes commits de données"
    )


def test_l_etape_2b_passe_la_coupure_a_la_verification():
    """« Brancher le paramètre dans l'étape 2b de la procédure, pour que la
    vérification porte sur la coupure que `--preparer` s'apprête à faire »
    (#575). Sans ça, la correction existe mais personne ne l'emploie : la
    procédure est le seul endroit où cette commande se lit."""
    texte = SCRIPT_BORNAGE.read_text(encoding="utf-8")
    # La LIGNE d'invocation, pas la prose autour : c'est elle qu'on recopie
    # dans un terminal. Chercher `--fenetre` n'importe où dans l'étape 2b
    # resterait vert alors que la commande à taper ne le porte plus — la prose
    # qui explique l'option contient le mot, forcément.
    invocations = [
        ligne.strip()
        for ligne in texte.split("\n")
        if "verifier_archivage_swh.py" in ligne and "python3" in ligne
    ]
    assert invocations, "l'étape 2b ne lance plus la vérification"
    assert all("--fenetre" in ligne or "--coupure" in ligne for ligne in invocations), (
        f"la vérification est lancée sans point de coupure : {invocations}"
    )
    assert "CONSERVÉS PAR LA COUPURE" in texte
    assert "pas pour cette coupure-ci" in texte
