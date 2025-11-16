


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
            self.SHORTENED_URL_LENGTH = int(os.getenv("SHORTENED_URL_LENGTH", "8"))
            self.MAX_MINUTES_STORAGE = int(os.getenv("MAX_MINUTES_STORAGE", "60"))
            self.MIN_MINUTES_STORAGE = int(os.getenv("MIN_MINUTES_STORAGE", "5"))
            
      def validate_required_vars(self):
            missing_vars = []
            for var in self.required_vars:
                  if not getattr(self, var):
                        missing_vars.append(var)
                  else:
                        print(f"VAR: {var} has {getattr(self, var)}")
            if missing_vars:
                  raise Exception(f"Missing vars: {missing_vars}")


