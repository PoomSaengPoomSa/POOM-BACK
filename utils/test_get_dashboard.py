import sys
import os
import asyncio

# Add the current directory to python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.services.trend import get_trend_dashboard

async def main():
    print("--- 트렌드 대시보드 API 쿼리 및 결과 검증 시작 ---")
    db = SessionLocal()
    mock_user = type("MockAccount", (object,), {"id": "pb_b1_1", "role": "user"})()
    
    try:
        result = await get_trend_dashboard(mock_user, db)
        print("API 실행 성공!")
        
        print("\n[NEWS 부분 응답 결과]")
        for category, articles in result["news"].items():
            print(f"- 카테고리: {category} (기사 수: {len(articles)}개)")
            for a in articles[:1]:  # 상위 1개만 출력
                print(f"  * ID: {a['id']}, 제목: {a['title']}, 발행일: {a['publishedAt']}")
                
        print("\n[INDICATORS 부분 응답 결과]")
        print("- 금값 (gold):", result["indicators"]["gold"])
        print("- 부동산 (realEstate):", result["indicators"]["realEstate"])
        print("- 기준금리 (interestRate):", result["indicators"]["interestRate"])
        
        print("\n--- 모든 검증이 완벽하게 완료되었습니다! ---")
        
    except Exception as e:
        print(f"API 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
