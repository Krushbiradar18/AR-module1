# AR Artwork Viewer

This application allows users to upload their artwork and view it in Augmented Reality (AR).

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
git clone <your-repo-url>

# Navigate to the project directory
cd ar_module

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

## Deployment

This application is configured to be deployed on Vercel.

1. Create a Vercel account if you don't have one
2. Install the Vercel CLI: `npm i -g vercel`
3. Run `vercel` in the project directory and follow the prompts

## Requirements

- Python 3.7+
- Required Python packages listed in requirements.txt
