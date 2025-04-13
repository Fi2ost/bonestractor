# main.py - Main entry point for the Medical Report Extractor application

import logging
from gui import MedicalReportExtractorApp

# Configure logging (basic configuration, can be enhanced)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler() # Log to console
        # Optionally add logging.FileHandler('app.log') here
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Initializes and runs the GUI application."""
    logger.info("Starting Medical Report Extractor Application...")
    try:
        app = MedicalReportExtractorApp()
        app.mainloop()
        logger.info("Application closed normally.")
    except Exception as e:
        logger.critical(f"Application encountered a critical error: {e}", exc_info=True)
        # Optionally show a message box here for critical startup errors if Tkinter is available

if __name__ == "__main__":
    main()