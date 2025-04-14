# Medical Report Extractor

## Project Description
This project aims to create a tool to extract relevant information from medical reports, specifically operative reports. The goal is to automate the identification of ICD-10-CM codes from unstructured text in medical documents.

## main.py Description
The `main.py` file is the main entry point for the Medical Report Extractor application. It initializes and runs the application's graphical user interface (GUI). It sets up logging to record the application's activity, including informational messages, warnings, and errors. It imports the `MedicalReportExtractorApp` class from the `gui` module and creates an instance of it to start the GUI. The main file also gracefully handles errors and logs them.

## Scripts
The `scripts` directory contains several Python scripts used for setting up and populating the ICD-10-CM database and processing ICD data.

## Configuration

The `config.py` file, located in the `src` directory, plays a crucial role in this project. It is used to set configuration variables for the project. The `config.py` file centralizes all of the paths and makes them easy to edit. By centralizing these paths in one place, we make the codebase more modular and less dependent on specific directory structures. This allows for easier migration and deployment of the project.