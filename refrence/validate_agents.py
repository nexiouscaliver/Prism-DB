#!/usr/bin/env python3

import os
import sys
import json
import logging
import re
from pathlib import Path
import importlib.util
import inspect

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("validate_agents.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("agent_validator")

# OpenAI function name validation regex
# Must contain only lowercase letters, numbers, and underscores
# Must start with a letter
# Must not end with an underscore
# Must not contain consecutive underscores
FUNCTION_NAME_PATTERN = re.compile(r'^[a-z][a-z0-9_]*[a-z0-9]$')

def is_valid_function_name(name):
    """Check if a function name is valid according to OpenAI requirements"""
    return bool(FUNCTION_NAME_PATTERN.match(name)) and '__' not in name

def validate_agent_config_files():
    """Validate agent names in config files"""
    agents_dir = Path(__file__).parent / "agents"
    if not agents_dir.exists():
        logger.error(f"Agents directory not found at {agents_dir}")
        return False
    
    valid_count = 0
    invalid_count = 0
    issues = []
    
    for config_file in agents_dir.glob("**/config.json"):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            if 'name' in config:
                name = config['name']
                if is_valid_function_name(name):
                    valid_count += 1
                else:
                    invalid_count += 1
                    issues.append(f"Invalid agent name in {config_file}: '{name}'")
                    logger.warning(f"Invalid agent name in {config_file}: '{name}'")
        except Exception as e:
            logger.error(f"Error validating {config_file}: {e}")
            issues.append(f"Error validating {config_file}: {e}")
    
    logger.info(f"Validated {valid_count + invalid_count} agent config files: {valid_count} valid, {invalid_count} invalid")
    return valid_count, invalid_count, issues

def validate_agent_class_names():
    """Validate agent class names in Python files"""
    agents_dir = Path(__file__).parent / "agents"
    if not agents_dir.exists():
        logger.error(f"Agents directory not found at {agents_dir}")
        return False
    
    valid_count = 0
    invalid_count = 0
    issues = []
    
    for py_file in agents_dir.glob("**/*.py"):
        try:
            # Import the module to inspect it
            module_name = py_file.stem
            spec = importlib.util.spec_from_file_location(module_name, py_file)
            if spec is None or spec.loader is None:
                logger.warning(f"Could not load spec for {py_file}")
                continue
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find all classes ending with "Agent"
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and name.endswith("Agent"):
                    # Convert class name to function name convention (camelCase to snake_case)
                    function_name = re.sub('([A-Z])', r'_\1', name).lower().lstrip('_')
                    
                    if is_valid_function_name(function_name):
                        valid_count += 1
                    else:
                        invalid_count += 1
                        issues.append(f"Invalid agent class in {py_file}: '{name}' -> '{function_name}'")
                        logger.warning(f"Invalid agent class in {py_file}: '{name}' -> '{function_name}'")
        except Exception as e:
            logger.error(f"Error validating {py_file}: {e}")
            issues.append(f"Error validating {py_file}: {e}")
    
    logger.info(f"Validated {valid_count + invalid_count} agent classes: {valid_count} valid, {invalid_count} invalid")
    return valid_count, invalid_count, issues

def validate_function_definitions():
    """Validate function definitions in agent files"""
    agents_dir = Path(__file__).parent / "agents"
    if not agents_dir.exists():
        logger.error(f"Agents directory not found at {agents_dir}")
        return False
    
    valid_count = 0
    invalid_count = 0
    issues = []
    
    for py_file in agents_dir.glob("**/*.py"):
        try:
            # Read the file and look for function definitions
            with open(py_file, 'r') as f:
                content = f.read()
            
            # Look for function definitions in a class that match "def function_name"
            function_matches = re.findall(r'def\s+([a-zA-Z0-9_]+)\s*\(', content)
            
            for func_name in function_matches:
                # Skip dunder methods and private methods
                if func_name.startswith('__') or func_name.startswith('_'):
                    continue
                
                if is_valid_function_name(func_name):
                    valid_count += 1
                else:
                    invalid_count += 1
                    issues.append(f"Invalid function name in {py_file}: '{func_name}'")
                    logger.warning(f"Invalid function name in {py_file}: '{func_name}'")
        except Exception as e:
            logger.error(f"Error validating functions in {py_file}: {e}")
            issues.append(f"Error validating functions in {py_file}: {e}")
    
    logger.info(f"Validated {valid_count + invalid_count} function names: {valid_count} valid, {invalid_count} invalid")
    return valid_count, invalid_count, issues

def generate_report(config_results, class_results, function_results):
    """Generate a validation report"""
    report_path = Path(__file__).parent / "agent_validation_report.txt"
    
    total_valid = config_results[0] + class_results[0] + function_results[0]
    total_invalid = config_results[1] + class_results[1] + function_results[1]
    
    with open(report_path, 'w') as f:
        f.write("===== Prism-DB Agent Validation Report =====\n\n")
        f.write(f"Total validated items: {total_valid + total_invalid}\n")
        f.write(f"Valid items: {total_valid}\n")
        f.write(f"Invalid items: {total_invalid}\n\n")
        
        f.write("===== Config File Names =====\n")
        f.write(f"Valid: {config_results[0]}, Invalid: {config_results[1]}\n\n")
        
        f.write("===== Agent Class Names =====\n")
        f.write(f"Valid: {class_results[0]}, Invalid: {class_results[1]}\n\n")
        
        f.write("===== Function Names =====\n")
        f.write(f"Valid: {function_results[0]}, Invalid: {function_results[1]}\n\n")
        
        f.write("===== Issues =====\n\n")
        all_issues = config_results[2] + class_results[2] + function_results[2]
        for issue in all_issues:
            f.write(f"- {issue}\n")
    
    logger.info(f"Validation report generated at {report_path}")
    return report_path

def main():
    """Main function to validate agent names"""
    logger.info("Starting agent validation process...")
    
    config_results = validate_agent_config_files()
    class_results = validate_agent_class_names()
    function_results = validate_function_definitions()
    
    report_path = generate_report(config_results, class_results, function_results)
    
    # Determine exit code based on whether any invalid items were found
    total_invalid = config_results[1] + class_results[1] + function_results[1]
    if total_invalid > 0:
        logger.warning(f"Validation completed with {total_invalid} issues. See {report_path} for details.")
        return 1
    else:
        logger.info("Validation completed successfully with no issues!")
        return 0

if __name__ == "__main__":
    sys.exit(main()) 