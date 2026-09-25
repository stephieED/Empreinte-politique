"""Le §8 de `docs/workflow-generate-data.md` dit l'ordre RÉEL des contrôles.

Jusqu'au 25/09/2026, sa colonne « Ordre » donnait 1 collecté-non-publié,
2 perte, 3 intégrité, 4 collecté-vs-publié — un classement qui n'était celui
d'aucune exécution : le YAML lance perte, intégrité, collecté-non-publié,
collecté-vs-publié. Personne ne s'en était aperçu parce qu'une table d'ordre se
lit sans être recoupée, et c'est exactement ce que ce test fait à sa place.

Relevé par la session « Visu workflow » en dessinant le graphe d'exécution : une
figure recoupe ce qu'une prose laisse passer.
"""

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"
DOC = RACINE / "docs" / "workflow-generate-data.md"

#: Le portail qualité n'est pas l'un des quatre contrôles : il les précède.
PORTAIL = "Quality gate — résumé et contrôle qualité"


def _etapes_du_job(nom: str) -> list[str]:
    """Les `- name:` d'un job, dans l'ordre du fichier."""
    texte = WORKFLOW.read_text(encoding="utf-8")
    debut = re.search(rf"^  {re.escape(nom)}:\s*$", texte, flags=re.MULTILINE)
    assert debut, f"job `{nom}` absent de {WORKFLOW.name}"
    suite = re.search(r"^  [a-z][a-z0-9-]*:\s*$", texte[debut.end():], flags=re.MULTILINE)
    bloc = texte[debut.end(): debut.end() + suite.start()] if suite else texte[debut.end():]
    return re.findall(r"^      - name: (.+)$", bloc, flags=re.MULTILINE)


def _etapes_du_tableau() -> list[str]:
    """La colonne « Étape du workflow » du tableau du §8, dans l'ordre."""
    doc = DOC.read_text(encoding="utf-8")
    section = doc.split("## 8. Les quatre contrôles avant commit")[1].split("\n## ")[0]
    lignes = [l for l in section.split("\n") if re.match(r"^\| \d+ \|", l)]
    assert lignes, "le tableau du §8 n'a plus de ligne numérotée"
    return [l.split("|")[3].strip() for l in lignes]


def test_le_tableau_du_paragraphe_8_suit_l_ordre_du_yaml():
    etapes = _etapes_du_job("merge-and-pivot")
    attendues = _etapes_du_tableau()
    assert len(attendues) == 4, f"le §8 annonce quatre contrôles, il en liste {len(attendues)}"

    rangs = []
    for libelle in attendues:
        assert libelle in etapes, (
            f"le §8 cite l'étape « {libelle} », que le workflow ne porte pas. "
            "Un intitulé renommé dans le YAML se recopie ici."
        )
        rangs.append(etapes.index(libelle))

    assert rangs == sorted(rangs), (
        "la colonne « Ordre » du §8 ne suit pas l'ordre d'exécution du YAML. "
        f"Ordre du fichier : {[attendues[i] for i in sorted(range(4), key=rangs.__getitem__)]}"
    )


def test_le_portail_qualite_precede_les_quatre_et_n_en_est_pas_un():
    etapes = _etapes_du_job("merge-and-pivot")
    assert PORTAIL in etapes, "le portail qualité a disparu du job"
    assert PORTAIL not in _etapes_du_tableau(), (
        "le portail qualité n'est pas l'un des quatre contrôles : il les précède"
    )
    assert etapes.index(PORTAIL) < min(etapes.index(e) for e in _etapes_du_tableau())


def test_le_job_ne_dit_plus_produire_des_fiches_de_parti():
    """#906 les a retirées, et la doc l'écrit dans sa propre section — mais le
    bloc du job les citait encore parmi ce qu'il produit."""
    doc = DOC.read_text(encoding="utf-8")
    bloc = doc.split("## 8. Les quatre contrôles avant commit")[0]
    assert "profils de parti ;" not in bloc, (
        "le bloc de merge-and-pivot annonce des profils de parti, retirés par #906"
    )
