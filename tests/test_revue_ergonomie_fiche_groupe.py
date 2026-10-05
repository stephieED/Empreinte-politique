"""La revue d'ergonomie de la fiche de groupe (02/10/2026).

Ce qui a été arrêté, section par section, sur maquette avec la propriétaire :
`docs/decisions/revue-ux-de-la-fiche-de-groupe.md`.

Ces tests tiennent ce qu'une session neuve déferait de bonne foi :

  1. Les TEXTES DES BULLES, au mot près — elle les a écrits ou choisis un par
     un, et une reformulation « pour améliorer » doit échouer.
  2. « Avec qui ils votent » n'écrit plus la base en gros : c'est ce nombre
     qu'un relecteur a lu comme un pourcentage.
  3. La liste des personnes s'ouvre un groupe à la fois, sans recherche ni
     « membres clefs ».
  4. La palette des commissions reste à distance des couleurs déjà prises —
     mesuré, pas estimé.
"""
from __future__ import annotations

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
SRC = RACINE / "web" / "UI_finale" / "src"
FICHE = SRC / "components" / "LigneeProfile.jsx"
FEUILLE = SRC / "components" / "LigneeProfile.css"
CANDIDAT = SRC / "components" / "CandidateProfile.jsx"
GOUVERNEMENT = SRC / "components" / "GovernmentProfile.jsx"
COMMISSIONS = SRC / "utils" / "commissions.js"
METHODO = SRC / "pages" / "MethodologyPage.jsx"

#: Les huit bulles, telles que la propriétaire les a arrêtées le 02/10/2026.
TEXTES = {
    "enBref": (
        "L’histoire du groupe à l’Assemblée : ses noms, ses effectifs, sa position face au gouvernement.",
        "Note : D’une législature à la suivante, l’Assemblée ne dit pas quel groupe succède à quel autre. Empreinte politique établit ce lien en comparant leurs membres.",
        "lignee",
    ),
    "quiSontIls": (
        "L’évolution de la composition du groupe d’une législature à la suivante et sous chacun de ses noms successifs.",
        "Note : Sont comptés tous les députés passés par le groupe pendant la législature, même brièvement.",
        "lignee",
    ),
    "textes": (
        "Les textes de loi portés par des membres du groupe, comme auteurs ou comme rapporteurs, à l’étape qu’ils ont atteinte.",
        "Note : Seuls les textes examinés en commission sont affichés. Un texte arrêté à une étape n’est pas nécessairement rejeté.",
        "depots",
    ),
    "amendements": (
        "Les amendements des membres du groupe, par matière et par texte amendé.",
        "Note : Le nombre d’amendements seul peut tromper. Chaque segment d’une barre est un texte amendé ; sa largeur est le nombre d’amendements déposés sur ce texte.",
        "depots",
    ),
    "paroles": (
        "Les prises de parole des membres du groupe à l’Assemblée, par législature, par nature et par débat.",
        "Note : Une prise de parole peut tenir en quelques mots.",
        "paroles",
    ),
    "vote": (
        "Les scrutins où le groupe a voté d’une seule voix, et ceux où ses membres se sont partagés, par législature.",
        "Note : « Quorum atteint » : au moins la moitié des membres du groupe a voté. « D’une seule voix » : toutes les positions exprimées vont dans le même sens.",
        "cohesion",
    ),
    "avecQui": (
        "La position du groupe comparée à celle de chaque autre groupe, texte par texte, par législature.",
        "Note : Voter dans le même sens n’est pas s’entendre : deux groupes peuvent rejeter un texte pour des raisons opposées. « Nuance » : l’un des deux groupes s’est abstenu.",
        "convergences",
    ),
    "couverture": (
        "Les limites de cette fiche : ce que les sources ne disent pas sur ces groupes.",
        "Note : Une information absente de cette fiche n’a pas été trouvée dans les sources. Cela ne veut pas dire qu’il ne s’est rien passé.",
        "couverture",
    ),
}


def _sans_commentaires(source: str) -> str:
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?<!:)//[^\n]*", "", source)


def _fiche() -> str:
    return FICHE.read_text(encoding="utf-8")


def _bulles() -> str:
    return _fiche().split("const BULLES = {")[1].split("\n};\n")[0]


def _entree(cle: str) -> str:
    return _bulles().split(f"  {cle}: {{")[1].split("\n  },")[0]


# ── 1. Les bulles ────────────────────────────────────────────────────────────


