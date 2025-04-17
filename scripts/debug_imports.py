#!/usr/bin/env python3
"""
Debug script to check available modules and classes in the Agno package.
This can help identify the correct import paths when facing import errors.
"""
import inspect
import pkgutil
import sys
import importlib
from pprint import pprint

def explore_package(package_name):
    """
    Explore a package to find all available modules and classes.
    
    Args:
        package_name: Name of the package to explore
        
    Returns:
        Dictionary with module information
    """
    try:
        # Import the package
        package = importlib.import_module(package_name)
        
        # Get all modules
        modules = {}
        
        print(f"\n=== Exploring package: {package_name} ===")
        
        # Get package location
        print(f"Package location: {package.__file__}")
        
        # Get all submodules
        print("\n=== Submodules ===")
        submodules = list(pkgutil.iter_modules(package.__path__, package_name + '.'))
        for module_info in submodules:
            module_name = module_info.name
            print(f"- {module_name}")
            
            try:
                # Import the module
                module = importlib.import_module(module_name)
                
                # Get all classes in the module
                classes = []
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and obj.__module__ == module_name:
                        classes.append(name)
                
                if classes:
                    print(f"  Classes: {', '.join(classes)}")
                
                modules[module_name] = {
                    'classes': classes
                }
            except Exception as e:
                print(f"  Error importing module {module_name}: {str(e)}")
        
        return modules
    
    except ImportError:
        print(f"Error: Package {package_name} not found")
        return {}
    except Exception as e:
        print(f"Error exploring package {package_name}: {str(e)}")
        return {}

def main():
    """Main function to run the script."""
    print("=== Debugging Agno imports ===")
    print(f"Python version: {sys.version}")
    
    # Check if agno is installed
    try:
        import agno
        print(f"Agno version: {getattr(agno, '__version__', 'unknown')}")
        print(f"Agno package: {agno.__file__}")
    except ImportError:
        print("Agno is not installed")
        return
    
    # Explore agno package
    agno_modules = explore_package('agno')
    
    # Explore agno.tools specifically
    tools_modules = explore_package('agno.tools')
    
    # Look for Tool class specifically
    print("\n=== Looking for Tool class ===")
    found = False
    
    for module_name in tools_modules:
        try:
            module = importlib.import_module(module_name)
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and name == 'Tool':
                    found = True
                    print(f"Found Tool class in {module_name}")
                    print(f"Full import path: from {module_name} import Tool")
        except Exception as e:
            print(f"Error looking for Tool in {module_name}: {str(e)}")
    
    if not found:
        print("Tool class not found in any agno.tools modules")
        print("Looking in other agno modules...")
        
        for module_name in agno_modules:
            try:
                module = importlib.import_module(module_name)
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and name == 'Tool':
                        found = True
                        print(f"Found Tool class in {module_name}")
                        print(f"Full import path: from {module_name} import Tool")
            except Exception:
                pass
    
    if not found:
        print("Tool class not found in any agno modules")
        print("Checking alternative base classes...")
        
        # Check for base classes with similar names
        alternative_names = ['BaseTool', 'ToolBase', 'AgnoTool']
        for alt_name in alternative_names:
            for module_name in tools_modules:
                try:
                    module = importlib.import_module(module_name)
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and name == alt_name:
                            print(f"Found alternative base class {alt_name} in {module_name}")
                            print(f"Full import path: from {module_name} import {alt_name}")
                except Exception:
                    pass

if __name__ == "__main__":
    main() 