"""WER, bootstrap and QA scoring tests (§11.2, §10.4)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.analytics.qa_scoring import score_call  # noqa: E402

from eval.metrics.bootstrap import bootstrap_metric, paired_bootstrap  # noqa: E402
from eval.metrics.wer import corpus_wer, macro_wer, normalize, wer  # noqa: E402


def test_wer_perfect():
    assert wer("hello world", "hello world") == 0.0


def test_wer_one_substitution():
    assert wer("hello world", "hello word") == 0.5


def test_wer_deletion():
    assert wer("one two three", "one three") == pytest.approx(1 / 3, 0.01)


def test_wer_insertion():
    assert wer("one two", "one two three") == 0.5


def test_symmetric_normalization():
    assert normalize("नमस्ते! १२३") == normalize("नमस्ते 123")
    assert normalize("AS-Ma-Na") == normalize("as ma na")


def test_corpus_and_macro():
    pairs = [("a b", "a b"), ("c d", "c x")]
    assert corpus_wer(pairs) == pytest.approx(0.25, 0.01)
    data = {"hi": [("a", "a")], "gu": [("a b", "a x")]}
    assert macro_wer(data) == 0.25


def test_bootstrap_ci_brackets_mean():
    r = bootstrap_metric([0.1, 0.2, 0.3, 0.4], resamples=500, seed=1)
    assert r["ci_low"] <= r["mean"] <= r["ci_high"]
    assert r["resamples"] == 500


def test_paired_bootstrap():
    r = paired_bootstrap([0.2, 0.3, 0.25], [0.1, 0.15, 0.12], resamples=500, seed=1)
    assert r["difference"] > 0
    assert r["significant"] is True


def test_qa_scoring_perfect():
    result = score_call(
        {"goal_achieved": True}, "a long transcript with plenty of words", " booked for 500 rupees at 11:30 on 112 ",
        [1.0, 1.0], [1200, 1500], {"500", "30", "11", "112"}, [],
    )
    assert result["total"] == 100
    assert result["judged_by"] == "machine"


def test_qa_scoring_penalizes_bad_figures():
    result = score_call({}, "x", "fee is 999 rupees", [0.5], [6000], {"500"}, [])
    assert result["total"] < 100
    assert result["breakdown"]["figure_accuracy"]["score"] < 20