def test_les_huit_bulles_sont_celles_qui_ont_ete_arretees() -> None:
    methodo = METHODO.read_text(encoding="utf-8")
    for cle, (phrase, note, ancre) in TEXTES.items():
        entree = _entree(cle)
        assert phrase in entree, f"la phrase de la bulle « {cle} » a été reformulée"
        assert note in entree, f"la note de la bulle « {cle} » a été reformulée"
        assert f"vers: '/methodologie#{ancre}'" in entree
        assert f"id: '{ancre}'" in methodo, f"#{ancre} n'existe pas en méthodologie"


def test_la_note_d_en_bref_dit_comment_le_lien_est_etabli() -> None:
    """La fin validée — « en comparant leurs membres » — est écrite depuis que
    le run calcule le rattachement (#1168, lot 3)."""
    assert "établit ce lien en comparant leurs membres." in _entree("enBref")


def test_le_premier_lien_de_la_derniere_section_est_celui_qu_elle_a_ecrit() -> None:
    entree = _entree("couverture")
    assert "{ libelle: 'Sources et couvertures →', vers: '/sources#frise' }" in entree
    assert "dépôt" not in _sans_commentaires(_fiche()).split("const BULLES = {")[1].split("\n};\n")[0], (
        "« dépôt » est un mot de travail, refusé sur la fiche candidat"
    )


def test_une_section_qui_a_sa_bulle_n_ecrit_plus_ni_phrase_ni_pied_ni_renvoi() -> None:
    """Une seule section garde l'ancienne forme, et seulement dans son état
    d'attente : « Sur quoi ils ont pris la parole », tant que le corpus ne
    porte pas le rôle de séance."""
    fiche = _sans_commentaires(_fiche())
    # La prop d'une `<Section>` est seule sur sa ligne ; `<VideFiltre critere=…>`,
    # qui porte le même nom pour autre chose, ne l'est jamais.
    assert len(re.findall(r'^\s+critere="', fiche, flags=re.MULTILINE)) == 1
    assert fiche.count("renvoi={{") == 1
    parole = fiche.split("function SurQuoiIlsParlent(")[1].split("\nfunction ")[0]
    assert 'critere="' in parole and "renvoi={{ ancre: 'paroles'" in parole
    for section in ("QuiSontIls", "CeQuIlsOntVote", "AvecQuiIlsVotent", "CeQuOnNaPasPuLire"):
        corps = fiche.split(f"function {section}(")[1].split("\nfunction ")[0]
        assert "bulle={BULLES." in corps and "pied=" not in corps, section
    assert "{...BULLES.enBref}" in fiche
    # La législature en cours n'est pas encore qualifiée : la note le dit, au mot près.
    assert "'L’Assemblée nationale ne dit quel groupe est majoritaire qu’une fois la législature achevée.'" in fiche
    assert "`${BULLES.enBref.note} ${NOTE_MAJORITE_NON_DITE}`" in fiche


def test_les_deux_cartes_de_la_section_trois_portent_chacune_leur_bulle() -> None:
    fiche = _fiche()
    assert "{...BULLES.textes} />" in fiche and "{...BULLES.amendements} />" in fiche
    propose = fiche.split("function CeQuIlsOntPropose(")[1].split("\nfunction ")[0]
    assert "bulle=" not in propose.split("<Section")[1].split(">")[0], (
        "comme sur la fiche candidat, le titre de la section n'a pas de bulle : ses cartes en ont"
    )


def test_la_fiche_candidat_redit_que_le_nombre_seul_peut_tromper() -> None:
    """La phrase avait quitté la note le 01/10/2026, quand la barre s'est
    découpée par texte. Relisant la bulle, la propriétaire n'y a plus trouvé
    l'alerte : la figure ne dispense pas de la dire."""
    candidat = CANDIDAT.read_text(encoding="utf-8").split("const BULLES = {")[1].split("\n};\n")[0]
    assert candidat.count("Note : Le nombre d’amendements seul peut tromper.") == 2, (
        "les deux versants — Assemblée et Parlement européen — la portent"
    )


def test_la_ligne_de_position_se_tait_sur_la_fiche_de_groupe() -> None:
    appel = _fiche().split("<NavigationPeriodes")[1].split("/>")[0]
    assert "sansPosition" in appel


# ── 2. Avec qui ils votent ───────────────────────────────────────────────────


