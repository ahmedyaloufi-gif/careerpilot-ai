import re

# ── Personal Data Masking ────────────────────────────────────────────────────

def mask_personal_data(text: str) -> tuple[str, dict]:
    """
    Masks personal data before sending to AI agents.
    Returns masked text and a dictionary of what was masked.
    """
    masked = text
    vault = {}  # stores original values

    # Mask email addresses
    emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    for i, email in enumerate(emails):
        placeholder = f"[EMAIL_{i+1}]"
        vault[placeholder] = email
        masked = masked.replace(email, placeholder)

    # Mask phone numbers (various formats)
    phones = re.findall(
        r'(\+?\d{1,3}[\s\-]?)?\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4}',
        text
    )
    for i, phone in enumerate(phones):
        phone = phone.strip()
        if phone and len(phone) >= 7:
            placeholder = f"[PHONE_{i+1}]"
            vault[placeholder] = phone
            masked = masked.replace(phone, placeholder)

    # Mask physical addresses (basic patterns)
    addresses = re.findall(
        r'\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)[\w\s,]*',
        text, re.IGNORECASE
    )
    for i, address in enumerate(addresses):
        placeholder = f"[ADDRESS_{i+1}]"
        vault[placeholder] = address
        masked = masked.replace(address, placeholder)

    # Mask national ID / passport numbers
    ids = re.findall(r'\b[A-Z]{1,2}\d{6,9}\b', text)
    for i, id_num in enumerate(ids):
        placeholder = f"[ID_{i+1}]"
        vault[placeholder] = id_num
        masked = masked.replace(id_num, placeholder)

    return masked, vault


def unmask_personal_data(text: str, vault: dict) -> str:
    """
    Restores original personal data from vault after AI processing.
    """
    restored = text
    for placeholder, original in vault.items():
        restored = restored.replace(placeholder, original)
    return restored


def get_security_report(vault: dict) -> str:
    """
    Returns a summary of what data was protected.
    """
    if not vault:
        return "✅ No sensitive personal data detected."

    report = "🔒 SECURITY LAYER ACTIVE — Protected Data:\n"
    for placeholder, original in vault.items():
        # Show only first 3 chars of sensitive data
        preview = original[:3] + "*" * (len(original) - 3)
        report += f"   {placeholder} → {preview}\n"
    return report