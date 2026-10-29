import json
import os
import tempfile
import unittest
from unittest.mock import patch
from finfreedom import guide_entries

class GuideEntryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.env=patch.dict(os.environ,{'FINFREEDOM_DATA_DIR':self.tmp.name});self.env.start()
    def tearDown(self): self.env.stop();self.tmp.cleanup()
    def test_builtin_favorites_are_snapshots_and_edits_are_mine(self):
        initial=guide_entries.list_entries('alice','all'); entry=next(x for x in initial['entries'] if x['id']=='builtin-01')
        guide_entries.manage('alice','favorite',{'id':entry['id'],'expected_version':0})
        changed=[dict(x) for x in guide_entries.builtin_entries()]; changed[0]['markdown']='# 新版本\n\n新内容'
        with patch.object(guide_entries,'builtin_entries',return_value=changed):
            self.assertEqual(guide_entries.list_entries('alice','favorites')['entries'][0]['markdown'],entry['markdown'])
            self.assertEqual(next(x for x in guide_entries.list_entries('alice','all')['entries'] if x['id']==entry['id'])['markdown'],entry['markdown'])
            guide_entries.manage('alice','update',{'id':entry['id'],'expected_version':1,'markdown':'# 我的版本\n\n自己写的提示'})
            self.assertEqual(guide_entries.list_entries('alice','mine')['entries'][0]['title'],'我的版本')
            self.assertEqual(guide_entries.list_entries('alice','favorites')['entries'][0]['title'],'我的版本')
            guide_entries.manage('alice','unfavorite',{'id':entry['id'],'expected_version':2})
            self.assertEqual(next(x for x in guide_entries.list_entries('alice','all')['entries'] if x['id']==entry['id'])['title'],'我的版本')
            guide_entries.manage('alice','delete',{'id':entry['id'],'expected_version':3})
            self.assertEqual(next(x for x in guide_entries.list_entries('alice','all')['entries'] if x['id']==entry['id'])['title'],'新版本')
    def test_custom_is_owner_scoped_and_stale_changes_are_rejected(self):
        r=guide_entries.manage('alice','create',{'markdown':'# 新研究\n\n执行研究','expected_version':0})
        self.assertEqual(guide_entries.list_entries('alice','mine')['entries'][0]['id'],r['id'])
        self.assertEqual(guide_entries.list_entries('bob','mine')['entries'],[])
        self.assertEqual(len(guide_entries.list_entries('alice','all')['entries']),len(guide_entries.builtin_entries()))
        with self.assertRaisesRegex(ValueError,'更新'): guide_entries.manage('alice','favorite',{'id':r['id'],'expected_version':0})
        guide_entries.manage('alice','favorite',{'id':r['id'],'expected_version':1})
        guide_entries.manage('alice','delete',{'id':r['id'],'expected_version':2})
        self.assertEqual(guide_entries.list_entries('alice','favorites')['entries'][0]['title'],'新研究')
    def test_new_builtins_sort_before_old_ones_and_keep_categories(self):
        from datetime import date
        with patch.object(guide_entries, '_is_new', side_effect=lambda row: bool(row.get('added_at'))):
            entries=guide_entries.list_entries('alice','all')['entries']
            self.assertTrue(entries[0]['is_new'])
            first_old=next(i for i,x in enumerate(entries) if not x['is_new'])
            self.assertTrue(all(x['is_new'] for x in entries[:first_old]))
            self.assertTrue(all(not x['is_new'] for x in entries[first_old:]))
            self.assertIn('组合与风险',{x['group'] for x in entries})
            self.assertIn('财务与估值',{x['group'] for x in entries})

    def test_validation(self):
        with self.assertRaisesRegex(ValueError,'一级标题'): guide_entries.manage('alice','create',{'markdown':'没有标题','expected_version':0})
        with self.assertRaises(ValueError): guide_entries.manage('alice','favorite',{'id':'../../bad','expected_version':0})

if __name__ == '__main__': unittest.main()

class GuideCatalogTests(unittest.TestCase):
    def test_all_entries_have_unique_stable_ids_and_bundled_skills(self):
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        entries=guide_entries.builtin_entries()
        self.assertGreaterEqual(len(entries),58)
        bundled={p.parent.name for p in (root/'skills').glob('*/SKILL.md')}
        referenced={skill for entry in entries for skill in entry['skills']}
        self.assertEqual(bundled, referenced)
        self.assertEqual(len({x['id'] for x in entries}),len(entries))
        for entry in entries:
            self.assertTrue(entry['group'])
            for skill in entry['skills']:
                self.assertTrue((root/'skills'/skill/'SKILL.md').is_file(), skill)
                self.assertIn(skill,entry['markdown'])
    def test_new_badge_has_a_bounded_lifetime(self):
        from datetime import date
        row={'added_at':'2026-10-29'}
        self.assertTrue(guide_entries._is_new(row,date(2026,10,29)))
        self.assertTrue(guide_entries._is_new(row,date(2026,11,27)))
        self.assertFalse(guide_entries._is_new(row,date(2026,11,28)))
        self.assertFalse(guide_entries._is_new(row,date(2026,10,28)))
