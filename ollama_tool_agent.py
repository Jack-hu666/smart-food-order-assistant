"""基于 LangChain 和 Ollama 的模拟外卖点餐 Agent。

运行方式：
    python ollama_tool_agent.py
    python ollama_tool_agent.py --demo

真实 Agent 需要先启动 Ollama，并下载默认模型 qwen2.5:7b。
--demo 使用固定示例，不需要 Ollama 服务。
"""

from __future__ import annotations

import argparse
from itertools import combinations
import json
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field


class RestaurantSearchInput(BaseModel):
    """餐馆搜索所需条件。"""

    food_type: str = Field(description="用户想吃的菜系或食物类型")
    max_price: float = Field(ge=0, description="用户可接受的总预算上限，人民币")
    exclude_ingredient: str = Field(default="", description="忌口食材；没有忌口时传空字符串")


class DishRecommendInput(BaseModel):
    """菜品推荐所需条件。"""

    restaurant_name: str = Field(description="餐馆名称，必须来自餐馆搜索结果")
    exclude_ingredient: str = Field(default="", description="忌口食材；没有忌口时传空字符串")
    max_price: float = Field(default=100000, ge=0, description="菜品预算上限")


class CalculateTotalInput(BaseModel):
    """订单试算所需条件。"""

    restaurant_name: str = Field(description="餐馆名称")
    dish_names: list[str] = Field(min_length=1, description="要计算价格的菜品名称列表")
    max_budget: float = Field(ge=0, description="用户总预算上限，人民币")


# 这是用于演示的模拟商家和菜单，不代表真实门店或实时价格。
RESTAURANTS = [
    {
        "name": "老街川菜",
        "food_types": ["川菜", "中餐", "辣味"],
        "delivery_fee": 4.0,
        "dishes": [
            {"name": "宫保鸡丁", "price": 26.0, "ingredients": ["鸡肉", "花生", "辣椒"]},
            {"name": "鱼香肉丝", "price": 24.0, "ingredients": ["猪肉", "木耳", "辣椒"]},
            {"name": "清炒时蔬", "price": 16.0, "ingredients": ["青菜", "大蒜"]},
        ],
    },
    {
        "name": "江南小馆",
        "food_types": ["江浙菜", "中餐", "清淡"],
        "delivery_fee": 3.5,
        "dishes": [
            {"name": "清蒸鲈鱼", "price": 32.0, "ingredients": ["鲈鱼", "姜"]},
            {"name": "香菇青菜", "price": 18.0, "ingredients": ["香菇", "青菜"]},
            {"name": "番茄炒蛋", "price": 20.0, "ingredients": ["番茄", "鸡蛋"]},
        ],
    },
    {
        "name": "麦田汉堡",
        "food_types": ["西式快餐", "汉堡", "西餐"],
        "delivery_fee": 5.0,
        "dishes": [
            {"name": "经典牛肉汉堡", "price": 28.0, "ingredients": ["牛肉", "小麦", "芝士"]},
            {"name": "香煎鸡腿堡", "price": 25.0, "ingredients": ["鸡肉", "小麦"]},
            {"name": "薯条", "price": 12.0, "ingredients": ["土豆"]},
        ],
    },
    {
        "name": "清真兰州面",
        "food_types": ["面食", "牛肉面", "西北菜"],
        "delivery_fee": 2.5,
        "dishes": [
            {"name": "红烧牛肉面", "price": 22.0, "ingredients": ["牛肉", "小麦"]},
            {"name": "素拌面", "price": 17.0, "ingredients": ["小麦", "黄瓜"]},
        ],
    },
]


def _matches_exclusion(dish: dict[str, Any], exclude_ingredient: str) -> bool:
    """检查菜品是否包含用户忌口的食材。"""
    excluded = exclude_ingredient.strip().casefold()
    if not excluded or excluded in {"无", "没有", "无忌口", "不忌口", "none"}:
        return False
    return any(excluded in ingredient.casefold() for ingredient in dish["ingredients"])


def _json(data: Any) -> str:
    """将工具结果转为便于模型读取的中文 JSON。"""
    return json.dumps(data, ensure_ascii=False)


