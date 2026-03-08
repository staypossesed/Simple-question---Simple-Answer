"""
Debug script — 10 тестов для диагностики RAG App
Запуск: python debug_tests.py
"""

import os
import sys
import subprocess

def test(name: str, ok: bool, detail: str = ""):
    status = "✅ PASS" if ok else "❌ FAIL"
    print(f"{status} | {name}")
    if detail:
        print(f"       └─ {detail}")
    return ok

results = []

# === Test 1: Python version ===
py_ver = sys.version_info
ok = py_ver >= (3, 10)
results.append(test("1. Python 3.10+", ok, f"Current: {py_ver.major}.{py_ver.minor}.{py_ver.micro}"))

# === Test 2: Working directory ===
cwd = os.getcwd()
expected = "portfolio-rag-app"
ok = expected in cwd or os.path.basename(cwd) == expected
results.append(test("2. Working dir (portfolio-rag-app)", ok, f"CWD: {cwd}"))

# === Test 3: .env exists ===
env_path = os.path.join(os.getcwd(), ".env")
ok = os.path.isfile(env_path)
results.append(test("3. .env file exists", ok, env_path if ok else "Create .env with OPENAI_API_KEY"))

# === Test 4: OPENAI_API_KEY in .env ===
key = ""
if ok:
    with open(env_path) as f:
        for line in f:
            if line.strip().startswith("OPENAI_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"\'')
                break
ok = bool(key) and len(key) > 20 and (key.startswith("sk-") or key != "sk-your-key-here")
results.append(test("4. OPENAI_API_KEY set & valid", ok, f"Length: {len(key)}" if key else "Missing or placeholder"))

# === Test 5: app.yaml exists ===
yaml_path = os.path.join(os.getcwd(), "app.yaml")
ok = os.path.isfile(yaml_path)
results.append(test("5. app.yaml exists", ok, yaml_path))

# === Test 6: data/ folder exists ===
data_path = os.path.join(os.getcwd(), "data")
ok = os.path.isdir(data_path)
files = os.listdir(data_path) if ok else []
results.append(test("6. data/ folder exists", ok, f"Files: {len(files)}" if ok else ""))

# === Test 7: pathway import ===
try:
    import pathway as pw
    ok = True
    results.append(test("7. pathway import", ok, f"Pathway {getattr(pw, '__version__', '?')}"))
except Exception as e:
    results.append(test("7. pathway import", False, str(e)))

# === Test 8: Load app.yaml via Pathway ===
if results[6]:  # if pathway imported
    try:
        with open(yaml_path) as f:
            config = pw.load_yaml(f)
        ok = "question_answerer" in config or "document_store" in config
        results.append(test("8. app.yaml loads (Pathway)", ok, "Config keys OK" if ok else "Invalid config"))
    except Exception as e:
        results.append(test("8. app.yaml loads (Pathway)", False, str(e)))
else:
    results.append(test("8. app.yaml loads (Pathway)", False, "Skipped (pathway not imported)"))

# === Test 9: OpenAI API reachable ===
if results[3]:  # if key exists
    try:
        import urllib.request
        req = urllib.request.Request(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {key}"}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            r.read()
        ok = True
        results.append(test("9. OpenAI API reachable", ok, "API key works"))
    except Exception as e:
        results.append(test("9. OpenAI API reachable", False, str(e)[:80]))
else:
    results.append(test("9. OpenAI API reachable", False, "Skipped (no key)"))

# === Test 10: App can start (dry run / import) ===
try:
    from dotenv import load_dotenv
    load_dotenv()
    with open(yaml_path) as f:
        cfg = pw.load_yaml(f)
    from pydantic import BaseModel, InstanceOf
    from pathway.xpacks.llm.question_answering import SummaryQuestionAnswerer
    # Don't actually run pw.run(), just check we can parse config
    ok = "question_answerer" in cfg
    results.append(test("10. App config parseable", ok, "SummaryQuestionAnswerer + YAML OK"))
except Exception as e:
    results.append(test("10. App config parseable", False, str(e)[:80]))

# === Summary ===
print("\n" + "=" * 50)
passed = sum(1 for r in results if r)
print(f"RESULT: {passed}/10 tests passed")
if passed < 10:
    print("\nFix the FAIL items above, then run again.")
else:
    print("\nAll checks passed. Try: python app.py")
