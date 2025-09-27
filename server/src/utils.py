import cv2
import numpy as np
import random

def add_noise(image, noise_level=0.1):
    noise = np.random.normal(0, 25 * noise_level, image.shape).astype(np.int16)
    noisy_image = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return noisy_image

def apply_sepia(image, intensity=0.5):
    sepia_filter = np.array([
        [0.272, 0.534, 0.131],
        [0.349, 0.686, 0.168],
        [0.393, 0.769, 0.189]]
    )
    sepia_img = cv2.transform(image, sepia_filter)
    return cv2.addWeighted(image, 1 - intensity, sepia_img, intensity, 0)


def apply_scratch_texture(image, texture_path=None, intensity=0.5):

    h, w = image.shape[:2]

    if texture_path is None:
        texture_path = "/textures/12698.png"
    texture = cv2.imread(texture_path, cv2.IMREAD_GRAYSCALE)
    if texture is None:
        raise FileNotFoundError(f"Текстура не найдена: {texture_path}")

    texture = cv2.resize(texture, (w, h))


    texture = cv2.normalize(texture, None, 0, 255, cv2.NORM_MINMAX)
    texture_colored = cv2.cvtColor(texture, cv2.COLOR_GRAY2BGR)


    alpha = 2.0
    beta = -100
    texture_colored = cv2.convertScaleAbs(texture_colored, alpha=alpha, beta=beta)

    blended = cv2.addWeighted(image, 1.0, texture_colored, intensity, 0)

    return blended