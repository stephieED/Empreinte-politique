"""Le sparse-checkout d'`extract-an` couvre ce que la collecte AN lit (#498).

**Pourquoi ce garde-fou existe.** Le run `33404236969` (31/08/2026) a tué ses
13 shards l'un après l'autre à 5 min 00 **dans `actions/checkout`**, l'étape
d'extraction restant `skipped`. La cause n'était pas le réseau : l'arbre pesait
8 483 Mio, dont **7 525 dans le seul `raw_data/profiles/`**, et `extract-an` est
le seul job à `timeout-minutes: 5`. Un shard tué par `timeout-minutes` n'écrit
aucun profil (#498) — 40 minutes pour rien.

Le correctif est une **liste blanche** : un shard ne matérialise que le code,
les référentiels de premier niveau, les index figés, et **son propre** profil
brut. Ce qui rend la liste dangereuse est ce qui rend celle de `tests.yml`
dangereuse — un chemin oublié **passe en local et échoue en CI** (#434, #518
deux fois, #520). Ici c'est pire que dans `tests.yml` : un référentiel absent ne
lève pas toujours, il se replie (`correspondance_acteurs_an.json` a un repli
*déclaré*, #525), et la collecte publie alors moins sans que rien n'échoue.

**Ce que ce test relève.** Il ne devine pas : il calcule la **fermeture des
imports** de `src/generate_all_profiles.py` restreinte à `src/`, puis relève
dans ces seuls modules les littéraux de chemin sous `raw_data/`. Un module de
migration ou d'audit, qui ne tourne pas dans le shard, n'entre donc pas dans le
périmètre — et un nouvel import l'y fait entrer tout seul.

Volontairement sans PyYAML (absent de `requirements.txt`), comme les autres
gardes-fous de workflow de ce dépôt.
"""

import ast
import re
from pathlib import Path

import _outils_ci

RACINE = Path(__file__).resolve().parents[1]
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"
SRC = RACINE / "src"

#: Le point d'entrée du shard, tel que le workflow l'invoque.
POINT_ENTREE = "generate_all_profiles"

#: `Path("raw_data") / "x"` et `Path("raw_data/x")`.
#:
#: Le second motif s'arrête au premier caractère qui ne peut pas appartenir à
#: un chemin : plusieurs messages destinés à l'utilisatrice nomment un fichier
#: **puis continuent la phrase** (`"raw_data/candidats.json, dont extract-an
#: collecte…"`). Sans cette borne, le chemin relevé serait la phrase entière et
#: le test échouerait sur un fichier pourtant couvert.
_LITTERAL_COMPOSE = re.compile(r'"raw_data"\s*(?:/\s*"([^"/]+)")')
_LITTERAL_PLAT = re.compile(r'"raw_data/([\w./-]+)"?')


#: Les jobs de ce workflow qui portent une liste blanche. Deux au 31/08/2026 :
#: `extract-an`, et `prepare-an-matrix` que la première application du lot avait
#: oublié — la cause n'est pas propre à un job, c'est le poids de l'arbre.
#: Trois depuis #757 : `rafraichir-candidats` lit la liste éditoriale et la table
#: de correspondance, et il est au budget le plus serré du premier étage.
JOBS_AVEC_LISTE_BLANCHE = ("rafraichir-candidats", "prepare-an-matrix", "extract-an")


def _tranche_du_job(job: str) -> str:
    """Le texte YAML du seul job nommé.

    Le workflow porte plusieurs blocs `sparse-checkout: |` et le parseur
    partagé rend le **premier** du fichier. Sans ce découpage, ce test croirait
    vérifier un job en lisant la liste d'un autre — et il serait vert sur une
    liste qu'il n'a jamais regardée.
    """
    texte = WORKFLOW.read_text(encoding="utf-8")
    debut = texte.index(f"\n  {job}:\n")
    suite = re.search(r"\n  [a-z][a-z0-9-]*:\n", texte[debut + 1:])
    return texte[debut:debut + 1 + suite.start()] if suite else texte[debut:]


