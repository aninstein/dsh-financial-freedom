import os
import tempfile
import unittest
from unittest.mock import patch
from finfreedom import memory

class MemoryTest(unittest.TestCase):
    def test_owner_scope_and_conflict(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'FINFREEDOM_DATA_DIR':directory}):
            result=memory.remember('alice','偏好分散投资','long-term')
            key=result['entry_id']; path='long-term/'+key+'.md'
            self.assertEqual(len(memory.entries('alice')),1)
            self.assertEqual(memory.entries('bob'),[])
            self.assertFalse(memory.remember('alice','偏好分散投资','long-term')['created'])
            doc=memory.document('alice',path)
            memory.save('alice',path,'偏好低波动',doc['sha256'])
            with self.assertRaises(ValueError): memory.save('alice',path,'覆盖',doc['sha256'])
            self.assertEqual(memory.document('alice',path)['content'],'偏好低波动')
            self.assertFalse(memory.delete('bob',key)['deleted'])
            self.assertTrue(memory.delete('alice',key)['deleted'])
            self.assertEqual(memory.entries('alice'),[])

if __name__ == '__main__': unittest.main()
