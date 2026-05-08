"""
长友杯辩论赛赛果查询系统 - 后端主程序
技术栈：Python + Flask
功能：提供辩论赛赛果查询、排行榜、管理员录入等功能
作者：AI助手
日期：2026-05-08

组织架构：
- 8名选手：安玲珊、王羿嘉彤、孙嘉栋、孟庆博、张涵、谢佳琪、刘昕雨、杨沉析
- 孙嘉栋兼任主理人（player + manager）
- 张涵兼任选手、嘉宾、管理员（player + guest + admin）

分组：
- A组：安玲珊、王羿嘉彤、孙嘉栋
- B组：孟庆博、张涵（嘉宾）、谢佳琪
- C组：刘昕雨、杨沉析

身份系统说明：
- player（选手）：可以查询自己的赛果、查看排行榜和比赛详情
- guest（特邀嘉宾）：同选手权限，但不参与晋级排名
- manager（主理人）：拥有选手所有权限，可以录入和修改赛果
- admin（管理员）：拥有所有权限，包括录入、修改赛果和管理用户

权限说明：
- 选手和特邀嘉宾：只能查看
- 主理人和管理员：可以录入和修改赛果
- 不同身份可以兼得，例如孙嘉栋是选手兼主理人，张涵是选手兼嘉宾兼管理员
"""

# 导入所需的模块
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
from datetime import datetime
from functools import wraps

# 创建Flask应用实例
app = Flask(__name__)
# 设置session密钥，用于加密session数据（请修改为自己的密钥）
app.secret_key = 'debate-competition-2026-secret-key'

# 定义数据文件路径，与app.py在同一目录
DATA_FILE = os.path.join(os.path.dirname(__file__), 'data.json')


def load_data():
    """
    加载数据函数
    从data.json文件中读取数据
    返回：包含用户、选手和比赛记录的字典
    """
    # 检查数据文件是否存在
    if os.path.exists(DATA_FILE):
        # 如果存在，读取文件内容
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # 如果不存在，创建默认数据结构
        data = {
            "users": [
                {"username": "安玲珊", "password": "123456", "name": "安玲珊", "roles": ["player"], "contestant_name": "安玲珊"},
                {"username": "王羿嘉彤", "password": "123456", "name": "王羿嘉彤", "roles": ["player"], "contestant_name": "王羿嘉彤"},
                {"username": "孙嘉栋", "password": "123456", "name": "孙嘉栋", "roles": ["player", "manager"], "contestant_name": "孙嘉栋"},
                {"username": "孟庆博", "password": "123456", "name": "孟庆博", "roles": ["player"], "contestant_name": "孟庆博"},
                {"username": "张涵", "password": "123456", "name": "张涵", "roles": ["player", "guest", "admin"], "contestant_name": "张涵"},
                {"username": "谢佳琪", "password": "123456", "name": "谢佳琪", "roles": ["player"], "contestant_name": "谢佳琪"},
                {"username": "刘昕雨", "password": "123456", "name": "刘昕雨", "roles": ["player"], "contestant_name": "刘昕雨"},
                {"username": "杨沉析", "password": "123456", "name": "杨沉析", "roles": ["player"], "contestant_name": "杨沉析"}
            ],
            "contestants": [
                {"name": "安玲珊", "group": "A", "is_guest": False},
                {"name": "王羿嘉彤", "group": "A", "is_guest": False},
                {"name": "孙嘉栋", "group": "A", "is_guest": False},
                {"name": "孟庆博", "group": "B", "is_guest": False},
                {"name": "张涵", "group": "B", "is_guest": True},
                {"name": "谢佳琪", "group": "B", "is_guest": False},
                {"name": "刘昕雨", "group": "C", "is_guest": False},
                {"name": "杨沉析", "group": "C", "is_guest": False}
            ],
            "matches": []
        }
        # 保存默认数据到文件
        save_data(data)
        return data


def save_data(data):
    """
    保存数据函数
    将数据写入data.json文件
    参数：data - 要保存的数据字典
    """
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        # ensure_ascii=False确保中文正常显示，indent=2使JSON格式美观
        json.dump(data, f, ensure_ascii=False, indent=2)


