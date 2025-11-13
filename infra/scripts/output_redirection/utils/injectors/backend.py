
from typing import Any, Dict
from ...templates import ENV_TEMPLATE
from jinja2 import Template



class BackendInjector:
       def __init__(self, environment) -> None:
             self.environment = environment
       def backend_dotenv_injection(self, backend_outputs: Dict[str, Any]):
            """
            Algo: 
                  1) Inject template
                  2) Read base env, and append to template injection
                  3) Write file
            Parameters:
                  - env_output: str = the path for where to write the env 
            """

            template = Template(ENV_TEMPLATE)

            # Create copy of base file
            synced_content = template.render(outputs=backend_outputs)

            return synced_content