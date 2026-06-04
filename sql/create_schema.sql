CREATE TABLE ACCOUNT (
    id VARCHAR(50) PRIMARY KEY,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(30) DEFAULT 'user' CHECK (role IN ('user', 'admin'))
);

CREATE TABLE PB_USER (
    u_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    email VARCHAR(50) NOT NULL UNIQUE,
    number VARCHAR(20) NOT NULL,
    branch INT NOT NULL,
    status VARCHAR(20) DEFAULT '재직' CHECK (status IN ('재직', '휴직', '퇴사', '발령대기')),
    position VARCHAR(30) DEFAULT 'PB' CHECK (position IN ('PB', '팀장', '지점장')),
    profile BLOB,
    start_date DATE NOT NULL,
    birth_date DATE NOT NULL,
    FOREIGN KEY (u_id) REFERENCES ACCOUNT(id),
    FOREIGN KEY (branch) REFERENCES BRANCH(b_id)
);

DROP TABLE BRANCH;
CREATE TABLE BRANCH (
    b_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    region VARCHAR(50) NOT NULL,
    b_phone VARCHAR(20) NOT NULL,
    address VARCHAR(255) NOT NULL
);

CREATE TABLE KPI (
    kpi_id INT AUTO_INCREMENT PRIMARY KEY,
    aum BIGINT NOT NULL CHECK (aum >= 0),
    non_interest BIGINT NOT NULL CHECK (non_interest >= 0),
    new_customer BIGINT NOT NULL DEFAULT 0 CHECK (new_customer >= 0),
    kpi_type VARCHAR(20) NOT NULL CHECK (kpi_type IN ('PB', 'BRANCH')),
    u_id VARCHAR(50), 
    b_id INT,         
    created_date DATE DEFAULT (CURRENT_DATE),
    target_aum BIGINT NOT NULL CHECK (target_aum >= 0),
    target_non_interest BIGINT NOT NULL CHECK (target_non_interest >= 0),
    target_new_customer BIGINT NOT NULL DEFAULT 0 CHECK (target_new_customer >= 0),
    
    FOREIGN KEY (u_id) REFERENCES PB_USER(u_id),
    FOREIGN KEY (b_id) REFERENCES BRANCH(b_id),
    
    -- kpi_type에 따라 u_id와 b_id 중 하나만 값이 들어가도록 강제
    CONSTRAINT chk_kpi_target CHECK (
        (kpi_type = 'PB' AND u_id IS NOT NULL AND b_id IS NULL) OR
        (kpi_type = 'BRANCH' AND b_id IS NOT NULL AND u_id IS NULL)
    )
);

CREATE TABLE CUSTOMER (
    c_id INT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    number VARCHAR(20) NOT NULL,
    birthday DATE,
    job VARCHAR(50) DEFAULT '무직',
    gender CHAR(1) CHECK (gender IN ('M', 'F')),
    email VARCHAR(50) NOT NULL,
    address VARCHAR(255) NOT NULL,
    tendency VARCHAR(30) NOT NULL CHECK (tendency IN ('안정형', '안정추구형', '위험중립형', '적극투자형', '공격투자형')),
    total_assets BIGINT NOT NULL,
    deposit BIGINT NOT NULL,
    investment BIGINT NOT NULL,
    pension BIGINT NOT NULL,
    loan BIGINT NOT NULL,
    net_worth BIGINT NOT NULL,
    marital_status BOOLEAN NOT NULL,
    start_date DATE DEFAULT (CURRENT_DATE),
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    analysis_time DATETIME NULL
);

CREATE TABLE CUSTOMER_RELATIONSHIP (
    cr_id INT AUTO_INCREMENT PRIMARY KEY,
    c_id INT NOT NULL,
    relationship VARCHAR(50) NOT NULL,
    information TEXT,
    FOREIGN KEY (c_id) REFERENCES CUSTOMER(c_id)
);

CREATE TABLE CUSTOMER_INFORMATION (
    ci_id INT AUTO_INCREMENT PRIMARY KEY,
    c_id INT NOT NULL,
    category VARCHAR(10) NOT NULL CHECK (category IN ('기호', '관계', '성향', '상품', '건강', '기타')),
    contents VARCHAR(500) NOT NULL,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (c_id) REFERENCES CUSTOMER(c_id)
);
CREATE TABLE CUSTOMER_TRANSACTION (
    ct_id INT AUTO_INCREMENT PRIMARY KEY,
    c_id INT NOT NULL,
    ca_id INT NOT NULL,
    ct_type CHAR(1) CHECK (ct_type IN ('D', 'W')),
    amount DECIMAL(15,2) NOT NULL,
    balance_after DECIMAL(15,2) NOT NULL,
    ct_datetime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    briefs VARCHAR(50),
    opp_name VARCHAR(10) NOT NULL,
    opp_account VARCHAR(30) NOT NULL,
    opp_bank_name VARCHAR(10) NOT NULL,
    channel VARCHAR(20) CHECK (channel IN ('ATM', 'MOBILE', 'BRANCH')),
    FOREIGN KEY (c_id) REFERENCES CUSTOMER(c_id),
    FOREIGN KEY (ca_id) REFERENCES CUSTOMER_ACCOUNT(ca_id)
);

CREATE TABLE CUSTOMER_ACCOUNT (
    ca_id INT AUTO_INCREMENT PRIMARY KEY,
    c_id INT NOT NULL,
    account_num VARCHAR(30) NOT NULL,
    account_type VARCHAR(20) NOT NULL CHECK (account_type IN ('보통', '예적금', '연금보험', '대출', '투자상품')),
    balance DECIMAL(15,2) NOT NULL,
    opening_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    cu_id INT NOT NULL,
    FOREIGN KEY (c_id) REFERENCES CUSTOMER(c_id),
    FOREIGN KEY (cu_id) REFERENCES CUSTOMER_PRODUCT(cu_id)
);

