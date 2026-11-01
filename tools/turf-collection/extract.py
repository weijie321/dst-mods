"""从点名的本地创意工坊副本只读抽取声明；中间证据保存在仓库外。"""
from pathlib import Path
import argparse
import base64
import json
import re
import subprocess

SOURCES = [
    ('2979177306', '海洋传说', ['main/worldgen/terrain.lua']),
    ('3349143694', '荔只只', ['modworldgenmain.lua']),
    ('3609964985', '丰耘秘境', ['modworldgenmain.lua']),
    ('3288149713', '童话世界', ['scripts/prefabs/ft_turfs_def.lua']),
    ('3544387985', '万物书', ['atbooks1/scripts/_key_modules_of_tbat/10_turfs/0[1-9]_*.lua', 'atbooks1/scripts/_key_modules_of_tbat/10_turfs/1[0-4]_*.lua', 'atbooks2/scripts/tbat_tiledefs.lua']),
    ('3597024951', '景熹家居', ['miao/jx_turfs.lua']),
    ('3361615927', '田园物语', ['scripts/jt_tilesdefs.lua']),
    ('3393876841', '花仙子', ['modworldgenmain.lua']),
    ('1289779251', '新版樱花林', ['init/init_tiles.lua']),
    ('3626093627', '炊烟袅袅', ['scripts/_key_modules_of_niaoniao/08_turfs/[0-9]*.lua']),
    ('3283650699', '悠', ['modworldgenmain.lua']),
]


def decode_source(raw):
    match = re.search(rb'=\{(\d+),(\d+),"([A-Za-z0-9+/]+)"\}', raw[:len(raw)])
    if raw.startswith(b'if true then local') and match:
        seed, expected = int(match[1]), int(match[2])
        result = bytearray()
        for value in base64.b64decode(match[3] + b'=' * (-len(match[3]) % 4)):
            seed = (seed * 1664525 + 1013904223) % 2**32
            result.append((value - seed % 256) % 256)
        checksum = 0
        for value in result:
            checksum = (checksum * 131 + value) % 2**32
        assert checksum == expected, '来源校验不匹配'
        return bytes(result)
    if b'l_knm' in raw[:30] or raw[:1] == b'\x03':
        return bytes((value + 7) % 256 for value in raw[::-1])
    return raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workshop-root', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    args.evidence.mkdir(parents=True, exist_ok=True)
    sources = []
    for workshop_id, title, patterns in SOURCES:
        root = args.workshop_root / workshop_id
        tiles, captures = [], []
        for pattern in patterns:
            paths = sorted(root.glob(pattern))
            assert paths, (workshop_id, pattern)
            for path in paths:
                raw = decode_source(path.read_bytes())
                if workshop_id == '3609964985':
                    raw = raw[:raw.index(b'local LAYOUTS=')]
                elif workshop_id == '3393876841':
                    raw = raw[:raw.index(b'-- =================================================================')]
                elif workshop_id == '3283650699':
                    raw = raw[raw.index(b'local TileRanges'):raw.index(b'Layouts["gentleness_cat_land"]')]
                entry = args.evidence / f'{workshop_id}-{path.name}'
                entry.write_bytes(raw)
                process = subprocess.run(['lua', str(Path(__file__).with_name('capture.lua')), root.as_posix(), entry.as_posix()], capture_output=True, timeout=50)
                assert process.returncode == 0, process.stderr.decode(errors='replace')
                try:
                    captured = json.loads(process.stdout.decode('utf-8'))
                except UnicodeDecodeError:
                    captured = json.loads(process.stdout.decode('gb18030', errors='replace'))
                captures.append({'file':path.relative_to(root).as_posix(), **captured})
                tiles.extend(captured['tiles'] if isinstance(captured['tiles'], list) else [])
                print(workshop_id, path.name, len(captured['tiles']), captured.get('error', 'ok'), flush=True)
        source = {'id': workshop_id, 'title': title, 'tiles': tiles, 'captures': captures}
        sources.append(source)
    (args.evidence/'captured.json').write_text(json.dumps(sources, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
