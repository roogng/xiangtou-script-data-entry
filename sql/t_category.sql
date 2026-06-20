/*
 Navicat Premium Data Transfer

 Source Server         : loacal
 Source Server Type    : MySQL
 Source Server Version : 80013
 Source Host           : localhost:3301
 Source Schema         : vill

 Target Server Type    : MySQL
 Target Server Version : 80013
 File Encoding         : 65001

 Date: 20/06/2026 23:24:52
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for t_category
-- ----------------------------
DROP TABLE IF EXISTS `t_category`;
CREATE TABLE `t_category`  (
  `category_id` int(11) NOT NULL AUTO_INCREMENT COMMENT '分类id',
  `category_img` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '分类图片URL',
  `category_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '分类名称',
  `category_type` smallint(6) NOT NULL COMMENT '分类类型',
  `parent_id` int(11) NOT NULL COMMENT '父级id',
  `sort` int(11) NOT NULL DEFAULT 0 COMMENT '排序',
  `disabled_flag` tinyint(4) NOT NULL DEFAULT 0 COMMENT '是否禁用',
  `deleted_flag` tinyint(4) NOT NULL DEFAULT 0 COMMENT '是否删除',
  `remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`category_id`) USING BTREE,
  INDEX `idx_parent_id`(`parent_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 385 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '分类表，主要用于商品分类' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of t_category
-- ----------------------------
INSERT INTO `t_category` VALUES (361, 'public/common/8ecc243258d642f5b02afffbc0e59e72_20260325210143.png', '生鲜果蔬', 1, 0, 0, 0, 0, NULL, '2026-03-25 13:02:37', '2025-10-25 05:32:18');
INSERT INTO `t_category` VALUES (362, 'public/common/4bdfa8bc32a540b097d5055715c62f89_20260325205334.png', '牛奶乳品', 1, 0, 0, 0, 0, NULL, '2026-03-25 12:55:42', '2025-11-08 05:11:57');
INSERT INTO `t_category` VALUES (363, 'public/common/192f8a46d0764d738d8672dfc12ce844_20260325205341.png', '米面粮油', 1, 0, 0, 0, 0, NULL, '2026-03-25 12:56:50', '2025-11-08 05:12:11');
INSERT INTO `t_category` VALUES (364, 'public/common/588c896678764566afb3dfb3255335ca_20260325205341.png', '一村一品', 1, 0, 0, 0, 0, NULL, '2026-05-13 06:14:12', '2025-11-08 05:12:19');
INSERT INTO `t_category` VALUES (365, 'public/common/45450fc8331445e881bcfd8abbf90696_20260325205341.png', '茶业酒水', 1, 0, 0, 0, 0, NULL, '2026-03-25 12:56:20', '2025-11-08 05:12:31');
INSERT INTO `t_category` VALUES (366, 'public/common/968249430f8f43cf9fab9bf446446b0e_20260325205341.png', '手工艺品', 1, 0, 0, 0, 0, NULL, '2026-03-25 12:56:03', '2025-11-08 05:12:42');
INSERT INTO `t_category` VALUES (367, NULL, '肉类', 1, 361, 0, 0, 0, NULL, '2025-11-08 05:13:28', '2025-11-08 05:13:28');
INSERT INTO `t_category` VALUES (368, NULL, '水果', 1, 361, 0, 0, 0, NULL, '2025-11-08 05:13:34', '2025-11-08 05:13:34');
INSERT INTO `t_category` VALUES (369, NULL, '蔬菜', 1, 361, 0, 0, 0, NULL, '2025-11-08 05:13:38', '2025-11-08 05:13:38');
INSERT INTO `t_category` VALUES (370, NULL, '牛奶', 1, 362, 0, 0, 0, NULL, '2025-11-08 05:14:08', '2025-11-08 05:14:08');
INSERT INTO `t_category` VALUES (371, NULL, '羊奶', 1, 362, 0, 0, 0, NULL, '2025-11-08 05:14:30', '2025-11-08 05:14:30');
INSERT INTO `t_category` VALUES (372, NULL, '谷类', 1, 363, 0, 0, 0, NULL, '2025-11-08 05:15:05', '2025-11-08 05:15:05');
INSERT INTO `t_category` VALUES (373, NULL, '面粉', 1, 363, 0, 0, 0, NULL, '2025-11-08 05:15:11', '2025-11-08 05:15:11');
INSERT INTO `t_category` VALUES (374, NULL, '食用油', 1, 363, 0, 0, 0, NULL, '2025-11-08 05:15:52', '2025-11-08 05:15:52');
INSERT INTO `t_category` VALUES (375, NULL, '果干', 1, 364, 0, 0, 0, NULL, '2025-11-08 05:16:18', '2025-11-08 05:16:18');
INSERT INTO `t_category` VALUES (376, NULL, '炒货', 1, 364, 0, 0, 0, NULL, '2025-11-08 05:16:26', '2025-11-08 05:16:26');
INSERT INTO `t_category` VALUES (377, NULL, '烘培类', 1, 364, 0, 0, 0, NULL, '2025-11-08 05:17:08', '2025-11-08 05:17:08');
INSERT INTO `t_category` VALUES (378, NULL, '陶瓷', 1, 366, 0, 0, 0, NULL, '2025-11-08 05:17:35', '2025-11-08 05:17:35');
INSERT INTO `t_category` VALUES (379, NULL, '藤类', 1, 366, 0, 0, 0, NULL, '2025-11-08 05:17:47', '2025-11-08 05:17:47');
INSERT INTO `t_category` VALUES (380, NULL, '布艺', 1, 366, 0, 0, 0, NULL, '2025-11-08 05:17:59', '2025-11-08 05:17:59');
INSERT INTO `t_category` VALUES (381, NULL, '茶叶', 1, 365, 0, 0, 0, NULL, '2025-11-08 05:18:19', '2025-11-08 05:18:19');
INSERT INTO `t_category` VALUES (382, NULL, '酒类', 1, 365, 0, 0, 0, NULL, '2025-11-08 05:18:25', '2025-11-08 05:18:25');
INSERT INTO `t_category` VALUES (383, NULL, '饮用水', 1, 365, 0, 0, 0, NULL, '2025-11-08 05:18:39', '2025-11-08 05:18:39');
INSERT INTO `t_category` VALUES (384, NULL, '蛋类', 1, 363, 0, 0, 0, NULL, '2025-11-08 05:19:20', '2025-11-08 05:19:20');

SET FOREIGN_KEY_CHECKS = 1;