def login_required(f):
    """
    登录验证装饰器
    用于保护需要登录才能访问的路由
    如果用户未登录，则重定向到登录页面
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查session中是否有用户信息
        if 'user' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    管理员权限验证装饰器
    用于保护只有主理人和管理员才能访问的路由
    如果用户没有相应权限，则重定向到首页
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查用户是否登录
        if 'user' not in session:
            return redirect(url_for('login', next=request.url))
        
        # 检查用户是否有管理员或主理人权限
        user_roles = session['user'].get('roles', [])
        if 'admin' not in user_roles and 'manager' not in user_roles:
            return render_template('error.html', message='您没有权限访问此页面')
        
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """
    获取当前登录用户信息
    返回：用户信息字典，如果未登录则返回None
    """
    return session.get('user')


def has_role(role):
    """
    检查当前用户是否拥有指定角色
    参数：role - 角色名称（player/guest/manager/admin）
    返回：True或False
    """
    if 'user' not in session:
        return False
    return role in session['user'].get('roles', [])


# ==================== 路由定义 ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    登录页面路由
    GET：显示登录表单
    POST：处理登录请求
    """
    # 如果用户已登录，直接跳转到首页
    if 'user' in session:
        return redirect(url_for('index'))
    
    # 处理POST请求（登录表单提交）
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 加载数据
        data = load_data()
        
        # 查找匹配的用户
        user = None
        for u in data['users']:
            if u['username'] == username and u['password'] == password:
                user = u
                break
        
        # 验证用户
        if user:
            # 登录成功，将用户信息保存到session
            session['user'] = user
            # 获取next参数，登录后跳转到原页面
            next_url = request.args.get('next')
            if next_url:
                return redirect(next_url)
            return redirect(url_for('index'))
        else:
            # 登录失败，显示错误信息
            return render_template('login.html', error='用户名或密码错误')
    
    # GET请求，显示登录表单
    return render_template('login.html')


@app.route('/logout')
def logout():
    """
    登出路由
    清除session中的用户信息，重定向到登录页面
    """
    session.pop('user', None)
    return redirect(url_for('login'))


@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """
    修改密码路由
    GET：显示修改密码表单
    POST：处理修改密码请求
    """
    user = get_current_user()
    error = None
    success = None
    
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # 验证旧密码
        if old_password != user['password']:
            error = '原密码错误'
        elif not new_password or len(new_password) < 6:
            error = '新密码长度不能少于6位'
        elif new_password != confirm_password:
            error = '两次输入的新密码不一致'
        else:
            # 更新密码
            data = load_data()
            for u in data['users']:
                if u['username'] == user['username']:
                    u['password'] = new_password
                    break
            save_data(data)
            
            # 更新session中的用户信息
            session['user']['password'] = new_password
            success = '密码修改成功'
    
    return render_template('change_password.html', user=user, error=error, success=success)


@app.route('/vote')
@login_required
def vote_page():
    """
    投票页面路由
    显示投票功能页面
    需要登录才能访问
    """
    data = load_data()
    user = get_current_user()
    polls = data.get('polls', [])
    
    # 查找用户参与的投票
    my_polls = []
    for poll in polls:
        if user['username'] in poll.get('voters', []):
            has_voted = user['username'] in poll.get('votes', {})
            my_polls.append({
                'id': poll['id'],
                'topic': poll['topic'],
                'positive_side': poll['positive_side'],
                'negative_side': poll['negative_side'],
                'status': poll['status'],
                'has_voted': has_voted,
                'results': poll.get('results', None),
                'votes': poll.get('votes', {}),
                'voters': poll.get('voters', [])
            })
    
    return render_template('vote.html', user=user, polls=polls, my_polls=my_polls)


@app.route('/vote/create', methods=['GET', 'POST'])
@login_required
def create_poll():
    """
    创建投票路由
    仅主理人和管理员可以访问
    """
    user = get_current_user()
    if 'admin' not in user['roles'] and 'manager' not in user['roles']:
        return render_template('error.html', user=user, error='权限不足，仅主理人和管理员可创建投票')
    
    data = load_data()
    error = None
    success = None
    
    if request.method == 'POST':
        topic = request.form.get('topic', '').strip()
        positive_side = request.form.get('positive_side', '').strip()
        negative_side = request.form.get('negative_side', '').strip()
        voters = request.form.getlist('voters')
        
        if not topic:
            error = '请输入辩题'
        elif not positive_side:
            error = '请输入正方选手'
        elif not negative_side:
            error = '请输入反方选手'
        elif not voters:
            error = '请至少指定一个投票人'
        else:
            polls = data.get('polls', [])
            poll_id = f"P{len(polls) + 1:03d}"
            
            new_poll = {
                'id': poll_id,
                'topic': topic,
                'positive_side': positive_side,
                'negative_side': negative_side,
                'voters': voters,
                'votes': {},
                'status': 'active',
                'created_by': user['username'],
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M')
            }
            
            polls.append(new_poll)
            data['polls'] = polls
            save_data(data)
            success = f'投票创建成功，编号：{poll_id}'
    
    # 获取所有用户列表供选择
    all_users = data.get('users', [])
    
    return render_template('create_poll.html', user=user, error=error, success=success, all_users=all_users)


