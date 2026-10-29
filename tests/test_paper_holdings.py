import os
import tempfile
import unittest
from unittest.mock import patch

from finfreedom import holdings, paper, paper_service

class WorkspaceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {'FINFREEDOM_DATA_DIR':self.tmp.name,'FINFREEDOM_FUTU_ENABLED':'false'})
        self.env.start()
    def tearDown(self):
        self.env.stop(); self.tmp.cleanup()
    def test_holdings_merge_and_version(self):
        first=holdings.update_positions('owner','CNY',[{'instrument_id':'CN:600519','name':'茅台','asset_class':'stock','quantity':100,'cost_basis':1000},{'instrument_id':'GOLD:Au99.99','name':'黄金','asset_class':'gold','quantity':2}],None)
        stamp=first['updated_at']
        holdings.update_positions('owner','CNY',[{'instrument_id':'CN:600519','quantity':200},{'instrument_id':'GOLD:Au99.99','quantity':3}],stamp)
        with paper_service.connect() as db:
            rows=db.execute('SELECT instrument_id,quantity,cost_basis FROM personal_positions WHERE owner_id=? ORDER BY instrument_id',('owner',)).fetchall()
        self.assertEqual([(r['instrument_id'],r['quantity'],r['cost_basis']) for r in rows], [('CN:600519',200,1000),('GOLD:Au99.99',3,None)])
        with self.assertRaises(RuntimeError): holdings.update_positions('owner','CNY',[{'instrument_id':'CN:600519','quantity':300}],stamp)
    def test_limit_order_reservation_cancel_and_isolation(self):
        with patch.object(paper_service,'session',return_value={'phase':'closed'}):
            account=paper_service.action('alice','create_account',{'label':'test','market':'US','initial_cash':1000},'account-1')
            payload={'account_id':account['account_id'],'instrument_id':'US:AAPL','side':'buy','type':'limit','quantity':10,'limit_price':20}
            preview=paper_service.action('alice','preview',payload)
            self.assertFalse(preview['would_fill_at_observed_quote'])
            order=paper_service.action('alice','submit',payload,'order-1')
            self.assertEqual(paper_service.action('alice','submit',payload,'order-1')['order_id'],order['order_id'])
            self.assertEqual(paper_service.action('alice','accounts',{})[0]['available_cash'],799.8)
            with self.assertRaises(paper.HTTPException): paper_service.action('bob','cancel',{'order_id':order['order_id']})
            self.assertEqual(paper_service.action('alice','cancel',{'order_id':order['order_id']})['status'],'cancelled')
            self.assertEqual(paper_service.action('alice','accounts',{})[0]['available_cash'],1000)

    def test_fresh_quote_matches_owner_limit_order(self):
        from datetime import datetime, timezone
        with patch.object(paper_service,'session',return_value={'phase':'closed'}):
            account=paper_service.action('alice','create_account',{'label':'test','market':'US','initial_cash':1000},'a')
            payload={'account_id':account['account_id'],'instrument_id':'US:AAPL','side':'buy','type':'limit','quantity':10,'limit_price':20}
            order=paper_service.action('alice','submit',payload,'o')
        now=datetime.now(timezone.utc).isoformat()
        with paper_service.connect() as db:
            db.execute("INSERT INTO quotes(instrument_id,symbol,name,market,asset_class,last,currency,quote_kind,price_unit,exchange_time,received_at,provider,freshness) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",('US:AAPL','AAPL','Apple','US','equity',19,'USD','snapshot','USD/share',now,now,'test','observed'))
        with patch.object(paper_service,'session',return_value={'phase':'open'}):
            self.assertEqual(paper_service.action('bob','orders',{}),[])
            rows=paper_service.action('alice','orders',{})
            self.assertEqual(rows[0]['status'],'filled')
            account=paper_service.action('alice','accounts',{})[0]
            self.assertEqual(account['cash'],809.81)
            self.assertEqual(account['positions'][0]['quantity'],10)
            self.assertEqual(rows[0]['order_id'],order['order_id'])

if __name__ == '__main__': unittest.main()
