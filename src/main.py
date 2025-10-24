import os
import uuid
from datetime import datetime, timedelta
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request, Query, Body
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import hashlib
import httpx
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Configuración
STORAGE_BUCKET = os.getenv("S3_BUCKET_NAME", "citizen-docs-bucket")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8080")

# Simulación de "base de datos" en memoria (diferente estructura)
files_storage = {}
access_tokens_db = {}

# Modelos (DIFERENTES a los compañeros)
class FileMetadata(BaseModel):
    file_id: str
    user_id: str
    original_name: str
    size_bytes: int
    created_at: str
    verified: bool = False
    storage_path: str

class ShareRequest(BaseModel):
    expiration_hours: int = 24
    max_downloads: int = 3  # Diferente default

class DownloadLinksRequest(BaseModel):
    file_paths: List[str]

# Utilidades
def now_utc():
    return datetime.utcnow()

def generate_timestamped_name(filename: str) -> str:
    name, ext = os.path.splitext(filename)
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")[:-3]
    return f"{name}_{timestamp}{ext}"

def validate_file_format(filename: str) -> bool:
    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
    ext = os.path.splitext(filename)[1].lower()
    return ext in allowed_extensions

# Validación de token (mock como tus compañeros)
async def verify_token(request: Request) -> Dict[str, Any]:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requerido")
    
    # Mock token validation (como en el ejemplo de tus compañeros)
    return {"sub": "test_user_123", "type": "citizen"}

# Endpoints principales (DIFERENTES a los compañeros)
@app.post("/api/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    category: str = Query("general"),
    token_data: dict = Depends(verify_token)
):
    user_id = token_data["sub"]
    
    # Validar archivo
    if not validate_file_format(file.filename):
        raise HTTPException(status_code=400, detail="Formato no soportado")
    
    if file.size and file.size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(status_code=413, detail="Archivo excede el límite")
    
    # Generar metadata
    doc_id = str(uuid.uuid4())
    stored_filename = generate_timestamped_name(file.filename)
    file_path = f"files/{user_id}/{stored_filename}"
    
    # Simular subida
    file_content = await file.read()
    
    # Guardar metadata
    metadata = {
        "file_id": doc_id,
        "user_id": user_id,
        "original_name": file.filename,
        "stored_name": stored_filename,
        "size_bytes": len(file_content),
        "created_at": now_utc().isoformat(),
        "verified": False,
        "category": category,
        "storage_path": file_path,
        "checksum": hashlib.sha256(file_content).hexdigest()
    }
    
    files_storage[file_path] = metadata
    
    return {
        "success": True, 
        "file_id": doc_id, 
        "storage_path": file_path,
        "message": "Archivo subido exitosamente"
    }

@app.get("/api/files/user/{user_id}")
async def get_user_files(
    user_id: str,
    request: Request,
    page: int = Query(1),
    size: int = Query(20),
    verified_only: bool = Query(False),
    token_data: dict = Depends(verify_token)
):
    requester_id = token_data.get("sub")
    
    # Control de acceso
    if requester_id != user_id and token_data.get("type") != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # Filtrar archivos del usuario
    user_files = [f for f in files_storage.values() if f["user_id"] == user_id]
    
    if verified_only:
        user_files = [f for f in user_files if f["verified"]]
    
    total_count = len(user_files)
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    page_files = user_files[start_idx:end_idx]
    
    return {
        "total_files": total_count,
        "page": page,
        "page_size": size,
        "files": page_files
    }

@app.get("/api/files/all")
async def get_all_files(
    request: Request,
    page: int = Query(1),
    size: int = Query(15),
    token_data: dict = Depends(verify_token)
):
    # Solo administradores
    if token_data.get("type") != "admin":
        raise HTTPException(status_code=403, detail="Requiere permisos de administrador")
    
    all_files = list(files_storage.values())
    total_count = len(all_files)
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    page_files = all_files[start_idx:end_idx]
    
    return {
        "total_files": total_count,
        "current_page": page,
        "page_size": size,
        "files": page_files
    }

@app.post("/api/files/download-links")
async def generate_download_links(
    request: Request,
    file_paths: List[str] = Body(..., embed=True),
    token_data: dict = Depends(verify_token)
):
    requester_id = token_data.get("sub")
    
    download_links = {}
    for file_path in file_paths:
        file_data = files_storage.get(file_path)
        if not file_data:
            raise HTTPException(status_code=404, detail=f"Archivo no encontrado: {file_path}")
        
        # Verificar acceso
        if file_data["user_id"] != requester_id and token_data.get("type") != "admin":
            raise HTTPException(status_code=403, detail=f"Sin acceso a: {file_path}")
        
        # URL temporal
        download_url = f"https://storage.aws.com/{STORAGE_BUCKET}/{file_data['storage_path']}?expires=3600"
        download_links[file_path] = download_url
    
    return {"download_links": download_links}

@app.get("/api/files/list/{user_id}")
async def list_user_files_with_links(
    request: Request,
    user_id: str,
    include_links: bool = Query(False),
    token_data: dict = Depends(verify_token)
):
    requester_id = token_data.get("sub")
    
    if requester_id != user_id and token_data.get("type") != "admin":
        raise HTTPException(status_code=403, detail="Acceso no autorizado")
    
    # Obtener archivos del usuario
    user_files = [f for f in files_storage.values() if f["user_id"] == user_id]
    file_paths = [f["storage_path"] for f in user_files]
    
    if not include_links:
        return {"file_paths": file_paths}
    
    # Generar links de descarga
    download_links = {}
    for file_data in user_files:
        download_url = f"https://storage.aws.com/{STORAGE_BUCKET}/{file_data['storage_path']}?expires=7200"
        download_links[file_data["storage_path"]] = download_url
    
    return {"download_links": download_links}

@app.post("/api/files/{file_id}/share")
async def create_file_share(
    request: Request,
    file_id: str,
    share_config: ShareRequest,
    token_data: dict = Depends(verify_token)
):
    user_id = token_data["sub"]
    
    # Buscar archivo
    file_data = None
    for f in files_storage.values():
        if f["file_id"] == file_id and f["user_id"] == user_id:
            file_data = f
            break
    
    if not file_data:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    # Crear token de acceso
    access_token = str(uuid.uuid4())
    expires_at = now_utc() + timedelta(hours=share_config.expiration_hours)
    
    access_tokens_db[access_token] = {
        "file_id": file_id,
        "owner": user_id,
        "expires_at": expires_at.isoformat(),
        "max_uses": share_config.max_downloads,
        "current_uses": 0
    }
    
    return {
        "access_token": access_token,
        "share_link": f"{request.base_url}api/files/shared/{access_token}",
        "expires_at": expires_at.isoformat()
    }

@app.delete("/api/files/remove/{file_path:path}")
async def remove_file(
    request: Request,
    file_path: str,
    token_data: dict = Depends(verify_token)
):
    user_id = token_data["sub"]
    
    file_data = files_storage.get(file_path)
    if not file_data:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    # Verificar permisos
    if file_data["user_id"] != user_id and token_data.get("type") != "admin":
        raise HTTPException(status_code=403, detail="Sin permisos para eliminar")
    
    # Eliminar
    del files_storage[file_path]
    
    return {"success": True, "message": "Archivo eliminado", "file_path": file_path}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "document-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)