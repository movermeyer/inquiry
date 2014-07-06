import unittest
import valideer

from inquiry.query import Query


class Tests(unittest.TestCase):
    def test_from(self):
        "query: must have a from table"
        q = Query()
        q.select("column_1")
        q.select("column_2")
        self.assertRaises(valideer.ValidationError, q, {}) 

    def test_resort_tables(self):
        "query: re-organizes tables"
        q = Query()
        q.select("column_1")
        q.select("column_2")
        q.tables("left join this using (that)", "from here")
        self.assertEqual("SELECT"+q({})[6:], "SELECT column_1, column_2__into__ from here left join this using (that)")

        q = Query()
        q.select("column_1")
        q.select("column_2")
        q.tables("left join this using (that)", "from here", "inner join a using (b)")
        self.assertEqual("SELECT"+q({})[6:], "SELECT column_1, column_2__into__ from here inner join a using (b) left join this using (that)")

    def test_filters_selects(self):
        "query: filters select columns"
        q = Query()
        q.select("column_1")
        q.select("column_2")
        q.select("column_1")
        q.select("column_1")
        q.tables("from here")
        self.assertEqual("SELECT"+q({})[6:], "SELECT column_1, column_2__into__ from here")

        q = Query()
        q.select("column_1")
        q.select("column_2")
        q.select(False)
        q.select("column_3")
        q.tables("from here")
        self.assertEqual("SELECT"+q({})[6:], "SELECT column_3__into__ from here")

    def test_filter_tables(self):
        q = Query()
        q.select("column_1")
        q.select("column_2")
        q.tables("from here", False, "inner join this using (that)", "from there")
        self.assertEqual("SELECT"+q({})[6:], "SELECT column_1, column_2__into__ from there inner join this using (that)")

    def test_into_toggle(self):
        "query: can toggle __into__"
        q = Query()
        q.select("column_1")
        q.tables("from here")
        self.assertEqual("SELECT"+q({})[6:], "SELECT column_1__into__ from here")

        q = Query()
        q.select("column_1")
        q.tables("from here")
        q.into(False)
        self.assertEqual("SELECT"+q({})[6:], "SELECT column_1 from here")

    def test_column_as(self):
        "query: select as name"
        q = Query()
        q.select("column_1", None, "name")
        self.assertItemsEqual(q._selects.keys(), ["name"])
        q.tables("from here")
        q.into(False)
        self.assertEqual("SELECT"+q({})[6:], "SELECT column_1 as name from here")

    def test_where(self):
        "query: manages where clause"
        q = Query()
        q.select("column_1", None, "name")
        q.where("name", "name like 'this'")
        q.tables("from here")
        q.into(False)
        self.assertEqual("SELECT"+q({})[6:], "SELECT column_1 as name from here where name like 'this'")

    def test_where_multi(self):
        "query: multiple where"
        q = Query()
        q.select("column_1", None, "name")
        q.where("name", "name like 'this'")
        q.where("this", "this like 'this'")
        q.tables("from here")
        q.into(False)
        self.assertEqual("SELECT"+q({})[6:], "SELECT column_1 as name from here where this like 'this' and name like 'this'")

    def test_where_multi_same(self):
        "query: multiple where of same column"
        q = Query()
        q.select("column_1", None, "name")
        q.where("name", "name like 'this'")
        q.where("name", "name < 10")
        q.tables("from here")
        q.into(False)
        self.assertEqual("SELECT"+q({})[6:], "SELECT column_1 as name from here where name like 'this' and name < 10")

    def test_where_aggs(self):
        "query: manages where aggs"
        q = Query()
        q.select("col", "sum", "total")
        q.select("store")
        q.agg("total")
        q.groupby("store")
        q.where("total", "total > 50")
        q.tables("from here")
        q.into(False)
        self.assertEqual(q({}), "with _data as (select sum(col) as total, store from here group by store) select store, total__into__ from _data where total > 50")

    def test_agg_filter(self):
        q = Query()
        q.select("total")
        q.select("store")
        q.agg("total")
        q.agg("total")
        q.where("total", "total > 50")
        q.tables("from here")
        self.assertEqual("SELECT"+q({})[6:], "SELECT store, total__into__ from here where total > 50")

        q = Query()
        q.select("total")
        q.select("store")
        q.agg("total")
        q.agg(False)
        q.agg("that")
        q.where("total", "total > 50")
        q.tables("from here")
        self.assertEqual("SELECT"+q({})[6:], "SELECT store, total__into__ from here where total > 50")

    def test_arguments(self):
        "query: inserts arguments"
        q = Query()
        q.select("col", "%(agg)s", "total")
        q.where("total", "total > 50")
        q.tables("from here")
        q.into(False)
        self.assertEqual("SELECT"+q(dict(agg="sum"))[6:], "SELECT sum(col) as total from here where total > 50")
        
    def test_sortby(self):
        "query: sort by must be seleted"
        q = Query()
        q.select("column_1")
        q.sortby("column_2")
        q.tables("from table")
        self.assertEqual("SELECT"+q(dict(dir="asc"))[6:], "SELECT column_2, column_1__into__ from table order by column_2 asc")
        
        q = Query()
        q.select("column_1")
        q.sortby("column_2")
        q.tables("from table")
        self.assertEqual("SELECT"+q(dict(dir="asc"))[6:], "SELECT column_2, column_1__into__ from table order by column_2 asc")

        q = Query()
        q.select("column_1")
        q.select("column_2")
        q.sortby("column_2")
        q.tables("from table")
        self.assertEqual("SELECT"+q(dict(dir="desc"))[6:], "SELECT column_1, column_2__into__ from table order by column_2 desc")

    def test_with(self):
        "query: with magic"
        q = Query()
        q.select("column_1")
        q.with_("select this from that", "_this")
        q.tables("from table")
        self.assertEqual(q({}), "with _this as (select this from that) select column_1__into__ from table")

    def test_with_filter(self):
        "query: with filtered"
        q = Query()
        q.select("column_1")
        q.with_("select this from that", "_this")
        q.with_("select this from that", "_this")
        q.tables("from table")
        self.assertEqual(q({}), "with _this as (select this from that) select column_1__into__ from table")

    def test_with_false(self):
        "query: with reduced"
        q = Query()
        q.select("column_1")
        q.with_("with _that ()")
        q.with_(False)
        q.with_("select this from that", "_that")
        q.tables("from table")
        self.assertEqual(q({}), "with _that as (select this from that) select column_1__into__ from table")

    def test_percentage_limit(self):
        "query a percentage of records"
        q = Query()
        q.select("total")
        q.tables("from orders")
        q.sortby('total')
        self.assertEqual(q({"limit":"50%"}), "with _l as (select total from orders), _ll as (select total from _l order by total asc limit (select round(count(*)*0.5) from _ll)) select total__into__ from _ll")

    def test_percentage_agg(self):
        "query a percentage of records"
        q = Query()
        q.select("total", "sum", "total")
        q.tables("from orders")
        q.sortby('total')
        self.assertEqual(q({"limit":"50%"}), "with _l as (select total as total from orders), _ll as (select total from _l order by total asc limit (select round(count(*)*0.5) from _ll)) select sum(total) as total__into__ from _ll")

    def test_percentage_where(self):
        "query a percentage of records w/ where condition"
        q = Query()
        q.select("total")
        q.tables("from orders")
        q.where("total", "total > 10")
        q.sortby('total')
        self.assertEqual(q({"limit":"10%"}), "with _l as (select total from orders where total > 10), _ll as (select total from _l order by total asc limit (select round(count(*)*0.1) from _ll)) select total__into__ from _ll")

    def test_where_arrangement(self):
        q = Query()
        q.select("a")
        q.where("a", "a > 10")
        q.where("b", "b > 20")
        q.where("c", "c > 30")
        q.tables("from t")
        q.into(False)

        # no column `d`
        self.assertRaises(valideer.ValidationError, q, valideer.parse({"where": "where"}).validate({"where": "(d|b)&c"}))

        self.assertEqual(q(valideer.parse({"where": "where"}).validate({"where": "(a|b)&c"})),
                         "select a from t where ((a > 10 or b > 20) and c > 30)")

    def test_where_multi_arg(self):
        q = Query()
        q.select("a")
        q.where("a", "a=1")
        q.where("b", "b=2")
        q.where("b", "b=3")
        q.tables("from t")
        q.into(False)

        # no column `col_1`
        self.assertRaises(valideer.ValidationError, q, valideer.parse({"where": "where"}).validate({"where": "a|b|c"}))

        self.assertEqual(q(valideer.parse({"where": "where"}).validate({"where": "a|b"})),
                         "select a from t where (a=1 or (b=2 and b=3))")
