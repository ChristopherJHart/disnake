import pytest

from disnake.flags import ListBaseFlags, fill_with_flags, flag_value


@fill_with_flags()
class _ListFlags(ListBaseFlags):
    @flag_value
    def flag1(self):
        return 1 << 0

    @flag_value
    def flag2(self):
        return 1 << 1

    @flag_value
    def flag3(self):
        return 1 << 2


class TestListBaseFlags:
    @pytest.mark.parametrize(
        ("kwargs", "expected_value", "expected_values"),
        [
            ({}, 0, []),
            ({"flag2": True}, 2, [2]),
            ({"flag3": True, "flag2": False, "flag1": True}, 5, [1, 3]),
        ],
    )
    def test_init(self, kwargs, expected_value, expected_values) -> None:
        flags = _ListFlags(**kwargs)
        assert flags.value == expected_value
        assert flags.values == expected_values

    def test_from_values(self) -> None:
        flags = _ListFlags._from_values([2, 3, 4, 5, 10])
        assert flags.value == 542
        assert flags.values == [2, 3, 4, 5, 10]

    @pytest.mark.parametrize("value", [-1, 0, 100])
    def test_from_values__invalid(self, value) -> None:
        with pytest.raises(ValueError, match=r"Flag values must be within \(0, 64\)"):
            _ListFlags._from_values([1, 2, value, 3])

    def test_update(self) -> None:
        flags = _ListFlags(flag2=True)
        flags.flag2 = False
        flags.flag3 = True
        assert flags.value == 4
        assert flags.values == [3]
