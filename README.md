# 🍜 Smart Food Order Assistant · 智能点餐助手

> 基于 **Python**、**LangChain** 与本地 **Ollama** 模型构建的单智能体外卖点餐助手。

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/LangChain-0.3+-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white" alt="LangChain">
  <img src="https://img.shields.io/badge/Ollama-Local-orange?style=for-the-badge&logo=ollama&logoColor=white" alt="Ollama">
  <img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License">
</p>

用户用自然语言告诉它想吃什么、预算多少、口味与忌口如何；信息不全时，Agent 会**先补问缺失的必需信息**，再依次搜索模拟餐馆、推荐菜品、核算菜品与配送费，最后展示点餐清单并询问是否确认。

> ⚠️ 项目内置**模拟商家与菜单**，不会连接真实外卖平台，也不会实际下单。

---

## 📖 目录

- [✨ 功能特性](#-功能特性)
- [🧰 内置工具](#-内置工具)
- [🍽️ 模拟数据](#️-模拟数据)
- [🚀 快速开始](#-快速开始)
- [🎬 离线演示](#-离线演示)
- [🧪 运行测试](#-运行测试)
- [💬 示例对话](#-示例对话)
- [📁 项目结构](#-项目结构)
- [🛠️ 技术栈](#️-技术栈)
- [📄 许可证](#-许可证)

---

## ✨ 功能特性

- **多轮对话补全信息**：菜系、预算、忌口任一项缺失时，先用中文追问，不猜测、不编造。
- **严格工具调用链**：按 `search_restaurant → dish_recommend → calculate_total` 顺序执行，防止越界调用。
- **忌口过滤**：搜索与推荐阶段都会过滤含忌口食材的菜品。
- **预算校验**：总预算包含配送费；超预算时自动尝试去掉部分菜品并说明原因。
- **两种运行模式**：
  - 🟢 真实 Agent 模式：连接本地 Ollama 模型对话；
  - 🔵 离线 `--demo` 模式：无需 Ollama，直接回放一段完整示例。

---

## 🧰 内置工具

| 工具 | 说明 | 关键参数 |
| --- | --- | --- |
| `search_restaurant` | 按菜系、预算和忌口筛选模拟餐馆 | `food_type`、`max_price`、`exclude_ingredient` |
| `dish_recommend` | 从指定餐馆菜单推荐符合条件的菜品 | `restaurant_name`、`exclude_ingredient`、`max_price` |
| `calculate_total` | 计算菜品小计、配送费与总价并核验预算 | `restaurant_name`、`dish_names`、`max_budget` |

终端会以简短决策摘要展示工具执行记录：

```
Thought: 根据已收集的点餐条件执行下一步（简要决策摘要）
Action: search_restaurant
Action Input: {"food_type": "川菜", "max_price": 35, "exclude_ingredient": "花生"}
Observation: {...}
```

> 出于安全与可读性考虑，模型隐藏的详细推理不会输出。

---

## 🍽️ 模拟数据

内置 4 家模拟餐馆（数据不代表真实门店或实时价格）：

| 餐馆 | 菜系 | 配送费 | 示例菜品 |
| --- | --- | --- | --- |
| 老街川菜 | 川菜 / 中餐 / 辣味 | ¥4.0 | 宫保鸡丁、鱼香肉丝、清炒时蔬 |
| 江南小馆 | 江浙菜 / 中餐 / 清淡 | ¥3.5 | 清蒸鲈鱼、香菇青菜、番茄炒蛋 |
| 麦田汉堡 | 西式快餐 / 汉堡 / 西餐 | ¥5.0 | 经典牛肉汉堡、香煎鸡腿堡、薯条 |
| 清真兰州面 | 面食 / 牛肉面 / 西北菜 | ¥2.5 | 红烧牛肉面、素拌面 |

---

## 🚀 快速开始

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 2. 安装并启动 Ollama

前往 [Ollama 官网](https://ollama.com/) 安装，然后下载支持工具调用的默认模型并启动服务：

```bash
ollama pull qwen2.5:7b
ollama serve
```

### 3. 启动交互式 Agent

```bash
python ollama_tool_agent.py
```

启动后即可用自然语言连续对话，输入 `exit` 退出。如需更换模型或 Ollama 地址：

```bash
python ollama_tool_agent.py --model qwen2.5:7b --base-url http://localhost:11434
```

---

## 🎬 离线演示

无需启动 Ollama，直接查看一段完整的模拟工具调用：

```bash
python ollama_tool_agent.py --demo
```

---

## 🧪 运行测试

项目内置自动化工具测试：

```bash
python -m unittest -v
```

---

## 💬 示例对话

```
用户：我想吃川菜，预算 35 元，不吃花生，推荐一份菜。

预期流程：
1. search_restaurant   → 筛选出「老街川菜」，过滤含花生的菜品
2. dish_recommend      → 推荐「鱼香肉丝」（¥24）
3. calculate_total     → 小计 ¥24 + 配送费 ¥4 = 总计 ¥28 ✅ 未超预算
4. 展示清单并询问用户是否确认
```

该示例可通过 `--demo` 离线运行。

---

## 📁 项目结构

```
.
├── ollama_tool_agent.py        # Agent 主程序（工具定义 + 对话循环 + 离线演示）
├── test_ollama_tool_agent.py   # 模拟工具的离线单元测试
├── requirements.txt            # Python 依赖
├── 项目说明.md                  # 简要项目说明
├── LICENSE                     # MIT 许可证
└── README.md
```

---

## 🛠️ 技术栈

- **Python 3.10+**
- **LangChain**（`langchain-core` / `langchain-ollama`）
- **Ollama**（本地模型，默认 `qwen2.5:7b`）
- **Pydantic**（工具参数校验）

---

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源。
