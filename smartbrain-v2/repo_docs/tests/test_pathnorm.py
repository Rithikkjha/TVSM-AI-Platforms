from __future__ import annotations

import pytest

from repo_docs import pathnorm as pn


@pytest.mark.parametrize("raw,display,norm", [
    ("api/bookings/{id}", "/api/bookings/{id}", "/api/bookings/{}"),
    ("/x/{id:int}", "/x/{id}", "/x/{}"),
    (r"/x/{code:regex(^\d{{3}}$)}/y", "/x/{code}/y", "/x/{}/y"),
    (r"/x/{code:regex(\d{3})}", "/x/{code}", "/x/{}"),
    ("/x/{id?}", "/x/{id}", "/x/{}"),
    ("/files/{*path}", "/files/{path}", "/files/{}"),
    ("/files/{**slug}", "/files/{slug}", "/files/{}"),
    ("/x/{page=1}", "/x/{page}", "/x/{}"),
    ("/regions/:country/states", "/regions/{country}/states", "/regions/{}/states"),
    ("/claim/[claimId]", "/claim/{claimId}", "/claim/{}"),
    ("/docs/[...slug]", "/docs/{slug}", "/docs/{}"),
    ("/docs/[[...slug]]", "/docs/{slug}", "/docs/{}"),
    ("/a/${this.user.id}/b", "/a/{id}/b", "/a/{}/b"),
    ("/a/${encodeURIComponent(x)}", "/a/{}", "/a/{}"),
    ("/a/{0}/b/{1}", "/a/{0}/b/{1}", "/a/{}/b/{}"),
    ("/a/%s/b/%d", "/a/{}/b/{}", "/a/{}/b/{}"),
    ("/a/{}/b", "/a/{}/b", "/a/{}/b"),
    ("~/api/service/appointment/fetch/slot", "/api/service/appointment/fetch/slot",
     "/api/service/appointment/fetch/slot"),
    ("//api//x/", "/api/x", "/api/x"),
    ("", "/", "/"),
    ("https://h.example.invalid:8080/api/x?y=1#f", "/api/x", "/api/x"),
    ("/x?q={q}", "/x", "/x"),
])
def test_forms(raw, display, norm):
    assert pn.display_path(raw) == display
    assert pn.normalize(raw) == norm


def test_split_url():
    assert pn.split_url("https://api.example.invalid:8443/v1/a?b=1&c=&b=2#frag") == (
        "https://api.example.invalid:8443", "/v1/a", ["b", "c"])
    assert pn.split_url("/v1/a") == (None, "/v1/a", [])
    assert pn.split_url("${base}/v1/x?id=1") == ("${base}", "/v1/x", ["id"])
    assert pn.split_url("{}/v1/x") == ("{}", "/v1/x", [])


def test_match_key_and_join():
    assert pn.match_key("/API/Bookings/{id}/") == "/api/bookings/{}"
    assert pn.match_key("/") == "/"
    assert pn.join("/api/x/", "/y") == "/api/x/y"
    assert pn.join("api", "") == "/api"
    assert pn.join("", "") == "/"
    assert pn.join("/a//", "b//c") == "/a/b/c"
