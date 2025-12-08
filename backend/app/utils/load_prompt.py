from functools import lru_cache
from pathlib import Path

import yaml

from app.utils.logger import logger


@lru_cache(maxsize=10)
def load_prompt(prompt_name: str) -> str:
    prompts_file = "prompts.yaml"
    prompts_path = Path(__file__).parent.parent / "prompts" / prompts_file
    try:
        with open(prompts_path, "r", encoding="utf-8") as file:
            # TODO: Validate if yaml can be loaded and parsed as a dict
            prompt_data = yaml.safe_load(file)
            prompt_template = prompt_data.get(prompt_name, "")
            if not prompt_template:
                logger.error(f"Prompt template not found in {prompts_path}")
            return prompt_template

    except FileNotFoundError:
        logger.error(f"Prompt file {prompts_path} not found.")
        return ""
