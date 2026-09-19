#!/usr/bin/env python3
"""Phase 0 identity collision census (RFC: docs/multi-world-architecture-v0.1.md §14 Phase 0).

Pipeline (repeat for every future World / protocol bump):

    SQL query contract (this script, --print-sql)
        -> export production corpus (read-only SELECT, never committed)
        -> census script (this file)
        -> report (docs/phase0-identity-census-*.md)

Usage:
    ./scripts/phase0-identity-census.py --print-sql      # emit the query contract
    ./scripts/phase0-identity-census.py                  # run against exports/phase0/
    ./scripts/phase0-identity-census.py --data DIR --contributions DIR

Standard library only. Never writes to PostgreSQL (AGENTS.md invariant);
the export step is a human-run, read-only SELECT.
"""

import argparse
import csv
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

RESERVED = {
    'timeline', 'graph', 'search', 'evidence', 'entities', 'capabilities', 'about',
}

# ---------------------------------------------------------------------------
# Query contract: exact read-only statements used for the 2026-09-19 census.
# TSV exports are headerless, field separator '|', tuples-only (psql -A -t -F '|').
# robots must be CSV (names contain embedded newlines).
# ---------------------------------------------------------------------------

SQL_CONTRACT = r"""
-- Export target dir: exports/phase0/  (gitignored — production data never committed)
-- Wrapper (adjust host alias):  ssh <prod> "docker exec -i emibot-pg psql -U emibot_app -d postgres -A -t -F '|'"

-- robots.csv  (CSV with header; embedded newlines in names)
--   \copy (SELECT id, url_slug, name, company, coalesce(form_category,''),
--          coalesce(data_quality_gate,'') FROM robots ORDER BY id)
--   TO 'exports/phase0/robots.csv' WITH (FORMAT csv, HEADER true)

SELECT canonical_name, entity_type, coalesce(headquarters,'') FROM company_profiles ORDER BY 1;
-- -> exports/phase0/company_profiles.tsv

SELECT entity_type, canonical_name, alias, coalesce(status,''), coalesce(proposal_kind,'')
  FROM entity_aliases ORDER BY 1,2,3;
-- -> exports/phase0/entity_aliases.tsv

SELECT canonical_name, coalesce(model_name,''), coalesce(variant,''), coalesce(mpn,''),
       coalesce(normalized_mpn,''), coalesce(manufacturer,''), coalesce(category,''),
       coalesce(subtype,''), coalesce(status,'') FROM parts ORDER BY id;
-- -> exports/phase0/parts.tsv

SELECT canonical_name, manufacturer, coalesce(status,'') FROM part_series ORDER BY id;
-- -> exports/phase0/part_series.tsv

SELECT event_key, coalesce(event_class,''), title, coalesce(event_type,''),
       coalesce(event_date::text,''), coalesce(status,'') FROM industry_events ORDER BY id;
-- -> exports/phase0/industry_events.tsv
"""

SQL_ROBOTS_COPY = (
    "\\copy (SELECT id, url_slug, name, company, coalesce(form_category,''), "
    "coalesce(data_quality_gate,'') FROM robots ORDER BY id) "
    "TO 'exports/phase0/robots.csv' WITH (FORMAT csv, HEADER true)"
)

# ---------------------------------------------------------------------------
# Normalization (ratify these rules in the v0.4 identity spec)
# ---------------------------------------------------------------------------

def norm(s):
    """Comparison normalization: NFC, casefold, whitespace collapse."""
    if s is None:
        return ''
    s = unicodedata.normalize('NFC', str(s))
    return re.sub(r'\s+', ' ', s).strip().casefold()


def slug(s):
    """Candidate canonical key slug: punctuation to space, `_`/space to `-`, keep CJK."""
    s = norm(s)
    s = re.sub(r"[&/+,．。·（）()\[\]【】'\".:;!?！？、，。：]", ' ', s)
    s = re.sub(r'[\s_]+', '-', s)
    return re.sub(r'-{2,}', '-', s).strip('-')


def has_ascii(s):
    return bool(re.search(r'[A-Za-z0-9]', s or ''))


def unsafe_chars(s):
    return sorted({c for c in (s or '') if c in ':' or ord(c) < 32 or c in '/?#%\\'})

# ---------------------------------------------------------------------------

def load_tsv(path, fields):
    with open(path) as fh:
        return [dict(zip(fields, row)) for row in csv.reader(fh, delimiter='|') if row]


def load_corpus(data_dir, contrib_dir):
    data_dir = Path(data_dir)
    corpus = {
        'robots': list(csv.DictReader(open(data_dir / 'robots.csv'))),
        'companies': load_tsv(data_dir / 'company_profiles.tsv',
                              ['canonical_name', 'entity_type', 'headquarters']),
        'aliases': load_tsv(data_dir / 'entity_aliases.tsv',
                            ['entity_type', 'canonical_name', 'alias', 'status', 'proposal_kind']),
        'parts': load_tsv(data_dir / 'parts.tsv',
                          ['canonical_name', 'model_name', 'variant', 'mpn', 'normalized_mpn',
                           'manufacturer', 'category', 'subtype', 'status']),
        'series': load_tsv(data_dir / 'part_series.tsv',
                           ['canonical_name', 'manufacturer', 'status']),
        'events': load_tsv(data_dir / 'industry_events.tsv',
                           ['event_key', 'event_class', 'title', 'event_type', 'event_date', 'status']),
    }
    contrib = []
    if Path(contrib_dir).is_dir():
        for f in sorted(Path(contrib_dir, 'robotics').glob('*/contribution.json')):
            d = json.loads(f.read_text())
            contrib.append((f.parent.name, d))
    corpus['contributions'] = contrib
    return corpus


