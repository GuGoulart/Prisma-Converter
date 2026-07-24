import os
import sys

sys.path.insert(0, os.path.abspath("."))

from core.media_tools import mp4_para_gif, _mp4_para_gif_opencv, encontrar_ffmpeg
from core.converter import CONVERSOES, converter_arquivo, _MAPA
from core.security import validar_magic

def main():
    print("=== TEST MP4 TO GIF INTEGRATION ===")
    print("FFmpeg executable:", encontrar_ffmpeg())
    print("CONVERSOES['mp4']:", CONVERSOES.get("mp4"))
    print("('mp4', 'gif') in _MAPA:", ("mp4", "gif") in _MAPA)
    
    # Generate a dummy test mp4 using OpenCV if possible
    import cv2
    import numpy as np

    tmp_dir = "scratch/test_output"
    os.makedirs(tmp_dir, exist_ok=True)
    mp4_path = os.path.join(tmp_dir, "test_input.mp4")
    gif_path = os.path.join(tmp_dir, "test_output.gif")

    # Create a 2-second synthetic video (30 fps, 60 frames)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(mp4_path, fourcc, 30.0, (160, 120))

    for i in range(60):
        # Create a frame with moving circle
        frame = np.zeros((120, 160, 3), dtype=np.uint8)
        x = int(20 + i * 2)
        cv2.circle(frame, (x, 60), 15, (0, 255, 128), -1)
        out.write(frame)
    out.release()

    print(f"Created synthetic MP4: {mp4_path} ({os.path.getsize(mp4_path)} bytes)")

    # Test conversion using mp4_para_gif
    if os.path.exists(gif_path):
        os.remove(gif_path)

    mp4_para_gif(mp4_path, gif_path, fps=10, largura=160)
    
    if os.path.exists(gif_path) and os.path.getsize(gif_path) > 0:
        print(f"SUCCESS: GIF created at {gif_path} ({os.path.getsize(gif_path)} bytes)")
        valid_gif = validar_magic(gif_path, "gif")
        print(f"Magic bytes valid for GIF: {valid_gif}")
    else:
        print("FAIL: GIF creation failed")

    # Test OpenCV fallback directly
    gif_fallback_path = os.path.join(tmp_dir, "test_fallback.gif")
    if os.path.exists(gif_fallback_path):
        os.remove(gif_fallback_path)

    _mp4_para_gif_opencv(mp4_path, gif_fallback_path, fps=10, largura=160)
    if os.path.exists(gif_fallback_path) and os.path.getsize(gif_fallback_path) > 0:
        print(f"SUCCESS: Fallback GIF created at {gif_fallback_path} ({os.path.getsize(gif_fallback_path)} bytes)")
    else:
        print("FAIL: Fallback GIF creation failed")

if __name__ == "__main__":
    main()
