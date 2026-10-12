"""外卖 Agent 模拟工具的离线测试。"""

import json
import unittest

from ollama_tool_agent import calculate_total, dish_recommend, search_restaurant


class TakeoutToolTests(unittest.TestCase):
    def test_search_filters_excluded_ingredient(self) -> None:
        result = json.loads(search_restaurant.invoke({
            "food_type": "川菜",
            "max_price": 35,
            "exclude_ingredient": "花生",
        }))

        self.assertEqual([item["restaurant_name"] for item in result["restaurants"]], ["老街川菜"])
        dishes = result["restaurants"][0]["available_dishes"]
        self.assertNotIn("宫保鸡丁", [dish["name"] for dish in dishes])

    def test_recommendation_respects_dietary_restriction(self) -> None:
        result = json.loads(dish_recommend.invoke({
            "restaurant_name": "老街川菜",
            "exclude_ingredient": "花生",
            "max_price": 35,
        }))

        self.assertIn("鱼香肉丝", [dish["name"] for dish in result["dishes"]])
        self.assertNotIn("宫保鸡丁", [dish["name"] for dish in result["dishes"]])

    def test_total_includes_delivery_fee_and_checks_budget(self) -> None:
        result = json.loads(calculate_total.invoke({
            "restaurant_name": "老街川菜",
            "dish_names": ["鱼香肉丝"],
            "max_budget": 35,
        }))

        self.assertEqual(result["subtotal"], 24.0)
        self.assertEqual(result["delivery_fee"], 4.0)
        self.assertEqual(result["total"], 28.0)
        self.assertTrue(result["within_budget"])

    def test_total_reports_over_budget(self) -> None:
        result = json.loads(calculate_total.invoke({
            "restaurant_name": "老街川菜",
            "dish_names": ["鱼香肉丝"],
            "max_budget": 27,
        }))

        self.assertFalse(result["within_budget"])


if __name__ == "__main__":
    unittest.main()