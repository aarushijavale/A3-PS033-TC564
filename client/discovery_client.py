
import argparse
import os
import sys
import time
import requests
import dns.resolver
import dns.flags
import dns.rdtypes.svcbbase

DNS_SERVER = os.getenv("DNS_SERVER", "127.0.0.1")
DNS_PORT = int(os.getenv("DNS_PORT", "15354"))
API_TOKEN = os.getenv("API_TOKEN", "aiori-demo-token")

SERVICES = {
    "latency": {
        "endpoint": "/latency",
        "capability": "latency-measurement",
        "port": 8443
    },
    "traceroute": {
        "endpoint": "/traceroute",
        "capability": "simulated-traceroute",
        "port": 8444
    },
    "pathmtu": {
        "endpoint": "/path-mtu",
        "capability": "path-mtu-detection",
        "port": 8445
    }
}


def create_resolver():
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = [DNS_SERVER]
    resolver.port = DNS_PORT
    resolver.timeout = 3
    resolver.lifetime = 5
    resolver.use_edns(edns=0, ednsflags=dns.flags.DO)
    return resolver


def query_dns(resolver, query_name, record_type):
    answer = resolver.resolve(query_name, record_type)

    if not (answer.response.flags & dns.flags.AD):
        raise RuntimeError(
            f"DNSSEC validation failed for {record_type}: AD flag missing"
        )

    return answer


def validate_txt_metadata(txt_value, service_name):
    if service_name not in SERVICES:
        raise ValueError("Unknown diagnostic service")

    metadata = {}

    for item in txt_value.split(";"):
        if "=" not in item:
            raise ValueError("Malformed TXT metadata")

        key, value = item.strip().split("=", 1)

        if not key or not value:
            raise ValueError("Malformed TXT metadata")

        if key in metadata:
            raise ValueError("Duplicate TXT metadata field")

        metadata[key] = value

    required_fields = {"version", "capability", "auth"}

    if set(metadata.keys()) != required_fields:
        raise ValueError("Missing or unknown TXT metadata fields")

    if metadata["version"] != "1.0":
        raise ValueError("Unsupported service metadata version")

    if metadata["capability"] != SERVICES[service_name]["capability"]:
        raise ValueError("Unexpected service capability")

    if metadata["auth"] != "bearer":
        raise ValueError("Unsupported authentication scheme")

    return metadata


def discover_service(service_name):
    if service_name not in SERVICES:
        raise ValueError("Unknown diagnostic service")

    query_name = f"_{service_name}._diag.diag.lab.test"
    resolver = create_resolver()

    print(f"\n[1] Discovering: {service_name}")

    svcb_answer = query_dns(resolver, query_name, "SVCB")

    print("[2] DNSSEC validation for SVCB: PASSED")

    record = svcb_answer[0]
    target = str(record.target).rstrip(".")

    port_param = record.params.get(
        dns.rdtypes.svcbbase.ParamKey.PORT
    )

    if port_param is None:
        raise ValueError("Missing port in SVCB record")

    port = port_param.port

    alpn_param = record.params.get(
        dns.rdtypes.svcbbase.ParamKey.ALPN
    )

    if alpn_param is None:
        raise ValueError("Missing ALPN protocol")

    alpn = [
        item.decode("utf-8")
        for item in alpn_param.ids
    ]

    expected_target = f"{service_name}.diag.lab.test"
    expected_port = SERVICES[service_name]["port"]

    if not 1 <= port <= 65535:
        raise ValueError("Invalid service port")

    if target != expected_target:
        raise ValueError("Unexpected service target")

    if port != expected_port:
        raise ValueError("Unexpected service port")

    if "http/1.1" not in alpn:
        raise ValueError("Unsupported service protocol")

    txt_answer = query_dns(resolver, query_name, "TXT")

    print("[3] DNSSEC validation for TXT: PASSED")

    txt_value = b"".join(txt_answer[0].strings).decode("utf-8")
    metadata = validate_txt_metadata(txt_value, service_name)

    print("[4] Service metadata validated")
    print(f"    Target: {target}")
    print(f"    Port: {port}")
    print(f"    Protocol: {alpn}")
    print(f"    Version: {metadata['version']}")
    print(f"    Capability: {metadata['capability']}")
    print(f"    Authentication: {metadata['auth']}")

    return target, port


def invoke_service(service_name, target, port):
    endpoint = SERVICES[service_name]["endpoint"]
    url = f"http://{target}:{port}{endpoint}"

    headers = {
        "Authorization": f"Bearer {API_TOKEN}"
    }

    print("[5] Invoking diagnostic service...")

    for attempt in range(1, 4):
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=5
            )

            if response.status_code in (401, 403):
                raise RuntimeError(
                    f"Service authentication failed (HTTP {response.status_code})"
                )

            response.raise_for_status()

            print("[6] Service response received")
            return response.json()

        except (requests.ConnectionError, requests.Timeout) as error:
            if attempt == 3:
                raise RuntimeError(
                    "Diagnostic service is unavailable after 3 attempts"
                ) from error

            print(
                f"[WARNING] Attempt {attempt} failed. "
                "Retrying in 2 seconds..."
            )
            time.sleep(2)

        except requests.HTTPError as error:
            raise RuntimeError(
                f"Diagnostic service returned HTTP {error.response.status_code}"
            ) from error


def main():
    parser = argparse.ArgumentParser(
        description="AIORI DNS Diagnostic Discovery Client"
    )

    parser.add_argument(
        "service",
        choices=list(SERVICES.keys()),
        help="Diagnostic service to invoke"
    )

    args = parser.parse_args()

    try:
        target, port = discover_service(args.service)

        result = invoke_service(
            args.service,
            target,
            port
        )

        print("\n========== DIAGNOSTIC RESULT ==========")
        print(result)

    except Exception as error:
        print(f"\n[ERROR] {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
