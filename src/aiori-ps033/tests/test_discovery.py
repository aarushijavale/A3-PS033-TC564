
import sys
from pathlib import Path

import pytest
import dns.flags

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "client")
)

import discovery_client


def test_valid_latency_metadata():
    metadata = discovery_client.validate_txt_metadata(
        "version=1.0; capability=latency-measurement; auth=bearer",
        "latency"
    )

    assert metadata["version"] == "1.0"
    assert metadata["capability"] == "latency-measurement"
    assert metadata["auth"] == "bearer"


def test_rejects_unsupported_version():
    with pytest.raises(ValueError, match="Unsupported service metadata version"):
        discovery_client.validate_txt_metadata(
            "version=2.0; capability=latency-measurement; auth=bearer",
            "latency"
        )


def test_rejects_wrong_capability():
    with pytest.raises(ValueError, match="Unexpected service capability"):
        discovery_client.validate_txt_metadata(
            "version=1.0; capability=wrong-capability; auth=bearer",
            "latency"
        )


def test_rejects_wrong_authentication():
    with pytest.raises(ValueError, match="Unsupported authentication scheme"):
        discovery_client.validate_txt_metadata(
            "version=1.0; capability=latency-measurement; auth=basic",
            "latency"
        )


def test_rejects_missing_metadata_field():
    with pytest.raises(ValueError, match="Missing or unknown TXT metadata fields"):
        discovery_client.validate_txt_metadata(
            "version=1.0; capability=latency-measurement",
            "latency"
        )


def test_rejects_duplicate_metadata_field():
    with pytest.raises(ValueError, match="Duplicate TXT metadata field"):
        discovery_client.validate_txt_metadata(
            "version=1.0; version=1.0; capability=latency-measurement; auth=bearer",
            "latency"
        )


def test_rejects_malformed_metadata():
    with pytest.raises(ValueError, match="Malformed TXT metadata"):
        discovery_client.validate_txt_metadata(
            "version=1.0; invalid-field; auth=bearer",
            "latency"
        )


def test_rejects_missing_dnssec_ad_flag():
    class FakeAnswer:
        response = type("Response", (), {"flags": 0})()

    class FakeResolver:
        def resolve(self, name, record_type):
            return FakeAnswer()

    with pytest.raises(RuntimeError, match="AD flag missing"):
        discovery_client.query_dns(
            FakeResolver(),
            "_latency._diag.diag.lab.test",
            "SVCB"
        )


def test_all_service_ports():
    assert discovery_client.SERVICES["latency"]["port"] == 8443
    assert discovery_client.SERVICES["traceroute"]["port"] == 8444
    assert discovery_client.SERVICES["pathmtu"]["port"] == 8445