CREATE TABLE PRODUCT (
    pd_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    explanation TEXT NOT NULL,
    type VARCHAR(15) NOT NULL CHECK (type IN ('보통', '예적금', '연금보험', '대출', '투자상품')),
    is_main BOOLEAN DEFAULT FALSE,
    update_date DATE NOT NULL
);

CREATE TABLE CUSTOMER_PRODUCT (
    cu_id INT AUTO_INCREMENT PRIMARY KEY,
    opening_date DATE NOT NULL,
    expiration_date DATE NOT NULL,
    pd_id INT NOT NULL,
    c_id INT NOT NULL,
    CONSTRAINT chk_date_logic CHECK (opening_date <= expiration_date),
    FOREIGN KEY (pd_id) REFERENCES PRODUCT(pd_id),
    FOREIGN KEY (c_id) REFERENCES CUSTOMER(c_id)
);

CREATE TABLE IN_CHARGE (
    u_id VARCHAR(50),
    c_id INT,
    PRIMARY KEY (u_id, c_id),
    FOREIGN KEY (u_id) REFERENCES PB_USER(u_id),
    FOREIGN KEY (c_id) REFERENCES CUSTOMER(c_id)
);

CREATE TABLE CHURN_LEVEL (
    level_id INT AUTO_INCREMENT PRIMARY KEY,
    c_id INT NOT NULL,
    grade VARCHAR(5) CHECK (grade IN ('양호', '주의', '위험')),
    reason VARCHAR(100) NOT NULL,
    explain_reason TEXT,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (c_id) REFERENCES CUSTOMER(c_id)
);

CREATE TABLE CONSULTATION_MEMO (
    cm_id INT AUTO_INCREMENT PRIMARY KEY,
    consult_date DATETIME NOT NULL,
    memo TEXT NOT NULL,
    c_id INT NOT NULL,
    u_id VARCHAR(50) NOT NULL,
    FOREIGN KEY (c_id) REFERENCES CUSTOMER(c_id),
    FOREIGN KEY (u_id) REFERENCES PB_USER(u_id)
);

CREATE TABLE CONSULTATION_REPORT (
    cr_id INT AUTO_INCREMENT PRIMARY KEY,
    key_contents TEXT NOT NULL,
    special_notes TEXT NOT NULL,
    follow_up_actions TEXT NOT NULL,
    summary TEXT,
    cm_id INT NOT NULL,
    FOREIGN KEY (cm_id) REFERENCES CONSULTATION_MEMO(cm_id)
);

CREATE TABLE AI_TODO (
    at_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(50) NOT NULL,
    memo VARCHAR(80),
    category VARCHAR(30) CHECK (category IN ('KPI 기반', '상담 일정 제안', '안부 연락 제안', '신규 상품 분석')),
    create_date TIMESTAMP NOT NULL,
    execution_date DATETIME NOT NULL,
    is_checked BOOLEAN DEFAULT FALSE,
    u_id VARCHAR(50) NOT NULL,
    FOREIGN KEY (u_id) REFERENCES PB_USER(u_id)
);
drop table if exists PB_SCHEDULE ;
CREATE TABLE SCHEDULE (
    s_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(50) NOT NULL,
    memo VARCHAR(80),
    category VARCHAR(10) CHECK (category IN ('개인', '공지', '상담')),
    execution_date DATETIME NOT NULL,
    u_id VARCHAR(50) NOT NULL,
    c_id INT, -- 개인이나 공지 일정일 경우 NULL 허용
    at_id INT, -- AI가 제안한 일정이 아닌 수동 등록일 경우 NULL 허용
    FOREIGN KEY (u_id) REFERENCES PB_USER(u_id),
    FOREIGN KEY (c_id) REFERENCES CUSTOMER(c_id),
    FOREIGN KEY (at_id) REFERENCES AI_TODO(at_id)
);

drop table notification;
CREATE TABLE NOTIFICATION (
    n_id INT AUTO_INCREMENT PRIMARY KEY,
    created_time TIMESTAMP NOT NULL,
    title VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(30) CHECK (category IN ('방문 예정 브리핑', '거액 거래 탐지', '만기 알림', '이탈 위험', '안부 연락')),
    state_us VARCHAR(20) NOT NULL,
    u_id VARCHAR(50) NOT NULL,
    s_id INT, -- 스케줄과 무관한 시스템 알림(거액 거래 탐지, 이탈 위험 등)을 위해 NULL 허용
    FOREIGN KEY (u_id) REFERENCES PB_USER(u_id),
    FOREIGN KEY (s_id) REFERENCES SCHEDULE(s_id)
);

CREATE TABLE HANDOVER (
    h_id INT AUTO_INCREMENT PRIMARY KEY,
    a_id VARCHAR(50) NOT NULL,
    c_id INT NOT NULL,
    from_u_id VARCHAR(50) NOT NULL,
    to_u_id VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT '대기' CHECK (status IN ('대기', '진행중', '완료')),
    h_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 기존 담당자와 신규 담당자가 같지 않도록 강제하는 제약조건
    CONSTRAINT chk_diff_pb CHECK (from_u_id <> to_u_id),
    
    FOREIGN KEY (a_id) REFERENCES ACCOUNT(id),
    FOREIGN KEY (c_id) REFERENCES CUSTOMER(c_id),
    FOREIGN KEY (from_u_id) REFERENCES PB_USER(u_id),
    FOREIGN KEY (to_u_id) REFERENCES PB_USER(u_id)
);


