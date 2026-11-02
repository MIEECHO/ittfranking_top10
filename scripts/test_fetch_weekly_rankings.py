import unittest

from fetch_weekly_rankings import parse


def fixture(source="ittf", ranks=range(1, 11)):
    header = "Rank Name Assoc Points".split()
    table_id = ' id="tablepress-72"' if source == "butterfly" else ""
    rows = "".join(
        f"<tr><td>{rank}</td><td><a>Player {rank}</a></td>"
        f"<td>{'France' if source == 'butterfly' else 'FRA'}</td>"
        f"<td>{2000-rank:,}</td></tr>" for rank in ranks
    )
    return ("<h2>Men's Singles</h2><p>2026 Week #44</p>"
            f"<table{table_id}><tr>" + "".join(f"<th>{h}</th>" for h in header)
            + "</tr>" + rows + "</table>")


class ParsingTests(unittest.TestCase):
    def test_official_fixture(self):
        rows = parse(fixture(), "2026-W44", "men", "ittf")
        self.assertEqual(len(rows), 10)
        self.assertEqual(rows[0]["points"], "1999")

    def test_butterfly_association(self):
        rows = parse(fixture("butterfly"), "2026-W44", "men", "butterfly")
        self.assertEqual(rows[0]["assoc"], "FRA")

    def test_wrong_week(self):
        with self.assertRaises(ValueError):
            parse(fixture(), "2026-W43", "men", "ittf")

    def test_wrong_category(self):
        with self.assertRaises(ValueError):
            parse(fixture(), "2026-W44", "women", "ittf")

    def test_incomplete_or_duplicate_ranks(self):
        for ranks in (range(1, 10), [1] * 10):
            with self.subTest(ranks=ranks), self.assertRaises(ValueError):
                parse(fixture(ranks=ranks), "2026-W44", "men", "ittf")

    def test_ascending_points(self):
        with self.assertRaises(ValueError):
            parse(fixture().replace("1,990", "9,999"), "2026-W44", "men", "ittf")


if __name__ == "__main__":
    unittest.main()
