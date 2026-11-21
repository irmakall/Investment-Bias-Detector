import pandas as pd
import pytest

from src.data.split import ids_hash, load_eval_items, make_split


def items(labels):
    """Small fake eval set: ids "0", "1", ... with the given labels."""
    return pd.DataFrame({"id": [str(i) for i in range(len(labels))], "label": labels})


FAKE = items(["no_bias"] * 20 + ["fomo"] * 10 + ["anchoring"] * 10)


def test_split_has_no_overlap_and_covers_everything():
    train, test = make_split(FAKE)
    assert set(train) | set(test) == set(FAKE["id"])        # nothing lost
    assert set(train) & set(test) == set()                   # no leakage


def test_split_is_stratified():
    train, test = make_split(FAKE, test_size=0.3)
    test_rows = FAKE[FAKE["id"].isin(test)]
    assert test_rows["label"].value_counts().to_dict() == {"no_bias": 6, "fomo": 3, "anchoring": 3}


def test_same_seed_gives_same_split():
    assert make_split(FAKE, seed=1) == make_split(FAKE, seed=1)
    assert make_split(FAKE, seed=1)[1] != make_split(FAKE, seed=2)[1]


def test_hash_ignores_order_but_not_content():
    assert ids_hash(["a", "b"]) != ids_hash(["a", "c"])     # different IDs -> different hash
    assert ids_hash(["b", "a"]) == ids_hash(["a", "b"])     # same IDs, any order -> same hash


def test_load_keeps_evaluated_labels_and_rejects_multi_label(tmp_path):
    path = tmp_path / "labels.csv"
    path.write_text("id,status,labels\na,labeled,fomo\nb,labeled,herd\nc,skip,\n")
    assert load_eval_items(path).to_dict("list") == {"id": ["a"], "label": ["fomo"]}

    path.write_text("id,status,labels\na,labeled,fomo|overconfidence\n")
    with pytest.raises(ValueError):
        load_eval_items(path)
