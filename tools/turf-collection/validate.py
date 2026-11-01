"""校验全部来源、拷贝资源和生成的图集，不依赖 Steam 或 Lua stub。"""
from pathlib import Path
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from animation import inspect_animation
from icons import region_size


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
        if rel.startswith('images/inventoryimages/'):
            assert not {'mapicons', 'map_icons', 'fx', 'ui'} & set(Path(origin['file']).parts), (rel, origin['file'])
        source = args.workshop_root/origin['source_id']/origin['file']
        assert hashlib.sha256(source.read_bytes()).hexdigest() == origin['sha256'], source
        dest = args.mod/rel
        assert dest.is_file(), dest
        if dest.suffix != '.xml' or 'output_sha256' in origin:
            assert hashlib.sha256(dest.read_bytes()).hexdigest() == origin.get('output_sha256', origin['sha256']), dest
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
        doc = ET.parse(atlas)
        texture = atlas.with_name(doc.find('Texture').attrib['filename'])
        origin = data['resources'].get(texture.relative_to(args.mod).as_posix())
        if origin:
            assert not {'mapicons', 'map_icons', 'fx', 'ui'} & set(Path(origin['file']).parts), (tile['name'], origin['file'])
        icon_source = tile['icon_source']
        assert icon_source['file'] == (origin['file'] if origin else None), tile['name']
        if icon_source['declared']:
            assert Path(icon_source['element']).stem == icon_source['declared'], tile['name']
        if not tile['icon_preview']:
            source_atlas = args.workshop_root/tile['source']/icon_source['atlas']
            elements = ET.parse(source_atlas).findall('./Elements/Element')
            assert any(e.attrib['name'] == icon_source['element'] for e in elements), tile['name']
        if tile['name'] == 'tc_3544387985_tbat_turf_water_lily_cat':
            assert icon_source['file'] == 'atbooks1/images/inventoryimages/tbat_turf_water_lily_cat_leaf.tex', icon_source
        width, height = region_size(texture, doc.find('./Elements/Element').attrib)
        assert 0 < width <= 64 and 0 < height <= 64, (tile['name'], width, height)
        turf = tile['turf']
        anim = args.mod/'anim'/(turf['animzip_override']+'.zip')
        if not anim.is_file():
            anim = args.dst_root/'data/anim'/(turf['animzip_override']+'.zip')
        build, animations = inspect_animation(anim)
        assert build == turf['build_override'], (tile['original'],build,turf)
        assert (turf['bank_override'],turf['anim']) in animations, (tile['original'],animations,turf)
    print('通过：11个来源、130种地皮、来源指纹、图标用途与声明、图集、动画 bank/build/anim 及资源闭包')


if __name__ == '__main__':
    main()
