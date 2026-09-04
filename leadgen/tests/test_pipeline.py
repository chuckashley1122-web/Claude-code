"""End-to-end checks that need no network and no API keys."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import yaml  # noqa: E402

from leadgen import export, score as scoring  # noqa: E402
from leadgen.models import Lead, normalize_domain  # noqa: E402
from leadgen.sources.apollo import ApolloSource, _buckets_for  # noqa: E402
from leadgen.sources.sales_navigator_csv import SalesNavigatorCSVSource  # noqa: E402

SAMPLE = Path(__file__).parent / "sample_sales_navigator_export.csv"


def load(brand):
    return yaml.safe_load((ROOT / "config" / f"{brand}.yaml").read_text())


def test_domain_normalisation():
    for raw in ("https://www.Foo.com/bar?x=1", "http://foo.com", "FOO.com", "www.foo.com"):
        assert normalize_domain(raw) == "foo.com", raw


def test_csv_parses_varied_headers():
    leads = SalesNavigatorCSVSource(SAMPLE).search({})
    assert len(leads) == 5
    dana = leads[0]
    assert dana.full_name == "Dana Whitfield"
    assert dana.title == "Owner"
    assert dana.company_domain == "northgateroofing.example"
    assert dana.email == "dana@northgateroofing.example"
    # "51-200 employees" must land on the low end of the range, not 51200.
    assert leads[1].employee_count == 51
    assert leads[2].employee_count == 80


def test_dedupe_keeps_richer_record():
    leads = SalesNavigatorCSVSource(SAMPLE).search({})
    deduped = scoring.dedupe(leads)
    assert len(deduped) == 4, "the two Dana Whitfield rows should collapse"
    dana = [x for x in deduped if x.last_name == "Whitfield"][0]
    assert dana.phone == "614-555-0142", "the row with a phone number should win"


def test_scoring_ranks_icp_fit_above_noise():
    config = load("ca-jenterprises")
    leads = scoring.dedupe(SalesNavigatorCSVSource(SAMPLE).search({}))
    for lead in leads:
        scoring.score_lead(lead, config)

    by_name = {x.full_name: x for x in leads}
    # Excluded title -> no title points; tiny agency -> nothing to sell to.
    assert by_name["Tom Beckett"].score < by_name["Dana Whitfield"].score
    assert by_name["Marcus Ellery"].score > 0
    assert all(x.tier in {"hot", "warm", "cold"} for x in leads)


def test_signal_weights_apply_from_config():
    config = load("ca-jconsulting")
    lead = Lead(title="Owner", industry="Construction", employee_count=40,
                email="a@b.com", signals={"nmls_licensed": True, "multi_location": True})
    scoring.score_lead(lead, config)
    # 20 title + 10 headcount + 10 industry + 8 reachable + 20 nmls + 14 multi_loc
    assert lead.score == 82
    assert lead.tier == "hot"
    assert any("nmls_licensed" in line for line in scoring.explain(lead, config))


def test_negative_signal_demotes_competitor():
    config = load("ca-jenterprises")
    lead = Lead(title="CEO", industry="Professional Services", employee_count=20,
                email="a@b.com", signals={"is_marketing_agency": True})
    scoring.score_lead(lead, config)
    assert lead.tier == "cold", "an agency is a competitor, not a prospect"


def test_apollo_headcount_buckets():
    assert _buckets_for(5, 200) == ["1,10", "11,20", "21,50", "51,100", "101,200"]
    assert _buckets_for(1, 1) == ["1,10"]


def test_sources_report_missing_keys_without_raising():
    ok, why = ApolloSource(api_key="").available()
    assert ok is False and "APOLLO_API_KEY" in why


def test_export_round_trip(tmp_path):
    config = load("ca-jenterprises")
    leads = scoring.dedupe(SalesNavigatorCSVSource(SAMPLE).search({}))
    for lead in leads:
        scoring.score_lead(lead, config)
    csv_path = export.to_csv(leads, tmp_path / "out.csv")
    body = csv_path.read_text()
    assert "full_name" in body and "Dana Whitfield" in body
    export.to_json(leads, tmp_path / "out.json")
    assert "leads" in export.summary(leads)
