from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional, Dict, Any

from app.schemas import KerberosKinitRequest, KerberosStatusResponse, ApiResponse
from app.services.kerberos import kerberos_service

router = APIRouter(prefix="/kerberos", tags=["kerberos"])


@router.post("/kinit", response_model=ApiResponse[Dict[str, Any]])
def kinit(request: KerberosKinitRequest):
    """获取 Kerberos 票据"""
    if request.keytab_path:
        result = kerberos_service.kinit_with_keytab(request.principal, request.keytab_path)
    elif request.password:
        result = kerberos_service.kinit_with_password(request.principal, request.password)
    else:
        raise HTTPException(status_code=400, detail="必须提供 keytab 路径或密码")

    if not result["success"]:
        return ApiResponse.error(message=result["message"])

    return ApiResponse.success(data=result, message=result["message"])


@router.get("/status", response_model=KerberosStatusResponse)
def get_status(principal: Optional[str] = None):
    """获取 Kerberos 票据状态"""
    return kerberos_service.get_status(principal)


@router.post("/keytab/upload", response_model=ApiResponse[Dict[str, Any]])
async def upload_keytab(principal: str, file: UploadFile = File(...)):
    """上传 Keytab 文件"""
    try:
        content = await file.read()
        result = kerberos_service.upload_keytab(principal, content)

        if not result["success"]:
            return ApiResponse.error(message=result["message"])

        return ApiResponse.success(data=result, message=result["message"])
    except Exception as e:
        return ApiResponse.error(message=f"上传失败: {str(e)}")


@router.post("/destroy", response_model=ApiResponse[Dict[str, Any]])
def destroy_ticket(principal: str):
    """销毁 Kerberos 票据"""
    result = kerberos_service.destroy_ticket(principal)
    return ApiResponse.success(data=result, message=result["message"])


@router.post("/auto-renewal/start", response_model=ApiResponse[Dict[str, Any]])
def start_auto_renewal(principal: str, keytab_path: Optional[str] = None):
    """启动票据自动续期"""
    if not keytab_path:
        keytab_path = kerberos_service.get_keytab_path(principal)
        if not keytab_path:
            raise HTTPException(status_code=400, detail="未找到对应的 keytab 文件")

    result = kerberos_service.start_auto_renewal(principal, keytab_path)
    return ApiResponse.success(data=result, message=result["message"])


@router.post("/auto-renewal/stop", response_model=ApiResponse[Dict[str, Any]])
def stop_auto_renewal(principal: str):
    """停止票据自动续期"""
    result = kerberos_service.stop_auto_renewal(principal)
    if not result["success"]:
        return ApiResponse.error(message=result["message"])
    return ApiResponse.success(data=result, message=result["message"])
