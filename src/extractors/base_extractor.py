

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class BaseExtractor:

    output_path: Path
    collected_data: List[Dict[str, Any]]

    def save_to_json(self) -> None:

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, mode="w", encoding="utf-8") as f:
            json.dump(self.collected_data, f, ensure_ascii=False, indent=2)
        logger.info(
            "Đã lưu %d bản ghi -> %s", len(self.collected_data), self.output_path
        )


async def _demo() -> None:
    """Demo nhanh: python base_extractor.py"""
    import tempfile, os

    class DummyExtractor(BaseExtractor):
        def __init__(self) -> None:
            self.output_path = Path(tempfile.gettempdir()) / "demo_output.json"
            self.collected_data = [{"id": 1, "title": "Test"}]

    ext = DummyExtractor()
    ext.save_to_json()
    assert ext.output_path.exists(), "File không được tạo!"
    os.unlink(ext.output_path)
    print("✅ Demo hoàn thành!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(_demo())
