# 明式构件细化与临园茶亭扩建

## 审美与工程范围

沿用江南临水客栈的白墙、黛瓦和温润木色。明式线条、结构与装饰的统一作为艺术方向；《营造法式》的模数思路作为构造参考，不宣称宋式官建筑与明式民居是同一制度，不宣称测绘复原。

参考：
- 故宫《营造法式》：https://www.dpm.org.cn/ancient/mingqing/149329.html
- 故宫黄花梨木镶乌木边条案（侧脚、收分、牙子、线脚）：https://www.dpm.org.cn/collection/gear/230533.html

## 第一轮：承托关系与轮廓

- 16 处层叠柱础：方形下枋、鼓形承托、收口柱颈。
- 24 件曲线雀替：梁下贴合、柱侧相接，局部边线随曲线延伸。
- 12 组斗拱：替换方盒堆叠，使用实体弧形拱、承托块、正交拱及顶枋。
- 四翼八道檐口：连续封檐板、露椽尾和圆瓦当几何。
- 参数化构件存放于 `source/architecture_detail.py`；无外部模型、无付费API。

## 约束

沿用十机位720×480 Eevee快速审阅。新增构件通过闭合性、绕序及有限坐标检查；整场景检查柱础对应、雀替与梁相交、头部净空、景观与主入口边界。

本次细化的工作场景上限为450,000三角面，用于诊断渲染；旧 `room-brief.json` 的200,000三角面Runtime目标仍未满足。不得把临时工作上限解释为用户批准提高Runtime预算，后续需LOD/实例化/合批。

现存 `room-layout.json` 和完整Form/Runtime证据仍需与当前程序化源码对齐。本轮不修改历史审批、不声称通过最终Form或Runtime门禁。最终交付仍是审阅模型。

## 复现

```sh
python ci/prepare_workspace.py
python .ci_work/build_scene.py
python .ci_work/refine_ming.py
python .ci_work/validate_ming.py
python ci/validate_review_contract.py
python ci/validate_landscape.py
python ci/validate_architecture.py
xvfb-run -a blender --background --python ci/blender_diagnostic.py -- --input .ci_work/ming_review.glb --output diagnostics
```

完整技能Form检查已运行，仍因旧证据文件路径缺失、开口mask/cutter和正式人工批准缺失而失败；本轮只继续用户明确授权的低成本建模诊断闭环，不越过正式发布门禁。

云端run79定位到新闭合法线修复调用依赖SciPy图连通性分析，而旧requirements未声明。已显式补上SciPy与NetworkX，防止仅在预装完整依赖的本地环境通过。

## 第二轮：东侧临园茶亭

新建4.2×4米平台，四柱、四向承梁、实体四坡顶、露椽、栏杆、台阶、通向桥岸的铺石路；北侧长凳与两只坐凳围绕茶桌。南入口保留1.9米宽审阅净空，桌椅不进入入口区。屋脊约4.44米，低于客栈主楼。

茶亭屋面为闭合网格，四坡拼合；柱脚、梁底雀替接触和入口通道均检查实际导出坐标。对称轴x=21.2，北侧长凳因坐赏功能作有意不对称。家具高度与支承接触来自同一米制构件参数。

十机位中的04/07本轮轮换为茶亭外观与檐下细节，主入口、全景、水岸、庭院和原有08/09梁柱檐口机位继续保留。没有增加到36机位。

第二轮Blender审阅还会对灯笼、柱础鼓部、茶杯和坐凳等回转表面合并重合顶点并平滑法线，保留UV接缝，消除低模三角面在柔和曲面上的明暗断裂。这是可复现的Blender材质/法线处理，不是新生成的贴图。

## 第一轮实际审阅（run80）

十张Blender 4.x Eevee图与全部CI检查通过。08视角可辨认柱础台阶和弧形雀替，09可见连续封檐板与椽尾；新增构件未观察到悬空。仍可见旧灯笼三角棱面和上层球形盆叶：本轮仅平滑前者，后者保留为后续独立资产细化项。该目视审阅不是人工Form批准。

本地衍生PNG曾出现截断；准备阶段改为内存完整编码、临时文件原子替换并实际解码检查，避免把不完整贴图送入后续构建。