def _liste_blanche(job: str, tmp_path) -> frozenset[str]:
    """Entrées du bloc `sparse-checkout: |` d'un job, via le parseur partagé.

    La tranche est écrite dans un fichier temporaire plutôt que ré-analysée
    ici : `tests/_outils_ci.py` existe précisément pour qu'il n'y ait **qu'un**
    analyseur de ce bloc dans le dépôt, et en redéfinir un ici rejouerait la
    divergence qu'il a été écrit pour clore.
    """
    tranche = tmp_path / f"{job}.yml"
    tranche.write_text(_tranche_du_job(job), encoding="utf-8")
    blanche = _outils_ci.lire_liste_blanche(tranche)
    assert blanche, (
        f"bloc `sparse-checkout: |` absent, vide ou de forme inattendue dans "
        f"le job `{job}` de generate-data.yml — voir "
        "`tests/_outils_ci.lire_liste_blanche`.")
    return blanche


def _fermeture_des_imports() -> set[str]:
    """Modules de `src/` atteignables depuis le point d'entrée du shard."""
    vus: set[str] = set()
    a_voir = [POINT_ENTREE]
    while a_voir:
        nom = a_voir.pop()
        if nom in vus:
            continue
        chemin = SRC / f"{nom}.py"
        if not chemin.is_file():
            continue
        vus.add(nom)
        arbre = ast.parse(chemin.read_text(encoding="utf-8"), filename=str(chemin))
        for noeud in ast.walk(arbre):
            if isinstance(noeud, ast.Import):
                a_voir.extend(alias.name.split(".")[0] for alias in noeud.names)
            elif isinstance(noeud, ast.ImportFrom) and noeud.module:
                a_voir.append(noeud.module.split(".")[0])
    return vus


