import aiohttp
import logging
import urllib.parse
from typing import Optional, Dict, Any, Tuple
from Utils.Const import CONFIG

logger = logging.getLogger(__name__)


class GuacamoleService:
    """Guacamole 服务类，处理与 Guacamole API 的交互"""
    
    _instance = None
    _token_cache: Optional[Dict[str, Any]] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._load_config()
    
    def _load_config(self):
        """加载 Guacamole 配置"""
        try:
            guac_config = CONFIG.get('GUACAMOLE', {})
            self.base_url = guac_config.get('BASE_URL', 'http://127.0.0.1:8080/guacamole')
            self.api_url = guac_config.get('API_URL', 'http://127.0.0.1:8080/guacamole/api')
            self.websocket_url = guac_config.get('WEBSOCKET_URL', 'ws://127.0.0.1:8080/guacamole/websocket-tunnel')
            self.username = guac_config.get('USERNAME', 'guacadmin')
            self.password = guac_config.get('PASSWORD', 'guacadmin')
            self.data_source = guac_config.get('DATA_SOURCE', 'postgresql')
            logger.info(f"Guacamole 配置加载完成: {self.base_url}")
        except Exception as e:
            logger.error(f"加载 Guacamole 配置失败: {e}")
            raise
    
    async def get_token(self) -> Tuple[str, str]:
        """
        获取 Guacamole 认证 Token
        
        Returns:
            Tuple[str, str]: (authToken, dataSource)
        """
        url = f"{self.api_url}/tokens"
        data = {
            "username": self.username,
            "password": self.password
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data, ssl=False) as response:
                    if response.status == 200:
                        result = await response.json()
                        token = result.get('authToken')
                        data_source = result.get('dataSource', self.data_source)
                        logger.info("成功获取 Guacamole Token")
                        return token, data_source
                    else:
                        text = await response.text()
                        logger.error(f"获取 Token 失败: {response.status} - {text}")
                        raise Exception(f"获取 Guacamole Token 失败: {response.status}")
        except aiohttp.ClientError as e:
            logger.error(f"连接 Guacamole 服务失败: {e}")
            raise Exception(f"连接 Guacamole 服务失败: {e}")
    
    async def get_connection_by_name(self, token: str, data_source: str, name: str) -> Optional[Dict[str, Any]]:
        """
        根据名称获取连接信息
        
        Args:
            token: 认证 Token
            data_source: 数据源
            name: 连接名称
            
        Returns:
            连接信息字典，如果不存在返回 None
        """
        url = f"{self.api_url}/session/data/{data_source}/connections?token={token}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, ssl=False) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.debug(f"Guacamole 连接列表响应: {result}")
                        if isinstance(result, dict):
                            for conn_id, conn_data in result.items():
                                if isinstance(conn_data, dict) and conn_data.get('name') == name:
                                    conn_data['identifier'] = conn_id
                                    return conn_data
                        elif isinstance(result, list):
                            for conn in result:
                                if isinstance(conn, dict) and conn.get('name') == name:
                                    return conn
                        return None
                    else:
                        logger.error(f"获取连接列表失败: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"获取连接列表异常: {e}")
            return None
    
    async def create_connection(
        self, 
        name: str,
        hostname: str,
        port: int,
        username: str,
        password: str,
        **extra_params
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        创建临时 RDP 连接（自动获取 Token）
        
        Args:
            name: 连接名称
            hostname: 目标主机地址
            port: RDP 端口
            username: 登录用户名
            password: 登录密码
            **extra_params: 额外的 RDP 参数
            
        Returns:
            Tuple[token, data_source, connection_id]
        """
        try:
            token, data_source = await self.get_token()
            
            url = f"{self.api_url}/session/data/{data_source}/connections?token={token}"
            
            width = max(1024, extra_params.get("width", 1024))
            height = max(768, extra_params.get("height", 768))
            
            parameters = {
                "hostname": hostname,
                "port": str(port),
                "username": username,
                "password": password,
                "domain": extra_params.get("domain", ""),
                "security": extra_params.get("security", "nla"),
                "ignore-cert": extra_params.get("ignore_cert", "true"),
                "color-depth": str(extra_params.get("color_depth", "32")),
                "resize-method": extra_params.get("resize_method", "display-update"),
                "enable-audio": extra_params.get("enable_audio", "true"),
                "enable-drive": extra_params.get("enable_drive", "true"),
                "drive-path": extra_params.get("drive_path", "/tmp/guac-drive"),
                "create-drive-path": extra_params.get("create_drive_path", "true"),
                "width": str(width),
                "height": str(height)
            }
            
            connection_data = {
                "name": name,
                "parentIdentifier": "ROOT",
                "protocol": "rdp",
                "attributes": {
                    "max-connections": extra_params.get("max_connections", "2"),
                    "max-connections-per-user": extra_params.get("max_connections_per_user", "1")
                },
                "parameters": parameters
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=connection_data, ssl=False) as response:
                    if response.status == 200:
                        result = await response.json()
                        connection_id = result.get('identifier')
                        logger.info(f"成功创建临时 Guacamole 连接: {name}, ID: {connection_id}, 分辨率: {width}x{height}")
                        return token, data_source, connection_id
                    else:
                        text = await response.text()
                        logger.error(f"创建连接失败: {response.status} - {text}")
                        return None, None, None
                        
        except Exception as e:
            logger.error(f"创建连接异常: {e}")
            return None, None, None
    
    async def update_connection(
        self,
        token: str,
        data_source: str,
        connection_id: str,
        hostname: str = None,
        port: int = None,
        username: str = None,
        password: str = None,
        **extra_params
    ) -> bool:
        """
        更新 RDP 连接
        
        Args:
            token: 认证 Token
            data_source: 数据源
            connection_id: 连接 ID
            hostname: 目标主机地址
            port: RDP 端口
            username: 登录用户名
            password: 登录密码
            **extra_params: 额外的 RDP 参数
            
        Returns:
            是否成功
        """
        # 直接使用传入的connection_id构建URL，不需要再次获取连接信息
        
        url = f"{self.api_url}/session/data/{data_source}/connections/{connection_id}?token={token}"
        
        # 构建完整的参数
        parameters = {
            "hostname": hostname or "",
            "port": str(port) if port else "3389",
            "username": username or "",
            "password": password or "",
            "security": extra_params.get("security", "nla"),
            "ignore-cert": extra_params.get("ignore_cert", "true"),
            "color-depth": str(extra_params.get("color_depth", "32")),
            "resize-method": extra_params.get("resize_method", "display-update"),
            "width": str(extra_params.get("width", 1024)),
            "height": str(extra_params.get("height", 768)),
            "enable-audio": "true",
            "enable-drive": "true",
            "drive-path": "/tmp/guac-drive",
            "create-drive-path": "true"
        }
        
        # 构建完整的连接数据
        connection_data = {
            "name": extra_params.get('name', ''),
            "parentIdentifier": "ROOT",
            "protocol": "rdp",
            "attributes": {
                "max-connections": "2",
                "max-connections-per-user": "1"
            },
            "parameters": parameters
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                # 尝试使用PUT方法更新连接
                async with session.put(url, json=connection_data, ssl=False) as response:
                    if response.status in [200, 204]:
                        resolution_info = f", 分辨率: {parameters.get('width')}x{parameters.get('height')}" if 'width' in parameters else ""
                        logger.info(f"成功更新 Guacamole 连接: {connection_id}{resolution_info}")
                        return True
                    else:
                        text = await response.text()
                        logger.error(f"更新连接失败: {response.status} - {text}")
                        return False
        except Exception as e:
            logger.error(f"更新连接异常: {e}")
            return False
    
    async def delete_connection(self, token: str, data_source: str, connection_id: str) -> bool:
        """
        删除连接
        
        Args:
            token: 认证 Token
            data_source: 数据源
            connection_id: 连接 ID
            
        Returns:
            是否成功
        """
        url = f"{self.api_url}/session/data/{data_source}/connections/{connection_id}?token={token}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(url, ssl=False) as response:
                    if response.status == 204:
                        logger.info(f"成功删除 Guacamole 连接: {connection_id}")
                        return True
                    else:
                        text = await response.text()
                        logger.error(f"删除连接失败: {response.status} - {text}")
                        return False
        except Exception as e:
            logger.error(f"删除连接异常: {e}")
            return False
    
    def get_websocket_url(self, token: str, data_source: str, connection_id: str) -> str:
        """
        获取 WebSocket 连接 URL
        
        Args:
            token: 认证 Token
            data_source: 数据源
            connection_id: 连接 ID
            
        Returns:
            WebSocket URL
        """
        base_ws_url = self.websocket_url
        params = {
            "token": token,
            "GUAC_ID": connection_id,
            "GUAC_DATA_SOURCE": data_source,
            "GUAC_TYPE": "c"
        }
        query_string = urllib.parse.urlencode(params)
        ws_url = f"{base_ws_url}?{query_string}"
        logger.debug(f"生成 WebSocket URL: {ws_url}")
        return ws_url
    
    async def get_or_create_connection(
        self,
        name: str,
        hostname: str,
        port: int,
        username: str,
        password: str,
        **extra_params
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        获取或创建连接（便捷方法）
        
        Args:
            name: 连接名称
            hostname: 目标主机地址
            port: RDP 端口
            username: 登录用户名
            password: 登录密码
            **extra_params: 额外的 RDP 参数
            
        Returns:
            Tuple[token, data_source, connection_id]
        """
        try:
            token, data_source = await self.get_token()
            
            existing_conn = await self.get_connection_by_name(token, data_source, name)
            
            if existing_conn:
                connection_id = existing_conn.get('identifier')
                logger.info(f"使用现有连接: {name}, ID: {connection_id}")
                
                await self.update_connection(
                    token, data_source, connection_id,
                    hostname=hostname,
                    port=port,
                    username=username,
                    password=password,
                    name=name,
                    **extra_params
                )
                return token, data_source, connection_id
            
            connection_id = await self.create_connection(
                token, data_source, name,
                hostname, port, username, password,
                **extra_params
            )
            
            if connection_id:
                return token, data_source, connection_id
            
            existing_conn = await self.get_connection_by_name(token, data_source, name)
            if existing_conn:
                connection_id = existing_conn.get('identifier')
                logger.info(f"连接已存在，获取现有连接: {name}, ID: {connection_id}")
                await self.update_connection(
                    token, data_source, connection_id,
                    hostname=hostname,
                    port=port,
                    username=username,
                    password=password,
                    name=name,
                    **extra_params
                )
                return token, data_source, connection_id
            
            return None, None, None
            
        except Exception as e:
            logger.error(f"获取或创建连接失败: {e}")
            return None, None, None


guacamole_service = GuacamoleService()
