"""OpenAPI şemasını dosyaya yazar (frontend tip üretimi için; sunucu çalıştırmaya gerek yok).

Kullanım: uv run python -m scripts.export_openapi ../frontend/openapi.json
"""

import json
import sys
from pathlib import Path

from app.main import create_app


def main() -> None:
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "openapi.json")
    schema = create_app().openapi()
    target.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"OpenAPI şeması yazıldı: {target}")


if __name__ == "__main__":
    main()
