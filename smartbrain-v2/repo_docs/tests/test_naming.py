from __future__ import annotations

import hashlib

import pytest

from repo_docs.naming import NamingError, assign_service_ids, service_id_for


@pytest.mark.parametrize("repo,sid", [
    ("TVS-CPS-BACKEND", "tvs-cps-backend"),
    ("BS2.0Backend_Integration", "bs2-0-backend-integration"),
    ("PaymentService", "payment-service"),
    ("tvsm-location-FE", "tvsm-location-fe"),
    ("Catalog-Microservice-Backend-for-Frontend-Layer",
     "catalog-microservice-backend-for-frontend-layer"),
    ("bto_api", "bto-api"),
    ("HTTPServer", "http-server"),
    ("--x__y--", "x-y"),
])
def test_service_id_for(repo, sid):
    assert service_id_for(repo) == sid


def test_collision_payment_service():
    """Both repos kept; the one whose lowercase name equals the base keeps it."""
    ids, collided = assign_service_ids(["PaymentService", "Payment-Service", "tvsm-auth"])
    h = hashlib.sha1(b"PaymentService").hexdigest()[:6]
    assert ids["Payment-Service"] == "payment-service"
    assert ids["PaymentService"] == f"payment-service-{h}"
    assert ids["tvsm-auth"] == "tvsm-auth"
    assert collided == {"PaymentService", "Payment-Service"}


def test_collision_no_exact_keeper():
    ids, collided = assign_service_ids(["FooBar", "Foo_Bar"])
    assert all(v.startswith("foo-bar-") for v in ids.values()) and len(set(ids.values())) == 2
    assert collided == {"FooBar", "Foo_Bar"}


def test_overrides_applied_and_unique():
    ids, collided = assign_service_ids(["PaymentService", "Payment-Service"],
                                       {"PaymentService": "payment-core"})
    assert ids == {"PaymentService": "payment-core", "Payment-Service": "payment-service"}
    assert not collided
    with pytest.raises(NamingError):
        assign_service_ids(["a", "b"], {"a": "x", "b": "x"})
