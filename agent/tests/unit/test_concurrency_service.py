"""Company counter keys are scoped per country by kidoapp."""

from services.concurrency_service import CompanyConcurrencyService


def test_split_country_scoped_key():
    assert CompanyConcurrencyService._split_country(
        "br:7f69fe54-b6ba-433d-b419-89f0a7793fa3"
    ) == ("br", "7f69fe54-b6ba-433d-b419-89f0a7793fa3")


def test_split_legacy_key_has_no_country():
    assert CompanyConcurrencyService._split_country(
        "7f69fe54-b6ba-433d-b419-89f0a7793fa3"
    ) == (None, "7f69fe54-b6ba-433d-b419-89f0a7793fa3")
