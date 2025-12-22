DEPENDENCY_GRAPH = {
    "api": ["auth", "db"],
    "auth": ["db"],
    "db": ["cache", "storage"],
    "cache": ["storage"],
    "storage": []
}
