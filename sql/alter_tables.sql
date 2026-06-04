ALTER TABLE CUSTOMER 
ADD COLUMN grade VARCHAR(30),
ADD COLUMN llm_insight TEXT;
SET SQL_SAFE_UPDATES = 0;
UPDATE CUSTOMER
SET grade = CASE
    WHEN total_assets >= 5000000000 THEN 'VVIP'
    WHEN total_assets >= 2000000000 THEN 'VIP'
    ELSE '일반'
END;
UPDATE CUSTOMER
SET llm_insight = CASE grade
    WHEN 'VVIP' THEN '부동산 및 거액 투자 자산 위주의 포트폴리오를 보유하고 있으며, 세무/증여 및 프리미엄 투자 상품에 대한 사전 컨설팅 니즈가 매우 높을 것으로 분석됨.'
    WHEN 'VIP' THEN '안정적인 현금 흐름과 투자 자산을 보유 중이며, 절세 및 포트폴리오 다각화(해외 ETF, 채권 등)에 관심이 많을 것으로 예상됨.'
    ELSE '예적금 위주의 안정적인 자산 비중이 높으며, 청약, 적립식 펀드 및 생활 밀착형 금융 상품(신용카드, 소액 대출) 제안이 효과적일 것으로 분석됨.'
END;
-- 1. NOT NULL 제약조건 추가
ALTER TABLE CUSTOMER MODIFY COLUMN grade VARCHAR(30) NOT NULL;

-- 2. CHECK 제약조건 추가 (지정된 값만 들어오도록 강제)
ALTER TABLE CUSTOMER ADD CONSTRAINT chk_customer_grade CHECK (grade IN ('일반', 'VIP', 'VVIP'));



ALTER TABLE KPI
ADD COLUMN current_aum BIGINT,
ADD COLUMN current_non_interest BIGINT,
ADD COLUMN current_new_customer BIGINT,
ADD COLUMN recorded_date DATE;
UPDATE KPI
SET current_aum = aum,
    current_non_interest = non_interest,
    current_new_customer = new_customer,
    recorded_date = created_date;
ALTER TABLE KPI
MODIFY COLUMN current_aum BIGINT NOT NULL,
MODIFY COLUMN current_non_interest BIGINT NOT NULL,
MODIFY COLUMN current_new_customer BIGINT NOT NULL DEFAULT 0,
MODIFY COLUMN recorded_date DATE NOT NULL,
ADD CONSTRAINT chk_current_aum CHECK (current_aum >= 0),
ADD CONSTRAINT chk_current_non_interest CHECK (current_non_interest >= 0),
ADD CONSTRAINT chk_current_new_customer CHECK (current_new_customer >= 0);



ALTER TABLE PRODUCT 
ADD COLUMN season VARCHAR(20),
ADD COLUMN issuer VARCHAR(50),
ADD COLUMN features TEXT,
ADD COLUMN target_customer TEXT,
ADD COLUMN expected_return FLOAT,
ADD COLUMN return_type VARCHAR(30);
-- 1. 우리WON통장 (보통예금)
UPDATE PRODUCT 
SET season = '2026 상반기', issuer = '우리은행', features = '이체 및 자동화기기 수수료 무제한 면제', target_customer = '급여 소득자 및 주거래 고객', expected_return = 0.1, return_type = '기본이율'
WHERE name = '우리WON통장';

-- 2. WON플러스예금 (정기예금)
UPDATE PRODUCT 
SET season = '2026 상반기', issuer = '우리은행', features = '매월 이자가 원금에 더해지는 월복리 효과', target_customer = '안정적인 목돈 굴리기를 희망하는 고객', expected_return = 3.5, return_type = '고정금리'
WHERE name = 'WON플러스예금';

-- 3. 우리희망연금보험 (연금보험)
UPDATE PRODUCT 
SET season = '2026 상반기', issuer = '우리은행', features = '10년 유지 시 비과세 혜택 및 종신 연금 수령 가능', target_customer = '노후 자산 관리가 필요한 4050 세대', expected_return = 4.2, return_type = '변동공시이율'
WHERE name = '우리희망연금보험';

-- 4. 우리주택담보대출 (대출)
UPDATE PRODUCT 
SET season = '2026 상반기', issuer = '우리은행', features = '친환경 주택 매입 시 최대 1.2% 우대금리 적용', target_customer = '내 집 마련 및 생활안정자금 필요 고객', expected_return = 4.5, return_type = '대출금리'
WHERE name = '우리주택담보대출';

