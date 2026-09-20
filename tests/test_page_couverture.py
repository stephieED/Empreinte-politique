"""« Ce que contient ce corpus » — la page commune aux fiches (/couverture).

CE QU'ELLE RÈGLE. Les deux tiers de « ce qu'on n'a pas pu lire » étaient
recopiés à l'identique sur chaque fiche : les bornes de source, les périodes que
la source ne publie pas, les institutions dont nous ne montrons rien. Rien de
tout cela ne parle du candidat affiché. La page les dit UNE FOIS, pour les trois
populations publiées — candidats, gouvernements, groupes — et la fiche ne garde
que ce qui est vrai de cette personne-là.

CE QUE CES GARDE-FOUS PROTÈGENT est éditorial, pas graphique. Quatre pentes,
toutes tentantes pour une session qui « améliorerait » la figure :

1. **Dédoubler la frise par origine.** Trois fiches peuvent porter le même fait
   sur la même période. Elles vivent dans le MÊME rail, superposées, et la
   teinte dit d'où vient le trait. Une piste par origine mettrait trois lignes
   là où une suffit, et ferait lire trois faits là où il y en a un.
2. **Écrire un chiffre dans le JSX.** Effectifs, bornes, noms des fiches où une
   liste manque : tout est mesuré au build. Un chiffre recopié à la main est un
   chiffre qui aura vieilli au run suivant — la méthodologie en porte déjà
   (« 1 160 positions »), et c'est exactement ce qu'il ne faut pas reproduire.
3. **Séparer le parlementaire du gouvernemental sur un intitulé.** Chaque liste
   porte son marqueur, publié par la source : `categorie`, `role`, `fonction`.
   Aucun n'est reconstruit depuis un libellé (#639).
4. **Confondre les deux absences.** Une fiche dont la liste est vide parce que
   son mandat précède la borne n'est pas une fiche où la donnée manque sans
   cause connue. Deux colonnes, jamais un total (§2 règle 5).

CE QU'ILS NE COUVRENT PAS, et il faut le dire (§2 règle 5) : aucun composant
React n'est rendu ici, et AUCUN TEST NE LIT `pivot_data/` — la CI monte le dépôt
en sparse-checkout sans le corpus (AGENTS.md §3b). Le rendu en navigateur — repli
des champs, alignement de l'axe sur les rails, défilement horizontal du tableau —
a été vérifié hors dépôt sur le paquet construit, à 1 440, 1 100 et 700 px.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale"
SRC = UI / "src"
GENERATEUR = UI / "scripts" / "couverture-corpus.mjs"
SYNC = UI / "scripts" / "sync-data.mjs"
PAGE = SRC / "pages" / "CoveragePage.jsx"
FRISE = SRC / "components" / "FriseCouverture.jsx"
FRISE_CSS = SRC / "components" / "FriseCouverture.css"
APP = SRC / "App.jsx"


def _sans_commentaires(source: str) -> str:
    """Retire les commentaires : une règle citée en commentaire n'est pas une
    règle appliquée, et un test qui les lit se félicite d'une intention."""
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"^\s*//.*$", "", source, flags=re.MULTILINE)


