"""
PrismDB application entry point.

This script runs the Flask application.
"""
import os
import sys
from app import create_app, logger

# Create app instance
app = create_app()

if __name__ == "__main__":
    # Check for Google API key
    if not os.environ.get("GOOGLE_API_KEY"):
        print("\033[91mError: GOOGLE_API_KEY environment variable is not set.\033[0m")
        print("\033[93mPlease set it before running the application:\033[0m")
        print("\033[96m    # On Linux/macOS:")
        print("    export GOOGLE_API_KEY=your_api_key_here")
        print("\n    # On Windows:")
        print("    set GOOGLE_API_KEY=your_api_key_here\033[0m\n")
        print("You can get a Google API key from: https://ai.google.dev/")
        sys.exit(1)
    
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "development") == "development"
    
    logger.info("Starting PrismDB application", 
                port=port, 
                debug=debug, 
                environment=os.environ.get("FLASK_ENV", "development"),
                model="gemini-2.0-flash-exp")
    
    print("\033[92m✓\033[0m PrismDB is running with Gemini Flash 2.0 model")
    print(f"\033[92m✓\033[0m Server is running at: http://localhost:{port}")
    
    app.run(host="0.0.0.0", port=port, debug=debug) 