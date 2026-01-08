# scripts/01_preprocess_data.py
import xml.etree.ElementTree as ET
from pathlib import Path
import shutil
from tqdm import tqdm
import cv2

# --- Configuration ---
# IMPORTANT: Update this mapping to match your dataset's classes.
CLASS_MAPPING = {
    "person": 0,
    "shopping_cart": 1,
    # "product_a": 2,
    # "product_b": 3,
}

# --- Paths ---
# Assumes the script is run from the project root 'deeplearning-repo-1'
ROOT_DIR = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = ROOT_DIR / "test" / "yw1" / "data" / "raw"
PROCESSED_DATA_DIR = ROOT_DIR / "test" / "yw1" / "data" / "processed"

# Directories for processed output
IMAGES_DIR = PROCESSED_DATA_DIR / "images"
LABELS_DIR = PROCESSED_DATA_DIR / "labels"


def convert_rbox_to_yolo_obb(image_width, image_height, rbox_points, class_id):
    """
    Converts rotated bounding box points to normalized YOLO OBB format.
    YOLO OBB format: <class_id> <x1> <y1> <x2> <y2> <x3> <y3> <x4> <y4> (normalized)

    Args:
        image_width (int): Width of the image.
        image_height (int): Height of the image.
        rbox_points (list): A list of 4 (x, y) tuples.
        class_id (int): The class index for the object.

    Returns:
        str: A string in YOLO OBB format.
    """
    normalized_points = []
    for x, y in rbox_points:
        normalized_x = x / image_width
        normalized_y = y / image_height
        normalized_points.extend([normalized_x, normalized_y])

    return f"{class_id} " + " ".join(map(str, normalized_points))


def parse_cvat_xml(xml_file, image_path):
    """
    Parses a CVAT XML file for rotated bounding boxes (rbox) and converts them to YOLO OBB format.

    Args:
        xml_file (Path): Path to the CVAT XML annotation file.
        image_path (Path): Path to the corresponding image file.

    Returns:
        tuple: A tuple containing (image_width, image_height, list_of_yolo_obb_strings).
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()

    yolo_obb_lines = []

    # Get image dimensions from the XML or by reading the image
    image_width = int(root.find("image").get("width"))
    image_height = int(root.find("image").get("height"))

    if not (image_width and image_height):
        # Fallback to reading image if dimensions are not in XML
        img = cv2.imread(str(image_path))
        if img is not None:
            image_height, image_width, _ = img.shape
        else:
            print("Image is not loaded")
            return 0, 0, 0

    for image_tag in root.findall("image"):
        for box in image_tag.findall("polygon"):
            if box.get("rbox"):  # Check if it's a rotated box
                label = box.get("label")
                if label not in CLASS_MAPPING:
                    print(
                        f"Warning: Skipping unknown class '{label}' in {xml_file.name}"
                    )
                    continue

                class_id = CLASS_MAPPING[label]

                # Points are stored as 'x1,y1;x2,y2;x3,y3;x4,y4'
                points_str = box.get("points").split(";")
                rbox_points = [tuple(map(float, p.split(","))) for p in points_str]

                # Ensure there are 4 points
                if len(rbox_points) == 4:
                    yolo_obb_line = convert_rbox_to_yolo_obb(
                        image_width, image_height, rbox_points, class_id
                    )
                    yolo_obb_lines.append(yolo_obb_line)

    return image_width, image_height, yolo_obb_lines


def process_raw_data():
    """
    Main function to process all raw data from CVAT format to YOLO OBB format.
    - It expects CVAT for image format, which exports annotations in a 'annotations.xml' file
      and images in an 'images' subdirectory.
    - This script assumes a structure like:
      - raw/
        - annotations.xml
        - images/
          - image1.jpg
          - image2.png
          ...
    """
    print("Starting data preprocessing...")

    # Clean and create directories
    if PROCESSED_DATA_DIR.exists():
        shutil.rmtree(PROCESSED_DATA_DIR)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    LABELS_DIR.mkdir(parents=True, exist_ok=True)

    annotations_xml = RAW_DATA_DIR / "annotations.xml"
    raw_images_dir = RAW_DATA_DIR / "images"

    if not annotations_xml.exists() or not raw_images_dir.exists():
        print(
            f"Error: Ensure 'annotations.xml' and an 'images' folder exist in '{RAW_DATA_DIR}'"
        )
        # Create placeholder files and folders for the user
        RAW_DATA_DIR.mkdir(exist_ok=True)
        raw_images_dir.mkdir(exist_ok=True)
        annotations_xml.touch()
        print("Created placeholder 'annotations.xml' and 'images/' directory.")
        print("Please populate them with your CVAT export data and run again.")
        return

    tree = ET.parse(annotations_xml)
    root = tree.getroot()

    print(f"Found {len(root.findall('image'))} images in {annotations_xml.name}")

    for image_tag in tqdm(root.findall("image"), desc="Processing images"):
        image_name = image_tag.get("name")

        # Find the source image file
        source_image_path = raw_images_dir / image_name
        if not source_image_path.exists():
            print(
                f"Warning: Image '{image_name}' not found in '{raw_images_dir}'. Skipping."
            )
            continue

        # Copy image to processed directory
        dest_image_path = IMAGES_DIR / source_image_path.name
        shutil.copy(source_image_path, dest_image_path)

        # --- Create Label File ---
        image_width = int(image_tag.get("width"))
        image_height = int(image_tag.get("height"))

        yolo_obb_lines = []
        # Find polygons associated with this image
        for poly in image_tag.findall("polygon"):
            if poly.get("rbox"):  # Oriented Bounding Box
                label = poly.get("label")
                if label not in CLASS_MAPPING:
                    print(
                        f"Warning: Skipping unknown class '{label}' for image '{image_name}'"
                    )
                    continue

                class_id = CLASS_MAPPING[label]
                points_str = poly.get("points").split(";")
                rbox_points = [tuple(map(float, p.split(","))) for p in points_str]

                if len(rbox_points) == 4:
                    yolo_line = convert_rbox_to_yolo_obb(
                        image_width, image_height, rbox_points, class_id
                    )
                    yolo_obb_lines.append(yolo_line)

        # Write the label file
        if yolo_obb_lines:
            label_filename = dest_image_path.stem + ".txt"
            label_path = LABELS_DIR / label_filename
            with open(label_path, "w") as f:
                f.write("\n".join(yolo_obb_lines))

    print("-" * 30)
    print("Preprocessing complete.")
    print(f"Images saved to: {IMAGES_DIR}")
    print(f"Labels saved to: {LABELS_DIR}")
    print("-" * 30)


if __name__ == "__main__":
    process_raw_data()
