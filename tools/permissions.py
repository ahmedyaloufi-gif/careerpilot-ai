# ── Permission Layer ─────────────────────────────────────────────────────────

def request_permissions(requested: list[str]) -> dict[str, bool]:
    """
    Asks user to approve access to their data before processing.
    Returns a dict of approved permissions.
    """
    print("\n🔐 CAREERPILOT AI — PERMISSION REQUEST")
    print("=" * 40)
    print("CareerPilot needs access to the following:")
    print()

    permissions = {}
    for item in requested:
        response = input(f"   Allow access to your {item}? (y/n): ").strip().lower()
        permissions[item] = response == 'y'
        status = "✅ Granted" if permissions[item] else "❌ Denied"
        print(f"   {status}")

    print()
    return permissions


def check_permission(permissions: dict, key: str) -> bool:
    """Check if a specific permission was granted."""
    return permissions.get(key, False)