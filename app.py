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
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AR Image Viewer</title>
        <script type="module" src="https://unpkg.com/@google/model-viewer@v1.12.0/dist/model-viewer.min.js"></script>
        <style>
          body {
            font-family: 'Arial', sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            text-align: center;
          }
          h2 {
            color: #333;
            font-size: 1.5rem;
          }
          .input-area {
            margin: 20px 0;
          }
          input[type="file"] {
            margin-right: 10px;
            max-width: 100%;
          }
          button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            margin: 5px;
          }
          button:hover {
            background-color: #45a049;
          }
          #ar-button {
            background-color: #2196F3;
            margin-top: 10px;
            display: none;
            font-weight: bold;
            padding: 12px 20px;
            font-size: 1.1rem;
          }
          #ar-button:hover {
            background-color: #0b7dda;
          }
          model-viewer {
            width: 100%;
            height: 60vh;
            margin-top: 20px;
            background-color: #f5f5f5;
            border-radius: 8px;
          }
          #status {
            margin: 10px 0;
            padding: 10px;
            border-radius: 4px;
            display: none;
          }
          .success {
            background-color: #d4edda;
            color: #155724;
          }
          .error {
            background-color: #f8d7da;
            color: #721c24;
          }
          .info {
            background-color: #e2f3f8;
            color: #0c5460;
          }
          .ar-instructions {
            display: none;
            margin-top: 15px;
            padding: 10px;
            background-color: #fff3cd;
            color: #856404;
            border-radius: 4px;
            text-align: left;
          }
          @media (max-width: 600px) {
            .input-area {
              display: flex;
              flex-direction: column;
              align-items: center;
            }
            input[type="file"] {
              margin-right: 0;
              margin-bottom: 10px;
              width: 100%;
            }
          }
        </style>
      </head>
      <body>
        <h2>Upload your artwork and view it in AR</h2>
        <div class="input-area">
          <input id="file" type="file" accept="image/*" />
          <button id="btn">Make 3D Model</button>
        </div>
        <div id="status"></div>
        <button id="ar-button">View in AR</button>
        <div id="ar-instructions" class="ar-instructions">
          <strong>AR Instructions:</strong>
          <ul>
            <li>iOS devices: The model will open in Quick Look AR.</li>
            <li>Android devices: The model will open in Scene Viewer AR.</li>
            <li>You'll need to allow camera permissions for AR to work.</li>
            <li>Position your device toward a wall to place the artwork.</li>
          </ul>
        </div>
        <model-viewer id="viewer"
          ar
          ar-modes="webxr scene-viewer quick-look"
          ar-placement="wall"
          ar-scale="fixed"
          camera-controls
          autoplay
          shadow-intensity="1"
          touch-action="pan-y"
          reveal="interaction"
          loading="eager"
          ar-status="not-presenting"
          alt="A 3D model of your artwork">
          <button slot="ar-button" id="built-in-ar-button" style="display:none;">View in AR</button>
          <div slot="poster" style="background-color: #f5f5f5; width: 100%; height: 100%; display: flex; justify-content: center; align-items: center;">
            <p>Upload an image to view in 3D and AR</p>
          </div>
          <div slot="progress-bar" style="height: 4px; background: #ddd; position: relative;">
            <div id="progress" style="height: 100%; background: #4CAF50; width: 0%;"></div>
          </div>
        </model-viewer>

        <script>
          const viewer = document.getElementById("viewer");
          const arButton = document.getElementById("ar-button");
          const status = document.getElementById("status");
          const arInstructions = document.getElementById("ar-instructions");
          const builtInArButton = document.getElementById("built-in-ar-button");
          
          // Check if AR is supported
          const isARSupported = () => {
            const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
            const isAndroid = /Android/.test(navigator.userAgent);
            const isChrome = /Chrome/.test(navigator.userAgent) && /Google Inc/.test(navigator.vendor);
            
            // Check for WebXR support (needed for Chrome AR)
            const hasWebXR = 'xr' in navigator && 'isSessionSupported' in navigator.xr;
            
            if (isIOS) {
              // iOS requires version 12+ for AR Quick Look
              const versionMatch = navigator.userAgent.match(/OS ([0-9]+)_([0-9]+)_?([0-9]+)?/);
              if (versionMatch) {
                const version = parseInt(versionMatch[1], 10);
                return version >= 12;
              }
            }
            
            // Chrome on Android needs WebXR or Scene Viewer
            if (isAndroid && isChrome) {
              // Chrome 79+ on Android 8.0+ should support AR
              const match = navigator.userAgent.match(/Chrome\/([0-9]+)/);
              if (match) {
                const version = parseInt(match[1], 10);
                return version >= 79 || hasWebXR;
              }
            }
            
            // General Android support check
            return isAndroid;
          };
          
          // Show status message
          const showStatus = (message, type) => {
            status.textContent = message;
            status.className = type;
            status.style.display = "block";
            setTimeout(() => {
              status.style.display = "none";
            }, 5000);
          };
          
          document.getElementById("btn").onclick = async () => {
            const f = document.getElementById("file").files[0];
            if (!f) {
              showStatus("Please select an image first!", "error");
              return;
            }
            
            // Show loading state
            const btn = document.getElementById("btn");
            const originalText = btn.textContent;
            btn.textContent = "Processing...";
            btn.disabled = true;
            showStatus("Converting image to 3D model...", "info");
            
            const fd = new FormData();
            fd.append("file", f);
            
            try {
              const res = await fetch("/make-glb", { method:"POST", body:fd });
              if (!res.ok) {
                throw new Error("Server error: " + res.status);
              }
              
              const blob = await res.blob();
              const url = URL.createObjectURL(blob);
              viewer.src = url;
              
              // Show AR button once model is loaded
              viewer.addEventListener('load', function() {
                showStatus("3D model created successfully!", "success");
                arButton.style.display = "inline-block";
                arInstructions.style.display = "block";
                
                // Check for AR support
                if (!isARSupported()) {
                  showStatus("Warning: Your device may not support AR features", "error");
                }
              }, { once: true });
              
              viewer.addEventListener('error', function(error) {
                showStatus("Error loading 3D model: " + error, "error");
              });
              
            } catch (error) {
              showStatus(error.message, "error");
            } finally {
              // Reset button state
              btn.textContent = originalText;
              btn.disabled = false;
            }
          };
          
          // Handle AR button click
          arButton.addEventListener('click', () => {
            if (viewer.src) {
              showStatus("Launching AR viewer...", "info");
              try {
                // Check if we're on HTTPS (required for AR on many devices)
                if (location.protocol !== 'https:' && !location.hostname.includes('localhost') && !location.hostname.includes('127.0.0.1')) {
                  showStatus("Warning: AR may require HTTPS to work properly on some devices", "error");
                }
                
                // Check browser type
                const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
                const isAndroid = /Android/.test(navigator.userAgent);
                const isChrome = /Chrome/.test(navigator.userAgent) && /Google Inc/.test(navigator.vendor);
                const hasWebXR = 'xr' in navigator && 'isSessionSupported' in navigator.xr;
                
                // Hide the built-in AR button first to prevent conflicts
                if (builtInArButton) {
                  builtInArButton.style.display = "none";
                }
                
                // Special handling for Chrome on Android
                if (isAndroid && isChrome) {
                  if (hasWebXR) {
                    showStatus("Launching WebXR AR experience...", "info");
                    // WebXR Mode (newer Chrome versions)
                    
                    // Make sure model-viewer has fully loaded
                    if (viewer.canActivateAR) {
                      // WebXR should be first in ar-modes to prioritize it
                      viewer.setAttribute('ar-modes', 'webxr scene-viewer quick-look');
                      
                      setTimeout(() => {
                        viewer.activateAR();
                      }, 500);
                    } else {
                      showStatus("WebXR not available, trying Scene Viewer...", "info");
                      // Fallback to Scene Viewer
                      launchSceneViewer();
                    }
                  } else {
                    // Scene Viewer mode (for older Chrome versions)
                    showStatus("Launching Scene Viewer AR experience...", "info");
                    launchSceneViewer();
                  }
                } else if (isIOS) {
                  // iOS Quick Look
                  showStatus("Launching Quick Look AR experience...", "info");
                  setTimeout(() => {
                    viewer.activateAR();
                  }, 300);
                } else {
                  // General fallback
                  if (viewer.canActivateAR) {
                    setTimeout(() => {
                      viewer.activateAR();
                    }, 300);
                  } else {
                    showStatus("AR mode not available on this device/browser", "error");
                  }
                }
                
                // Function to launch Scene Viewer as a fallback
                function launchSceneViewer() {
                  // Prioritize scene-viewer for Android
                  viewer.setAttribute('ar-modes', 'scene-viewer webxr quick-look');
                  
                  setTimeout(() => {
                    try {
                      viewer.activateAR();
                    } catch (err) {
                      showStatus("Error launching Scene Viewer: " + err.message, "error");
                    }
                  }, 300);
                }
                
              } catch (error) {
                console.error("AR activation error:", error);
                showStatus("Error launching AR: " + error.message, "error");
              }
            } else {
              showStatus("Please create a 3D model first!", "error");
            }
          });
          
          // Add debug info for AR support
          const debugInfo = document.createElement('div');
          debugInfo.style.fontSize = '12px';
          debugInfo.style.color = '#666';
          debugInfo.style.margin = '20px 0';
          debugInfo.style.textAlign = 'left';
          
          // Detect browser and AR capabilities
          const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
          const isAndroid = /Android/.test(navigator.userAgent);
          const isChrome = /Chrome/.test(navigator.userAgent) && /Google Inc/.test(navigator.vendor);
          const hasWebXR = 'xr' in navigator && 'isSessionSupported' in navigator.xr;
          
          // Check Chrome version
          let chromeVersion = 'N/A';
          if (isChrome) {
            const match = navigator.userAgent.match(/Chrome\/([0-9]+)/);
            if (match) {
              chromeVersion = match[1];
            }
          }
          
          // Check Android version
          let androidVersion = 'N/A';
          if (isAndroid) {
            const match = navigator.userAgent.match(/Android ([0-9]+)\.([0-9]+)/);
            if (match) {
              androidVersion = `${match[1]}.${match[2]}`;
            }
          }
          
          debugInfo.innerHTML = `
            <details>
              <summary>Debug Information</summary>
              <p>User Agent: ${navigator.userAgent}</p>
              <p>Browser: ${isChrome ? 'Chrome ' + chromeVersion : isIOS ? 'Safari' : 'Other'}</p>
              <p>Platform: ${isAndroid ? 'Android ' + androidVersion : isIOS ? 'iOS' : 'Other'}</p>
              <p>WebXR Support: ${hasWebXR ? 'Yes' : 'No'}</p>
              <p>Protocol: ${location.protocol}</p>
              <p>Can Activate AR: ${viewer.canActivateAR ? 'Yes' : 'No'}</p>
              <p>AR Mode Priority: ${viewer.getAttribute('ar-modes')}</p>
              <p>Screen: ${window.innerWidth} x ${window.innerHeight}</p>
              <p>Secure Context: ${window.isSecureContext ? 'Yes' : 'No'}</p>
            </details>
          `;
          document.body.appendChild(debugInfo);
        </script>
      </body>
    </html>
    """
    return Response(html, mimetype="text/html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7861, debug=True)
