@echo off
REM ==============================================================================
REM InterviewIQ — Quick Deploy to Hugging Face Spaces
REM ==============================================================================

echo [InterviewIQ] Deploying to Hugging Face Spaces...
echo.

if "%~1"=="" (
    echo Usage: deploy_hf.bat ^<HUGGINGFACE_SPACE_GIT_URL^>
    echo.
    echo Example:
    echo   deploy_hf.bat https://huggingface.co/spaces/your-username/interviewiq
    echo.
    echo Tip: When prompted for password, paste your Hugging Face 'Write' Access Token:
    echo      https://huggingface.co/settings/tokens
    exit /b 1
)

set SPACE_URL=%~1

echo [*] Checking git remote 'space'...
git remote remove space 2>nul
git remote add space %SPACE_URL%

echo [*] Staging all files...
git add .

echo [*] Creating deployment commit...
git commit -m "Deploy update to Hugging Face Spaces" 2>nul

echo [*] Pushing HEAD to Hugging Face Space main branch...
git push -u space HEAD:main --force

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Code successfully pushed to Hugging Face Spaces!
    echo Visit your Space on huggingface.co to view live build logs and launch your app.
    echo.
    echo NOTE: Remember to configure your GEMINI_API_KEY in:
    echo Space Settings -^> Variables and secrets -^> New secret
) else (
    echo.
    echo [ERROR] Git push failed. Please verify your Space URL and Hugging Face Access Token.
)
