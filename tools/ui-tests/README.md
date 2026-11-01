# DST 可选图像探针

本目录保留手动截图模板探针，依赖见 `requirements.txt`。它不是统一验收的必需项，
也不证明真实客户端行为通过。日常开发和验收使用 `../dst.ps1 verify`，规则见
`../DST_TESTING.md`。需要像素外观测试时，再为具体需求补模板与断言。

## Recommended workflow

1. Start DST in a stable window size and UI scale.
2. Navigate once to the screen you want to test.
3. Capture a template from the screen.
4. Reuse the template in later probes.

## Capture a template

Move the mouse to the top-left corner of the target region, press Enter, then move
to the bottom-right corner and press Enter.

```powershell
E:\work\code\dst-mods\.venv\Scripts\python.exe E:\work\code\dst-mods\tools\ui-tests\dst_ui_probe.py capture --name skilltree_wanda_root
```

Templates are saved under:

```text
E:\work\code\dst-mods\tools\ui-tests\templates
```

## Find or click a template

```powershell
E:\work\code\dst-mods\.venv\Scripts\python.exe E:\work\code\dst-mods\tools\ui-tests\dst_ui_probe.py find --template skilltree_wanda_root.png --threshold 0.82
```

```powershell
E:\work\code\dst-mods\.venv\Scripts\python.exe E:\work\code\dst-mods\tools\ui-tests\dst_ui_probe.py click --template skilltree_wanda_root.png --threshold 0.82
```

## Check simple animation movement

This compares screenshots from a screen region over time. It is useful for
catching a completely frozen animation, not for proving exact animation quality.

```powershell
E:\work\code\dst-mods\.venv\Scripts\python.exe E:\work\code\dst-mods\tools\ui-tests\dst_ui_probe.py motion --region 600,300,180,180 --seconds 2 --min-diff 1.5
```

## Template rules

Keep templates small and specific. Capture the icon, button, or animation region
only, not the whole screen. Keep the DST resolution and UI scale stable when
running visual probes. Use different templates for different languages or UI
scales when text is involved.