def run_census(corpus):
    out = []
    counts = {}
    say = out.append

    robots = corpus['robots']
    slug_rows = [r for r in robots if (r.get('url_slug') or '').strip()]
    noslug = [r for r in robots if not (r.get('url_slug') or '').strip()]
    counts['robots_total'] = len(robots)
    counts['robots_with_slug'] = len(slug_rows)
    counts['robots_without_slug'] = len(noslug)

    # --- reserved route slugs ---
    reserved_hits = sorted({r['url_slug'].strip() for r in slug_rows
                            if norm(r['url_slug']) in RESERVED})
    say(('SECTION', 'Reserved route collisions (/robot/<slug> vs RFC §8.2)',
         [f'`{s}`' for s in reserved_hits]))

    # --- slug normalization collisions + format ---
    by_norm_slug = defaultdict(list)
    for r in slug_rows:
        by_norm_slug[slug(r['url_slug'])].append(r)
    dup = {k: v for k, v in by_norm_slug.items() if len(v) > 1}
    say(('SECTION', 'Robot slug normalization collisions',
         [f"key=`{k}` ← " + ' / '.join(r['url_slug'] for r in v) for k, v in dup.items()]))
    fmt_bad = [r for r in slug_rows
               if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', r['url_slug'])]
    say(('SECTION', f'Robot slug format violations ({len(fmt_bad)})',
         [f"`{r['url_slug']}`" for r in fmt_bad]))

    # --- name-slug identity swap hazard ---
    slug_by_name = defaultdict(list)
    for r in slug_rows:
        s = slug(r['name'])
        if s:
            slug_by_name[s].append(r)
    swaps = []
    for s, rows in slug_by_name.items():
        if s in by_norm_slug:
            holders = by_norm_slug[s]
            if any(h['id'] not in {x['id'] for x in rows} for h in holders):
                holder_txt = ' / '.join(
                    f"{h['url_slug']} ({h.get('name', '')[:20]})" for h in holders)
                swaps.append(f"name-slug `{s}` ({' / '.join(r['name'][:20] for r in rows)})"
                             f" → held by {holder_txt}")
    say(('SECTION', 'Name slug → foreign slug collisions (identity-swap hazard)', swaps))

    # --- missing slugs ---
    say(('SECTION', f'Robots without slug ({len(noslug)})',
         [f"id={r['id']} name={r['name']!r} company={r['company']!r}" for r in noslug]))

    # --- companies ---
    comp_names = [r['canonical_name'] for r in corpus['companies']
                  if (r.get('canonical_name') or '').strip()]
    comp_by_slug = defaultdict(list)
    for n in comp_names:
        comp_by_slug[slug(n)].append(n)
    say(('SECTION', 'Company slug collisions',
         [f"key=`{k}` ← " + ' / '.join(v) for k, v in comp_by_slug.items() if len(v) > 1]))
    cjk_only = [n for n in comp_names if not has_ascii(n)]
    counts['companies'] = len(comp_names)
    counts['companies_cjk_only'] = len(cjk_only)
    say(('SECTION', f'Companies with no ASCII form ({len(cjk_only)}/{len(comp_names)})',
         cjk_only, 60))
    say(('SECTION', 'Company names with key-unsafe characters',
         [f"{n!r} chars={''.join(unsafe_chars(n))}" for n in comp_names if unsafe_chars(n)]))

    # --- aliases ---
    alias_conflict = defaultdict(set)
    for r in corpus['aliases']:
        t, cn, a = (r.get('entity_type', '').strip(), r.get('canonical_name', '').strip(),
                    r.get('alias', '').strip())
        if a:
            alias_conflict[(t, norm(a))].add(cn)
    say(('SECTION', 'Alias conflicts (same entity_type+alias → multiple canonical_name)',
         [f"{t} `{a}` → " + ' / '.join(sorted(v))
          for (t, a), v in alias_conflict.items() if len(v) > 1]))
    say(('SECTION', 'Alias entity_type distribution',
         [f'{t}: {c}' for t, c in Counter(r.get('entity_type', '').strip()
                                          for r in corpus['aliases']).most_common()]))

    # --- parts / series ---
    part_by_slug = defaultdict(list)
    mpn_dup = defaultdict(list)
    for r in corpus['parts']:
        key = slug(f"{r['canonical_name']} {r['model_name']} {r['variant']}".strip())
        part_by_slug[key].append(f"{r['canonical_name']}|{r['model_name']}|{r['variant']}")
        if r.get('normalized_mpn'):
            mpn_dup[r['normalized_mpn']].append(r['canonical_name'])
    say(('SECTION', 'Part slug collisions',
         [f"key=`{k}` ← " + ' / '.join(v) for k, v in part_by_slug.items() if len(v) > 1]))
    say(('SECTION', 'Duplicate normalized_mpn',
         [f"{m}: " + ' / '.join(v) for m, v in mpn_dup.items() if len(v) > 1]))
    ser_by_slug = defaultdict(list)
    for r in corpus['series']:
        ser_by_slug[slug(r['canonical_name'])].append(r['canonical_name'])
    say(('SECTION', 'Part series slug ∩ part slug',
         [f'`{k}`' for k in sorted(set(ser_by_slug) & set(part_by_slug))]))

    # --- events ---
    def key_class(k):
        m = re.match(r'^([a-z-]+)-', k or '')
        return m.group(1) if m else (k or '')[:12]
    say(('SECTION', 'Event key shape distribution',
         [f'{c}: {n}' for c, n in Counter(key_class(r['event_key'])
                                          for r in corpus['events']).most_common(15)]))
    say(('SECTION', 'Event key charset violations',
         [f"`{r['event_key']}`" for r in corpus['events']
          if not re.fullmatch(r'[a-z0-9][a-z0-9._-]*', r['event_key'])]))
    ev_title = defaultdict(list)
    for r in corpus['events']:
        ev_title[slug(re.sub(r'[（(].*?[)）]', '', r['title']))[:40]].append(r['event_key'])
    say(('SECTION', 'Event title-slug collisions (v0.4 key minting needs disambiguation)',
         [f"`{k}` ← {', '.join(v)}" for k, v in ev_title.items() if len(v) > 1], 30))
    counts['events'] = len(corpus['events'])
    counts['events_distinct_key'] = len({r['event_key'] for r in corpus['events']})

    # --- cross-type same slug (informational) ---
    all_sets = {'robot': set(by_norm_slug), 'company': set(comp_by_slug),
                'part': set(part_by_slug), 'series': set(ser_by_slug)}
    cross = []
    for a, b in (('robot', 'company'), ('robot', 'part'), ('company', 'part'),
                 ('part', 'series'), ('company', 'series')):
        for s in sorted(all_sets[a] & all_sets[b]):
            cross.append(f'{a} ∩ {b}: `{s}`')
    say(('SECTION', 'Cross-type same slug (type-namespaced, informational)', cross))

    # --- IWM runtime corpus ---
    iwm_ent, iwm_ev = [], []
    for folder, d in corpus['contributions']:
        for e in d.get('entities', []):
            iwm_ent.append((d.get('pack'), folder, e.get('entity_type'),
                            e.get('entity_key'), e.get('name', '')))
        for e in d.get('events', []):
            iwm_ev.append((d.get('pack'), folder, e.get('event_key'), e.get('title', '')[:40]))
    counts['iwm_contributions'] = len(corpus['contributions'])
    counts['iwm_entities'] = len(iwm_ent)
    counts['iwm_events'] = len(iwm_ev)
    say(('SECTION', 'IWM v0.3 runtime corpus (contributions)',
         [f'{p}/{f}: {et} `{ek}` ({nm})' for p, f, et, ek, nm in iwm_ent] +
         [f'{p}/{f}: event `{ek}` ({ti})' for p, f, ek, ti in iwm_ev]))
    clash = []
    iwm_slugs = {(et, slug(ek)) for _, _, et, ek, _ in iwm_ent}
    for et, s in iwm_slugs:
        if et == 'robot' and s in set(by_norm_slug):
            clash.append(f'robot `{s}` collides with production robot slug')
        if et == 'company' and s in set(comp_by_slug):
            clash.append(f'company `{s}` collides with production company slug')
    say(('SECTION', 'IWM corpus ↔ production key collisions', clash))

    return out, counts


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--data', default='exports/phase0', help='export dir (see --print-sql)')
    ap.add_argument('--contributions', default='contributions', help='IWM contributions dir')
    ap.add_argument('--print-sql', action='store_true', help='emit the read-only query contract')
    args = ap.parse_args()

    if args.print_sql:
        print(SQL_CONTRACT)
        print('-- robots export (client-side CSV):')
        print('--  ' + SQL_ROBOTS_COPY)
        return 0

    out, counts = run_census(load_corpus(args.data, args.contributions))
    print('=' * 72)
    print('PHASE 0 IDENTITY CENSUS — counts')
    for k, v in counts.items():
        print(f'  {k}: {v}')
    print('=' * 72)
    for item in out:
        kind = item[0]
        if kind == 'SECTION':
            _, title, rows = item[:3]
            limit = item[3] if len(item) > 3 else 25
            print(f'\n## {title}')
            if not rows:
                print('（无）')
            else:
                for r in rows[:limit]:
                    print(f'- {r}')
                if len(rows) > limit:
                    print(f'- …共 {len(rows)} 条，其余略')
    return 0


if __name__ == '__main__':
    sys.exit(main())
