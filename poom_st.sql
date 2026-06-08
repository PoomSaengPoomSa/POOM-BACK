-- MySQL dump 10.13  Distrib 8.0.38, for Win64 (x86_64)
--
-- Host: 118.67.131.22    Database: poom_db
-- ------------------------------------------------------
-- Server version	8.0.38

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `account`
--

DROP TABLE IF EXISTS `account`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `account` (
  `id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `role` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT 'user',
  PRIMARY KEY (`id`),
  CONSTRAINT `account_chk_1` CHECK ((`role` in (_utf8mb4'user',_utf8mb4'admin')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ai_todo`
--

DROP TABLE IF EXISTS `ai_todo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_todo` (
  `at_id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `memo` varchar(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `category` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `create_date` timestamp NOT NULL,
  `execution_date` datetime NOT NULL,
  `is_checked` tinyint(1) DEFAULT '0',
  `u_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `c_id` int DEFAULT NULL,
  PRIMARY KEY (`at_id`),
  KEY `u_id` (`u_id`),
  KEY `fk_aitodo_customer` (`c_id`),
  CONSTRAINT `ai_todo_ibfk_1` FOREIGN KEY (`u_id`) REFERENCES `pb_user` (`u_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_aitodo_customer` FOREIGN KEY (`c_id`) REFERENCES `customer` (`c_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `ai_todo_chk_1` CHECK ((`category` in (_utf8mb4'KPI 기반',_utf8mb4'상담 일정 제안',_utf8mb4'안부 연락 제안',_utf8mb4'신규 상품 분석')))
) ENGINE=InnoDB AUTO_INCREMENT=233 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `baserate_performance`
--

DROP TABLE IF EXISTS `baserate_performance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `baserate_performance` (
  `run_id` varchar(32) NOT NULL COMMENT '실행 ID (고유 식별자)',
  `accuracy` decimal(5,4) NOT NULL COMMENT '모델 정확도 (0~1)',
  `precision` decimal(5,4) NOT NULL COMMENT '모델 정밀도 (0~1)',
  `recall` decimal(5,4) NOT NULL COMMENT '모델 재현율 (0~1)',
  `f1_score` decimal(5,4) NOT NULL COMMENT '모델 F1-Score (0~1)',
  `evaluated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '성능 지표 작성(기록) 시간',
  PRIMARY KEY (`run_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='금리 모델 버전별 성능 평가지표';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `baserate_prediction`
--

DROP TABLE IF EXISTS `baserate_prediction`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `baserate_prediction` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '고유 로그 ID',
  `run_id` varchar(32) NOT NULL COMMENT '예측에 사용된 MLflow 실행 ID (외래키)',
  `prob_hike` decimal(5,4) NOT NULL COMMENT '금리 인상 확률 (Hike)',
  `prob_freeze` decimal(5,4) NOT NULL COMMENT '금리 동결 확률 (Freeze)',
  `prob_cut` decimal(5,4) NOT NULL COMMENT '금리 인하 확률 (Cut)',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '예측 수행 및 저장 시간',
  PRIMARY KEY (`id`),
  KEY `idx_base_rate_run_id` (`run_id`),
  KEY `idx_base_rate_created_at` (`created_at`),
  CONSTRAINT `baserate_prediction_ibfk_1` FOREIGN KEY (`run_id`) REFERENCES `baserate_performance` (`run_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='금리 인상/동결/인하 건별 예측 로그';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `baserate_predictions`
--

DROP TABLE IF EXISTS `baserate_predictions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `baserate_predictions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `run_id` varchar(32) DEFAULT NULL,
  `prob_cut` float DEFAULT NULL,
  `prob_freeze` float DEFAULT NULL,
  `prob_hike` float DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=69 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `branch`
--

DROP TABLE IF EXISTS `branch`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `branch` (
  `b_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `region` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `b_phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `address` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  PRIMARY KEY (`b_id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `churn_level`
--

DROP TABLE IF EXISTS `churn_level`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `churn_level` (
  `level_id` int NOT NULL AUTO_INCREMENT,
  `c_id` int NOT NULL,
  `grade` varchar(5) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `reason` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `explain_reason` text COLLATE utf8mb4_general_ci,
  `created_date` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`level_id`),
  KEY `c_id` (`c_id`),
  CONSTRAINT `churn_level_ibfk_1` FOREIGN KEY (`c_id`) REFERENCES `customer` (`c_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `churn_level_chk_1` CHECK ((`grade` in (_utf8mb4'양호',_utf8mb4'주의',_utf8mb4'위험')))
) ENGINE=InnoDB AUTO_INCREMENT=116 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `consultation_memo`
--

DROP TABLE IF EXISTS `consultation_memo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `consultation_memo` (
  `cm_id` int NOT NULL AUTO_INCREMENT,
  `consult_date` datetime NOT NULL,
  `memo` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `c_id` int NOT NULL,
  `u_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  PRIMARY KEY (`cm_id`),
  KEY `c_id` (`c_id`),
  KEY `u_id` (`u_id`),
  CONSTRAINT `consultation_memo_ibfk_1` FOREIGN KEY (`c_id`) REFERENCES `customer` (`c_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `consultation_memo_ibfk_2` FOREIGN KEY (`u_id`) REFERENCES `pb_user` (`u_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=46 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `consultation_report`
--

DROP TABLE IF EXISTS `consultation_report`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `consultation_report` (
  `cr_id` int NOT NULL AUTO_INCREMENT,
  `cm_id` int NOT NULL,
  `key_contents` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `special_notes` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `follow_up_actions` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `summary` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  PRIMARY KEY (`cr_id`),
  KEY `cm_id` (`cm_id`),
  CONSTRAINT `fk_consultation_report_memo` FOREIGN KEY (`cm_id`) REFERENCES `consultation_memo` (`cm_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=35 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `customer`
--

DROP TABLE IF EXISTS `customer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `customer` (
  `c_id` int NOT NULL,
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `number` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `birthday` date DEFAULT NULL,
  `job` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '무직',
  `gender` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `email` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `address` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `tendency` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `total_assets` bigint NOT NULL,
  `deposit` bigint NOT NULL,
  `investment` bigint NOT NULL,
  `pension` bigint NOT NULL,
  `loan` bigint NOT NULL,
  `net_worth` bigint NOT NULL,
  `marital_status` tinyint(1) NOT NULL,
  `start_date` date DEFAULT (curdate()),
  `grade` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `llm_insight` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `analysis_time` datetime DEFAULT NULL,
  `features` text COLLATE utf8mb4_general_ci,
  PRIMARY KEY (`c_id`),
  CONSTRAINT `chk_customer_grade` CHECK ((`grade` in (_utf8mb4'일반',_utf8mb4'VIP',_utf8mb4'VVIP'))),
  CONSTRAINT `customer_chk_1` CHECK ((`gender` in (_utf8mb4'M',_utf8mb4'F'))),
  CONSTRAINT `customer_chk_2` CHECK ((`tendency` in (_utf8mb4'안정형',_utf8mb4'안정추구형',_utf8mb4'위험중립형',_utf8mb4'적극투자형',_utf8mb4'공격투자형')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `customer_account`
--

DROP TABLE IF EXISTS `customer_account`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `customer_account` (
  `ca_id` int NOT NULL AUTO_INCREMENT,
  `c_id` int NOT NULL,
  `account_num` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `account_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `balance` decimal(15,2) NOT NULL,
  `opening_date` datetime DEFAULT CURRENT_TIMESTAMP,
  `cu_id` int NOT NULL,
  PRIMARY KEY (`ca_id`),
  KEY `c_id` (`c_id`),
  KEY `cu_id` (`cu_id`),
  CONSTRAINT `customer_account_ibfk_1` FOREIGN KEY (`c_id`) REFERENCES `customer` (`c_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `customer_account_ibfk_2` FOREIGN KEY (`cu_id`) REFERENCES `customer_product` (`cu_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `customer_account_chk_1` CHECK ((`account_type` in (_utf8mb4'보통',_utf8mb4'예적금',_utf8mb4'연금보험',_utf8mb4'대출',_utf8mb4'투자상품')))
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `customer_information`
--

DROP TABLE IF EXISTS `customer_information`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `customer_information` (
  `ci_id` int NOT NULL AUTO_INCREMENT,
  `c_id` int NOT NULL,
  `category` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `contents` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `created_date` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`ci_id`),
  KEY `c_id` (`c_id`),
  CONSTRAINT `customer_information_ibfk_1` FOREIGN KEY (`c_id`) REFERENCES `customer` (`c_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `customer_information_chk_1` CHECK ((`category` in (_utf8mb4'기호',_utf8mb4'관계',_utf8mb4'성향',_utf8mb4'상품',_utf8mb4'건강',_utf8mb4'기타')))
) ENGINE=InnoDB AUTO_INCREMENT=239 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `customer_product`
--

DROP TABLE IF EXISTS `customer_product`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `customer_product` (
  `cu_id` int NOT NULL AUTO_INCREMENT,
  `opening_date` date NOT NULL,
  `expiration_date` date NOT NULL,
  `pd_id` int NOT NULL,
  `c_id` int NOT NULL,
  PRIMARY KEY (`cu_id`),
  KEY `pd_id` (`pd_id`),
  KEY `c_id` (`c_id`),
  CONSTRAINT `customer_product_ibfk_1` FOREIGN KEY (`pd_id`) REFERENCES `product` (`pd_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `customer_product_ibfk_2` FOREIGN KEY (`c_id`) REFERENCES `customer` (`c_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `chk_date_logic` CHECK ((`opening_date` <= `expiration_date`))
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `customer_relationship`
--

DROP TABLE IF EXISTS `customer_relationship`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `customer_relationship` (
  `cr_id` int NOT NULL AUTO_INCREMENT,
  `c_id` int NOT NULL,
  `relationship` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
  `information` text COLLATE utf8mb4_general_ci,
  `birthday` date DEFAULT NULL,
  `job` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `is_spouse` tinyint(1) DEFAULT '0',
  `wedding_date` date DEFAULT NULL,
  PRIMARY KEY (`cr_id`),
  KEY `c_id` (`c_id`),
  CONSTRAINT `customer_relationship_ibfk_1` FOREIGN KEY (`c_id`) REFERENCES `customer` (`c_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=68 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `customer_transaction`
--

DROP TABLE IF EXISTS `customer_transaction`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `customer_transaction` (
  `ct_id` int NOT NULL AUTO_INCREMENT,
  `c_id` int NOT NULL,
  `ca_id` int NOT NULL,
  `ct_type` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `amount` decimal(15,2) NOT NULL,
  `balance_after` decimal(15,2) NOT NULL,
  `ct_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `briefs` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `opp_name` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `opp_account` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `opp_bank_name` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `channel` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  PRIMARY KEY (`ct_id`),
  KEY `c_id` (`c_id`),
  KEY `ca_id` (`ca_id`),
  CONSTRAINT `customer_transaction_ibfk_1` FOREIGN KEY (`c_id`) REFERENCES `customer` (`c_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `customer_transaction_ibfk_2` FOREIGN KEY (`ca_id`) REFERENCES `customer_account` (`ca_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `customer_transaction_chk_1` CHECK ((`ct_type` in (_utf8mb4'D',_utf8mb4'W'))),
  CONSTRAINT `customer_transaction_chk_2` CHECK ((`channel` in (_utf8mb4'ATM',_utf8mb4'MOBILE',_utf8mb4'BRANCH')))
) ENGINE=InnoDB AUTO_INCREMENT=73 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `economic_indicator_contribution`
--

DROP TABLE IF EXISTS `economic_indicator_contribution`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `economic_indicator_contribution` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `variable` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `weight` decimal(5,4) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=195 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `economic_indicator_history`
--

DROP TABLE IF EXISTS `economic_indicator_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `economic_indicator_history` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `value` decimal(15,4) NOT NULL,
  `recorded_at` datetime NOT NULL,
  `source` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_eih_type_recorded` (`type`,`recorded_at` DESC)
) ENGINE=InnoDB AUTO_INCREMENT=544 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `economic_indicator_prediction`
--

DROP TABLE IF EXISTS `economic_indicator_prediction`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `economic_indicator_prediction` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `predicted_value` decimal(15,4) NOT NULL,
  `confidence_lower` decimal(15,4) DEFAULT NULL,
  `confidence_upper` decimal(15,4) DEFAULT NULL,
  `predicted_date` date NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_eip_type_date` (`type`,`predicted_date`)
) ENGINE=InnoDB AUTO_INCREMENT=127 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `gold_performance`
--

DROP TABLE IF EXISTS `gold_performance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `gold_performance` (
  `run_id` varchar(32) NOT NULL COMMENT 'MLflow 실행 ID (고유 식별자)',
  `accuracy` decimal(5,4) NOT NULL COMMENT '모델 정확도 (0~1)',
  `precision` decimal(5,4) NOT NULL COMMENT '모델 정밀도 (0~1)',
  `recall` decimal(5,4) NOT NULL COMMENT '모델 재현율 (0~1)',
  `f1_score` decimal(5,4) NOT NULL COMMENT '모델 F1-Score (0~1)',
  `evaluated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '성능 지표 작성(기록) 시간',
  PRIMARY KEY (`run_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='모델 버전별 성능 평가지표';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `gold_prediction`
--

DROP TABLE IF EXISTS `gold_prediction`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `gold_prediction` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '고유 로그 ID',
  `run_id` varchar(32) NOT NULL COMMENT '예측에 사용된 MLflow 실행 ID (외래키)',
  `prob_rise` decimal(5,4) NOT NULL COMMENT '금값 상승 확률',
  `prob_fall` decimal(5,4) NOT NULL COMMENT '금값 하락 확률',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '예측 수행 및 저장 시간',
  PRIMARY KEY (`id`),
  KEY `idx_run_id` (`run_id`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `gold_prediction_ibfk_1` FOREIGN KEY (`run_id`) REFERENCES `gold_performance` (`run_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=620 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='금값 상승/하락 건별 예측 로그';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `gold_predictions`
--

DROP TABLE IF EXISTS `gold_predictions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `gold_predictions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `run_id` varchar(32) DEFAULT NULL,
  `prob_rise` float DEFAULT NULL,
  `prob_fall` float DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=43 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `handover`
--

DROP TABLE IF EXISTS `handover`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `handover` (
  `h_id` int NOT NULL AUTO_INCREMENT,
  `a_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `c_id` int NOT NULL,
  `from_u_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `to_u_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '대기',
  `h_date` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`h_id`),
  KEY `a_id` (`a_id`),
  KEY `c_id` (`c_id`),
  KEY `from_u_id` (`from_u_id`),
  KEY `fk_ho_pb_to` (`to_u_id`),
  KEY `idx_ho_from_status` (`from_u_id`,`status`),
  CONSTRAINT `fk_ho_pb_to` FOREIGN KEY (`to_u_id`) REFERENCES `pb_user` (`u_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `handover_ibfk_1` FOREIGN KEY (`a_id`) REFERENCES `account` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `handover_ibfk_2` FOREIGN KEY (`c_id`) REFERENCES `customer` (`c_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `handover_ibfk_3` FOREIGN KEY (`from_u_id`) REFERENCES `pb_user` (`u_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `handover_ibfk_4` FOREIGN KEY (`to_u_id`) REFERENCES `pb_user` (`u_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `chk_diff_pb` CHECK ((`from_u_id` <> `to_u_id`)),
  CONSTRAINT `handover_chk_1` CHECK ((`status` in (_utf8mb4'대기',_utf8mb4'진행중',_utf8mb4'완료')))
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `in_charge`
--

DROP TABLE IF EXISTS `in_charge`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `in_charge` (
  `u_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `c_id` int NOT NULL,
  PRIMARY KEY (`u_id`,`c_id`),
  KEY `c_id` (`c_id`),
  KEY `idx_ic_cid` (`c_id`),
  CONSTRAINT `in_charge_ibfk_1` FOREIGN KEY (`u_id`) REFERENCES `pb_user` (`u_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `in_charge_ibfk_2` FOREIGN KEY (`c_id`) REFERENCES `customer` (`c_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `kpi`
--

DROP TABLE IF EXISTS `kpi`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kpi` (
  `kpi_id` int NOT NULL AUTO_INCREMENT,
  `aum` bigint NOT NULL,
  `non_interest` bigint NOT NULL,
  `new_customer` bigint NOT NULL DEFAULT '0',
  `kpi_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `u_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `b_id` int DEFAULT NULL,
  `created_date` date DEFAULT (curdate()),
  `target_aum` bigint NOT NULL,
  `target_non_interest` bigint NOT NULL,
  `target_new_customer` bigint NOT NULL DEFAULT '0',
  `current_aum` bigint NOT NULL,
  `current_non_interest` bigint NOT NULL,
  `current_new_customer` bigint NOT NULL DEFAULT '0',
  `recorded_date` date NOT NULL,
  PRIMARY KEY (`kpi_id`),
  KEY `u_id` (`u_id`),
  KEY `b_id` (`b_id`),
  CONSTRAINT `kpi_ibfk_1` FOREIGN KEY (`u_id`) REFERENCES `pb_user` (`u_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `kpi_ibfk_2` FOREIGN KEY (`b_id`) REFERENCES `branch` (`b_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `chk_current_aum` CHECK ((`current_aum` >= 0)),
  CONSTRAINT `chk_current_new_customer` CHECK ((`current_new_customer` >= 0)),
  CONSTRAINT `chk_current_non_interest` CHECK ((`current_non_interest` >= 0)),
  CONSTRAINT `chk_kpi_target` CHECK ((((`kpi_type` = _utf8mb4'PB') and (`u_id` is not null) and (`b_id` is null)) or ((`kpi_type` = _utf8mb4'BRANCH') and (`b_id` is not null) and (`u_id` is null)))),
  CONSTRAINT `kpi_chk_1` CHECK ((`aum` >= 0)),
  CONSTRAINT `kpi_chk_2` CHECK ((`non_interest` >= 0)),
  CONSTRAINT `kpi_chk_3` CHECK ((`new_customer` >= 0)),
  CONSTRAINT `kpi_chk_4` CHECK ((`kpi_type` in (_utf8mb4'PB',_utf8mb4'BRANCH'))),
  CONSTRAINT `kpi_chk_5` CHECK ((`target_aum` >= 0)),
  CONSTRAINT `kpi_chk_6` CHECK ((`target_non_interest` >= 0)),
  CONSTRAINT `kpi_chk_7` CHECK ((`target_new_customer` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ml_baserate_preprocessed`
--

DROP TABLE IF EXISTS `ml_baserate_preprocessed`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ml_baserate_preprocessed` (
  `date_ym` varchar(10) NOT NULL,
  `kr_cpi_yoy` decimal(15,4) DEFAULT NULL,
  `wti_oil_yoy` decimal(15,4) DEFAULT NULL,
  `kr_usd_exchange_yoy` decimal(15,4) DEFAULT NULL,
  `wti_oil` decimal(15,4) DEFAULT NULL,
  `wti_oil_ma3` decimal(15,4) DEFAULT NULL,
  `wti_oil_ma6` decimal(15,4) DEFAULT NULL,
  `kr_cpi_mom6` decimal(15,4) DEFAULT NULL,
  `kr_m2_change` decimal(15,4) DEFAULT NULL,
  `kr_cpi_ma3` decimal(15,4) DEFAULT NULL,
  `kr_cpi` decimal(15,4) DEFAULT NULL,
  `kr_base_rate_change` decimal(15,4) DEFAULT NULL,
  `label` varchar(20) DEFAULT NULL,
  `label_encoded` int DEFAULT NULL,
  PRIMARY KEY (`date_ym`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ml_baserate_raw`
--

DROP TABLE IF EXISTS `ml_baserate_raw`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ml_baserate_raw` (
  `br_id` int NOT NULL AUTO_INCREMENT,
  `loaded_date` datetime NOT NULL,
  `kr_base_rate` decimal(15,2) DEFAULT NULL,
  `kr_cpi` decimal(15,2) DEFAULT NULL,
  `kr_unemployment` decimal(15,2) DEFAULT NULL,
  `kr_usd_exchange` decimal(15,2) DEFAULT NULL,
  `kr_gdp` decimal(15,2) DEFAULT NULL,
  `kr_m2` decimal(15,2) DEFAULT NULL,
  `us_fed_rate` decimal(15,2) DEFAULT NULL,
  `vix` decimal(15,2) DEFAULT NULL,
  `wti_oil` decimal(15,2) DEFAULT NULL,
  PRIMARY KEY (`br_id`,`loaded_date`)
) ENGINE=InnoDB AUTO_INCREMENT=151 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ml_gold_preprocessed`
--

DROP TABLE IF EXISTS `ml_gold_preprocessed`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ml_gold_preprocessed` (
  `loaded_date` varchar(20) NOT NULL,
  `gold` decimal(15,6) DEFAULT NULL,
  `gold_change_rate` decimal(15,6) DEFAULT NULL,
  `kr_cpi` decimal(15,6) DEFAULT NULL,
  `kr_usd_exchange` decimal(15,6) DEFAULT NULL,
  `wti_oil` decimal(15,6) DEFAULT NULL,
  `dxy_proxy` decimal(15,6) DEFAULT NULL,
  `vix` decimal(15,6) DEFAULT NULL,
  `kospi200` decimal(15,6) DEFAULT NULL,
  `sp500` decimal(15,6) DEFAULT NULL,
  `kr_usd_exchange_change_rate` decimal(15,6) DEFAULT NULL,
  `wti_oil_change_rate` decimal(15,6) DEFAULT NULL,
  `dxy_proxy_change_rate` decimal(15,6) DEFAULT NULL,
  `vix_change_rate` decimal(15,6) DEFAULT NULL,
  `kospi200_change_rate` decimal(15,6) DEFAULT NULL,
  `sp500_change_rate` decimal(15,6) DEFAULT NULL,
  `gold_rsi_14` decimal(15,6) DEFAULT NULL,
  `gold_macd` decimal(15,6) DEFAULT NULL,
  `gold_macd_signal` decimal(15,6) DEFAULT NULL,
  `gold_change_rate_ema_5` decimal(15,6) DEFAULT NULL,
  `gold_change_rate_ema_20` decimal(15,6) DEFAULT NULL,
  `sp500_kospi200_spread` decimal(15,6) DEFAULT NULL,
  `gold_dxy_interaction` decimal(15,6) DEFAULT NULL,
  `gold_change_rate_lag_1` decimal(15,6) DEFAULT NULL,
  `gold_change_rate_lag_2` decimal(15,6) DEFAULT NULL,
  `gold_change_rate_lag_3` decimal(15,6) DEFAULT NULL,
  `kr_usd_exchange_change_rate_lag_1` decimal(15,6) DEFAULT NULL,
  `kr_usd_exchange_change_rate_lag_2` decimal(15,6) DEFAULT NULL,
  `kr_usd_exchange_change_rate_lag_3` decimal(15,6) DEFAULT NULL,
  `wti_oil_change_rate_lag_1` decimal(15,6) DEFAULT NULL,
  `wti_oil_change_rate_lag_2` decimal(15,6) DEFAULT NULL,
  `wti_oil_change_rate_lag_3` decimal(15,6) DEFAULT NULL,
  `dxy_proxy_change_rate_lag_1` decimal(15,6) DEFAULT NULL,
  `dxy_proxy_change_rate_lag_2` decimal(15,6) DEFAULT NULL,
  `dxy_proxy_change_rate_lag_3` decimal(15,6) DEFAULT NULL,
  `vix_change_rate_lag_1` decimal(15,6) DEFAULT NULL,
  `vix_change_rate_lag_2` decimal(15,6) DEFAULT NULL,
  `vix_change_rate_lag_3` decimal(15,6) DEFAULT NULL,
  `kospi200_change_rate_lag_1` decimal(15,6) DEFAULT NULL,
  `kospi200_change_rate_lag_2` decimal(15,6) DEFAULT NULL,
  `kospi200_change_rate_lag_3` decimal(15,6) DEFAULT NULL,
  `sp500_change_rate_lag_1` decimal(15,6) DEFAULT NULL,
  `sp500_change_rate_lag_2` decimal(15,6) DEFAULT NULL,
  `sp500_change_rate_lag_3` decimal(15,6) DEFAULT NULL,
  `gold_rsi_14_lag_1` decimal(15,6) DEFAULT NULL,
  `gold_rsi_14_lag_2` decimal(15,6) DEFAULT NULL,
  `gold_rsi_14_lag_3` decimal(15,6) DEFAULT NULL,
  `gold_macd_lag_1` decimal(15,6) DEFAULT NULL,
  `gold_macd_lag_2` decimal(15,6) DEFAULT NULL,
  `gold_macd_lag_3` decimal(15,6) DEFAULT NULL,
  `gold_macd_signal_lag_1` decimal(15,6) DEFAULT NULL,
  `gold_macd_signal_lag_2` decimal(15,6) DEFAULT NULL,
  `gold_macd_signal_lag_3` decimal(15,6) DEFAULT NULL,
  `gold_change_rate_ema_5_lag_1` decimal(15,6) DEFAULT NULL,
  `gold_change_rate_ema_5_lag_2` decimal(15,6) DEFAULT NULL,
  `gold_change_rate_ema_5_lag_3` decimal(15,6) DEFAULT NULL,
  `gold_change_rate_ema_20_lag_1` decimal(15,6) DEFAULT NULL,
  `gold_change_rate_ema_20_lag_2` decimal(15,6) DEFAULT NULL,
  `gold_change_rate_ema_20_lag_3` decimal(15,6) DEFAULT NULL,
  `sp500_kospi200_spread_lag_1` decimal(15,6) DEFAULT NULL,
  `sp500_kospi200_spread_lag_2` decimal(15,6) DEFAULT NULL,
  `sp500_kospi200_spread_lag_3` decimal(15,6) DEFAULT NULL,
  `gold_dxy_interaction_lag_1` decimal(15,6) DEFAULT NULL,
  `gold_dxy_interaction_lag_2` decimal(15,6) DEFAULT NULL,
  `gold_dxy_interaction_lag_3` decimal(15,6) DEFAULT NULL,
  `gold_change_rate_sma_5` decimal(15,6) DEFAULT NULL,
  `gold_change_rate_sma_20` decimal(15,6) DEFAULT NULL,
  `gold_change_rate_std_5` decimal(15,6) DEFAULT NULL,
  `gold_change_rate_std_20` decimal(15,6) DEFAULT NULL,
  `target_tomorrow_gold_change_rate` decimal(15,6) DEFAULT NULL,
  `target_tomorrow_gold_direction` int DEFAULT NULL,
  PRIMARY KEY (`loaded_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ml_gold_raw`
--

DROP TABLE IF EXISTS `ml_gold_raw`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ml_gold_raw` (
  `gr_id` int NOT NULL AUTO_INCREMENT,
  `loaded_date` datetime NOT NULL,
  `gold` decimal(15,2) DEFAULT NULL,
  `kr_usd_exchange` decimal(15,2) DEFAULT NULL,
  `wti_oil` decimal(15,2) DEFAULT NULL,
  `dxy_proxy` decimal(15,2) DEFAULT NULL,
  `vix` decimal(15,2) DEFAULT NULL,
  `kospi200` decimal(15,2) DEFAULT NULL,
  `sp500` decimal(15,2) DEFAULT NULL,
  `kr_cpi` decimal(15,2) DEFAULT NULL,
  `us_fed_rate` decimal(15,6) DEFAULT NULL,
  `kr_base_rate` decimal(15,6) DEFAULT NULL,
  PRIMARY KEY (`gr_id`,`loaded_date`)
) ENGINE=InnoDB AUTO_INCREMENT=4534 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ml_realestate_preprocessed`
--

DROP TABLE IF EXISTS `ml_realestate_preprocessed`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ml_realestate_preprocessed` (
  `date_ym` varchar(10) NOT NULL,
  `house_price_idx` decimal(15,6) DEFAULT NULL,
  `house_price_idx_change` decimal(15,6) DEFAULT NULL,
  `kr_cpi_change` decimal(15,6) DEFAULT NULL,
  `kospi200_change` decimal(15,6) DEFAULT NULL,
  `apt_trade_count_change` decimal(15,6) DEFAULT NULL,
  `kr_m2_change` decimal(15,6) DEFAULT NULL,
  `kr_unemployment_change` decimal(15,6) DEFAULT NULL,
  `kr_base_rate_change` decimal(15,6) DEFAULT NULL,
  `kr_mortgage_rate_change` decimal(15,6) DEFAULT NULL,
  `buyer_dominance_change` decimal(15,6) DEFAULT NULL,
  `house_price_idx_change_lag1` decimal(15,6) DEFAULT NULL,
  `house_price_idx_change_lag2` decimal(15,6) DEFAULT NULL,
  `house_price_idx_change_lag3` decimal(15,6) DEFAULT NULL,
  `kr_cpi_change_lag1` decimal(15,6) DEFAULT NULL,
  `kr_cpi_change_lag2` decimal(15,6) DEFAULT NULL,
  `kr_cpi_change_lag3` decimal(15,6) DEFAULT NULL,
  `kospi200_change_lag1` decimal(15,6) DEFAULT NULL,
  `kospi200_change_lag2` decimal(15,6) DEFAULT NULL,
  `kospi200_change_lag3` decimal(15,6) DEFAULT NULL,
  `apt_trade_count_change_lag1` decimal(15,6) DEFAULT NULL,
  `apt_trade_count_change_lag2` decimal(15,6) DEFAULT NULL,
  `apt_trade_count_change_lag3` decimal(15,6) DEFAULT NULL,
  `kr_m2_change_lag1` decimal(15,6) DEFAULT NULL,
  `kr_m2_change_lag2` decimal(15,6) DEFAULT NULL,
  `kr_m2_change_lag3` decimal(15,6) DEFAULT NULL,
  `kr_unemployment_change_lag1` decimal(15,6) DEFAULT NULL,
  `kr_unemployment_change_lag2` decimal(15,6) DEFAULT NULL,
  `kr_unemployment_change_lag3` decimal(15,6) DEFAULT NULL,
  `kr_base_rate_change_lag1` decimal(15,6) DEFAULT NULL,
  `kr_base_rate_change_lag2` decimal(15,6) DEFAULT NULL,
  `kr_base_rate_change_lag3` decimal(15,6) DEFAULT NULL,
  `kr_mortgage_rate_change_lag1` decimal(15,6) DEFAULT NULL,
  `kr_mortgage_rate_change_lag2` decimal(15,6) DEFAULT NULL,
  `kr_mortgage_rate_change_lag3` decimal(15,6) DEFAULT NULL,
  `buyer_dominance_change_lag1` decimal(15,6) DEFAULT NULL,
  `buyer_dominance_change_lag2` decimal(15,6) DEFAULT NULL,
  `buyer_dominance_change_lag3` decimal(15,6) DEFAULT NULL,
  `house_price_idx_change_ma3` decimal(15,6) DEFAULT NULL,
  `house_price_idx_change_ma6` decimal(15,6) DEFAULT NULL,
  `buyer_dominance_change_ma3` decimal(15,6) DEFAULT NULL,
  `buyer_dominance_change_ma6` decimal(15,6) DEFAULT NULL,
  `apt_trade_count_change_ma3` decimal(15,6) DEFAULT NULL,
  `apt_trade_count_change_ma6` decimal(15,6) DEFAULT NULL,
  `kr_mortgage_rate_change_ma3` decimal(15,6) DEFAULT NULL,
  `kr_mortgage_rate_change_ma6` decimal(15,6) DEFAULT NULL,
  `month_sin` decimal(15,6) DEFAULT NULL,
  `month_cos` decimal(15,6) DEFAULT NULL,
  `next_change_rate` decimal(15,6) DEFAULT NULL,
  PRIMARY KEY (`date_ym`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ml_realestate_raw`
--

DROP TABLE IF EXISTS `ml_realestate_raw`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ml_realestate_raw` (
  `rr_id` int NOT NULL AUTO_INCREMENT,
  `loaded_date` datetime NOT NULL,
  `house_price_idx` decimal(15,2) DEFAULT NULL,
  `kr_cpi` decimal(15,2) DEFAULT NULL,
  `kr_unemployment` decimal(15,2) DEFAULT NULL,
  `kr_base_rate` decimal(15,2) DEFAULT NULL,
  `kr_mortgage_rate` decimal(15,2) DEFAULT NULL,
  `kospi200` decimal(15,2) DEFAULT NULL,
  `apt_trade_count` decimal(15,2) DEFAULT NULL,
  `kr_m2` decimal(15,2) DEFAULT NULL,
  `buyer_dominance` decimal(15,2) DEFAULT NULL,
  `us_fed_rate` decimal(15,2) DEFAULT NULL,
  PRIMARY KEY (`rr_id`,`loaded_date`)
) ENGINE=InnoDB AUTO_INCREMENT=151 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `notification`
--

DROP TABLE IF EXISTS `notification`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notification` (
  `n_id` int NOT NULL AUTO_INCREMENT,
  `created_time` timestamp NOT NULL,
  `title` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `category` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `state_us` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `u_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `s_id` int DEFAULT NULL,
  `c_id` int DEFAULT NULL,
  PRIMARY KEY (`n_id`),
  UNIQUE KEY `uq_notification_s_id_category` (`s_id`,`category`),
  KEY `u_id` (`u_id`),
  KEY `s_id` (`s_id`),
  KEY `fk_notification_customer` (`c_id`),
  CONSTRAINT `fk_notification_customer` FOREIGN KEY (`c_id`) REFERENCES `customer` (`c_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `notification_ibfk_1` FOREIGN KEY (`u_id`) REFERENCES `pb_user` (`u_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `notification_ibfk_2` FOREIGN KEY (`s_id`) REFERENCES `pb_schedule` (`s_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `notification_chk_1` CHECK ((`category` in (_utf8mb4'방문 예정 브리핑',_utf8mb4'거액 거래 탐지',_utf8mb4'만기 알림',_utf8mb4'이탈 위험',_utf8mb4'안부 연락')))
) ENGINE=InnoDB AUTO_INCREMENT=183 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `pb_schedule`
--

DROP TABLE IF EXISTS `pb_schedule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pb_schedule` (
  `s_id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `memo` varchar(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `category` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `execution_date` datetime NOT NULL,
  `u_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `c_id` int DEFAULT NULL,
  `at_id` int DEFAULT NULL,
  `end_datetime` datetime NOT NULL,
  PRIMARY KEY (`s_id`),
  KEY `u_id` (`u_id`),
  KEY `c_id` (`c_id`),
  KEY `at_id` (`at_id`),
  KEY `idx_sched_u_cat_exec` (`u_id`,`category`,`execution_date` DESC),
  KEY `idx_sched_c_cat_exec` (`c_id`,`category`,`execution_date` DESC),
  CONSTRAINT `pb_schedule_ibfk_1` FOREIGN KEY (`u_id`) REFERENCES `pb_user` (`u_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `pb_schedule_ibfk_2` FOREIGN KEY (`c_id`) REFERENCES `customer` (`c_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `pb_schedule_ibfk_3` FOREIGN KEY (`at_id`) REFERENCES `ai_todo` (`at_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `pb_schedule_chk_1` CHECK ((`category` in (_utf8mb4'개인',_utf8mb4'공지',_utf8mb4'상담')))
) ENGINE=InnoDB AUTO_INCREMENT=242 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `pb_user`
--

DROP TABLE IF EXISTS `pb_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pb_user` (
  `u_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `email` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `number` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `branch` int NOT NULL,
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '재직',
  `position` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT 'PB',
  `profile` blob,
  `start_date` date NOT NULL,
  `birth_date` date NOT NULL,
  PRIMARY KEY (`u_id`),
  UNIQUE KEY `email` (`email`),
  KEY `branch` (`branch`),
  CONSTRAINT `pb_user_ibfk_1` FOREIGN KEY (`u_id`) REFERENCES `account` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `pb_user_ibfk_2` FOREIGN KEY (`branch`) REFERENCES `branch` (`b_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `pb_user_chk_1` CHECK ((`status` in (_utf8mb4'재직',_utf8mb4'휴직',_utf8mb4'퇴사',_utf8mb4'발령대기'))),
  CONSTRAINT `pb_user_chk_2` CHECK ((`position` in (_utf8mb4'PB',_utf8mb4'팀장',_utf8mb4'지점장')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `product`
--

DROP TABLE IF EXISTS `product`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `product` (
  `pd_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `explanation` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `type` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `is_main` tinyint(1) DEFAULT '0',
  `update_date` date NOT NULL,
  `season` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `issuer` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `features` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `target_customer` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `expected_return` float NOT NULL,
  `return_type` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  PRIMARY KEY (`pd_id`),
  UNIQUE KEY `name` (`name`),
  CONSTRAINT `product_chk_1` CHECK ((`type` in (_utf8mb4'보통',_utf8mb4'예적금',_utf8mb4'연금보험',_utf8mb4'대출',_utf8mb4'투자상품')))
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `product_matching`
--

DROP TABLE IF EXISTS `product_matching`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `product_matching` (
  `matching_id` int NOT NULL AUTO_INCREMENT,
  `pd_id` int NOT NULL,
  `c_id` int NOT NULL,
  `is_suitable` tinyint(1) NOT NULL,
  `reason` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `created_date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`matching_id`),
  KEY `fk_pm_product` (`pd_id`),
  KEY `fk_pm_customer` (`c_id`),
  CONSTRAINT `fk_pm_customer` FOREIGN KEY (`c_id`) REFERENCES `customer` (`c_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_pm_product` FOREIGN KEY (`pd_id`) REFERENCES `product` (`pd_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=520 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `realestate_performance`
--

DROP TABLE IF EXISTS `realestate_performance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `realestate_performance` (
  `run_id` varchar(32) NOT NULL COMMENT '실행 ID',
  `rmse` decimal(10,4) NOT NULL COMMENT '루트 평균 제곱 오차 (RMSE)',
  `r2_score` decimal(5,4) NOT NULL COMMENT '결정계수 (R2 Score)',
  `mae` decimal(10,4) NOT NULL COMMENT '평균 절대 오차 (MAE)',
  `mse` decimal(15,4) NOT NULL COMMENT '평균 제곱 오차 (MSE)',
  `evaluated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '성능 지표 작성(기록) 시간',
  PRIMARY KEY (`run_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='부동산 회귀 모델 버전별 성능 평가지표';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `realestate_prediction`
--

DROP TABLE IF EXISTS `realestate_prediction`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `realestate_prediction` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '고유 로그 ID',
  `run_id` varchar(32) NOT NULL COMMENT '예측에 사용된 실행 ID',
  `predicted_value` decimal(10,4) NOT NULL COMMENT '모델이 예측한 부동산 매매 가격 지수',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '예측 수행 및 저장 시간',
  PRIMARY KEY (`id`),
  KEY `idx_real_estate_run_id` (`run_id`),
  KEY `idx_real_estate_created_at` (`created_at`),
  CONSTRAINT `realestate_prediction_ibfk_1` FOREIGN KEY (`run_id`) REFERENCES `realestate_performance` (`run_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=49 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='부동산 매매 가격 지수 건별 예측 로그';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `realestate_predictions`
--

DROP TABLE IF EXISTS `realestate_predictions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `realestate_predictions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `run_id` varchar(32) DEFAULT NULL,
  `predicted_value` float DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `predicted_index` float DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=85 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `trend_llm_report`
--

DROP TABLE IF EXISTS `trend_llm_report`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `trend_llm_report` (
  `report_id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(50) NOT NULL,
  `content` text NOT NULL,
  `summary` text,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`report_id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `trend_news`
--

DROP TABLE IF EXISTS `trend_news`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `trend_news` (
  `news_id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `category` varchar(50) NOT NULL,
  `body` text,
  `published_at` datetime DEFAULT NULL,
  `source` varchar(100) NOT NULL,
  `origin_url` varchar(255) DEFAULT NULL,
  `tags` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`news_id`),
  KEY `idx_tn_pub` (`published_at` DESC),
  KEY `idx_tn_cat_pub` (`category`,`published_at` DESC),
  KEY `idx_tn_url` (`origin_url`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-06-05 16:31:01
