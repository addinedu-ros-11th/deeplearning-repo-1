# scripts/02_split_dataset.py
import shutil
import random
from pathlib import Path
from tqdm import tqdm
import yaml

# --- Configuration ---
# Define the split ratios for train, validation, and test sets.
# The sum should be 1.0.
TRAIN_RATIO = 0.8
VAL_RATIO = 0.2
TEST_RATIO = 0.0

if TRAIN_RATIO + VAL_RATIO + TEST_RATIO != 1.0:
    raise ValueError("The sum of TRAIN, VAL, and TEST ratios must be 1.0.")

# --- Paths ---
# Assumes the script is run from the project root 'deeplearning-repo-1'
ROOT_DIR = Path(__file__).resolve().parents[2]
BASE_DATA_DIR = ROOT_DIR / "yw1" / "data"
PROCESSED_DATA_DIR = BASE_DATA_DIR / "processed"
SOURCE_ROOTS = [BASE_DATA_DIR / "from_datacenter", BASE_DATA_DIR / "from_labelling"]
NAMES = [
    "MountainDew",
    "MonsterEnergy",
    "PocariSweat",
    "BananaKick",
    "PocaChip",
    "Ojingeojip",
    "Yukgaejang",
    "Buldak",
    "SesameRamen",
]


def split_dataset():
    """
    Main function to split the dataset into training, validation, and test sets.
    It takes the files from `processed/images` and `processed/labels` and distributes
    them into `train`, `val`, and `test` subdirectories within those folders.
    """
    print("Starting dataset splitting...")
    data_by_class = {name: [] for name in NAMES}  # (image_path, label_path) 튜플 저장

    # --- 1. Get list of all images ---
    for root in SOURCE_ROOTS:
        for name in NAMES:
            if root == SOURCE_ROOTS[1]:
                img_dir = root / name / "images" / "Train"
                lbl_dir = root / name / "labels" / "Train"
            else:
                img_dir = root / name / "images"
                lbl_dir = root / name / "labels"

            if img_dir.exists():
                images = list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.png"))
                # for img_path in images:
                #     # 동일한 이름의 txt 파일 경로 계산
                #     lbl_path = lbl_dir / (img_path.stem + ".txt")
                #     data_by_class[name].append((img_path, lbl_path))

                # --- 수정된 데이터 수집 로직 ---
                for img_path in images:
                    lbl_path = lbl_dir / (img_path.stem + ".txt")

                    # 조건 1: 라벨 파일이 존재하는가?
                    # 조건 2: 파일이 존재한다면 내용이 비어있지 않은가? (파일 크기 체크)
                    if lbl_path.exists():
                        data_by_class[name].append((img_path, lbl_path))
                    else:
                        # 라벨이 없는 이미지는 skip하거나 별도 로그 출력
                        # print(f"Skipping empty image: {img_path.name}")
                        pass

    final_sets = {"train": [], "val": [], "test": []}

    # --- 2. 클래스별로 순회하며 8:1:1 분할 ---
    random.seed(42)
    for name, pairs in data_by_class.items():
        if not pairs:
            print(f"⚠️ 경고: {name} 카테고리에 데이터가 없습니다.")
            continue

        random.shuffle(pairs)  # 클래스 내부에서 셔플

        total = len(pairs)
        train_end = int(total * TRAIN_RATIO)
        val_end = int(total * (TRAIN_RATIO + VAL_RATIO))

        final_sets["train"].extend(pairs[:train_end])
        final_sets["val"].extend(pairs[train_end:val_end])
        final_sets["test"].extend(pairs[val_end:])

        print(
            f"📊 {name.ljust(15)}: 총 {total}개 -> Train:{train_end}, Val:{val_end-train_end}, Test:{total-val_end}"
        )

    # --- 3. 폴더 생성 및 복사 (기존 로직과 동일) ---
    for set_name, data_list in final_sets.items():
        dest_img_dir = PROCESSED_DATA_DIR / "images" / set_name
        dest_lbl_dir = PROCESSED_DATA_DIR / "labels" / set_name

        if dest_img_dir.exists():
            shutil.rmtree(dest_img_dir)
        if dest_lbl_dir.exists():
            shutil.rmtree(dest_lbl_dir)
        dest_img_dir.mkdir(parents=True, exist_ok=True)
        dest_lbl_dir.mkdir(parents=True, exist_ok=True)

        for img_path, lbl_path in tqdm(data_list, desc=f"Copying {set_name}"):
            shutil.copy(img_path, dest_img_dir / img_path.name)
            dest_lbl_path = dest_lbl_dir / lbl_path.name
            if lbl_path.exists():
                shutil.copy(lbl_path, dest_lbl_path)
            else:
                dest_lbl_path.touch()

    print("\n✅ 모든 데이터 분할 및 저장이 완료되었습니다!")
    print(f"위치: {PROCESSED_DATA_DIR}")


def generate_yaml(output_path, processed_dir, class_names):
    """
    YOLOv11 학습을 위한 data.yaml 파일을 생성합니다.
    """
    # 윈도우 환경에서도 경로 인식을 명확히 하기 위해 POSIX 스타일(forward slash)로 변환
    data_config = {
        "path": str(processed_dir.absolute()),  # 데이터셋 최상위 경로
        "train": "images/train",  # path 기준 상대 경로
        "val": "images/val",
        "test": "images/test",
        "names": {
            i: name for i, name in enumerate(class_names)
        },  # {0: 'MountainDew', 1: ...}
    }

    # yaml 파일 저장
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(
            data_config,
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

    print(f"✅ YAML 파일 생성 완료: {output_path}")


# --- 실행 구간 ---


if __name__ == "__main__":
    split_dataset()

    # yaml_save_path = PROCESSED_DATA_DIR / "data.yaml"
    # generate_yaml(yaml_save_path, PROCESSED_DATA_DIR, NAMES)
