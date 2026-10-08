"""« Ce qu'on n'a pas pu lire » est UNE liste de manques (revue du 01/10/2026).

La section portait trois cartes : un tableau « Ce que chaque liste porte »
(couvert depuis / hors couverture / N entrées), puis « Ce que le corpus ne dit
pas de son parcours », puis « Ce que la collecte signale ». Le tableau répondait
à « qu'avons-nous ? » sous un titre qui promet « que n'avons-nous pas ? », et le
seul fait propre à la personne — un mandat que la source ne couvre pas — restait
à déduire de deux dates.

Elle porte désormais UNE carte, « Ce qui manque sur cette fiche », une ligne par
manque, dans un ordre arrêté avec la propriétaire. Les textes sont validés au mot
près : c'est pourquoi ces tests comparent des listes entières, et non des
fragments.

CE QUE CES TESTS EXÉCUTENT. `manquesDeLaFiche` et ses dépendances
(`utils/profilCandidat.js`), sous node, sur sept fiches dont les entrées sont
COPIÉES du corpus — `tests/fixtures/fiches_section_6_extrait.json`, qui dit
lui-même d'où il vient. Aucun test ne lit `pivot_data/` (AGENTS.md §3b), et une
entrée inventée aurait confirmé le monde tel que le code l'imagine : c'est sur
les vraies que se voient un état `non_collecte` sans date, un mandat de sénateur
de 1986, un mandat à cheval sur la borne.

CE QU'ILS NE COUVRENT PAS (§2 règle 5) : aucun composant React n'est rendu ici.
Les sept listes ont été vérifiées par rendu serveur (`renderToString`) hors
dépôt, le 01/10/2026, sur les 31 fiches publiées ; le rendu à l'écran — colonne
de 240 px, filets — n'est tenu par aucun test.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
SRC = RACINE / "web" / "UI_finale" / "src"
PROFIL = SRC / "utils" / "profilCandidat.js"
FICHE = SRC / "components" / "CandidateProfile.jsx"
ADAPTATEUR = SRC / "data" / "pivotAdapter.js"
DONNEES = SRC / "data" / "index.js"
EXTRAIT = RACINE / "tests" / "fixtures" / "fiches_section_6_extrait.json"

NON_COUVERT_2012 = (
    "Votes, Amendements, Textes portés",
    "Son mandat de juin 2007 à juin 2012 n’est pas couvert : la source commence le 20 juin 2012.",
)
AVANT_2002 = ("Avant juin 2002", "Nos sources ne connaissent aucun mandat avant le 19 juin 2002.")
ENTREE_AU_GOUVERNEMENT = (
    "Entrée au gouvernement",
    "La source ne dit pas si un mandat s’est interrompu quand cette personne est entrée au gouvernement.",
)


def sans_commentaires(source: str) -> str:
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?<!:)//[^\n]*", "", source)


def _node(script: str) -> dict:
    if shutil.which("node") is None:
        pytest.skip("node absent")
    entete = f"""
    import {{ readFileSync }} from 'node:fs';
    const m = await import({json.dumps(PROFIL.as_uri())});
    const extrait = JSON.parse(readFileSync({json.dumps(str(EXTRAIT))}, 'utf-8'));
    const bornes = extrait.bornes_du_corpus;
    // Les trois listes d'activité ne sont pas recopiées dans l'extrait : seul
    // leur effectif est lu par la règle, et il est reconstitué ici.
    const profilDe = (slug) => {{
      const p = extrait.fiches[slug].profil;
      const liste = (n) => Array.from({{ length: n }}, () => ({{}}));
      return {{ ...p, votes: liste(p.effectifs.votes), amendements: liste(p.effectifs.amendements),
                interventions: liste(p.effectifs.interventions) }};
    }};
    const section = (slug, avecBornes = true) => {{
      const profil = profilDe(slug);
      const limites = m.limitesDeclarees({{
        profil, roles: m.rolesDuParcours(profil.mandats).roles, sieges: m.siegesElectifs(profil.mandats),
      }});
      const r = m.manquesDeLaFiche({{
        profil, limites, manques: extrait.fiches[slug].manques, bornesDuCorpus: avecBornes ? bornes : null,
      }});
      return {{ phrase: r.phrase, lignes: r.lignes.map((l) => [l.titre, l.texte]) }};
    }};
    """
    res = subprocess.run(
        ["node", "--input-type=module", "-e", entete + script],
        capture_output=True, text=True, check=False,
    )
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout.strip().splitlines()[-1])


@pytest.fixture(scope="module")
def sections() -> dict:
    return _node(
        """
        console.log(JSON.stringify(Object.fromEntries(
          Object.keys(extrait.fiches).map((slug) => [slug, section(slug)]),
        )));
        """
    )


def _lignes(sections: dict, slug: str) -> list[tuple[str, str]]:
    return [tuple(l) for l in sections[slug]["lignes"]]


# ── Les quatre contrôles arrêtés en revue ───────────────────────────────────


def test_francois_ruffin_quatre_lignes(sections: dict) -> None:
    """Trois mandats, tous ouverts le 18 juin 2017 ou après : aucun n'est « non
    couvert », la source des prises de parole commençant trois jours plus tard."""
    assert sections["francois-ruffin"]["phrase"] is None
    assert _lignes(sections, "francois-ruffin") == [
        ("Majorité ou opposition", "L’Assemblée ne l’a pas déclaré pour 1 de ses 3 mandats."),
        ("Votes", "Sur ses 168 votes, 39 n’ont pas de commission connue et 36 n’ont pas de sort connu."),
        (
            "Prises de parole",
            "Sur 3 499 prises de parole, 1 n’a pas de texte et 3 475 n’indiquent pas à quel "
            "titre la personne parlait.",
        ),
        AVANT_2002,
    ]


def test_delphine_batho_l_ordre_des_sept_lignes(sections: dict) -> None:
    """L'ordre est la règle : les mandats non couverts, puis ce que la source ne
    dit pas du parcours, puis ce que des entrées ne portent pas, puis la borne.

    Ses prises de parole sont `non_collecte` SANS date au profil : le 21 juin
    2017 vient des bornes du corpus (`couverture.json`), et la ligne en dépend.
    """
    assert _lignes(sections, "delphine-batho") == [
        NON_COUVERT_2012,
        (
            "Prises de parole",
            "Son mandat de juin 2007 à juin 2017 n’est pas couvert : la source commence le 21 juin 2017.",
        ),
        ("Majorité ou opposition", "L’Assemblée ne l’a pas déclaré pour 1 de ses 5 mandats."),
        ENTREE_AU_GOUVERNEMENT,
        ("Votes", "Sur ses 164 votes, 32 n’ont pas de commission connue et 30 n’ont pas de sort connu."),
        (
            "Prises de parole",
            "Sur 2 143 prises de parole, 2 n’ont pas de texte et 2 143 n’indiquent pas à quel "
            "titre la personne parlait.",
        ),
        AVANT_2002,
    ]


def test_anasse_kazib_une_phrase_et_pas_de_liste(sections: dict) -> None:
    """La phrase dit ce que nos SOURCES savent, jamais un fait sur la personne :
    « n'a exercé aucun mandat » serait une affirmation que rien n'établit (§2
    règle 5). C'est elle que les « Pourquoi → » des sections vides viennent lire.
    """
    assert sections["anasse-kazib"] == {
        "phrase": (
            "Nos sources ne connaissent aucun mandat parlementaire de cette personne. "
            "Il n’y a donc ni vote, ni amendement, ni prise de parole à publier."
        ),
        "lignes": [],
    }


def test_segolene_royal_les_mandats_anterieurs_font_taire_la_borne(sections: dict) -> None:
    """« Avant juin 2002 — nos sources ne connaissent aucun mandat… » sous une
    ligne qui en cite sept serait une contradiction sur deux lignes voisines."""
    lignes = _lignes(sections, "segolene-royal")
    assert lignes == [
        (
            "Votes, Amendements, Textes portés",
            "Son mandat de juin 2002 à juin 2007 n’est pas couvert : la source commence le 20 juin 2012.",
        ),
        (
            "Prises de parole",
            "Son mandat de juin 2002 à juin 2007 n’est pas couvert : la source commence le 21 juin 2017.",
        ),
        ENTREE_AU_GOUVERNEMENT,
        (
            "Mandats antérieurs",
            "7 mandats exercés avant le 19 juin 2002 — 3 à l’Assemblée, 4 au gouvernement — sont cités "
            "depuis leur source primaire. Aucune activité n’y est collectée.",
        ),
    ]
    assert not any(titre.startswith("Avant ") for titre, _ in lignes)


# ── Le Sénat et le Parlement européen : aucune règle, et rien de faux ───────


def test_un_mandat_de_senateur_n_est_pas_oppose_a_une_source_de_l_assemblee(sections: dict) -> None:
    """Jean-Luc Mélenchon porte trois mandats au Sénat (1986-2010) et deux au
    Parlement européen (2009-2017). Les quatre bornes sont celles de sources de
    l'Assemblée : leur opposer ces mandats écrirait « n'est pas couvert : la
    source commence le 20 juin 2012 », d'une source qui ne les aurait pas
    couverts davantage après. Son seul mandat à l'Assemblée s'ouvre le 18 juin
    2017 : aucune ligne de mandat non couvert.

    Et pas de « Avant juin 2002 » non plus : la ligne des mandats antérieurs la
    fait taire, et un siège au Sénat de 1986 l'aurait rendue fausse de toute
    façon.
    """
    lignes = _lignes(sections, "jean-luc-melenchon")
    assert [titre for titre, _ in lignes] == [
        "Sénat", "Votes", "Prises de parole", "Mandats antérieurs", "Explications de vote au Parlement européen",
    ]
    assert not any("la source commence" in texte for _, texte in lignes), (
        "une borne de l'Assemblée est opposée à un mandat qui n'y a pas été exercé"
    )
    # LE SÉNAT A SA PROPRE LIGNE (02/10/2026), sans borne : la source ne
    # commence pas plus tard, elle ne porte pas ces trois listes.
    assert lignes[0][1] == (
        "Ses mandats au Sénat, d’octobre 1986 à avril 2000 puis d’octobre 2004 à janvier 2010, "
        "ne sont pas couverts : ni vote, ni amendement, ni prise de parole."
    )
    assert lignes[1][1] == "Sur ses 101 votes, 37 n’ont pas de commission connue et 37 n’ont pas de sort connu."
    # DEUX SIGNALEMENTS DE COLLECTE NE SE LISENT PLUS TELS QUELS (#1161, arbitré
    # le 02/10/2026) : « votes non publiés » dit un choix, pas un manque, et
    # n'est plus adressé au lecteur ; « explications de vote » est réécrit.
    assert not any("scrutin(s)" in texte or "explication(s)" in texte for _, texte in lignes)
    assert lignes[4][1] == "1 de ses 49 explications de vote est publiée sans lien vers le document officiel."


def test_emmanuel_maurel_garde_les_lignes_que_la_collecte_signale(sections: dict) -> None:
    """Deux mandats européens (2014-2024), un à l'Assemblée depuis 2024."""
    lignes = _lignes(sections, "emmanuel-maurel")
    assert [titre for titre, _ in lignes] == [
        "Votes", "Prises de parole", "Explications de vote au Parlement européen", "Avant juin 2002",
    ]
    assert lignes[1][1] == (
        "Sur 1 562 prises de parole, 162 n’ont pas de texte et 1 532 n’indiquent pas à quel "
        "titre la personne parlait."
    )


