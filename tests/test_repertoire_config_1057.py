"""`config/` porte ce qu'une personne décide, `raw_data/` ce qu'un run écrit (#1057).

Le critère est **qui écrit le fichier**, jamais son nom — `gouvernements_reels.json`
reste dans `raw_data/` bien qu'il ressemble à de la configuration, parce que
`src/gouvernements_amo30.py --out` le régénère à chaque run.

Ce que ces gardes tiennent : qu'un run n'écrive jamais dans `config/`, que la
navette entre les deux dépôts continue de traiter `config/` comme du code, et
qu'aucun ancien chemin ne survive dans le code exécuté. Sans elles, la règle
« les données viennent du public, le code du privé » redevient une règle à
exception, et c'est exactement ce que ce lot supprime.
"""

import pathlib
import re

RACINE = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"
SYNC = RACINE / "scripts" / "sync_depots.sh"

#: Les trois fichiers écrits à la main. Aucun n'est produit par un run.
ECRITS_A_LA_MAIN = (
    "groupes_reels.json",
    "mandats_anterieurs.json",
    "correspondance_elus_rne.json",
)


def test_les_trois_fichiers_ecrits_a_la_main_sont_dans_config():
    for nom in ECRITS_A_LA_MAIN:
        assert (RACINE / "config" / nom).is_file(), f"config/{nom} attendu"
        assert not (RACINE / "raw_data" / nom).exists(), (
            f"raw_data/{nom} subsiste : deux copies divergeraient en silence"
        )


def test_gouvernements_reels_reste_dans_raw_data():
    """Il ressemble à de la config et n'en est pas : le run le régénère.

    `src/gouvernements_amo30.py --out raw_data/gouvernements_reels.json` — le
    déplacer ferait écrire un run dans `config/`, ce que la règle interdit.
    """
    assert (RACINE / "raw_data" / "gouvernements_reels.json").is_file()
    assert not (RACINE / "config" / "gouvernements_reels.json").exists()
    assert "--out raw_data/gouvernements_reels.json" in WORKFLOW.read_text(encoding="utf-8"), (
        "si le run n'écrit plus ce fichier, sa place est à réexaminer — et cette "
        "garde avec elle"
    )


def test_aucun_run_n_ecrit_dans_config():
    """Le `git add` du commit de données ne doit nommer aucun chemin de `config/`.

    C'est la garde de fond : un fichier que le run réécrirait ne serait plus de
    la configuration, et la règle de synchronisation le renverrait au mauvais
    dépôt à chaque publication.
    """
    contenu = WORKFLOW.read_text(encoding="utf-8")
    lignes_add = [l for l in contenu.splitlines() if "git add " in l]
    assert lignes_add, "le step de commit doit exister — sinon cette garde ne garde rien"
    for ligne in lignes_add:
        assert "config/" not in ligne, (
            f"un run écrit dans config/ : {ligne.strip()}"
        )


def test_la_navette_traite_config_comme_du_code():
    """`DONNEES` ne liste que les deux répertoires écrits par un run.

    `scripts/sync_depots.sh` récupère `DONNEES` depuis le public et publie tout
    le reste depuis le privé. `config/` doit donc en rester dehors : c'est ce
    qui fait voyager une correction de lignée avec le code qui la lit.
    """
    declaration = re.search(r"^DONNEES=\(([^)]*)\)", SYNC.read_text(encoding="utf-8"),
                            re.MULTILINE)
    assert declaration, "la constante DONNEES doit rester lisible par une garde"
    assert declaration.group(1).split() == ["pivot_data", "raw_data"], (
        f"DONNEES vaut ({declaration.group(1)}) — `config/` y entrerait comme donnée, "
        "et une correction écrite à la main serait écrasée par le contenu du public"
    )


def test_aucun_ancien_chemin_ne_survit_dans_le_code_execute():
    """Les fichiers de décision et `docs/archive/` sont exclus : ils ne s'éditent pas.

    Une décision dit ce qui était vrai le jour où elle a été prise ; c'est
    `docs/decisions/repertoire-config-1057.md` qui porte le déplacement.
    """
    exclus = ("docs/decisions", "docs/archive", ".git/")
    motif = re.compile(r"raw_data/(?:%s)" % "|".join(n[:-5] for n in ECRITS_A_LA_MAIN))
    coupables = []
    for chemin in (*RACINE.glob("src/*.py"), *RACINE.glob("scripts/*"),
                   *RACINE.glob("tests/*.py"), *RACINE.glob(".github/workflows/*.yml")):
        if any(e in str(chemin) for e in exclus):
            continue
        try:
            texte = chemin.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if motif.search(texte):
            coupables.append(str(chemin.relative_to(RACINE)))
    assert not coupables, f"anciens chemins encore lus : {sorted(coupables)}"
