/*
 Navicat Premium Data Transfer

 Source Server         : 乡投-正式
 Source Server Type    : MySQL
 Source Server Version : 80030
 Source Host           : 120.26.58.146:3301
 Source Schema         : vill

 Target Server Type    : MySQL
 Target Server Version : 80030
 File Encoding         : 65001

 Date: 20/06/2026 20:02:24
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for vill_village_job
-- ----------------------------
DROP TABLE IF EXISTS `vill_village_job`;
CREATE TABLE `vill_village_job`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '编号',
  `title` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '标题',
  `village_id` bigint NULL DEFAULT NULL COMMENT '乡村id',
  `pattern` tinyint(1) NOT NULL DEFAULT 0 COMMENT '0招工，1求职',
  `payment` tinyint(1) NOT NULL DEFAULT 0 COMMENT '结算方式，0小时结，1日结，2月结,3完工结',
  `min_salary` decimal(10, 2) UNSIGNED ZEROFILL NULL DEFAULT 00000000.00 COMMENT '最低薪资，元',
  `man_salary` decimal(10, 2) UNSIGNED ZEROFILL NULL DEFAULT 00000000.00 COMMENT '最高薪资，元',
  `introduce` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '详情',
  `introduce_html` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '详情html',
  `member_id` bigint NOT NULL DEFAULT 0 COMMENT '会员id',
  `end_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '结束时间',
  `online` tinyint NULL DEFAULT 0 COMMENT '0下架，1上架',
  `recommend` tinyint(1) NULL DEFAULT 0 COMMENT '推荐：0-否，1-是',
  `longitude` decimal(10, 6) NULL DEFAULT 0.000000 COMMENT '经度',
  `latitude` decimal(10, 6) NULL DEFAULT 0.000000 COMMENT '维度',
  `approve_status` tinyint NULL DEFAULT 0 COMMENT '审批状态，0未审批，1审批中，2审批通过，3审批未通过',
  `approve_id` bigint NULL DEFAULT NULL COMMENT '审批人ID',
  `approve_remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '审批说明',
  `deleted_flag` tinyint(1) NOT NULL DEFAULT 0 COMMENT '删除标志（0代表存在 1代表删除）',
  `create_user_id` bigint NOT NULL DEFAULT 0 COMMENT '创建者',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',
  `update_user_id` bigint NOT NULL DEFAULT 0 COMMENT '更新者',
  `update_time` datetime NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_village_id`(`village_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 59 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '村庄用工求职' ROW_FORMAT = DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;