@tool(args_schema=RestaurantSearchInput)
def search_restaurant(food_type: str, max_price: float, exclude_ingredient: str = "") -> str:
    """按菜品类型、总预算（含配送费）和忌口搜索模拟餐馆。"""
    matches = []
    query = food_type.strip().casefold()
    for restaurant in RESTAURANTS:
        type_match = any(query in tag.casefold() or tag.casefold() in query for tag in restaurant["food_types"])
        eligible_dishes = [
            dish for dish in restaurant["dishes"]
            if dish["price"] + restaurant["delivery_fee"] <= max_price
            and not _matches_exclusion(dish, exclude_ingredient)
        ]
        if type_match and eligible_dishes:
            matches.append({
                "restaurant_name": restaurant["name"],
                "food_types": restaurant["food_types"],
                "delivery_fee": restaurant["delivery_fee"],
                "available_dishes": eligible_dishes,
            })
    return _json({"restaurants": matches, "message": "未找到符合条件的模拟餐馆" if not matches else "搜索完成"})


@tool(args_schema=DishRecommendInput)
def dish_recommend(restaurant_name: str, exclude_ingredient: str = "", max_price: float = 100000) -> str:
    """从指定模拟餐馆推荐单道菜加配送费不超过预算且不含忌口食材的菜品。"""
    restaurant = next((item for item in RESTAURANTS if item["name"] == restaurant_name), None)
    if restaurant is None:
        return _json({"dishes": [], "message": f"模拟数据中没有餐馆：{restaurant_name}"})
    dishes = [
        dish for dish in restaurant["dishes"]
        if dish["price"] + restaurant["delivery_fee"] <= max_price
        and not _matches_exclusion(dish, exclude_ingredient)
    ]
    return _json({"restaurant_name": restaurant_name, "dishes": dishes, "message": "推荐完成" if dishes else "没有符合条件的菜品"})


@tool(args_schema=CalculateTotalInput)
def calculate_total(restaurant_name: str, dish_names: list[str], max_budget: float) -> str:
    """按模拟菜单价格计算菜品小计、配送费和总价，并检查是否超出预算。"""
    restaurant = next((item for item in RESTAURANTS if item["name"] == restaurant_name), None)
    if restaurant is None:
        return _json({"error": f"模拟数据中没有餐馆：{restaurant_name}"})

    menu = {dish["name"]: dish for dish in restaurant["dishes"]}
    unknown_dishes = [name for name in dish_names if name not in menu]
    if unknown_dishes:
        return _json({"error": "菜单中找不到菜品", "unknown_dishes": unknown_dishes})

    selected = [menu[name] for name in dish_names]
    subtotal = round(sum(dish["price"] for dish in selected), 2)
    delivery_fee = restaurant["delivery_fee"]
    total = round(subtotal + delivery_fee, 2)
    return _json({
        "restaurant_name": restaurant_name,
        "items": [{"name": dish["name"], "price": dish["price"]} for dish in selected],
        "subtotal": subtotal,
        "delivery_fee": delivery_fee,
        "total": total,
        "max_budget": max_budget,
        "within_budget": total <= max_budget,
    })


TOOLS = [search_restaurant, dish_recommend, calculate_total]
TOOL_BY_NAME = {item.name: item for item in TOOLS}

SYSTEM_PROMPT = """你是一个中文外卖点餐助手，通过 LangChain 工具调用协助用户挑选模拟餐馆和菜品。
先收集：想吃的菜系或食物、总预算、忌口（明确说没有也算已回答）。口味偏好和配送要求可以一并询问，但不是筛选工具已支持的数据。
如果想吃什么、预算、忌口任一项缺失，先用自然中文追问缺少的信息；不可猜测，也不可调用工具。
信息齐全后必须按顺序调用 search_restaurant、dish_recommend、calculate_total，并且只能使用工具返回的餐馆、菜单、价格和配送费。用户预算是含配送费的总预算；不要推荐超预算菜品。用户只要求“一份/一道”时只选一道菜，不要为了凑单添加其他菜。传给搜索与推荐工具的 max_price 使用用户总预算，计算工具必须将总预算用于核验。
如果没找到餐馆或菜品，说明没有匹配项并询问用户是否愿意调整条件，不要编造商家或菜单。
计算完成后展示餐馆、菜品价格、小计、配送费和总价，并询问用户是否确认下单。这个演示程序不会真的下单；用户提到配送地址、时效等要求时，说明模拟数据无法验证实际配送范围或时间。
每次回复使用简洁的中文。工具调用过程由程序显示 Thought（简短决策摘要）、Action、Action Input、Observation；不要输出隐藏的详细推理。完成时以 Final Answer 展示面向用户的结果。"""


