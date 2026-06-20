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

 Date: 20/06/2026 20:03:04
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for vill_goods
-- ----------------------------
DROP TABLE IF EXISTS `vill_goods`;
CREATE TABLE `vill_goods`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '编号',
  `comment_code` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '评论code',
  `goods_name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '商品名',
  `village_id` bigint NOT NULL DEFAULT 0 COMMENT '乡村id',
  `goods_status` int NULL DEFAULT NULL COMMENT '商品状态:[1:预约中,2:售卖中,3:售罄]',
  `category_id` int NOT NULL COMMENT '商品类目',
  `place` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '产地',
  `shipment` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '发货地',
  `price` decimal(10, 2) UNSIGNED NOT NULL COMMENT '价格',
  `stock_count` int NOT NULL DEFAULT 0 COMMENT '库存数量',
  `goods_imgs` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '图片，多张逗号隔开',
  `introduce` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '详情介绍',
  `introduce_html` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '详情介绍html',
  `carriage` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '运费',
  `standards` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '规格',
  `online` tinyint(1) NULL DEFAULT 0 COMMENT '0-下线 1-上线',
  `approve_status` tinyint NULL DEFAULT NULL COMMENT '审批状态，0未审批，1审批中，2审批通过，3审批未通过',
  `approve_id` bigint NULL DEFAULT NULL COMMENT '审批人ID',
  `approve_remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '审批说明',
  `approve_time` datetime NULL DEFAULT NULL COMMENT '审批时间',
  `member_id` bigint NULL DEFAULT NULL COMMENT '会员id',
  `shop_id` bigint NULL DEFAULT NULL COMMENT '店铺id，关联vill_shop表主键',
  `like_count` int NULL DEFAULT 0 COMMENT '点赞次数',
  `browse_count` int NULL DEFAULT 0 COMMENT '浏览次数',
  `share_count` int NULL DEFAULT 0 COMMENT '分享次数',
  `collect_count` int NULL DEFAULT 0 COMMENT '收藏次数',
  `heat_score` decimal(20, 6) NULL DEFAULT 10.000000 COMMENT '综合热度值（数值越高越热门）',
  `comment_count` int NULL DEFAULT 0 COMMENT '评论次数',
  `deleted_flag` tinyint(1) NOT NULL DEFAULT 0 COMMENT '删除标志（0代表存在 1代表删除）',
  `create_user_id` bigint NOT NULL DEFAULT 0 COMMENT '创建者',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',
  `update_user_id` bigint NOT NULL DEFAULT 0 COMMENT '更新者',
  `update_time` datetime NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_village_id`(`village_id` ASC) USING BTREE,
  INDEX `idx_heat_query`(`online` ASC, `approve_status` ASC, `deleted_flag` ASC, `heat_score` DESC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 192 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '村庄商品' ROW_FORMAT = DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;
