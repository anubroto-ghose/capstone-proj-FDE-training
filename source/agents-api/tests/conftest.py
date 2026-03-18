import sys
from pathlib import Path
from dotenv import load_dotenv

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

# Load test-specific env first (without overriding already-exported env vars).
env_tests = SERVICE_ROOT / ".env.tests"
if env_tests.exists():
    load_dotenv(env_tests, override=False)
