import sys
from pathlib import Path

# Thêm project root vào sys.path để import src.* hoạt động trong pytest
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
