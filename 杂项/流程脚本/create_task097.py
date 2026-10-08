import sys
import uuid
from pathlib import Path

sys.path.insert(0, r'C:\Users\12187\.config\opencode\vibe-workflow\scripts')
from state_context import apply_command, open_store, refresh_views  # noqa: E402

root = Path(r'D:\Project\vibe-coding')


def apply(action, payload):
    store = open_store(root, heal=True)
    apply_command(root, {
        'schema_version': 1, 'command_id': uuid.uuid4().hex,
        'expected_revision': store.status()['revision'],
        'action': action, 'payload': payload,
    })
    print('OK', action, payload.get('id') or payload.get('task_id'))


apply('task.create', {
    'id': 'TASK-098',
    'title': '鏍告煡 Windows 骞冲彴娴嬭瘯澶辫触鎶ュ憡锛? 绫?21 椤癸級骞惰褰曠粨璁?,
    'goal_id': None,
    'extensions': {
        'authority': 'B',
        'kind': 'task',
        'phase': 'verification',
        'risk': 'standard',
        'implementer': 'vibe-main (opencode main agent, serial-role-fallback)',
        'inputs': ['澶栭儴 agent 鎻愪氦鐨?Windows 骞冲彴娴嬭瘯澶辫触鎶ュ憡锛? 绫绘牴鍥犮€?1 椤瑰け璐ワ級'],
        'done_when': [
            '閫愭潯鍒ゅ畾鎶ュ憡 5 绫绘牴鍥犵殑鐪熷疄鎬э細浜у搧浠ｇ爜 bug / 娴嬭瘯涓嶅吋瀹?/ 涓嶆垚绔?,
            '姣忔潯缁撹闄勪唬鐮佷綅缃垨瀹炶窇杈撳嚭浣滀负璇佹嵁',
            '澶嶇幇鎬绘暟涓庢姤鍛婁竴鑷达紙246 tests / 8 failures / 13 errors / 3 skipped锛夋垨璇存槑宸紓',
            '鏍稿疄"浜у搧 bug"杩欎竴绫绘槸鍚︾湡鐨勫瓨鍦ㄤ簬瀵瑰濂戠害锛堝畨瑁呯姸鎬佹枃浠讹級',
            '璁板綍鏈獙璇侀」涓庡缓璁殑鍚庣画鍔ㄤ綔',
        ],
        'related_business_logic': [],
        'plan': [
            '璇诲彇琚寚璁ょ殑浠ｇ爜浣嶇疆锛坕nstaller 鐩稿璺緞銆乻ymlink 璋冪敤鐐广€乻ubprocess encoding銆乻him銆佸彲鎵ц浣嶆柇瑷€锛?,
            '瀹炶窇鐩爣娴嬭瘯鎶撲綇鍘熷鎶ラ敊锛屼笌鎶ュ憡鎻忚堪閫愭潯姣斿',
            '瀹炶窇鍏ㄩ噺濂椾欢纭璁℃暟涓庡垎绫诲垎甯?,
            '杈撳嚭鏍告煡缁撹骞跺綊妗?,
        ],
        'outputs': ['EV-WIN-AUDIT-001'],
    },
})

apply('task.begin', {
    'task_id': 'TASK-098',
    'run_id': 'RUN-109',
    'next_action': '閫愭潯鏍告煡鎶ュ憡缁撹骞舵姄鍙栦唬鐮?瀹炶窇璇佹嵁',
})

print('revision', refresh_views(root)['revision'])

