#!/usr/bin/env python3
"""Phase 0 route collision census — reserved World paths under /robot/* (RFC §8.2).

Checks two directions of collision before World-scoped routes ship:

1. production robot slugs that would be shadowed by reserved World paths
   (/robot/timeline, /robot/graph, /robot/search, ...);
2. existing static application routes under /robot/* that a World path
   would collide with (pass them via --routes-file, one path per line).

Pipeline mirrors scripts/phase0-identity-census.py:

    SQL query contract (--print-sql)
        -> export robots.csv (read-only, never committed)
        -> this script
        -> report

Usage:
    ./scripts/phase0-route-collision-census.py --print-sql
    ./scripts/phase0-route-collision-census.py --data exports/phase0/robots.csv
    ./scripts/phase0-route-collision-census.py --routes-file robot-static-routes.txt
"""

import argparse
import csv
import re
import sys
import unicodedata
from pathlib import Path

DEFAULT_RESERVED = 'timeline,graph,search,evidence,entities,capabilities,about'

SQL_CONTRACT = r"""
-- Read-only query contract (adjust host alias):
--   ssh <prod> "docker exec -i emibot-pg psql -U emibot_app -d postgres -q -c '\copy ...'"
--
-- \copy (SELECT id, url_slug, name FROM robots ORDER BY id)
--   TO 'exports/phase0/robots-routes.csv' WITH (FORMAT csv, HEADER true)
--
-- Static app routes: list existing paths under /robot/* one per line
-- (e.g. from the frontend route tree), pass via --routes-file.
"""


def norm(s):
    s = unicodedata.normalize('NFC', str(s or ''))
    return re.sub(r'\s+', ' ', s).strip().casefold()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--data', default='exports/phase0/robots.csv',
                    help='robots export CSV (id,url_slug,name)')
    ap.add_argument('--reserved', default=DEFAULT_RESERVED,
                    help='comma-separated reserved World path segments (RFC §8.2)')
    ap.add_argument('--routes-file', default=None,
                    help='optional file of existing static /robot/* paths, one per line')
    ap.add_argument('--print-sql', action='store_true')
    args = ap.parse_args()

    if args.print_sql:
        print(SQL_CONTRACT)
        return 0

    reserved = {norm(w) for w in args.reserved.split(',') if w.strip()}
    static_routes = []
    if args.routes_file:
        static_routes = [l.strip() for l in open(args.routes_file)
                         if l.strip() and not l.startswith('#')]

    rows = list(csv.DictReader(open(args.data)))
    slugs = [(r.get('url_slug') or '').strip() for r in rows]
    slugs = [s for s in slugs if s]
    problems = 0

    print(f'robots: {len(rows)} rows, {len(slugs)} with slug, '
          f'{len(rows) - len(slugs)} without')
    print(f'reserved segments: {sorted(reserved)}')

    hits = sorted({s for s in slugs if norm(s) in reserved})
    if hits:
        problems += len(hits)
        print(f'\nFAIL — robot slugs colliding with reserved World paths ({len(hits)}):')
        for s in hits:
            print(f'  /robot/{s}')
    else:
        print('\nPASS — no robot slug collides with reserved World paths')

    dupes = {s for s in slugs if slugs.count(s) > 1}
    if dupes:
        problems += len(dupes)
        print(f'\nFAIL — duplicate robot slugs ({len(dupes)}): '
              + ', '.join(sorted(dupes)))
    else:
        print('PASS — robot slugs unique')

    bad_fmt = sorted({s for s in slugs if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', s)})
    if bad_fmt:
        problems += len(bad_fmt)
        print(f'\nWARN — slugs outside ^[a-z0-9-]+$ ({len(bad_fmt)}): ' + ', '.join(bad_fmt[:20]))
    else:
        print('PASS — slug format')

    route_conf = []
    for route in static_routes:
        segs = [s for s in route.strip('/').split('/') if s]
        if len(segs) >= 2 and segs[0] == 'robot' and norm(segs[1]) in reserved:
            route_conf.append(route)
    if route_conf:
        problems += len(route_conf)
        print(f'\nFAIL — static app routes shadowed by reserved World paths:')
        for r in route_conf:
            print(f'  {r}')
    elif static_routes:
        print('PASS — no static /robot/* route collides with reserved World paths')

    print(f'\nverdict: {"FAIL" if problems else "PASS"} ({problems} problem(s))')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
