from pathlib import Path
import zipfile


ZIP_PATH = Path(r"S:\game\steam\steamapps\common\Don't Starve Together\data\databundles\scripts.zip")
OUT_DIR = Path(__file__).resolve().parent / "scripts"
TARGETS = {
    "scripts/modutil.lua",
    "scripts/mods.lua",
    "scripts/strict.lua",
    "scripts/util.lua",
}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(ZIP_PATH) as archive:
        for name in archive.namelist():
            if name in TARGETS:
                target_path = OUT_DIR / Path(name).name
                target_path.write_bytes(archive.read(name))
                print(f"extracted {name} -> {target_path}")


if __name__ == "__main__":
    main()
