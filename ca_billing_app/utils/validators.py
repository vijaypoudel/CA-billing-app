import re

GST_REGEX = r"^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"

def validate_gstin(gstin):
    if not gstin:
        return False
    gstin = gstin.strip().upper()
    return bool(re.match(GST_REGEX, gstin))