@app.route('/vote/submit', methods=['POST'])
@login_required
def submit_vote():
    """
    提交投票路由
    """
    data = load_data()
    user = get_current_user()
    poll_id = request.form.get('poll_id')
    vote = request.form.get('vote')
    
    if not poll_id or not vote:
        return redirect(url_for('vote_page', error='投票数据不完整'))
    
    polls = data.get('polls', [])
    poll_found = False
    
    for poll in polls:
        if poll['id'] == poll_id:
            poll_found = True
            
            # 检查投票状态
            if poll['status'] != 'active':
                return redirect(url_for('vote_page', error='该投票已结束'))
            
            # 检查用户是否有投票权限
            if user['username'] not in poll.get('voters', []):
                return redirect(url_for('vote_page', error='您没有该投票的权限'))
            
            # 检查是否已投票
            if user['username'] in poll.get('votes', {}):
                return redirect(url_for('vote_page', error='您已经投过票了'))
            
            # 记录投票
            poll['votes'][user['username']] = vote
            
            # 检查是否所有投票人都已投票
            all_voters = set(poll.get('voters', []))
            voted_users = set(poll.get('votes', {}).keys())
            
            if all_voters == voted_users:
                # 所有人已投票，计算结果并发布
                positive_votes = 0
                negative_votes = 0
                
                for voter_username, vote_option in poll['votes'].items():
                    # 查找投票人身份
                    voter_weight = 1  # 默认player权重为1
                    for u in data['users']:
                        if u['username'] == voter_username:
                            if 'guest' in u.get('roles', []):
                                voter_weight = 100  # guest权重为100
                            break
                    
                    if vote_option == 'positive':
                        positive_votes += voter_weight
                    else:
                        negative_votes += voter_weight
                
                if positive_votes > negative_votes:
                    winner = '正方'
                elif negative_votes > positive_votes:
                    winner = '反方'
                else:
                    winner = '平局'
                
                poll['results'] = {
                    'positive_votes': positive_votes,
                    'negative_votes': negative_votes,
                    'winner': winner
                }
                poll['status'] = 'completed'
                poll['completed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M')
            
            break
    
    if not poll_found:
        return redirect(url_for('vote_page', error='投票不存在'))
    
    save_data(data)
    return redirect(url_for('vote_page'))


@app.route('/vote/delete/<poll_id>', methods=['POST'])
@login_required
def delete_poll(poll_id):
    """
    删除投票路由
    仅主理人、管理员和嘉宾可以访问
    """
    user = get_current_user()
    if 'admin' not in user['roles'] and 'manager' not in user['roles'] and 'guest' not in user['roles']:
        return redirect(url_for('vote_page', error='权限不足'))
    
    data = load_data()
    polls = data.get('polls', [])
    
    # 查找并删除投票
    new_polls = [p for p in polls if p['id'] != poll_id]
    
    if len(new_polls) == len(polls):
        return redirect(url_for('vote_page', error='投票不存在'))
    
    data['polls'] = new_polls
    save_data(data)
    return redirect(url_for('vote_page'))


@app.route('/')
@login_required
def index():
    """
    首页路由
    显示系统首页，提供功能导航
    需要登录才能访问
    """
    user = get_current_user()
    return render_template('index.html', user=user)


