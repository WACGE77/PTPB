from django.apps import AppConfig


class AlertConfig(AppConfig):
    name = 'alert'
    
    def ready(self):
        import alert.signals
