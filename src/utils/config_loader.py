from dotenv import load_dotenv
import os
import yaml

load_dotenv()

APP_ENV = os.environ.get('APP_ENV', 'development').lower()
PROJECT_ROOT = os.environ.get('PROJECT_ROOT', os.getcwd())

def load_config_by_name(name):
    config_path = f"{PROJECT_ROOT}/src/config/{APP_ENV}/{name.lower()}.yaml"
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    return config