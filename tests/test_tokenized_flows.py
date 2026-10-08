import copy
import unittest
from unittest.mock import patch
import fetch_tokenized_flows as f


def word(n):
    return '0x' + format(n, '064x')


class FlowHistoryTests(unittest.TestCase):
    def setUp(self):
        self.end = int(f.timestamp(f.CREATION_TIME)) + 3600
        self.snapshot = {'block': {'number': hex(f.CREATION_BLOCK+100), 'timestamp': hex(self.end), 'hash': '0x'+'1'*64}, 'values': {
            'rawSupply':word(70*f.SCALE), 'multiplier':word(2*f.SCALE), 'uiSupply':word(140*f.SCALE),
            'symbol':word(32)+word(5)[2:]+'5553444542'.ljust(64,'0'), 'decimals':word(18)}}
        base={'kind':'event','block_number':f.CREATION_BLOCK,'block_time':f.CREATION_TIME,'log_index':0,'tx_hash':'0x'+'2'*64,'block_hash':f.CREATION_HASH,'topic0':f.MULTIPLIER,'topic1':None,'topic2':None,'data':word(0)+word(f.SCALE)[2:]+word(self.end-3600)[2:]}
        self.rows=[base, dict(base, block_number=f.CREATION_BLOCK+1,log_index=1,topic0=f.TRANSFER,topic1=f.ZERO,topic2=word(1),data=word(100*f.SCALE)),dict(base, block_number=f.CREATION_BLOCK+1,log_index=2,topic0=f.TRANSFER,topic1=word(1),topic2=f.ZERO,data=word(30*f.SCALE)), {'kind':'watermark','block_number':f.CREATION_BLOCK+100}]

    def test_same_transaction_logs_are_counted_and_multiplier_does_not_create_flows(self):
        p=f.build_payload(self.rows,self.snapshot,'test')
        self.assertEqual(p['rawSupply'],str(70*f.SCALE))
        self.assertEqual(len(p['events']),2)
        self.assertEqual(p['adjustedSupply'],str(140*f.SCALE))
        self.assertEqual(p['rawMinted'],str(100*f.SCALE))

    def test_incomplete_or_unreconciled_history_is_rejected(self):
        for change in ['missing_mint','missing_burn','missing_creation','duplicate','watermark','wrong_symbol','wrong_scaled','ordinary_transfer']:
            with self.subTest(change=change):
                rows,s=copy.deepcopy(self.rows),copy.deepcopy(self.snapshot)
                if change=='missing_mint': rows.pop(1)
                if change=='missing_burn': rows.pop(2)
                if change=='missing_creation': rows.pop(0)
                if change=='duplicate': rows.insert(2,copy.deepcopy(rows[1]))
                if change=='watermark': rows[-1]['block_number']=None
                if change=='wrong_symbol': s['values']['symbol']='0x'
                if change=='wrong_scaled': s['values']['uiSupply']=word(1)
                if change=='ordinary_transfer': rows[1]['topic1']=word(2)
                with self.assertRaises(ValueError): f.build_payload(rows,s,'test')

    def test_zero_activity_is_verified_zero_not_missing(self):
        s=copy.deepcopy(self.snapshot);s['values']['rawSupply']=s['values']['uiSupply']=word(0)
        p=f.build_payload([self.rows[0],self.rows[-1]],s,'test')
        self.assertEqual(p['events'],[])
        self.assertEqual(p['rawSupply'],'0')

    def test_pagination_fetches_every_page_and_rejects_truncation(self):
        class Response:
            def __init__(self,data):self.data=data
            def raise_for_status(self):pass
            def json(self):return self.data
        for total in [4,5]:
            results=[Response({'state':'QUERY_STATE_COMPLETED','result_metadata':{'total_row_count':total}}),Response({'result':{'rows':self.rows[:2]},'next_offset':2}),Response({'result':{'rows':self.rows[2:]}})]
            with patch.object(f.requests,'post',return_value=Response({'execution_id':'test'})),patch.object(f.requests,'get',side_effect=results),patch.object(f.time,'sleep'):
                if total==4:self.assertEqual(f.query(self.snapshot,'test')['rawSupply'],str(70*f.SCALE))
                else:
                    with self.assertRaisesRegex(ValueError,'Incomplete'):f.query(self.snapshot,'test')

if __name__=='__main__':unittest.main()
