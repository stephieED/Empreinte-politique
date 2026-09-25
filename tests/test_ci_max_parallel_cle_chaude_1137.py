"""#1137 — `extract-an` ne sérialise ses shards que si la chaîne de cache sert.

Le mécanisme, en une phrase
---------------------------
`max-parallel: 1` sur `extract-an` est conservé par #412 pour une seule raison :
les shards se passent le cache AN de proche en proche, le premier écrivant la
clé de la semaine et les suivants faisant un *exact key hit*. Cet argument ne
vaut **que sur une clé froide** — une fois l'entrée écrite, chaque shard fait un
hit exact dès le premier et la chaîne ne transmet plus rien. C'est exactement ce
que #467 a constaté sur la matrice roster, ouverte à 4 pour cette raison.

`prepare-an-matrix` sonde donc la clé (`lookup-only: true`) et publie
`cache_chaud` ; `extract-an` en tire son `max-parallel`.

Pourquoi ce fichier de tests existe
-----------------------------------
Parce que le mécanisme **échoue en silence**. Son repli est l'état d'avant, la
sérialisation : une sonde qui se trompe ne casse aucun run, ne lève aucune
alerte, et coûte simplement les ~23 minutes qu'elle devait faire gagner. Trois
façons de se tromper, chacune tenue par un test ci-dessous :

1. le `path:` de la sonde diverge de celui d'`extract-an` — la *version* d'une
   entrée de cache est un hachage du `path`, donc la sonde ne trouve plus rien
   et répond « froid » pour toujours ;
2. sa **clé** diverge de celle que les shards restaurent ;
3. `restore-keys` s'y glisse — le repli par préfixe sert une entrée d'une autre
   semaine, et la sonde répondrait « chaud » sur une clé qui n'existe pas
   encore, cette fois dans le mauvais sens.

Les deux modes non sondés (`cold_start`, `collect_interventions`) sont un choix,
pas un oubli : le dernier test de ce fichier tient la raison écrite dans le YAML.

Volontairement sans PyYAML (absent de `requirements.txt`), comme
`tests/test_ci_cache_paths.py` : une lecture textuelle suffit, et c'est le TEXTE
des deux blocs `path:` qui décide de la version d'une entrée de cache — pas
l'objet Python qu'un parseur en tirerait.
"""

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"

# La valeur ouverte sur une clé chaude. 4, comme la matrice roster (#467) : elle
# n'a pas été re-arbitrée, et l'aligner évite d'avoir deux plafonds à défendre.
PARALLELISME_ATTENDU = 4


def _yaml() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def _job(nom: str) -> str:
    """Le bloc d'un job, de son en-tête au prochain en-tête de même indentation."""
    texte = _yaml()
    debut = re.search(rf"^  {re.escape(nom)}:\s*$", texte, re.MULTILINE)
    assert debut, f"Job `{nom}` introuvable dans {WORKFLOW.name}."
    suite = re.search(r"^  [a-z][a-z0-9-]*:\s*$", texte[debut.end():], re.MULTILINE)
    return texte[debut.end(): debut.end() + suite.start()] if suite else texte[debut.end():]


def _bloc_path(bloc: str) -> list[str]:
    """Les lignes d'un `path: |`, nettoyées de leur indentation."""
    trouve = re.search(r"\n(\s+)path: \|\n((?:\1  .*\n)+)", bloc)
    if not trouve:
        return []
    return [ligne.strip() for ligne in trouve.group(2).strip().split("\n")]


def _sans_commentaires(bloc: str) -> str:
    """Le YAML débarrassé de ses lignes de commentaire.

    Ce fichier en a besoin pour une raison qui est elle-même un piège : les
    commentaires de `generate-data.yml` CITENT les mécanismes qu'ils
    expliquent — « un `pip install` entamerait le timeout » — et une recherche
    textuelle naïve y trouve ce qu'elle est censée interdire. Un test qui
    échoue sur sa propre justification n'est pas un test, c'est un piège à
    rédaction.
    """
    return "\n".join(
        ligne for ligne in bloc.split("\n") if not ligne.lstrip().startswith("#")
    )


def _steps_de_cache(bloc: str) -> list[str]:
    """Les steps `actions/cache*` d'un job, chacun avec son contenu."""
    steps = re.split(r"\n      - (?=uses:|name:)", bloc)
    return [s for s in steps if "actions/cache" in s.split("\n")[0]]


# ---------------------------------------------------------------------------
# Garde-fou du garde-fou : les extracteurs ci-dessus trouvent réellement
# quelque chose. Sans lui, tous les tests de ce fichier passeraient sur un
# workflow vide — le motif qui ne cherche rien ne trouve jamais de défaut.
# ---------------------------------------------------------------------------


