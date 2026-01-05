import re

ERROR_KEYWORDS = ["error","exception","fatal","traceback","failure","critical"]
WARNING_KEYWORDS = ["warning","warn","timeout","retry","slow query"]

def classify_log(message: str):
    """
    Classify log severity from raw log string.
    Returns category or None.
    """
    if not isinstance(message, str):
        return None

    msg = message.lower()

    if "[error]" in msg:
        return "error"
    if "[warn]" in msg or "[warning]" in msg:
        return "warning"

    return None



import re

def detect_http_status(message: str):
    """
    Detect HTTP status codes from raw log string.
    Returns status code or None.
    """
    if not isinstance(message, str):
        return None

    match = re.search(r"\b(4\d{2}|5\d{2})\b", message)
    if match:
        return int(match.group(1))

    return None
