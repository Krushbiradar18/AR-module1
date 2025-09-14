import io
import numpy as np
from PIL import Image
import trimesh
from flask import Flask, request, send_file, abort, Response, redirect, url_for
from flask_cors import CORS

# ---- Flask App ----
app = Flask(__name__)
# Allow CORS from any origin with any headers - Chrome-friendly configuration
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Access-Control-Allow-Credentials", "Cache-Control"]
    }
})

# Add security headers for AR support
@app.after_request
def add_header(response):
    # Chrome-specific CORS headers
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Accept, Authorization, X-Requested-With, Origin'
    response.headers['Access-Control-Max-Age'] = '86400'  # 24 hours
    response.headers['Access-Control-Allow-Credentials'] = 'false'
    # Remove headers that can cause issues in Chrome
    response.headers.pop('Cross-Origin-Opener-Policy', None)
    response.headers.pop('Cross-Origin-Embedder-Policy', None)
    response.headers.pop('Cross-Origin-Resource-Policy', None)
    return response

@app.route("/")
def home():
    # Redirect root to /viewer
    return redirect(url_for("viewer"))

@app.route("/health", methods=["GET", "OPTIONS"])
def health_check():
    # Simple health check endpoint for testing connectivity
    if request.method == "OPTIONS":
        response = Response(status=200)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Accept'
        return response
    
    return Response("OK", status=200, mimetype='text/plain')

def create_glb_from_image(file_like, width_m=0.5, thickness_m=0.01):
    try:
        img = Image.open(file_like).convert("RGBA")
        w_px, h_px = img.size
        
        # Validate image dimensions
        if w_px == 0 or h_px == 0:
            raise ValueError("Invalid image dimensions")
        
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
        
    except Exception as e:
        print(f"Error in create_glb_from_image: {str(e)}")
        return None

@app.route("/make-glb", methods=["POST", "OPTIONS"])
def make_glb():
    # Handle CORS preflight requests - Chrome-specific
    if request.method == "OPTIONS":
        response = Response(status=200)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Accept, Authorization, X-Requested-With, Origin'
        response.headers['Access-Control-Max-Age'] = '86400'
        response.headers['Access-Control-Allow-Credentials'] = 'false'
        response.headers['Content-Length'] = '0'
        return response
    
    try:
        # Validate request
        if 'image' not in request.files:
            print("Debug: No 'image' in request.files")
            print("Debug: Available keys:", list(request.files.keys()))
            return Response("No file uploaded. Please select an image file.", status=400)
        
        f = request.files['image']
        
        # Check if file is selected
        if f.filename == '':
            return Response("No file selected. Please choose an image.", status=400)
        
        # Basic file type validation
        if not f.content_type or not f.content_type.startswith('image/'):
            return Response("Invalid file type. Please upload an image file (JPG, PNG, etc.).", status=400)
        
        # Process the image
        glb_bytes = create_glb_from_image(f.stream)
        
        if not glb_bytes:
            return Response("Failed to process image. Please try a different image.", status=500)
        
        response = send_file(
            io.BytesIO(glb_bytes),
            mimetype="model/gltf-binary",
            as_attachment=False,  # Changed to False for better browser handling
            download_name="photo_frame.glb"
        )
        
        # Set proper headers for GLB files
        response.headers['Content-Disposition'] = 'inline; filename="photo_frame.glb"'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
        
    except Exception as e:
        print(f"Error in make_glb: {str(e)}")  # Server-side logging
        return Response(f"Server error while processing image: {str(e)}", status=500)

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
        <!-- AR Viewer - Simple version -->
        <model-viewer id="ar-viewer"
                      ar
                      ar-modes="webxr scene-viewer quick-look"
                      ar-scale="auto"
                      camera-controls
                      shadow-intensity="1"
                      exposure="1"
                      auto-rotate
                      style="width: 100%; height: 400px; background-color: #f0f0f0; border-radius: 8px;"
                      poster="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100'%3E%3Crect width='100' height='100' fill='%23f0f0f0'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='.3em' fill='%23666'%3EUpload Image%3C/text%3E%3C/svg%3E">
        </model-viewer>        <script>
        document.addEventListener('DOMContentLoaded', function() {
          const viewer = document.getElementById("ar-viewer");
          const arButton = document.getElementById("ar-button");
          const status = document.getElementById("status");
          const arInstructions = document.getElementById("ar-instructions");
          
          // Check if elements exist to prevent null errors
          if (!viewer) {
            console.error("AR viewer element not found");
            return;
          }
          if (!arButton) {
            console.error("AR button element not found");
            return;
          }
          if (!status) {
            console.error("Status element not found");
            return;
          }
          
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
              const match = navigator.userAgent.match(/Chrome\\/([0-9]+)/);
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
            
            // Keep launching messages visible longer
            const duration = (type === "info" && message.includes("Launching")) ? 8000 : 5000;
            
            setTimeout(() => {
              status.style.display = "none";
            }, duration);
          };

          // Check camera permissions for AR
          const checkCameraPermissions = async () => {
            try {
              const permissions = await navigator.permissions.query({ name: 'camera' });
              console.log('Camera permission status:', permissions.state);
              return permissions.state;
            } catch (err) {
              console.log('Permission API not available:', err);
              return 'unknown';
            }
          };

          // Initialize camera check on page load
          checkCameraPermissions();
          
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
            fd.append("image", f);
            
            try {
              // Chrome-specific fetch configuration
              const res = await fetch("/make-glb", { 
                method: "POST", 
                body: fd,
                mode: 'cors',
                credentials: 'omit',
                headers: {
                  'Accept': 'model/gltf-binary, */*'
                }
              });
              
              if (!res.ok) {
                const errorText = await res.text();
                throw new Error(`Server error ${res.status}: ${errorText}`);
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
          
          // Handle AR button click - Simple version that was working
          arButton.addEventListener('click', () => {
            if (!viewer.src) {
              showStatus("Please create a 3D model first!", "error");
              return;
            }

            showStatus("Launching AR viewer...", "info");
            
            try {
              // For local testing, allow without HTTPS check
              const isLocalhost = location.hostname.includes('localhost') || 
                                location.hostname.includes('127.0.0.1') || 
                                location.hostname.startsWith('192.168.');
              
              if (location.protocol !== 'https:' && !isLocalhost) {
                showStatus("AR requires HTTPS. Please use the deployed version on your mobile device.", "error");
                return;
              }
              
              // Simple AR activation - this was working in phone screen
              setTimeout(() => {
                viewer.activateAR();
              }, 500);
              
            } catch (error) {
              console.error("AR activation error:", error);
              showStatus("Error launching AR: " + error.message, "error");
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
            const match = navigator.userAgent.match(/Chrome\\/([0-9]+)/);
            if (match) {
              chromeVersion = match[1];
            }
          }
          
          // Check Android version
          let androidVersion = 'N/A';
          if (isAndroid) {
            const match = navigator.userAgent.match(/Android ([0-9]+)\\.([0-9]+)/);
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
        }); // End DOMContentLoaded
        </script>
      </body>
    </html>
    """
    return Response(html, mimetype="text/html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7861, debug=True)