def test_bruno_retailleau_la_source_du_senat_dit_pourquoi_un_mandat_a_pris_fin(sections: dict) -> None:
    """Quatre mandats au Sénat, aucun à l'Assemblée dans le corpus, six
    fonctions gouvernementales.

    L'ancienne limite — « suspendu_pour_fonction_gouvernementale n'est renseigné
    sur aucun de ses 4 mandats électifs » — était vraie à la lettre : le champ
    est absent. La nouvelle phrase affirme quelque chose d'une SOURCE (« la
    source ne dit pas si un mandat s'est interrompu… »), et data.senat.fr le
    dit : son mandat de 2020 porte `motif_fin_senat: FINMEMGVT`. La ligne ne
    paraît donc que pour des mandats à l'Assemblée (§2 règle 2).
    """
    extrait = json.loads(EXTRAIT.read_text(encoding="utf-8"))
    electifs = [
        m for m in extrait["fiches"]["bruno-retailleau"]["profil"]["mandats"]
        if m["categorie"] == "mandat_electif"
    ]
    assert {m["chambre"] for m in electifs} == {"Senat"}
    assert "FINMEMGVT" in {m.get("motif_fin_senat") for m in electifs}
    assert _lignes(sections, "bruno-retailleau") == [
        # Le texte arrêté par la propriétaire le 02/10/2026, sur cette fiche :
        # vingt ans de mandat sénatorial dont la section ne disait rien.
        (
            "Sénat",
            "Ses mandats au Sénat, d’octobre 2004 à octobre 2024 puis depuis novembre 2025, "
            "ne sont pas couverts : ni vote, ni amendement, ni prise de parole.",
        ),
        (
            "Mandats antérieurs",
            "1 mandat exercé avant le 19 juin 2002 est cité depuis sa source primaire. "
            "Aucune activité n’y est collectée.",
        ),
    ]


