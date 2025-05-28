from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from flask_caching import Cache

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+psycopg2://username:password@username.mysql.pythonanywhere-services.com/dbname'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}
db = SQLAlchemy(app)
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})
cache.init_app(app)
# 数据库模型
class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    ingredients = db.Column(db.String(200))
    steps = db.Column(db.Text)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dish_name = db.Column(db.String(100))

# 确保数据库初始化的关键代码
def initialize_database():
    # 确保数据库文件目录存在
    db_dir = os.path.join(basedir, 'instance')
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
    # 在应用上下文中创建数据库
    with app.app_context():
        db.create_all()
        
        # 添加示例数据（如果表为空）
        if not Recipe.query.first():
            sample_recipe = Recipe(
                name="番茄炒蛋",
                ingredients="番茄, 鸡蛋, 盐, 糖",
                steps="1. 鸡蛋打散加少许盐\n2. 热油炒鸡蛋至凝固盛出\n3. 番茄切块炒至出汁\n4. 加入鸡蛋翻炒，加糖调味"
            )
            db.session.add(sample_recipe)
            db.session.commit()
            print("✅ 数据库已创建并添加示例菜谱")

# 在应用启动时调用初始化函数
initialize_database()
@app.route('/')
def index():
    recipes = Recipe.query.all()
    return render_template('index.html', recipes=recipes)   
if __name__ == '__main__':
    initialize_database()  # 启动时初始化数据库
    with app.app_context():
        db.create_all()
    app.run(debug=True)
# app.py 添加新路由

# 清空点菜单
@app.route('/orders/clear', methods=['DELETE'])
def clear_orders():
    try:
        # 删除所有点菜记录
        Order.query.delete()
        db.session.commit()
        return jsonify({'message': '点菜单已清空'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
# 后端分页
@app.route('/search')
@cache.cached(timeout=300, query_string=True)  # 缓存5分钟
def search():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    recipes = Recipe.query.filter(...).paginate(page=page, per_page=per_page)
    
    return jsonify({
        'recipes': [recipe.to_dict() for recipe in recipes.items],
        'total_pages': recipes.pages,
        'current_page': recipes.page
    })
