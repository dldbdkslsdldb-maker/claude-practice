import pytest
from collections import defaultdict


# ── Pure helpers extracted for testing ──────────────────────────

def is_all_numeric_missing(row):
    return (row.get("판매수량", "").strip() == "" and
            row.get("매출액", "").strip() == "" and
            row.get("영업이익", "").strip() == "")


def to_float(v):
    try:
        return float(v.replace(",", "").strip())
    except:
        return 0.0


def clean_rows(rows):
    cleaned = []
    seen = set()
    for row in rows:
        if is_all_numeric_missing(row):
            continue
        oid = row["주문번호"]
        if oid in seen:
            continue
        seen.add(oid)
        if row.get("담당자", "").strip() == "":
            row["담당자"] = "미확인"
        row["주문일"] = row["주문일"].replace("/", "-")
        cleaned.append(row)
    return cleaned


# ── is_all_numeric_missing ───────────────────────────────────────

class TestIsAllNumericMissing:
    def test_all_missing(self):
        row = {"판매수량": "", "매출액": "", "영업이익": ""}
        assert is_all_numeric_missing(row) is True

    def test_whitespace_only(self):
        row = {"판매수량": "  ", "매출액": " ", "영업이익": "\t"}
        assert is_all_numeric_missing(row) is True

    def test_one_field_present(self):
        row = {"판매수량": "5", "매출액": "", "영업이익": ""}
        assert is_all_numeric_missing(row) is False

    def test_all_present(self):
        row = {"판매수량": "10", "매출액": "50000", "영업이익": "5000"}
        assert is_all_numeric_missing(row) is False

    def test_missing_keys_treated_as_empty(self):
        assert is_all_numeric_missing({}) is True


# ── to_float ────────────────────────────────────────────────────

class TestToFloat:
    def test_plain_number(self):
        assert to_float("1234") == 1234.0

    def test_comma_separated(self):
        assert to_float("1,234,567") == 1234567.0

    def test_with_spaces(self):
        assert to_float("  500 ") == 500.0

    def test_decimal(self):
        assert to_float("3.14") == pytest.approx(3.14)

    def test_empty_string(self):
        assert to_float("") == 0.0

    def test_non_numeric(self):
        assert to_float("N/A") == 0.0

    def test_negative(self):
        assert to_float("-200") == -200.0


# ── clean_rows ──────────────────────────────────────────────────

def _make_row(order_id, sales="1000", qty="2", profit="100",
              manager="홍길동", date="2024-01-15"):
    return {
        "주문번호": order_id,
        "매출액": sales,
        "판매수량": qty,
        "영업이익": profit,
        "담당자": manager,
        "주문일": date,
    }


class TestCleanRows:
    def test_removes_all_numeric_missing_row(self):
        rows = [
            _make_row("A001"),
            {"주문번호": "A002", "매출액": "", "판매수량": "", "영업이익": "",
             "담당자": "홍길동", "주문일": "2024-02-01"},
        ]
        result = clean_rows(rows)
        assert len(result) == 1
        assert result[0]["주문번호"] == "A001"

    def test_removes_duplicate_order_id(self):
        rows = [_make_row("A001"), _make_row("A001")]
        result = clean_rows(rows)
        assert len(result) == 1

    def test_fills_missing_manager(self):
        rows = [_make_row("A001", manager="")]
        result = clean_rows(rows)
        assert result[0]["담당자"] == "미확인"

    def test_normalizes_date_slash_to_dash(self):
        rows = [_make_row("A001", date="2024/01/15")]
        result = clean_rows(rows)
        assert result[0]["주문일"] == "2024-01-15"

    def test_keeps_valid_rows_unchanged(self):
        rows = [_make_row("A001"), _make_row("A002")]
        result = clean_rows(rows)
        assert len(result) == 2

    def test_empty_input(self):
        assert clean_rows([]) == []


# ── aggregation helpers ──────────────────────────────────────────

class TestAggregation:
    def _sample_cleaned(self):
        return [
            {"제품분류": "IT기기", "매출액": "500,000", "영업이익": "50,000",
             "지역": "서울", "담당자": "김철수", "주문일": "2024-03-10", "주문번호": "X1"},
            {"제품분류": "사무용품", "매출액": "200,000", "영업이익": "20,000",
             "지역": "부산", "담당자": "이영희", "주문일": "2024-03-15", "주문번호": "X2"},
            {"제품분류": "IT기기", "매출액": "300,000", "영업이익": "30,000",
             "지역": "서울", "담당자": "김철수", "주문일": "2024-04-05", "주문번호": "X3"},
        ]

    def test_category_sales_sum(self):
        cleaned = self._sample_cleaned()
        cat_sales = defaultdict(float)
        for row in cleaned:
            s = to_float(row["매출액"])
            if s > 0:
                cat_sales[row["제품분류"]] += s
        assert cat_sales["IT기기"] == pytest.approx(800_000)
        assert cat_sales["사무용품"] == pytest.approx(200_000)

    def test_monthly_grouping(self):
        cleaned = self._sample_cleaned()
        month_sales = defaultdict(float)
        for row in cleaned:
            m = row["주문일"][:7]
            s = to_float(row["매출액"])
            if s > 0:
                month_sales[m] += s
        assert month_sales["2024-03"] == pytest.approx(700_000)
        assert month_sales["2024-04"] == pytest.approx(300_000)

    def test_margin_calculation(self):
        total_sales = 1_000_000.0
        total_profit = 100_000.0
        margin = total_profit / total_sales * 100
        assert margin == pytest.approx(10.0)

    def test_zero_sales_guard(self):
        total_sales = 0.0
        total_profit = 0.0
        margin = total_profit / total_sales * 100 if total_sales else 0
        assert margin == 0