def test_la_base_ne_s_ecrit_plus_en_gros() -> None:
    """« 51 textes communs » a été lu « 51 % de proximité » : le nombre le plus
    visible de la ligne était le dénominateur. La base se compte désormais, un
    carré par texte, et reste écrite en petit — un ratio de groupe garde son
    dénominateur (AGENTS.md §2 règle 7)."""
    fiche = _sans_commentaires(_fiche())
    feuille = FEUILLE.read_text(encoding="utf-8")
    assert "lp-accord-n" not in fiche and ".lp-accord-n" not in feuille
    assert "lp-accord-barre" not in fiche, "la barre proportionnelle est partie avec le nombre en gros"
    section = fiche.split("function AvecQuiIlsVotent(")[1].split("\nfunction ")[0]
    assert 'className="lp-accord-base lp-num"' in section and "commun{a.communs > 1 ? 's' : ''}" in section
    base = feuille.split(".lp-accord-base {")[1].split("}")[0]
    assert "font-size: 12px" in base, "la base reste à l'échelle des libellés"


def test_un_carre_par_texte_commun_dans_l_ordre_des_trois_natures() -> None:
    section = _sans_commentaires(_fiche()).split("function AvecQuiIlsVotent(")[1].split("\nfunction ")[0]
    assert "NATURES.flatMap((n) => (a.scrutins[n.cle] || []).map(([id]) => (" in section
    assert "aria-label={`${m.scrutins[id]?.texte || 'Intitulé non publié'} — ${LIBELLES_NATURE[n.cle]}`}" in section
    # Aucun pourcentage, aucun tri par proximité : l'ordre reste celui des règles.
    assert "%" not in re.sub(r"`[^`]*`", "", section).replace("% ", "")
    assert ".sort(" not in section


# ── 3. La liste des personnes ────────────────────────────────────────────────


def test_la_liste_s_ouvre_un_groupe_a_la_fois() -> None:
    """7 583 px pour les 448 personnes d'Ensemble pour la République, tous
    groupes dépliés d'un coup. Un rang par groupe, un seul ouvert."""
    section = _sans_commentaires(_fiche()).split("function QuiSontIls(")[1].split("\nfunction ")[0]
    assert "const [rang, setRang] = useState(null);" in section
    assert "onClick={() => setRang(ouvert ? null : i)}" in section
    assert "{ouvert && (" in section and 'className="lp-rang-noms"' in section
    assert "<details" not in section and "lp-tous-colonnes" not in section


def test_la_fiche_ne_choisit_pas_qui_compte() -> None:
    """Ni recherche — la propriétaire l'a écartée —, ni « membres clefs » : ce
    serait la fiche qui déciderait qui compte dans un groupe (§2 règle 1)."""
    section = _sans_commentaires(_fiche()).split("function QuiSontIls(")[1].split("\nfunction ")[0]
    assert "<input" not in section
    assert ".slice(" not in section, "aucune liste tronquée à un nombre de noms"


def test_ce_qui_s_ouvre_se_replie_au_clic_ailleurs() -> None:
    fiche = _sans_commentaires(_fiche())
    assert "import { useReplieAuClicDehors } from '../hooks/useReplieAuClicDehors';" in fiche
    for etat in ("rang != null", "ouvert != null", "sel != null", "ouverte != null", "ouvert && !force"):
        assert f"useReplieAuClicDehors(carte, {etat}," in fiche or f"useReplieAuClicDehors(ref, {etat}," in fiche, etat


# ── 4. La palette ────────────────────────────────────────────────────────────

#: Les couleurs que le site emploie déjà pour autre chose.
PRISES = {
    "le vert des votes « pour »": "#007A45",
    "le rouge des votes « contre »": "#E53420",
    "le prune de l'Assemblée": "#803060",
    "le bronze du gouvernement": "#85510d",
    "le bleu du Parlement européen": "#003399",
    "le sarcelle du Sénat": "#169e9e",
    "l'ambre des amendements retirés": "#F2A93B",
    "le mauve des groupes minoritaires": "#c9a3b9",
}


def _oklab(couleur: str) -> tuple[float, float, float]:
    def lin(c: int) -> float:
        x = c / 255
        return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(int(couleur[i:i + 2], 16)) for i in (1, 3, 5))
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (
        0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
        1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
        0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s,
    )


def _ecart(a: str, b: str) -> float:
    x, y = _oklab(a), _oklab(b)
    return 100 * sum((p - q) ** 2 for p, q in zip(x, y)) ** 0.5


def _teintes() -> dict[str, str]:
    table = COMMISSIONS.read_text(encoding="utf-8").split("export const TEINTE_COMMISSION_PERMANENTE = {")[1].split("};")[0]
    return dict(re.findall(r"'([^']+)': '(#[0-9a-fA-F]{6})'", table))


