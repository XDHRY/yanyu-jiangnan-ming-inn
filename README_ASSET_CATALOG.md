# 烟雨江南 · 明式临水客栈资产批次

本批次针对“树形不够好、屋顶与二楼接缝偏宽、整体不够精致”的反馈完成了几何与资产修订。

## 本次几何修订

- 屋面外挑收窄到约 0.25 m，并新增连续的 `roof_wall_plate` 压缝梁；檐口、墙压顶和山墙底线在同一高度关系内收口。
- 上层廊檐改为更薄的坡度关系，避免二楼与屋面之间出现宽缝。
- 树改为渐细主干 + 六组主枝/次枝 + 分层小叶簇，保留江南庭院的疏朗视线，不再使用八个大球状叶团。
- 重新生成 `ming_review.glb`、`ming_review.html` 与四张审阅图；Function gate 已通过，Form/Runtime 仍保持待原生 Blender/浏览器审阅。

## 资产库

`generated_assets/manifest.json` 记录了 65 张高精度参考图：20 件明式道具、15 件建筑构件、10 件庭院/水岸环境、20 张可平铺材质。每一张图均保留生成类别、用途与约束；代表性树、斗拱、锦缎和圈椅已做视觉抽查。

`asset_library/` 是可直接在 GitHub 中浏览的轻量预览目录（384 px JPEG），保持 65 个一一对应的文件名；原始 PNG 在本地工程 `generated_assets/` 中保留。

## 生成与费用边界

本批次使用 OpenAI 内置 imagegen 生成参考图；没有提交任何付费 Meshy 任务，也没有消耗 Meshy credits。`props.json` 只保留后续可选的 Meshy-5 资产合同与护栏，真正的 Image-to-3D 提交需在 Form gate 前单独确认预算。
