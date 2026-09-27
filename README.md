# EMPREINTE POLITIQUE

![Projet en construction](https://img.shields.io/badge/PROJET-EN%20CONSTRUCTION-00E5FF?style=for-the-badge&labelColor=17141F)

> [!WARNING]
> **Ce projet est en construction.** Le pipeline et l'interface évoluent
> quotidiennement. Les données publiées sont réelles et sourcées, mais peuvent
> être incomplètes, et certaines absences portent encore une explication
> imprécise — ne pas conclure d'une liste vide sans lire son bloc `couverture`.
>
> Ce que le corpus contient, et depuis quand, se lit sur la page
> [Sources](https://empreinte-politique.fr/sources) du site.

**Empreinte politique** produit des « CV politiques » factuels et sourcés —
mandats, responsabilités, votes, textes portés, interventions en séance — pour
les candidats à l'élection présidentielle française de 2027, ainsi que pour les
groupes parlementaires et les gouvernements réels.

**Principe directeur** : tout fait affiché doit être traçable jusqu'à une source
primaire. Le projet agrège des faits ; il ne produit ni classement, ni score, ni
appréciation des positions politiques.

---

## Ce qu'on n'y trouvera pas

C'est ce qui distingue ce projet, et ce sont des règles non négociables,
dupliquées dans le schéma, dans la validation et dans la page méthodologie :

1. **Aucun jugement de valeur, aucun score, aucun classement.**
2. **Traçabilité intégrale** : chaque fait renvoie à une source primaire.
3. **Aucun taux de présence individuel n'est jamais publié.**
4. **Un 49.3 n'est jamais traité comme une position de vote** — c'est un fait de
   procédure, présenté comme tel.
5. **Une donnée manquante reste manquante**, jamais un `0` par défaut. Une liste
   vide se lit avec son bloc `couverture`, jamais toute seule.
6. Une position dans l'hémicycle exige une `source_url` vérifiable.
7. **Un ratio de groupe n'est publié qu'avec son numérateur, son dénominateur et
   une couverture suffisante** ; sinon `N/D`. Les écarts individu ↔ groupe sont
   du contrôle qualité interne, jamais public.
8. Les étiquettes thématiques sont des aides à la lecture, pas des positions
   déclarées par le candidat.

Le détail et le raisonnement : [`AGENTS.md`](AGENTS.md) §2 et §6.

## D'où viennent les données

| Source | Ce qu'elle apporte | Licence |
|---|---|---|
| [Open data de l'Assemblée nationale](https://data.assemblee-nationale.fr/) | **La seule source de l'activité parlementaire française** : identité, mandats, votes, amendements, dossiers, comptes rendus Syceron, questions | Licence Ouverte (Etalab) — attribution |
| [Open data du Sénat](https://data.senat.fr/) | **Les appartenances sénatoriales seulement** — mandats, groupes, commissions. Le jeu ne porte **ni scrutin ni compte rendu** | Licence Ouverte 2.0 (Etalab) — attribution |
| [Parltrack](https://parltrack.org) | Le volet européen des anciens eurodéputés | ODbL v1.0 — **partage à l'identique** |
| [Parlement européen](https://data.europarl.europa.eu/) | Le mandat européen, les scrutins et les dossiers cités | CC BY 4.0 — attribution, `User-Agent` identifiant le réutilisateur |
| [EuroVoc](https://publications.europa.eu/webapi/rdf/sparql) | Le **nom français** d'une matière européenne quand le Parlement n'en donne que l'identifiant, et son domaine | CC BY 4.0 — attribution, indication des modifications |
| [Sycomore](https://www2.assemblee-nationale.fr/sycomore/recherche) (Assemblée nationale) | **Citée, pas collectée** : les mandats de député antérieurs au 19/06/2002, relus à la main un par un | tous droits réservés — **seuls des faits** (fonction, dates) repris, avec leur lien |
| Journal officiel ([DILA](https://echanges.dila.gouv.fr/OPENDATA/JORF/), [Légifrance](https://www.legifrance.gouv.fr/)) | Les décrets, arrêtés et ordonnances parus depuis 2007, et les lois que chacun applique ou cite. Le texte des actes n'est pas republié. **Aucun rattachement à une personne** : la source ne publie pas le signataire | Licence Ouverte 2.0 (Etalab) — attribution |
| [Répertoire national des élus](https://www.data.gouv.fr/datasets/repertoire-national-des-elus-1) (RNE) + sortants 2026 | **Les mandats locaux** des candidats déclarés. La source ne publie **aucune date de fin** | Licence Ouverte 2.0 (Etalab) — attribution |
| Wikipédia / Wikidata | Le suivi des candidatures déclarées | CC BY-SA 4.0 / CC0 |
| [Conseil constitutionnel](https://www.conseil-constitutionnel.fr/) | **À venir** : la liste officielle des candidats et les parrainages, qui remplaceront Wikipédia pour dire qui est candidat. Aucune date n'est annoncée | non connue à ce jour |
| NosDéputés / NosSénateurs | **Plus collectées**, mais des champs déjà publiés en dérivent | ODbL v1.0 — **partage à l'identique** |

Ce que chaque fournisseur publie, ses pièges et ses URL :
[`docs/sources/`](docs/sources/) — la seule documentation qui dérive avec lui,
pas avec notre code.

Le corpus **n'est pas** sous une licence unique : chaque profil déclare dans
`meta.licence_donnees` les licences dont son propre contenu relève, dérivées de
ses `sources[]`. Le site HTML est une « œuvre dérivée » ODbL (attribution
suffisante) ; une republication des données brutes téléchargeables déclenche le
partage à l'identique.
→ [`AGENTS.md`](AGENTS.md) §7, [`docs/decisions/licence-lot-6-530.md`](docs/decisions/licence-lot-6-530.md)

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

`requirements-dev.txt` tire `requirements.txt` (les dépendances d'exécution) et
y ajoute `pytest`. Pour un environnement d'exécution seul — ce que font les jobs
d'extraction — installer `requirements.txt`.

Toutes les commandes se lancent **depuis la racine du dépôt**, environnement
virtuel activé.

## Une première chose à lancer

Le profil d'un candidat, brut puis pivot :

```bash
python3 src/generate_all_profiles.py --only jean-luc-melenchon --pivot
```

Puis l'interface, sur les données présentes en local :

```bash
cd web/UI_finale
npm install     # la première fois seulement
npm run dev     # synchronise les données puis démarre Vite
```

**Toutes les autres commandes du dépôt sont dans
[`docs/commandes.md`](docs/commandes.md)** — générer, auditer, vérifier avant de
committer, opérer, voir ce que voit l'utilisatrice. Une commande y est
documentée si l'on peut avoir à la lancer soi-même, et un test vérifie que ce
fichier ne cite ni un script disparu ni une option qui n'existe plus.

## Où vit quoi

```
raw_data/      Entrées déclaratives + collecte brute (proche de la source)
  candidats.json            la liste éditoriale des candidats déclarés
  lois_jorf.json            numéro de loi → identifiant au Journal officiel
  groupes_reels.json        les groupes parlementaires à produire
  gouvernements_reels.json  les gouvernements à produire, lus dans AMO30
  profiles/                 <slug>.json + une tranche par législature
pivot_data/    Le format pivot — la SEULE couche que web/ lit
  profiles/       <slug>.pivot.json
  groupes/        groupe-<SIGLE>-<leg>.json
  gouvernements/  gouvernement-<ID>.json
  lignees/        une fiche par lignée de groupe — la seule que web/ lit
  scrutins.json            index partagé des scrutins de l'Assemblée
  scrutins_europeens.json  les scrutins du PE cités, effectifs par groupe
  dossiers_europeens.json  référence de procédure → titre, stade, commission
  amendements/             index partagé, un fichier par législature
  actes_reglementaires/    décrets, arrêtés et ordonnances du Journal officiel,
                           un fichier par mois, avec un index de mots
  textes_promulgues.json   les textes promulgués, avec leur commission au fond
src/           Le pipeline (collecte, normalisation, agrégation, audits, gate)
scripts/       Les scripts d'exploitation (run local, bornage, rendu du formulaire)
web/UI_finale/ L'interface de production : React 19 + Vite
web/old/       Les générations de design archivées
docs/          La documentation (voir ci-dessous)
tests/         La suite pytest
```

`.cache/` et `logs/` sont créés automatiquement et git-ignorés.

Un profil pivot ne se lit **plus seul** : ses votes et ses amendements ne sont
que des renvois (`{scrutin_id, position}`, `{amendement_id, role_signataire}`)
vers les index partagés. Pourquoi, et ce que ça a fait gagner :
[`docs/data-architecture.md`](docs/data-architecture.md).

## Où aller pour le reste

| Question | Fichier |
|---|---|
| **« Qu'est-ce qui alimente quoi ? »** — la carte des sources aux fiches publiées, en figure | [`docs/fabrique-du-jeu-de-donnees.html`](docs/fabrique-du-jeu-de-donnees.html) |
| **« Quelle était la commande, déjà ? »** | [`docs/commandes.md`](docs/commandes.md) |
| **« Que devient la donnée ? »** — flux, schémas, sorties de `pivot_data/`, volumétrie | [`docs/data-architecture.md`](docs/data-architecture.md) |
| **« Que fait un run ? »** — les jobs, le formulaire, caches, artifacts, budgets, le push, la relance automatique | [`docs/workflow-generate-data.md`](docs/workflow-generate-data.md) |
| **« Comment marche l'extraction pilotée par roster ? »** — le seul job qui a une page à lui | [`docs/extract-roster-groupes.md`](docs/extract-roster-groupes.md) |
| **« Pourquoi c'est fait comme ça ? »** — une décision par fichier | [`docs/decisions/`](docs/decisions/), indexées par [`docs/technical_decisions.md`](docs/technical_decisions.md) |
| **« Où cette source publie-t-elle ce champ ? »** | [`docs/sources/`](docs/sources/) |
| **Les règles non négociables, pour un agent comme pour un humain** | [`AGENTS.md`](AGENTS.md) |
| **Ce qui est planifié, et les défauts connus restés ouverts** | [`ROADMAP.md`](ROADMAP.md) |

`/rapports` réunit les articles publiés : ce que les fiches disent d'un sujet, au
jour des données qui l'ont produit, chaque fait lié à sa source. Un instantané
n'est jamais mis à jour — un sujet repris plus tard en donne un nouveau, à une
nouvelle adresse.

## Ce que la couverture ne couvre pas encore

**La page [« Sources »](https://empreinte-politique.fr/sources) du site est la
référence** : elle dit, pour les trois populations publiées, ce que le dépôt
porte, depuis quand, et les fiches où la donnée manque. Ce fichier n'en garde
que la liste des limites — leur détail, leurs mesures et leurs dates vivent dans
[`docs/data-architecture.md`](docs/data-architecture.md) et dans les décisions
citées.

- **Groupes** — seuls ceux déclarés dans `raw_data/groupes_reels.json` sont
  produits, une fiche par groupe **et par législature**, publiées en une page
  par lignée. Les groupes du **Sénat restent gelés** : `data.senat.fr` ne porte
  aucun scrutin, donc le cœur d'une fiche de groupe resterait vide.
- **Gouvernements** — ceux que le référentiel AMO30 de l'Assemblée publie, depuis
  Fillon I (17/05/2007) ; pas toute la Ve République. `membres[]` porte une
  entrée **par période**, pas par personne.
- **Textes portés** — les archives de dossiers de l'Assemblée s'arrêtent à la
  XIV<sup>e</sup> législature, donc rien avant le **20/06/2012** : les
  gouvernements Fillon et Ayrault I sont hors couverture, et leur `textes: []`
  est une absence de source, jamais « aucun texte porté ».
- **Sénat** — **les appartenances, jamais l'activité**. La condition posée pour
  rouvrir la chambre est **déclarée non remplie**, pas contournée.
- **Parlement européen** — lu comme une institution à part entière ; pour
  certains candidats, c'est **tout** leur mandat parlementaire. Aucun dump ne
  porte le **sort** d'un amendement, et les entrées antérieures au 22/11/2016
  portent la date de leur **republication**, pas celle de la séance.
- **Journal officiel** — le signataire d'un décret n'est pas publié par la
  source : un acte se rattache à un gouvernement par sa **date de parution**,
  jamais à une personne. Et un acte sans lien vers une loi n'est pas un acte pris
  sans loi — Légifrance pose la qualification longtemps après la parution.
- **Interventions** — Syceron est la seule source, et la résolution des
  identifiants d'acteur nus reste livrée inactive : une collecte fraîche ne rend
  que les questions officielles.
- **Mandats locaux** — la couverture **commence en 2020** : avant cette borne,
  une absence se lit « non couvert », jamais « aucun mandat local ».
- **Biais de couverture** — un ancien parlementaire laisse des traces bien plus
  riches qu'un candidat qui ne l'a jamais été.

## Tests

```bash
pytest -q
```

La suite s'exécute sur chaque pull request et chaque push sur `main`. Elle est
**découplée du corpus vivant** : aucun test ne lit `pivot_data/` ni
`raw_data/profiles/`, aucun n'écrit sous l'un des deux, aucun ne sort sur le
réseau. Le job CI le rend structurel — il ne pose sur le disque du runner qu'une
liste blanche de chemins, si bien qu'un test qui se recouplerait au corpus y
échoue en nommant le fichier.
→ [`docs/decisions/ci-tests-pytest.md`](docs/decisions/ci-tests-pytest.md)

## Licence

**Le code est sous AGPL-3.0** ([`LICENSE`](LICENSE)) : utilisable, modifiable et
redistribuable, à une condition — qui met en ligne un service fondé sur une
version modifiée doit en publier le code sous la même licence.

**Les textes rédigés pour le site et la charte graphique sont tous droits
réservés** : une licence de logiciel porte sur le code, pas sur la prose ni sur
la marque.

**Les données, elles, gardent les licences de leurs sources** — et elles ne sont
pas les mêmes d'un champ à l'autre : l'obligation de partage à l'identique de
l'ODbL vit sur certains, pas sur tous ([`AGENTS.md`](AGENTS.md) §7,
[`docs/decisions/licences.md`](docs/decisions/licences.md)). La licence du code
n'y change rien.
