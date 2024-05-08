import os

import pytest

from backend.main import Wallet


# unit-tests


@pytest.fixture
def wallet():
    path = "wallet.csv"
    if os.path.exists(path):
        os.remove("wallet.csv")
    return Wallet("wallet.csv")


def test_init(wallet):
    assert wallet.balance == 0


def test_add_entry(wallet):
    wallet.add_entry("Доход", "2022-01-01", 100, "Test income")
    assert wallet.balance == 100


def test_add_entry_invalid_category(wallet):
    wallet.add_entry("Invalid category", "2022-01-01", 100, "Test income")
    assert wallet.balance == 0  # invalid category


def test_invalid_edit_entry(wallet):
    wallet.add_entry("Доход", "2022-01-01", 100, "Test income")
    wallet.edit_entry(0, category="Расход", amount=50)
    assert wallet.balance == 50


def test_search_entry(wallet):
    wallet.add_entry("Доход", "2022-01-01", 100, "Test income")
    wallet.add_entry("Доход", "2022-01-01", 150, "Second test income")
    assert len(wallet.search_entries(category="Доход")) == 2

