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

 Date: 20/06/2026 20:03:21
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for vill_dynamics
-- ----------------------------
DROP TABLE IF EXISTS `vill_dynamics`;
CREATE TABLE `vill_dynamics`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '编号',
  `comment_code` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '评论code,关联评论表',
  `context` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '动态内容',
  `cover` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '封面url，一张图',
  `img_url` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '图片，或视频，多个用逗号链接',
  `homestay_id` bigint NOT NULL DEFAULT 0 COMMENT '链接到民宿,民宿id',
  `goods_id` bigint NOT NULL DEFAULT 0 COMMENT '链接到土特产,商品id',
  `village_id` bigint NOT NULL DEFAULT 0 COMMENT '链接到村，村id',
  `remind_ids` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '提醒谁看，多用户id，逗号分隔',
  `topic` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '话题，多个，用逗号分隔',
  `latitude` decimal(10, 6) NULL DEFAULT NULL COMMENT '经度',
  `longitude` decimal(10, 6) NULL DEFAULT NULL COMMENT '维度',
  `member_id` bigint NOT NULL COMMENT '会员ID',
  `browse_count` int NULL DEFAULT 0 COMMENT '浏览次数',
  `like_count` int NULL DEFAULT 0 COMMENT '点赞次数',
  `comment_count` int NULL DEFAULT 0 COMMENT '评论次数',
  `share_count` int NULL DEFAULT 0 COMMENT '分享次数',
  `collect_count` int NULL DEFAULT 0 COMMENT '收藏次数',
  `heat_score` decimal(20, 6) NULL DEFAULT 10.000000 COMMENT '综合热度值（数值越高越热门）',
  `online` tinyint NOT NULL DEFAULT 0 COMMENT '0-下线 1-上线',
  `recommend` tinyint(1) NOT NULL DEFAULT 0 COMMENT '推荐：0-否，1-是',
  `approve_status` tinyint NULL DEFAULT 0 COMMENT '审批状态，0未审批，1审批中，2审批通过，3审批未通过',
  `approve_id` bigint NULL DEFAULT NULL COMMENT '审批人ID',
  `approve_remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '审批说明',
  `deleted_flag` tinyint(1) NOT NULL DEFAULT 0 COMMENT '删除标志（0代表存在 1代表删除）',
  `create_user_id` bigint NOT NULL DEFAULT 0 COMMENT '创建者',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',
  `update_user_id` bigint NOT NULL DEFAULT 0 COMMENT '更新者',
  `update_time` datetime NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_heat_query`(`online` ASC, `approve_status` ASC, `deleted_flag` ASC, `heat_score` DESC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 336 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '会员动态表' ROW_FORMAT = DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;
