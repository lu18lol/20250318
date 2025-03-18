# 答题系统

一个功能完善的在线答题系统，支持多种题型、随机出题、错题分析等功能。

## 功能特点

### 题库管理
- 支持单选题、多选题、判断题、问答题
- Excel批量导入题目
- 题目分类与标签管理
- 题目编辑、删除、查看功能

### 测试管理
- 测试目录页面，用户可浏览并选择参加的测试
- 随机抽题功能（从题库中随机抽取指定数量的题目）
- 支持设置测试时间、及格分数线等参数
- 测试结果统计与分析

### 用户答题界面
- 清晰展示题目内容和选项
- 答题进度显示
- 计时功能
- 提交后即时评分

### 成绩反馈系统
- 根据不同分数段显示不同的提示信息
- 提示信息可在后台自定义配置
- 答题结果详情展示（正确答案、解析等）

### 错题分析功能
- 自动收集错题
- 按分类和题型统计错误率
- 错题集查看和管理
- 错题分析图表展示

## 技术栈

- **后端**: Python + Django + Django REST Framework
- **前端**: Django Templates + Tailwind CSS + Alpine.js + Chart.js
- **数据库**: PostgreSQL
- **缓存**: Redis
- **任务队列**: Celery

## 安装与运行

### 环境要求
- Python 3.9+
- PostgreSQL
- Redis (可选，用于缓存和Celery)

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/yourusername/quiz-system.git
cd quiz-system
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置数据库
```bash
# 在 quiz_system/settings.py 中配置数据库连接
```

5. 运行迁移
```bash
python manage.py migrate
```

6. 创建超级用户
```bash
python manage.py createsuperuser
```

7. 运行开发服务器
```bash
python manage.py runserver
```

8. 访问系统
- 前台: http://localhost:8000/
- 后台: http://localhost:8000/admin/

## 部署

### 使用Docker部署

1. 构建镜像
```bash
docker build -t quiz-system .
```

2. 运行容器
```bash
docker-compose up -d
```

## 许可证

MIT 