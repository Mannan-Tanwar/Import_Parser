# Install Tesseract OCR for Fast Image Processing

Your code is currently slow because it's using a heavy AI vision model. 
Installing Tesseract OCR will make it 100x faster (seconds instead of minutes).

## Windows Installation

1. Download the installer:
   https://github.com/UB-Mannheim/tesseract/wiki

2. Run the installer (tesseract-ocr-w64-setup-5.x.x.exe)

3. During installation, note the installation path (usually `C:\Program Files\Tesseract-OCR`)

4. Add Tesseract to your PATH:
   - Open System Properties → Environment Variables
   - Edit the "Path" variable
   - Add: `C:\Program Files\Tesseract-OCR`
   - Click OK

5. Restart your terminal/command prompt

6. Test it works:
   ```bash
   tesseract --version
   ```

7. Run your code again:
   ```bash
   python main.py image.png
   ```

## Alternative: Quick Install via Chocolatey

If you have Chocolatey installed:
```bash
choco install tesseract
```

## After Installation

Once Tesseract is installed, your image processing will be:
- ✅ Fast (2-5 seconds instead of 2-5 minutes)
- ✅ Accurate for printed text
- ✅ Works offline
- ✅ No GPU needed
