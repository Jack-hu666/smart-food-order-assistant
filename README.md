# 外卖点餐智能 Agent

使用 Python、LangChain 和本地 Ollama 模型构建的单智能体点餐助手。用户用自然语言告诉它菜系、预算、口味、忌口和配送要求；Agent 会先补问缺失的必需信息，再依次搜索模拟餐馆、推荐菜品、核算菜品与配送费，并询问用户是否确认清单。

项目内置模拟商家和菜单，不会连接真实外卖平台，也不会实际下单。终端会显示简短决策摘要和 `Action`、`Action Input`、`Observation`、`Final Answer` 工具执行记录，不输出模型隐藏的详细推理。

## 安装与启动

安装 Python 依赖：

```bash
pip install -r requirements.txt
```

安装并启动 [Ollama](https://ollama.com/)，下载支持工具调用的默认模型：

```bash
ollama pull qwen2.5:7b
ollama serve
```

在另一个终端启动交互式 Agent：

```bash
python ollama_tool_agent.py
```

可以连续回答 Agent 的追问；输入 `exit` 退出。更换模型或 Ollama 地址：

```bash
python ollama_tool_agent.py --model qwen2.5:7b --base-url http://localhost:11434
```

## 离线演示与测试

不启动 Ollama 也能查看一段完整的模拟工具调用：

```bash
python ollama_tool_agent.py --demo
```

运行自动化工具测试：

```bash
python -m unittest -v
```

## 内置工具

- `search_restaurant(food_type, max_price, exclude_ingredient)`：按菜系、预算和忌口筛选模拟餐馆。
- `dish_recommend(restaurant_name, exclude_ingredient, max_price)`：从指定餐馆菜单中推荐符合条件的菜品。
- `calculate_total(restaurant_name, dish_names, max_budget)`：按模拟菜单和配送费计算总价，并检查是否超预算。

## 示例测试用例

用户：我想吃川菜，预算 35 元，不吃花生，推荐一份菜。

预期流程：搜索“老街川菜”并过滤含花生菜品，推荐“鱼香肉丝”，计算菜品 24 元 + 配送费 4 元 = 28 元，展示清单并询问用户是否确认。该示例可通过 `--demo` 离线运行。
