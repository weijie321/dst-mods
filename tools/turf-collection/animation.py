"""读取 DST ANIM v4 中的 bank 与动画名，用于检查拷贝资源的实际契约。"""
import struct
import zipfile


def inspect_animation(path):
    with zipfile.ZipFile(path) as archive:
        raw = archive.read('anim.bin')
        build = archive.read('build.bin')
    assert raw[:4] == b'ANIM' and struct.unpack_from('<I', raw, 4)[0] == 4, path
    count = struct.unpack_from('<I', raw, 20)[0]
    offset = 24

    def uint():
        nonlocal offset
        value = struct.unpack_from('<I', raw, offset)[0]
        offset += 4
        return value

    def string():
        nonlocal offset
        size = uint()
        value = raw[offset:offset+size].decode('utf-8')
        offset += size
        return value

    animations = []
    for _ in range(count):
        name = string()
        offset += 1
        bank = uint()
        offset += 4
        for _ in range(uint()):
            offset += 16
            events = uint()
            offset += events * 4
            elements = uint()
            offset += elements * 40
        animations.append((bank, name))
    hashes = {}
    for _ in range(uint()):
        value = uint()
        hashes[value] = string()
    assert offset == len(raw), (path, offset, len(raw))
    assert build[:4] == b'BILD'
    size = struct.unpack_from('<I', build, 16)[0]
    build_name = build[20:20+size].decode('utf-8')
    return build_name, {(hashes[bank], name) for bank, name in animations}
