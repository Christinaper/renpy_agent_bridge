# A11y-RenPy-Bridge - Project Context

**当前版本:** v0.2.0  
**最后更新:** 2026-05-15  
**状态:** 技术验证完成，可发布

---

## 快速理解这个项目

### 一句话
让AI Agent通过JSON（而非像素）玩Ren'Py视觉小说游戏。

### 核心成就（v0.2）
- ✅ 16个turn完整通关
- ✅ LLM做决策（llama3.2:1b via Ollama）
- ✅ 100%成功率，无需人工干预
- ✅ 协议简洁：state.json ↔ action.json

### 关键文件
1. **game/a11y.rpy** - Ren'Py侧协议实现
2. **agent/simple_player.py** - Agent侧实现
3. **docs/handoff-v0.2.md** - 完整技术报告
4. **docs/schema.json** - JSON格式定义

---

## 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| 游戏引擎 | Ren'Py | 8.3+ |
| Agent语言 | Python | 3.8+ |
| LLM运行时 | Ollama | latest |
| LLM模型 | llama3.2:1b | - |
| 通信方式 | 文件轮询 | JSON |

---

## 架构速览

Ren'Py → state.json → Agent读取 → LLM决策 →
Agent写action.json → Ren'Py消费 → 推进游戏 → 循环

**关键机制:**
- `turn_id`: 握手同步
- `mode`: 状态机（idle/awaiting_action/finished）
- `actions[]`: 可用动作列表（advance/choice）

---

## 已知问题（v0.2可接受）

1. **UI阻塞** - `wait_for_action()`阻塞主线程
2. **手动清理** - 每次运行前需删除exports/*
3. **narrative重复** - choice点的current_text被清空

详见 `docs/handoff-v0.2.md#已知限制`

---

## 下一步方向（v0.3候选）

### 推荐优先级

**P0 (必须):**
- Session ID隔离（解决手动清理问题）
- choice_context字段（数据质量）

**P1 (应该):**
- 非阻塞UI（用户体验）
- 错误恢复（鲁棒性）

**P2 (可选):**
- Debug overlay
- Web API替代文件轮询

详见 `docs/v0.3-roadmap.md`

---

## 开发环境

**我的配置:**
- Windows 11 宿主
- Ren'Py在 `D:\02_Dev\Projects\Games\a11y_renpy_bridge`
- Agent在WSL2 Ubuntu
- Ollama在WSL2

**文件路径映射:**

Windows: D:\02_Dev\Projects\Games\a11y_renpy_bridge\game\exports
WSL2:    /mnt/d/02_Dev/Projects/Games/a11y_renpy_bridge/game/exports

---

## 快速命令

```bash
# 清空状态
rm -rf game/exports/*

# 启动游戏（Windows）
.\renpy.exe game

# 启动Agent（WSL2）
cd agent && python3 simple_player.py

# 查看最终状态
cat game/exports/state.json | grep -o '"mode": "[^"]*"'
```

---

## 待办事项

### 立即
- [ ] 发布到GitHub
- [ ] 写README
- [ ] 录制demo视频

### 本周
- [ ] 收集相关文献
- [ ] 规划v0.3技术路线
- [ ] （可选）写博客

### 下周+
- [ ] 决定是否做v0.3
- [ ] 或转向论文写作

---

## 联系人

**主要开发者:** saki
**项目开始:** 2026-05-08  
**当前阶段:** Week 2完成  

---

## 给下一个AI助手的话

这个项目的核心价值是**证明非像素接口可行**，不是做最强AI。

v0.2已经完成技术验证，不要被功能诱惑过度设计。

如果要做v0.3，先问："这对发论文/开源/找工作有帮助吗？"

**优先级:** 文档 > 演示 > 新功能

爱这个项目的人。❤️