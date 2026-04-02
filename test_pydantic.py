import sys
import os

# Add src to the path
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    from pydantic import BaseModel
    print("Successfully imported pydantic.BaseModel")
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel
    print("Successfully imported ai_karen_engine.pydantic_stub.BaseModel")

class TestModel(BaseModel):
    id: str

t = TestModel(id="test")
print(f"Created model with id: {t.id}")
