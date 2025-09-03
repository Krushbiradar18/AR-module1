# AR Artwork Viewer

This application allows users to upload their artwork and view it in Augmented Reality (AR).

## Live Demo

You can try the live demo at: [https://armodule-knu9fivlq-krushnalis-projects.vercel.app](https://armodule-knu9fivlq-krushnalis-projects.vercel.app)

## Features

- Upload any image
- Convert the image into a 3D model (GLB format)
- View the 3D model in AR directly from the browser
- Responsive design

## How It Works

1. User uploads an image
2. The server converts the image into a 3D GLB model
3. The model is displayed in the browser using Google's model-viewer
4. User can click "View in AR" to see the artwork in their real environment

## Technical Details

- Flask backend
- Google's model-viewer for AR visualization
- Trimesh for 3D model creation
- PIL for image processing

## Installation

```bash
# Clone the repository
git clone https://github.com/Krushbiradar18/AR-module1.git

# Navigate to the project directory
cd AR-module1

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

## Deployment

This application is deployed on Vercel. To deploy your own instance:

1. Fork this repository
2. Sign up for a Vercel account if you don't have one
3. Import your repository in the Vercel dashboard
4. Deploy it with default settings

### Vercel Deployment Settings

The application uses the following files for Vercel deployment:
- `vercel.json` - Configuration for the Vercel platform
- `requirements.txt` - Python dependencies
- `app.py` - Main application code
- `wsgi.py` - WSGI entry point

## AR Compatibility

For the AR features to work properly:

### iOS Requirements:
- iOS 12 or later
- Safari browser
- ARKit-compatible device (iPhone 6s or newer)

### Android Requirements:
- Android 8.0 or later
- ARCore-compatible device
- Chrome browser (version 79 or newer)

## Notes on AR Functionality

- AR features require HTTPS, which is why it works better on the deployed version
- Local testing may have limitations with AR features
- For best results, ensure good lighting conditions when using AR

## License

MIT