# ── D'où vient la date où une source commence ───────────────────────────────


def test_la_date_vient_du_profil_puis_des_bornes_du_corpus_jamais_d_une_constante() -> None:
    """Le profil d'abord (`portee.debut` de l'état `couvert` ou `fait_etabli`).

    Les prises de parole de Delphine Batho sont `non_collecte`, sans portée :
    la date vient alors des bornes que les autres fiches déclarent. SANS ces
    bornes, la ligne ne s'écrit pas — une date ne s'invente pas (§2 règle 5) —,
    et les trois autres listes, que le profil date lui-même, tiennent toujours.
    """
    out = _node(
        """
        const p = profilDe('delphine-batho');
        const a = profilDe('anasse-kazib');
        const j = profilDe('jean-luc-melenchon');
        console.log(JSON.stringify({
          etats: p.couverture.interventions.map((e) => [e.etat, e.portee ?? null]),
          sansBornes: m.debutDeSource(p.couverture, 'interventions', null),
          avecBornes: m.debutDeSource(p.couverture, 'interventions', bornes),
          votes: m.debutDeSource(p.couverture, 'votes', null),
          faitEtabli: m.debutDeSource(a.couverture, 'interventions', null),
          // L'entrée européenne de Mélenchon ouvre ses votes au 25/11/2009 : ce
          // n'est pas la borne d'une source, c'est sa première donnée.
          europe: j.couverture.votes.filter((e) => e.source === 'parlement_europeen').map((e) => e.portee.debut),
          votesMelenchon: m.debutDeSource(j.couverture, 'votes', null),
          section: section('delphine-batho', false).lignes.map((l) => l[0]),
        }));
        """
    )
    assert out["etats"] == [["non_collecte", None]]
    assert out["sansBornes"] is None
    assert out["avecBornes"] == "2017-06-21"
    assert out["votes"] == "2012-06-20"
    assert out["faitEtabli"] == "2017-06-21", "`fait_etabli` date la source comme `couvert`"
    assert out["europe"] == ["2009-11-25"]
    assert out["votesMelenchon"] == "2012-06-20"
    assert out["section"] == [
        "Votes, Amendements, Textes portés", "Majorité ou opposition", "Entrée au gouvernement",
        "Votes", "Prises de parole", "Avant juin 2002",
    ]
    code = sans_commentaires(PROFIL.read_text(encoding="utf-8"))
    for date in ("2012-06-20", "2017-06-21", "20 juin 2012", "21 juin 2017"):
        assert date not in code, f"la borne {date} est écrite en dur dans les règles de la fiche"


