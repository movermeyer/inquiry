import unittest
import valideer

from inquiry import Inquiry
from inquiry.navigator import Navigator

EXAMPLES = [
{
  "title": "Example Figure",
  "description": "",
  # seeds on top lvl
  "where": "b > 10",
  "tables": "from table",
  "outline": {
    "index": {
      "select": "value"
    },
    "/merge": {
      "select": "c",
      "arguments": {
        "&a[]": {
          "default": "Whats up!"
        }
      }
    },
    "/": {
      # regexp example
      "/(count|total)": {
        "select": "count(o.*) as count"
      },
      "/inherit": {
        "inherit": "b/other",
        "select": "that",
        "where": ["r = %(r)s"]
      },
      "arguments": {
        "&agg": {
          "&default": "sum"
        }
      }
    }
  },
  "arguments": {
    "a[]": {
      "validator": "string",
      "default": "Hello",
      "column": "col_a::text"
    },
    "groupby": {
      "adapt": False,
      "options": {
        "days?": {
          "select": "column_day as day",
          "value": "day"
        }
      }
    },
    "ignore1": {
      "validator": "string",
      "ignore": "a"
    },
    "ignore2": {
      "validator": "string",
      "ignore": ["a", "groupby"]
    }
  }
},
{
  "tables": ["from table"],
  "outline": {
    "index": {
      "select": "a"
    },
    "/other": {
      "tables": ["inner join other using (this)"],
      "select": "this",
      "arguments": {
        "this": {
          "validator": "string",
          "required": True
        }
      }
    }
  },
  "arguments": {
    "r": {
      "validator": "string",
      "required": True
    }
  }
}]


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.inquiry = Inquiry()
        self.inquiry.add_figure("a", EXAMPLES[0])
        self.inquiry.add_figure("b", EXAMPLES[1])

    def setUp(self):
        self.q = self.inquiry.new()

    def test_inquiry_nav(self):
        "nav - new"
        self.assertIsInstance(self.q, Navigator)

    def test_nav_via_getattr(self):
        "nav - __getattr__"
        self.assertIsInstance(self.q.a, Navigator)

    def test_nav_via_getitem(self):
        "nav - __getitem__"
        self.assertIsInstance(self.q['a'], Navigator)

    def test_outline_nav_regexp(self):
        "outline - nav with regexp"
        self.assertEqual(self.q('a', 'count').pg(), "select count(o.*) as count from table where col_a = 'Hello'::text and b > 10")
        self.setUp()
        self.assertEqual(self.q('a', 'total').pg(), "select count(o.*) as count from table where col_a = 'Hello'::text and b > 10")

    def test_outline_inheritance(self):
        self.assertRaisesRegexp(valideer.ValidationError, "missing required property: this", self.q, 'a', 'inherit')
        self.setUp()
        self.assertEqual(self.q('a', 'inherit', this="apples", r="something").pg(), "select this, that from table inner join other using (this) where col_a = 'Hello'::text and r = 'something'")

    def test_default_arguments(self):
        "argument - `default`"
        self.assertEqual(self.q('a').pg(), "select value from table where col_a = 'Hello'::text and b > 10")

    def test_argument_list(self):
        "argument - accepts lists with `[]` at end of key"
        self.assertEqual(self.q('a', a=["this", "that"]).pg(), "select value from table where ARRAY['this', 'that']::text[] @> array[col_a] and b > 10")

    def test_arguments_option_regexp(self):
        "argument:options - keys are regexp"
        self.assertEqual(self.q('a', groupby="day").pg(),  "select column_day as day, value from table where col_a = 'Hello'::text and b > 10 group by day")
        self.setUp()
        self.assertEqual(self.q('a', groupby="days").pg(), "select column_day as day, value from table where col_a = 'Hello'::text and b > 10 group by day")

    def test_arguments_seeds_ignore_str(self):
        "argument:ignore - <str>"
        self.assertEqual(self.q('a', ignore1="true").pg(), "select value from table where b > 10")

    def test_arguments_seeds_ignore_list(self):
        "argument:ignore - <list>"
        self.assertRaisesRegexp(valideer.ValidationError, "additional properties: groupby", self.q, 'a', groupby="day", ignore2="true")

    def test_argument_seed_requires(self):
        "argument:required - requres a value"
        self.assertRaisesRegexp(valideer.ValidationError, "missing required property: r", self.q, 'b')

    def test_argument_merge(self):
        "arguments - can merge"
        self.assertEqual(self.q('a', 'merge').pg(), "select c from table where col_a = 'Whats up!'::text and b > 10")
