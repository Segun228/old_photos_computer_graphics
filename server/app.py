from flask import Flask, render_template, request, send_file, url_for
from werkzeug.utils import secure_filename
from src.utils import add_noise, apply_sepia, apply_scratch_texture
import os
import cv2
import time
import zipfile
from io import BytesIO
import numpy as np

app = Flask(__name__, static_folder='static', static_url_path='/static')

UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'static/results'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename))


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        files = request.files.getlist('file')
        processed_images = []

        noise_level = float(request.form.get('noise', 0)) / 100
        sepia_level = float(request.form.get('sepia', 0)) / 100
        scratch_level = float(request.form.get('scratch', 0)) / 100

        fmt = request.form.get('format', 'jpg')
        quality = int(request.form.get('quality', 90))

        for file in files:
            if not file or file is None:
                continue
            filename = secure_filename(file.filename) #type:ignore
            name, _ = os.path.splitext(filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            image = cv2.imread(filepath)


            if noise_level > 0:
                image = add_noise(image, noise_level)
            if sepia_level > 0:
                image = apply_sepia(image, sepia_level)
            if scratch_level > 0:
                image = apply_scratch_texture(image=image, intensity=scratch_level)


            result_filename = f"{name}_{int(time.time())}.{fmt}"
            result_path = os.path.join(RESULT_FOLDER, result_filename)

            if fmt.lower() == 'jpg':
                cv2.imwrite(result_path, image, [cv2.IMWRITE_JPEG_QUALITY, quality])
            else:
                cv2.imwrite(result_path, image)


            processed_images.append({
                'original': url_for('uploaded_file', filename=filename),
                'result': f"/{result_path}",
                'name': result_filename
            })

        return render_template('result.html', images=processed_images)

    return render_template('index.html')


@app.route('/download/<filename>')
def download(filename):
    path = os.path.join(RESULT_FOLDER, filename)
    return send_file(path, as_attachment=True)


@app.route('/process_images', methods=['POST'])
def process_images():
    files = request.files.getlist('files')
    if not files:
        return "No files uploaded", 400

    noise_level = float(request.form.get('noise', 0)) / 100
    sepia_level = float(request.form.get('sepia', 0)) / 100
    scratch_level = float(request.form.get('scratch', 0)) / 100
    fmt = request.form.get('format', 'jpg')
    quality = int(request.form.get('quality', 90))

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for i, file in enumerate(files):
            file_bytes = np.frombuffer(file.read(), np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

            if noise_level > 0:
                image = add_noise(image, noise_level)
            if sepia_level > 0:
                image = apply_sepia(image, sepia_level)
            if scratch_level > 0:
                image = apply_scratch_texture(image=image, intensity=scratch_level)

            is_success, buffer = cv2.imencode(f".{fmt}", image, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
            if not is_success:
                continue

            zip_file.writestr(f"processed_{i}.{fmt}", buffer.tobytes())

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='processed_images.zip'
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)