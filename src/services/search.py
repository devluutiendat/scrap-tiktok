import sys
from pathlib import Path
from typing import List, Dict, Any, Union
import pandas as pd
from src.utils.logger import get_logger

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

logger = get_logger(__name__)

# danh sách này được lấy từ api của tiktokshop partner center
# https://partner.tiktokshop.com/docv2/page/get-categories-202309#Back%20To%20Top


DEFAULT_EXCEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "storage"
    / "TikTok_Shop_Category.xlsx"
)
_CACHED_DF: Union[pd.DataFrame, None] = None


def load_category_data(file_path: Union[str, Path] = DEFAULT_EXCEL_PATH, reload: bool = False) -> pd.DataFrame:
    global _CACHED_DF
    path = Path(file_path)
    if not path.exists():
        logger.error("Không tìm thấy file Excel tại: %s", path)
        raise FileNotFoundError(f"Không tìm thấy file Excel tại: {path}")

    if _CACHED_DF is None or reload:
        logger.debug("Đang load category data từ %s", path)
        _CACHED_DF = pd.read_excel(path)
        logger.info("Load xong category data: %d dòng", len(_CACHED_DF))

    return _CACHED_DF


def search_categories(
    x: str,
    file_path: Union[str, Path] = DEFAULT_EXCEL_PATH,
    case_sensitive: bool = False,
    as_dict: bool = True
) -> Union[List[Dict[str, Any]], pd.DataFrame]:
    if not x or not str(x).strip():
        return [] if as_dict else pd.DataFrame()

    query = str(x).strip()
    df = load_category_data(file_path)

    category_name_series = df["Tên danh mục"].fillna("").astype(str)
    parent_category_series = df["Danh mục cha"].fillna("").astype(str)

    mask = (
        category_name_series.str.contains(query, case=case_sensitive, regex=False)
        | parent_category_series.str.contains(query, case=case_sensitive, regex=False)
    )

    result_df = df[mask].copy()

    leaf_col = "Là danh mục lá"
    if leaf_col in result_df.columns and not result_df.empty:
        sort_key = result_df[leaf_col].apply(
            lambda v: 0 if (v is False or str(v).strip().lower() in ("false", "0")) else 1
        )
        result_df = result_df.iloc[sort_key.argsort(kind="stable")].copy()

    if as_dict:
        records = result_df.to_dict(orient="records")
        for row in records:
            for k, v in row.items():
                if pd.isna(v):
                    row[k] = None
                elif isinstance(v, pd.Timestamp):
                    row[k] = str(v)
        logger.debug("search_categories('%s') -> %d kết quả", x, len(records))
        return records

    logger.debug("search_categories('%s') -> %d kết quả (DataFrame)", x, len(result_df))
    return result_df
