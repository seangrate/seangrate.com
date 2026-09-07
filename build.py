#!/usr/bin/env python3
"""Generates the static site from data/*.yml + templates/ into the repo root.

Usage:
    python3 build.py

Edit a data/*.yml file or a templates/*.html file, rerun this script, and
preview the changed output before committing. Every page it writes is a
plain static HTML file -- GitHub Pages configuration never has to change.
"""
import datetime
import json
import pathlib
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = pathlib.Path(__file__).parent
DATA_DIR = ROOT / "data"
TEMPLATES_DIR = ROOT / "templates"


def load_yaml(name):
    with open(DATA_DIR / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


def json_default(obj):
    if isinstance(obj, datetime.date):
        return obj.isoformat()
    raise TypeError(f"not JSON serializable: {obj!r}")


def to_timeline_events(entries, root, include_venue):
    """Builds the JSON payload consumed by the client-side timeline renderer.

    Dates are passed as explicit {year, month, day} rather than an ISO string
    so the browser builds a local-time Date(year, month-1, day) -- parsing an
    ISO "YYYY-MM-DD" string instead would have JS treat it as UTC midnight,
    which silently rolls back to the previous day/month in US timezones.
    """
    events = []
    for e in entries:
        d = e["date"]
        event = {
            "title": e["title"],
            "year": d.year,
            "month": d.month,
            "day": d.day,
            "location": e.get("location", ""),
            "city": e.get("city", ""),
            "extras": {
                "notes": (root + e["notes"]) if e.get("notes") else "",
                "code": e.get("code", ""),
                "slides": (root + e["slides"]) if e.get("slides") else "",
                "video": e.get("video", ""),
                "abstract": e.get("abstract", ""),
            },
        }
        if include_venue:
            event["venue"] = e.get("venue", "")
        events.append(event)
    return events


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
    env.filters["tojson"] = lambda value: json.dumps(value, default=json_default)

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

    talks_events = to_timeline_events(talks, "../", include_venue=True)
    travel_events = to_timeline_events(travel, "../", include_venue=False)

    pages = [
        ("pages/index.html", "index.html", {"site": site, "home": home, "root": ""}),
        ("pages/papers.html", "papers/index.html", {"site": site, "papers": papers, "root": "../"}),
        ("pages/talks_timeline.html", "talks/index.html", {"site": site, "events": talks_events, "root": "../"}),
        ("pages/talks_condensed.html", "talks/condensed.html", {"site": site, "talks": group_talks_for_condensed(talks), "root": "../"}),
        ("pages/travel_timeline.html", "travel/index.html", {"site": site, "events": travel_events, "root": "../"}),
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
