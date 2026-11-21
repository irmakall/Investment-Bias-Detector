"""analyze() with a fake client: no network, no API key."""

from types import SimpleNamespace

from src.llm.gemini import analyze

VALID = ('{"rationale": "Waits to break even.", "label": "loss_aversion", "evidence": "back to even", '
         '"missing_checks": ["invalidation"], "questions": [{"text": "What would prove you wrong?", '
         '"check": "invalidation"}]}')
INVALID = '{"rationale": "r", "label": "loss_aversion", "evidence": null, "missing_checks": [], "questions": []}'


class FakeClient:
    """Returns the given replies in order. A reply that is an Exception is raised instead."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = []
        self.models = self

    def generate_content(self, model, contents, config):
        self.calls.append(contents)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        usage = SimpleNamespace(prompt_token_count=100, candidates_token_count=20, thoughts_token_count=None)
        return SimpleNamespace(text=reply, usage_metadata=usage)


def test_valid_answer():
    out = analyze("Not selling until I'm back to even.", client=FakeClient(VALID), model="m")
    assert out["result"]["label"] == "loss_aversion"
    assert out["attempts"] == 1 and out["input_tokens"] == 100 and out["output_tokens"] == 20


def test_invalid_answer_is_retried_with_feedback():
    client = FakeClient(INVALID, VALID)
    out = analyze("text", client=client, model="m")
    assert out["result"]["label"] == "loss_aversion" and out["attempts"] == 2
    assert len(client.calls[1]) == 3                    # note + invalid answer + feedback
    assert "invalid" in client.calls[1][2].parts[0].text


def test_two_invalid_answers_give_an_error():
    out = analyze("text", client=FakeClient(INVALID, "not json"), model="m")
    assert "error" in out and out["attempts"] == 2


def test_api_failure_gives_an_error_instead_of_raising():
    out = analyze("text", client=FakeClient(RuntimeError("429 quota")), model="m")
    assert out["error"].startswith("API call failed") and "429" in out["error"]
