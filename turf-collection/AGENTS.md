# 地皮合集

独立收录用户点名的 11 个模组的地皮，不改动创意工坊来源副本。实现和沟通使用中文。

- 先读 `DEVELOPMENT_STATUS.md` 和 `README.md`，验收走根目录 `tools/DST_TESTING.md`。
- `scripts/turf_collection_catalog.lua`、`scripts/turf_collection_assets.lua`、`SOURCES.json` 由 `tools/turf-collection/` 生成；变更来源后重新抽取与验收。
- 所有 tile / prefab / 图标 / 自定义地纹与边缘遮罩使用 `tc_` 命名空间。动画保留来源 build / bank 名称。
- 不复制原模组的世界生成、角色、商店、RPC、桥梁/平台组件或付费皮肤系统。特殊支持地形转换为普通可铺挖陆地地纹，差异必须记录。
- 只把真实注册的地皮算入覆盖；未注册测试贴图、实体地毯、皮肤不混入地皮数量。
- 修改运行源码或验证状态时更新 `DEVELOPMENT_STATUS.md`；未获得客户端证据不得宣称完整通过。