def test_la_fiche_charge_les_bornes_du_corpus_sans_en_dependre() -> None:
    """`couverture.json` est lu avec le reste, et son échec ne casse pas la fiche."""
    donnees = sans_commentaires(DONNEES.read_text(encoding="utf-8"))
    assert "loadCouverture().catch(() => null)" in donnees
    assert "bornesDuCorpus: couverture?.bornes ?? null" in donnees
    adaptateur = sans_commentaires(ADAPTATEUR.read_text(encoding="utf-8"))
    assert "ceQuiManque: manquesDeLaFiche({" in adaptateur
    assert "bornesDuCorpus," in adaptateur


# ── Le calcul des mandats non couverts ──────────────────────────────────────


def test_sept_jours_de_tolerance_et_les_mandats_contigus_fusionnent() -> None:
    """Les mandats de Delphine Batho, tels que le corpus les porte.

    SEPT JOURS : son mandat du 18 juin 2017 n'est pas « non couvert » par une
    source ouverte le 21. QUARANTE-CINQ JOURS : 2007-2012 et 2012-2017, séparés
    de quatre jours, sont UN manque de dix ans, pas deux lignes.
    """
    out = _node(
        """
        const mandats = profilDe('delphine-batho').mandats
          .filter((x) => x.categorie === 'mandat_electif')
          .map((x) => ({ debut: x.debut, fin: x.fin }));
        console.log(JSON.stringify({
          mandats: mandats.map((x) => [x.debut, x.fin]).sort(),
          votes: m.segmentsNonCouverts(mandats, '2012-06-20'),
          paroles: m.segmentsNonCouverts(mandats, '2017-06-21'),
          sansBorne: m.segmentsNonCouverts(mandats, null),
          tolerance: m.TOLERANCE_DEBUT_DE_MANDAT_JOURS,
          contigu: m.ECART_ENTRE_MANDATS_CONTIGUS_JOURS,
        }));
        """
    )
    assert out["mandats"] == [
        ["2007-06-20", "2012-06-16"], ["2012-06-20", "2017-06-20"], ["2017-06-18", "2022-06-21"],
        ["2022-06-19", "2024-06-09"], ["2024-07-07", None],
    ]
    assert out["votes"] == [{"debut": "2007-06-20", "fin": "2012-06-16"}]
    assert out["paroles"] == [{"debut": "2007-06-20", "fin": "2017-06-20"}]
    assert out["sansBorne"] == []
    assert (out["tolerance"], out["contigu"]) == (7, 45)


