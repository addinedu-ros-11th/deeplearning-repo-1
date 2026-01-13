# scripts/01_filter_v1_train_only.py
from pathlib import Path
import shutil


IMAGE_EXTS = {".jpg", ".jpeg", ".png"}


def filter_train_v1(
    src_images: Path,
    src_labels: Path,
    dst_images: Path,
    dst_labels: Path,
) -> None:
    dst_images.mkdir(parents=True, exist_ok=True)
    dst_labels.mkdir(parents=True, exist_ok=True)

    images = [
        p for p in src_images.iterdir()
        if p.suffix.lower() in IMAGE_EXTS and p.stem.endswith("_v1")
    ]

    if not images:
        raise RuntimeError(f"No _v1 images found in {src_images}")

    copied, skipped = 0, 0

    for img in images:
        label = src_labels / f"{img.stem}.txt"
        if not label.exists():
            skipped += 1
            continue

        shutil.copy2(img, dst_images / img.name)
        shutil.copy2(label, dst_labels / label.name)
        copied += 1

    print(f"[OK] train: copied={copied}, skipped(no label)={skipped}")


def main() -> None:
    root = Path(__file__).resolve().parents[2]

    src_root = root / "yw1" / "data" / "yolo_oversampling"
    dst_root = root / "yw1" / "data" / "yolo_oversampling_v1"

    filter_train_v1(
        src_images=src_root / "train" / "images",
        src_labels=src_root / "train" / "labels",
        dst_images=dst_root / "train" / "images",
        dst_labels=dst_root / "train" / "labels",
    )

    print("\nTrain v1 dataset prepared.")
    print(f"Output: {dst_root / 'train'}")


if __name__ == "__main__":
    main()
