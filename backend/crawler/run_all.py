from crawler.hana import main as hana_main
from crawler.shjoongang import main as shjoongang_main
from crawler.suhyup import main as suhyup_main
from crawler.woori import main as woori_main
from crawler.kb import main as kb_main
from crawler.kb import wait_for_download_complete


def run_all_crawlers():
    for script_name, fn in [
        ("hana", hana_main),
        ("shjoongang", shjoongang_main),
        ("suhyup", suhyup_main),
        ("woori", woori_main),
        ("kb", kb_main),
    ]:
        try:
            print(f"\u25b6 실행 중: {script_name}")
            fn()
        except Exception as e:
            print(f"\u274c 실패: {script_name} \u2192 {e}")

if __name__ == "__main__":
    run_all_crawlers()