def test_aucune_commission_ne_se_confond_avec_une_couleur_deja_prise() -> None:
    """La palette du 01/10/2026 passait le validateur et se confondait quatre
    fois avec le reste du site : Défense à 2 du vert « pour », Affaires
    économiques à 3 du prune de l'Assemblée, Finances à 4 du sarcelle du Sénat,
    Affaires étrangères à 8 du bleu du Parlement européen. Sous 8, deux
    couleurs se confondent ; la palette A tient chaque teinte à 12."""
    teintes = _teintes()
    assert len(teintes) == 8
    for commission, teinte in teintes.items():
        for nom, prise in PRISES.items():
            ecart = _ecart(teinte, prise)
            assert ecart >= 11.9, f"{commission} ({teinte}) est à {ecart:.1f} de {nom}"


def test_les_huit_teintes_se_distinguent_entre_elles() -> None:
    teintes = list(_teintes().values())
    for i, a in enumerate(teintes):
        for b in teintes[i + 1:]:
            assert _ecart(a, b) >= 15, f"{a} et {b} sont à {_ecart(a, b):.1f} : sous 15, on les confond"


def test_les_fiches_lisent_la_meme_table() -> None:
    """La fiche de groupe colorait au rang ; elle lit la table des commissions.

    La fiche de gouvernement l'a lue du 02 au 04/10/2026, puis ses carrés ont
    pris la teinte du MINISTÈRE qui présente le texte (forme A, arbitrée par la
    propriétaire) : elle ne colore plus par commission, et jamais au rang.
    """
    source = _sans_commentaires(FICHE.read_text(encoding="utf-8"))
    assert "teinteCommission(" in source
    for composant in (FICHE, GOUVERNEMENT):
        source = _sans_commentaires(composant.read_text(encoding="utf-8"))
        assert "teinteMatiere(" not in source and "PALETTE_MATIERE" not in source, composant.name
    gouvernement = _sans_commentaires(GOUVERNEMENT.read_text(encoding="utf-8"))
    assert "fondDuTexte(poles, teintes, t)" in gouvernement and "teinteCommission(" not in gouvernement


# ── 5. Les prises de parole comptées ─────────────────────────────────────────

import json
import subprocess

UI = RACINE / "web" / "UI_finale"
REGLE = SRC / "utils" / "paroleDeGroupe.js"
VUE = UI / "scripts" / "vue-lignee.mjs"
SYNC = UI / "scripts" / "sync-data.mjs"


def _node(script: str):
    sortie = subprocess.run(
        ["node", "--input-type=module", "-e", script], capture_output=True, text=True, cwd=UI, check=False,
    )
    assert sortie.returncode == 0, sortie.stderr
    return json.loads(sortie.stdout)


#: Trois entrées COPIÉES du corpus publié (profils `yael-braun-pivet`,
#: `stephanie-rist`, `charles-sitzenstuhl`, XVIIe législature, relevées le
#: 02/10/2026) : une présidence de séance, une parole de ministre, une
#: intervention. `role_seance` et `fonction` sont ceux que l'index de collecte
#: porte pour ces mêmes identifiants (cache du 11/09/2026) — le corpus publié
#: ne les a pas encore, il les recevra au prochain run (#1169).
ENTREES = [
    {"intervention_id": "syceron_CRSANR5L17S2026E1N023_000420", "date": "2026-07-21", "type_detail": "debat",
     "theme_officiel": "Protection des enfants",
     "texte": "La parole est à Mme la présidente de la commission spéciale.", "role_seance": "presidence"},
    {"intervention_id": "syceron_CRSANR5L17S2026E1N023_000350", "date": "2026-07-21", "type_detail": "explication_vote",
     "theme_officiel": "Protection des enfants", "texte": "Mais non !",
     "fonction": "ministre de la santé, des familles, de l’autonomie et des personnes handicapées"},
    {"intervention_id": "syceron_CRSANR5L17S2026E1N001_000265", "date": "2026-07-01", "type_detail": "debat",
     "theme_officiel": "Justice criminelle et respect des victimes", "texte": "Ce n’est pas le bon article !"},
]


def test_la_presidence_et_la_parole_de_ministre_ne_sont_pas_la_parole_du_groupe() -> None:
    """« Ça ne fait pas partie des interventions du groupe » : la présidence de
    séance, et la parole prononcée comme membre du gouvernement pendant le mois
    où un député nommé ministre reste membre de son groupe. Retirées, sans
    pastille."""
    r = _node(f"""
      import {{ estParoleDuGroupe, porteUnRoleDeSeance }} from './src/utils/paroleDeGroupe.js';
      const e = {json.dumps(ENTREES)};
      console.log(JSON.stringify({{ garde: e.map(estParoleDuGroupe), role: e.map(porteUnRoleDeSeance) }}));
    """)
    assert r["garde"] == [False, False, True]
    assert r["role"] == [True, False, False], "seule une clé PRÉSENTE dit que le corpus porte le rôle"


