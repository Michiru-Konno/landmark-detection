// DOM要素の取得
const video = document.getElementById("video");
const canvas = document.getElementById("overlay");
const ctx = canvas.getContext("2d");
const result = document.getElementById("result");

// カメラの起動設定
navigator.mediaDevices
    .getUserMedia({ video: { width: 1280, height: 720 } })
    .then((stream) => {
        video.srcObject = stream;
        video.addEventListener("loadeddata", () => {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
        });
    })
    .catch((err) => displayError("カメラの起動に失敗しました"));

// サーバーにビデオフレームを送信
async function sendFrame() {
    // フレームキャプチャ用の仮想Canvas作成
    const captureCanvas = document.createElement("canvas");
    captureCanvas.width = video.videoWidth;
    captureCanvas.height = video.videoHeight;
    const captureCtx = captureCanvas.getContext("2d");
    captureCtx.drawImage(video, 0, 0, captureCanvas.width, captureCanvas.height);

    // キャプチャした画像データをBase64形式に変換
    const imageData = captureCanvas.toDataURL("image/jpeg");

    try {
        // サーバーに画像データを送信
        const response = await fetch("/process_frame", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ image: imageData }),
        });

        const data = await response.json(); // サーバーからのレスポンスをパース
        console.log("サーバーレスポンス:", data); // デバッグ用ログ

        if (data.image) {
            drawServerImage(data.image); // サーバーからの画像を描画
        }

        displayResult(data); // 結果を表示
    } catch (err) {
        console.error("サーバーエラー:", err);
        displayError("サーバーエラーが発生しました");
    }
}

// サーバーから返却された画像を描画
function drawServerImage(base64Image) {
    const img = new Image();
    img.onload = () => {
        ctx.clearRect(0, 0, canvas.width, canvas.height); // 既存の描画をクリア
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height); // 新しい画像を描画
    };
    img.src = base64Image;
}

// サーバーから返却されたデータを表示
function displayResult(data) {
    const { focused, reason } = data;

    // 結果をテキストと色で表示
    result.textContent = focused ? "集中しています" : `非集中: ${reason}`;
    result.style.color = focused ? "green" : "red";

    // 結果をキャンバスに描画
    ctx.clearRect(0, 0, canvas.width, 50); // 上部にある以前の結果をクリア
    ctx.font = "20px Arial";
    ctx.fillStyle = focused ? "green" : "red";
    ctx.fillText(result.textContent, 20, 40);
}

// エラー表示
function displayError(message) {
    result.textContent = message;
    result.style.color = "red";
    ctx.clearRect(0, 0, canvas.width, canvas.height); // キャンバスをクリア
    ctx.font = "20px Arial";
    ctx.fillStyle = "red";
    ctx.fillText(message, 20, 40);
}

