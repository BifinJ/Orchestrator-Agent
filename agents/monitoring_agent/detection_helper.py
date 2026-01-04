import re

ERROR_KEYWORDS = ["error","exception","fatal","traceback","failure","critical"]
WARNING_KEYWORDS = ["warning","warn","timeout","retry","slow query"]

def classify_log(message: str):
    m = message.lower()

    if any(k in m for k in ERROR_KEYWORDS):
        return "log_error"

    if any(k in m for k in WARNING_KEYWORDS):
        return "log_warning"

    return None


def detect_http_status(message: str):
    match = re.search(r"\b(4\d{2}|5\d{2})\b", message)
    return match.group(1) if match else None
