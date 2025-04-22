"""
PrismDB Scheduler module for Prism-DB.
This module defines a scheduler to periodically check and update prism database records.
"""
import time
import threading
import logging
import schedule
from datetime import datetime
import os
import dotenv

from prismagent import get_prism_agents

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('prism_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PrismScheduler")

dotenv.load_dotenv(dotenv_path=".env.agent")

def prism_update_job():
    """
    Job to check and update prism database records.
    This function will initialize a Prism agent and instruct it to update the prism database.
    """
    logger.info(f"Starting prism update job at {datetime.now()}")
    
    try:
        # Create a Prism agent with GPT-4o
        prism_agent = get_prism_agents(model_name="gpt-4o")
        
        # Create a message instructing the PrismDBAgent to update all prism records
        update_message = {
            "role": "user",
            "content": """
            Please check and update all prism database records:
            1. For each connected database, verify if a corresponding prism exists
            2. If a prism doesn't exist, create one by extracting schema information
            3. If a prism exists, check if the schema has changed and update if necessary
            4. Document all changes and provide a summary report
            
            This is an automated scheduled task for database maintenance.
            """
        }
        
        # Run the agent with the update message
        response = prism_agent.run(messages=[update_message])
        
        # Log the result
        logger.info(f"Prism update job completed successfully at {datetime.now()}")
        logger.info(f"Response: {response.content}")
        
    except Exception as e:
        logger.error(f"Error in prism update job: {str(e)}")

def run_scheduler():
    """
    Run the scheduler to periodically check and update prism database records.
    """
    # Schedule the prism update job to run every 6 hours
    schedule.every(6).hours.do(prism_update_job)
    
    # Also run it once at startup
    logger.info("Running initial prism update job at startup")
    prism_update_job()
    
    # Run the scheduler in a loop
    while True:
        schedule.run_pending()
        time.sleep(60)  # Sleep for 1 minute between checks

def start_scheduler_thread():
    """
    Start the scheduler in a separate thread so it doesn't block the main application.
    """
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True  # Set as daemon so it will exit when the main program exits
    scheduler_thread.start()
    logger.info("Prism scheduler thread started")
    return scheduler_thread

if __name__ == "__main__":
    logger.info("Starting Prism scheduler")
    run_scheduler() 