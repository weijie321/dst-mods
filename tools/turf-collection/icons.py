"""限制物品图标的实际图集区域，避免原版配方预览按地纹原尺寸显示。"""
import struct


def region_size(texture, attrs):
    raw = texture.read_bytes()
    assert raw[:4] == b'KTEX', texture
    width, height = struct.unpack_from('<HH', raw, 8)
    return (width * abs(float(attrs['u2']) - float(attrs['u1'])),
            height * abs(float(attrs['v2']) - float(attrs['v1'])))


def inventory_icon(texture, attrs):
    raw = texture.read_bytes()
    if max(region_size(texture, attrs)) <= 64:
        return raw, attrs
    from PIL import Image

    # KTEX 的位域和 mip 表按 ktools src/common/ktex/specs.cpp、ktex.cpp。
    header, = struct.unpack_from('<I', raw, 4)
    compression, mipmaps = (header >> 4) & 31, (header >> 13) & 31
    assert mipmaps > 0 and ((header >> 9) & 15) == 1, texture
    width, height, pitch, size = struct.unpack_from('<HHHI', raw, 8)
    offset = 8 + mipmaps * 10
    pixels = raw[offset:offset + size]
    assert len(pixels) == size, texture
    if compression in (0, 1, 2):
        image = Image.frombytes('RGBA', (width, height), pixels, 'bcn', (compression + 1,))
    else:
        assert compression in (4, 5), (texture, compression)
        mode = 'RGBA' if compression == 4 else 'RGB'
        image = Image.frombytes(mode, (width, height), pixels, 'raw', mode, pitch).convert('RGBA')
    # 保持 TEX 自身的垂直方向；裁切和重新编码均使用同一坐标系。
    box = (round(float(attrs['u1']) * width), round(float(attrs['v1']) * height),
           round(float(attrs['u2']) * width), round(float(attrs['v2']) * height))
    image = image.crop(box)
    image.thumbnail((64, 64), Image.Resampling.LANCZOS)
    canvas = Image.new('RGBA', (64, 64))
    canvas.paste(image, ((64 - image.width) // 2, (64 - image.height) // 2))
    pixels = canvas.tobytes()
    # 单层 RGBA 图标；地面纹理和原共享图集保持原样。
    output = b'KTEX' + struct.pack('<IHHHI', 0xFFFC2240, 64, 64, 256, len(pixels)) + pixels
    return output, dict(u1='0', u2='1', v1='0', v2='1')
