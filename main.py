from src.services.kalodata import scrape_all_creators
from src.services.search import search_categories
import sys
import asyncio
async def main():
    # tìm kiếm danh mục 
    print(" CÔNG CỤ TÌM KIẾM DANH MỤC TIKTOK SHOP")
    if len(sys.argv) > 1:
        keyword = " ".join(sys.argv[1:])
        results = search_categories(keyword, as_dict=True)
        print(f"Tìm thấy {len(results)} kết quả phù hợp với từ khóa '{keyword}':\n")
        for i, row in enumerate(results, 1):
            print(f"{i}. [ID: {row.get('TikTok Category ID')}]")
            print(f"   - Tên danh mục: {row.get('Tên danh mục')}")
            print(f"   - Danh mục cha: {row.get('Danh mục cha')}")
            print(f"   - Là danh mục lá: {row.get('Là danh mục lá')}")
            print("-" * 50)
        
    print("\nNhập STT danh mục muốn cào (cách nhau bằng dấu phẩy, ví dụ: 1,3).")
    print("Để trống và nhấn Enter → lấy tất cả danh mục lá (Là danh mục lá = True):")
    raw_input = input("Chọn: ").strip()

    if raw_input:
        try:
            chosen_indices = [int(x.strip()) - 1 for x in raw_input.split(",")]
            selected = [results[i] for i in chosen_indices if 0 <= i < len(results)]
        except (ValueError, IndexError):
            print("[WARN] Lựa chọn không hợp lệ, lấy tất cả danh mục lá.")
            selected = [r for r in results if r.get("Là danh mục lá")]
    else:
        selected = [r for r in results if r.get("Là danh mục lá")]
        if not selected:
            selected = results 
    print(selected)
    category_ids = [item.get("TikTok Category ID") for item in selected if item.get("TikTok Category ID")]

    print(f"\nĐang cào {len(category_ids)} danh mục: {[item.get('Tên danh mục') for item in selected]}")
    
    #lấy danh sách các creator theo danh mục 
    scrape_all_creators(category_ids)
if __name__ == "__main__":
    asyncio.run(main())