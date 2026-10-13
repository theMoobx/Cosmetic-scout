Cosmetic-to-3D Creator — Full Project Starter

This version connects an actual image-to-3D provider: Meshy API.
It can:
- Search public web results (best effort) and open 16 platform-specific search links.
- Organize reference images and a project manifest.
- Generate a model from one selected local image through Meshy's Image-to-3D API.
- Poll task status and download returned GLB/FBX/OBJ files.
- Open downloaded files with the default program.
- If Blender is installed, convert a supported model to .blend and .fbx.

Windows setup:
1. Extract this ZIP.
2. Install Python 3.10+ if needed.
3. Double-click run_app.bat.
4. Open Settings and enter your Meshy API key. Official API documentation: https://docs.meshy.ai/en/api/image-to-3d
5. Save settings. API access may require a paid plan/credits; check your account before generating.
6. On Search & references, create a project, add a clear image, or select any local image on the Generate tab.
7. Generate 3D model. When it completes, select the downloaded model and open it or use Blender conversion.
8. For FBX/BLEND conversion, install Blender and ensure it is found in Settings.

Safety/privacy:
- API key is stored locally in the current Windows user profile config file.
- Never share the API key.
- Search results are possible leads, not confirmed cosmetic matches.
- The app does not bypass login walls, access private posts, or guarantee complete results across social networks.
- AI reconstruction from a single image is approximate; multiple images help identification but this version's Meshy request uses one image.
- The app has not been tested on the user's specific PC. The EXE build script is included but must be run on Windows and verified.


WINDOWS STANDALONE EXE (AUTOMATIC BUILD)
----------------------------------------
The project includes .github/workflows/build-windows-exe.yml for building on a real
Windows runner. This is more reliable than trying to build a Windows EXE on Linux.

To use it:
1. Create/sign into a GitHub account and create a new repository.
2. Upload the CONTENTS of this project folder (app.py, requirements.txt, etc.).
   Make sure the .github/workflows/build-windows-exe.yml file is included.
3. Open the repository's Actions tab.
4. Choose "Build Windows EXE" and click "Run workflow" (or push to main).
5. When it finishes, open the workflow run and download the
   "CosmeticTo3DCreator-Windows" artifact.
6. Extract the downloaded ZIP; run CosmeticTo3DCreator.exe on Windows.

The EXE has not been built/tested on your PC yet. Windows may show a SmartScreen
warning for an unsigned personal EXE. Only run it if you built it from this source.

CREDITS: IMPORTANT
------------------
The app cannot mint real AI-provider credits or make a third-party API free.
The local app's search/reference/project features do not need Meshy credits.
Meshy API generation is separately billed in provider credits. Meshy's official
docs currently describe API calls as prepaid usage, and API access depends on
the plan. Check current provider terms before spending. Avoid putting an API key
in a public repository; enter it only in the app's local Settings screen.
