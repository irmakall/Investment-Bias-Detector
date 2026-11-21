import json
import sys

from src.eval import run

GOOD = {"result": {"rationale": "r", "label": "no_bias", "evidence": None,
                   "missing_checks": ["thesis"], "questions": [{"text": "Why this stock?", "check": "thesis"}]},
        "model": "m", "attempts": 1, "latency_s": 1.0, "input_tokens": 10, "output_tokens": 5}


def test_evidence_grounding_ignores_case_and_spaces():
    assert run.is_grounded("Not  selling until", "I am not selling until even")
    assert not run.is_grounded("diamond hands", "I am not selling until even")


def test_advice_phrases_are_flagged():
    questions = [{"text": "Could this capital be deployed into better opportunities elsewhere?", "check": "opportunity_cost"},
                 {"text": "What would prove your thesis wrong?", "check": "invalidation"},
                 {"text": "Isn't it overvalued at this price?", "check": "valuation"}]
    assert len(run.flagged_questions(questions)) == 2


def test_priority_check_rule():
    q = [{"text": "...", "check": "valuation"}]
    assert run.targets_priority_check("fomo", ["valuation", "thesis"], q) is True
    assert run.targets_priority_check("fomo", ["valuation", "thesis"], [{"text": "...", "check": "thesis"}]) is False
    assert run.targets_priority_check("fomo", ["thesis"], q) is None          # no priority check missing
    assert run.targets_priority_check("no_bias", ["thesis"], q) is None


def test_temporary_errors_are_recognised():
    assert run.is_temporary_error({"error": "API call failed: ServerError: 503 UNAVAILABLE"})
    assert run.is_temporary_error({"error": "API call failed: ClientError: 429 RESOURCE_EXHAUSTED"})
    assert not run.is_temporary_error({"error": "Invalid output after 2 attempts"})
    assert not run.is_temporary_error(GOOD)


def test_cache_key_depends_on_model_and_text():
    assert run.cache_key("a", "x") != run.cache_key("b", "x") != run.cache_key("a", "y")


def test_cache_is_used_and_errors_are_not_cached(tmp_path, monkeypatch):
    monkeypatch.setattr(run, "CACHE_DIR", tmp_path)
    calls = []
    monkeypatch.setattr(run, "analyze", lambda text, client, model: calls.append(text) or GOOD)
    assert run.analyze_cached("note", None, "m", fresh=False, delay_s=0) == (GOOD, False)
    assert run.analyze_cached("note", None, "m", fresh=False, delay_s=0) == (GOOD, True)
    assert len(calls) == 1                                                  # second answer came from disk

    monkeypatch.setattr(run, "analyze", lambda text, client, model: {"error": "bad output"})
    run.analyze_cached("other", None, "m", fresh=False, delay_s=0)
    assert len(list(tmp_path.iterdir())) == 1                               # the error was not cached


def test_full_run_with_fake_gemini(tmp_path, monkeypatch):
    for name in ["CACHE_DIR", "ERRORS_DIR", "RESULTS_DIR"]:
        monkeypatch.setattr(run, name, tmp_path / name)
    monkeypatch.setattr(run, "analyze", lambda text, client, model: GOOD)
    monkeypatch.setattr(run, "get_client", lambda: None)
    monkeypatch.setattr(run, "get_model", lambda: "fake-model")
    monkeypatch.setattr(sys, "argv", ["run", "--limit", "6", "--delay", "0"])
    run.main()

    results = json.loads(next((tmp_path / "RESULTS_DIR").glob("*.json")).read_text())
    assert results["setup"]["llm_model"] == "fake-model" and results["setup"]["n_test"] == 6
    assert results["llm"]["n_errors"] == 0 and 0 <= results["llm"]["macro_f1"] <= 1
    assert not (tmp_path / "RESULTS_DIR" / "latest.md").exists()           # partial run keeps the README table
