import cv2
from ultralytics import YOLO

def verify_model(model_path, video_source):
    # 모델 로드
    model = YOLO(model_path)
    
    # 영상 소스 열기
    cap = cv2.VideoCapture(video_source)
    if not cap.isOpened():
        print(f"❌ 영상을 열 수 없습니다: {video_source}")
        return

    print(f"🚀 검증 시작: {video_source}")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # 모델 추론 (Inference)
        results = model.predict(frame, conf=0.35, verbose=False)

        # 결과 시각화 (Annotate)
        annotated_frame = results[0].plot()

        # 화면 표시
        cv2.imshow("Model Verification", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # 내부 테스트용 경로 설정 (필요시 수정)
    MODEL_PATH = "test/changhee/cart_person_integrated.pt"
    VIDEO_PATH = "/home/changpc/Videos/Camera/Recording from 2025-12-30 15-10-16.695632.webm"
    verify_model(MODEL_PATH, VIDEO_PATH)
