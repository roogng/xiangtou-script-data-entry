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

 Date: 20/06/2026 20:06:20
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for vill_restaurant_dish
-- ----------------------------
DROP TABLE IF EXISTS `vill_restaurant_dish`;
CREATE TABLE `vill_restaurant_dish`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '编号',
  `restaurant_id` bigint NOT NULL COMMENT '餐馆id,vill_restaurant表外键',
  `cover_img` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '菜品头像图片',
  `dish_name` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '餐品名',
  `introduction` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '菜品简介',
  `unit_price` decimal(6, 2) NULL DEFAULT 0.00 COMMENT '单价',
  `recommendation_count` int NULL DEFAULT 0 COMMENT '推荐次数',
  `deleted_flag` tinyint(1) NULL DEFAULT 0 COMMENT '删除标志（0代表存在 1代表删除）',
  `create_user_id` bigint NOT NULL DEFAULT 0 COMMENT '创建者',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_user_id` bigint NULL DEFAULT 0 COMMENT '更新者',
  `update_time` datetime NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `online` tinyint NOT NULL DEFAULT 0 COMMENT '0-下线 1-上线',
  `approve_status` tinyint NOT NULL DEFAULT 0 COMMENT '审批状态，0未审批，1审批中，2审批通过，3审批未通过',
  `approve_id` bigint NULL DEFAULT 0 COMMENT '审批人ID',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_restaurant_id`(`restaurant_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 51 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '餐馆菜品表' ROW_FORMAT = DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;