def test_un_secretaire_d_etat_ecrit_avec_l_apostrophe_typographique_est_reconnu() -> None:
    r = _node("""
      import { estFonctionGouvernementale as f } from './src/utils/fonctionGouvernementale.js';
      console.log(JSON.stringify([f('secrétaire d’État chargé de la mer'), f("secrétaire d'État"), f('rapporteur'), f(null)]));
    """)
    assert r == [True, True, False, False]


def test_les_debats_se_rangent_par_prises_de_parole_et_les_pastilles_recomptent() -> None:
    """Rangés par nombre de prises de parole — son arbitrage —, puis par nombre
    de membres. Une pastille cochée recompte les débats ; le nombre écrit sur
    chaque pastille reste celui de tout le groupe."""
    r = _node("""
      import { agregerParoles, debatsSousSelection, NATURES_DE_PAROLE } from './src/utils/paroleDeGroupe.js';
      const e = [
        { sujet: 'a', orateur: 1, nature: 0 }, { sujet: 'a', orateur: 1, nature: 0 }, { sujet: 'a', orateur: 2, nature: 1 },
        { sujet: 'b', orateur: 1, nature: 1 }, { sujet: 'b', orateur: 2, nature: 1 }, { sujet: 'b', orateur: 3, nature: 1 },
        { sujet: 'b', orateur: 3, nature: 1 },
      ];
      const p = agregerParoles(e);
      const tout = debatsSousSelection(p);
      const loi = debatsSousSelection(p, new Set([0]));
      console.log(JSON.stringify({ natures: NATURES_DE_PAROLE.slice(0, 2), tout, loi }));
    """)
    assert r["natures"] == ["Débats sur un texte de loi", "Débats"], "les mots de la fiche candidat"
    assert [(l["label"], l["paroles"], l["membres"]) for l in r["tout"]["lignes"]] == [("b", 4, 3), ("a", 3, 2)]
    assert r["tout"]["lignes"][0]["segments"] == [[3, 2], [1, 1], [2, 1]], "les segments du plus grand au plus petit"
    assert [(l["label"], l["paroles"], l["membres"]) for l in r["loi"]["lignes"]] == [("a", 2, 1)]
    assert r["loi"]["parNature"][:2] == [2, 5] and r["loi"]["total"] == 2


def test_la_figure_reste_eteinte_tant_que_le_corpus_ne_porte_pas_le_role() -> None:
    """Sans `role_seance`, la présidence passerait pour la parole du groupe :
    20 788 des 39 581 prises de parole d'Ensemble pour la République en XVIIe.
    `rolesPublies` est un fait du CORPUS, écrit après la boucle des groupes —
    un groupe dont aucun membre n'a présidé doit s'allumer avec les autres."""
    fiche = _sans_commentaires(_fiche())
    assert "if (!filtreActif && paroles?.rolesPublies) {" in fiche
    vue = _sans_commentaires(VUE.read_text(encoding="utf-8"))
    assert "if (porteUnRoleDeSeance(i)) maillon.rolesVus = true;" in vue
    assert vue.index("if (!estParoleDuGroupe(i)) continue;") < vue.index("maillon.entrees.push("), (
        "les extraits qu'on lit en ouvrant un débat sont la même population que le compte"
    )
    sync = _sans_commentaires(SYNC.read_text(encoding="utf-8"))
    boucle = sync.index("if (x.rolesVus) rolesDeSeancePublies = true;")
    assert boucle < sync.index("rolesPublies: rolesDeSeancePublies, ...paroles")
    assert "path.join(projectRoot, 'src', 'utils', 'paroleDeGroupe.js')," in sync, (
        "le cache de build doit se refaire quand la règle change"
    )


def test_aucune_pastille_de_role() -> None:
    """Ni « Présidence de séance », ni « Rapporteur », ni « Membre du
    gouvernement » : proposées, écartées. Seules les pastilles de nature."""
    figure = _sans_commentaires(_fiche()).split("function ParolesComptees(")[1].split("\nfunction ")[0]
    assert "NATURES_DE_PAROLE.map(" in figure
    for mot in ("Présidence", "Rapporteur", "gouvernement"):
        assert mot not in figure
