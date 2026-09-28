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
