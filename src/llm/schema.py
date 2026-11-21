"""The structure the LLM must return for one note (REQ-011, REQUIREMENTS §7.3).

Two layers of checking:
- The JSON schema generated from these classes is sent to Gemini, so the model is told
  which fields and values are allowed. Field descriptions are part of that schema and
  act as short instructions to the model.
- Gemini does not run our validators. Every response is therefore parsed with
  Analysis.model_validate_json() in our own code. A ValueError there means an invalid
  answer, which triggers the single retry (REQ-011).

Design choices:
- `rationale` comes first. The model writes its reasoning before it commits to a label,
  which usually gives better labels than answering first and justifying afterwards.
- `label` is a Literal of the 5 evaluated labels. herd/confirmation are not evaluated
  in the MVP (REQUIREMENTS §4.1), so the model is not allowed to output them.
- Classification and questions come from one call: cheaper and faster on the free tier,
  and the label is written before the questions, so the questions cannot change it.
"""

from typing import Literal

from pydantic import BaseModel, Field, model_validator

# Literal values must be written out, not built from a set at runtime.
# tests/test_schema.py checks that they match labels.py and REQUIREMENTS §4.4.
Label = Literal["fomo", "loss_aversion", "anchoring", "overconfidence", "no_bias"]
Check = Literal["thesis", "invalidation", "valuation", "research",
                "position_size", "time_horizon", "opportunity_cost"]


class Question(BaseModel):
    text: str = Field(min_length=1, description="A reflective question to the author. No advice, no verdict on the asset.")
    check: Check = Field(description="The skipped check this question targets.")


class Analysis(BaseModel):
    rationale: str = Field(min_length=1, description="Short reasoning: which cue in the text decides the label, and why.")
    label: Label = Field(description="Exactly one label: the bias the decision rests on, or no_bias.")
    evidence: str | None = Field(description="The shortest exact phrase from the text that shows the bias. null for no_bias.")
    missing_checks: list[Check] = Field(description="Checks a literate investor makes that this note does not mention.")
    questions: list[Question] = Field(max_length=3, description="Up to 3 questions, each targeting one missing check.")

    @model_validator(mode="after")
    def evidence_matches_label(self):
        """Guideline Step 4: a bias label needs evidence, no_bias has none."""
        if self.label == "no_bias" and self.evidence:
            raise ValueError("no_bias must not have evidence")
        if self.label != "no_bias" and not self.evidence:
            raise ValueError(f"label '{self.label}' needs an evidence phrase")
        return self

    @model_validator(mode="after")
    def questions_target_missing_checks(self):
        """REQ-027: questions only ask about checks the note actually skipped."""
        if len(set(self.missing_checks)) != len(self.missing_checks):
            raise ValueError("missing_checks contains a duplicate")
        for question in self.questions:
            if question.check not in self.missing_checks:
                raise ValueError(f"question targets '{question.check}', which is not in missing_checks")
        return self
