from django.apps import AppConfig


class QuizAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'quiz_app'
    
    def ready(self):
        # 导入信号处理器
        import quiz_app.models  # 确保信号被加载 