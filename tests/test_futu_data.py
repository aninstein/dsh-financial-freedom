import json
import threading
import time
import unittest
from unittest.mock import patch
from finfreedom import futu_data

class FutuCacheTests(unittest.TestCase):
    def setUp(self):
        futu_data._cache.clear()
    def test_account_summary_cached_and_independent_of_quotes(self):
        calls=[]
        gate=threading.Event()
        class Result:
            def __init__(self, data): self.stdout=json.dumps(data)
        def run(args, **kwargs):
            calls.append(args[-2])
            if args[-2]=='quotes': gate.wait(2)
            return Result({'state':'connected','accounts':[{'id':'1'}]})
        with patch('finfreedom.futu_data.subprocess.run',side_effect=run):
            thread=threading.Thread(target=futu_data.watchlist); thread.start()
            start=time.monotonic()
            futu_data.account_summary('SIMULATE')
            self.assertLess(time.monotonic()-start,1)
            futu_data.account_summary('SIMULATE')
            gate.set(); thread.join()
        self.assertEqual(calls.count('account_summary'),1)

if __name__=='__main__': unittest.main()

class RealAccountAccessTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        import os
        self.os = os
        self.temp=tempfile.TemporaryDirectory()
        self.env=patch.dict(os.environ,{'FINFREEDOM_DATA_DIR':self.temp.name},clear=False)
        self.env.start()
        futu_data._cache.clear()
    def tearDown(self):
        self.env.stop(); self.temp.cleanup()
    def test_only_discovered_accounts_can_be_authorized(self):
        account='futu-real-hk-' + 'a'*24
        with patch.object(futu_data,'discover_real',return_value={'state':'connected','accounts':[{'id':account}]}):
            with self.assertRaises(ValueError): futu_data.set_real_access(['futu-real-us-'+'b'*24])
            self.assertEqual(futu_data.real_access(),[])
            futu_data.set_real_access([account])
            self.assertEqual(futu_data.real_access(),[account])
            self.assertEqual(self.os.stat(futu_data._access_path()).st_mode & 0o777,0o600)
            futu_data.set_real_access([])
            self.assertEqual(futu_data.real_access(),[])
    def test_failed_discovery_does_not_clear_access(self):
        account='futu-real-hk-' + 'a'*24
        with patch.object(futu_data,'discover_real',return_value={'state':'connected','accounts':[{'id':account}]}):
            futu_data.set_real_access([account])
        with patch.object(futu_data,'discover_real',return_value={'state':'unavailable','accounts':[]}):
            with self.assertRaises(ValueError): futu_data.set_real_access([])
        self.assertEqual(futu_data.real_access(),[account])

class RealDiscoveryTests(unittest.TestCase):
    def test_discovery_does_not_read_balances_until_authorized(self):
        import types
        from finfreedom import futu_worker
        calls=[]
        class Frame:
            def __init__(self, rows): self.rows=rows
            def to_dict(self, **kwargs): return self.rows
        class Context:
            def __init__(self,filter_trdmarket,**kwargs): self.market=filter_trdmarket
            def get_acc_list(self): return 0,Frame([{'acc_id':'12345678','trd_env':'REAL','trdmarket_auth':['HK']}])
            def accinfo_query(self,**kwargs): calls.append('balance'); return 0,Frame([{'cash':10,'total_assets':12}])
            def position_list_query(self,**kwargs): calls.append('positions'); return 0,Frame([])
            def close(self): pass
        module=types.SimpleNamespace(OpenSecTradeContext=Context,RET_OK=0)
        with patch.dict('sys.modules',{'futu':module}), patch.dict('os.environ',{'FINFREEDOM_FUTU_REAL_ACCOUNT_IDS':'','FINFREEDOM_FUTU_REAL_ACCOUNT_TOKENS':''}):
            result=futu_worker.accounts('REAL',summary=True,discover=True)
            self.assertEqual(calls,[])
            self.assertFalse(result['accounts'][0]['authorized'])
            self.assertNotIn('acc_id',result['accounts'][0])
            self.assertEqual(futu_worker.accounts('REAL')['accounts'],[])
            token=result['accounts'][0]['id']
            with patch.dict('os.environ',{'FINFREEDOM_FUTU_REAL_ACCOUNT_TOKENS':token}):
                authorized=futu_worker.accounts('REAL')
            self.assertEqual(len(authorized['accounts']),1)
            self.assertEqual(calls,['balance','positions'])
