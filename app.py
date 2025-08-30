import io
import numpy as np
from PIL import Image
import trimesh
from flask import Flask, request, send_file, abort, Response, redirect, url_for
from flask_cors import CORS

# ---- Flask App ----
app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    # Redirect root to /viewer
    return redirect(url_for("viewer"))

def create_glb_from_image(file_like, width_m=0.5, thickness_m=0.01):
    img = Image.open(file_like).convert("RGBA")
    w_px, h_px = img.size
    aspect = h_px / float(w_px)

    W = float(width_m)
    H = W * aspect
    T = float(thickness_m)

    box = trimesh.creation.box(extents=(W, H, T))
    box.apply_translation((0, 0, T/2.0))

    uv = np.zeros((len(box.vertices), 2), dtype=np.float32)
    verts = box.vertices
    min_xy = verts[:, :2].min(axis=0)
    max_xy = verts[:, :2].max(axis=0)
    span_xy = np.maximum(max_xy - min_xy, 1e-8)
    uv[:] = (verts[:, :2] - min_xy) / span_xy

    texture = trimesh.visual.texture.TextureVisuals(uv=uv, image=img)
    box.visual = texture

    glb_bytes = box.export(file_type="glb")
    return glb_bytes if isinstance(glb_bytes, bytes) else glb_bytes.read()

@app.route("/make-glb", methods=["POST"])
def make_glb():
    if 'file' not in request.files:
        abort(400, "Upload an image under 'file'.")
    f = request.files['file']
    glb_bytes = create_glb_from_image(f.stream)
    return send_file(
        io.BytesIO(glb_bytes),
        mimetype="model/gltf-binary",
        as_attachment=True,
        download_name="photo_frame.glb"
    )

@app.route("/viewer")
def viewer():
    html = """
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <title>AR Image Viewer</title>
        <script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
      </head>
      <body>
        <h2>Upload an image → place it in AR</h2>
        <input id="file" type="file" accept="image/*" />
        <button id="btn">Make GLB</button>
        <br><br>
        <model-viewer id="viewer"
          ar
          ar-modes="scene-viewer webxr quick-look"
          ar-placement="wall"
          ar-scale="fixed"
          camera-controls
          autoplay
          style="width: 100%; height: 80vh;">
        </model-viewer>

        <script>
          document.getElementById("btn").onclick = async () => {
            const f = document.getElementById("file").files[0];
            if (!f) return alert("Pick an image first!");
            const fd = new FormData();
            fd.append("file", f);
            const res = await fetch("/make-glb", { method:"POST", body:fd });
            if (!res.ok) {
              alert("Server error: " + res.status);
              return;
            }
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            document.getElementById("viewer").src = url;
          }
        </script>
      </body>
    </html>
    """
    return Response(html, mimetype="text/html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860, debug=True)