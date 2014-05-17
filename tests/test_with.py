import unittest
import valideer

from inquiry import Inquiry


class WithTest(unittest.TestCase):
    figure = {
      "tables": ["from orders"],
      "outline": {
        "index": {
          "select": ["customer", "subtotal"]
        }
      },
      "arguments": {
        "count": {
          # the `False` will clear out the seleted columns from above
          "select": [False, "count(*) as count"],
          "validator": "number",
          "column": "count::int",
          # to compare this value we must make a with query.
          "agg": True,
          # for this example we need to require a groupby value to be set
          "requires": "groupby"
        },
        "groupby" : {
          "validator": "string",
          "adapt": False
        }
      }
    }
    @classmethod
    def setUpClass(self):
        self.inquiry = Inquiry(debug=True)
        self.inquiry.add_figure("data", self.figure)

    def setUp(self):
        self.q = self.inquiry.new()

    def test_agg_not_provided(self):
        self.assertEqual(self.q('data').pg(), "select customer, subtotal from orders")

    def test_groupby_required(self):
        self.assertRaisesRegexp(valideer.ValidationError, "required property not set: groupby", self.q, 'data', count=10)

    def test_agg_provided(self):
        self.assertEqual(self.q('data', count=10, groupby="customer").pg(), "with _data as (select count(*) as count, customer from orders group by customer) select count, customer from _data where count = 10::int")


class WithTest2(unittest.TestCase):
    figure = {
      "tables": ["from orders"],
      "outline": {
        "index": {
          "select": ["customer", "subtotal"]
        },
        "/bycustomer": {
          "arguments": {
            "groupby" : {
              "validator": "string",
              "adapt": False,
              "default": "customer"
            },
            "count": {
              "select": "count(*) as count",
              "validator": "number",
              "column": "count::int",
              "agg": True
            }
          }
        }
      }
    }
    @classmethod
    def setUpClass(self):
        self.inquiry = Inquiry(debug=True)
        self.inquiry.add_figure("data", self.figure)

    def setUp(self):
        self.q = self.inquiry.new()

    def test_agg_not_provided(self):
        self.assertEqual(self.q('data').pg(), "select customer, subtotal from orders")

    def test_groupby_required(self):
        self.assertRaisesRegexp(valideer.ValidationError, r"additional properties: \[\'count\'\]", self.q, 'data', count=10)

    def test_agg_provided(self):
        self.assertEqual(self.q('data', 'bycustomer', count=10).pg(), "with _data as (select count(*) as count, customer from orders group by customer) select count, customer from _data where count = 10::int")

