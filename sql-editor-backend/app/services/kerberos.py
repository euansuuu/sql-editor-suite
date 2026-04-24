import subprocess
import re
import os
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from config.settings import settings


class KerberosService:
    """Kerberos 票据管理服务"""

    def __init__(self):
        self.keytab_dir = settings.KEYTAB_DIR
        self.ticket_cache_dir = settings.TICKET_CACHE_DIR
        self._renewal_threads = {}
        self._stop_events = {}

    def _get_krb5cc_path(self, principal: str) -> Path:
        """获取票据缓存文件路径"""
        safe_principal = principal.replace('/', '_').replace('@', '_')
        return self.ticket_cache_dir / f"krb5cc_{safe_principal}"

    def kinit_with_keytab(self, principal: str, keytab_path: str) -> dict:
        """使用 keytab 获取票据"""
        krb5cc_path = self._get_krb5cc_path(principal)
        env = os.environ.copy()
        env['KRB5CCNAME'] = str(krb5cc_path)

        try:
            result = subprocess.run(
                ['kinit', '-kt', keytab_path, principal],
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                return {
                    "success": False,
                    "message": f"kinit 失败: {result.stderr}",
                }

            return {
                "success": True,
                "message": "票据获取成功",
                "principal": principal,
                "ticket_cache": str(krb5cc_path),
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"执行异常: {str(e)}",
            }

    def kinit_with_password(self, principal: str, password: str) -> dict:
        """使用密码获取票据"""
        krb5cc_path = self._get_krb5cc_path(principal)
        env = os.environ.copy()
        env['KRB5CCNAME'] = str(krb5cc_path)

        try:
            result = subprocess.run(
                ['kinit', principal],
                env=env,
                input=password,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                return {
                    "success": False,
                    "message": f"kinit 失败: {result.stderr}",
                }

            return {
                "success": True,
                "message": "票据获取成功",
                "principal": principal,
                "ticket_cache": str(krb5cc_path),
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"执行异常: {str(e)}",
            }

    def get_status(self, principal: Optional[str] = None) -> dict:
        """获取 Kerberos 票据状态"""
        if principal:
            krb5cc_path = self._get_krb5cc_path(principal)
            env = os.environ.copy()
            env['KRB5CCNAME'] = str(krb5cc_path)
        else:
            env = os.environ.copy()

        try:
            result = subprocess.run(
                ['klist'],
                env=env,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return {
                    "valid": False,
                    "principal": None,
                    "ticket_expires": None,
                    "message": "无有效票据",
                }

            # 解析 klist 输出
            output = result.stdout
            principal_match = re.search(r'Default principal:\s+(\S+)', output)
            expires_match = re.search(r'Valid starting\s+Expires\s+Service principal\n[^\n]+\s+(\S+\s+\S+)', output)

            found_principal = principal_match.group(1) if principal_match else None
            expires_str = expires_match.group(1) if expires_match else None

            ticket_expires = None
            if expires_str:
                try:
                    ticket_expires = datetime.strptime(expires_str, '%m/%d/%Y %H:%M:%S')
                except ValueError:
                    pass

            return {
                "valid": True,
                "principal": found_principal,
                "ticket_expires": ticket_expires,
                "message": "票据有效",
                "raw_output": output,
            }
        except Exception as e:
            return {
                "valid": False,
                "principal": None,
                "ticket_expires": None,
                "message": f"检查状态失败: {str(e)}",
            }

    def destroy_ticket(self, principal: str) -> dict:
        """销毁票据"""
        krb5cc_path = self._get_krb5cc_path(principal)
        env = os.environ.copy()
        env['KRB5CCNAME'] = str(krb5cc_path)

        try:
            subprocess.run(
                ['kdestroy'],
                env=env,
                capture_output=True,
                text=True,
                timeout=10,
            )
            return {"success": True, "message": "票据已销毁"}
        except Exception as e:
            return {"success": False, "message": f"销毁失败: {str(e)}"}

    def upload_keytab(self, principal: str, file_content: bytes) -> dict:
        """上传 keytab 文件"""
        safe_principal = principal.replace('/', '_').replace('@', '_')
        keytab_path = self.keytab_dir / f"{safe_principal}.keytab"

        try:
            keytab_path.parent.mkdir(parents=True, exist_ok=True)
            keytab_path.write_bytes(file_content)

            return {
                "success": True,
                "message": "Keytab 上传成功",
                "keytab_path": str(keytab_path),
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"上传失败: {str(e)}",
            }

    def get_keytab_path(self, principal: str) -> Optional[str]:
        """获取 keytab 文件路径"""
        safe_principal = principal.replace('/', '_').replace('@', '_')
        keytab_path = self.keytab_dir / f"{safe_principal}.keytab"
        return str(keytab_path) if keytab_path.exists() else None

    def _auto_renewal_worker(self, principal: str, keytab_path: str, stop_event: threading.Event):
        """自动续期工作线程"""
        while not stop_event.is_set():
            status = self.get_status(principal)

            if not status["valid"] and status["ticket_expires"]:
                # 检查是否需要续期（过期前 1 小时续期）
                time_until_expiry = status["ticket_expires"] - datetime.now()
                if time_until_expiry < timedelta(hours=1):
                    self.kinit_with_keytab(principal, keytab_path)

            # 每 30 分钟检查一次
            stop_event.wait(1800)

    def start_auto_renewal(self, principal: str, keytab_path: str) -> dict:
        """启动自动续期"""
        if principal in self._renewal_threads and self._renewal_threads[principal].is_alive():
            return {"success": True, "message": "自动续期已在运行"}

        stop_event = threading.Event()
        self._stop_events[principal] = stop_event

        thread = threading.Thread(
            target=self._auto_renewal_worker,
            args=(principal, keytab_path, stop_event),
            daemon=True,
        )
        thread.start()
        self._renewal_threads[principal] = thread

        return {"success": True, "message": "自动续期已启动"}

    def stop_auto_renewal(self, principal: str) -> dict:
        """停止自动续期"""
        if principal in self._stop_events:
            self._stop_events[principal].set()
            self._stop_events.pop(principal, None)
            self._renewal_threads.pop(principal, None)
            return {"success": True, "message": "自动续期已停止"}

        return {"success": False, "message": "未找到该 principal 的自动续期任务"}


# 全局单例
kerberos_service = KerberosService()
