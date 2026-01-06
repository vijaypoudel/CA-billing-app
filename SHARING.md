# How to Share the CA Billing App

This guide explains how to share the application with other users or move it to a different machine (like a Windows laptop).

## 0. How to Transfer the Project (to your Windows Laptop)
Since you need to build the `.exe` on Windows, you first need to get all these files onto your Windows laptop.

### Method 1: Zipping (Easiest)
1. On your current machine, right-click the main project folder (`sidereal-apollo`) and select **Compress** or **Send to Zip**.
2. Send this `.zip` file to your Windows laptop via **Google Drive**, **WeTransfer**, or a **USB Drive**.
3. On the Windows laptop, **Extract** the zip file to your `Downloads` or `Documents` folder.

### Method 2: Git (Advanced)
If you have Git installed on your Windows laptop, you can simply clone your repository:
```bash
git clone <your-repository-url>
```

---

## 1. Prerequisites for Building
Once the files are on your Windows laptop, follow these steps:

1. **Python Installed**: You must have Python 3.10+ installed on your computer.
2. **Required Libraries**: All libraries in `requirements.txt` must be installed. You can install them with:
   ```bash
   pip install -r ca_billing_app/requirements.txt
   ```
3. **Correct OS**:
   - To build a **Windows `.exe`**, you MUST run the build on a Windows computer.
   - To build a **Mac `.app`**, you MUST run the build on a Mac.
   - *Note: A Mac cannot build a Windows .exe file, and vice-versa.*

4. **Project Files**: Make sure you have the `build.py` script and the `ca_billing_app` folder in the same place.

---

## 1. Build the Application

You can build the app in two ways:

### Option A: Single Executable (Recommended for sharing)
This creates one single file that you can send directly.
```bash
python build.py --onefile
```
- **Windows**: Look for `dist/CABillingApp.exe`
- **Mac**: Look for `dist/CABillingApp` (it will be a single app bundle)

### Option B: Application Folder
This creates a folder with many files. It starts up faster but is harder to share.
```bash
python build.py
```
- The output is in `dist/CABillingApp`. You **must** zip this folder before sharing.

## 2. Share the File
Send the `.exe` or zipped folder to the recipient. 

> [!IMPORTANT]
> **OS Compatibility**: A file built on a Mac will only work on Mac. A file built on Windows will only work on Windows.

## 3. What the Recipient Needs to Do
1. **Download and Run**: They can just click the file to start.
2. **Data Storage**: The app automatically creates a folder at `~/Documents/AnkitaCA` to store its database and settings.
3. **Email Setup**: If they want to use the backup feature, they should update their email password in `ca_billing_app/daily_tasks.py` (or you can do it for them before building).

## 4. Troubleshooting: App Doesn't Open
If the `.exe` file was created but doesn't open when you double-click it, follow these steps to find the error:

### Step 1: Build in Debug Mode
On your Windows laptop, run the build command again with the `--debug` flag:
```bash
python build.py --onefile --debug
```
This will create a version of the app that shows a black console window (terminal) when it starts.

### Step 2: Run from Terminal to see Errors
1. Open **Command Prompt** or **PowerShell**.
2. Go to the folder where the `.exe` is (e.g., `cd dist`).
3. Type the name of the file to run it: `CABillingApp.exe`
4. Look at the error message (Traceback) that stays in the window. **Copy and send that error to me.**

### Common Issues
- **Missing Requirements**: Make sure you ran `pip install -r ca_billing_app/requirements.txt` on the Windows machine.
- **Path Issues**: Sometimes antivirus software blocks new `.exe` files. Try running it as Administrator or temporarily disabling antivirus.

---

## 5. Moving Data
If you want to share your *current* data with someone else:
1. Go to your `Documents` folder.
2. Copy the `AnkitaCA` folder.
3. Tell the recipient to put that folder in their `Documents` directory before running the app for the first time.
