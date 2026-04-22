from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings


def main() -> None:
    print("Phase 1 scaffold ready.")
    print("Next step: implement ingestion and indexing in Phase 2.")
    print(f"Data directory: {settings.data_dir}")


if __name__ == "__main__":
    main()
