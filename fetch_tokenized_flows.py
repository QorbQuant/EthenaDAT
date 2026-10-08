"""USDEB mint/burn history. Dune logs must reconcile to a saved BNB block.

The existing refresh job captures a pending snapshot on every run, then queries
an earlier snapshot once Dune has had time to index it. No API key is published.
"""
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).parent
OUT = ROOT / 'output/usdeb-flows.json'
PENDING = ROOT / 'output/usdeb-flow-pending.json'
SQL = ROOT / 'research/usdeb-flows/events.sql'
TOKEN = '0xdfd3ba51d4591f243481a6f26059d1a5ee95252f'
RPC = 'https://bsc-dataseed.bnbchain.org'
DUNE = 'https://api.dune.com/api/v1'
CREATION_BLOCK = 124478553
CREATION_TIME = '2026-09-28T06:41:41Z'
CREATION_HASH = '0xb359ef78685ce30764c41ff092e9351278a1c8ae1bedba61a6a84bc14ccf607b'
TRANSFER = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
MULTIPLIER = '0x2205df4534432b2f60654a3fdb48737ffdaf3e9edb1a498bd985bc026b15b055'
OVERWRITTEN = '0x62204eb4daab41a604e7262a5dca11bd936210002ddfaa885fad182b677ff92c'
ZERO = '0x' + '0' * 64
SCALE = 10**18


def iso(stamp):
    return datetime.fromtimestamp(stamp, timezone.utc).isoformat().replace('+00:00', 'Z')


def timestamp(value):
    return datetime.fromisoformat(value.replace(' UTC', '+00:00').replace('Z', '+00:00')).timestamp()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, separators=(',', ':'), allow_nan=False) + '\n')
    temporary.replace(path)