def test_un_mandat_a_cheval_sur_la_borne_n_est_non_couvert_que_jusqu_a_elle() -> None:
    """Ségolène Royal, 19 juin 2002 → 19 juin 2007 : entièrement avant les deux
    bornes. Rapporté à une source qui commencerait au milieu du mandat, le
    manque s'arrête à la borne — et un mandat en cours (`fin` nulle) aussi."""
    out = _node(
        """
        const mandats = profilDe('segolene-royal').mandats
          .filter((x) => x.categorie === 'mandat_electif')
          .map((x) => ({ debut: x.debut, fin: x.fin }));
        console.log(JSON.stringify({
          mandats,
          avant: m.segmentsNonCouverts(mandats, '2012-06-20'),
          aCheval: m.segmentsNonCouverts(mandats, '2005-01-01'),
          enCours: m.segmentsNonCouverts(mandats.map((x) => ({ ...x, fin: null })), '2005-01-01'),
        }));
        """
    )
    assert out["mandats"] == [{"debut": "2002-06-19", "fin": "2007-06-19"}]
    assert out["avant"] == [{"debut": "2002-06-19", "fin": "2007-06-19"}]
    assert out["aCheval"] == [{"debut": "2002-06-19", "fin": "2005-01-01"}]
    assert out["enCours"] == [{"debut": "2002-06-19", "fin": "2005-01-01"}]


# ── Les deux mesures venues des sections 3 et 5 ─────────────────────────────


