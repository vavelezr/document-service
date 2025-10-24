"""
Test básico para Document Service
"""
import sys
import os

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from fastapi.testclient import TestClient
    from main import app
    
    def test_health():
        """Probar health check"""
        client = TestClient(app)
        response = client.get("/health")
        print(f"Health: {response.status_code} - {response.json()}")
        return response.status_code == 200

    def test_docs():
        """Probar documentación"""
        client = TestClient(app)
        response = client.get("/docs")
        print(f"Docs: {response.status_code}")
        return response.status_code == 200

    if __name__ == "__main__":
        print("🧪 Testing Document Service...")
        
        if test_health():
            print("✅ Health check OK")
        else:
            print("❌ Health check failed")
        
        if test_docs():
            print("✅ Docs OK")
        else:
            print("❌ Docs failed")
            
        print("\n� Para ejecutar: uvicorn src.main:app --reload --port 8000")
        print("📚 Docs: http://localhost:8000/docs")
            
except Exception as e:
    print(f"❌ Error: {e}")
    print("Ejecuta: pip install fastapi uvicorn")