@app.route('/ranking')
@login_required
def ranking():
    """
    排行榜路由
    显示各小组排名和总体排名，以及晋级四强的选手
    特殊嘉宾(is_guest=True)不参与晋级排名
    积分规则：获胜3分，平局1分，失败0分
    """
    data = load_data()
    user = get_current_user()
    
    # 计算各小组排名
    group_rankings = {}
    for group in ['A', 'B', 'C']:
        # 获取该小组的所有选手
        group_contestants = [c for c in data['contestants'] if c['group'] == group]
        
        # 初始化每个选手的统计数据
        for c in group_contestants:
            c['wins'] = 0          # 胜场数
            c['losses'] = 0        # 负场数
            c['draws'] = 0         # 平局数
            c['points'] = 0        # 积分
            c['match_count'] = 0   # 比赛场次
        
        # 遍历比赛记录，计算每个选手的统计数据
        for match in data['matches']:
            if match['group'] == group:
                for c in group_contestants:
                    if c['name'] == match['participant1']:
                        c['match_count'] += 1
                        if match.get('winner') == match['participant1']:
                            c['wins'] += 1
                            c['points'] += 3
                        elif match.get('winner') == match['participant2']:
                            c['losses'] += 1
                        else:
                            c['draws'] += 1
                            c['points'] += 1
                    elif c['name'] == match['participant2']:
                        c['match_count'] += 1
                        if match.get('winner') == match['participant2']:
                            c['wins'] += 1
                            c['points'] += 3
                        elif match.get('winner') == match['participant1']:
                            c['losses'] += 1
                        else:
                            c['draws'] += 1
                            c['points'] += 1
        
        # 按积分排序（积分优先，胜场次之）
        group_contestants.sort(key=lambda x: (x['points'], x['wins']), reverse=True)
        
        # 检查小组比赛是否全部结束（组内每个人都完成2场比赛）
        all_finished = all(c['match_count'] == 2 for c in group_contestants)
        
        # 如果比赛全部结束，添加状态
        if all_finished:
            for i, c in enumerate(group_contestants):
                if i == 0:
                    c['status'] = '晋级四强'
                elif i == 1:
                    c['status'] = '进入复活赛'
                else:
                    c['status'] = '淘汰'
        else:
            for c in group_contestants:
                c['status'] = ''
        
        group_rankings[group] = group_contestants
    
    # 计算总体排名（排除特殊嘉宾）
    all_contestants = [c for c in data['contestants'] if not c['is_guest']]
    
    # 初始化统计数据
    for c in all_contestants:
        c['wins'] = 0
        c['losses'] = 0
        c['draws'] = 0
        c['points'] = 0
        c['match_count'] = 0
    
    # 计算总体统计数据
    for match in data['matches']:
        for c in all_contestants:
            if c['name'] == match['participant1']:
                c['match_count'] += 1
                if match.get('winner') == match['participant1']:
                    c['wins'] += 1
                    c['points'] += 3
                elif match.get('winner') == match['participant2']:
                    c['losses'] += 1
                else:
                    c['draws'] += 1
                    c['points'] += 1
            elif c['name'] == match['participant2']:
                c['match_count'] += 1
                if match.get('winner') == match['participant2']:
                    c['wins'] += 1
                    c['points'] += 3
                elif match.get('winner') == match['participant1']:
                    c['losses'] += 1
                else:
                    c['draws'] += 1
                    c['points'] += 1
    
    # 计算投票结果统计数据
    polls = data.get('polls', [])
    for poll in polls:
        if poll['status'] == 'completed' and poll.get('results'):
            winner = poll['results']['winner']
            positive_side = poll['positive_side']
            negative_side = poll['negative_side']
            
            for c in all_contestants:
                if c['name'] == positive_side:
                    c['match_count'] += 1
                    if winner == '正方':
                        c['wins'] += 1
                        c['points'] += 3
                    elif winner == '反方':
                        c['losses'] += 1
                    else:
                        c['draws'] += 1
                        c['points'] += 1
                elif c['name'] == negative_side:
                    c['match_count'] += 1
                    if winner == '反方':
                        c['wins'] += 1
                        c['points'] += 3
                    elif winner == '正方':
                        c['losses'] += 1
                    else:
                        c['draws'] += 1
                        c['points'] += 1
    
    # 按积分降序排序
    all_contestants.sort(key=lambda x: (x['points'], x['wins']), reverse=True)
    
    # 计算晋级四强的选手
    # 规则：有人获胜两场就直接锁定晋级（???除外），以及复活赛第一名
    top4 = []
    matches = data.get('matches', [])
    polls = data.get('polls', [])
    
    # 查找各小组中获胜2场的选手（直接晋级）
    for group in ['A', 'B', 'C']:
        group_contestants = group_rankings[group]
        for c in group_contestants:
            if c['wins'] >= 2 and c['name'] != '???':
                if c not in top4:
                    top4.append(c)
                break
    
    # 查找复活赛获胜者
    for match in matches:
        if match.get('group') == '复活赛':
            winner_name = match.get('winner')
            for c in all_contestants:
                if c['name'] == winner_name:
                    if c not in top4:
                        top4.append(c)
                    break
    
    # 如果top4不足4人，显示虚位以待
    while len(top4) < 4:
        top4.append({'name': '虚位以待', 'group': '-', 'match_count': 0, 'wins': 0, 'draws': 0, 'losses': 0, 'points': 0, 'is_guest': False})
    
    # 渲染排行榜页面
    return render_template('ranking.html', 
                         group_rankings=group_rankings,
                         overall_ranking=all_contestants,
                         top4=top4,
                         user=user)