def test_les_extracteurs_de_ce_fichier_lisent_bien_le_workflow():
    assert len(_job("prepare-an-matrix")) > 1000
    assert len(_job("extract-an")) > 1000
    sondes = _steps_de_cache(_job("prepare-an-matrix"))
    assert len(sondes) == 1, (
        f"{len(sondes)} step(s) de cache dans prepare-an-matrix : ce job n'en a "
        "qu'un, la sonde de #1137. Les tests ci-dessous désignent « le » step de "
        "cache de ce job et deviendraient ambigus."
    )
    assert _bloc_path(sondes[0]), "La sonde n'a pas de bloc `path:` lisible."
    # Le retrait des commentaires enlève des lignes, et RIEN QUE des lignes de
    # commentaire : sans cette vérification, une expression trop gourmande
    # viderait les blocs et tous les tests « X n'est pas présent » passeraient.
    bloc = _job("prepare-an-matrix")
    nu = _sans_commentaires(bloc)
    assert "#" in bloc and len(nu) < len(bloc)
    assert "- name: Parallélisme d'extract-an pour ce run (#1137)" in nu
    assert "lookup-only: true" in nu


# ---------------------------------------------------------------------------
# 1. Le `max-parallel` est conditionnel, et son repli est la sérialisation
# ---------------------------------------------------------------------------


def _expression_max_parallel() -> str:
    trouve = re.search(r"\n      max-parallel: (.+)\n", _job("extract-an"))
    assert trouve, "`extract-an` n'a plus de `max-parallel:`."
    return trouve.group(1).strip()


def test_extract_an_lit_le_parallelisme_dans_un_needs():
    """`jobs.<id>.strategy` n'accepte que les contextes `github`, `needs`,
    `vars` et `inputs` : une condition tirée d'un `steps` du même job ne
    s'évalue pas, et le workflow entier devient invalide."""
    expression = _expression_max_parallel()
    assert "needs.prepare-an-matrix.outputs.cache_chaud" in expression, (
        f"`max-parallel: {expression}` ne lit plus la sonde de prepare-an-matrix "
        "(#1137). Si la sérialisation est redevenue inconditionnelle, c'est une "
        "décision à écrire, pas un retour à l'état par défaut."
    )
    assert "steps." not in expression, (
        "`max-parallel` lit un `steps.` : ce contexte n'existe pas dans "
        "`strategy`, et le workflow entier serait refusé au démarrage du run."
    )


def test_le_repli_est_la_serialisation():
    """Tout ce qui n'est pas un « oui » franc de la sonde doit sérialiser :
    sortie vide, job amont en échec, mode non sondé. Le mécanisme retombe sur
    l'état d'avant #1137, jamais sur un parallélisme par défaut."""
    expression = _expression_max_parallel()
    trouve = re.search(
        r"needs\.prepare-an-matrix\.outputs\.cache_chaud\s*==\s*'true'\s*&&\s*(\d+)\s*\|\|\s*(\d+)",
        expression,
    )
    assert trouve, (
        f"`max-parallel: {expression}` n'a plus la forme « chaud && N || 1 ». "
        "Une autre forme peut être juste, mais elle doit dire aussi clairement "
        "ce qui arrive quand la sonde ne répond pas."
    )
    chaud, froid = int(trouve.group(1)), int(trouve.group(2))
    assert froid == 1, (
        f"Le repli est {froid} : sur une clé FROIDE, {froid} shards "
        "retéléchargeraient chacun les dumps AN au lieu de se passer le cache "
        "que le premier écrit (#412, #424)."
    )
    assert chaud == PARALLELISME_ATTENDU


def test_prepare_an_matrix_publie_la_sonde():
    bloc = _job("prepare-an-matrix")
    assert re.search(r"\n      cache_chaud: \$\{\{ steps\.\w+\.outputs\.\w+ \}\}", bloc), (
        "`prepare-an-matrix` ne publie plus d'output `cache_chaud` : le "
        "`max-parallel` d'extract-an lirait une chaîne vide et sérialiserait "
        "indéfiniment, sans qu'aucun run ne le signale."
    )


# ---------------------------------------------------------------------------
# 2. La sonde interroge la MÊME entrée que celle que les shards restaurent
# ---------------------------------------------------------------------------


def test_la_sonde_et_extract_an_ont_le_meme_path():
    """La *version* d'une entrée de cache est un hachage du `path:`. Un `path`
    divergent ne rend pas une mauvaise réponse : il ne trouve rien, jamais."""
    sonde = _bloc_path(_steps_de_cache(_job("prepare-an-matrix"))[0])
    restore_an = _bloc_path(_steps_de_cache(_job("extract-an"))[0])
    assert sonde == restore_an, (
        "Le `path:` de la sonde a divergé de celui d'extract-an :\n"
        f"  sonde     : {sonde}\n"
        f"  extract-an: {restore_an}\n"
        "La sonde répondrait « froid » à tous les runs, et les 31 shards "
        "resteraient en série en silence (#1137)."
    )


def test_la_sonde_et_extract_an_ont_la_meme_cle():
    """En mode par défaut, la clé d'`extract-an` est la semaine ISO nue : c'est
    exactement celle que la sonde doit poser. Le suffixe de complétude (#550)
    n'appartient qu'au mode interventions, que la sonde ne couvre pas."""
    sonde = _steps_de_cache(_job("prepare-an-matrix"))[0]
    cle_sonde = re.search(r"\n\s+key: (.+)\n", sonde)
    assert cle_sonde, "La sonde n'a plus de `key:`."
    assert cle_sonde.group(1).strip() == (
        "public-data-cache-an-${{ steps.week.outputs.week }}"
    ), (
        f"Clé de la sonde : {cle_sonde.group(1).strip()}. Elle doit être celle "
        "qu'extract-an restaure en mode par défaut, sans quoi la réponse porte "
        "sur une autre entrée que celle dont dépend la chaîne de réchauffement."
    )


