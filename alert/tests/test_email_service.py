import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from types import SimpleNamespace

# Ensure project package root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import types

# Create a lightweight stub for alert.models to avoid Django settings during unit tests
models_stub = types.ModuleType('alert.models')
class _DummyManager:
    def __init__(self):
        pass
    def filter(self, *args, **kwargs):
        return MagicMock(first=MagicMock(return_value=None))

class _DummyModel:
    objects = _DummyManager()

models_stub.GlobalSMTPConfig = _DummyModel
models_stub.AlertMethod = object
models_stub.AlertTemplate = object
import sys as _sys
_sys.modules['alert.models'] = models_stub

from alert.services.alert import AlertService


class TestEmailService(unittest.TestCase):

    def setUp(self):
        # 准备一个假的 SMTP 配置对象
        self.mock_config = SimpleNamespace(
            smtp_host='smtp.example.com',
            smtp_port=587,
            smtp_username='user@example.com',
            smtp_password='password',
            smtp_ssl=False
        )

        # 简单的告警方式对象
        self.alert_method = SimpleNamespace(
            to_list=['test@example.com'],
            name='测试'
        )

    @patch('alert.services.alert.GlobalSMTPConfig')
    @patch('smtplib.SMTP')
    def test_send_email_success(self, mock_smtp_cls, mock_global_config):
        # mock GlobalSMTPConfig.objects.filter(...).first()
        mock_qs = MagicMock()
        mock_qs.first.return_value = self.mock_config
        mock_global_config.objects.filter.return_value = mock_qs

        # mock SMTP context manager
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        success, err = AlertService.send_email_alert(self.alert_method, 'sub', 'content', return_error=True)
        self.assertTrue(success)
        self.assertEqual(err, '')

    @patch('alert.services.alert.GlobalSMTPConfig')
    @patch('smtplib.SMTP')
    def test_send_email_smtp_error(self, mock_smtp_cls, mock_global_config):
        mock_qs = MagicMock()
        mock_qs.first.return_value = self.mock_config
        mock_global_config.objects.filter.return_value = mock_qs

        # mock server to raise SMTPException on login
        mock_server = MagicMock()
        mock_server.login.side_effect = Exception('auth failed')
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        success, err = AlertService.send_email_alert(self.alert_method, 'sub', 'content', return_error=True)
        self.assertFalse(success)
        self.assertTrue(('Unexpected error' in err) or ('SMTP error' in err))


if __name__ == '__main__':
    unittest.main()
