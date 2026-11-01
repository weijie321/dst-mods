from __future__ import annotations

from pathlib import Path

from airtest.core.api import Template, assert_exists, auto_setup, exists, snapshot, touch


ROOT = Path(__file__).resolve().parent
TEMPLATE_DIR = ROOT / "templates"


auto_setup(__file__, devices=["Windows:///"])


def template(name: str, threshold: float = 0.82) -> Template:
    return Template(str(TEMPLATE_DIR / name), threshold=threshold)


def main() -> None:
    # Replace these filenames with templates captured by dst_ui_probe.py.
    skilltree_button = template("skilltree_wanda_root.png")

    assert_exists(skilltree_button, "Wanda skill tree root icon/button should be visible.")
    if exists(skilltree_button):
        touch(skilltree_button)
    snapshot(filename=str(ROOT / "output" / "airtest_after_click.png"))


if __name__ == "__main__":
    main()
