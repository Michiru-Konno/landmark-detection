import numpy as np
import cv2
import dlib
from flask import Flask, request, jsonify, render_template
import os
import base64

# Flaskアプリケーションの初期化
app = Flask(__name__)

# モデルのロード
MODEL_PATH = "shape_predictor_68_face_landmarks.dat"  # ローカルにモデルを配置
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(MODEL_PATH)

# 定数
FACE_ORIENTATION_THRESHOLD = 0.2
EYE_ASPECT_RATIO_THRESHOLD = 0.2
CLOSED_EYE_FRAME_THRESHOLD = 15

# グローバル変数
closed_eye_frames = 0
BASELINE_LANDMARKS = None

# EAR (Eye Aspect Ratio) 計算
def eye_aspect_ratio(eye):
    vertical_1 = np.linalg.norm(eye[1] - eye[5])
    vertical_2 = np.linalg.norm(eye[2] - eye[4])
    horizontal = np.linalg.norm(eye[0] - eye[3])
    return (vertical_1 + vertical_2) / (2.0 * horizontal)

# 目のランドマーク取得
def get_eye_coordinates(landmarks):
    left_eye = np.array([[landmarks.part(i).x, landmarks.part(i).y] for i in range(36, 42)])
    right_eye = np.array([[landmarks.part(i).x, landmarks.part(i).y] for i in range(42, 48)])
    return left_eye, right_eye

# 顔の向き計算
def calculate_face_orientation(landmarks, baseline):
    left_eye = np.mean([[landmarks.part(i).x, landmarks.part(i).y] for i in range(36, 42)], axis=0)
    right_eye = np.mean([[landmarks.part(i).x, landmarks.part(i).y] for i in range(42, 48)], axis=0)
    nose_tip = np.array([landmarks.part(30).x, landmarks.part(30).y])
    base_left_eye, base_right_eye, base_nose_tip = baseline

    horizontal_ratio = abs(left_eye[0] - nose_tip[0]) / abs(base_left_eye[0] - base_nose_tip[0])
    vertical_ratio = abs(right_eye[0] - nose_tip[0]) / abs(base_right_eye[0] - base_nose_tip[0])

    return horizontal_ratio, vertical_ratio

# 基準ランドマークのキャプチャ
def capture_baseline_landmarks(landmarks):
    left_eye = np.mean([[landmarks.part(i).x, landmarks.part(i).y] for i in range(36, 42)], axis=0)
    right_eye = np.mean([[landmarks.part(i).x, landmarks.part(i).y] for i in range(42, 48)], axis=0)
    nose_tip = np.array([landmarks.part(30).x, landmarks.part(30).y])
    return left_eye, right_eye, nose_tip

# 集中度の評価
def evaluate_focus(landmarks):
    global BASELINE_LANDMARKS, closed_eye_frames

    if BASELINE_LANDMARKS is None:
        BASELINE_LANDMARKS = capture_baseline_landmarks(landmarks)
        return True, "基準を設定しました"

    horizontal_ratio, vertical_ratio = calculate_face_orientation(landmarks, BASELINE_LANDMARKS)
    if horizontal_ratio > (1 + FACE_ORIENTATION_THRESHOLD) or vertical_ratio > (1 + FACE_ORIENTATION_THRESHOLD):
        return False, "顔が画面外を向いています"

    left_eye, right_eye = get_eye_coordinates(landmarks)
    avg_ear = (eye_aspect_ratio(left_eye) + eye_aspect_ratio(right_eye)) / 2.0

    if avg_ear < EYE_ASPECT_RATIO_THRESHOLD:
        closed_eye_frames += 1
        if closed_eye_frames >= CLOSED_EYE_FRAME_THRESHOLD:
            return False, "目を長時間閉じています"
    else:
        closed_eye_frames = 0

    return True, "集中しています"

# 画像データ処理
def process_image(image_data):
    try:
        nparr = np.frombuffer(base64.b64decode(image_data.split(",")[1]), np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = detector(gray)
        if len(faces) == 0:
            return {"focused": False, "reason": "顔が検出されません"}

        for face in faces:
            landmarks = predictor(gray, face)
            is_focused, reason = evaluate_focus(landmarks)

            return {
                "focused": is_focused,
                "reason": reason
            }
    except Exception as e:
        return {"focused": False, "reason": f"エラー: {str(e)}"}

# Flaskエンドポイント
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process_frame", methods=["POST"])
def process_frame():
    if not request.json or "image" not in request.json:
        return jsonify({"focused": False, "reason": "Invalid request"}), 400
    image_data = request.json["image"]
    result = process_image(image_data)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
