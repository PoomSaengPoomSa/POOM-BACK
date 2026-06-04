import sys
import os
from sqlalchemy import text

# Add the parent directory (POOM-BACK) to python path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app.database import engine

def migrate():
    # 1. Alter table queries
    alter_queries = [
        "ALTER TABLE CUSTOMER_RELATIONSHIP DROP CONSTRAINT chk_wedding_date;",
        "ALTER TABLE CUSTOMER_RELATIONSHIP DROP COLUMN birthday;",
        "ALTER TABLE CUSTOMER_RELATIONSHIP DROP COLUMN job;",
        "ALTER TABLE CUSTOMER_RELATIONSHIP DROP COLUMN is_spouse;",
        "ALTER TABLE CUSTOMER_RELATIONSHIP DROP COLUMN wedding_date;",
        "ALTER TABLE CUSTOMER_RELATIONSHIP ADD COLUMN information TEXT NULL;",
        "ALTER TABLE CUSTOMER_RELATIONSHIP MODIFY COLUMN relationship VARCHAR(50) NOT NULL;"
    ]
    
    # 2. Clear old data (since schema has completely simplified)
    clear_query = "DELETE FROM CUSTOMER_RELATIONSHIP;"
    
    # 3. Insert newly structured dummy data
    insert_queries = """
    INSERT INTO CUSTOMER_RELATIONSHIP (c_id, relationship, information) VALUES
    (1001, '배우자', '김지훈 고객의 배우자로 미술관 큐레이터로 재직 중. 2010년 결혼하여 동반 자산 관리에 공동 관심이 많음.'),
    (1001, '직장동료', '함께 일하는 건축사 동료로, 주로 대형 프로젝트 협업을 진행함.'),
    (1001, '사업파트너', '시행사 대표로, 부동산 시행 부문의 중요한 비즈니스 파트너이자 거액 자금 운용 협조자임.'),
    (1001, '골프모임지인', '정기적인 서초구 골프 모임 멤버이며 현직 치과의사.'),
    (1001, '대학동기', '대학 동기인 현직 대학교수로, 학술 연구 및 다양한 외부 자문 활동을 공유함.'),
    (1002, '학부모지인', '교내 학부모 상담 등을 통해 알게 된 지역 학부모 지인으로 교육 정보 공유 중.'),
    (1002, '교직원동료', '같은 학교에 근무하는 초등 교사 동료로 정기적인 적금 계 개설.'),
    (1002, '요가학원친구', '함께 요가 센터에 다니는 사적으로 친밀한 디자이너 친구.'),
    (1002, '동네지인', '잠실 인근 아파트에 거주하는 이웃이자 전업주부로 친분이 깊음.'),
    (1002, '대학선배', '대학 교육학과 선배로 교육행정직 공무원으로 근무 중.'),
    (1003, '배우자', '이현우 고객의 전업주부 배우자로 가정 자산 안정을 최우선으로 생각하는 보수적 투자 선호 성향.'),
    (1003, '비즈니스클럽', '상공회의소 비즈니스 클럽에서 만난 타 제조업체 대표로 거액의 교류 진행.'),
    (1003, '고교동창', '오래된 고교 동창이자 현직 특허 전문 변리사로 법률적 이슈 상의 파트너.'),
    (1003, '업무협력사', '주요 부품 공급 물류망을 총괄하는 협력업체 임원으로 비즈니스 신뢰 관계.'),
    (1003, '테니스모임', '매주 주말 분당 테니스 클럽에서 운동을 함께하는 시중 금융사 임원 지인.'),
    (1004, '배우자', '최지영 고객의 배우자로 IT 기업의 수석 개발자로 근무 중이며 테크 핀 분야 관심도 높음.'),
    (1004, '마케팅학회지인', '대학 연합 광고 마케팅 학회 동기 출신의 현직 메이저 광고 기획사 과장.'),
    (1004, '독서모임', '매월 주말 정기적으로 진행하는 독서 클럽의 베스트셀러 소설가 작가 지인.'),
    (1004, '이전직장동료', '전 직장 마케팅 팀에서 호흡을 맞추었던 패션 브랜드 매니저 동료.'),
    (1004, '친자매', '최근 병원 정밀 진단 결과를 앞둔 친자매로 대학병원 수간호사로 근무 중.'),
    (1005, '배우자', '정재욱 고객의 배우자로 요식업 매장을 함께 공동 경영하며 세무 자금을 관리하고 있음.'),
    (1005, '식자재납품업체', '오랜 기간 안정적으로 신선 야채 및 식자재를 전담 수송해 온 청과물 유통 연계 사업자.'),
    (1005, '상가번영회장', '정재욱 고객의 매장이 입점한 상가 건물의 소유주이자 상가번영회 자문위원.'),
    (1005, '동네조기축구회', '주말 해운대 조기 축구회 회원으로 같이 운동하며 자영업 운영 애환을 나누는 지인.'),
    (1005, '장남', '해외 유학 및 요리 전문 교육을 준비 중인 가업 승계 1순위 대학교 2학년 자녀.');
    """

    with engine.begin() as conn:
        print("1. Altering CUSTOMER_RELATIONSHIP schema...")
        for query in alter_queries:
            try:
                conn.execute(text(query))
                print(f"[SUCCESS] {query}")
            except Exception as e:
                # 만약 이미 지워진 상태이거나 하면 무시하고 지나감
                print(f"[INFO] Failed or already applied: {query} (Error: {e})")
                
        print("\n2. Clearing old relationship data...")
        conn.execute(text(clear_query))
        
        print("\n3. Inserting simplified relationship dummy data...")
        conn.execute(text(insert_queries))
        print("[SUCCESS] All steps executed successfully!")

if __name__ == "__main__":
    migrate()
