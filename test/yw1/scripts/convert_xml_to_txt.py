import xml.etree.ElementTree as ET
import os
from pathlib import Path

class_map = [
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


def convert_all_xmls(input_dir, output_dir, class_index=0):
    # 1. 출력 폴더가 없으면 생성
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"폴더 생성 완료: {output_dir}")

    # 2. 폴더 내 모든 파일 리스트 가져오기
    files = [f for f in os.listdir(input_dir) if f.endswith(".xml")]

    count = 0
    for filename in files:
        xml_path = os.path.join(input_dir, filename)

        # 출력 파일명 설정 (확장자만 .txt로 변경)
        txt_filename = Path(filename).stem + ".txt"
        output_path = os.path.join(output_dir, txt_filename)

        try:
            # XML 파싱
            tree = ET.parse(xml_path)
            root = tree.getroot()

            size = root.find("size")
            w = int(size.find("width").text)
            h = int(size.find("height").text)

            obb_results = []
            for obj in root.iter("object"):
                xmlbox = obj.find("bndbox")

                xmin = float(xmlbox.find("xmin").text)
                ymin = float(xmlbox.find("ymin").text)
                xmax = float(xmlbox.find("xmax").text)
                ymax = float(xmlbox.find("ymax").text)

                # YOLO OBB 형식: x1 y1 x2 y2 x3 y3 x4 y4 (정규화 포함)
                coords = [
                    xmin / w,
                    ymin / h,  # p1 (좌상)
                    xmax / w,
                    ymin / h,  # p2 (우상)
                    xmax / w,
                    ymax / h,  # p3 (우하)
                    xmin / w,
                    ymax / h,  # p4 (좌하)
                ]

                line = f"{class_index} " + " ".join([f"{c:.6f}" for c in coords])
                obb_results.append(line)

            # TXT 파일 저장
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(obb_results))

            count += 1
        except Exception as e:
            print(f"오류 발생 ({filename}): {e}")

    print("\n--- 변환 완료 ---")
    print(f"총 처리된 파일 수: {count}")


# --- 설정 구간 ---
input_folder = "test/yw1/dataset/drink_label"  # 원본 XML 파일들이 있는 폴더
input_folder_dict = {
    "test/yw1/dataset/drink_label/10032_롯데마운틴듀355ML": 0,
    "test/yw1/dataset/drink_label/10037_동아포카리스웨트500ML": 2,
    "test/yw1/dataset/drink_label/30015_몬스터에너지그린355ML": 1,
    "test/yw1/dataset/rameon_label/10103_오뚜기참깨라면(컵)": 8,
    "test/yw1/dataset/rameon_label/20114_삼양)까르보불닭볶음면큰컵105G": 7,
    "test/yw1/dataset/rameon_label/60119_오뚜기육개장용기면86G": 6,
    "test/yw1/dataset/snack1_label/10092_농심오징어집83G": 5,
    "test/yw1/dataset/snack1_label/10095_농심바나나킥75G": 3,
    "test/yw1/dataset/snack1_label/10210_오리온)포카칩오리지널66G": 4,
}
"""
    test/yw1/dataset/drink_label/10032_롯데마운틴듀355ML
    test/yw1/dataset/drink_label/10037_동아포카리스웨트500ML
    test/yw1/dataset/drink_label/30015_몬스터에너지그린355ML
    test/yw1/dataset/rameon_label/10103_오뚜기참깨라면(컵)
    test/yw1/dataset/rameon_label/20114_삼양)까르보불닭볶음면큰컵105G
    test/yw1/dataset/rameon_label/60119_오뚜기육개장용기면86G
    test/yw1/dataset/snack1_label/10092_농심오징어집83G
    test/yw1/dataset/snack1_label/10095_농심바나나킥75G
    test/yw1/dataset/snack1_label/10210_오리온)포카칩오리지널66G
"""

for input_path, index in input_folder_dict.items():
    name = class_map[index]
    output_folder = f"test/yw1/data/from_datacenter/{name}/labels"
    convert_all_xmls(input_path, output_folder, index)
# 실행
# convert_all_xmls(input_folder, output_folder, target_class_id)
