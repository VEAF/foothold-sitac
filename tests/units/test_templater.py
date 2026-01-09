# test foothold_sitac/templater.py

import pytest

from foothold_sitac.templater import _base36_encode


@pytest.mark.parametrize(
    ("num", "expected"),
    [
        (0, "0"),
        (1, "1"),
        (9, "9"),
        (10, "a"),
        (35, "z"),
        (36, "10"),
        (71, "1z"),
        (1296, "100"),  # 36^2
        (46656, "1000"),  # 36^3
        (1704067200, "s6k2o0"),  # typical timestamp
    ],
)
def test_base36_encode(num: int, expected: str) -> None:
    assert _base36_encode(num) == expected


@pytest.mark.parametrize("num", [-1, -1000000])
def test_base36_encode_negative_raises(num: int) -> None:
    with pytest.raises(ValueError, match="Cannot encode negative numbers"):
        _base36_encode(num)
