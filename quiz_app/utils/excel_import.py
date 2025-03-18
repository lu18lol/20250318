import pandas as pd
from ..models import Question, Option, Category, Tag

def process_excel_import(file, user):
    """处理Excel导入题目"""
    df = pd.read_excel(file)
    
    # 验证必要列
    required_columns = ['题目类型', '题目内容', '难度']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Excel文件缺少必要列: {col}")
    
    questions_created = 0
    errors = []
    
    for index, row in df.iterrows():
        try:
            # 获取题目类型
            q_type_map = {
                '单选题': 'single',
                '多选题': 'multiple',
                '判断题': 'truefalse',
                '问答题': 'essay'
            }
            q_type = q_type_map.get(row['题目类型'])
            if not q_type:
                errors.append(f"行 {index+2}: 无效的题目类型 '{row['题目类型']}'")
                continue
            
            # 获取难度
            difficulty_map = {
                '简单': 'easy',
                '中等': 'medium',
                '困难': 'hard'
            }
            difficulty = difficulty_map.get(row['难度'], 'medium')
            
            # 创建题目
            question = Question.objects.create(
                type=q_type,
                content=row['题目内容'],
                explanation=row.get('解析', ''),
                difficulty=difficulty,
                created_by=user
            )
            
            # 处理分类
            if '分类' in row and pd.notna(row['分类']):
                categories = [c.strip() for c in str(row['分类']).split(',')]
                for cat_name in categories:
                    cat, _ = Category.objects.get_or_create(name=cat_name)
                    question.categories.add(cat)
            
            # 处理标签
            if '标签' in row and pd.notna(row['标签']):
                tags = [t.strip() for t in str(row['标签']).split(',')]
                for tag_name in tags:
                    tag, _ = Tag.objects.get_or_create(name=tag_name)
                    question.tags.add(tag)
            
            # 处理选项
            if q_type in ['single', 'multiple']:
                for i in range(1, 10):  # 假设最多9个选项
                    option_key = f'选项{i}'
                    is_correct_key = f'选项{i}是否正确'
                    
                    if option_key not in row or pd.isna(row[option_key]):
                        break
                    
                    Option.objects.create(
                        question=question,
                        content=row[option_key],
                        is_correct=row.get(is_correct_key, False)
                    )
            
            elif q_type == 'truefalse':
                # 判断题只有两个选项: 是/否
                Option.objects.create(
                    question=question,
                    content='是',
                    is_correct=row.get('正确答案', '') == '是'
                )
                Option.objects.create(
                    question=question,
                    content='否',
                    is_correct=row.get('正确答案', '') == '否'
                )
            
            questions_created += 1
            
        except Exception as e:
            errors.append(f"行 {index+2}: {str(e)}")
    
    return {
        'success': questions_created > 0,
        'questions_created': questions_created,
        'errors': errors
    } 