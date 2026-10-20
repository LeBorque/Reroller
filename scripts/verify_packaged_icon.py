# Python 3.14 | scripts/verify_packaged_icon.py | Windows shell icon verification
import ctypes as c
from ctypes import wintypes as w
import hashlib
import json
from pathlib import Path
import struct

import pefile


ROOT = Path(__file__).resolve().parent.parent


def verify_resources(executable, icon):
    contents = icon.read_bytes()
    count = struct.unpack_from('<H', contents, 4)[0]
    expected = []
    for index in range(count):
        size, offset = struct.unpack_from('<II', contents, 6 + index * 16 + 8)
        expected.append(contents[offset:offset + size])
    actual = []
    with pefile.PE(str(executable)) as binary:
        for resource in binary.DIRECTORY_ENTRY_RESOURCE.entries:
            if resource.id == 3:
                for item in resource.directory.entries:
                    for language in item.directory.entries:
                        entry = language.data.struct
                        actual.append(binary.get_data(entry.OffsetToData, entry.Size))
    assert set(actual) == set(expected), 'EXE icon resources differ from the generated ICO'
    return {'embedded_images': len(actual), 'all_images_match_ico': True,
            'png_sha256': hashlib.sha256((ROOT / 'assets/reroller_icon.png').read_bytes()).hexdigest()}


def shell_icon(path):
    class FileInfo(c.Structure):
        _fields_ = [('hIcon', w.HICON), ('iIcon', c.c_int), ('attributes', w.DWORD),
                    ('displayName', w.WCHAR * 260), ('typeName', w.WCHAR * 80)]
    function = c.windll.shell32.SHGetFileInfoW
    function.argtypes = [w.LPCWSTR, w.DWORD, c.POINTER(FileInfo), w.UINT, w.UINT]
    function.restype = c.c_size_t
    info = FileInfo()
    if not function(str(path), 0, c.byref(info), c.sizeof(info), 0x100):
        raise OSError(f'No shell icon for {path}')
    return info.hIcon


def icon_pixels(handle):
    class IconInfo(c.Structure):
        _fields_ = [('isIcon', w.BOOL), ('xHotspot', w.DWORD), ('yHotspot', w.DWORD),
                    ('mask', w.HBITMAP), ('color', w.HBITMAP)]
    class Bitmap(c.Structure):
        _fields_ = [('type', w.LONG), ('width', w.LONG), ('height', w.LONG), ('widthBytes', w.LONG),
                    ('planes', w.WORD), ('bitsPixel', w.WORD), ('bits', c.c_void_p)]
    class Header(c.Structure):
        _fields_ = [('size', w.DWORD), ('width', w.LONG), ('height', w.LONG), ('planes', w.WORD),
                    ('bitCount', w.WORD), ('compression', w.DWORD), ('imageSize', w.DWORD),
                    ('xPelsPerMeter', w.LONG), ('yPelsPerMeter', w.LONG), ('clrUsed', w.DWORD), ('clrImportant', w.DWORD)]
    user, gdi = c.windll.user32, c.windll.gdi32
    user.GetIconInfo.argtypes = [w.HICON, c.POINTER(IconInfo)]
    gdi.GetObjectW.argtypes = [w.HANDLE, c.c_int, c.c_void_p]
    gdi.CreateCompatibleDC.argtypes, gdi.CreateCompatibleDC.restype = [w.HDC], w.HDC
    gdi.GetDIBits.argtypes = [w.HDC, w.HBITMAP, w.UINT, w.UINT, c.c_void_p, c.c_void_p, w.UINT]
    gdi.DeleteObject.argtypes, gdi.DeleteDC.argtypes = [w.HANDLE], [w.HDC]
    info, bitmap = IconInfo(), Bitmap()
    if not user.GetIconInfo(handle, c.byref(info)):
        raise OSError('GetIconInfo failed')
    dc = None
    try:
        if not gdi.GetObjectW(info.color, c.sizeof(bitmap), c.byref(bitmap)):
            raise OSError('No icon color bitmap')
        header = Header(c.sizeof(Header), bitmap.width, -bitmap.height, 1, 32)
        pixels = c.create_string_buffer(bitmap.width * bitmap.height * 4)
        dc = gdi.CreateCompatibleDC(None)
        if gdi.GetDIBits(dc, info.color, 0, bitmap.height, pixels, c.byref(header), 0) != bitmap.height:
            raise OSError('Cannot read icon pixels')
        return (bitmap.width, bitmap.height), pixels.raw
    finally:
        if dc:
            gdi.DeleteDC(dc)
        gdi.DeleteObject(info.color)
        gdi.DeleteObject(info.mask)


def main():
    executable, icon = ROOT / 'dist/PoE2Reroller.exe', ROOT / 'assets/reroller_icon.ico'
    desktop = Path.home() / 'Desktop/PoE 2 Reroller.lnk'
    report = verify_resources(executable, icon)
    handles = []
    try:
        reference = shell_icon(icon)
        handles.append(reference)
        expected_size, expected = icon_pixels(reference)
        for name, path in [('explorer_exe', executable), ('desktop_shortcut', desktop)]:
            handle = shell_icon(path)
            handles.append(handle)
            dimensions, pixels = icon_pixels(handle)
            assert dimensions == expected_size, f'{name} has unexpected icon dimensions'
            differences = [(index % dimensions[0], index // dimensions[0]) for index in range(len(pixels) // 4)
                           if pixels[index * 4:index * 4 + 4] != expected[index * 4:index * 4 + 4]]
            if name == 'desktop_shortcut':
                # Windows draws its shortcut arrow over the lower-left part of the artwork.
                assert all(x < dimensions[0] // 2 and y >= dimensions[1] // 2 for x, y in differences), 'Shortcut artwork differs outside the arrow overlay'
            else:
                assert not differences, f'{name} shell icon does not match'
            report[name] = {'matches_artwork': True, 'shortcut_arrow': bool(differences),
                            'size': dimensions, 'pixel_sha256': hashlib.sha256(pixels).hexdigest()}
        report['ok'] = True
        (ROOT / 'artifacts/icons-1.2.9.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report))
    finally:
        c.windll.user32.DestroyIcon.argtypes = [w.HICON]
        for handle in handles:
            c.windll.user32.DestroyIcon(handle)


if __name__ == '__main__':
    main()
