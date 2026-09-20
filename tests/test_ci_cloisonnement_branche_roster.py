"""La branche roster est cloisonnée : sa panne ne coûte plus le commit (#524).

## Ce qui est verrouillé, et pourquoi

Le run `32876863499` (24/08/2026) a perdu son commit alors que `merge-and-pivot`
avait TERMINÉ l'étape 12 (fusion des bruts) et l'étape 13 (normalisation pivot
+ enrichissement ParlTrack, 165 s, verte). Il est mort au step 15, `Repli —
construction de la liste roster-driven`, sur un `www.nosdeputes.fr/deputes/json`
en 500 — et tout ce travail a été jeté.

C'est exactement l'arbitrage que #518 avait écrit 70 lignes plus bas pour
`generate_group_profiles.py` et jamais appliqué au repli roster juste au-dessus :

> « Refuser qu'une donnée NON écrite annule la publication d'une donnée écrite,
> c'est ce que le run 32750929942 a fait faute de cette distinction. »

Deux propriétés sont testées ici, et elles vont ensemble :

- **B** — un fetch roster tombé ne fait plus échouer `merge-and-pivot`, et la
  passe pivot roster est conditionnée à l'EXISTENCE du fichier (il n'est pas
  committé) plutôt qu'au succès d'un step ;
- **C** — le code `2` (« extraction de tous les groupes suspendue ») est toléré
  par les TROIS appelants de `generate_roster_candidats.py`.

Et une propriété négative, qui compte autant : **aucun `continue-on-error: true`
n'est ajouté sur ces steps**. Il avalerait aussi ce qui n'est pas un code de
sortie documenté (127, 137/OOM…) et ferait passer un job mort pour une source
indisponible — même raison qu'au step groupes de #518.

Ce que ces tests NE relâchent PAS : `audit_collecte_non_publiee.py` (#511/#518)
reste armé avant le commit, et c'est lui qui rend le saut légitime plutôt que
décrété.

Volontairement sans PyYAML (absent de `requirements.txt`), comme les autres
gardes-fous de workflow de ce dépôt.
"""

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"
SCRIPT = "python3 src/generate_roster_candidats.py"
ROSTER_JSON = "raw_data/roster_candidats.json"
#: Ce qui distingue la passe pivot des **candidats déclarés** de celle du
#: roster : elle seule enrichit depuis ParlTrack.
PASSE_PIVOT_DECLARES = "--enrich-parltrack"
#: Les trois appelants du script dans un run, dans l'ordre chronologique.
APPELANTS = ("prepare-roster-matrix", "extract-roster-groupes", "merge-and-pivot")


def _bloc_job(nom: str) -> str:
    texte = WORKFLOW.read_text(encoding="utf-8")
    debut = re.search(rf"^  {re.escape(nom)}:\s*$", texte, flags=re.MULTILINE)
    assert debut, f"job `{nom}` absent de {WORKFLOW.name}"
    suite = re.search(r"^  [a-z][a-z0-9-]*:\s*$", texte[debut.end():], flags=re.MULTILINE)
    return texte[debut.end(): debut.end() + suite.start()] if suite else texte[debut.end():]


def _sans_commentaires(bloc: str) -> str:
    """Les rationales de ce dépôt citent abondamment les commandes qu'elles
    expliquent : les lire comme du workflow serait un faux positif permanent."""
    return "\n".join(l for l in bloc.split("\n") if not l.lstrip().startswith("#"))


def _steps(bloc: str) -> list[str]:
    code = _sans_commentaires(bloc)
    decoupe = re.split(r"^      - (?=name:|uses:|run:)", code, flags=re.MULTILINE)
    return [s for s in decoupe[1:] if s.strip()]


def _step_contenant(nom_job: str, aiguille: str) -> str:
    trouves = [s for s in _steps(_bloc_job(nom_job)) if aiguille in s]
    assert len(trouves) == 1, (
        f"{nom_job} : {len(trouves)} step(s) contiennent {aiguille!r}, 1 attendu.")
    return trouves[0]


# ---------------------------------------------------------------------------
# C — le code 2 est toléré par les trois appelants
# ---------------------------------------------------------------------------

def test_les_trois_appelants_tolerent_le_code_2():
    """LE test de C.

    `generate_roster_candidats.py` rend 2 quand toutes les entrées de
    `groupes_reels.json` ont leur extraction suspendue : rien à collecter, rien
    d'écrit, par décision documentée (#516). Un appelant qui laisserait ce code
    faire rougir son step rendrait la suspension — le seul remède documenté à
    une source en panne — strictement équivalente à la panne.
    """
    for job in APPELANTS:
        step = _step_contenant(job, SCRIPT)
        assert '"$CODE" == "2"' in step or '"$CODE" == "1" || "$CODE" == "2"' in step, (
            f"`{job}` ne filtre pas le code 2 de generate_roster_candidats.py (#524) :\n{step}")


def test_aucun_appelant_ne_tolere_un_code_inattendu():
    """La tolérance porte sur des codes NOMMÉS, jamais sur « ça a échoué ».

    Un 127 (commande absente) ou un 137 (OOM) doit continuer de faire rougir le
    step : sans cette ligne, un job mort pour une tout autre cause passerait
    pour un roster indisponible.
    """
    for job in APPELANTS:
        step = _step_contenant(job, SCRIPT)
        assert 'exit "$CODE"' in step, (
            f"`{job}` ne repropage pas les codes non documentés (#524) :\n{step}")


