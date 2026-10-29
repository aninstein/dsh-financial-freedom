import asyncio
import os
import tempfile
import unittest
from unittest.mock import patch
from finfreedom import mcp_server, research_data
from finfreedom.database import connect

class ResearchMigrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.env=patch.dict(os.environ,{'FINFREEDOM_DATA_DIR':self.tmp.name,'FINFREEDOM_OWNER_ID':'alice','FINFREEDOM_FUTU_ENABLED':'false','AKSHARE_ENABLED':'false'})
        self.env.start()
    async def asyncTearDown(self):
        self.env.stop();self.tmp.cleanup()
    async def test_core_research_and_missing_bars(self):
        overview=await mcp_server.research('get_market_overview',{'market':'CN'})
        self.assertEqual(overview['quote_count'],0)
        detail=await mcp_server.research('get_instrument_research',{'instrument_id':'FUND:513100'})
        self.assertEqual(detail['instrument_id'],'FUND:513100')
        self.assertEqual(detail['bar_count'],0)
        self.assertTrue(detail['data_gap'])
        rotation=await mcp_server.research('get_sector_rotation',{})
        self.assertEqual(rotation['state'],'unavailable')
        for arg in ({'code':'FUND:513100'},{'instrument_id':'FUND:513100'},{'fund_code':'513100'}):
            self.assertEqual(mcp_server._read_sync('fund_detail',arg)['code'],'513100')
    async def test_uploaded_documents_are_owner_scoped(self):
        with connect() as db:
            db.execute("INSERT INTO ai_documents(document_id,filename,document_type,owner_id,content_hash,page_count,imported_at) VALUES(?,?,?,?,?,?,?)",('D-AAAAAAAAAAAA','private.pdf','pdf','bob','x',1,'2026-01-01'))
            db.execute("INSERT INTO ai_document_pages(document_id,page_no,content) VALUES(?,?,?)",('D-AAAAAAAAAAAA',1,'营业收入私有数据'))
        result=await mcp_server.research('search_uploaded_documents',{'query':'营业收入'})
        self.assertEqual(result['matches'],[])
        result=await mcp_server.research('read_uploaded_document',{'document_id':'D-AAAAAAAAAAAA'})
        self.assertIn('不存在',result['data_gap'])
    async def test_workspace_versions_and_owner_isolation(self):
        from finfreedom import workspace_state
        initial=workspace_state.get_state('alice','calendar')
        saved=workspace_state.mutate('alice','calendar','create',{'expected_version':initial['version'],'kind':'event','item':{'date':'2026-10-29','title':'复盘'}})
        self.assertEqual(saved['version'],1)
        self.assertEqual(workspace_state.get_state('bob','calendar')['events'],[])
        with self.assertRaises(workspace_state.HTTPException):
            workspace_state.mutate('alice','calendar','create',{'expected_version':0,'kind':'event','item':{'date':'2026-10-30','title':'复盘'}})

    async def test_index_collection_persists_daily_bars(self):
        sample={'rows':[{'bar_time':'2026-01-02','open':1,'high':2,'low':1,'close':2,'volume':3}], 'source':'test','received_at':'2026-01-02T10:00:00+00:00','state':'available'}
        with patch.object(research_data,'_worker',return_value=sample):
            result=await research_data._collect_and_store(connect,'index','INDEX:SH000001',None)
        with connect() as db:
            row=db.execute('SELECT close FROM bars WHERE instrument_id=?',('INDEX:SH000001',)).fetchone()
        self.assertEqual(row['close'],2)
