# Deploying to Vercel

Follow these steps to deploy your AR Artwork Viewer to Vercel:

## Prerequisites

1. Create a Vercel account at https://vercel.com if you don't have one
2. Install Node.js if you haven't already (required for Vercel CLI)

## Deployment Steps

### Option 1: Using Vercel CLI (Recommended)

1. Install Vercel CLI globally:
   ```bash
   npm install -g vercel
   ```

2. Navigate to your project directory:
   ```bash
   cd /Users/krushnali/ar_module
   ```

3. Login to Vercel:
   ```bash
   vercel login
   ```

4. Deploy the project:
   ```bash
   vercel
   ```
   
   Follow the prompts. When asked about the build settings:
   - Choose to use the settings from your `vercel.json` file
   - Select "Python" as the framework
   - Select "Other" as the project type
   - Set output directory to "." (current directory)
   - Set build command to "pip install -r requirements.txt"

5. After deployment is complete, Vercel will give you a URL to access your application.

### Option 2: Using Vercel Dashboard

1. Push your code to a Git repository (GitHub, GitLab, or Bitbucket)

2. Go to https://vercel.com and sign in

3. Click "New Project"

4. Import your Git repository

5. Configure your project:
   - Framework Preset: Other
   - Build Command: `pip install -r requirements.txt`
   - Output Directory: `.`
   - Install Command: Leave as default

6. Click "Deploy"

## Important Notes

- Make sure your `vercel.json` file is in the root directory
- Vercel has limitations for Python applications, especially those with complex dependencies
- The free tier has limitations on build time and resources
- You may need to upgrade your Vercel plan if your application requires more resources

## Troubleshooting

If you encounter issues with the deployment:

1. Check Vercel's build logs for errors
2. Ensure all dependencies are listed in `requirements.txt`
3. Make sure your application is configured to listen on the port provided by Vercel
4. Try simplifying your application if it's hitting resource limits
