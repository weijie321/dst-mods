# Official DST texture notes

Source checked:

- Klei `ds_mod_tools` README
- `pkg/cmn/mod_tools/compiler_scripts/image_build.py`
- `pkg/cmn/mod_tools/compiler_scripts/properties.py`
- `pkg/cmn/mod_tools/png.txt`
- Local DST atlas samples under `S:\game\steam\steamapps\common\Don't Starve Together\data`

## What Klei tools do

The official mod-tools flow is designed around the autocompiler. Its `png`
compiler processes PNG files placed in these mod directories:

- `images`
- `bigportraits`

The image compiler converts each PNG into a same-name `.tex` file and writes a
same-name `.xml` atlas file. For example:

```text
images/inventoryimages/wanda_timebox_1.png
images/inventoryimages/wanda_timebox_1.tex
images/inventoryimages/wanda_timebox_1.xml
```

The generated XML has the usual DST atlas shape:

```xml
<Atlas>
  <Texture filename="wanda_timebox_1.tex" />
  <Elements>
    <Element name="wanda_timebox_1.tex" u1="..." u2="..." v1="..." v2="..." />
  </Elements>
</Atlas>
```

## Size rules

The compiler asserts that image width and height are multiples of 4.

Official tool properties define:

```python
ImageProperties = {
    "inventoryimages": {
        "width": 64,
        "height": 64,
    },
    "road": {
        "border": 4,
    }
}
```

Use 64x64 PNGs for inventory item icons unless a specific DST UI surface has a
different established size.

## Lua registration pattern

For a custom inventory item:

```lua
Assets = {
    Asset("ATLAS", "images/inventoryimages/wanda_timebox_1.xml"),
    Asset("IMAGE", "images/inventoryimages/wanda_timebox_1.tex"),
}

RegisterInventoryItemAtlas("images/inventoryimages/wanda_timebox_1.xml", "wanda_timebox_1.tex")
```

Then point recipes and inventory items at the same atlas/image pair:

```lua
atlas = "images/inventoryimages/wanda_timebox_1.xml"
image = "wanda_timebox_1.tex"
```

```lua
inst.components.inventoryitem.atlasname = "images/inventoryimages/wanda_timebox_1.xml"
inst.components.inventoryitem.imagename = "wanda_timebox_1"
```

For UI visual tests, capture the rendered game result as a screenshot template;
do not use the source PNG directly as the OpenCV template unless the UI renders
it at the same scale and with the same background.
