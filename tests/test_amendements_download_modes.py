"""Quatre modes de défaillance de `data.assemblee-nationale.fr` (#443, #1050).

Testés contre un **vrai serveur HTTP local** et non des doubles de `requests` :
ce qui est en cause ici est le comportement du transfert lui-même — un corps
tronqué par rapport au `Content-Length` annoncé, une connexion fermée en cours
de flux — que seul un vrai serveur reproduit fidèlement (`iter_content` lève
alors depuis urllib3, comme en production). Un mock ne prouverait que le chemin
nominal, celui qui n'a jamais posé de problème.

Relevé du 18/08/2026 sur `Amendements_XV.json.zip` (648 Mo), reconfirmé le
19/08 :

| État | `Range`                        | GET séquentiel      |
| ---- | ------------------------------ | ------------------- |
| 1    | fonctionne                     | —                   |
| 2    | 0 octet à toutes les tailles   | délivre             |
| 3    | 0 octet                        | coupe à 13-25 Mo    |
| 4    | délivre DEUX versions          | délivre l'une ou l'autre |

Le serveur annonce `Accept-Ranges: bytes` et un `Content-Length` correct dans
les quatre états : aucune sonde ne les distingue, seul le transfert le peut.
Le quatrième (relevé du 21/09/2026, #1050) est le seul que la taille finale ne
trahit pas — l'archive recollée fait exactement le nombre d'octets annoncé.
"""

import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from candidate_profile import (  # noqa: E402
    SourceAmendementsIncoherenteError,
    SourceAmendementsIndisponibleError,
    _download_amendements_zip,
)

PAYLOAD = bytes(range(256)) * 4  # 1024 octets, contenu non répétitif par bloc


class _FauxCDN(BaseHTTPRequestHandler):
    """Reproduit les modes de défaillance observés sur le CDN de l'AN.

    Chaque mode est décrit par deux fonctions portées par le serveur :
    `octets_range(debut, fin)` -> combien d'octets du segment demandé sont
    réellement délivrés (le `Content-Length` annoncé, lui, reste toujours celui
    du segment complet : c'est précisément ce décalage qui fait lever le
    client), et `octets_sequentiel(n_appel)` -> combien d'octets un GET sans
    en-tête `Range` délivre.
    """

    protocol_version = "HTTP/1.1"

    def log_message(self, *args):  # silence : le test n'a pas besoin du journal
        pass

    def setup(self):
        # Une instance de handler = une connexion TCP, réutilisée pour toutes
        # les requêtes keep-alive qui y passent. C'est ce qui permet de
        # modéliser l'affinité de backend de #1050, et de compter les
        # connexions ouvertes par le client.
        self.server.connexions += 1
        self.numero_connexion = self.server.connexions
        super().setup()

    def _version(self):
        """`(payload, etag)` servis à cette requête. Par défaut une seule
        version et aucun validateur — c'est l'état d'avant #1050, et les tests
        des états 1 à 3 doivent continuer à le voir tel quel."""
        choisir = getattr(self.server, "choisir_version", None)
        if choisir is None:
            return self.server.payload, None
        return choisir(self)

    def do_HEAD(self):
        payload, etag = self._version()
        self.send_response(200)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Accept-Ranges", "bytes")
        if etag:
            self.send_header("ETag", etag)
        self.end_headers()

    def do_GET(self):
        payload, etag = self._version()
        entete_range = self.headers.get("Range")
        if_range = self.headers.get("If-Range")
        if entete_range and etag and if_range and if_range != etag:
            # Validateur périmé : la RFC demande de servir la ressource
            # ENTIÈRE, en 200, au lieu de la plage. Vérifié le 21/09/2026 sur
            # data.assemblee-nationale.fr, qui se comporte ainsi.
            self.server.range_refuses += 1
            entete_range = None
        if entete_range:
            debut, fin = (int(x) for x in entete_range.removeprefix("bytes=").split("-"))
            fin = min(fin, len(payload) - 1)
            self.server.appels_range.append(debut)
            attendu = payload[debut : fin + 1]
            livres = self.server.octets_range(debut, fin)
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {debut}-{fin}/{len(payload)}")
            # Toujours la taille du segment complet : le CDN annonce un
            # Content-Length correct même dans les états où il ne délivre rien.
            self.send_header("Content-Length", str(len(attendu)))
            if etag:
                self.send_header("ETag", etag)
            self.end_headers()
            corps = attendu[:livres]
            annonce = len(attendu)
        else:
            self.server.appels_sequentiels += 1
            livres = self.server.octets_sequentiel(self.server.appels_sequentiels)
            self.send_response(200)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Accept-Ranges", "bytes")
            if etag:
                self.send_header("ETag", etag)
            self.end_headers()
            corps = payload[:livres]
            annonce = len(payload)
        if corps:
            self.wfile.write(corps)
        self.wfile.flush()
        # Moins d'octets que le Content-Length annoncé : la connexion est
        # fermée en cours de corps, le client lève (IncompleteRead) après avoir
        # tout de même reçu — et, correctif de #443, écrit — le préfixe. Une
        # réponse complète, elle, laisse la connexion ouverte : c'est ce que
        # fait un vrai serveur en HTTP/1.1, et c'est ce qui permet de compter
        # les connexions réellement ouvertes par le client (#1050).
        if len(corps) < annonce:
            self.close_connection = True


