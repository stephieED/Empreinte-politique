"""La cascade du versant européen — une porte, et la nomenclature de la source (#901).

CE QUE CE LOT RÈGLE. Les 694 textes portés européens des six fiches à mandat
européen n'atteignaient pas l'écran : `STADES_PUBLIES` est un ORDRE — un texte
est publié s'il a atteint au moins l'examen en commission — et aucune des seize
valeurs européennes n'y a de rang. Raphaël Glucksmann affichait « 0 publiés »
en portant 23 textes, dont 9 à un stade que la source publie.

CE QUE CES GARDE-FOUS PROTÈGENT est éditorial, pas graphique. Quatre pentes,
toutes tentantes pour une session qui « harmoniserait » les deux versants :

1. **Traduire un stade européen en stade français.** « Procedure completed »
   recouvre l'adoption comme l'échec — « Procedure rejected » est une procédure
   achevée elle aussi. Le rabattre sur `adopte` publierait un fait que la source
   n'établit pas (§2 règle 2).
2. **Les ordonner.** Les seize valeurs décrivent des ÉTATS, pas des degrés. Une
   échelle ferait dire à la figure qu'un texte « en attente du Conseil » est
   allé plus loin qu'un texte « rejeté ».
3. **Compter les résolutions sans dossier sous la figure.** 628 des 694 textes
   sont des propositions de résolution que la source ne rattache à aucun
   dossier : les sortir de la figure viderait la fiche de Florian Philippot, qui
   en porte 500 sur 502.
4. **Deviner la matière.** Le thème vient des domaines EuroVoc de
   `pivot_data/documents_europeens.json` ou des familles OEIL de
   `dossiers_europeens.json`, jamais de l'intitulé du texte.

CE QU'ILS NE COUVRENT PAS, et il faut le dire (§2 règle 5) : aucun composant
React n'est rendu ici, et aucun test ne lit `pivot_data/`. Le rendu — commutateur,
étiquettes à droite des barres, repli sous 560 px — a été vérifié hors dépôt sur
le serveur de développement.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale" / "src"
REGLES = UI / "utils" / "profilCandidat.js"
MISE_EN_PAGE = UI / "utils" / "cascadeTextes.js"
COMPOSANT = UI / "components" / "CascadeTextes.jsx"
FICHE = UI / "components" / "CandidateProfile.jsx"
ADAPTATEUR = UI / "data" / "pivotAdapter.js"
CHARGEUR = UI / "data" / "index.js"
SYNC = RACINE / "web" / "UI_finale" / "scripts" / "sync-data.mjs"
SCHEMA = RACINE / "src" / "schema_pivot.py"
NORMALISEUR = RACINE / "src" / "normalize_parltrack_dumps.py"


def _sans_commentaires(source: str) -> str:
    """Une règle citée en commentaire n'est pas une règle appliquée."""
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"^\s*//.*$", "", source, flags=re.MULTILINE)