@pytest.fixture(scope="module")
def generateur() -> str:
    return _sans_commentaires(GENERATEUR.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def frise() -> str:
    return _sans_commentaires(FRISE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def page() -> str:
    return _sans_commentaires(PAGE.read_text(encoding="utf-8"))


# ── Les fichiers existent, et sont branchés ─────────────────────────────────


def test_les_quatre_fichiers_de_la_page_existent() -> None:
    for chemin in (GENERATEUR, PAGE, FRISE, FRISE_CSS):
        assert chemin.exists(), f"{chemin.relative_to(RACINE)} manquant"


def test_la_route_existe_et_l_accueil_y_mene() -> None:
    """Une page qu'aucun lien n'atteint n'est pas publiée."""
    app = APP.read_text(encoding="utf-8")
    # Depuis #951 la page vit sur /sources ; /couverture y redirige, ancre comprise.
    assert '<Route path="/sources" element={<CoveragePage />} />' in app
    assert '<Route path="/couverture" element={<RedirectionCouverture />} />' in app
    assert "pathname: '/sources', hash" in app

    # Depuis la forme C de l'accueil (#951), la page s'atteint par la barre des
    # pages du site, que l'accueil porte comme toutes les pages.
    nav = (SRC / "components" / "NavigationSite.jsx").read_text(encoding="utf-8")
    assert "vers: '/sources'" in nav, "la barre ne mène pas à la page"
    accueil = (SRC / "pages" / "LandingPage.jsx").read_text(encoding="utf-8")
    assert "<EnTeteSite />" in accueil, "l'accueil ne porte pas la barre"


def test_le_build_produit_la_couverture(generateur: str) -> None:
    """Le fichier est calculé par `sync-data`, pas versionné : `public/data/`
    est ignoré par git, et une projection commitée serait périmée au run
    suivant."""
    sync = SYNC.read_text(encoding="utf-8")
    assert "construireCouverture" in sync
    assert "couverture.json" in sync
    assert "export function construireCouverture" in generateur

    ignore = (RACINE / ".gitignore").read_text(encoding="utf-8")
    assert "web/UI_finale/public/data/" in ignore


# ── Règle 1 : une piste, des couches — jamais une piste par origine ─────────


def test_les_origines_se_superposent_dans_un_seul_rail(frise: str) -> None:
    """Un rail contient N couches ; il n'existe pas de rail par origine.

    LE COMPTE A ÉTÉ REMPLACÉ PAR L'INTENTION le 15/09/2026. Ce test exigeait
    UNE seule occurrence de ``className="fc-rail"``, ce qui tenait tant que le
    composant n'avait qu'une façon de dessiner un rail. #885 en ajoute une
    seconde, qui n'est pas une origine : une liste que la SOURCE ne publie pas
    — les quatre listes sénatoriales — porte une hachure pleine et aucune
    couche. Compter les occurrences interdisait ce cas sans rapport avec la
    règle qu'il protège.

    Ce qui est vérifié reste donc : les couches d'une même piste se superposent,
    et aucun rail n'est construit DANS la boucle des origines.
    """
    assert "couches.map" in frise
    boucle = re.search(r"couches\.map\(\(c\) => \((.*?)\n      \)\)", frise, re.DOTALL)
    assert boucle, "la boucle des couches a changé de forme — relire avant d'adapter"
    assert 'className="fc-rail"' not in boucle.group(1), (
        "un rail construit par origine est exactement la pente que la figure refuse"
    )
    feuille = FRISE_CSS.read_text(encoding="utf-8")
    # Une seule encre depuis le 11/09/2026 (frise-couverture-donnees-collectees-328) :
    # la fiche d'origine n'est plus une teinte, donc plus de mélange à voir.
    assert "--pop-" not in feuille and "fc-couche--" not in frise, (
        "les faits portés sont une seule catégorie, « Données collectées »"
    )
    for inst in ("AN", "gouvernement", "PE"):
        assert f".fc-groupe--{inst} {{ --fc-inst:" in feuille, f"la teinte de l'institution {inst} manque"
    assert "Données collectées" in frise
    assert "position: absolute" in feuille and "inset: 0" in feuille


def test_un_champ_donne_une_seule_ligne(generateur: str) -> None:
    """Deux origines qui mesurent la même chose tombent sur la même ligne : le
    champ porte ses `couches`, il n'est pas répété par origine."""
    assert "const champ = (titre, apports)" in generateur
    assert "couches: apports" in generateur


# ── Règle 2 : aucun chiffre n'est écrit à la main ───────────────────────────


CHIFFRE_ECRIT = re.compile(r"(?<![\w#-])\d{3,}(?![\w%])")


@pytest.mark.parametrize("fichier", ["CoveragePage.jsx", "FriseCouverture.jsx"])
def test_aucun_effectif_n_est_ecrit_dans_le_jsx(fichier: str) -> None:
    """Les seuls nombres tolérés sont des repères de mise en page (années de
    graduation, seuils), jamais un effectif du corpus."""
    chemin = PAGE if fichier == "CoveragePage.jsx" else FRISE
    source = _sans_commentaires(chemin.read_text(encoding="utf-8"))
    autorises = {"2000", "2005", "2010", "2015", "2020", "2025", "100", "640", "108", "262"}
    trouves = {m for m in CHIFFRE_ECRIT.findall(source) if m not in autorises}
    assert not trouves, (
        f"{fichier} porte des nombres écrits à la main : {sorted(trouves)} — "
        "tout effectif vient de couverture.json, mesuré au build"
    )


def test_les_reperes_de_tete_viennent_des_donnees(page: str) -> None:
    for cle in ("reperes.fichesPubliees", "reperes.candidats", "reperes.gouvernements", "reperes.groupes"):
        assert cle in page, f"{cle} n'est pas lu depuis les données"


# ── Règle 3 : la séparation est lue, jamais déduite d'un intitulé ───────────


def test_les_trois_marqueurs_sont_des_champs_publies(generateur: str) -> None:
    """Un mandat, un texte, une intervention : chacun porte le marqueur que la
    source publie. Aucun n'est reconstruit depuis un libellé (#639)."""
    assert "m?.categorie === 'fonction_gouvernementale'" in generateur
    assert "t?.role === 'initiateur_projet_de_loi'" in generateur
    assert "i.fonction" in generateur, "la qualité de l'orateur vient du compte rendu"


def test_le_senat_et_le_parlement_europeen_sortent_de_la_piste_assemblee() -> None:
    """Ni l'un ni l'autre n'est de l'activité à l'Assemblée : les ranger sous
    « Assemblée nationale » dirait une activité qui n'y a pas eu lieu.

    CE TEST A ÉTÉ RÉÉCRIT LE 15/09/2026, et il garde la mémoire de pourquoi.
    Il vérifiait la chaîne ``const HORS_ASSEMBLEE = new Set(['Senat', 'PE'])``,
    c'est-à-dire l'écriture d'alors — et il est resté vert pendant que 126
    appartenances sénatoriales étaient comptées sous l'Assemblée. Le défaut
    tenait à ce que ce ``Set`` ne teste que ``chambre``, que seul le mandat
    électif porte : commissions, délégations et groupes d'amitié ont
    ``chambre: null`` et ne se reconnaissent qu'à ``categorie_source``.

    Il teste donc le COMPORTEMENT, sur les deux formes que le corpus porte
    réellement. Une écriture qui retomberait sur ``chambre`` seule le fait
    rougir ; une réécriture du filtre qui garde l'intention le laisse vert.
    """
    import json
    import shutil
    import subprocess

    if shutil.which("node") is None:
        pytest.skip("node absent")

    script = f"""
    const {{ estMandatAssemblee, estMandatSenatorial }} =
      await import({json.dumps(GENERATEUR.as_uri())});
    const cas = [
      // Le mandat électif : il porte `chambre`.
      [{{ categorie: 'mandat_electif', chambre: 'Senat', categorie_source: 'senat' }}, false],
      // L'ORGANE sénatorial : `chambre` absente, seul `categorie_source` le dit.
      [{{ categorie: 'commission', chambre: null, categorie_source: 'senat' }}, false],
      [{{ categorie: 'groupe_amitie', chambre: null, categorie_source: 'senat' }}, false],
      // Les mêmes deux formes côté européen, déjà couvertes depuis le 11/09/2026.
      [{{ categorie: 'mandat_electif', chambre: 'PE', categorie_source: 'europarl' }}, false],
      [{{ categorie: 'commission', chambre: null, categorie_source: 'europarl' }}, false],
      // Et l'Assemblée, qui doit rester vraie dans ses deux formes.
      [{{ categorie: 'mandat_electif', chambre: 'AN', categorie_source: 'an' }}, true],
      [{{ categorie: 'commission', chambre: null, categorie_source: 'an' }}, true],
    ];
    const echecs = cas
      .map(([m, attendu], i) => (estMandatAssemblee(m) === attendu ? null : i))
      .filter((x) => x !== null);
    const senatorial = [
      estMandatSenatorial({{ chambre: 'Senat' }}),
      estMandatSenatorial({{ chambre: null, categorie_source: 'senat' }}),
      estMandatSenatorial({{ chambre: 'AN', categorie_source: 'an' }}),
    ];
    console.log(JSON.stringify({{ echecs, senatorial }}));
    """
    res = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True, text=True, check=False,
    )
    assert res.returncode == 0, res.stderr
    sortie = json.loads(res.stdout.strip().splitlines()[-1])
    assert sortie["echecs"] == [], (
        f"cas mal rattachés (index) : {sortie['echecs']} — un organe sans "
        "`chambre` doit être reconnu par `categorie_source`"
    )
    assert sortie["senatorial"] == [True, True, False]


def _corpus_minimal(tmp_path: Path) -> Path:
    """Une fiche de candidat qui porte un vote de chaque institution, et les
    deux `couverture` que la collecte écrit : la borne de l'Assemblée, et la
    `portee` européenne, qui va de la première à la dernière donnée."""
    import json

    profils = tmp_path / "pivot_data" / "profiles"
    profils.mkdir(parents=True)
    (tmp_path / "pivot_data" / "scrutins.json").write_text(json.dumps({"scrutins": [
        {"id": "an:16:1", "date": "2023-02-01", "source_url": "https://www.assemblee-nationale.fr/s1"},
    ]}), encoding="utf-8")
    fiche = {
        "id": "x", "nom": "X", "meta": {"provenance": "candidat_declare", "genere_le": "2026-09-11"},
        "mandats": [
            {"categorie": "mandat_electif", "chambre": "AN", "debut": "2022-06-22", "categorie_source": "an"},
            {"categorie": "commission", "debut": "2010-01-01", "categorie_source": "europarl"},
        ],
        "votes": [
            {"scrutin_id": "an:16:1", "position": "pour"},
            {"scrutin_id": None, "position": "contre", "scrutin_non_resolu": {
                "institution": "parlement_europeen", "date": "2005-03-10",
                "reference_dossier": "2004/0001(COD)", "source_url": "https://www.europarl.europa.eu/v"}},
        ],
        "interventions": [
            {"date": "2006-01-01", "sujet": "S", "source": {"institution": "parlement_europeen"}},
        ],
        "couverture": {"votes": [
            {"etat": "couvert", "portee": {"debut": "2012-06-20"}},
            {"etat": "couvert", "source": "parlement_europeen", "portee": {"debut": "2004-09-15", "fin": "2017-05-17"}},
        ]},
    }
    (profils / "x.pivot.json").write_text(json.dumps(fiche), encoding="utf-8")
    return tmp_path


def test_le_parlement_europeen_a_ses_listes_et_ne_deplace_pas_la_borne_de_l_assemblee(tmp_path: Path) -> None:
    """Mesuré le 11/09/2026 sur les 30 fiches de candidats publiées : 160 mandats, 383 textes et 5 329 interventions
    européens comptés sous l'Assemblée, 11 013 votes et 7 303 amendements nulle
    part, et la `portee` européenne d'une fiche prise pour la borne des votes de
    l'Assemblée — 2004 au lieu de 2012. Rien de tout cela ne lève d'erreur."""
    import json
    import shutil
    import subprocess

    if shutil.which("node") is None:
        pytest.skip("node absent")
    racine = _corpus_minimal(tmp_path)
    script = f"""
      const m = await import({json.dumps(GENERATEUR.as_uri())});
      const c = m.construireCouverture({{ repoRoot: {json.dumps(str(racine))} }});
      const total = (inst, cle) => c.hierarchie.find((i) => i.cle === inst)
        .pistes.find((p) => p.cle === cle).couches.reduce((s, x) => s + x.total, 0);
      process.stdout.write(JSON.stringify({{
        borne: c.bornes.votes,
        votesAN: total('AN', 'votes'), votesPE: total('PE', 'votes'),
        mandatsAN: total('AN', 'mandats'), mandatsPE: total('PE', 'mandats'),
        parolesAN: total('AN', 'interventions'), parolesPE: total('PE', 'interventions'),
        bornesPE: Object.fromEntries(c.hierarchie.find((i) => i.cle === 'PE').pistes.map((p) => [p.cle, p.borne])),
        finPE: c.hierarchie.find((i) => i.cle === 'PE').pistes.find((p) => p.cle === 'votes').finSource,
      }}));
    """
    res = subprocess.run(["node", "--input-type=module", "-e", script],
                         capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    assert json.loads(res.stdout) == {
        "borne": "2012-06-20",
        "votesAN": 1, "votesPE": 1,
        "mandatsAN": 1, "mandatsPE": 1,
        "parolesAN": 0, "parolesPE": 1,
        "bornesPE": {"mandats": None, "votes": "2004-09-15", "amendements": "2008-02-01",
                     "textes_portes": None, "interventions": None},
        "finPE": "2017-05-17",
    }


def test_le_parlement_europeen_n_est_plus_une_ligne_non_collectee(frise: str) -> None:
    """Une institution dont le dépôt porte les listes vit dans la hiérarchie.

    ARBITRAGE RENVERSÉ LE 15/09/2026, et ce test en garde la mémoire. Il
    exigeait ``cle: 'Senat'`` dans `SANS_ACTIVITE`, au motif que « le Sénat
    garde sa ligne — mandat publié, activité hors périmètre ». C'était vrai
    tant que #528 le tenait dehors.

    #885 collecte ses appartenances : 133 sur 2 candidats déclarés. Il rejoint
    donc la hiérarchie avec ses cinq listes, comme le Parlement européen l'a
    fait le 11/09. Sa ligne d'avant portait « 7 · 2 candidats » — les sept
    mandats électifs seuls, les 126 organes n'étant comptés nulle part.

    Les mandats locaux restent, eux, dans `SANS_ACTIVITE` : ils ne sont pas une
    institution, et n'ont qu'une liste. Depuis le 16/09/2026 leur ligne dessine
    ce que le Répertoire national des élus publie, au lieu de « aucune source ».
    """
    assert "cle: 'PE'" not in frise, "le Parlement européen a ses listes : il vit dans la hiérarchie"
    assert "cle: 'Senat'" not in frise, (
        "le Sénat a ses cinq listes dans la hiérarchie depuis #885 — l'y remettre "
        "en ligne unique recompterait 7 mandats sur 133"
    )
    assert "cle: 'local'" in frise, "les mandats locaux gardent leur ligne unique"


# ── Règle 4 : deux absences, deux colonnes ──────────────────────────────────


def test_le_manquant_hors_borne_ne_se_confond_pas_avec_un_trou(page: str, generateur: str) -> None:
    assert "l.horsBorne" in page and "l.trous" in page, "les deux colonnes doivent exister"
    assert "horsBorne:" in generateur and "trous:" in generateur


def test_le_denominateur_est_le_nombre_de_fiches_qui_ont_siege(generateur: str, page: str) -> None:
    """Une fiche sans mandat à l'Assemblée n'a pas de vote à porter : sa liste
    vide est un fait sur elle, pas un trou. Le dénominateur l'exclut."""
    assert "siege: siegeants.length" in generateur
    assert "couverture.siege" in page


def test_la_borne_est_celle_que_la_source_declare(generateur: str) -> None:
    """Prendre le minimum des dates rencontrées rendrait la borne tautologique :
    la hachure s'arrêterait là où la première donnée commence, et ne dirait plus
    rien. Elle vient du bloc `couverture` du profil."""
    assert "function bornesPubliees" in generateur
    assert "e.etat !== 'couvert' && e.etat !== 'fait_etabli'" in generateur


# ── Ce que la fiche ne répète plus ──────────────────────────────────────────


def test_les_deux_mentions_de_fiche_renvoient_a_la_methodologie() -> None:
    """« Ce qu'il a voté » et « Ce qu'il a dit » gardent leurs chiffres — vrais
    de cette personne — et renvoient le pourquoi, identique sur les 30 fiches, à
    la méthodologie."""
    votes = (SRC / "components" / "VotesParPeriode.jsx").read_text(encoding="utf-8")
    paroles = (SRC / "components" / "ParolesParPeriode.jsx").read_text(encoding="utf-8")
    assert 'to="/methodologie#votes"' in votes
    assert 'to="/methodologie#interventions"' in paroles
    for source in (votes, paroles):
        assert "Ce que cette figure ne sait pas" in source, (
            "le chiffre reste sous la figure ; c'est le pourquoi qui déménage"
        )


# ── L'accueil : une borne par institution, et les fiches hors couverture ─────


def test_l_accueil_dit_depuis_quand_et_nomme_sans_rien_ecrire_a_la_main(tmp_path: Path) -> None:
    """Relecture du 11/09/2026 : une borne par institution, et les fiches dont
    une partie de la carrière est hors couverture. Tout est calculé au build ;
    une liste recopiée n'accueillerait pas le prochain candidat déclaré."""
    import json
    import shutil
    import subprocess

    if shutil.which("node") is None:
        pytest.skip("node absent")
    racine = _corpus_minimal(tmp_path)
    profils = racine / "pivot_data" / "profiles"
    (profils / "s.pivot.json").write_text(json.dumps({
        "id": "s", "nom": "Sénatrice Exemple", "meta": {"provenance": "candidat_declare"},
        "mandats": [{"categorie": "mandat_electif", "chambre": "Senat", "debut": "2004-09-26"}],
    }), encoding="utf-8")
    (profils / "z.pivot.json").write_text(json.dumps({
        "id": "z", "nom": "Zoé Sansmandat", "meta": {"provenance": "candidat_declare"}, "mandats": [],
    }), encoding="utf-8")
    # Relue avec un mandat antérieur ; relue sans ; non relue (`null`) : seule
    # la première est nommée — absent n'est pas « aucun ».
    for slug, anterieurs in (("r", [{"institution": "assemblee_nationale", "debut": "1988-06-13"}]),
                             ("v", []), ("n", None)):
        (profils / f"{slug}.pivot.json").write_text(json.dumps({
            "id": slug, "nom": f"Nom {slug.upper()}", "meta": {"provenance": "candidat_declare"},
            "mandats": [{"categorie": "mandat_electif", "chambre": "AN", "debut": "2002-06-19"}],
            "mandats_anterieurs": anterieurs,
        }), encoding="utf-8")
    script = f"""
      const m = await import({json.dumps(GENERATEUR.as_uri())});
      const c = m.construireCouverture({{ repoRoot: {json.dumps(str(racine))} }});
      const i = Object.fromEntries(c.accueil.institutions.map((x) => [x.cle, x]));
      process.stdout.write(JSON.stringify({{
        an: i.AN.hachureJusqua, pe: i.PE.hachureJusqua, peDebut: i.PE.debut,
        gouvBorne: c.hierarchie.find((x) => x.cle === 'gouvernement').pistes.find((p) => p.cle === 'mandats').borne,
        anterieurs: c.accueil.horsCouverture.anterieurs.map((p) => p.id),
        senat: c.accueil.horsCouverture.senat.map((p) => p.id),
        sansMandat: c.accueil.horsCouverture.sansMandat.map((p) => p.id),
      }}));
    """
    res = subprocess.run(["node", "--input-type=module", "-e", script],
                         capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    assert json.loads(res.stdout) == {
        # L'Assemblée déclare une borne sur chacune de ses listes ; le fixture
        # n'en déclare que pour les votes, donc aucune hachure d'institution.
        "an": None,
        # Les mandats européens n'ont pas de borne : la hachure ne s'affirme pas ;
        # le début est la borne des votes, antérieure à la première donnée.
        "pe": None, "peDebut": "2004-09-15",
        # #859 : la borne de l'AMO30 n'est plus prêtée aux fonctions gouvernementales.
        "gouvBorne": None,
        "anterieurs": ["r"], "senat": ["s"], "sansMandat": ["z"],
    }


def test_l_accueil_ne_montre_plus_de_fait_fictif_ni_sa_frise() -> None:
    """La frise simplifiée de l'accueil (`CouvertureAccueil`) est partie avec
    « Sources & fraîcheur » dans la forme C (#951) : la vraie frise est sur
    /sources. Le fait fictif de #328 ne revient pas pour autant."""
    accueil = (SRC / "pages" / "LandingPage.jsx").read_text(encoding="utf-8")
    assert "<FactDemo" not in accueil and not (SRC / "components" / "landing" / "FactDemo.jsx").exists()
    assert not (SRC / "components" / "landing" / "CouvertureAccueil.jsx").exists()
    assert "parcours politiques" in (SRC / "components" / "landing" / "Hero.jsx").read_text(encoding="utf-8")


def test_les_mandats_locaux_sont_comptes_avec_leur_borne(tmp_path: Path) -> None:
    """La ligne « Mandats locaux » disait « aucune source » alors que les fiches
    publiées en portaient 34 sur 14 candidats (16/09/2026). Le générateur les
    compte, et leur borne vient de la donnée — jamais d'une année écrite ici."""
    import json
    import shutil
    import subprocess

    if shutil.which("node") is None:
        pytest.skip("node absent")
    racine = _corpus_minimal(tmp_path)
    profils = racine / "pivot_data" / "profiles"
    (profils / "l.pivot.json").write_text(json.dumps({
        "id": "l", "nom": "Élue Locale", "meta": {"provenance": "candidat_declare"},
        "mandats": [{"categorie": "mandat_local", "debut": "2020-06-28"}],
        "mandats_locaux_couverture": {"appariement": "date_naissance", "borne_couverture": 2020},
    }), encoding="utf-8")
    script = f"""
      const m = await import({json.dumps(GENERATEUR.as_uri())});
      const c = m.construireCouverture({{ repoRoot: {json.dumps(str(racine))} }});
      process.stdout.write(JSON.stringify(c.institutions.find((i) => i.cle === 'local') || null));
    """
    res = subprocess.run(["node", "--input-type=module", "-e", script],
                         capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    local = json.loads(res.stdout)
    assert local == {"cle": "local", "candidats": 1, "mandats": 1, "debut": "2020-06-28", "fin": None, "borne": "2020-01-01"}
    frise = FRISE.read_text(encoding="utf-8")
    assert "fc-seg fc-seg--${x.cle}" in frise and "aucune donnée publiée avant le" in frise
    assert ".fc-seg--local" in FRISE_CSS.read_text(encoding="utf-8")
