from __future__ import annotations

from bojudges.core.router import Router


def test_route_python_sqli():
    src = "cur.execute('SELECT * FROM users WHERE name = ' + name)"
    r = Router().route("app.py", src)
    assert r.language == "python"
    assert "security" in r.domain_tags
    assert "sql-injection" in r.risk_tags


def test_route_typescript():
    src = "const x: string = userInput;"
    r = Router().route("a.ts", src)
    assert r.language == "typescript"
    assert "frontend" in r.domain_tags


def test_route_dockerfile():
    r = Router().route("Dockerfile", "FROM python:3.11\nRUN pip install flask\n")
    assert r.language == "dockerfile"
    assert "devops" in r.domain_tags


def test_route_unknown():
    r = Router().route("x.whatever", "blah")
    assert r.language == "unknown"
    assert r.domain_tags == ["code"]


def test_route_sensitivity_high_when_auth_present():
    src = "def login(user, password):\n    session['user'] = user\n"
    r = Router().route("auth.py", src)
    assert r.sensitivity == "high"
