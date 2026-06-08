import sys
import csv
from datetime import datetime
from sqlalchemy.orm import Session

# 프로젝트 모듈 임포트를 위해 sys.path에 추가
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.account import Account, PbUser
from app.models.branch import Branch
from app.utils.security import hash_password

CSV_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "accounts_seed.csv")

# 10개 지점의 현실적인 데이터 정의
REALISTIC_BRANCHES = {
    1: {"name": "강남금융센터지점", "region": "서울", "b_phone": "02-555-0101", "address": "서울특별시 강남구 테헤란로 123"},
    2: {"name": "여의도영업부지점", "region": "서울", "b_phone": "02-789-0202", "address": "서울특별시 영등포구 국제금융로 24"},
    3: {"name": "명동중앙지점", "region": "서울", "b_phone": "02-345-0303", "address": "서울특별시 중구 남대문로 84"},
    4: {"name": "부산서면지점", "region": "부산", "b_phone": "051-808-0404", "address": "부산광역시 부산진구 중앙대로 700"},
    5: {"name": "대구범어지점", "region": "대구", "b_phone": "053-744-0505", "address": "대구광역시 수성구 달구벌대로 2400"},
    6: {"name": "광주상무지점", "region": "광주", "b_phone": "062-385-0606", "address": "광주광역시 서구 상무중앙로 80"},
    7: {"name": "대전둔산지점", "region": "대전", "b_phone": "042-482-0707", "address": "대전광역시 서구 둔산로 100"},
    8: {"name": "울산금융센터지점", "region": "울산", "b_phone": "052-260-0808", "address": "울산광역시 남구 삼산로 150"},
    9: {"name": "인천송도지점", "region": "인천", "b_phone": "032-831-0909", "address": "인천광역시 연수구 송도국제대로 123"},
    10: {"name": "분당판교지점", "region": "경기", "b_phone": "031-707-1010", "address": "경기도 성남시 분당구 판교역로 230"}
}

def ensure_branches_exist(db: Session, branch_ids: set):
    """
    필요한 branch_id(1~10)가 DB에 없다면 자동으로 생성하고,
    이미 있다면 현실적인 지점 정보(명칭, 지역, 전화번호, 주소)로 업데이트(Update)합니다.
    """
    try:
        # 현재 DB에 존재하는 브랜치들 조회
        existing_branches = {b.b_id: b for b in db.query(Branch).filter(Branch.b_id.in_(branch_ids)).all()}
        
        created_count = 0
        updated_count = 0

        for b_id in branch_ids:
            info = REALISTIC_BRANCHES.get(b_id, {
                "name": f"임시 지점 {b_id}",
                "region": "서울",
                "b_phone": "02-1234-5678",
                "address": f"서울시 어딘가 지점 {b_id}"
            })
            
            if b_id not in existing_branches:
                # 1. 존재하지 않는 경우 생성
                new_branch = Branch(
                    b_id=b_id,
                    name=info["name"],
                    region=info["region"],
                    b_phone=info["b_phone"],
                    address=info["address"]
                )
                db.add(new_branch)
                created_count += 1
                print(f"새로운 지점 등록: {info['name']} (ID: {b_id})")
            else:
                # 2. 존재하는 경우 현실적인 정보로 업데이트
                branch = existing_branches[b_id]
                # 변경 사항이 있을 때만 수정 및 커밋 유도
                if (branch.name != info["name"] or 
                    branch.region != info["region"] or 
                    branch.b_phone != info["b_phone"] or 
                    branch.address != info["address"]):
                    
                    branch.name = info["name"]
                    branch.region = info["region"]
                    branch.b_phone = info["b_phone"]
                    branch.address = info["address"]
                    updated_count += 1
                    print(f"지점 정보 업데이트: {info['name']} (ID: {b_id})")

        db.commit()
        
        if created_count > 0 or updated_count > 0:
            print(f"지점 반영 결과 - 신규 등록: {created_count}개, 정보 업데이트: {updated_count}개")
        else:
            print("모든 지점 정보가 이미 최신 상태입니다.")
            
    except Exception as e:
        db.rollback()
        print(f"브랜치 사전 등록/업데이트 중 오류 발생: {e}")
        raise e

def seed_accounts_from_csv():
    """
    data/accounts_seed.csv 파일로부터 데이터를 읽어와 
    비밀번호를 해싱하고 DB에 적재합니다. (지점 정보는 항상 동기화/업데이트)
    """
    if not os.path.exists(CSV_FILE_PATH):
        print(f"오류: CSV 파일을 찾을 수 없습니다. 경로를 확인해주세요: {CSV_FILE_PATH}")
        return

    db: Session = SessionLocal()
    print(f"CSV 파일 읽는 중: {CSV_FILE_PATH}")

    try:
        # CSV 내용 임시 로드 및 branch_id 추출
        rows = []
        required_branch_ids = set()
        with open(CSV_FILE_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
                required_branch_ids.add(int(row['branch']))

        # 1. 지점 정보 확인 및 강제 업데이트
        ensure_branches_exist(db, required_branch_ids)

        # 2. 이미 존재하는 계정 ID 조회
        existing_ids = {row[0] for row in db.query(Account.id).all()}
        
        new_accounts = []
        new_users = []
        skipped_count = 0
        added_count = 0

        for row in rows:
            user_id = row['id']
            
            # 중복 ID 방지
            if user_id in existing_ids:
                skipped_count += 1
                continue
            
            # 비밀번호 해싱
            plain_password = row['password']
            hashed_pwd = hash_password(plain_password)
            
            # 1. Account 객체 생성
            account = Account(
                id=user_id,
                password=hashed_pwd,
                role=row['role']
            )
            new_accounts.append(account)
            
            # 2. PbUser 객체 생성
            # 날짜 포맷 변환 (YYYY-MM-DD -> date)
            start_date = datetime.strptime(row['start_date'], "%Y-%m-%d").date()
            birth_date = datetime.strptime(row['birth_date'], "%Y-%m-%d").date()
            
            pb_user = PbUser(
                u_id=user_id,
                name=row['name'],
                email=row['email'],
                number=row['number'],
                branch=int(row['branch']),
                status=row['status'],
                position=row['position'],
                start_date=start_date,
                birth_date=birth_date
            )
            new_users.append(pb_user)
            added_count += 1

        if added_count > 0:
            # Account 먼저 삽입 후 커밋 (외래 키 제약 조건 만족을 위함)
            db.add_all(new_accounts)
            db.commit()
            
            # PbUser 삽입 후 커밋
            db.add_all(new_users)
            db.commit()
            print(f"성공적으로 {added_count}개의 계정을 추가했습니다.")
        else:
            print("추가할 새로운 계정이 없습니다.")

        if skipped_count > 0:
            print(f"주의: 이미 존재하는 ID {skipped_count}개는 건너뛰었습니다.")
            
    except Exception as e:
        db.rollback()
        print(f"데이터 삽입 중 오류 발생: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_accounts_from_csv()
