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

 Date: 20/06/2026 20:13:15
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for vill_restaurant
-- ----------------------------
DROP TABLE IF EXISTS `vill_restaurant`;
CREATE TABLE `vill_restaurant`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '编号',
  `restaurant_name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '餐馆名字',
  `shop_id` bigint NOT NULL COMMENT '商铺id，vill_shop表外键',
  `comment_code` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '评价code，用来联查评价表',
  `province_id` bigint NOT NULL DEFAULT 0 COMMENT '省id',
  `province_name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '省份',
  `city_id` bigint NOT NULL DEFAULT 0 COMMENT '城市id',
  `city_name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '城市名',
  `area_id` bigint NOT NULL DEFAULT 0 COMMENT '区id',
  `area_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '地区名',
  `street_id` bigint NOT NULL COMMENT '所属街道id',
  `street_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '所属街道名',
  `village_id` bigint NOT NULL COMMENT '村id',
  `village_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '村名',
  `address` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '详细地址',
  `location_point` point NOT NULL COMMENT '经纬度',
  `lng` decimal(10, 6) GENERATED ALWAYS AS (round(st_x(`location_point`),6)) STORED NULL,
  `lat` decimal(10, 6) GENERATED ALWAYS AS (round(st_y(`location_point`),6)) STORED NULL,
  `introduction` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '餐馆简介',
  `introduction_html` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '餐馆简介html',
  `notice` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '餐馆公告',
  `cover_img` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '餐馆头像图片',
  `score` decimal(4, 2) NULL DEFAULT 0.00 COMMENT '评分，最大5分',
  `deleted_flag` tinyint(1) NULL DEFAULT 0 COMMENT '删除标志（0代表存在 1代表删除）',
  `create_user_id` bigint NULL DEFAULT 0 COMMENT '创建者',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_user_id` bigint NULL DEFAULT 0 COMMENT '更新者',
  `update_time` datetime NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `browse_count` int NULL DEFAULT 0 COMMENT '浏览次数',
  `like_count` int NULL DEFAULT 0 COMMENT '点赞次数',
  `comment_count` int NULL DEFAULT 0 COMMENT '评论次数',
  `collect_count` int NULL DEFAULT 0 COMMENT '收藏次数',
  `heat_score` decimal(20, 6) NULL DEFAULT 10.000000 COMMENT '综合热度值（数值越高越热门）',
  `share_count` int NULL DEFAULT 0 COMMENT '分享次数',
  `online` tinyint NOT NULL DEFAULT 0 COMMENT '0-下线 1-上线',
  `approve_status` tinyint NOT NULL DEFAULT 0 COMMENT '审批状态，0未审批，1审批中，2审批通过，3审批未通过',
  `approve_id` bigint NULL DEFAULT 0 COMMENT '审批人ID',
  `approve_remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '审批说明',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_lng_lat`(`lng` ASC, `lat` ASC) USING BTREE,
  INDEX `idx_restaurant_name`(`restaurant_name` ASC) USING BTREE,
  INDEX `idx_heat_query`(`online` ASC, `approve_status` ASC, `deleted_flag` ASC, `heat_score` DESC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 11 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '农庄信息表' ROW_FORMAT = DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;