def _sans_prose(texte: str) -> str:
    """Le module amputé de ses commentaires et de ses docstrings.

    **Ce n'est pas de la coquetterie** : la prose de ce dépôt cite les chemins
    en toutes lettres, et les deux premiers chemins relevés par ce test
    l'avaient été dans une phrase, pas dans un appel. Un garde-fou qui échoue
    sur une phrase se fait désarmer. Même règle que #529, qui lit le code
    exécuté et jamais les commentaires.
    """
    arbre = ast.parse(texte)
    lignes = texte.split("\n")
    for noeud in ast.walk(arbre):
        corps = getattr(noeud, "body", None)
        if not isinstance(corps, list) or not corps:
            continue
        if not isinstance(noeud, (ast.Module, ast.ClassDef,
                                  ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        premier = corps[0]
        if not (isinstance(premier, ast.Expr)
                and isinstance(premier.value, ast.Constant)
                and isinstance(premier.value.value, str)):
            continue
        for i in range(premier.lineno - 1, premier.end_lineno):
            lignes[i] = ""
    return "\n".join(
        ligne for ligne in lignes if not ligne.lstrip().startswith("#"))


def _chemins_raw_data_lus() -> set[str]:
    """Chemins sous `raw_data/` que le code du shard construit réellement."""
    trouves: set[str] = set()
    for nom in sorted(_fermeture_des_imports()):
        code = _sans_prose((SRC / f"{nom}.py").read_text(encoding="utf-8"))
        trouves.update(f"raw_data/{m}" for m in _LITTERAL_COMPOSE.findall(code))
        trouves.update(f"raw_data/{m}" for m in _LITTERAL_PLAT.findall(code))
    return trouves


def _couvert(chemin: str, blanche: frozenset[str]) -> bool:
    """Un chemin est couvert par une entrée égale ou par un de ses parents."""
    parts = chemin.split("/")
    return any("/".join(parts[:i]) in blanche for i in range(1, len(parts) + 1))


def test_chaque_bloc_sparse_checkout_est_declare_ici():
    """Un bloc ajouté à un job que ce test ignore ne serait vérifié par
    personne. Le parseur partagé rend le PREMIER bloc du fichier : c'est le
    découpage par job qui rend l'ajout visible, et ce cas qui rend l'oubli
    bruyant. C'est exactement l'oubli qui a coûté le run `33414042623` —
    `extract-an` réparé, `prepare-an-matrix` non, et la matrice jamais
    publiée."""
    texte = WORKFLOW.read_text(encoding="utf-8")
    assert texte.count("sparse-checkout: |") == len(JOBS_AVEC_LISTE_BLANCHE), (
        f"{texte.count('sparse-checkout: |')} blocs `sparse-checkout: |` pour "
        f"{len(JOBS_AVEC_LISTE_BLANCHE)} job(s) déclaré(s) dans "
        "JOBS_AVEC_LISTE_BLANCHE : ajouter le job ici, sinon sa liste blanche "
        "n'est vérifiée par rien")
    for job in JOBS_AVEC_LISTE_BLANCHE:
        assert "sparse-checkout: |" in _tranche_du_job(job), (
            f"`{job}` est déclaré ici mais n'a plus de liste blanche")


def test_prepare_an_matrix_materialise_le_fichier_de_candidats(tmp_path):
    """Ce job ne lit qu'un fichier, et sans lui il ne publie aucune matrice —
    donc `extract-an` est skippé et le run ne collecte rien côté AN, sans
    qu'aucune étape n'échoue autrement qu'en s'annulant."""
    blanche = _liste_blanche("prepare-an-matrix", tmp_path)
    assert "raw_data/candidats.json" in blanche
    assert "raw_data" not in blanche
    assert not any(e.startswith("raw_data/profiles") for e in blanche), (
        "prepare-an-matrix ne lit aucun profil : l'y inscrire ramènerait les "
        "7 525 Mio qui l'ont tué")


def test_la_fermeture_des_imports_atteint_bien_le_coeur_de_la_collecte():
    """Sans ce cas, une fermeture cassée rendrait les autres verts pour rien —
    c'est le défaut du diagnostic muet de #518, transposé."""
    modules = _fermeture_des_imports()
    assert POINT_ENTREE in modules
    for attendu in ("candidate_profile", "merge_profile", "profil_brut"):
        assert attendu in modules, (
            f"`{attendu}` n'est plus atteignable depuis `{POINT_ENTREE}` : la "
            "fermeture des imports ne décrit plus ce que le shard exécute.")


def test_la_liste_blanche_couvre_les_referentiels_que_la_collecte_lit(tmp_path):
    blanche = _liste_blanche("extract-an", tmp_path)
    # `raw_data/profiles` est couvert **partiellement et exprès** : le shard ne
    # matérialise que son propre profil, via les deux entrées `matrix.slug`.
    # C'est tout l'objet du lot — l'y inscrire en entier ramènerait 7 525 Mio.
    non_couverts = sorted(
        chemin for chemin in _chemins_raw_data_lus()
        if not chemin.startswith("raw_data/profiles")
        and not _couvert(chemin, blanche))
    assert not non_couverts, (
        "ces chemins sont lus par la collecte AN mais absents du "
        "sparse-checkout d'extract-an — ils seront absents du disque du "
        f"runner, et la collecte se repliera en silence : {non_couverts}")


def test_le_shard_materialise_son_propre_profil_brut(tmp_path):
    """Socle **et** tranches (#580). Sans le socle, la fusion additive repart de
    zéro et republie un profil amputé sans que rien n'échoue (#465)."""
    blanche = _liste_blanche("extract-an", tmp_path)
    assert "raw_data/profiles/${{ matrix.slug }}.json" in blanche, (
        "le socle du profil du shard n'est pas dans la liste blanche")
    assert "raw_data/profiles/${{ matrix.slug }}" in blanche, (
        "le répertoire de tranches par législature n'est pas dans la liste "
        "blanche : un profil partitionné (#580) reviendrait sans ses "
        "amendements")


def test_le_corpus_entier_reste_hors_de_la_liste_blanche(tmp_path):
    """L'autre sens de la liste. `raw_data` entier, ou `raw_data/profiles`
    entier, rendrait le lot inutile et le timeout se refermerait."""
    blanche = _liste_blanche("extract-an", tmp_path)
    assert "raw_data" not in blanche
    assert "raw_data/profiles" not in blanche
    assert "pivot_data" not in blanche, (
        "extract-an ne lit pas le pivot : l'y inscrire ajouterait 894 Mio")


def test_le_filtre_de_blobs_accompagne_chaque_liste_blanche():
    """Sans `filter: blob:none`, git télécharge les blobs de tout l'arbre avant
    de n'en matérialiser qu'une fraction — le coût qu'on supprime revient.
    Vérifié **job par job** : la liste blanche seule ne suffit pas, et un job
    qui l'oublie paierait le checkout complet sans que rien ne le dise."""
    for job in JOBS_AVEC_LISTE_BLANCHE:
        tranche = _tranche_du_job(job)
        entete = tranche[:tranche.index("sparse-checkout: |")]
        assert "filter: blob:none" in entete, (
            f"`filter: blob:none` manque au checkout de `{job}`")
        assert "sparse-checkout-cone-mode: false" in entete, (
            f"`{job}` : le mode cône ne sait pas exprimer un chemin de fichier "
            "comme `raw_data/candidats.json` ni `raw_data/profiles/<slug>.json` "
            "— la liste blanche serait silencieusement élargie au répertoire")


#: Au-dessous de ce plafond, le checkout complet (4 min 52 à 6 min 03, mesuré
#: sur le run `33404236969`) mange une part inacceptable du budget du job. Le
#: seuil est à 10 et non à 5 pour garder une marge : aucun job du workflow ne
#: se situe aujourd'hui entre 6 et 15 minutes.
PLAFOND_SANS_LISTE_BLANCHE = 10


def test_tout_job_au_budget_serre_porte_une_liste_blanche():
    """La règle générale, celle qui évite la troisième occurrence.

    Nommer les jobs un par un a déjà échoué une fois : `extract-an` réparé,
    `prepare-an-matrix` oublié, run `33414042623` perdu le jour même. Le
    critère n'est pas l'identité du job, c'est son budget — un job à
    `timeout-minutes` serré ne peut pas payer 6 minutes de checkout.

    Un `timeout-minutes` exprimé en expression `${{ }}` n'est pas évaluable
    ici : il est signalé comme non vérifiable plutôt que supposé conforme.
    """
    texte = WORKFLOW.read_text(encoding="utf-8")
    for job in re.findall(r"\n  ([a-z][a-z0-9-]*):\n", texte):
        tranche = _tranche_du_job(job)
        trouve = re.search(r"\n    timeout-minutes:\s*(.+)", tranche)
        if not trouve:
            continue
        # Un commentaire de fin de ligne suit parfois la valeur
        # (`timeout-minutes: 30   # ← même valeur que ...`) : sans cette coupe,
        # un job conforme serait signalé comme non vérifiable.
        brut = trouve.group(1).split("#")[0].strip()
        if not brut.isdigit():
            # Expression : la couverture se vérifie par la déclaration.
            assert job in JOBS_AVEC_LISTE_BLANCHE, (
                f"`{job}` a un `timeout-minutes` calculé et aucune liste "
                "blanche : sa conformité n'est pas vérifiable ici")
            continue
        if int(brut) <= PLAFOND_SANS_LISTE_BLANCHE:
            assert "sparse-checkout: |" in tranche, (
                f"`{job}` a `timeout-minutes: {brut}` et aucune liste "
                "blanche : le checkout complet coûte 4 min 52 à 6 min 03 "
                "(run 33404236969) et le tuera, sans écrire quoi que ce soit "
                "(#498). Ajouter la liste blanche, pas relever le plafond.")


def test_le_timeout_du_shard_est_inchange():
    """Le lot supprime la CAUSE, il ne desserre pas la contrainte. Si ce test
    échoue parce que le timeout a été relevé, c'est que quelqu'un a soigné le
    symptôme : `AGENTS.md` §3b interdit de le faire seul (#498)."""
    texte = WORKFLOW.read_text(encoding="utf-8")
    assert "timeout-minutes: ${{ inputs.collect_interventions && 10 || 5 }}" in texte, (
        "le `timeout-minutes` d'extract-an a changé : relire #498 et "
        "docs/decisions/budget-collecte-interventions.md avant de le valider")
