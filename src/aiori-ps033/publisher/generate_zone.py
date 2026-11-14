
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
CATALOGUE = ROOT / "publisher" / "services.yaml"
ZONE_FILE = ROOT / "zone" / "db.diag.lab.test"


def generate_zone():
    with open(CATALOGUE, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    domain = config["domain"]
    serial = config["zone_serial"]

    lines = [
        "$TTL 3600",
        "",
        f"@ IN SOA ns1.{domain}. admin.{domain}. (",
        f"    {serial}",
        "    3600",
        "    1800",
        "    604800",
        "    86400",
        ")",
        "",
        f"@ IN NS ns1.{domain}.",
        "",
        "ns1 IN A 172.20.0.10",
        "",
        "; Diagnostic service records",
        ""
    ]

    for service in config["services"]:
        name = service["name"]
        hostname = service["hostname"]
        ip = service["ip"]
        discovery = service["discovery_name"]
        port = service["port"]
        protocol = service["protocol"]
        version = service["version"]
        capability = service["capability"]
        auth_scheme = service["auth_scheme"]

        lines.append(f"{name} IN A {ip}")
        lines.append(
            f'{discovery}. IN SVCB 1 {hostname}. '
            f'alpn="{protocol}" port={port}'
        )

        metadata = (
            f"version={version}; "
            f"capability={capability}; "
            f"auth={auth_scheme}"
        )

        lines.append(
            f'{discovery}. IN TXT "{metadata}"'
        )

        lines.append("")

    ZONE_FILE.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8"
    )

    print(f"Zone file generated successfully: {ZONE_FILE}")


if __name__ == "__main__":
    generate_zone()