class _Serveur(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def _demarrer_serveur(payload, octets_range, octets_sequentiel, choisir_version=None):
    serveur = _Serveur(("127.0.0.1", 0), _FauxCDN)
    serveur.payload = payload
    serveur.octets_range = octets_range
    serveur.octets_sequentiel = octets_sequentiel
    serveur.choisir_version = choisir_version
    serveur.appels_range = []
    serveur.appels_sequentiels = 0
    serveur.connexions = 0
    serveur.range_refuses = 0
    threading.Thread(target=serveur.serve_forever, daemon=True).start()
    return serveur


@pytest.fixture
def cdn():
    """Serveur local paramétrable, arrêté en fin de test."""
    serveurs = []

    def _fabrique(octets_range, octets_sequentiel, payload=PAYLOAD, choisir_version=None):
        serveur = _demarrer_serveur(payload, octets_range, octets_sequentiel, choisir_version)
        serveurs.append(serveur)
        return serveur

    yield _fabrique
    for serveur in serveurs:
        serveur.shutdown()
        serveur.server_close()


def _url(serveur):
    return f"http://127.0.0.1:{serveur.server_address[1]}/Amendements.json.zip"


def _telecharger(serveur, zip_path, **kwargs):
    kwargs.setdefault("chunk_bytes", 128)
    kwargs.setdefault("max_attempts", 3)
    kwargs.setdefault("stall_max_cycles", 2)
    kwargs.setdefault("stall_wait_seconds", 0)
    with patch("candidate_profile.time.sleep", return_value=None):
        _download_amendements_zip(_url(serveur), zip_path, "15", **kwargs)


# ---------------------------------------------------------------------------
# État 1 — `Range` fonctionne : reprise par segments, le mode nominal (#241).
# ---------------------------------------------------------------------------

def test_etat_1_range_fonctionne_telecharge_par_segments(tmp_path, cdn):
    serveur = cdn(
        octets_range=lambda debut, fin: fin - debut + 1,  # segment complet
        octets_sequentiel=lambda n: len(PAYLOAD),
    )
    zip_path = tmp_path / "amendements.zip"
    _telecharger(serveur, zip_path)

    assert zip_path.read_bytes() == PAYLOAD
    assert serveur.appels_range == [0, 128, 256, 384, 512, 640, 768, 896]
    assert serveur.appels_sequentiels == 0, (
        "Tant que le Range fonctionne, aucun repli séquentiel ne doit être déclenché"
    )


# ---------------------------------------------------------------------------
# Le défaut aggravant de #443 : les octets reçus étaient jetés quand la coupure
# survenait en cours de segment (`b"".join(resp.iter_content(...))`).
# ---------------------------------------------------------------------------

def test_coupure_en_cours_de_segment_conserve_les_octets_recus(tmp_path, cdn):
    """Une coupure en cours de segment doit reprendre à l'octet **réellement
    obtenu**, pas au début du segment.

    Ce test est le discriminant du correctif central : avec le
    `b"".join(resp.iter_content(...))` d'origine, le segment était relancé
    depuis son offset de départ et les octets déjà reçus étaient perdus — les
    offsets demandés seraient donc 0, 0, 0, … et le téléchargement n'avancerait
    jamais.
    """
    serveur = cdn(
        # La moitié du segment demandé (au moins un octet), puis coupure — à
        # chaque fois : le cas où la coupure tombe à un point arbitraire.
        octets_range=lambda debut, fin: max(1, (fin - debut + 1) // 2),
        octets_sequentiel=lambda n: 0,
    )
    zip_path = tmp_path / "amendements.zip"
    _telecharger(serveur, zip_path)

    assert zip_path.read_bytes() == PAYLOAD, "Le fichier doit être reconstitué octet pour octet"
    assert serveur.appels_range == sorted(set(serveur.appels_range)), (
        "Les offsets demandés doivent être strictement croissants : jamais deux fois "
        "le même point de départ, sinon des octets déjà reçus ont été jetés"
    )
    assert serveur.appels_range[:3] == [0, 64, 128]
    assert serveur.appels_sequentiels == 0, (
        "Un segment qui progresse, même partiellement, n'est pas une panne de Range : "
        "aucun repli séquentiel ne doit être déclenché"
    )


# ---------------------------------------------------------------------------
# État 2 — `Range` mort à toutes les tailles, GET séquentiel opérant.
# ---------------------------------------------------------------------------

def test_etat_2_range_mort_bascule_sur_le_get_sequentiel(tmp_path, cdn):
    """Range annoncé (206 + Content-Range corrects) mais 0 octet délivré, quelle
    que soit la taille de segment : le repli doit être le GET séquentiel, pas
    une réduction de la taille de segment (inopérante — 8 Kio échouent autant
    que 32 Mio)."""
    serveur = cdn(
        octets_range=lambda debut, fin: 0,
        octets_sequentiel=lambda n: len(PAYLOAD),
    )
    zip_path = tmp_path / "amendements.zip"
    _telecharger(serveur, zip_path)

    assert zip_path.read_bytes() == PAYLOAD
    assert serveur.appels_sequentiels == 1, "Le GET séquentiel doit avoir servi et suffi"


def test_etat_2_petit_chunk_ne_sauve_rien_seul_le_sequentiel_le_fait(tmp_path, cdn):
    """La taille de segment n'est pas la dimension en cause : avec des segments
    de 8 octets comme de 128, c'est le repli séquentiel qui débloque."""
    serveur = cdn(
        octets_range=lambda debut, fin: 0,
        octets_sequentiel=lambda n: len(PAYLOAD),
    )
    zip_path = tmp_path / "amendements.zip"
    _telecharger(serveur, zip_path, chunk_bytes=8)

    assert zip_path.read_bytes() == PAYLOAD
    assert serveur.appels_sequentiels == 1


def test_etat_2_un_prefixe_sequentiel_plus_court_ne_remplace_jamais_un_plus_long(tmp_path, cdn):
    """« Ne jamais jeter un préfixe valide, d'où qu'il vienne » : quand une
    tentative séquentielle rend moins d'octets que le préfixe déjà détenu, elle
    doit être écartée, pas écrire par-dessus.

    Discriminant : sans la comparaison de longueur, le fichier final ferait
    300 octets au lieu de 700 — la deuxième tentative ayant tronqué la
    première."""
    longueurs = {1: 700, 2: 300, 3: 300}
    serveur = cdn(
        octets_range=lambda debut, fin: 0,
        octets_sequentiel=lambda n: longueurs.get(n, 300),
    )
    zip_path = tmp_path / "amendements.zip"
    with pytest.raises(SourceAmendementsIndisponibleError):
        _telecharger(serveur, zip_path, stall_max_cycles=2)

    assert zip_path.read_bytes() == PAYLOAD[:700], (
        "Le plus long préfixe obtenu doit être conservé intact, y compris après "
        "des tentatives ultérieures plus courtes"
    )


# ---------------------------------------------------------------------------
# État 3 — `Range` mort ET GET séquentiel coupé : aucun repli réseau ne marche.
# ---------------------------------------------------------------------------

def test_etat_3_leve_une_erreur_de_source_indisponible(tmp_path, cdn):
    """Le message doit dire que la **source** est indisponible, pas que le
    téléchargement a échoué : la personne qui lit le log n'en fait pas la même
    chose — dans un cas elle relance, dans l'autre elle attend."""
    serveur = cdn(
        octets_range=lambda debut, fin: 0,
        octets_sequentiel=lambda n: 200,  # coupe toujours au même point
    )
    zip_path = tmp_path / "amendements.zip"
    with pytest.raises(SourceAmendementsIndisponibleError) as exc_info:
        _telecharger(serveur, zip_path, stall_max_cycles=2)

    message = str(exc_info.value)
    assert "source" in message.lower() and "indisponible" in message.lower()
    assert "data.assemblee-nationale.fr" in message
    assert "pas un échec de téléchargement à relancer" in message
    assert "15" in message, "La législature concernée doit figurer dans le message"


def test_etat_3_reste_attrapable_par_les_appelants_existants(tmp_path, cdn):
    """Les appelants existants font `except (requests.RequestException, OSError)`
    ; le nouveau type doit y rester pris, sans quoi l'erreur remonterait non
    gérée jusqu'au job CI au lieu d'être convertie en `AmendementsIndexError`."""
    assert issubclass(SourceAmendementsIndisponibleError, OSError)

    serveur = cdn(
        octets_range=lambda debut, fin: 0,
        octets_sequentiel=lambda n: 200,
    )
    zip_path = tmp_path / "amendements.zip"
    with pytest.raises(OSError):
        _telecharger(serveur, zip_path, stall_max_cycles=2)


def test_etat_3_attend_entre_deux_cycles_au_lieu_de_marteler(tmp_path, cdn):
    """Attente avec intervalle, et nombre de requêtes borné : dans cet état,
    réessayer en boucle ne rend aucun octet et ne fait que consommer du budget
    CI et de la bande passante chez l'AN."""
    serveur = cdn(
        octets_range=lambda debut, fin: 0,
        octets_sequentiel=lambda n: 200,
    )
    zip_path = tmp_path / "amendements.zip"
    with patch("candidate_profile.time.sleep") as faux_sleep:
        with pytest.raises(SourceAmendementsIndisponibleError):
            _download_amendements_zip(
                _url(serveur), zip_path, "15", chunk_bytes=128, max_attempts=2,
                stall_max_cycles=3, stall_wait_seconds=42,
            )

    # Déroulé : un premier cycle productif (le GET séquentiel rend les 200
    # premiers octets), puis `stall_max_cycles` cycles où plus rien n'arrive.
    attentes = [appel.args[0] for appel in faux_sleep.call_args_list]
    assert attentes.count(42) == 2, (
        "Une attente de l'intervalle demandé entre deux cycles sans progrès (le "
        "dernier échoue sans attendre)"
    )
    assert serveur.appels_sequentiels == 4, (
        "Un seul GET séquentiel par cycle (1 productif + 3 sans progrès), pas de martèlement"
    )
    assert len(serveur.appels_range) == 8, (
        "max_attempts=2 plages par cycle et pas davantage, sur les 4 cycles"
    )


def test_etat_3_conserve_le_prefixe_obtenu_pour_la_prochaine_invocation(tmp_path, cdn):
    """Même en échec définitif, le préfixe obtenu reste sur disque : c'est lui
    que la sonde de reprise trouvera à la prochaine invocation, quand la source
    sera redevenue disponible."""
    serveur = cdn(
        octets_range=lambda debut, fin: 0,
        octets_sequentiel=lambda n: 200,
    )
    zip_path = tmp_path / "amendements.zip"
    with pytest.raises(SourceAmendementsIndisponibleError):
        _telecharger(serveur, zip_path, stall_max_cycles=2)

    assert zip_path.read_bytes() == PAYLOAD[:200]
    assert not (tmp_path / "amendements.zip.seq").exists(), (
        "Le fichier de travail du repli séquentiel ne doit pas rester sur disque"
    )


# ---------------------------------------------------------------------------
# Arbitrage à l'exécution : le mode de défaillance change en quelques minutes,
# il ne peut donc pas être choisi par configuration.
# ---------------------------------------------------------------------------

def test_arbitrage_a_l_execution_le_range_repris_des_qu_il_refonctionne(tmp_path, cdn):
    """Range mort au départ (repli séquentiel, préfixe conservé), puis de nouveau
    opérant : la reprise par segments doit repartir du préfixe déjà obtenu, sans
    le retélécharger."""
    etat = {"range_vivant": False}

    def octets_range(debut, fin):
        return (fin - debut + 1) if etat["range_vivant"] else 0

    def octets_sequentiel(n):
        etat["range_vivant"] = True  # le CDN change d'état après ce transfert
        return 512

    serveur = cdn(octets_range=octets_range, octets_sequentiel=octets_sequentiel)
    zip_path = tmp_path / "amendements.zip"
    _telecharger(serveur, zip_path)

    assert zip_path.read_bytes() == PAYLOAD
    assert serveur.appels_sequentiels == 1
    assert [o for o in serveur.appels_range if o >= 512] == [512, 640, 768, 896]
    assert 128 not in serveur.appels_range[1:], (
        "Le préfixe séquentiel de 512 octets ne doit pas être retéléchargé par plages"
    )


def test_arbitrage_sonde_au_decalage_courant_pas_en_tete_de_fichier(tmp_path, cdn):
    """Mesuré le 19/08/2026 : une plage à l'octet 0 ou à 4 Mio est servie
    normalement pendant que la même plage à 64 Mio ne rend rien. Sonder le
    support du `Range` en tête de fichier conclurait donc à tort qu'il
    fonctionne — l'arbitrage doit porter sur le décalage courant."""
    serveur = cdn(
        # Le Range fonctionne sur les 256 premiers octets seulement.
        octets_range=lambda debut, fin: (fin - debut + 1) if debut < 256 else 0,
        octets_sequentiel=lambda n: len(PAYLOAD),
    )
    zip_path = tmp_path / "amendements.zip"
    _telecharger(serveur, zip_path)

    assert zip_path.read_bytes() == PAYLOAD
    assert serveur.appels_range[:2] == [0, 128], "Les plages servies en tête doivent être utilisées"
    assert serveur.appels_sequentiels == 1, (
        "Le repli séquentiel doit se déclencher au décalage où le Range meurt, "
        "et pas rester inhibé par le succès des premières plages"
    )


# ---------------------------------------------------------------------------
# État 4 — la source sert DEUX versions de la même URL (#1050).
#
# Mesuré le 21/09/2026 sur `…/17/loi/amendements_div_legis/Amendements.json.zip` :
# 10 requêtes HEAD, 8 fois l'ETag `"11e77868-65bee362fa5cb"` (300 382 312
# octets) et 2 fois `"11e807a3-65befe27af972"` (300 418 979). Sept plages
# enchaînées sur UNE connexion keep-alive rendent en revanche toutes la même.
# Recoller des segments prélevés au hasard sur l'une ou l'autre produit un
# fichier de la taille annoncée et illisible : le seul des quatre états que la
# garde de taille finale ne voit pas.
# ---------------------------------------------------------------------------

PAYLOAD_B = bytes(range(255, -1, -1)) * 4  # même longueur que PAYLOAD, tout autre contenu
ETAG_A = '"version-a"'
ETAG_B = '"version-b"'


def _versions_par_connexion(handler):
    """Affinité de backend : une connexion voit toujours la même version, deux
    connexions successives n'en voient pas la même. C'est le comportement
    observé sur la source réelle."""
    if handler.numero_connexion % 2 == 1:
        return PAYLOAD, ETAG_A
    return PAYLOAD_B, ETAG_B


def test_etat_4_tous_les_segments_passent_par_une_seule_connexion(tmp_path, cdn):
    """L'affinité de connexion est la première des deux gardes : c'est elle qui
    rend l'incohérence rare au lieu de majoritaire. Sans elle, chaque segment
    rejoue le tirage entre les deux backends — sur 8 segments et un partage
    mesuré à 80/20, l'archive avait ~17 % de chances d'être cohérente."""
    serveur = cdn(
        octets_range=lambda debut, fin: fin - debut + 1,
        octets_sequentiel=lambda n: len(PAYLOAD),
        choisir_version=_versions_par_connexion,
    )
    zip_path = tmp_path / "amendements.zip"
    _telecharger(serveur, zip_path)

    assert zip_path.read_bytes() == PAYLOAD, (
        "Les 8 segments doivent tous venir de la version servie par la première connexion"
    )
    assert serveur.connexions == 1, (
        f"Les segments doivent être enchaînés sur une seule connexion, "
        f"{serveur.connexions} ouvertes"
    )


def test_etat_4_une_version_qui_change_fait_redemarrer_sans_jamais_recoller(tmp_path, cdn):
    """La version change au milieu du téléchargement : le préfixe déjà obtenu
    n'est plus complétable, il est jeté et tout redémarre. Le discriminant est
    le CONTENU final — avant #1050, le fichier faisait la bonne taille en
    mélangeant les deux versions, et seule la décompression le révélait."""
    etat = {"requetes": 0}

    def versions_par_requete(handler):
        etat["requetes"] += 1
        # Les deux premiers segments viennent de A, la suite de B : le cas
        # d'une archive republiée en cours de transfert.
        return (PAYLOAD, ETAG_A) if etat["requetes"] <= 2 else (PAYLOAD_B, ETAG_B)

    serveur = cdn(
        octets_range=lambda debut, fin: fin - debut + 1,
        octets_sequentiel=lambda n: len(PAYLOAD_B),
        choisir_version=versions_par_requete,
    )
    zip_path = tmp_path / "amendements.zip"
    _telecharger(serveur, zip_path)

    octets = zip_path.read_bytes()
    assert octets == PAYLOAD_B, (
        "Le fichier final doit provenir d'UNE seule version, celle servie après le changement"
    )
    assert octets[:128] != PAYLOAD[:128], (
        "Le début doit avoir été réécrit : garder le préfixe de la version A et lui "
        "coudre la fin de la version B est exactement le défaut de #1050"
    )
    assert serveur.range_refuses >= 1, (
        "Le serveur doit avoir refusé au moins une plage sur `If-Range` périmée — "
        "c'est la garde qui détecte le changement au segment où il se produit"
    )
    assert serveur.appels_range.count(0) >= 2, "Le téléchargement doit avoir redémarré à l'octet 0"


def test_etat_4_une_source_durablement_incoherente_echoue_en_le_disant(tmp_path, cdn):
    """Quand la version change à CHAQUE requête, aucun redémarrage ne converge.
    Il faut alors échouer, et le dire avec le bon mot : la source n'est pas
    indisponible — elle délivre parfaitement — elle est incohérente avec
    elle-même. Le log oriente la personne qui le lit, et « échec du
    téléchargement » l'enverrait chercher une panne réseau qui n'existe pas."""
    etat = {"requetes": 0}

    def versions_alternees(handler):
        etat["requetes"] += 1
        return (PAYLOAD, ETAG_A) if etat["requetes"] % 2 else (PAYLOAD_B, ETAG_B)

    serveur = cdn(
        octets_range=lambda debut, fin: fin - debut + 1,
        octets_sequentiel=lambda n: 0,
        choisir_version=versions_alternees,
    )
    zip_path = tmp_path / "amendements.zip"

    with pytest.raises(SourceAmendementsIncoherenteError) as exc:
        _telecharger(serveur, zip_path)

    assert "incohérente" in str(exc.value)
    octets = zip_path.read_bytes() if zip_path.is_file() else b""
    assert PAYLOAD.startswith(octets) or PAYLOAD_B.startswith(octets), (
        "Même en échec, les octets laissés sur disque doivent être le préfixe d'UNE "
        "version, jamais un mélange des deux"
    )