def test_un_terme_a_zero_ne_s_ecrit_pas_et_le_verbe_s_accorde() -> None:
    """Les nombres de François Ruffin, puis les mêmes avec des termes annulés.

    `themeSeul` et `sansDate` valent 0 sur les 31 fiches publiées au 01/10/2026 :
    leur ligne est donc muette aujourd'hui. Quand l'un des deux n'est pas nul, il
    a SA ligne, dans la formulation de l'encadré retiré de la section 5.
    """
    out = _node(
        """
        const base = extrait.fiches['francois-ruffin'].manques;
        const profil = profilDe('francois-ruffin');
        const lignes = (manques) => m.manquesDeLaFiche({ profil, limites: [], manques, bornesDuCorpus: bornes })
          .lignes.filter((l) => l.cle !== 'avant-la-borne').map((l) => [l.titre, l.texte]);
        console.log(JSON.stringify({
          base,
          sansSort: lignes({ ...base, votes: { ...base.votes, sansSort: 0 } }),
          toutSu: lignes({ votes: { total: 168, sansCommission: 0, sansSort: 0 },
                           paroles: { ...base.paroles, sansVerbatim: 0, sansQualite: 0 } }),
          unSeul: lignes({ votes: { total: 168, sansCommission: 1, sansSort: 0 },
                           paroles: { ...base.paroles, sansQualite: 1 } }),
          autres: lignes({ votes: base.votes, paroles: { ...base.paroles, themeSeul: 12, sansDate: 1 } }),
        }));
        """
    )
    assert out["base"]["paroles"]["themeSeul"] == 0 and out["base"]["paroles"]["sansDate"] == 0
    assert out["base"]["paroles"]["sansIntitule"] == 0
    assert out["sansSort"][0] == ["Votes", "Sur ses 168 votes, 39 n’ont pas de commission connue."]
    assert out["toutSu"] == [], "une phrase dont tous les termes sont nuls ne s'écrit pas"
    assert out["unSeul"] == [
        ["Votes", "Sur ses 168 votes, 1 n’a pas de commission connue."],
        [
            "Prises de parole",
            "Sur 3 499 prises de parole, 1 n’a pas de texte et 1 n’indique pas à quel titre la "
            "personne parlait.",
        ],
    ]
    assert out["autres"][2:] == [
        ["Prises de parole", "12 relèvent d’une collecte réduite au thème."],
        ["Prises de parole", "1 ne porte pas de date exploitable et reste hors du découpage."],
    ]


# ── Ce qui ne s'affiche plus, et ce qui reste ───────────────────────────────


def test_ni_etat_de_pipeline_ni_nom_de_champ_sur_la_fiche() -> None:
    """« Non collecté — collecte écartée par le run… (meta.collecte_ecartee,
    #357) » était du vocabulaire interne, et faux à l'écran quand la liste
    portait 3 522 entrées. « suspendu_pour_fonction_gouvernementale » est un nom
    de champ de notre schéma."""
    fiche = sans_commentaires(FICHE.read_text(encoding="utf-8"))
    for interdit in (
        "LIBELLE_ETAT", "non collecté", "hors couverture'", "fait établi", "e.preuve",
        "Ce que chaque liste porte", "Ce que la collecte signale", "ne dit pas de son parcours",
        "c.couverture", "c.limites",
    ):
        assert interdit not in fiche, f"« {interdit} » est revenu dans la fiche candidat"
    assert "Ce qui manque sur cette fiche" in fiche
    assert "manques={c.ceQuiManque}" in fiche
    profil = sans_commentaires(PROFIL.read_text(encoding="utf-8"))
    bloc = profil[profil.index("cle: 'suspension'") :]
    bloc = bloc[: bloc.index("});")]
    assert "suspendu_pour_fonction_gouvernementale" not in bloc
    assert "${" not in bloc, "la phrase validée ne porte aucun nombre"


def test_la_section_reste_la_ou_les_pourquoi_renvoient() -> None:
    """Le filtre par mot (#979) retire la section ; rien d'autre ne le fait."""
    fiche = FICHE.read_text(encoding="utf-8")
    ouverture = fiche.index('numero="6"')
    assert "{!filtre && (" in fiche[ouverture - 60 : ouverture]
    assert 'titre="Ce qu’on n’a pas pu lire"' in fiche[ouverture : ouverture + 80]
    assert "cp-couv-ecarts" in fiche
