# 江南景观细化：2026-09-28

本轮从 main `13bfb3e` 接续，主场景布局和十个诊断机位保持原样。

## 模型变化

| 项目 | 基线 | 本轮候选 |
|---|---:|---:|
| 场景三角面 | 335,280 | 375,968 |
| 网格部件 | 10,433 | 10,322 |
| 庭院及外围树 | 5 棵球状叶团树 | 5 棵渐细枝干树，5,880 片折面叶片 |
| 岸边蕨草 | 0 | 7 簇 |
| 运河表面 | 平面 | 12,800 面浅波网格 |

树木分为枝干、深浅叶片三个材质批次，增加实际细节同时减少对象数。

首次原生 Blender 十机位图包（run 74）验证通过，但目视发现叶片发白。已修正植物纯色从 sRGB 调色板到 glTF 线性颜色的转换，并检查导出值。

首次几何预览显示树冠过稀，第二轮加密了侧生小枝与叶片，同时将枝干从家具木纹材质改为独立粗糙树皮材质。树冠没有随细化扩张进回廊保留区。

## 复现

```bash
python -m pip install -r requirements-ci.txt
python ci/prepare_workspace.py
python .ci_work/build_scene.py
python .ci_work/refine_ming.py
python .ci_work/validate_ming.py
python ci/validate_review_contract.py
python ci/validate_landscape.py
blender --background --python-exit-code 1 --python ci/blender_diagnostic.py -- --input .ci_work/ming_review.glb --output diagnostics
python ci/make_contact_sheet.py diagnostics
python ci/validate_diagnostics.py diagnostics
```

无显示器的 Linux 主机使用 `xvfb-run -a blender ...`。默认仍为十张 720×480 Eevee 诊断图。局部复核可传 `--views 03_courtyard,06_tree_clearance`；局部输出不能代替完整十机位验收。

## 验证与边界

- 本地模型重建、GLB 回读、十张嵌入纹理及既有 PBR 合同通过。
- 景观检查覆盖树冠高度、回廊保留区、码头/桥头/主入口避让，以及运河波高和岸线。
- `render_manifest.json` 为每轮图片记录 GLB 哈希、源码哈希和剖视时隐藏的对象类别。
- 标准 room Form 验证器仍报告既有证据路径、开口 mask/cutter 和人工审批等缺项。本轮不将脚本通过改写为完整 Form 或 Runtime 批准。
- 原有屋面、盆景、建筑接缝和灯光仍有精修空间。这是低成本建模诊断，不是最终高成本 Cycles 成片。
- `blender-preview-*` 为轻量图包；完整可编辑 `.blend` 在 `blender-diagnostic-*` 中。

## 后续建议

继续检查盆栽的球状叶团、回廊盆器的支承接触与屋顶交接缝，再进入最终材质细化。优先修可从图片核实的问题，不以资产数量替代画面质量。