-- 5. 우리글로벌투자신탁 (투자상품)
UPDATE PRODUCT 
SET season = '2026 상반기', issuer = '우리자산운용', features = '미국 빅테크 및 우량 배당주에 집중 투자하여 알파 수익 창출', target_customer = '공격투자형 및 글로벌 자산 배분 선호 고객', expected_return = 8.5, return_type = '목표수익률'
WHERE name = '우리글로벌투자신탁';

-- 6. 직장인우대적금 (예적금)
UPDATE PRODUCT 
SET season = '2026 상반기', issuer = '우리은행', features = '급여 이체 및 당행 신용카드 결제 시 특별 우대금리 제공', target_customer = '체계적인 목돈 마련을 계획 중인 직장인', expected_return = 4.0, return_type = '고정금리'
WHERE name = '직장인우대적금';

-- 7. 신용대출-플러스 (대출)
UPDATE PRODUCT 
SET season = '2026 상반기', issuer = '우리은행', features = '서류 제출 없이 모바일로 즉시 실행 가능한 넉넉한 한도', target_customer = '긴급 자금 융통이 필요한 고신용/VIP 고객', expected_return = 5.2, return_type = '대출금리'
WHERE name = '신용대출-플러스';

ALTER TABLE PRODUCT 
MODIFY COLUMN season VARCHAR(20) NOT NULL,
MODIFY COLUMN issuer VARCHAR(50) NOT NULL,
MODIFY COLUMN features TEXT NOT NULL,
MODIFY COLUMN target_customer TEXT NOT NULL,
MODIFY COLUMN expected_return FLOAT NOT NULL,
MODIFY COLUMN return_type VARCHAR(30) NOT NULL;



ALTER TABLE AI_TODO
ADD COLUMN c_id INT;
-- user1 고객 관련 row
UPDATE AI_TODO SET c_id = 1001 WHERE u_id = 'user1' AND title LIKE '%1001%';
UPDATE AI_TODO SET c_id = 1002 WHERE u_id = 'user1' AND title LIKE '%1002%';
UPDATE AI_TODO SET c_id = 1003 WHERE u_id = 'user1' AND title LIKE '%1003%';
UPDATE AI_TODO SET c_id = 1004 WHERE u_id = 'user1' AND title LIKE '%1004%';
UPDATE AI_TODO SET c_id = 1005 WHERE u_id = 'user1' AND title LIKE '%1005%';

-- user2 고객 관련 row
UPDATE AI_TODO SET c_id = 1043 WHERE u_id = 'user2' AND title LIKE '%1043%';
UPDATE AI_TODO SET c_id = 1044 WHERE u_id = 'user2' AND title LIKE '%1044%';
UPDATE AI_TODO SET c_id = 1045 WHERE u_id = 'user2' AND title LIKE '%1045%';
UPDATE AI_TODO SET c_id = 1046 WHERE u_id = 'user2' AND title LIKE '%1046%';
UPDATE AI_TODO SET c_id = 1047 WHERE u_id = 'user2' AND title LIKE '%1047%';
UPDATE AI_TODO SET c_id = 1048 WHERE u_id = 'user2' AND title LIKE '%1048%';
UPDATE AI_TODO SET c_id = 1049 WHERE u_id = 'user2' AND title LIKE '%1049%';
UPDATE AI_TODO SET c_id = 1050 WHERE u_id = 'user2' AND title LIKE '%1050%';

-- KPI 기반 / 신규 상품 분석 카테고리는 c_id = NULL 유지 (그대로 둠)

ALTER TABLE AI_TODO
ADD CONSTRAINT fk_aitodo_customer
FOREIGN KEY (c_id) REFERENCES CUSTOMER(c_id);

select * from pb_schedule;

-- CUSTOMER 테이블에 update_time 및 analysis_time 추가
ALTER TABLE CUSTOMER 
ADD COLUMN update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
ADD COLUMN analysis_time DATETIME NULL;

-- CUSTOMER_RELATIONSHIP 테이블 구조 변경 (기존 열/제약조건 제거 및 TEXT형 information 추가)
ALTER TABLE CUSTOMER_RELATIONSHIP DROP CONSTRAINT chk_wedding_date;
ALTER TABLE CUSTOMER_RELATIONSHIP 
DROP COLUMN birthday,
DROP COLUMN job,
DROP COLUMN is_spouse,
DROP COLUMN wedding_date,
ADD COLUMN information TEXT;
ALTER TABLE CUSTOMER_RELATIONSHIP MODIFY COLUMN relationship VARCHAR(50) NOT NULL;

-- CHURN_LEVEL 테이블에 explain_reason(판정 상세 설명) TEXT 컬럼 추가
ALTER TABLE CHURN_LEVEL ADD COLUMN explain_reason TEXT AFTER reason;