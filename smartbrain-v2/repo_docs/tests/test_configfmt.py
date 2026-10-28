from __future__ import annotations

from repo_docs.extractors import configfmt as cf


def test_properties():
    text = ("# comment\n! bang comment\nserver.servlet.context-path=/${spring.application.name}\n"
            "a.b : spaced\nc.d value with spaces\nmulti=one\\\n    two\nuni=caf\\u00e9\n"
            "esc\\:key=v\nempty=\n")
    e = {k: (v, ln) for k, v, ln in cf.parse_properties(text).entries}
    assert e["server.servlet.context-path"] == ("/${spring.application.name}", 3)
    assert e["a.b"] == ("spaced", 4)
    assert e["c.d"] == ("value with spaces", 5)
    assert e["multi"] == ("onetwo", 6)
    assert e["uni"][0] == "café"
    assert e["esc:key"][0] == "v"
    assert e["empty"] == ("", 10)


def test_dotenv():
    text = ('# c\nexport A=1\nB="two words" # c\nC=\'single\'\nD=plain # comment\n'
            'E="multi\nline"\nF=x#notcomment\n')
    r = cf.parse_dotenv(text)
    e = {k: (v, ln) for k, v, ln in r.entries}
    assert r.ok
    assert e["A"] == ("1", 2) and e["B"] == ("two words", 3) and e["C"] == ("single", 4)
    assert e["D"] == ("plain", 5) and e["E"] == ("multi\nline", 6) and e["F"][0] == "x#notcomment"
    assert not cf.parse_dotenv("garbage line\n").ok


def test_jsonc_host_json_style():
    # PaymentService host.json has a // comment line
    text = '{\n  "version": "2.0",\n  // Pipeline test\n  "logging": {\n    "a": [1, 2,],\n' \
           '    "url": "http://x//y" /* c */\n  },\n}\n'
    r = cf.parse_jsonc(text)
    assert r.ok and r.data["logging"]["url"] == "http://x//y"
    lines = {p: ln for p, _, ln in r.entries}
    assert lines[("version",)] == 2 and lines[("logging", "url")] == 6
    assert lines[("logging", "a", 1)] == 5
    bad = cf.parse_jsonc('{"a": }')
    assert not bad.ok and bad.error.startswith("JSONDecodeError")


def test_yaml_multidoc_profiles_and_lines():
    text = ("spring:\n  application:\n    name: mdp\nserver:\n  port: 8080\n---\n"
            "spring:\n  config:\n    activate:\n      on-profile: uat\nserver:\n  port: 9090\n"
            "list:\n  - a\n  - b: 1\n")
    docs, ok, err = cf.yaml_with_lines(text)
    assert ok and len(docs) == 2
    assert docs[0].profile is None and docs[1].profile == "uat"
    l1 = {p: (v, ln) for p, v, ln in docs[1].entries}
    assert l1[("server", "port")] == (9090, 12)
    assert l1[("list", 0)] == ("a", 14)
    assert l1[("list", 1, "b")] == (1, 15)
    docs, ok, err = cf.yaml_with_lines("a: [1,\nb: : :\n")
    assert not ok and "YAMLError" in err


def test_xml_lines_and_namespaces():
    text = ('<?xml version="1.0"?>\n<project xmlns="http://maven.apache.org/POM/4.0.0">\n'
            '  <modules>\n    <module>a</module>\n  </modules>\n</project>\n')
    d = cf.xml_with_lines(text)
    assert d.ok and d.root.tag == "project"
    m = d.root.find("modules/module")
    assert m.text == "a" and d.line(m) == 4
    assert not cf.xml_with_lines("<a><b></a>").ok


def test_dockerfile():
    text = ("# c\nFROM maven:3.9 AS build\nRUN mvn \\\n  # inner comment\n  package\n"
            "FROM amazoncorretto:17\nENV TZ Asia/Kolkata\nENV A=1 B=\"two words\"\nEXPOSE 8080\n"
            'ENTRYPOINT ["java", "-jar", "x.jar"]\n')
    r = cf.parse_dockerfile(text)
    assert r.ok
    ins = [(i, ln) for i, _, ln in r.entries]
    assert ins == [("FROM", 2), ("RUN", 3), ("FROM", 6), ("ENV", 7), ("ENV", 8), ("EXPOSE", 9),
                   ("ENTRYPOINT", 10)]
    assert r.entries[1][1] == "mvn package"
    assert cf.docker_kv("TZ Asia/Kolkata") == [("TZ", "Asia/Kolkata")]
    assert cf.docker_kv('A=1 B="two words"') == [("A", "1"), ("B", "two words")]
    assert not cf.parse_dockerfile("FROM x\nBOGUS y\n").ok
