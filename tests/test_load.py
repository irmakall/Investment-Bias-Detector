import pandas as pd

from src.data.load import base_filter, drop_repeated


def frame(texts):
    return pd.DataFrame({"id": [str(i) for i in range(len(texts))], "text": texts})


def test_base_filter_drops_short_long_and_bot_texts():
    df = frame(["too short", "this one has enough words", "x " * 800, "I am a bot from the mods, beep"])
    assert base_filter(df)["text"].tolist() == ["this one has enough words"]


def test_drop_repeated_removes_every_copy_after_normalizing():
    df = frame(["Buy the dip now guys", "  buy the DIP now guys ", "a unique sentence here"])
    assert drop_repeated(df)["text"].tolist() == ["a unique sentence here"]
