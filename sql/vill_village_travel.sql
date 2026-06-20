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

 Date: 20/06/2026 20:02:35
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for vill_village_travel
-- ----------------------------
DROP TABLE IF EXISTS `vill_village_travel`;
CREATE TABLE `vill_village_travel`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '编号',
  `travel_name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '旅游路线名',
  `village_id` bigint NOT NULL DEFAULT 0 COMMENT '乡村id',
  `guide_id` bigint NOT NULL DEFAULT 0 COMMENT '导游id',
  `departure_province_id` bigint NULL DEFAULT NULL COMMENT '出发省id',
  `departure_province_name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '出发省名',
  `departure_city_id` bigint NULL DEFAULT 0 COMMENT '出发城市id',
  `departure_city_name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '出发城市名',
  `travel_imgs` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '图片，多张逗号隔开',
  `introduce` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '路线介绍',
  `introduce_html` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '路线介绍html',
  `gathering_address` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '集合地址',
  `latitude` decimal(10, 6) NULL DEFAULT 0.000000 COMMENT '集合地-经度',
  `longitude` decimal(10, 6) NULL DEFAULT 0.000000 COMMENT '集合地-维度',
  `day_long` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '行程天数',
  `min_group_size` int NULL DEFAULT 1 COMMENT '最小成团人数',
  `price` decimal(10, 2) NULL DEFAULT 0.00 COMMENT '价格，成人价格',
  `child_price` decimal(10, 2) NULL DEFAULT 0.00 COMMENT '儿童价格',
  `comment_code` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '评论code',
  `hot_flag` tinyint(1) NULL DEFAULT 0 COMMENT '热门：0-否，1-是',
  `online` tinyint(1) NULL DEFAULT 0 COMMENT '0-下线 1-上线',
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
  `update_user_id` bigint NOT NULL DEFAULT 0 COMMENT '更新者',
  `update_time` datetime NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `approve_id` bigint NULL DEFAULT 0 COMMENT '审批人ID',
  `approve_remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '审批说明',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_village_id`(`village_id` ASC) USING BTREE,
  INDEX `idx_heat_query`(`online` ASC, `approve_status` ASC, `deleted_flag` ASC, `heat_score` DESC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 220 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '村庄旅行路线' ROW_FORMAT = DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;
