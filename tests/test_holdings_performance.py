import json
import os
import tempfile
import unittest
from unittest.mock import patch

from finfreedom.database import connect
from finfreedom.holdings_performance import history

class HoldingsPerformanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {'FINFREEDOM_DATA_DIR': self.temp.name})
        self.env.start()
    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()
    def test_confirmed_snapshot_and_closes_produce_estimate_without_backfill(self):
        with connect() as db:
            db.execute('INSERT INTO holdings_history VALUES(?,?,?,?)', ('alice','USD','2024-01-01T10:00:00+00:00',json.dumps([{'instrument_id':'US:AAPL','quantity':10}])))
            for day, close in [('2024-01-02',100),('2024-01-03',103)]:
                db.execute("INSERT INTO bars(instrument_id,interval_name,bar_time,close,currency,adjustment,provider,received_at) VALUES(?,?,?,?,?,?,?,?)",('US:AAPL','1d',day,close,'USD','none','test','2024-01-04'))
        rows=history('alice','USD','2023-12-29','2024-01-03')['days']
        self.assertEqual(rows[0]['reason'],'no_holdings_history')
        self.assertTrue(rows[-1]['complete'])
        self.assertEqual(rows[-1]['day_pnl'],30)
        self.assertEqual(history('bob','USD','2024-01-03','2024-01-03')['days'][0]['reason'],'no_holdings_history')
    def test_changed_holdings_and_missing_prices_are_not_fabricated(self):
        with connect() as db:
            for stamp, quantity in [('2024-01-01T10:00:00+00:00',10),('2024-01-03T10:00:00+00:00',20)]:
                db.execute('INSERT INTO holdings_history VALUES(?,?,?,?)',('alice','USD',stamp,json.dumps([{'instrument_id':'US:AAPL','quantity':quantity}])))
        rows=history('alice','USD','2024-01-03','2024-01-04')['days']
        self.assertEqual(rows[0]['reason'],'holdings_changed')
        self.assertEqual(rows[1]['reason'],'missing_bars')
        self.assertFalse(rows[1]['complete'])

if __name__ == '__main__': unittest.main()