class TakeoutAgent:
    """管理模型、工具调用以及跨轮对话记录的单智能体。"""

    def __init__(self, model: str = "qwen2.5:7b", base_url: str = "http://localhost:11434") -> None:
        self.llm = ChatOllama(model=model, base_url=base_url, temperature=0).bind_tools(TOOLS)
        self.history: list[Any] = []

    def reply(self, user_text: str) -> str:
        """处理一轮用户输入，必要时多次调用工具直到生成最终回答。"""
        messages = [SystemMessage(content=SYSTEM_PROMPT), *self.history, HumanMessage(content=user_text)]
        stages = ["search_restaurant", "dish_recommend", "calculate_total"]
        stage = 0
        recommended_dishes: list[str] = []
        final_total: dict[str, Any] | None = None
        invalid_calls = 0
        for _ in range(8):
            response: AIMessage = self.llm.invoke(messages)
            messages.append(response)
            calls = response.tool_calls or []
            if not calls:
                answer = str(response.content).strip()
                self.history.extend([HumanMessage(content=user_text), response])
                self.history = self.history[-16:]
                return answer

            for call in calls:
                name = call.get("name", "")
                args = call.get("args", {})
                call_id = call.get("id", name)
                if stage >= len(stages) or name != stages[stage]:
                    invalid_calls += 1
                    observation = _json({
                        "error": f"当前流程应调用 {stages[stage] if stage < len(stages) else '直接生成最终回答'}，不能调用 {name}。"
                    })
                    print(f"\nObservation: {observation}")
                    messages.append(ToolMessage(content=observation, tool_call_id=call_id))
                    continue

                print("\nThought: 根据已收集的点餐条件执行下一步（简要决策摘要）")
                print(f"Action: {name}")
                print(f"Action Input: {json.dumps(args, ensure_ascii=False)}")
                try:
                    tool = TOOL_BY_NAME[name]
                    observation = tool.invoke(args)
                    result = json.loads(observation)
                    if name == "search_restaurant" and not result.get("restaurants"):
                        stage = len(stages)
                    elif name == "search_restaurant":
                        stage += 1
                    elif name == "dish_recommend":
                        recommended_dishes = [dish["name"] for dish in result.get("dishes", [])]
                        stage += 1
                    elif name == "calculate_total":
                        if not result.get("within_budget") and recommended_dishes:
                            restaurant_name = args["restaurant_name"]
                            budget = args["max_budget"]
                            selected = [item for item in args["dish_names"] if item in recommended_dishes]
                            affordable_result = None
                            for count in range(len(selected), 0, -1):
                                for subset in combinations(selected, count):
                                    candidate = json.loads(calculate_total.invoke({
                                        "restaurant_name": restaurant_name,
                                        "dish_names": list(subset),
                                        "max_budget": budget,
                                    }))
                                    if candidate.get("within_budget"):
                                        affordable_result = candidate
                                        removed = [item for item in selected if item not in subset]
                                        if removed:
                                            candidate["removed_for_budget"] = removed
                                        break
                                if affordable_result is not None:
                                    break
                            if affordable_result is not None:
                                result = affordable_result
                                observation = _json(result)
                        final_total = result
                        stage += 1
                except Exception as exc:
                    observation = _json({"error": f"工具调用失败：{exc}"})
                print(f"Observation: {observation}")
                messages.append(ToolMessage(content=str(observation), tool_call_id=call_id))

            if invalid_calls >= 3 and final_total is None:
                break

        if final_total is not None:
            items = ", ".join(f"{item['name']} {item['price']:.2f} 元" for item in final_total["items"])
            removed = final_total.get("removed_for_budget", [])
            adjustment = f"预算不足，已移除：{'、'.join(removed)}。" if removed else ""
            return (
                f"推荐餐馆：{final_total['restaurant_name']}。菜品：{items}。"
                f"小计 {final_total['subtotal']:.2f} 元，配送费 {final_total['delivery_fee']:.2f} 元，"
                f"总计 {final_total['total']:.2f} 元。{adjustment}以上为模拟数据，不会实际下单。请问确认这份清单吗？"
            )
        return "工具调用次数过多，暂时无法完成推荐。请简化需求后重试。"


