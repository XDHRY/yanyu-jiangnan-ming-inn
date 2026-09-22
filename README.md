# 烟雨江南·临水客栈：明式精细化审阅版

本轮接续已有客栈模型，不替换为另一项目。源建筑：`adc0ebe5c8134af780ea7a`；一层 `f4724a45a74a4d0db8a962`；二层 `8d2c6482546c427b845efb`。主体18×14米，层高2.7米。两份 `source_walkmyplan_*.json` 保存本轮读取的在线实测结构；`ground.json/upper.json` 是此前独立模型采用的数据，二者不应混称同步双向编辑。

## 看什么

- `ming_review.html`：离线可旋转的材质审阅，含屋顶/二层开关与白模。
- `ming_review.glb`：含UV、嵌入贴图的可编辑审阅模型。
- `review/tea_room.png`、`review/joinery.png`：本轮新构件的实际模型预览。
- `review/overview.png`、`review/courtyard.png`：模型总览。
- 根目录保留6张早期AI材质原稿；`asset_library_hires/textures/` 另有20张768px材质参考。以文件实际像素尺寸为准，不称为4K/8K扫描。
- `source/refine_ming.py`：可重复生成精细化构件和UV的权威源码。
- `ci/blender_diagnostic.py`：原生Blender低成本10机位诊断入口；仓库公开后由 GitHub Actions 自动执行。

## 美术方向

本项目是明式审美启发的创作，非文物级历史复原。高级感由修长的框架、木纹方向、细小压边、密而有序的窗棂、克制的金属装饰与孔雀青织锦共同构成。白墙、灰瓦和青石承担安静背景；华丽集中在近景木作与陈设。

| 材质原稿 | 构件用途 | 本轮状态 |
|---|---|---|
| huanghuali.png | 木框、圈椅、茶桌、柜体 | 已绑定模型UV |
| lotus_panel.png | 隔扇裙板、柜门下部面板 | 已绑定；图中雕刻尚为二维表现 |
| teal_brocade.png | 圈椅坐垫与客房织物 | 已绑定模型UV |
| lime_plaster.png | 墙体灰泥 | 已绑定模型UV |
| blue_limestone.png | 铺地、石作与桥体 | 已绑定模型UV |
| lacquer_gold_trim.png / tex_lacquer_black_gold.jpg | 入口牌匾、黑漆描金构件 | 已进入本轮CI材质绑定；公开仓库首轮构建后验证 |
| tex_brass_aged.jpg | 牌匾边框、吊链、金属件 | 已进入本轮CI材质绑定；公开仓库首轮构建后验证 |

## 实际几何

窗棂由真实杆件组成，孔洞可穿视。隔扇具有边框、镂空上部、实体下裙板、细金属压线与合页；茶室和楼上雅集厅各布置五扇壁前隔扇、茶桌与四把圈椅。圈椅包含连续弧形搭脑/扶手、靠背、支撑、腿、横枨及织锦坐垫。柜门增设独立边框与装饰面板。保持原有天井开口、回廊、楼梯洞口、月洞门、码头与石桥。本轮进一步把斗拱、入口黑漆描金牌匾和南檐雨链固化到权威场景生成器，不再只作为诊断叠加物。

## 运行

```bash
python -m pip install -r requirements-ci.txt
python ci/prepare_workspace.py
python .ci_work/build_scene.py
python .ci_work/refine_ming.py
python .ci_work/validate_ming.py
```

原生 Blender 诊断由 `.github/workflows/blender-diagnostic.yml` 执行，输出10张720×480诊断图、验证报告与打包 `.blend`。`ci/review_matrix.json` 规定每个机位的审阅目标。

打开 `ming_review.html`。离线浏览器需支持WebGL2与DecompressionStream；生成静态预览需要EGL。脚本重建会覆盖生成文件，不覆盖原始贴图。

本地具备 Blender 时可复现诊断：

```bash
blender --background --python ci/blender_diagnostic.py -- --input .ci_work/ming_review.glb --output diagnostics
python ci/validate_diagnostics.py diagnostics
```

## 验证边界

预览来自模型真实三角面与贴图，经简单OpenGL着色输出；不是AI场景概念图，也不是Cycles最终光追结果。贴图未做无缝接缝认证，非扫描PBR套图，无伪造法线/位移文件。雕花源图不能证明真实雕刻深度。屋面、植被、倒角、近景接缝和最终灯光仍需继续精修。保留原先的待审阅门禁，不把脚本运行成功写成人工批准。

本轮不调用付费 Meshy。GitHub Actions 工作流已加入公开仓库门禁：仓库仍为 private 时 job 自动跳过；可见性切换为 public 后，`public` 事件会启动首轮 Blender 诊断。当前报告中的“5张嵌入纹理”属于上一次已生成结果；新一轮预计增加黑漆描金与老黄铜两类纹理，必须以公开后实际 CI 产物为准。
