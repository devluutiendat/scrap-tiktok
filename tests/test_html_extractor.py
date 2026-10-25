"""
Unit tests cho HtmlExtractor.

Mọi test đều mock page.content() với HTML tĩnh — không gọi browser thật.
Chạy: pytest tests/test_html_extractor.py -v
"""

import asyncio
import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.extractors.html_extractor import FieldRule, HtmlExtractor, PaginationConfig


# ---------------------------------------------------------------------------
# HTML fixtures
# ---------------------------------------------------------------------------

SIMPLE_HTML = """
<html><body>
  <ul id="job-list">
    <li class="job-card">
      <h3 class="title"><a href="/job/1">Python Developer</a></h3>
      <span class="salary">20-30 triệu</span>
      <span class="company">ABC Corp</span>
    </li>
    <li class="job-card">
      <h3 class="title"><a href="/job/2">Data Engineer</a></h3>
      <span class="salary">25-35 triệu</span>
      <span class="company">XYZ Ltd</span>
    </li>
    <li class="job-card">
      <h3 class="title"><a href="/job/3">Backend Dev</a></h3>
      <span class="salary">15-20 triệu</span>
      <span class="company">Startup VN</span>
    </li>
  </ul>
</body></html>
"""

DUPLICATE_HTML = """
<html><body>
  <ul>
    <li class="job-card">
      <h3 class="title"><a href="/job/1">Python Developer</a></h3>
      <span class="salary">20-30 triệu</span>
    </li>
    <li class="job-card">
      <h3 class="title"><a href="/job/1">Python Developer</a></h3>
      <span class="salary">20-30 triệu</span>
    </li>
  </ul>
</body></html>
"""

MISSING_FIELD_HTML = """
<html><body>
  <ul>
    <li class="job-card">
      <h3 class="title"><a href="/job/99">Only Title</a></h3>
      <!-- salary bị thiếu -->
    </li>
  </ul>
</body></html>
"""

MULTIPLE_TAGS_HTML = """
<html><body>
  <div class="news-item">
    <span class="tag">Python</span>
    <span class="tag">Backend</span>
    <span class="tag">Remote</span>
  </div>
</body></html>
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_extractor(html: str, tmp_path: Path, **kwargs) -> HtmlExtractor:
    """Tạo HtmlExtractor với page mock trả về html cố định."""
    page = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.content = AsyncMock(return_value=html)

    return HtmlExtractor(
        page=page,
        item_selector="li.job-card",
        field_rules=[
            FieldRule("title", "h3.title a"),
            FieldRule("url", "h3.title a", attribute="href"),
            FieldRule("salary", "span.salary"),
            FieldRule("company", "span.company"),
        ],
        output_file=str(tmp_path / "output.json"),
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_extract_returns_correct_count(tmp_path: Path):
    """extract_current_page() phải trả về đúng số bản ghi tìm thấy."""
    extractor = make_extractor(SIMPLE_HTML, tmp_path)
    count = await extractor.extract_current_page()
    assert count == 3


@pytest.mark.asyncio
async def test_extract_field_values_correct(tmp_path: Path):
    """Các field phải được trích xuất đúng giá trị."""
    extractor = make_extractor(SIMPLE_HTML, tmp_path)
    await extractor.extract_current_page()

    first = extractor.collected_data[0]
    assert first["title"] == "Python Developer"
    assert first["url"] == "/job/1"
    assert first["salary"] == "20-30 triệu"
    assert first["company"] == "ABC Corp"


@pytest.mark.asyncio
async def test_dedup_by_unique_id_key(tmp_path: Path):
    """Bản ghi trùng unique_id_key phải bị loại bỏ."""
    extractor = make_extractor(DUPLICATE_HTML, tmp_path, unique_id_key="url")
    count = await extractor.extract_current_page()
    # 2 item trong HTML nhưng chỉ 1 url duy nhất -> chỉ 1 bản ghi
    assert count == 1
    assert len(extractor.collected_data) == 1


@pytest.mark.asyncio
async def test_missing_field_returns_none(tmp_path: Path):
    """Field không tìm thấy trong HTML phải trả về None, không raise exception."""
    extractor = make_extractor(MISSING_FIELD_HTML, tmp_path)
    count = await extractor.extract_current_page()
    assert count == 1
    assert extractor.collected_data[0]["salary"] is None
    assert extractor.collected_data[0]["company"] is None


@pytest.mark.asyncio
async def test_multiple_field_rule(tmp_path: Path):
    """FieldRule với multiple=True phải trả về list."""
    page = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.content = AsyncMock(return_value=MULTIPLE_TAGS_HTML)

    extractor = HtmlExtractor(
        page=page,
        item_selector="div.news-item",
        field_rules=[
            FieldRule("tags", "span.tag", multiple=True),
        ],
        output_file=str(tmp_path / "output.json"),
    )
    await extractor.extract_current_page()
    assert extractor.collected_data[0]["tags"] == ["Python", "Backend", "Remote"]


@pytest.mark.asyncio
async def test_transform_applied(tmp_path: Path):
    """FieldRule.transform phải được gọi với giá trị thô."""
    extractor = make_extractor(
        SIMPLE_HTML,
        tmp_path,
        # Thay FieldRule salary với transform upper()
    )
    # Ghi đè field_rules để có transform
    extractor.field_rules = [
        FieldRule("salary", "span.salary", transform=str.upper),
    ]
    await extractor.extract_current_page()
    assert extractor.collected_data[0]["salary"] == "20-30 TRIỆU"


@pytest.mark.asyncio
async def test_save_to_json_creates_valid_file(tmp_path: Path):
    """save_to_json() phải tạo file JSON hợp lệ với đúng nội dung."""
    extractor = make_extractor(SIMPLE_HTML, tmp_path)
    await extractor.extract_current_page()
    extractor.save_to_json()

    output_file = tmp_path / "output.json"
    assert output_file.exists()

    with open(output_file, encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert len(data) == 3
    assert data[0]["title"] == "Python Developer"


@pytest.mark.asyncio
async def test_no_items_found_returns_zero(tmp_path: Path):
    """Nếu selector không khớp item nào, trả về 0 và collected_data rỗng."""
    empty_html = "<html><body><p>Không có gì cả</p></body></html>"
    extractor = make_extractor(empty_html, tmp_path)
    count = await extractor.extract_current_page()
    assert count == 0
    assert extractor.collected_data == []
