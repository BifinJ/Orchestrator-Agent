DEPENDENCY_GRAPH = {
    "api": ["auth", "cache", "db"],
    "auth": ["db"],
    "db": ["storage"],
    "cache": ["storage"],
    "storage": [],
    "ec2": ["api", "db", "cache"]
}
