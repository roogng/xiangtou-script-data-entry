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

 Date: 20/06/2026 20:02:02
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for vill_village_activity
-- ----------------------------
DROP TABLE IF EXISTS `vill_village_activity`;
CREATE TABLE `vill_village_activity`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '编号',
  `comment_code` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '评论code',
  `village_id` bigint NULL DEFAULT NULL COMMENT '村庄id',
  `activity_name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '活动名称',
  `day_long` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '0' COMMENT '活动所需时间',
  `introduce` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '活动介绍',
  `introduce_html` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '活动介绍html',
  `start_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
  `end_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '结束时间',
  `activity_imgs` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '活动图片',
  `main_org` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '主办方',
  `main_org_introduction` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '主办方简介',
  `assist_org` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '协办方',
  `assist_org_introduction` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '协办方简介',
  `sponsor` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '赞助方',
  `sponsor_introduction` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '赞助方简介',
  `current_price` decimal(10, 2) UNSIGNED ZEROFILL NULL DEFAULT 00000000.00 COMMENT '当前价格，元',
  `precautions` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '注意事项',
  `address` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '活动地址',
  `latitude` decimal(10, 6) NULL DEFAULT NULL COMMENT '活动地-经度',
  `longitude` decimal(10, 6) NULL DEFAULT NULL COMMENT '活动地-维度',
  `member_id` bigint NULL DEFAULT NULL COMMENT '会员id',
  `online` tinyint NULL DEFAULT 0 COMMENT '0下架，1上架',
  `approve_status` tinyint NULL DEFAULT 0 COMMENT '审批状态，0未审批，1审批中，2审批通过，3审批未通过',
  `activity_status` tinyint NULL DEFAULT 1 COMMENT '活动状态，1预热，2进行中，3已结束',
  `like_count` int NULL DEFAULT 0 COMMENT '点赞次数',
  `browse_count` int NULL DEFAULT 0 COMMENT '浏览次数',
  `share_count` int NULL DEFAULT 0 COMMENT '分享次数',
  `collect_count` int NULL DEFAULT 0 COMMENT '收藏次数',
  `heat_score` decimal(20, 6) NULL DEFAULT 10.000000 COMMENT '综合热度值（数值越高越热门）',
  `comment_count` int NULL DEFAULT 0 COMMENT '评论次数',
  `max_member_count` int NULL DEFAULT -1 COMMENT '最大报名人数，-1表示不限制',
  `current_member_count` int NULL DEFAULT 0 COMMENT '当前报名人数',
  `deleted_flag` tinyint(1) NOT NULL DEFAULT 0 COMMENT '删除标志（0代表存在 1代表删除）',
  `create_user_id` bigint NOT NULL DEFAULT 0 COMMENT '创建者',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',
  `update_user_id` bigint NULL DEFAULT 0 COMMENT '更新者',
  `update_time` datetime NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `approve_id` bigint NULL DEFAULT 0 COMMENT '审批人ID',
  `approve_remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '审批说明',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_village_id`(`village_id` ASC) USING BTREE,
  INDEX `idx_heat_query`(`online` ASC, `approve_status` ASC, `deleted_flag` ASC, `heat_score` DESC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 296 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '村庄活动' ROW_FORMAT = DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;