@app.route('/detail')
@login_required
def detail():
    """
    比赛详情路由
    显示所有比赛的详细信息（包括已完成的投票）
    """
    data = load_data()
    user = get_current_user()
    
    # 获取常规比赛记录
    matches = data.get('matches', [])
    
    # 获取已完成的投票，转换为比赛记录格式
    polls = data.get('polls', [])
    for poll in polls:
        if poll['status'] == 'completed' and poll.get('results'):
            winner_raw = poll['results']['winner']
            if winner_raw == '正方':
                winner_name = poll['positive_side']
            elif winner_raw == '反方':
                winner_name = poll['negative_side']
            elif winner_raw == '平局':
                winner_name = '平局'
            else:
                winner_name = winner_raw
            
            match_from_poll = {
                'id': poll['id'],
                'group': '投票',
                'date': poll.get('completed_at', ''),
                'time': '',
                'topic': poll['topic'],
                'participant1': poll['positive_side'],
                'score1': poll['results']['positive_votes'],
                'participant2': poll['negative_side'],
                'score2': poll['results']['negative_votes'],
                'winner': winner_name
            }
            matches.append(match_from_poll)
    
    return render_template('detail.html', matches=matches, contestants=data['contestants'], user=user)


@app.route('/admin')
@admin_required
def admin_page():
    """
    管理员页面路由
    只有主理人和管理员才能访问
    显示管理后台，可以录入和修改赛果
    """
    data = load_data()
    user = get_current_user()
    return render_template('admin.html', contestants=data['contestants'], user=user)


@app.route('/admin/add_match', methods=['POST'])
@admin_required
def add_match():
    """
    添加比赛结果路由
    只有主理人和管理员才能访问
    管理员录入新的比赛结果
    """
    data = load_data()
    
    # 从表单获取比赛信息
    match = {
        'id': f"M{len(data['matches']) + 1:03d}",  # 自动生成比赛编号，如M001、M002
        'group': request.form.get('group'),           # 小组（A/B/C）
        'participant1': request.form.get('participant1'),  # 选手1的姓名
        'participant2': request.form.get('participant2'),  # 选手2的姓名
        'score1': int(request.form.get('score1', 0)),      # 选手1的得分
        'score2': int(request.form.get('score2', 0)),      # 选手2的得分
        'winner': request.form.get('winner'),               # 获胜者姓名
        'topic': request.form.get('topic', ''),             # 辩题
        'date': request.form.get('date', datetime.now().strftime('%Y-%m-%d')),  # 比赛日期
        'time': request.form.get('time', datetime.now().strftime('%H:%M'))      # 比赛时间
    }
    
    # 将新比赛记录添加到列表
    data['matches'].append(match)
    # 保存到文件
    save_data(data)
    
    # 返回管理后台，显示成功信息
    return render_template('admin.html', contestants=data['contestants'], success='比赛结果已添加', user=get_current_user())


@app.route('/admin/delete_match/<match_id>', methods=['POST'])
@admin_required
def delete_match(match_id):
    """
    删除比赛结果路由
    只有主理人和管理员才能访问
    管理员删除指定的比赛记录
    参数：match_id - 要删除的比赛编号
    """
    data = load_data()
    # 过滤掉要删除的比赛记录
    data['matches'] = [m for m in data['matches'] if m['id'] != match_id]
    save_data(data)
    return render_template('admin.html', contestants=data['contestants'], success='比赛结果已删除', user=get_current_user())


@app.route('/api/contestants/<group>')
@login_required
def get_contestants_by_group(group):
    """
    API接口：根据小组获取选手列表
    用于前端动态加载指定小组的选手
    参数：group - 小组名称（A/B/C）
    返回：JSON格式的选手列表
    """
    data = load_data()
    contestants = [c for c in data['contestants'] if c['group'] == group]
    return jsonify(contestants)


@app.route('/history')
@login_required
def history():
    """
    往届赛果路由
    显示历届比赛的赛果记录
    """
    data = load_data()
    user = get_current_user()
    seasons = data.get('seasons', [])
    return render_template('history.html', seasons=seasons, user=user)


# 程序入口
if __name__ == '__main__':
    # 启动时先加载数据（确保data.json文件存在）
    load_data()
    # 启动Flask开发服务器
    # host='0.0.0.0'表示允许外部访问（网络部署需要）
    # port=5000表示服务器运行在5000端口
    # debug=True表示开启调试模式，代码修改后自动重启
    app.run(host='0.0.0.0', port=5000, debug=True)
