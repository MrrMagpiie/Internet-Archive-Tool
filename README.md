# Library Archive Tool

A desktop application built with Python and PyQt6 for processing, viewing, and organizing collections of single-page document scans (such as TIFFs) into digital records.

## Features
* **Document Schema**: Allows for the creation of custom schema for generating IA metadata for processing multiple documents or similar types.
* **Image Processing:** Uses imageMagick for automatically deskewing of document images.
* **Memory Management:** Uses JIT rendering to convert cached `QImage` objects into `QPixmap` objects only when they are visible on screen, minimizing memory usage.
* **Asynchronous Tasks:** Image processing and loading are handled via Python `multiprocessing` queues to maintain UI responsiveness.
* **Metadata Storage:** Uses a local SQLite database.

---

## Running the Application (End Users)

This application is distributed as a Windows executable (`.exe`). It requires an external C-library (ImageMagick) to handle image processing.

### Prerequisites
1. Download the [ImageMagick Windows Installer](https://imagemagick.org/script/download.php#windows).
2. Run the installer and check the following boxes during setup:
   * [x] *Install legacy utilities (e.g. convert)*
   * [x] *Install development headers and libraries for C and C++*

### Installation
1. Navigate to the [Releases](../../releases) page of this repository.
2. Download the latest `LibraryArchive.exe` file.
3. Place the file in your preferred directory and run it.

---

### Current Limiations
This is very much a work in progress and the gui is not complete, however the underlying document process should be functional for deskewing images, generating metadata, and uploading to the Internet Archive.
in its current state the releases are for testing purposes.
