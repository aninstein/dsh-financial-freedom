import os, tempfile, unittest
from datetime import date, timedelta
from unittest.mock import patch
from finfreedom import backtest
from finfreedom.database import connect

class BacktestTest(unittest.TestCase):
    def test_delayed_signal_cost_and_owner(self):
        with tempfile.TemporaryDirectory() as path, patch.dict(os.environ, {'FINFREEDOM_DATA_DIR':path}):
            start=date(2024,1,1)
            with connect() as db:
                for i,price in enumerate((10,11,12,13,14,15)):
                    db.execute("INSERT INTO bars(instrument_id,interval_name,bar_time,open,high,low,close,volume,currency,adjustment,provider,received_at,price_unit,volume_unit) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",('CN:000001','1d',(start+timedelta(days=i)).isoformat(),price,price,price,price,0,'CNY','none','test','2024-01-01','CNY/share','share'))
            result=backtest.run('alice',{'instrument_id':'CN:000001','start':'2024-01-01','end':'2024-01-06','fast_window':2,'slow_window':3,'fee_bps':10,'slippage_bps':5})
            expected=(1+(13/12-1)-.0015)*(14/13)*(15/14)-1
            self.assertAlmostEqual(result['metrics']['total_return'],expected)
            with connect() as db: self.assertEqual(db.execute('SELECT COUNT(*) AS n FROM research_runs WHERE owner_id=?',('alice',)).fetchone()['n'],1)

if __name__=='__main__': unittest.main()
