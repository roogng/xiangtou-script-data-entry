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

 Date: 20/06/2026 20:03:33
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for vill_homestay_room
-- ----------------------------
DROP TABLE IF EXISTS `vill_homestay_room`;
CREATE TABLE `vill_homestay_room`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '编号',
  `homestay_id` bigint NOT NULL DEFAULT 0 COMMENT '所属民宿id',
  `room_name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '房号',
  `room_type` tinyint NOT NULL COMMENT '房型（1大床房 2双人房 3亲子房 4套房 5VIP房）',
  `cover_img` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '封面图片,多张用逗号隔开',
  `introduction` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '房型简介',
  `week_day_price` decimal(10, 2) UNSIGNED NULL DEFAULT NULL COMMENT '平日价格，元',
  `holiday_price` decimal(10, 2) UNSIGNED NULL DEFAULT NULL COMMENT '假日价格，元',
  `special_day_price` decimal(10, 2) UNSIGNED NULL DEFAULT NULL COMMENT '特定日价格，元',
  `refund_rule` tinyint(1) NOT NULL DEFAULT 0 COMMENT '退订规则（0宽松 1中等 2严格）',
  `other_fee` varchar(2000) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '其他额外费用',
  `breakfast_flag` tinyint(1) NULL DEFAULT NULL COMMENT '含早（0否 1是）',
  `confirm_flag` tinyint(1) NULL DEFAULT NULL COMMENT '即时确认（0否 1是）',
  `cacel_flag` tinyint(1) NULL DEFAULT NULL COMMENT '允许取消（0否 1是）',
  `roomarea` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '房间面积',
  `max_residents` int NULL DEFAULT NULL COMMENT '最大居住人数',
  `remark` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '备注',
  `online` tinyint NOT NULL DEFAULT 0 COMMENT '0-下线 1-上线',
  `slippers` tinyint(1) NULL DEFAULT NULL COMMENT '拖鞋（0无 1有）',
  `aircondition` tinyint(1) NULL DEFAULT NULL COMMENT '空调（0无 1有）',
  `wifi` tinyint(1) NULL DEFAULT NULL COMMENT '无线网络（0无 1有）',
  `wired_network` tinyint(1) NULL DEFAULT NULL COMMENT '有线网络（0无 1有）',
  `windows` tinyint(1) NULL DEFAULT NULL COMMENT '窗户（0无 1有）',
  `lift` tinyint(1) NULL DEFAULT NULL COMMENT '电梯（0无 1有）',
  `private_bathroom` tinyint(1) NULL DEFAULT NULL COMMENT '独立卫浴（0无 1有）',
  `charge_point` tinyint(1) NULL DEFAULT NULL COMMENT '充电桩（0无 1有）',
  `park_space` tinyint(1) NULL DEFAULT NULL COMMENT '停车位（0无 1有）',
  `pay_park` tinyint(1) NULL DEFAULT NULL COMMENT '付费停车位（0无 1有）',
  `free_park` tinyint(1) NULL DEFAULT NULL COMMENT '免费停车位（0无 1有）',
  `smart_lock` tinyint(1) NULL DEFAULT NULL COMMENT '智能门锁（0无 1有）',
  `drink_water_equip` tinyint(1) NULL DEFAULT NULL COMMENT '饮水设备（0无 1有）',
  `bed_replace` tinyint(1) NULL DEFAULT NULL COMMENT '床品更换（0每天更换床品 1换客更换床品）',
  `checkin_service` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '入住服务，多个服务用逗号分隔',
  `bathroom_facilities` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '卫浴设施，多个设施用逗号分隔',
  `deleted_flag` tinyint(1) NOT NULL DEFAULT 0 COMMENT '删除标志（0代表存在 1代表删除）',
  `create_user_id` bigint NOT NULL DEFAULT 0 COMMENT '创建者',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_user_id` bigint NOT NULL DEFAULT 0 COMMENT '更新者',
  `update_time` datetime NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `approve_status` tinyint NULL DEFAULT NULL COMMENT '审批状态，0未审批，1审批中，2审批通过，3审批未通过',
  `approve_id` bigint NULL DEFAULT NULL COMMENT '审批人ID',
  `approve_remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '审批说明',
  `approve_time` datetime NULL DEFAULT NULL COMMENT '审批时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_homestayId`(`homestay_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 524281 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '民宿信息-房间信息' ROW_FORMAT = DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;
