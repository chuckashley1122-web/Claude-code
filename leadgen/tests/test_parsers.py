"""Parser tests against recorded API response shapes.

These two parsers are the ones a paying user depends on, and neither can be
exercised without a key — so the response shapes are pinned as fixtures here.
The edge cases are the real ones: Apollo masks locked emails, nulls out
`organization` for people with no current employer, and returns
`primary_phone: null` rather than omitting the key.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from leadgen.sources.apollo import ApolloSource  # noqa: E402
from leadgen.sources.brightdata import BrightDataSource  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


def load(name):
    return json.loads((FIXTURES / name).read_text())


# --- Apollo ---------------------------------------------------------------

def apollo_leads():
    return [ApolloSource._to_lead(p) for p in load("apollo_people_search.json")["people"]]


def test_apollo_maps_a_full_record():
    dana = apollo_leads()[0]
    assert dana.full_name == "Dana Whitfield"
    assert dana.title == "Owner"
    assert dana.company == "Northgate Roofing"
    assert dana.company_domain == "northgateroofing.example"
    assert dana.employee_count == 24
    assert dana.email == "dana@northgateroofing.example"
    assert dana.location == "Columbus, Ohio, United States"
    assert dana.linkedin_url.endswith("/danawhitfield")
    assert dana.source == "apollo"
    assert dana.source_ref == "5f1a2b3c4d5e6f0001"


def test_apollo_drops_masked_email_placeholder():
    """`email_not_unlocked@domain.com` is a mask, not a deliverable address."""
    marcus = apollo_leads()[1]
    assert marcus.email == "", "the locked-email placeholder must not survive"


def test_apollo_survives_null_organization_and_null_phone():
    """Apollo sends explicit nulls, so `.get(k, {})` is not enough."""
    leads = apollo_leads()
    assert leads[1].phone == "", "primary_phone: null must not raise"
    priya = leads[2]
    assert priya.full_name == "Priya Raghavan"
    assert priya.company == "" and priya.company_domain == ""
    assert priya.employee_count is None


def test_apollo_reads_org_phone_when_person_has_none():
    dana = apollo_leads()[0]
    assert dana.phone == "+16145550142"


# --- Bright Data ----------------------------------------------------------

def brightdata_leads():
    return [BrightDataSource._to_lead(r) for r in load("brightdata_profiles.json")]


def test_brightdata_maps_nested_company():
    dana = brightdata_leads()[0]
    assert dana.full_name == "Dana Whitfield"
    assert dana.company == "Northgate Roofing"
    assert dana.company_domain == "northgateroofing.example"
    assert dana.linkedin_url.endswith("/danawhitfield")
    assert dana.source_ref == "danawhitfield"


def test_brightdata_falls_back_across_field_spellings():
    """Field names differ between Bright Data's LinkedIn datasets."""
    priya = brightdata_leads()[1]
    assert priya.full_name == "Priya Raghavan"      # full_name, not name
    assert priya.title == "Founder"                 # title, not position
    assert priya.company == "Raghavan Freight"      # flat, not nested
    assert priya.location == "Newark, NJ"
    assert priya.source_ref == "priyaraghavan"      # linkedin_id, not id


def test_brightdata_handles_null_company_and_single_word_name():
    leads = brightdata_leads()
    assert leads[1].company_domain == "", "current_company: null must not raise"
    cher = leads[2]
    assert cher.first_name == "Cher" and cher.last_name == ""


def test_both_parsers_always_set_provenance():
    for lead in apollo_leads() + brightdata_leads():
        assert lead.source in {"apollo", "brightdata"}