def test_la_sonde_ne_se_replie_sur_aucun_prefixe():
    """`restore-keys` servirait l'entrée de la semaine PRÉCÉDENTE (#555 : le
    préfixe nu traverse les semaines). La sonde répondrait « chaud » sur une clé
    qui n'existe pas encore, les shards partiraient à 4 sur un cache froid et
    retéléchargeraient chacun les dumps AN — le défaut de #424, retrouvé par
    l'autre bout."""
    sonde = _steps_de_cache(_job("prepare-an-matrix"))[0]
    assert "restore-keys" not in sonde, (
        "La sonde a un `restore-keys:` : elle ne répond plus à la question "
        "« la clé exacte existe-t-elle ? » mais à « une entrée approchante "
        "existe-t-elle ? »."
    )
    assert "lookup-only: true" in sonde, (
        "La sonde a perdu son `lookup-only: true` : elle EXTRAIT désormais des "
        "centaines de Mo dans un job à `timeout-minutes: 5` qui n'en lit aucun "
        "(#674)."
    )


# ---------------------------------------------------------------------------
# 3. Les deux modes non sondés sont un choix, et il tient à une contrainte réelle
# ---------------------------------------------------------------------------


def test_la_sonde_ne_tourne_ni_en_cold_start_ni_en_mode_interventions():
    """`cold_start` : chaque shard repart des archives, on ne multiplie pas par
    4 ce qu'on demande à data.assemblee-nationale.fr ce jour-là.
    `collect_interventions` : la clé porte l'empreinte de complétude (#550), que
    seul `src/cache_an_empreinte.py` sait calculer — et il importe `requests`,
    que ce job n'installe pas (test suivant)."""
    sonde = _steps_de_cache(_job("prepare-an-matrix"))[0]
    condition = re.search(r"\n\s+if: (.+)\n", sonde)
    assert condition, "La sonde n'a plus de `if:` : elle tournerait dans tous les modes."
    texte = condition.group(1)
    assert "!inputs.cold_start" in texte and "!inputs.collect_interventions" in texte, (
        f"Condition de la sonde : {texte}. Les deux modes doivent y rester "
        "exclus tant que ce job ne peut pas calculer l'empreinte de complétude."
    )


def test_prepare_an_matrix_n_installe_toujours_aucune_dependance():
    """La raison pour laquelle le mode interventions n'est pas sondé. Ce job
    tourne en `python3` système, sans dépendance, sous `timeout-minutes: 5` —
    et #674 l'a déjà vu mourir dans `actions/checkout`. Le jour où il gagne un
    `pip install`, l'empreinte de #550 devient calculable ici et la sonde peut
    couvrir les deux modes : ce test est là pour que ce jour-là se remarque."""
    bloc = _sans_commentaires(_job("prepare-an-matrix"))
    assert "setup-python" not in bloc and "pip install" not in bloc, (
        "`prepare-an-matrix` installe désormais des dépendances. Deux "
        "conséquences à trancher : son budget de 5 minutes (#674), et le fait "
        "que la sonde de #1137 pourrait maintenant couvrir le mode "
        "`collect_interventions` en calculant l'empreinte de #550."
    )


# ---------------------------------------------------------------------------
# 4. L'avertissement de temps mur dit la cadence réelle
# ---------------------------------------------------------------------------


def test_l_avertissement_de_temps_mur_suit_le_parallelisme_du_run():
    """Même règle qu'à AN_TIMEOUT_MINUTES (#498) : annoncer un temps mur série
    pendant qu'un run tourne à 4 rendrait l'avertissement faux au moment précis
    où il sert."""
    bloc = _job("prepare-an-matrix")
    trouve = re.search(
        r"AN_MAX_PARALLEL: \$\{\{ steps\.\w+\.outputs\.\w+ == 'true' && (\d+) \|\| (\d+) \}\}",
        bloc,
    )
    assert trouve, (
        "`prepare-an-matrix` n'expose plus AN_MAX_PARALLEL : son avertissement "
        "de temps mur retomberait sur une cadence en dur, désolidarisée du "
        "`max-parallel` réel d'extract-an."
    )
    expression = _expression_max_parallel()
    nombres = re.findall(r"\b(\d+)\b", expression)
    assert (trouve.group(1), trouve.group(2)) == tuple(nombres), (
        f"AN_MAX_PARALLEL dit ({trouve.group(1)}, {trouve.group(2)}) là où "
        f"`max-parallel` dit {nombres} : l'avertissement annoncerait un temps "
        "mur que le run ne prendra pas."
    )
    assert "COUNT * AN_TIMEOUT_MINUTES" not in bloc, (
        "Le temps mur se calcule encore comme si tous les shards se suivaient : "
        "il doit passer par le nombre de VAGUES."
    )
