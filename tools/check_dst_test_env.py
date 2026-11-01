"""旧环境检查入口：转发到已配置的统一 doctor，不要求可选图像工具。"""
import json
from pathlib import Path
import subprocess
import sys


if __name__ == '__main__':
    config = Path.home() / '.ai/local/config/dst-mod-development/config.json'
    try:
        settings = json.loads(config.read_text(encoding='utf-8-sig'))
        result = subprocess.run([settings['python'], '-X', 'utf8', '-B',
            str(Path(__file__).with_name('dst_workflow.py')), 'doctor', '--config', str(config), *sys.argv[1:]])
        raise SystemExit(result.returncode)
    except (OSError, KeyError, ValueError) as exc:
        print(json.dumps({'status': 'blocked', 'reason': str(exc)}, ensure_ascii=False))
        raise SystemExit(2)
