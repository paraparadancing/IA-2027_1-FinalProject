from schebuilder.loader import load_from_csv
from pathlib import Path

def test_good_data():
    ai_path = Path("tests/test_data/ai_groups.csv")
    groups_ai = load_from_csv(ai_path)
    assert len(groups_ai) == 7

    vlsi_path = Path("tests/test_data/vlsi_groups.csv")
    groups_vlsi = load_from_csv(vlsi_path)
    assert len(groups_vlsi) == 6
