# main.py
import argparse
from config_loader import Config
from db import MySQL
from llm_client import LLMClient
from qiniu_uploader import QiniuUploader
from file_repo import FileRepo
from status_repo import StatusRepo
from village_repo import VillageRepo
from category_repo import CategoryRepo
from image_search import ImageSearcher
from pipeline import Pipeline
from runner import Runner


def load_village_ids(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s:
                out.append(int(s))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--retry-failed", action="store_true")
    args = ap.parse_args()

    cfg = Config.load(args.config)
    db = MySQL.from_config(cfg)
    kimi = LLMClient.from_config(cfg)
    uploader = QiniuUploader.from_config(cfg)
    file_repo = FileRepo(db, creator_id=43, creator_user_type=1, creator_name="乡投会员5446")
    status = StatusRepo(db)
    village_repo = VillageRepo(db)
    category_repo = CategoryRepo(db)
    is_cfg = cfg["image_search"] if "image_search" in cfg.raw else {}
    searcher = ImageSearcher(pixabay_key=is_cfg.get("pixabay_key", ""))
    pipe = Pipeline(db, kimi, uploader, file_repo, defaults={},
                    category_repo=category_repo,
                    goods_category_fallback=cfg["run"].get("goods_category_fallback", 0),
                    image_searcher=searcher)
    overwrite = bool(cfg["run"].get("overwrite", False))

    ids = load_village_ids(cfg["run"]["village_ids_file"])
    if args.retry_failed:
        ids = list(status.failed_ids())
    runner = Runner(db, status, pipe, village_repo, overwrite)
    runner.run(ids)
    db.close()


if __name__ == "__main__":
    main()
