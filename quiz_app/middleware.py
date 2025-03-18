from django.shortcuts import render, redirect
from django.urls import resolve
from django.conf import settings

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # 需要登录的URL路径前缀列表
        self.login_required_paths = [
            '/exams/',
            '/submissions/',
            '/questions/',
            '/mistakes/',
            '/profile/',
        ]
        # 总是允许访问的URL列表
        self.public_paths = [
            '/login/',
            '/admin/',
            '/static/',
            '/media/',
            '/',  # 主页允许访问
            '/accounts/login/',  # 兼容Django默认的登录URL
        ]

    def __call__(self, request):
        # 已登录用户不受限制
        if request.user.is_authenticated:
            return self.get_response(request)
        
        # 检查当前路径是否需要登录
        path = request.path_info
        
        # 如果是Django默认的账户登录路径，重定向到我们的登录页面
        if path.startswith('/accounts/login/'):
            next_url = request.GET.get('next', '/')
            return redirect(f'/login/?next={next_url}')
        
        # 检查是否为公开路径
        for public_path in self.public_paths:
            if path.startswith(public_path):
                return self.get_response(request)
        
        # 检查是否为受限路径
        for login_path in self.login_required_paths:
            if path.startswith(login_path):
                # 使用我们的自定义错误页面
                return render(request, 'quiz_app/error_pages/login_required.html', {
                    'requested_path': path
                }, status=403)
        
        # 默认情况下允许访问
        return self.get_response(request) 