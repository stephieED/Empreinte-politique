<a id="hors-perimetre"></a>
# Deferred / out-of-scope investigations

`en continu`

> **En bref** — investigations menées puis écartées : Sénat open data, textes UE, portefeuille ministériel, agenda, maires…

Findings from explored sources that led to a "not now" verdict, with full
rationale — kept here rather than in `ROADMAP.md` so the reasoning survives
even if the backlog entry itself is reworded or dropped.

## Senate votes, amendments, sponsored texts

Explored `data.senat.fr`'s open data catalog (2026). No structured roll-call
vote dataset exists at all (unlike AN's `Scrutins.json.zip`). `ameli.zip`
(amendments) is a raw 717 MB SQL dump (`ameli.sql`), not per-senator
JSON/CSV — impractical to download/parse on every run. `dossiers-legislatifs.csv`
has no author/sponsor field, so per-senator sponsored texts would require
scraping individual `dossier-legislatif` HTML pages (fragile, out of pattern
with the rest of this project's official-JSON-based sources). A full Senate
pipeline equivalent to the AN one is not currently feasible without a fragile
HTML-scraping approach. No official structured vote source has been found
as an alternative either.

**Senate *debates* are a distinct case, settled separately by #501.** This
section covers roll-call votes, amendments and sponsored texts; it says nothing
about floor speeches, which come from `archive.nossenateurs.fr` rather than from
`data.senat.fr`. Measured on 2026-08-20: that archive *does* serve both the
intervention search and the per-document detail, and serves them fast (0,2-0,9 s
per document). What it does not serve is the **attribution**:
`fetch_intervention_details` resolves a speaker through the document's
`url_nosdeputes` key, and the Senate archive publishes `url_nossenateurs`
instead — so every Senate intervention is classified `mention` and dropped, and
0 of the 789 published interventions come from the Senate. `extract-senat`
therefore hard-codes `--skip-interventions`. Unlike votes and amendments, this
one is a **fixable** limitation, not a missing dataset — see
[[interventions-senat-501]] and `ROADMAP.md`.

Applies to the gouvernement view's `textes[]` too (confirmed in
[[gouvernement-doc-cloture]], #214): `gouvernement_textes.py` only reads the
AN dossiers-legislatifs dump, so a bill whose primary deposit chamber is the
Senate is never captured, regardless of `schema_gouvernement.py` exposing a
`"Senat"` value for `chambre_depot_initial` (reachable only via texts
deposited at the AN and later transmitted to the Senate).

## European Parliament — textes_portés / amendements via the official API

Explored the EP Open Data Portal API v2 (2026). `/plenary-documents`
(reports) and `/documents?work_type=AMENDMENT_LIST` exist, but neither
exposes a structured author/rapporteur field referencing a `person/<id>`
MEP URI — the rapporteur name only appears as free text inside multilingual
titles. No server-side filter works (`creator=person/<id>` and text-search
params are all silently ignored). The `/plenary-documents` corpus is
~10-15k documents with no per-item title in the list response, so
identifying a given MEP's reports would require fetching every document's
detail individually — at the API's 500 req/5min rate limit, a full scan
takes 1h30+ per regeneration run. Amendment-list documents are further
compiled per-report batches, not per-amendment/per-signatory records, so
even textual matching would only attribute a whole batch to the report's
rapporteur, not individual amendments to their actual authors.

**Status: superseded.** A follow-up investigation into third-party
aggregators (Parltrack, HowTheyVote) found a viable path — see
[`investigation-sources-ue.md`](investigation-sources-ue.md) for the comparative
feasibility verdict and implementation brief. This entry is kept for
context on why the official-API-only approach was abandoned.

## Ministerial function — precise portfolio title

**RÉSOLU (#382/#383, 2026-08-17) — section conservée pour l'historique.**

L'affirmation ci-dessous (« no open-data source has been identified yet »)
était **factuellement inexacte** : le même jeu de données bulk expose un
`typeOrgane == "MINISTERE"` portant l'intitulé précis (« Ministère de la
cohésion des territoires », « Secrétariat d'État auprès du ministre de la
transition écologique »), soit 52 intitulés distincts sur les profils
analysés. Il n'était simplement pas mappé. Désormais exploité — voir
[[taxonomie-mandats-typeorgane-an]], et
[[gouvernement-premier-ministre-portefeuille]] pour sa consommation par les
profils de gouvernement (#398 : le mapping de #382/#383 avait rendu l'intitulé
disponible sans que `gouvernement_profile.py` le lise).

*Constat d'origine, dépassé :* `mandats[].categorie ==
"fonction_gouvernementale"` is sourced from the AN `acteurs_historique` bulk
dataset (`organe.codeType == "GOUVERNEMENT"`), which only identifies *which*
government (e.g. "BORNE", "CASTEX") an elected official belonged to and the
dates — not the specific portfolio title (e.g. "Ministre de l'Intérieur"). No
open-data source for the precise portfolio has been identified yet.

## Extra-parliamentary bodies

Corresponds to the `extra_parlementaire` category already planned in
`schema_pivot.KNOWN_CATEGORIES`, but matching to a profile can only be done
by free-text name (no `acteurRef`) — a real risk of false positives on
homonyms. Not implemented without a careful matching strategy (e.g. name +
group, or accepting partial coverage rather than a bad match).

## Agenda / committee meetings dataset

`.../vp/reunions/Agenda.json.zip` describes committee/plenary meetings
(agenda, bills examined). Organized by body/meeting, not by individual —
more useful for precisely dating when a bill was examined in committee than
for enriching an individual profile directly. No expressed need for this
today.

## Mayors

No dedicated collection module or source identified yet.

## HATVP lobby register

`AGENTS.md` pointed at a `docs/hatvp_opendata.md` that **never existed** —
removed on 30/08/2026, same family as the three phantom anchors (`#positionnement`,
`#fusion`, `#cas-limites`). The subject itself is real and stays out of scope,
so the verdict is recorded here instead of in a file nobody can open.

The HATVP register lists **interest representatives** (lobbies), not elected
officials' records: it describes who lobbies whom, which is a different object
from a factual political CV (§1). No collection module, no source explored, no
expressed need.

Not to be confused with the **only** HATVP datum the pipeline does carry:
`identite.uri_hatvp` (and its `identifiants.hatvp` twin, #539), a URI to a
member's own declaration of interests, read from AN open data's AMO30
referential — never from the lobby register. See
[[identite-profils-539]] and [[absences-publiees-comme-faits-556-558-560]].

### Re-examined on 31/08/2026, and deliberately left undecided

The question came back during the #594 brainstorm — *would it make sense to show
interest representations on an Empreinte politique page?* The owner's answer:
**the point is recorded, it will not be worked on, and no decision is taken on it
in the short term.** What follows exists so the same ground is not covered a
third time, not to prepare an implementation.

**What was said against putting it on a person's page.** Placing a lobby beside
someone's name **suggests influence without establishing it** — two facts set
side by side to imply a third that neither carries. That is harder to defend than
a score, because the judgment is nowhere written down and so nowhere sourced
(§2 rules 1 and 2). It is also the argument that decides the subject, and it does
not depend on any measurement.

**The one variant that was not ruled out.** On a *text* rather than a person —
« on this bill, N interest representatives declared an action » — attributes
nothing to anyone and would ride on the legislative-dossier key of #639. It stays
un-instructed, and two things would have to be established before it were worth
anything:

- **whether the register names people at all.** It is believed to record actions
  by *category* of decision-maker and by targeted decision, not by named
  official — **unverified against the register's own open data**, and that single
  fact decides whether a per-candidate view is even possible;
- that it is a **full collection project** — new source, new licence, new schema —
  outside epic #324 in any case.
