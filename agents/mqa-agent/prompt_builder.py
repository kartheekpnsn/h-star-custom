import yaml
from typing import List, Dict
from prompts import MULTI_QUERY_PROMPT

class PromptBuilder:
    def __init__(self, yaml_file: str):
        # Load the configuration
        with open(yaml_file, 'r') as f:
            self.config = yaml.safe_load(f)
        self.categories = self._parse_categories()
        self.parameters = self.config.get('parameters', {})

    def get_time_context(self):
        from datetime import datetime, timedelta
        current_date = datetime.now()
        week_back_date = current_date - timedelta(days=7)
        return {
            "current_date": current_date.strftime("%Y-%m-%d"),
            "week_back_date": week_back_date.strftime("%Y-%m-%d"),
            "current_month": current_date.strftime("%B"),
            "current_year": current_date.year
        }

    def _parse_categories(self) -> Dict[str, List[str]]:
        """
        Adjusts for the YAML structure where categories are a list of dicts 
        or a specific nested format.
        """
        cat_map = {}
        for item in self.config.get('categories', []):
            if isinstance(item, dict):
                name = item.get('name')
                params = item.get('parameters', [])
                if name:
                    cat_map[name] = params
        return cat_map

    def get_context_metadata(self, selected_categories: List[str]):
        """Extracts unique parameters and their sub-values for selected categories."""
        unique_params = set()
        for cat in selected_categories:
            params = self.categories.get(cat, [])
            unique_params.update(params)
        
        metadata = {param: self.parameters.get(param, []) for param in unique_params}
        return metadata

    def build_system_prompt(self, user_query: str, selected_categories: List[str], time_context: dict = None) -> str:
        metadata = self.get_context_metadata(selected_categories)
        if time_context is None:
            time_context = self.get_time_context()
        
        # Format the metadata into a readable string for the LLM
        schema_str = ""
        for param, values in metadata.items():
            schema_str += f"- {param}: {', '.join(values)}\n"

        selected_categories = ', '.join(selected_categories)
        prompt = MULTI_QUERY_PROMPT.format(
            user_query=user_query,
            selected_categories=selected_categories,
            schema_str=schema_str,
            **time_context
        )
        return prompt

if __name__ == "__main__":
    builder = PromptBuilder("agents/mqa-agent/config.yaml")
    system_prompt = builder.build_system_prompt(
        user_query="How has my drug D1 performed over last 6 months?", 
        selected_categories=["performance_trends"]
    )

    print(system_prompt)