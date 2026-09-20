# Sycomore, Journal officiel, Wikidata — les sources CITÉES des mandats antérieurs

> **Status: cited, not collected (#860).** No job queries these sites. They are the
> primary sources behind `raw_data/mandats_anterieurs.json`, a table reviewed by hand:
> the mandates a declared candidate held **before 19/06/2002**, the first day of the
> Assembly's open data. External reference: it drifts with its providers, not with
> our code. Siblings: `an-opendata.md` (live, collected), `nosdeputes/` (historical).

Written on 11/09/2026, while reviewing the table's 11 lines. Everything below was
**observed**, not assumed.

## Sycomore — députés since 1789 (Assemblée nationale)

- **URL**: `https://www2.assemblee-nationale.fr/sycomore/fiche?num_dept=<id>`.
  Plain HTML, reachable by `curl` (HTTP 200, ~40 KB).
- **What a page gives**: one block per mandate — `Législature` / `Mandat`
  (« Du 1 juin 1997 au 18 juin 2002 ») / `Département` / `Groupe`. Read by stripping
  tags and walking the labels; each block's value is the next line.
- **The id** is Wikidata **`P1045`**. It is not the AMO30 actor id.
- **Dates are the Assembly's**: they can differ from Wikipedia and Wikidata by days
  (Royal 13/06/1988 against 23/06 ; Dupont-Aignan 01/06/1997 against 12/06). The
  table keeps Sycomore's.
- **Ministerial functions are not on Sycomore** — Royal's page lists only her
  mandates as a deputy.

## Journal officiel, through Légifrance — government composition decrees

- **URL**: `https://www.legifrance.gouv.fr/jorf/id/JORFTEXT<12 digits>`.
- **`curl` is refused** — HTTP 403, a Cloudflare « Just a moment... » challenge,
  browser headers included. A **web fetch** (Claude's `WebFetch`) reads the page:
  that is how the decrees were read, and it is an **indirect** reading — the page is
  summarised by a model, not parsed.
- **Some old decrees render only their title**: the composition decree of
  02/04/1992 (`JORFTEXT000000703414`). A function it creates can be attested
  elsewhere — Royal signs decree n° 92-396 of 16/04/1992 as « Le ministre de
  l'environnement ».
- **An end date is a separate decree**: a change of portfolio is the next
  composition decree ; the end of a whole government is a « cessation des
  fonctions du Gouvernement » decree (06/05/2002, `JORFTEXT000000412382`). The one
  ending the Bérégovoy government in 1993 was **not found** — the table publishes
  that end `null` with its motive.
- **Search**: Légifrance search is not reachable by script ; a web search restricted
  to `legifrance.gouv.fr` finds most decrees by title and date.

## Wikidata — to DISCOVER, never to publish

- **`P4123`** (Assembly actor id) is stored **without the `PA` prefix**:
  `"2650"`, not `"PA2650"`. A query with the prefix returns nothing — the first
  measurement for #860 came back empty for that reason alone.
- **`P39`** (position held, with `P580`/`P582` qualifiers) lists deputy and senator
  mandates reliably, **but missed all four of Royal's ministerial functions** — an
  absence in Wikidata is not an absence of fact.
- **`P1045`** gives the Sycomore id, **`P1808`** the Senate id.
- Query service: `https://query.wikidata.org/sparql`, with a `User-Agent` header.

## The Senate

`www.senat.fr` answers, and Jean-Luc Mélenchon's two pre-2002 senator mandates are
there. They are **not carried**: #528 took the Senate out of scope, biographical use
included. Reopening it means adding `senat` to `KNOWN_INSTITUTIONS_ANTERIEURES`.