def test_aucun_continue_on_error_sur_les_steps_de_roster():
    """La propriété négative de #518, reconduite : filtrer sur le CODE, dans le
    shell, jamais par un `continue-on-error: true` — celui-ci avalerait aussi
    un vrai plantage et laisserait le run publier sans que rien ne bloque."""
    for job in APPELANTS:
        step = _step_contenant(job, SCRIPT)
        assert "continue-on-error" not in step, (
            f"`{job}` : `continue-on-error` sur le step de roster (#518, #524) :\n{step}")


# ---------------------------------------------------------------------------
# B — la branche roster ne coûte plus le commit des candidats déclarés
# ---------------------------------------------------------------------------

def test_le_repli_de_merge_and_pivot_ne_fait_plus_echouer_le_job():
    """LE test de B.

    Le code 1 est « roster INCOMPLET, donc NON ÉCRIT » (#511) : c'est celui du
    500 du run 32876863499. Rien n'a été écrit sur ce chemin — les profils de
    candidats déclarés et les fiches de parti, eux, l'ont été.
    """
    step = _step_contenant("merge-and-pivot", SCRIPT)
    assert '"$CODE" == "1"' in step, (
        "un fetch roster tombé fait encore échouer `merge-and-pivot`, donc "
        "annule le commit de données correctement écrites (#524) :\n" + step)


def test_la_passe_pivot_roster_est_conditionnee_a_l_existence_du_fichier():
    """Sur l'EXISTENCE du fichier, et non sur le succès du step précédent : le
    roster peut manquer par plusieurs routes (artifact absent, repli sauté,
    `prepare-roster-matrix` skippé). Il n'est pas committé — sans lui, la passe
    échouerait de toute façon, sur un message parlant de fichier introuvable
    plutôt que de branche roster fermée."""
    step = _step_contenant("merge-and-pivot", f"--candidats {ROSTER_JSON}")
    assert f"hashFiles('{ROSTER_JSON}') != ''" in step, (
        "la normalisation pivot roster-driven n'est pas conditionnée à "
        f"l'existence de {ROSTER_JSON} (#524) :\n" + step)


def test_l_extraction_des_shards_est_conditionnee_de_la_meme_facon():
    """Même raison dans `extract-roster-groupes` : sans liste, il n'y a rien à
    extraire, et un shard qui n'extrait rien publie un artifact vide — jamais
    la baseline committée (#450)."""
    step = _step_contenant("extract-roster-groupes", f"--candidats {ROSTER_JSON}")
    assert f"hashFiles('{ROSTER_JSON}') != ''" in step, step


def test_les_profils_de_candidats_declares_ne_dependent_pas_du_roster():
    """L'invariant que B rétablit, lu dans l'ordre des steps.

    La première passe pivot — celle des candidats déclarés, reconnaissable à
    `--enrich-parltrack` — précède la branche roster. Si elle venait APRÈS un
    step de roster non tolérant, sa publication redeviendrait tributaire de
    NosDéputés.

    Ce test s'ancrait aussi sur `src/parti_profile.py`, qui venait **après** le
    roster : c'était le cas qui obligeait le repli à cesser de tuer le job.
    #906 a retiré les fiches de parti — aucun lecteur, 25 des 29 n'agrégeant
    qu'un seul candidat — et l'ancrage restant est le plus fort des deux : ce
    qui compte est que les déclarés soient publiés **avant** que le roster
    puisse échouer.
    """
    code = _sans_commentaires(_bloc_job("merge-and-pivot"))
    rang_pivot_declares = code.find(PASSE_PIVOT_DECLARES)
    rang_repli_roster = code.find(SCRIPT)
    assert 0 <= rang_repli_roster
    assert 0 <= rang_pivot_declares, (
        f"la passe pivot des candidats déclarés ne se reconnaît plus à "
        f"{PASSE_PIVOT_DECLARES!r} — l'invariant n'est plus vérifié par personne.")
    assert rang_pivot_declares < rang_repli_roster


def test_l_audit_de_collecte_non_publiee_reste_arme():
    """Ce qui rend le saut légitime plutôt que décrété (#511/#518).

    Si un profil roster avait été collecté sans être publié — l'hypothèse sur
    laquelle B repose étant que les shards n'ont rien collecté non plus —, cet
    audit bloquerait le commit en nommant les slugs. Le retirer, ou lui câbler
    une tolérance, transformerait ce saut en trou silencieux.
    """
    code = _sans_commentaires(_bloc_job("merge-and-pivot"))
    assert "src/audit_collecte_non_publiee.py" in code
    assert "--autoriser-roster-incomplet" not in code


# ---------------------------------------------------------------------------
# Le producteur : pas d'artifact vide sur une suspension totale
# ---------------------------------------------------------------------------

def test_le_producteur_ne_publie_pas_d_artifact_sans_roster():
    """Un artifact ABSENT et un artifact VIDE ne se lisent pas pareil.

    Sur une suspension totale il n'y a aucun fichier à publier. Sans `if:` sur
    le step, il faudrait relâcher `if-no-files-found: error` en `ignore` — et
    les consommateurs téléchargeraient alors un artifact vide avec succès,
    transformant « roster absent » en « roster de 0 candidat », c'est-à-dire
    l'incident de #511. Un artifact absent, lui, fait tomber les consommateurs
    sur leur repli.
    """
    step = _step_contenant("prepare-roster-matrix", "name: roster-candidats")
    assert "if-no-files-found: error" in step
    assert "if:" in step, (
        "l'artifact roster est publié inconditionnellement : sur une suspension "
        "totale, `if-no-files-found: error` ferait rougir le job (#524).")
    assert "steps.roster.outputs.ecrit == 'true'" in step, step
