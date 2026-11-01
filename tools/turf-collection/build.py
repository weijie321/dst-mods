"""从已捕获的地皮声明构建独立合集及来源清单，不改动创意工坊副本。"""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import re
import xml.etree.ElementTree as ET

from extract import decode_source
from icons import inventory_icon


def lua(value):
    if value is None:
        return 'nil'
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return '{' + ','.join(map(lua, value)) + '}'
    return '{' + ','.join('[' + lua(k) + ']=' + lua(v) for k, v in sorted(value.items())) + '}'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workshop-root', type=Path, required=True)
    p.add_argument('--captured', type=Path, required=True)
    p.add_argument('--dst-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    sources = json.loads(args.captured.read_text(encoding='utf-8'))
    output = args.output
    output.mkdir(exist_ok=True)
    previous = json.loads((output/'SOURCES.json').read_text(encoding='utf-8')) if (output/'SOURCES.json').exists() else {}
    manifest, entries, assets, summary = {}, [], set(), []

    def write(rel, content):
        dest = output / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)

    for src in sources:
        mid = src['id']
        root = args.workshop_root / mid
        roots = [root, root/'atbooks1', root/'atbooks2']
        for cap in src['captures']:
            assert cap['ok'], (mid, cap.get('error'))
        assert src['tiles'], f'{mid} 未捕获到地皮'

        def find(rel):
            return next((r/rel for r in roots if (r/rel).is_file()), None)

        def record(source, dest, content=None):
            raw = source.read_bytes()
            manifest[dest] = {'source_id':mid, 'file':source.relative_to(root).as_posix(),
                              'sha256':hashlib.sha256(raw).hexdigest()}
            if content is not None:
                manifest[dest]['output_sha256'] = hashlib.sha256(content).hexdigest()
            write(dest, content if content is not None else raw)

        def surface(name, folder, ext):
            base = Path(name).stem
            rel = f'levels/{folder}/{base}.{ext}'
            source = find(rel)
            if not source:
                assert (args.dst_root/'data'/rel).is_file(), f'资源缺失: {mid}/{rel}'
                return base
            target = f'tc_{mid}_{base}'
            if ext == 'xml':
                doc = ET.fromstring(source.read_bytes())
                texture = doc.find('Texture')
                original = source.with_suffix('.tex')
                assert original.is_file(), original
                texture.set('filename', f'levels/{folder}/{target}.tex')
                record(original, f'levels/{folder}/{target}.tex')
                record(source, f'levels/{folder}/{target}.xml', ET.tostring(doc, encoding='utf-8'))
            else:
                record(source, f'levels/{folder}/{target}.tex')
            return target

        strings = {}
        for file in root.rglob('*.lua'):
            rel = file.relative_to(root).as_posix().lower()
            if not any(k in rel for k in ['string','language','legend_chs','localization','ft_turfs_def']):
                continue
            if file.stat().st_size > 1000000:
                continue
            raw = decode_source(file.read_bytes())
            try:
                text = raw.decode('utf-8-sig')
            except UnicodeDecodeError:
                text = raw.decode('gb18030', errors='replace')
            for key, value in re.findall(r'(?:STRINGS\.)?NAMES\.([A-Z0-9_]+)\s*=\s*"([^"\n]+)"', text):
                if re.search('[\u4e00-\u9fff]', value):
                    strings[key] = value
            for bracket, plain, value in re.findall(r'(?:\["([a-z0-9_]+)"\]|\b([a-z0-9_]+))\s*=\s*\{\s*(?:\["name"\]|name)\s*=\s*"([^"\n]+)"', text):
                if re.search('[\u4e00-\u9fff]', value):
                    strings[(bracket or plain).upper()] = value
            for value, key in re.findall(r'--\s*([^\n]+)\s*\n\s*tile_name\s*=\s*"([^"]+)"', text):
                strings[key.upper()] = value.strip()
            for key, value in re.findall(r'addString\("([^"]+)",\s*"([^"]+)"', text):
                strings[key.upper()] = value
        atlas_elements = {}
        for image_root in roots:
            images = image_root/'images'
            if not images.is_dir():
                continue
            for atlas in images.rglob('*.xml'):
                doc = ET.fromstring(atlas.read_bytes())
                for element in doc.findall('./Elements/Element'):
                    atlas_elements.setdefault(Path(element.attrib['name']).stem, (atlas, element))
        overrides = {
            'HMR_CHERRY_FLOWER':'樱花地皮', 'HMR_CHERRY_GRASS':'樱草地皮',
            'HMR_CHERRY_MYSTERY':'樱海秘境地皮', 'HMR_CHERRY_ROAD':'樱花小径地皮', 'HMR_CHERRY_XMM':'悉樱樱地皮',
            'CHERRIFT':'樱花裂隙地纹', 'GENTLENESS_GREEN':'绿色地皮',
            'GENTLENESS_STRAWBERRY':'草莓地皮', 'GENTLENESS_STAR':'星星地皮',
            'JX_DOCK':'码头地纹', 'TBAT_TURF_WATER_LILY_CAT':'睡莲猫猫地纹',
        }
        for source_tile in sorted(src['tiles'], key=lambda t:t['name'].upper()):
            tile = copy.deepcopy(source_tile)
            original_name = tile['name'].upper()
            key = f'tc_{mid}_{original_name.lower()}'
            turf = tile.get('turf') or {}
            original_turf = turf.get('name')
            display = strings.get(('turf_'+(original_turf or original_name)).upper())
            display = display or strings.get((original_turf or '').upper()) or strings.get(original_name) or overrides.get(original_name)
            display = display or (tile.get('data') or {}).get('ground_name')
            if not isinstance(display, str) or not re.search('[\u4e00-\u9fff]', display):
                display = f'地皮 {original_name}'
            # 桥的外观来自实体动画；这里仅收录其真实地面纹理。
            if original_name.startswith('LZ_BRIDGE'):
                display += '（基底地纹）'
            for definition in [tile['ground'], tile['mini']]:
                definition['name'] = surface(definition['name'], 'tiles', 'tex')
                definition['atlas'] = surface(definition.get('atlas', source_tile['ground' if definition is tile['ground'] else 'mini']['name']), 'tiles', 'xml')
                definition['noise_texture'] = surface(definition['noise_texture'], 'textures', 'tex')
            ground = tile['ground']
            adjusted = [k for k in ['cannotbedug','istemptile','isinvisibletile','nogroundoverlays','colors','ocean_depth','is_shoreline','wavetint'] if k in ground]
            for flag in adjusted:
                ground.pop(flag)
            # 不带入整套樱花音效库；使用同类型原版脚步声。
            for field in ['runsound','walksound','snowsound','mudsound']:
                if field in ground and not ground[field].startswith('dontstarve/'):
                    ground[field] = 'dontstarve/movement/' + ('run_grass' if field == 'runsound' else 'walk_grass')
            bank = turf.get('bank_override') or turf.get('bank_build') or 'turf'
            build = turf.get('build_override') or turf.get('bank_build') or 'turf'
            animzip = turf.get('animzip_override') or (build if build != 'turf' else 'turf')
            animation = turf.get('anim') or original_turf or 'forest'
            fallback = False
            if not original_turf or (bank == 'turf' and build == 'turf'):
                bank, build, animzip, animation = 'turf', 'turf', 'turf', 'forest'
                fallback = True
            if mid == '3283650699':
                # 原模组通过自有 prefab 修正了通用 AddTile 中的占位 bank/anim。
                kind = original_name.lower().removeprefix('gentleness_')
                bank = 'turf_gentleness_' + kind
                build = animzip = 'turf_gentleness' if kind == 'green' else bank
                animation = 'idle'
            animfile = find(f'anim/{animzip}.zip')
            if animfile:
                record(animfile, f'anim/{animzip}.zip')
            else:
                assert (args.dst_root/'data'/'anim'/f'{animzip}.zip').is_file(), f'物品动画缺失: {mid}/{animzip}'
            candidates = list(dict.fromkeys(filter(None, [
                'turf_'+original_turf if original_turf else None, original_turf,
                (original_turf+'_turf') if original_turf else None,
                turf.get('anim'), turf.get('invicon_override'), original_name.lower(),
            ])))
            found_icon = next((atlas_elements[name] for name in candidates if name in atlas_elements), None)
            icon = found_icon[0] if found_icon else None
            if found_icon:
                doc = ET.fromstring(icon.read_bytes())
                filename = doc.find('Texture').attrib['filename']
                texture = root/filename if '/' in filename else icon.with_name(filename)
                attrs = dict(found_icon[1].attrib)
            else:
                # 原模组没有独立物品图标的特殊地形，用对应地纹作预览。
                noise = source_tile['ground']['noise_texture']
                texture = find(f'levels/textures/{Path(noise).stem}.tex')
                if texture is None:
                    texture = args.dst_root/'data/levels/textures'/f'{Path(noise).stem}.tex'
                attrs = dict(u1='0',u2='1',v1='0',v2='1')
            name = 'turf_'+key
            icon_bytes, attrs = inventory_icon(texture, attrs)
            texture_name = f'tc_{mid}_' + hashlib.sha256(icon_bytes).hexdigest()[:16] + '.tex'
            doc = ET.Element('Atlas')
            ET.SubElement(doc,'Texture',filename=texture_name)
            attrs['name'] = name+'.tex'
            ET.SubElement(ET.SubElement(doc,'Elements'),'Element',attrs)
            if texture.is_relative_to(root):
                record(texture, f'images/inventoryimages/{texture_name}', icon_bytes)
            else:
                write(f'images/inventoryimages/{texture_name}',icon_bytes)
            write(f'images/inventoryimages/{name}.xml',ET.tostring(doc,encoding='utf-8'))
            assets.add(('ATLAS',f'images/inventoryimages/{name}.xml'))
            assets.add(('IMAGE',f'images/inventoryimages/{texture_name}'))
            entry = dict(source=mid, source_title=src['title'], original=original_name, original_turf=original_turf,
                tile=key.upper(), name=key, display=display, ground=ground, mini=tile['mini'],
                turf=dict(name=key, bank_build=build, bank_override=bank, build_override=build,
                    animzip_override=animzip, anim=animation, invicon_override=key, pickupsound=turf.get('pickupsound','cloth')),
                adjusted=adjusted, fallback_item=fallback, icon_preview=icon is None)
            entries.append(entry)
        info = root/'modinfo.lua'
        info_text = info.read_text(encoding='utf-8-sig',errors='replace')
        author = re.search(r'\bauthor\s*=\s*[\'"]([^\'"\n]+)', info_text)
        payloads = list((root/'data').rglob('*.dat')) if mid == '3609964985' else []
        if mid == '3283650699':
            payloads.append(root/'scripts/enums/gentleness_prefabs.lua')
        summary.append({'id':mid,'name':src['title'],'count':len(src['tiles']),
            'author':author[1] if author else '见原模组页面',
            'url':f'https://steamcommunity.com/sharedfiles/filedetails/?id={mid}',
            'modinfo_sha256':hashlib.sha256(info.read_bytes()).hexdigest(),
            'supporting_files':[{'file':f.relative_to(root).as_posix(),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted(payloads)],
            'declarations':[{'file':cap['file'],'sha256':hashlib.sha256((root/cap['file']).read_bytes()).hexdigest()} for cap in src['captures']]})
    names = [e['tile'] for e in entries]
    assert len(names) == len(set(names))
    write('scripts/turf_collection_catalog.lua', ('-- 自动抽取清单；来源和调整见 SOURCES.json。\nreturn '+lua(entries)+'\n').encode())
    write('scripts/turf_collection_assets.lua', ('return {\n'+''.join(f'    Asset({lua(k)}, {lua(f)}),\n' for k,f in sorted(assets))+'}\n').encode())
    write('scripts/turf_collection_icons.lua', ''.join(f'RegisterInventoryItemAtlas({lua("images/inventoryimages/turf_"+e["name"]+".xml")}, {lua("turf_"+e["name"]+".tex")})\n' for e in entries).encode())
    write('SOURCES.json',json.dumps({'sources':summary,'tiles':entries,'resources':manifest},ensure_ascii=False,indent=2).encode())
    # 清理本生成器旧版本产生的逐物品纹理，保留所有当前共用纹理。
    for old in (output/'images/inventoryimages').glob('turf_tc_*.tex'):
        old.unlink()
    for rel, info in previous.get('resources', {}).items():
        if rel not in manifest and rel.endswith('.tex'):
            old = output/rel
            if old.exists():
                assert output.resolve() in old.resolve().parents
                assert hashlib.sha256(old.read_bytes()).hexdigest() == info['sha256'], f'保留手工改动：{rel}'
                old.unlink()
    for source in summary:
        print(source['name'],source['count'])
    print('合计',len(entries),'项；资源',len(manifest))


if __name__ == '__main__':
    main()
