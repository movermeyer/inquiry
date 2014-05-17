import unittest

from inquiry import Inquiry
from inquiry.navigator import Navigator

EXAMPLE = {
  "title": "Example Figure",
  "description": "",
  # seeds on top lvl
  "where": "col_b > 10",
  "tables": "from table",
  "outline": {
    "index": {
      "select": "value",
      "ignores": "",
      "arguments": {
        # merging example
        "&agg": {
          
        },

      }
    },
    "/": {
      # regexp example
      "/(count|total)": {
        "select": "count(o.*) as count"
      },
      "arguments": {
        "&agg": {
          "&default": "sum"
        }
      }
    }
  },
  "arguments": {
    # multiple ?a=1&b=2
    "a[]": {
      "validator": "string",
      "default": "Hello",
      "column": "col_a::text"
    },
    # option argument
    "groupby": {
      "adapt": False,
      "options": {
        # allows regexp
        "days?": {
          "select": "to_char(date_trunc('day', o.timestamp), 'YYYY-MM-DD') as day"
        }
      }
    }
  }
}


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.inquiry = Inquiry()
        self.inquiry.add_figure("example", EXAMPLE)

    def test_inquiry_nav(self):
        "create new navs"
        nav = self.inquiry.new()
        self.assertIsInstance(nav, Navigator)

    def test_nav_via_getattr(self):
        "nav by getattr"
        nav = self.inquiry.new()
        self.assertIsInstance(nav.example, Navigator)

    def test_nav_via_getitem(self):
        "nav by item"
        nav = self.inquiry.new()
        self.assertIsInstance(nav['example'], Navigator)

    def test_default_arguments(self):
        nav = self.inquiry.new()
        self.assertEqual(nav('example').pg(), "select value from table where col_a = 'Hello'::text and col_b > 10")








