import smtplib
import logging
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict

from ..models import GlobalSMTPConfig, AlertMethod, AlertTemplate

logger = logging.getLogger(__name__)


class AlertService:
    """告警服务"""
    
    @staticmethod
    def _simple_render(template_str: str, context: Dict) -> str:
        """
        简单的模板渲染函数，支持 {{ variable }} 语法
        
        Args:
            template_str: 模板字符串
            context: 上下文数据
            
        Returns:
            渲染后的字符串
        """
        result = template_str
        
        # 匹配 {{ variable }} 格式的变量
        pattern = r'\{\{\s*(\w+)\s*\}\}'
        
        def replace_var(match):
            var_name = match.group(1)
            return str(context.get(var_name, f'{{{{{var_name}}}}}'))
        
        return re.sub(pattern, replace_var, result)
    
    @staticmethod
    def render_template(template: AlertTemplate, context: Dict) -> tuple:
        """
        渲染告警模板
        
        Args:
            template: 告警模板对象
            context: 模板上下文数据
            
        Returns:
            (标题, 内容)
        """
        try:
            # 渲染标题
            rendered_title = AlertService._simple_render(template.title, context)
            
            # 渲染内容
            rendered_content = AlertService._simple_render(template.content, context)
            
            return rendered_title, rendered_content
        except Exception as e:
            logger.error(f'Template rendering error: {e}')
            return template.title, template.content
    
    @staticmethod
    def send_email_alert(
        alert_method: AlertMethod,
        subject: str,
        content: str,
        return_error: bool = False
    ) -> bool:
        """
        发送邮件告警
        
        Args:
            alert_method: 告警方式对象
            subject: 邮件主题
            content: 邮件内容
            
        Returns:
            是否发送成功
        """
        try:
            # 获取全局SMTP配置
            smtp_config = GlobalSMTPConfig.objects.filter(is_active=True).first()
            if not smtp_config:
                msg = 'No active SMTP config found'
                logger.error(msg)
                return (False, msg) if return_error else False
            
            smtp_host = smtp_config.smtp_host
            smtp_port = smtp_config.smtp_port
            smtp_username = smtp_config.smtp_username
            smtp_password = smtp_config.smtp_password
            smtp_ssl = smtp_config.smtp_ssl
            smtp_timeout = getattr(smtp_config, 'smtp_timeout', 10)
            to_list = alert_method.to_list
            
            if not smtp_username or not smtp_password or not to_list:
                msg = 'Email config incomplete'
                logger.error(msg)
                return (False, msg) if return_error else False
            
            # 简单校验收件人格式
            email_pattern = r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$"
            for addr in to_list:
                if not re.match(email_pattern, addr):
                    msg = f'Invalid recipient email: {addr}'
                    logger.error(msg)
                    return (False, msg) if return_error else False

            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = ', '.join(to_list)
            msg['Subject'] = subject
            
            # 添加邮件内容
            msg.attach(MIMEText(content, 'plain', 'utf-8'))
            
            # 发送邮件，使用 with 管理连接并设置超时，正确调用 ehlo/starttls
            try:
                if smtp_ssl:
                    with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=smtp_timeout) as server:
                        server.ehlo()
                        server.login(smtp_username, smtp_password)
                        server.send_message(msg)
                else:
                    with smtplib.SMTP(smtp_host, smtp_port, timeout=smtp_timeout) as server:
                        server.ehlo()
                        server.starttls()
                        server.ehlo()
                        server.login(smtp_username, smtp_password)
                        server.send_message(msg)

                logger.info(f'Email alert sent to {to_list}')
                return (True, '') if return_error else True
            except smtplib.SMTPException as se:
                msg = f'SMTP error: {se}'
                logger.error(msg, exc_info=True)
                return (False, msg) if return_error else False
            except Exception as e:
                msg = f'Unexpected error when sending email: {e}'
                logger.error(msg, exc_info=True)
                return (False, msg) if return_error else False
            
        except Exception as e:
            msg = f'Email send error: {e}'
            logger.error(msg, exc_info=True)
            return (False, msg) if return_error else False
    
    @staticmethod
    def send_alert(
        alert_method: Optional[AlertMethod],
        alert_template: Optional[AlertTemplate],
        context: Dict
    ) -> bool:
        """
        发送告警
        
        Args:
            alert_method: 告警方式对象
            alert_template: 告警模板对象
            context: 告警上下文数据
            
        Returns:
            是否发送成功
        """
        if not alert_method:
            logger.info('Alert method not configured')
            return False
        
        if not alert_template:
            logger.info('Alert template not configured')
            return False
        
        # 渲染模板
        subject, content = AlertService.render_template(alert_template, context)
        
        # 根据告警类型发送
        if alert_method.type == 'email':
            return AlertService.send_email_alert(alert_method, subject, content)
        else:
            logger.error(f'Unknown alert type: {alert_method.type}')
            return False
