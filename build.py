#!/usr/bin/env python3
"""Generates the static site from data/*.yml + templates/ into the repo root.

Usage:
    python3 build.py

Edit a data/*.yml file or a templates/*.html file, rerun this script, and
preview the changed output before committing. Every page it writes is a
plain static HTML file -- GitHub Pages configuration never has to change.
"""
import pathlib
from datetime import date

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = pathlib.Path(__file__).parent
DATA_DIR = ROOT / "data"
TEMPLATES_DIR = ROOT / "templates"

# Timeline spacing: each node's vertical position is driven by its actual
# calendar distance from the previous node on one shared axis (PX_PER_DAY) --
# not a layout heuristic, and not compressed for long gaps either. Fixed
# month/year tick marks (see month_marks/year_marks below) are placed on that
# same axis regardless of whether an event happened nearby, so a quiet
# stretch still reads as real elapsed time passing rather than empty space.
# The one exception: events within CLUSTER_WITHIN_DAYS of each other are
# genuinely too close to place at their true distance without overlapping,
# so they're merged into a single expandable cluster node instead.
TIMELINE_PX_PER_DAY = 1.3
TIMELINE_CLUSTER_WITHIN_DAYS = 16
TIMELINE_MIN_GAP_PX = 10


def load_yaml(name):
    with open(DATA_DIR / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


def year_marks(oldest_date, newest_date):
    return [date(y, 1, 1) for y in range(newest_date.year, oldest_date.year - 1, -1)]


def month_marks(oldest_date, newest_date):
    """Every month boundary in range, excluding January (already a year mark)."""
    marks = []
    y, m = newest_date.year, newest_date.month
    while (y, m) >= (oldest_date.year, oldest_date.month):
        if m != 1:
            marks.append(date(y, m, 1))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return marks


def build_entry_view(e, root, include_venue):
    links = []
    if e.get("notes"):
        links.append({"icon": "fa-file-pdf-o", "label": "Notes", "href": root + e["notes"], "external": False})
    if e.get("code"):
        links.append({"icon": "fa-keyboard-o", "label": "Code", "href": e["code"], "external": True})
    if e.get("slides"):
        links.append({"icon": "fa-file-pdf-o", "label": "Slides", "href": root + e["slides"], "external": True})
    if e.get("video"):
        links.append({"icon": "fa-video-camera", "label": "Video", "href": e["video"], "external": True})
    abstract = e.get("abstract", "")
    return {
        "date_label": e["date"].strftime("%B %Y"),
        "title": e["title"],
        "venue": e.get("venue") if include_venue else None,
        "location": e.get("location", ""),
        "city": e.get("city", ""),
        "links": links,
        "abstract": abstract,
        "expandable": bool(links or abstract),
    }


def layout_timeline(entries, root, include_venue):
    """Lays out talks/travel entries on a single time axis, computed here at
    build time (no client-side JS) -- see the constants above for the model.

    Fixed tick marks are placed at every month boundary the data spans (a
    labeled one for January, an unlabeled minor one otherwise), on the same
    axis as the real events -- so the timeline reads as an actual calendar
    ruler, ticking past at a steady rate, rather than a list whose spacing
    happens to reflect elapsed time.

    Spacing is expressed as a margin-top *before* each row rather than an
    absolute pixel position, so the page stays in normal document flow: when
    a card or cluster expands, it pushes later rows down instead of
    overlapping them (an absolutely-positioned layout would need every card's
    collapsed height guessed correctly in advance, and would still overlap
    whatever comes after it the moment more than one nearby item is expanded
    at once).
    """
    if not entries:
        return {"rows": []}

    # 1. Group entries that are too close together in real time to place at
    # their true distance without overlapping.
    clusters = [[entries[0]]]
    for e in entries[1:]:
        if (clusters[-1][-1]["date"] - e["date"]).days <= TIMELINE_CLUSTER_WITHIN_DAYS:
            clusters[-1].append(e)
        else:
            clusters.append([e])

    # 2. Build the full set of anchors to place on the axis: each cluster
    # (represented by its most recent member's date for ordering), plus a
    # fixed tick for every month/year boundary the data spans -- so the
    # timeline reads like a real calendar ruler with regular ticks, not just
    # "however many events happened, spaced apart."
    oldest_date, newest_date = entries[-1]["date"], entries[0]["date"]
    anchors = [{"date": c[0]["date"], "kind": "cluster", "cluster": c} for c in clusters]
    anchors += [{"date": d, "kind": "yearmark"} for d in year_marks(oldest_date, newest_date)]
    anchors += [{"date": d, "kind": "monthmark"} for d in month_marks(oldest_date, newest_date)]
    anchors.sort(key=lambda a: a["date"], reverse=True)

    # 3. Walk the merged, time-sorted anchors and place each on the axis.
    rows = []
    prev_date = None
    for anchor in anchors:
        anchor_date = anchor["date"]
        margin_top = 0
        if prev_date is not None:
            gap_days = (prev_date - anchor_date).days
            margin_top = max(TIMELINE_MIN_GAP_PX, gap_days * TIMELINE_PX_PER_DAY)

        if anchor["kind"] == "yearmark":
            rows.append({"kind": "yearmark", "margin_top": round(margin_top), "year": anchor_date.year})
            prev_date = anchor_date
            continue
        if anchor["kind"] == "monthmark":
            rows.append({"kind": "monthmark", "margin_top": round(margin_top)})
            prev_date = anchor_date
            continue

        cluster = anchor["cluster"]
        common = {"margin_top": round(margin_top)}
        oldest_member_date = cluster[-1]["date"]
        if len(cluster) == 1:
            rows.append({"kind": "event", **common, **build_entry_view(cluster[0], root, include_venue)})
        else:
            first, last = oldest_member_date, anchor_date  # chronological order
            if first.year == last.year and first.month == last.month:
                span_label = first.strftime("%B %Y")
            elif first.year == last.year:
                span_label = first.strftime("%B") + "–" + last.strftime("%B %Y")
            else:
                span_label = first.strftime("%B %Y") + "–" + last.strftime("%B %Y")
            rows.append({
                "kind": "cluster",
                **common,
                "count": len(cluster),
                "span_label": span_label,
                "members": [build_entry_view(e, root, include_venue) for e in cluster],
            })
        prev_date = oldest_member_date

    return {"rows": rows}


def group_talks_for_condensed(talks):
    """Splits talks into the sections/groups the condensed (list) view renders:
    conference talks, flat seminar talks, seminar talks grouped by a recurring
    institution (e.g. "Iowa State University"), and everything else.
    """
    conference = [t for t in talks if t["category"] == "conference"]
    other = [t for t in talks if t["category"] == "other"]
    seminar = [t for t in talks if t["category"] == "seminar"]

    seminar_flat = [t for t in seminar if not t.get("institution")]

    groups_by_name = {}
    for t in seminar:
        inst = t.get("institution")
        if inst:
            groups_by_name.setdefault(inst, []).append(t)
    seminar_groups = [
        {"institution": name, "talks": sorted(items, key=lambda t: t["date"], reverse=True)}
        for name, items in groups_by_name.items()
    ]
    seminar_groups.sort(key=lambda g: g["talks"][0]["date"], reverse=True)

    return {
        "conference": conference,
        "seminar_flat": seminar_flat,
        "seminar_groups": seminar_groups,
        "other": other,
    }


def build():
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(enabled_extensions=(), default=False),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    site = load_yaml("site.yml")
    home = load_yaml("home.yml")
    papers = load_yaml("papers.yml")
    teaching = load_yaml("teaching.yml")
    service = load_yaml("service.yml")
    outreach = load_yaml("outreach.yml")
    past_projects = load_yaml("past_projects.yml")
    talks = load_yaml("talks.yml")
    travel = load_yaml("travel.yml")
    research_slugs = sorted(p.stem for p in (TEMPLATES_DIR / "pages" / "research").glob("*.html"))

    talks_timeline = layout_timeline(talks, "../", include_venue=True)
    travel_timeline = layout_timeline(travel, "../", include_venue=False)

    pages = [
        ("pages/index.html", "index.html", {"site": site, "home": home, "root": ""}),
        ("pages/papers.html", "papers/index.html", {"site": site, "papers": papers, "root": "../"}),
        ("pages/talks_timeline.html", "talks/index.html", {"site": site, "timeline": talks_timeline, "root": "../"}),
        ("pages/talks_condensed.html", "talks/condensed.html", {"site": site, "talks": group_talks_for_condensed(talks), "root": "../"}),
        ("pages/travel_timeline.html", "travel/index.html", {"site": site, "timeline": travel_timeline, "root": "../"}),
        ("pages/travel_condensed.html", "travel/condensed.html", {"site": site, "travel": travel, "root": "../"}),
        ("pages/teaching.html", "teaching/index.html", {"site": site, "teaching": teaching, "root": "../"}),
        ("pages/service.html", "service/index.html", {"site": site, "service": service, "root": "../"}),
        ("pages/outreach.html", "outreach/index.html", {"site": site, "outreach": outreach, "root": "../"}),
        ("pages/past_projects.html", "past-projects/index.html", {"site": site, "projects": past_projects, "root": "../"}),
    ]

    for slug in research_slugs:
        pages.append((f"pages/research/{slug}.html", f"{slug}/index.html", {"site": site, "root": "../"}))

    for template_name, out_path, context in pages:
        template = env.get_template(template_name)
        rendered = template.render(**context)
        out_file = ROOT / out_path
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(rendered, encoding="utf-8")
        print(f"wrote {out_path}")


if __name__ == "__main__":
    build()
