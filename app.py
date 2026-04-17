from flask import Flask, request, jsonify, send_file
import cv2
import numpy as np
import base64
import io

app = Flask(__name__)


def cartoonify_image(image_bytes):
    file_bytes = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    if img is None:
        return None

    original_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    gray_scale_image = cv2.cvtColor(original_image, cv2.COLOR_RGB2GRAY)
    smooth_gray_scale = cv2.medianBlur(gray_scale_image, 5)

    get_edge = cv2.adaptiveThreshold(
        smooth_gray_scale,
        255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        9,
        9
    )

    color_image = cv2.bilateralFilter(original_image, 9, 300, 300)
    cartoon_image = cv2.bitwise_and(color_image, color_image, mask=get_edge)

    cartoon_bgr = cv2.cvtColor(cartoon_image, cv2.COLOR_RGB2BGR)
    success, buffer = cv2.imencode(".png", cartoon_bgr)

    if not success:
        return None

    return buffer.tobytes()


@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Cartoonify Image</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f5f5f5;
                padding: 30px;
                margin: 0;
            }
            .container {
                max-width: 800px;
                margin: auto;
                background: white;
                padding: 30px;
                border-radius: 16px;
                box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            }
            h1 {
                margin-top: 0;
            }
            input, button {
                width: 100%;
                padding: 12px;
                margin-top: 12px;
                font-size: 16px;
                border-radius: 8px;
                box-sizing: border-box;
            }
            input {
                border: 1px solid #ccc;
            }
            button {
                background: black;
                color: white;
                border: none;
                cursor: pointer;
            }
            button:hover {
                opacity: 0.92;
            }
            img {
                max-width: 100%;
                margin-top: 20px;
                border-radius: 12px;
                border: 1px solid #ddd;
            }
            .hidden {
                display: none;
            }
            .message {
                margin-top: 16px;
                font-size: 16px;
            }
            a.download-btn {
                display: inline-block;
                margin-top: 16px;
                padding: 12px 18px;
                background: black;
                color: white;
                text-decoration: none;
                border-radius: 8px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎨 Cartoonify Your Image</h1>
            <p>Upload an image and turn it into a cartoon-style version.</p>

            <input type="file" id="imageInput" accept="image/*">
            <button onclick="uploadImage()">Cartoonify Image</button>

            <div class="message" id="message"></div>

            <img id="resultImage" class="hidden" alt="Cartoonified image">
            <br>
            <a id="downloadLink" class="download-btn hidden" download="cartoonified_image.png">Download Cartoon Image</a>
        </div>

        <script>
            async function uploadImage() {
                const input = document.getElementById("imageInput");
                const message = document.getElementById("message");
                const resultImage = document.getElementById("resultImage");
                const downloadLink = document.getElementById("downloadLink");

                if (!input.files.length) {
                    message.innerText = "Please choose an image first.";
                    return;
                }

                message.innerText = "Processing image...";
                resultImage.classList.add("hidden");
                downloadLink.classList.add("hidden");

                const formData = new FormData();
                formData.append("image", input.files[0]);

                try {
                    const response = await fetch("/cartoonify", {
                        method: "POST",
                        body: formData
                    });

                    const data = await response.json();

                    if (data.error) {
                        message.innerText = data.error;
                        return;
                    }

                    resultImage.src = data.image;
                    resultImage.classList.remove("hidden");

                    downloadLink.href = data.image;
                    downloadLink.classList.remove("hidden");

                    message.innerText = "Done! Your image has been cartoonified.";
                } catch (error) {
                    message.innerText = "Something went wrong while processing the image.";
                }
            }
        </script>
    </body>
    </html>
    """


@app.route("/cartoonify", methods=["POST"])
def cartoonify():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded."}), 400

    image_file = request.files["image"]
    image_bytes = image_file.read()

    cartoon_bytes = cartoonify_image(image_bytes)

    if cartoon_bytes is None:
        return jsonify({"error": "Invalid image or processing failed."}), 400

    encoded_image = base64.b64encode(cartoon_bytes).decode("utf-8")
    image_data_url = f"data:image/png;base64,{encoded_image}"

    return jsonify({"image": image_data_url})


if __name__ == "__main__":
    app.run(debug=True)