def run_demo() -> None:
    """运行一段离线示例，演示三种工具和最终点单清单。"""
    print("测试对话：我想吃川菜，预算 35 元，不吃花生，推荐一份菜。\n")
    args = {"food_type": "川菜", "max_price": 35, "exclude_ingredient": "花生"}
    print("Thought: 已知菜系、预算和忌口，先筛选餐馆。")
    print("Action: search_restaurant")
    print(f"Action Input: {json.dumps(args, ensure_ascii=False)}")
    search_result = json.loads(search_restaurant.invoke(args))
    print(f"Observation: {json.dumps(search_result, ensure_ascii=False)}")

    restaurant_name = search_result["restaurants"][0]["restaurant_name"]
    recommend_args = {"restaurant_name": restaurant_name, "exclude_ingredient": "花生", "max_price": 35}
    print("\nThought: 从匹配餐馆中推荐不含忌口食材的菜品。")
    print("Action: dish_recommend")
    print(f"Action Input: {json.dumps(recommend_args, ensure_ascii=False)}")
    recommend_result = json.loads(dish_recommend.invoke(recommend_args))
    print(f"Observation: {json.dumps(recommend_result, ensure_ascii=False)}")

    dish_name = recommend_result["dishes"][0]["name"]
    total_args = {"restaurant_name": restaurant_name, "dish_names": [dish_name], "max_budget": 35}
    print("\nThought: 根据模拟菜单和配送费核算总价。")
    print("Action: calculate_total")
    print(f"Action Input: {json.dumps(total_args, ensure_ascii=False)}")
    total_result = json.loads(calculate_total.invoke(total_args))
    print(f"Observation: {json.dumps(total_result, ensure_ascii=False)}")
    print("\nFinal Answer: 推荐老街川菜的鱼香肉丝，菜品 24 元，配送费 4 元，总计 28 元。以上为模拟数据，不会实际下单。请问要确认这份清单吗？")


def main() -> None:
    """启动命令行 Agent，支持真实模型对话或离线示例。"""
    parser = argparse.ArgumentParser(description="基于 LangChain 的模拟外卖点餐 Agent")
    parser.add_argument("--model", default="qwen2.5:7b", help="Ollama 模型名称，默认 qwen2.5:7b")
    parser.add_argument("--base-url", default="http://localhost:11434", help="Ollama 服务地址")
    parser.add_argument("--demo", action="store_true", help="运行离线演示，不连接 Ollama")
    args = parser.parse_args()

    if args.demo:
        run_demo()
        return

    try:
        agent = TakeoutAgent(model=args.model, base_url=args.base_url)
    except Exception as exc:
        raise SystemExit(f"初始化 Ollama Agent 失败：{exc}\n请先安装依赖、启动 Ollama 并下载模型。") from exc

    print("外卖点餐助手已启动。输入 exit 退出。")
    while True:
        try:
            user_text = input("\n你：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n已退出。")
            break
        if user_text.casefold() in {"exit", "quit"}:
            print("已退出。")
            break
        if not user_text:
            continue
        try:
            print(f"\nFinal Answer: {agent.reply(user_text)}")
        except Exception as exc:
            print(f"\nFinal Answer: 暂时无法处理请求：{exc}")


if __name__ == "__main__":
    main()
