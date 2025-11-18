


from abc import ABC, abstractmethod
import os

class BaseSettings(ABC):      
      @abstractmethod
      def extract_all_variables(self):
            ...
      
      @property
      @abstractmethod
      def required_vars(self):
            ...
      
      def _extract_app_logic_variables(self):
            """
            Not environment dependent 
            """
            pass
            
      def validate_required_vars(self):
            missing_vars = []
            for var in self.required_vars:
                  if not getattr(self, var):
                        missing_vars.append(var)
                  else:
                        print(f"VAR: {var} has {getattr(self, var)}")
            if missing_vars:
                raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}") 
