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

 Date: 20/06/2026 20:03:28
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for vill_homestay
-- ----------------------------
DROP TABLE IF EXISTS `vill_homestay`;
CREATE TABLE `vill_homestay`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '编号',
  `title` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '标题',
  `cover_img` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '封面图片,多张用逗号隔开',
  `comment_code` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '评价code，用来联查评价表',
  `village_id` bigint NOT NULL DEFAULT 0 COMMENT '所属村庄id，联查村庄表',
  `village_code` bigint NULL DEFAULT NULL COMMENT '村庄的行政编码',
  `village_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '村庄名字',
  `province_id` bigint NOT NULL DEFAULT 0 COMMENT '省id',
  `province_name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '省份',
  `city_id` bigint NOT NULL DEFAULT 0 COMMENT '城市id',
  `city_name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '城市名',
  `area_id` bigint NOT NULL DEFAULT 0 COMMENT '区id',
  `area_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '地区名',
  `street_id` bigint NOT NULL COMMENT '所属街道id',
  `street_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '所属街道名',
  `address` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '详细地址',
  `homeowner_id` bigint NOT NULL DEFAULT 0 COMMENT '房东id',
  `introduce` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '民宿介绍',
  `introduce_html` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '民宿介绍，富文本',
  `introduce_img` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '介绍图片，多张用逗号隔开',
  `link_man` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '联系人',
  `link_phone` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '联系电话',
  `head_man` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '负责人姓名',
  `head_phone` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '负责人电话',
  `identity_front_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '证件正面',
  `identity_back_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '证件反面',
  `identity_handheld_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '手持证件照',
  `business_license_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '营业执照',
  `sale_count` int NULL DEFAULT 0 COMMENT '销量',
  `score` int NULL DEFAULT 0 COMMENT '评分，最大10分',
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
  `approve_time` datetime NULL DEFAULT NULL COMMENT '审批时间',
  `deleted_flag` tinyint(1) NOT NULL DEFAULT 0 COMMENT '删除标志（0代表存在 1代表删除）',
  `create_user_id` bigint NOT NULL DEFAULT 0 COMMENT '创建者',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_user_id` bigint NULL DEFAULT 0 COMMENT '更新者',
  `update_time` datetime NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `location` point NOT NULL COMMENT '经纬度',
  PRIMARY KEY (`id`) USING BTREE,
  SPATIAL INDEX `idx_homestay_location`(`location`),
  INDEX `idx_villageId`(`village_id` ASC) USING BTREE,
  INDEX `idx_heat_query`(`online` ASC, `approve_status` ASC, `deleted_flag` ASC, `heat_score` DESC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 196715 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '民宿信息-主表' ROW_FORMAT = DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;
