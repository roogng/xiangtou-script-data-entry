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

 Date: 20/06/2026 20:01:43
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for vill_village
-- ----------------------------
DROP TABLE IF EXISTS `vill_village`;
CREATE TABLE `vill_village`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '编号',
  `village_name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '村名字',
  `area_code` bigint NULL DEFAULT 0 COMMENT '行政代码',
  `session_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '村群聊，会话id',
  `province_id` bigint NOT NULL DEFAULT 0 COMMENT '省id',
  `province_name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '省份',
  `city_id` bigint NOT NULL DEFAULT 0 COMMENT '城市id',
  `city_name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '城市名',
  `area_id` bigint NOT NULL DEFAULT 0 COMMENT '区id',
  `area_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '地区名',
  `street_id` bigint NOT NULL COMMENT '所属街道id',
  `street_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '所属街道名',
  `address` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '详细地址',
  `contact_phone` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '村委会联系电话',
  `village_head_id` bigint NULL DEFAULT 0 COMMENT '村长id',
  `head_name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '村长名',
  `head_cover` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '村长照片',
  `head_introduction` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '村长简介',
  `head_introduction_html` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '村长简介html',
  `village_tag` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '乡村标签，逗号分隔',
  `introduce` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '村简介',
  `notice` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '村公告',
  `entire_cover_img` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '整村风貌',
  `scenic_cover_img` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '景区照片',
  `street_cover_img` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '主要街道',
  `home_cover_img` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '住宿照片',
  `agritainment_cover_img` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '农家乐照片',
  `nature_cover_img` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '自然风景区照片',
  `deleted_flag` tinyint(1) NULL DEFAULT 0 COMMENT '删除标志（0代表存在 1代表删除）',
  `create_user_id` bigint NOT NULL DEFAULT 0 COMMENT '创建者',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',
  `update_user_id` bigint NULL DEFAULT 0 COMMENT '更新者',
  `update_time` datetime NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `member_count` bigint NULL DEFAULT 0 COMMENT '村民数',
  `activity_count` bigint NULL DEFAULT 0 COMMENT '活动数',
  `travel_count` bigint NULL DEFAULT 0 COMMENT '旅游路线数量',
  `job_count` bigint NULL DEFAULT 0 COMMENT '用工就业数量',
  `sages_count` bigint NULL DEFAULT 0 COMMENT '村贤数量',
  `homestay_count` bigint NULL DEFAULT 0 COMMENT '民宿数量',
  `goods_count` bigint NULL DEFAULT 0 COMMENT '土特产数量',
  `img_count` bigint NULL DEFAULT 0 COMMENT '村景数量',
  `project_count` bigint NULL DEFAULT 0 COMMENT '合作项目数量',
  `donation_count` bigint NULL DEFAULT 0 COMMENT '捐款数量',
  `adopt_count` bigint NULL DEFAULT 0 COMMENT '认养数量',
  `restaurant_count` bigint NULL DEFAULT 0 COMMENT '农庄数量',
  `attraction_count` bigint NULL DEFAULT 0 COMMENT '景区数量',
  `recommend` int NULL DEFAULT 0 COMMENT '是否推荐，推荐排序(0不推荐，大于0按照从大到小排序)',
  `location_point` point NOT NULL,
  `lng` decimal(10, 6) GENERATED ALWAYS AS (round(st_x(`location_point`),6)) STORED NULL,
  `lat` decimal(10, 6) GENERATED ALWAYS AS (round(st_y(`location_point`),6)) STORED NULL,
  `approve_status` tinyint NULL DEFAULT 0 COMMENT '审批状态，0未审批，1审批中，2审批通过，3审批未通过',
  `approve_id` bigint NULL DEFAULT 0 COMMENT '审批人ID',
  `approve_remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '审批说明',
  `approve_time` datetime NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '审批时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ind_streetid`(`street_id` ASC) USING BTREE,
  INDEX `ind_recommend`(`recommend` DESC) USING BTREE,
  INDEX `idx_lng_lat`(`lng` ASC, `lat` ASC) USING BTREE,
  INDEX `idx_village_name`(`village_name` ASC) USING BTREE,
  INDEX `ind_proid`(`province_id` ASC) USING BTREE,
  INDEX `ind_cityid`(`city_id` ASC) USING BTREE,
  INDEX `ind_areaid`(`area_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 655355 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '村庄信息表' ROW_FORMAT = DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;