@pytest.fixture(scope="module")
def regles() -> str:
    return _sans_commentaires(REGLES.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def mise_en_page() -> str:
    return _sans_commentaires(MISE_EN_PAGE.read_text(encoding="utf-8"))


def _stades_ue_du_schema() -> set[str]:
    texte = SCHEMA.read_text(encoding="utf-8")
    bloc = re.search(r"STADES_PROCEDURAUX_UE[^{]*\{(.*?)\}", texte, re.DOTALL)
    assert bloc, "le schéma doit déclarer STADES_PROCEDURAUX_UE"
    return set(re.findall(r'"(ue_[a-z0-9_]+)"', bloc.group(1)))


# ---------------------------------------------------------------------------
# 1. Chaque stade de la source a son libellé français
# ---------------------------------------------------------------------------


def test_chaque_stade_europeen_du_schema_a_son_libelle(regles) -> None:
    """Sans libellé, la fiche afficherait `ue_procedure_achevee` tel quel.

    La liste de référence est celle du SCHÉMA, pas une copie : un stade ajouté
    au pipeline fait rougir ce test au lieu de traverser l'écran en clé technique.
    """
    bloc = re.search(r"export const LIBELLE_STADE = \{(.*?)\n\};", regles, re.DOTALL)
    assert bloc, "LIBELLE_STADE doit rester exporté"
    libelles = set(re.findall(r"^\s*(ue_[a-z0-9_]+):", bloc.group(1), re.MULTILINE))
    manquants = _stades_ue_du_schema() - libelles
    assert not manquants, f"stades européens sans libellé français : {sorted(manquants)}"


def test_aucun_libelle_europeen_ne_promet_une_adoption(regles) -> None:
    """« Procédure achevée » n'est pas « adoptée », et c'est tout l'argument.

    Le dump ne porte AUCUN sort de dossier (`source_sans_sort` sur les 694
    textes). Un libellé qui dirait l'issue inventerait ce que la source tait.
    """
    bloc = re.search(r"export const LIBELLE_STADE = \{(.*?)\n\};", regles, re.DOTALL)
    for cle, libelle in re.findall(r"^\s*(ue_[a-z0-9_]+):\s*\n?\s*'([^']*)'", bloc.group(1), re.MULTILINE):
        for interdit in ("adopté", "adoptée", "promulgu", "voté"):
            assert interdit not in libelle.lower(), (
                f"« {libelle} » ({cle}) annonce une issue que la source ne publie pas"
            )


# ---------------------------------------------------------------------------
# 2. Le seuil §6 est écrit par exclusion, et une seule fois
# ---------------------------------------------------------------------------


def test_le_seuil_europeen_est_le_meme_que_celui_du_schema(regles) -> None:
    """`AGENTS.md` §6 : tout stade `ue_` est public SAUF la phase préparatoire.

    Écrire la règle dans l'autre sens — une liste de stades publiés — ferait
    disparaître en silence tout stade que la source ajouterait ensuite.
    """
    schema = re.search(
        r"STADES_UE_NON_PUBLIES: frozenset\[str\] = frozenset\(\{(.*?)\}\)",
        SCHEMA.read_text(encoding="utf-8"),
        re.DOTALL,
    )
    attendu = set(re.findall(r'"(ue_[a-z0-9_]+)"', schema.group(1)))
    bloc = re.search(r"export const STADES_UE_NON_PUBLIES = \[(.*?)\];", regles, re.DOTALL)
    assert bloc, "l'interface doit déclarer STADES_UE_NON_PUBLIES"
    assert set(re.findall(r"'(ue_[a-z0-9_]+)'", bloc.group(1))) == attendu


def test_aucune_valeur_europeenne_n_entre_dans_l_echelle_francaise(regles) -> None:
    """Le seuil français est un RANG ; une valeur européenne n'en a aucun."""
    bloc = re.search(r"export const STADES_PUBLIES = \[(.*?)\];", regles, re.DOTALL)
    assert "ue_" not in bloc.group(1), (
        "un stade européen a été glissé dans l'échelle française : il y prendrait "
        "un rang que la source n'établit pas"
    )


def test_le_hors_seuil_est_compte_et_dit(regles) -> None:
    """Un texte que §6 ne publie pas n'est pas un texte absent (§2 règle 5)."""
    bloc = re.search(r"export function textesEuropeens\((.*?)\n\}", regles, re.DOTALL).group(1)
    assert "horsSeuil" in bloc, "les textes hors seuil doivent être comptés"
    fiche = FICHE.read_text(encoding="utf-8")
    assert "horsSeuil" in fiche, "et la fiche doit les dire"


# ---------------------------------------------------------------------------
# 3. Les trois causes d'absence de stade ne se confondent pas
# ---------------------------------------------------------------------------


def test_les_trois_motifs_du_pipeline_ont_chacun_leur_branche(regles) -> None:
    """« La source se tait sur ce dossier » et « il n'y a pas de dossier » sont
    deux faits différents : les confondre ferait compter comme une lacune de la
    source ce qui est une propriété de l'activité."""
    motifs_pipeline = set(
        re.findall(r'"motif": "(activite_sans_dossier|source_sans_stade|stade_source_inconnu)"',
                   NORMALISEUR.read_text(encoding="utf-8"))
    )
    assert len(motifs_pipeline) == 3, "le normaliseur doit écrire les trois motifs"
    bloc = re.search(r"export const LIBELLE_MOTIF_STADE_UE = \{(.*?)\n\};", regles, re.DOTALL)
    assert bloc, "l'interface doit nommer les motifs"
    libelles = set(re.findall(r"^\s*([a-z_]+):", bloc.group(1), re.MULTILINE))
    assert motifs_pipeline <= libelles, (
        f"motifs sans libellé : {sorted(motifs_pipeline - libelles)}"
    )


# ---------------------------------------------------------------------------
# 4. Une porte, et pas une échelle
# ---------------------------------------------------------------------------


def test_la_mise_en_page_europeenne_n_empile_pas_les_stades(mise_en_page) -> None:
    """La figure française calcule `atteint[i]` — la somme des arrêts au-delà.

    Ce cumul n'a de sens que sur une échelle. La fonction européenne ne doit
    additionner aucune issue à une autre : chaque texte va dans la barre de son
    stade, et rien n'en traverse une autre.
    """
    bloc = re.search(r"export function disposerCascadeUE\((.*?)\n\}\n", mise_en_page, re.DOTALL)
    assert bloc, "la mise en page européenne doit exister"
    corps = bloc.group(1)
    assert "atteint[i]" not in corps and ".slice(i)" not in corps, (
        "la figure européenne ne cumule pas les issues : elles sont parallèles"
    )


def test_la_fiche_choisit_la_mise_en_page_et_le_vocabulaire(mise_en_page) -> None:
    """Une seule figure, deux mises en page — et la liste suit.

    « examiné en commission, et non discuté en séance » n'a de sens que sur une
    échelle : sur le versant européen, il n'y a pas d'étape suivante.
    """
    fiche = FICHE.read_text(encoding="utf-8")
    assert "disposerCascadeUE" in fiche, "la fiche doit passer la mise en page européenne"
    assert re.search(r"ordonnee=\{!ue\}", fiche), (
        "la liste doit savoir que les issues européennes ne s'ordonnent pas"
    )
    composant = COMPOSANT.read_text(encoding="utf-8")
    assert "disposer = disposerCascade" in composant, (
        "la mise en page française reste la valeur par défaut du composant"
    )


def test_la_branche_basse_porte_les_textes_sans_dossier(regles) -> None:
    """628 des 694 textes européens du corpus n'ont aucun dossier à interroger.

    Les compter sous la figure viderait la fiche de Florian Philippot — 500 de
    ses 502 textes sont dans ce cas.
    """
    bloc = re.search(r"export function textesEuropeens\((.*?)\n\}", regles, re.DOTALL).group(1)
    assert "basses" in bloc, "la cascade doit déclarer ses branches basses"
    assert "cascade.total" not in bloc or "dessines.length" in bloc, (
        "les textes sans stade restent DANS la figure"
    )


# ---------------------------------------------------------------------------
# 5. Le thème : les domaines EuroVoc au prorata, jamais un seul, jamais un compte
# ---------------------------------------------------------------------------
#
# ARBITRÉ LE 17/09/2026 (`axe-europeen-prorata-domaines-901`). L'axe « commission
# au fond », que ces tests verrouillaient jusque-là, ne couvrait que 17 des 383
# textes portés européens : il est abandonné. Ce qui ne bouge pas : rien ne se
# déduit de l'intitulé, et aucun libellé n'est écrit à la main.


def _executer(script: str) -> dict:
    import json
    import shutil
    import subprocess

    if shutil.which("node") is None:
        pytest.skip("node absent")
    entete = f"const u = await import({json.dumps(REGLES.as_uri())});\n"
    res = subprocess.run(["node", "--input-type=module", "-e", entete + script],
                         capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout.strip().splitlines()[-1])


_DOCUMENTS = """
const docs = {
  'B-8-2014-0056': { matieres: [
    { code: '1', domaine: { code: '24', libelle: '24 FINANCES' } },
    { code: '2', domaine: { code: '24', libelle: '24 FINANCES' } },
    { code: '3', domaine: { code: '24', libelle: '24 FINANCES' } },
    { code: '4', domaine: { code: '12', libelle: '12 DROIT' } },
  ] },
  'B-8-2014-0057': { matieres: [{ code: '9', domaine: null }] },
};
const dossiers = {
  '2021/0136(COD)': { type_procedure: 'COD - Ordinary legislative procedure', familles: [
    { code: '2', libelle: 'Internal market, single market' },
    { code: '6', libelle: 'External relations of the Union' },
  ] },
  '2014/2717(RSP)': { type_procedure: 'RSP - Resolutions on topical subjects', familles: [] },
};
const doc = (id) => docs[id] || null;
const dos = (r) => dossiers[r] || null;
const url = (id) => `http://www.europarl.europa.eu/doceo/document/${id}_EN.html`;
"""


def test_un_texte_repartit_son_unite_entre_ses_domaines() -> None:
    """3 concepts « Finances » et 1 « Droit » : ¾ et ¼. Le thème minoritaire
    n'est jamais écrasé — c'est tout l'objet de l'arbitrage."""
    out = _executer(_DOCUMENTS + """
      const t = { source_url: url('B-8-2014-0056') };
      console.log(JSON.stringify(Object.fromEntries(u.themesEuropeens(t, dos, doc))));
    """)
    assert out == {"Finances": 0.75, "Droit": 0.25}


def test_sans_domaine_les_familles_oeil_partagent_l_unite() -> None:
    """Un document sans domaine résolu passe aux familles du dossier, en anglais
    tel que la source les publie, à parts égales."""
    out = _executer(_DOCUMENTS + """
      const t = { source_url: url('B-8-2014-0057'), reference_dossier: '2021/0136(COD)' };
      console.log(JSON.stringify(Object.fromEntries(u.themesEuropeens(t, dos, doc))));
    """)
    assert out == {"Internal market, single market": 0.5, "External relations of the Union": 0.5}


def test_sans_domaine_ni_famille_la_matiere_n_est_pas_etablie() -> None:
    out = _executer(_DOCUMENTS + """
      const t = { source_url: url('B-9-2020-0001') };
      console.log(JSON.stringify(u.themesEuropeens(t, dos, doc)));
    """)
    assert out == [["Matière non établie", 1]]


def test_les_stades_comptent_des_textes_entiers() -> None:
    """Les parts s'additionnent par thème ; par stade, elles redonnent le nombre
    de textes. Un texte à quatre thèmes reste UN texte à droite."""
    out = _executer(_DOCUMENTS + """
      const textes = [
        { source_url: url('B-8-2014-0056'), stade_procedural_non_resolu: { motif: 'activite_sans_dossier' } },
        { source_url: url('B-8-2014-0057'), reference_dossier: '2021/0136(COD)', stade_procedural: 'ue_procedure_achevee' },
      ];
      const e = u.textesEuropeens(textes, dos, doc);
      const parStade = {};
      for (const [, st, n] of e.cascade.flux) parStade[st] = (parStade[st] || 0) + n;
      console.log(JSON.stringify({ parStade, themes: e.cascade.textes.map((t) => t.themes) }));
    """)
    assert out["parStade"] == {"activite_sans_dossier": 1, "ue_procedure_achevee": 1}
    assert out["themes"] == [["Finances", "Droit"], ["Internal market, single market", "External relations of the Union"]]


def test_la_nature_se_lit_dans_le_type_de_procedure() -> None:
    """Libellés et forme arbitrés le 17/09/2026. Une procédure que la liste ne
    nomme pas, ou un dossier hors index, n'est rangé dans aucune nature."""
    out = _executer(_DOCUMENTS + """
      console.log(JSON.stringify([
        u.natureEuropeenne({}, dos),
        u.natureEuropeenne({ reference_dossier: '2021/0136(COD)' }, dos),
        u.natureEuropeenne({ reference_dossier: '2014/2717(RSP)' }, dos),
        u.natureEuropeenne({ reference_dossier: '1999/0001(XYZ)' }, dos),
        u.NATURES_UE.map((n) => n.libelle),
      ]));
    """)
    assert out[:4] == ["sans_dossier", "legislatif", "resolution", None]
    assert out[4] == [
        "Législatif",
        "Rapports d’initiative et institutionnels",
        "Résolutions d’actualité",
        "Propositions de résolution sans dossier",
    ]


def test_le_clic_retrouve_un_texte_sous_chacun_de_ses_themes(mise_en_page) -> None:
    """Demandé le 17/09/2026 : la même mécanique qu'au niveau français. Un texte
    à deux thèmes est dans la liste de l'un comme de l'autre."""
    bloc = re.search(r"export function textesDeLaSelection\((.*?)\n\}", mise_en_page, re.DOTALL).group(1)
    assert "t.themes.includes(selection.matiere)" in bloc


def test_aucun_compte_n_est_affiche_par_theme(mise_en_page) -> None:
    """Une « part de texte » porterait à confusion auprès du public (arbitré le
    17/09/2026) : ni nombre devant un thème, ni dans l'infobulle d'un ruban."""
    bloc = re.search(r"export function disposerCascadeUE\((.*?)\n\}", mise_en_page, re.DOTALL).group(1)
    rubans = bloc[bloc.index("const rubans"):bloc.index("const barres")]
    assert "l.value}" not in rubans and "texte${" not in rubans


def test_aucun_domaine_n_est_ecarte(regles) -> None:
    """« Géographie » compris (17/09/2026) : l'écarter ne retirait qu'un nœud et
    aurait été un tri éditorial."""
    bloc = re.search(r"export function themesEuropeens\((.*?)\n\}", regles, re.DOTALL).group(1)
    assert "GÉOGRAPHIE" not in bloc and "'72'" not in bloc and "titre" not in bloc


def test_l_index_des_documents_europeens_est_copie_puis_charge() -> None:
    sync = SYNC.read_text(encoding="utf-8")
    assert "documents_europeens.json" in sync, "sync-data doit copier l'index"
    assert "/data/documents_europeens.json" in CHARGEUR.read_text(encoding="utf-8")
    appel = re.search(r"textesPortes\((.*?)\);", ADAPTATEUR.read_text(encoding="utf-8"), re.DOTALL).group(1)
    assert "documentEuropeen" in appel


def test_l_index_des_dossiers_europeens_est_copie_puis_charge() -> None:
    """Un index construit et jamais servi ne colorie rien.

    Il a vécu deux jours dans `pivot_data/` sans que `sync-data` le copie : la
    cascade européenne aurait dessiné tous ses rubans en « matière non établie »
    sans qu'aucun test ne le dise.
    """
    sync = SYNC.read_text(encoding="utf-8")
    assert "dossiers_europeens.json" in sync, "sync-data doit copier l'index"
    chargeur = CHARGEUR.read_text(encoding="utf-8")
    assert "/data/dossiers_europeens.json" in chargeur, "l'interface doit le lire"
    adaptateur = ADAPTATEUR.read_text(encoding="utf-8")
    assert "dossierEuropeen" in adaptateur, "et le passer en résolveur"
    appel = re.search(r"textesPortes\((.*?)\);", adaptateur, re.DOTALL).group(1)
    assert "dossierEuropeen" in appel
