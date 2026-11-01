"""校验全部来源、拷贝资源和生成的图集，不依赖 Steam 或 Lua stub。"""
from pathlib import Path
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from animation import inspect_animation


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mod', type=Path, required=True)
    p.add_argument('--workshop-root', type=Path, required=True)
    p.add_argument('--dst-root', type=Path, required=True)
    args = p.parse_args()
    data = json.loads((args.mod/'SOURCES.json').read_text(encoding='utf-8'))
    assert len(data['sources']) == 11
    assert len(data['tiles']) == sum(s['count'] for s in data['sources']) == 130
    assert len({t['tile'] for t in data['tiles']}) == len(data['tiles'])
    for src in data['sources']:
        root = args.workshop_root/src['id']
        assert hashlib.sha256((root/'modinfo.lua').read_bytes()).hexdigest() == src['modinfo_sha256']
        for decl in src['declarations'] + src.get('supporting_files', []):
            assert hashlib.sha256((root/decl['file']).read_bytes()).hexdigest() == decl['sha256']
    for rel, origin in data['resources'].items():
        source = args.workshop_root/origin['source_id']/origin['file']
        assert hashlib.sha256(source.read_bytes()).hexdigest() == origin['sha256'], source
        dest = args.mod/rel
        assert dest.is_file(), dest
        if dest.suffix != '.xml':
            assert hashlib.sha256(dest.read_bytes()).hexdigest() == origin['sha256'], dest
    for atlas in args.mod.rglob('*.xml'):
        doc = ET.fromstring(atlas.read_bytes())
        name = doc.find('Texture').attrib['filename']
        texture = args.mod/name if '/' in name else atlas.with_name(name)
        assert texture.is_file(), (atlas, texture)
    for tile in data['tiles']:
        assert tile['tile'].startswith('TC_') and tile['name'].startswith('tc_')
        assert not tile['display'].startswith('地皮 '), tile['original']
        assert 'cannotbedug' not in tile['ground'] and 'istemptile' not in tile['ground']
        for definition in [tile['ground'], tile['mini']]:
            for folder, field, ext in [('tiles','name','tex'),('tiles','atlas','xml'),('textures','noise_texture','tex')]:
                rel = f'levels/{folder}/{definition[field]}.{ext}'
                assert (args.mod/rel).is_file() or (args.dst_root/'data'/rel).is_file(), rel
        atlas = args.mod/'images/inventoryimages'/('turf_'+tile['name']+'.xml')
        assert ET.parse(atlas).find('./Elements/Element').attrib['name'] == 'turf_'+tile['name']+'.tex'
        turf = tile['turf']
        anim = args.mod/'anim'/(turf['animzip_override']+'.zip')
        if not anim.is_file():
            anim = args.dst_root/'data/anim'/(turf['animzip_override']+'.zip')
        build, animations = inspect_animation(anim)
        assert build == turf['build_override'], (tile['original'],build,turf)
        assert (turf['bank_override'],turf['anim']) in animations, (tile['original'],animations,turf)
    print('通过：11个来源、130种地皮、来源指纹、图集、动画 bank/build/anim 及资源闭包')


if __name__ == '__main__':
    main()