def rpc(method, params):
    r = requests.post(RPC, json={'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}, timeout=25)
    r.raise_for_status()
    payload = r.json()
    if payload.get('error') or payload.get('result') is None:
        raise ValueError(f'BNB RPC failed: {method}')
    return payload['result']


def capture_snapshot():
    if int(rpc('eth_chainId', []), 16) != 56:
        raise ValueError('Wrong chain')
    head = rpc('eth_getBlockByNumber', ['latest', False])
    # Avoid the live tip, while remaining within the public node's state window.
    b = rpc('eth_getBlockByNumber', [hex(int(head['number'], 16) - 20), False])
    if not 0 <= time.time() - int(b['timestamp'], 16) <= 300:
        raise ValueError('Stale or future BNB block')
    fields = {'rawSupply': '0x18160ddd', 'multiplier': '0xa60bf13d', 'uiSupply': '0x9bea6429', 'symbol': '0x95d89b41', 'decimals': '0x313ce567'}
    values = {k: rpc('eth_call', [{'to': TOKEN, 'data': v}, b['number']]) for k, v in fields.items()}
    return {'block': {k: b[k] for k in ['number', 'hash', 'timestamp']}, 'values': values}


def decode_word(value):
    if not isinstance(value, str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}', value):
        raise ValueError('Invalid uint256 word')
    return int(value, 16)


def build_payload(rows, snapshot, execution_id, generated_at=None):
    b, values = snapshot['block'], snapshot['values']
    end_block, end_time = int(b['number'], 16), int(b['timestamp'], 16)
    symbol = values['symbol']
    if (not re.fullmatch(r'0x[0-9a-fA-F]{192}', symbol) or int(symbol[2:66], 16) != 32
            or int(symbol[66:130], 16) != 5 or symbol[130:140].lower() != '5553444542'
            or decode_word(values['decimals']) != 18):
        raise ValueError('Unexpected token identity or units')
    raw = decode_word(values['rawSupply'])
    multiplier = decode_word(values['multiplier'])
    adjusted = decode_word(values['uiSupply'])
    if multiplier <= 0 or raw * multiplier // SCALE != adjusted:
        raise ValueError('Adjusted supply mismatch')
    watermarks = [r for r in rows if r['kind'] == 'watermark']
    if len(watermarks) != 1 or (watermarks[0]['block_number'] or 0) < end_block:
        raise ValueError('Dune has not indexed the reconciliation block')
    events, adjustments, seen = [], [], set()
    running = minted = burned = 0
    has_initialization = False
    ordered = sorted((r for r in rows if r['kind'] == 'event'), key=lambda r: (r['block_number'], r['log_index']))
    if len(ordered) + 1 != len(rows):
        raise ValueError('Unexpected result row')
    for r in ordered:
        block, index, topic = r['block_number'], r['log_index'], r['topic0']
        t = int(timestamp(r['block_time']))
        if not CREATION_BLOCK <= block <= end_block or not timestamp(CREATION_TIME) <= t <= end_time:
            raise ValueError('Event outside verified coverage')
        if not isinstance(index, int) or index < 0:
            raise ValueError('Invalid log index')
        for key in ['tx_hash', 'block_hash']:
            if not re.fullmatch(r'0x[0-9a-fA-F]{64}', r[key] or ''):
                raise ValueError('Invalid event identity')
        identity = (block, index)
        if identity in seen:
            raise ValueError('Duplicate log event')
        seen.add(identity)
        if topic == TRANSFER:
            if r['topic1'] != ZERO and r['topic2'] != ZERO:
                raise ValueError('Ordinary transfer in supply result')
            if r['topic1'] == ZERO and r['topic2'] == ZERO:
                raise ValueError('Ambiguous mint/burn')
            direction = 'mint' if r['topic1'] == ZERO else 'burn'
            amount = decode_word(r['data'])
            if not amount:
                continue  # Zero-value events have no supply effect.
            running += amount if direction == 'mint' else -amount
            minted += amount if direction == 'mint' else 0
            burned += amount if direction == 'burn' else 0
            if running < 0:
                raise ValueError('History burns more than was minted')
            events.append({'t': t * 1000, 'kind': direction, 'rawAmount': str(amount), 'block': block, 'logIndex': index, 'tx': r['tx_hash']})
        elif topic in [MULTIPLIER, OVERWRITTEN]:
            size = 192 if topic == MULTIPLIER else 256
            if not re.fullmatch(r'0x[0-9a-fA-F]{' + str(size) + r'}', r['data'] or ''):
                raise ValueError('Invalid multiplier event')
            words = [str(int(r['data'][i:i+64], 16)) for i in range(2, len(r['data']), 64)]
            if topic == MULTIPLIER and block == CREATION_BLOCK and r['block_hash'] == CREATION_HASH:
                has_initialization = words[0] == '0' and words[1] == str(SCALE)
            else:
                adjustments.append({'t': t * 1000, 'type': 'scheduled' if topic == MULTIPLIER else 'overwritten', 'values': words, 'tx': r['tx_hash']})
        else:
            raise ValueError('Unexpected event signature')
    if not has_initialization:
        raise ValueError('Missing verified deployment event')
    if running != raw:
        raise ValueError(f'Supply does not reconcile: {running} != {raw}')
    return {'version': 1, 'symbol': 'USDEB', 'chainId': 56, 'contract': TOKEN,
            'generatedAt': generated_at or iso(time.time()), 'observedAt': iso(end_time),
            'coverageStart': CREATION_TIME, 'blockNumber': end_block, 'blockHash': b['hash'],
            'rawSupply': str(raw), 'rawMinted': str(minted), 'rawBurned': str(burned),
            'multiplier': str(multiplier), 'adjustedSupply': str(adjusted),
            'reconciled': True, 'executionId': execution_id, 'events': events, 'adjustments': adjustments}


def query(snapshot, api_key):
    b = snapshot['block']
    sql = SQL.read_text().replace('{{end_date}}', iso(int(b['timestamp'], 16))[:10]).replace('{{end_block}}', str(int(b['number'], 16)))
    headers = {'X-Dune-API-Key': api_key}
    r = requests.post(DUNE + '/sql/execute', headers=headers, json={'sql': sql, 'performance': 'medium'}, timeout=60)
    r.raise_for_status()
    execution = r.json()['execution_id']
    for _ in range(90):
        time.sleep(4)
        r = requests.get(f'{DUNE}/execution/{execution}/status', headers=headers, timeout=30)
        r.raise_for_status()
        status = r.json()
        if status['state'] == 'QUERY_STATE_COMPLETED':
            break
        if status.get('is_execution_finished'):
            raise ValueError(f'Dune query ended {status["state"]}')
    else:
        raise TimeoutError('Dune query timed out')
    rows, offset = [], 0
    while True:
        r = requests.get(f'{DUNE}/execution/{execution}/results', headers=headers, params={'limit': 10000, 'offset': offset}, timeout=60)
        r.raise_for_status()
        result = r.json()
        rows.extend(result['result']['rows'])
        if result.get('next_offset') is None:
            break
        new_offset = result['next_offset']
        if not isinstance(new_offset, int) or new_offset <= offset:
            raise ValueError('Invalid result pagination')
        offset = new_offset
    if len(rows) != status['result_metadata']['total_row_count']:
        raise ValueError('Incomplete Dune result')
    print(f'USDEB: {len(rows)} source rows; {status.get("execution_cost_credits", "unknown")} Dune credits')
    return build_payload(rows, snapshot, execution)


def main():
    key = os.environ.get('DUNE_API_KEY')
    if not key:
        print('USDEB: DUNE_API_KEY unavailable; preserving existing history')
        return
    try:
        previous = json.loads(PENDING.read_text())
    except (OSError, ValueError):
        previous = None
    snapshot = capture_snapshot()
    write_json(PENDING, snapshot)
    if OUT.exists():
        published = json.loads(OUT.read_text())
        if time.time() - timestamp(published['generatedAt']) < 6 * 3600:
            print('USDEB: history refreshed within six hours; no query credits used')
            return
    if not previous or time.time() - int(previous['block']['timestamp'], 16) < 15 * 60:
        print('USDEB: saved reconciliation block; awaiting the next refresh after Dune indexing')
        return
    # Reject a reorg before relying on the saved supply checkpoint.
    canonical = rpc('eth_getBlockByNumber', [previous['block']['number'], False])
    if canonical['hash'] != previous['block']['hash']:
        raise ValueError('Reconciliation block changed')
    payload = query(previous, key)
    write_json(OUT, payload)
    print(f'USDEB: published {len(payload["events"])} mint/burn events through {payload["observedAt"]}')


if __name__ == '__main__':
    main()
