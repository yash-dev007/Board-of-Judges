from __future__ import annotations

from bojudges.core.verifier import LineVerifier
from bojudges.schema import Issue, Severity

SQLI_SOURCE = """\
def find_user(conn, name):
    cur = conn.cursor()
    sql = "SELECT * FROM users WHERE name = '" + name + "'"
    cur.execute(sql)
    return cur.fetchall()
"""


def _issue(line: int, category: str = "sql-injection") -> Issue:
    return Issue(
        id="t:0",
        severity=Severity.HIGH,
        title="x",
        description="d",
        file="s.py",
        line=line,
        category=category,
        confidence=0.9,
    )


def test_verify_valid_sqli():
    v = LineVerifier()
    result = v.verify(_issue(4, "sql-injection"), {"s.py": SQLI_SOURCE})
    assert result.verified is True


def test_verify_line_out_of_range():
    v = LineVerifier()
    result = v.verify(_issue(50, "sql-injection"), {"s.py": SQLI_SOURCE})
    assert result.verified is False
    assert "out of range" in result.reason


def test_verify_wrong_category_rejected():
    v = LineVerifier()
    # Line 4 is the execute() line — not XSS-related
    result = v.verify(_issue(4, "xss"), {"s.py": SQLI_SOURCE})
    assert result.verified is False


def test_verify_unknown_category_accepts():
    v = LineVerifier()
    result = v.verify(_issue(4, "novel-category"), {"s.py": SQLI_SOURCE})
    assert result.verified is True


def test_verify_file_level():
    v = LineVerifier()
    result = v.verify(_issue(-1, "sql-injection"), {"s.py": SQLI_SOURCE})
    assert result.verified is True


def test_verify_missing_file():
    v = LineVerifier()
    result = v.verify(_issue(4, "sql-injection"), {})
    assert result.verified is False
