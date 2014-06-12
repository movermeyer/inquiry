import os
import json
import tornpsql
import unittest
from decimal import Decimal

from inquiry import Inquiry


EXAMPLES = [
{
  "title": "Orders",
  "description": "",
  "tables": "from orders o",
  "outline": {
    "index": {
      "select": ["o.orderid", "o.userid", "o.total", "o.due", "o.placed", "u.name", "u.email"],
      "tables": ["inner join users u using (userid)"]
    },
    "/": {
      "/count": {
        "select": "count(o.*) as count"
      },
      "/totals?": {
        "select": "%(agg)s(o.total) total"
      },
      "arguments": {
        "agg": {
          "adapt": False,
          "default": "sum",
          "options": {
            "sum": {}
          }
        },
        "groupby": {
          "adapt": False,
          "options": {
            "users?": {
              # "select": "column_day as day",
              "value": "userid"
            }
          }
        }
      }
    }
  },
  "arguments": {
    "due": {
      "validator": "string",
      "column": "o.due::numeric"
    },
    "total": {
      "validator": "string",
      "column": "o.total::numeric"
    }
  }
}]

class Data(Inquiry):
    def __init__(self, *a, **k):
        Inquiry.__init__(self, *a, **k)
        self.db = tornpsql.Connection(os.getenv("PSQL"))

    def query(self, query, *extra):
        return self.db.query(query)


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.inquiry = Data(debug=True)
        self.inquiry.add_figure("orders", EXAMPLES[0])
        # self.inquiry.add_figure("users", EXAMPLES[1])

    def setUp(self):
        self.q = self.inquiry.new()

    def test_one_row_one_value(self):
        result = self.q("order", "totals", due=">0")
        self.assertEquals(result, Decimal("398.89"))

    def test_one_row_multi_values(self):
        "cannot compare when there are many results"
        self.skipTest("wip")
        result = self.q("orders", due="0")
        print result, result > 0
        self.assertRaises(TypeError, lambda: result > 10)
        raise Exception("Hello")

    def test_json(self):
        result = json.loads(self.q("order", "totals", due=">0", groupby="user").json())
        self.assertEquals(result["meta"]["status"], 200)
        self.assertEquals(result["meta"]["total"], 15)
        self.assertItemsEqual(result['results'], [{"total": 26.83, "userid": 14}, {"total": 6.51, "userid": 8}, {"total": 11.0, "userid": 17}, {"total": 32.28, "userid": 1}, {"total": 22.96, "userid": 15}, {"total": 20.24, "userid": 2}, {"total": 54.06, "userid": 10}, {"total": 11.69, "userid": 3}, {"total": 28.63, "userid": 11}, {"total": 15.95, "userid": 4}, {"total": 45.97, "userid": 5}, {"total": 18.07, "userid": 13}, {"total": 14.11, "userid": 9}, {"total": 64.01, "userid": 16}, {"total": 26.58, "userid": 7}])
