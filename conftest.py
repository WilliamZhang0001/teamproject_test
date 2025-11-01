import importlib.util

collect_ignore = []

if importlib.util.find_spec("pandas") is None:
    collect_ignore.append("test_scenarios.py")

if importlib.util.find_spec("sqlalchemy") is None or importlib.util.find_spec("pymysql") is None:
    collect_ignore.append("tests/test_literature_integration.py")
