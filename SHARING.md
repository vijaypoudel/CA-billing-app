# How to Share the CA Billing App

This guide explains how to share the application with other users.

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

## 4. Moving Data
If you want to share your *current* data with someone else:
1. Go to your `Documents` folder.
2. Copy the `AnkitaCA` folder.
3. Tell the recipient to put that folder in their `Documents` directory before running the app for the first time.
