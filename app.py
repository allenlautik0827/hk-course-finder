#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
香港留学课程检索系统 - HK Course Finder
Backend: Flask + SQLite (local) / PostgreSQL (production)
"""

import sqlite3
import json
import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, g
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hk-course-finder-2026'
CORS(app)  # 允许跨域请求（支持 CloudStudio 等静态页面同步数据）

# ============================================================
# 数据库模式检测：PostgreSQL（生产）or SQLite（本地）
# ============================================================

DATABASE_URL = os.environ.get('DATABASE_URL', '')

# Render 有时返回 postgres:// 需要改成 postgresql://
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

USE_PG = bool(DATABASE_URL)

# SQLite 路径（仅本地开发使用）
DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db'))

# ============================================================
# 数据库工具函数（统一接口）
# ============================================================

def get_db():
    if 'db' not in g:
        if USE_PG:
            import psycopg2
            import psycopg2.extras
            conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
            g.db = conn
        else:
            g.db = sqlite3.connect(DB_PATH)
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA journal_mode=WAL")
            g.db.execute("PRAGMA foreign_keys=ON")
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def db_execute(query, params=None, fetchone=False, fetchall=False, lastrowid=False):
    """统一执行 SQL，兼容 SQLite 和 PostgreSQL"""
    db = get_db()
    if USE_PG:
        # PostgreSQL 使用 %s 占位符
        pg_query = query.replace('?', '%s')
        # 处理 SQLite 特有的 AUTOINCREMENT 语法（init 时不走这里）
        cur = db.cursor()
        cur.execute(pg_query, params or ())
        if fetchone:
            return cur.fetchone()
        if fetchall:
            return cur.fetchall()
        if lastrowid:
            # PostgreSQL 需要 RETURNING id
            return None  # 由调用方处理
        return cur
    else:
        cur = db.execute(query, params or ())
        if fetchone:
            return cur.fetchone()
        if fetchall:
            return cur.fetchall()
        if lastrowid:
            return cur.lastrowid
        return cur

def db_commit():
    get_db().commit()

def init_db():
    """初始化数据库表结构"""
    if USE_PG:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schools (
                id SERIAL PRIMARY KEY,
                name_cn TEXT NOT NULL,
                abbreviation TEXT NOT NULL UNIQUE,
                name_en TEXT NOT NULL,
                website TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id SERIAL PRIMARY KEY,
                course_code TEXT UNIQUE NOT NULL,
                school_id INTEGER NOT NULL,
                subject_category TEXT NOT NULL,
                course_name_cn TEXT NOT NULL,
                course_name_en TEXT NOT NULL DEFAULT '',
                teaching_mode TEXT NOT NULL,
                study_mode TEXT NOT NULL,
                study_duration_ft REAL,
                study_duration_pt REAL,
                teaching_language TEXT NOT NULL,
                academic_year TEXT NOT NULL,
                student_identity TEXT NOT NULL,
                tuition_local REAL DEFAULT 0,
                tuition_non_local REAL DEFAULT 0,
                deadline_local TEXT DEFAULT '',
                deadline_non_local TEXT DEFAULT '',
                qf_level TEXT DEFAULT '',
                qr_number TEXT DEFAULT '',
                education_requirement TEXT DEFAULT '',
                chinese_exempt INTEGER DEFAULT 0,
                chinese_dse TEXT DEFAULT '',
                chinese_gaokao TEXT DEFAULT '',
                chinese_hsk TEXT DEFAULT '',
                chinese_other TEXT DEFAULT '',
                english_exempt INTEGER DEFAULT 0,
                english_dse TEXT DEFAULT '',
                english_gaokao TEXT DEFAULT '',
                english_toefl_pbt TEXT DEFAULT '',
                english_toefl_ibt TEXT DEFAULT '',
                english_ielts TEXT DEFAULT '',
                english_cet4 TEXT DEFAULT '',
                english_other TEXT DEFAULT '',
                other_requirements TEXT DEFAULT '',
                interview_required INTEGER DEFAULT 0,
                course_description TEXT DEFAULT '',
                course_page_url TEXT DEFAULT '',
                course_brochure_url TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id SERIAL PRIMARY KEY,
                table_name TEXT NOT NULL,
                record_id INTEGER,
                record_name TEXT DEFAULT '',
                action TEXT NOT NULL,
                changes TEXT DEFAULT '{}',
                modified_by TEXT DEFAULT 'admin',
                modified_date TEXT NOT NULL,
                modified_time TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
    else:
        db = sqlite3.connect(DB_PATH)
        db.execute("PRAGMA foreign_keys=ON")
        cursor = db.cursor()
        cursor.executescript('''
            CREATE TABLE IF NOT EXISTS schools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_cn TEXT NOT NULL,
                abbreviation TEXT NOT NULL UNIQUE,
                name_en TEXT NOT NULL,
                website TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_code TEXT UNIQUE NOT NULL,
                school_id INTEGER NOT NULL,
                subject_category TEXT NOT NULL,
                course_name_cn TEXT NOT NULL,
                course_name_en TEXT NOT NULL DEFAULT '',
                teaching_mode TEXT NOT NULL,
                study_mode TEXT NOT NULL,
                study_duration_ft REAL,
                study_duration_pt REAL,
                teaching_language TEXT NOT NULL,
                academic_year TEXT NOT NULL,
                student_identity TEXT NOT NULL,
                tuition_local REAL DEFAULT 0,
                tuition_non_local REAL DEFAULT 0,
                deadline_local TEXT DEFAULT '',
                deadline_non_local TEXT DEFAULT '',
                qf_level TEXT DEFAULT '',
                qr_number TEXT DEFAULT '',
                education_requirement TEXT DEFAULT '',
                chinese_exempt INTEGER DEFAULT 0,
                chinese_dse TEXT DEFAULT '',
                chinese_gaokao TEXT DEFAULT '',
                chinese_hsk TEXT DEFAULT '',
                chinese_other TEXT DEFAULT '',
                english_exempt INTEGER DEFAULT 0,
                english_dse TEXT DEFAULT '',
                english_gaokao TEXT DEFAULT '',
                english_toefl_pbt TEXT DEFAULT '',
                english_toefl_ibt TEXT DEFAULT '',
                english_ielts TEXT DEFAULT '',
                english_cet4 TEXT DEFAULT '',
                english_other TEXT DEFAULT '',
                other_requirements TEXT DEFAULT '',
                interview_required INTEGER DEFAULT 0,
                course_description TEXT DEFAULT '',
                course_page_url TEXT DEFAULT '',
                course_brochure_url TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                record_id INTEGER,
                record_name TEXT DEFAULT '',
                action TEXT NOT NULL,
                changes TEXT DEFAULT '{}',
                modified_by TEXT DEFAULT 'admin',
                modified_date TEXT NOT NULL,
                modified_time TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        db.commit()
        db.close()

def seed_schools():
    """预置18所香港高校数据"""
    schools = [
        ('香港恒生大学', 'HSU', 'The Hang Seng University of Hong Kong', 'https://gs.hsu.edu.hk/'),
        ('香港珠海学院', 'CHC', 'Hong Kong Chu Hai College', 'https://www.chuhai.edu.hk/'),
        ('香港都会大学', 'HKMU', 'Hong Kong Metropolitan University', 'https://www.hkmu.edu.hk/'),
        ('香港理工大学', 'PolyU', 'The Hong Kong Polytechnic University', 'https://www.polyu.edu.hk/'),
        ('香港理工大学专业进修学院', 'PolySeed', 'SPEED (The Hong Kong Polytechnic University)', 'https://www.speed-polyu.edu.hk/'),
        ('香港浸会大学', 'HKBU', 'Hong Kong Baptist University', 'https://www.sci.hkbu.edu.hk/'),
        ('香港大学', 'HKU', 'The University of Hong Kong', 'https://www.hku.hk/'),
        ('香港大学专业进修学院', 'HKUSpace', 'HKU School of Professional and Continuing Education', 'https://hkuspace.hku.hk/cht'),
        ('香港科技大学', 'HKUST', 'The Hong Kong University of Science and Technology', 'https://fytgs.hkust.edu.hk/'),
        ('香港岭南大学', 'LNU', 'Lingnan University', 'https://www.ln.edu.hk/cht'),
        ('香港教育大学', 'EDU', 'The Education University of Hong Kong', 'https://www.eduhk.hk/en/'),
        ('香港城市大学', 'CityU', 'City University of Hong Kong', 'https://www.cityu.edu.hk/zh-hk'),
        ('香港中文大学', 'CUHK', 'The Chinese University of Hong Kong', 'https://www.cuhk.edu.hk/chinese/'),
        ('香港树人大学', 'HKSYU', 'Hong Kong Shue Yan University', 'https://www.hksyu.edu/tc/home'),
        ('香港伍伦贡学院', 'UOWC', 'Hong Kong UOW College', 'https://www.uowchk.edu.hk/'),
        ('圣方济各大学', 'SFU', 'Saint Francis University', 'https://www.sfu.edu.hk/tc/home/index.html'),
        ('东华学院', 'TWC', 'Tung Wah College', 'https://www.twc.edu.hk/tc/'),
        ('香港演艺学院', 'HKAPA', 'The Hong Kong Academy for Performing Arts', 'https://www.hkapa.edu/tch'),
    ]

    if USE_PG:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM schools")
        count = cur.fetchone()[0]
        if count == 0:
            cur.executemany(
                "INSERT INTO schools (name_cn, abbreviation, name_en, website) VALUES (%s, %s, %s, %s) ON CONFLICT (abbreviation) DO NOTHING",
                schools
            )
            conn.commit()
        conn.close()
    else:
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM schools")
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.executemany(
                "INSERT INTO schools (name_cn, abbreviation, name_en, website) VALUES (?, ?, ?, ?)",
                schools
            )
            db.commit()
        db.close()

def db_row_to_dict(row):
    """将数据库行转换为字典（兼容 SQLite Row 和 psycopg2 RealDictRow）"""
    if row is None:
        return None
    if isinstance(row, dict):
        return dict(row)
    return dict(row)

def log_audit(table_name, record_id, record_name, action, changes, modified_by='admin'):
    """记录审计日志"""
    now = datetime.now()
    db = get_db()
    q = """INSERT INTO audit_log (table_name, record_id, record_name, action, changes, modified_by, modified_date, modified_time)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
    p = (table_name, record_id, record_name, action, json.dumps(changes, ensure_ascii=False),
         modified_by, now.strftime('%Y-%m-%d'), now.strftime('%H:%M:%S'))
    if USE_PG:
        cur = db.cursor()
        cur.execute(q.replace('?', '%s'), p)
    else:
        db.execute(q, p)
    db.commit()

# ============================================================
# 通用 SQL 执行助手（兼容 SQLite 和 PostgreSQL）
# ============================================================

def sql(query, params=None):
    """执行 SQL 并返回 cursor，自动将 ? 转为 %s（PostgreSQL）"""
    db = get_db()
    p = params or ()
    if USE_PG:
        cur = db.cursor()
        cur.execute(query.replace('?', '%s'), p)
        return cur
    else:
        return db.execute(query, p)

def sql_one(query, params=None):
    """执行 SQL，返回第一行（字典）"""
    row = sql(query, params).fetchone()
    if row is None:
        return None
    return dict(row)

def sql_all(query, params=None):
    """执行 SQL，返回所有行（字典列表）"""
    rows = sql(query, params).fetchall()
    return [dict(r) for r in rows]

def sql_insert(query, params=None):
    """执行 INSERT，返回新行 id（兼容两种数据库）"""
    db = get_db()
    p = params or ()
    if USE_PG:
        # 附加 RETURNING id
        pg_query = query.replace('?', '%s')
        if 'RETURNING' not in pg_query.upper():
            pg_query += ' RETURNING id'
        cur = db.cursor()
        cur.execute(pg_query, p)
        row = cur.fetchone()
        if row is None:
            return None
        # RealDictCursor returns a dict-like row: access by key
        if isinstance(row, dict):
            return row['id']
        # Fallback for regular cursor (tuple-like)
        return row[0]
    else:
        cur = db.execute(query, p)
        return cur.lastrowid

def sql_commit():
    get_db().commit()

def db_row_to_dict(row):
    """将数据库行转换为字典（兼容 SQLite Row 和 psycopg2 RealDictRow）"""
    if row is None:
        return None
    return dict(row)

def log_audit(table_name, record_id, record_name, action, changes, modified_by='admin'):
    """记录审计日志"""
    now = datetime.now()
    # Safely serialize changes (handle datetime, Decimal, etc.)
    def default_serializer(obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        return str(obj)
    try:
        changes_json = json.dumps(changes, ensure_ascii=False, default=default_serializer)
    except Exception:
        changes_json = '{}'
    try:
        sql("""INSERT INTO audit_log (table_name, record_id, record_name, action, changes, modified_by, modified_date, modified_time)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (table_name, record_id, record_name, action, changes_json,
             modified_by, now.strftime('%Y-%m-%d'), now.strftime('%H:%M:%S')))
        sql_commit()
    except Exception as e:
        app.logger.warning(f"log_audit failed (non-critical): {e}")

# ============================================================
# 页面路由
# ============================================================

@app.route('/')
def index():
    return render_template('index.html')

# ============================================================
# 学校 API
# ============================================================

@app.route('/api/schools', methods=['GET'])
def get_schools():
    """获取所有学校列表（含课程数量统计）"""
    schools = sql_all("""
        SELECT s.*,
               (SELECT COUNT(*) FROM courses c WHERE c.school_id = s.id AND c.teaching_mode = '授课式') as taught_count,
               (SELECT COUNT(*) FROM courses c WHERE c.school_id = s.id AND c.teaching_mode = '研究式') as research_count
        FROM schools s
        ORDER BY s.id
    """)
    result = []
    for s in schools:
        result.append({
            'id': s['id'],
            'name_cn': s['name_cn'],
            'abbreviation': s['abbreviation'],
            'name_en': s['name_en'],
            'website': s['website'],
            'taught_count': s['taught_count'],
            'research_count': s['research_count'],
            'created_at': str(s['created_at']),
        })
    return jsonify(result)

@app.route('/api/schools/<int:school_id>', methods=['GET'])
def get_school(school_id):
    school = sql_one("SELECT * FROM schools WHERE id = ?", (school_id,))
    if not school:
        return jsonify({'error': '学校不存在'}), 404
    school['created_at'] = str(school['created_at'])
    return jsonify(school)

@app.route('/api/schools', methods=['POST'])
def add_school():
    """添加学校"""
    data = request.json
    try:
        school_id = sql_insert(
            "INSERT INTO schools (name_cn, abbreviation, name_en, website) VALUES (?, ?, ?, ?)",
            (data['name_cn'], data['abbreviation'], data['name_en'], data.get('website', ''))
        )
        sql_commit()
        log_audit('schools', school_id, data['name_cn'], 'CREATE',
                  {'name_cn': data['name_cn'], 'abbreviation': data['abbreviation'],
                   'name_en': data['name_en'], 'website': data.get('website', '')})
        return jsonify({'id': school_id, 'message': '学校添加成功'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/schools/<int:school_id>', methods=['PUT'])
def update_school(school_id):
    """修改学校"""
    data = request.json
    old = sql_one("SELECT * FROM schools WHERE id = ?", (school_id,))
    if not old:
        return jsonify({'error': '学校不存在'}), 404

    changes = {}
    for field in ['name_cn', 'abbreviation', 'name_en', 'website']:
        if field in data and str(data[field]) != str(old[field]):
            changes[field] = {'old': old[field], 'new': data[field]}

    sql("UPDATE schools SET name_cn=?, abbreviation=?, name_en=?, website=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (data.get('name_cn', old['name_cn']),
         data.get('abbreviation', old['abbreviation']),
         data.get('name_en', old['name_en']),
         data.get('website', old['website']),
         school_id))
    sql_commit()
    log_audit('schools', school_id, old['name_cn'], 'UPDATE', changes, data.get('modified_by', 'admin'))
    return jsonify({'message': '学校修改成功'})

@app.route('/api/schools/<int:school_id>', methods=['DELETE'])
def delete_school(school_id):
    """删除学校"""
    old = sql_one("SELECT * FROM schools WHERE id = ?", (school_id,))
    if not old:
        return jsonify({'error': '学校不存在'}), 404

    sql("DELETE FROM schools WHERE id = ?", (school_id,))
    sql_commit()
    log_audit('schools', school_id, old['name_cn'], 'DELETE', old)
    return jsonify({'message': '学校删除成功'})

# ============================================================
# 课程 API
# ============================================================

def format_course(c):
    """格式化课程数据（含展示字段）"""
    # 格式化修读时间
    study_mode = c.get('study_mode', '')
    ft = c.get('study_duration_ft')
    pt = c.get('study_duration_pt')
    if study_mode in ('全日制/兼读制', '全日制/非全日制'):
        ft_str = f"{ft}年" if ft else '-'
        pt_str = f"{pt}年" if pt else '-'
        study_duration = f"{ft_str}<br>{pt_str}"
    elif study_mode == '全日制':
        study_duration = f"{ft}年" if ft else '-'
    else:
        study_duration = f"{pt}年" if pt else '-'

    # 格式化学费
    tl_val = c.get('tuition_local') or 0
    tn_val = c.get('tuition_non_local') or 0
    tl = f"HKD{int(tl_val):,}" if tl_val else None
    tn = f"HKD{int(tn_val):,}" if tn_val else None
    if tl and tn and tl != tn:
        tuition = f"{tl}（本地生）<br>{tn}（非本地生）"
    elif tl:
        tuition = tl
    elif tn:
        tuition = tn
    else:
        tuition = '—'

    # 格式化截止日期
    dl = c.get('deadline_local') or ''
    dn = c.get('deadline_non_local') or ''
    if dl and dn and dl != dn:
        deadline = f"{dl}（本地生）<br>{dn}（非本地生）"
    elif dl:
        deadline = f"{dl}（本地生）"
    elif dn:
        deadline = f"{dn}（非本地生）"
    else:
        deadline = '—'

    return {
        'id': c['id'],
        'course_code': c['course_code'],
        'school_id': c['school_id'],
        'school_abbr': c.get('school_abbr', ''),
        'school_name_cn': c.get('school_name_cn', ''),
        'school_name_en': c.get('school_name_en', ''),
        'subject_category': c['subject_category'],
        'course_name_cn': c['course_name_cn'],
        'course_name_en': c.get('course_name_en', ''),
        'teaching_mode': c['teaching_mode'],
        'study_mode': study_mode,
        'study_duration_ft': ft,
        'study_duration_pt': pt,
        'study_duration_display': study_duration,
        'teaching_language': c['teaching_language'],
        'academic_year': c['academic_year'],
        'student_identity': c['student_identity'],
        'tuition_local': tl_val,
        'tuition_non_local': tn_val,
        'tuition_display': tuition,
        'deadline_local': dl,
        'deadline_non_local': dn,
        'deadline_display': deadline,
        'qf_level': c.get('qf_level', ''),
        'qr_number': c.get('qr_number', ''),
        'education_requirement': c.get('education_requirement', ''),
        'chinese_exempt': bool(c.get('chinese_exempt')),
        'chinese_dse': c.get('chinese_dse', ''),
        'chinese_gaokao': c.get('chinese_gaokao', ''),
        'chinese_hsk': c.get('chinese_hsk', ''),
        'chinese_other': c.get('chinese_other', ''),
        'english_exempt': bool(c.get('english_exempt')),
        'english_dse': c.get('english_dse', ''),
        'english_gaokao': c.get('english_gaokao', ''),
        'english_toefl_pbt': c.get('english_toefl_pbt', ''),
        'english_toefl_ibt': c.get('english_toefl_ibt', ''),
        'english_ielts': c.get('english_ielts', ''),
        'english_cet4': c.get('english_cet4', ''),
        'english_other': c.get('english_other', ''),
        'other_requirements': c.get('other_requirements', ''),
        'interview_required': bool(c.get('interview_required')),
        'course_description': c.get('course_description', ''),
        'course_page_url': c.get('course_page_url', ''),
        'course_brochure_url': c.get('course_brochure_url', ''),
        'created_at': str(c.get('created_at', '')),
    }

@app.route('/api/courses', methods=['GET'])
def get_courses():
    """获取课程列表（支持多维度筛选）"""
    query = """
        SELECT c.*, s.abbreviation as school_abbr, s.name_cn as school_name_cn, s.name_en as school_name_en
        FROM courses c
        JOIN schools s ON c.school_id = s.id
        WHERE 1=1
    """
    params = []

    if request.args.get('course_code'):
        query += " AND c.course_code LIKE ?"
        params.append(f"%{request.args['course_code']}%")

    if request.args.get('school_id'):
        query += " AND c.school_id = ?"
        params.append(int(request.args['school_id']))

    if request.args.get('subject_category'):
        query += " AND c.subject_category = ?"
        params.append(request.args['subject_category'])

    if request.args.get('teaching_mode'):
        query += " AND c.teaching_mode = ?"
        params.append(request.args['teaching_mode'])

    if request.args.get('course_name'):
        query += " AND (c.course_name_cn LIKE ? OR c.course_name_en LIKE ?)"
        kw = f"%{request.args['course_name']}%"
        params.extend([kw, kw])

    if request.args.get('study_mode'):
        query += " AND c.study_mode = ?"
        params.append(request.args['study_mode'])

    if request.args.get('study_duration'):
        query += " AND (c.study_duration_ft = ? OR c.study_duration_pt = ?)"
        dur = float(request.args['study_duration'])
        params.extend([dur, dur])

    if request.args.get('academic_year'):
        query += " AND c.academic_year = ?"
        params.append(request.args['academic_year'])

    if request.args.get('student_identity'):
        query += " AND c.student_identity = ?"
        params.append(request.args['student_identity'])

    if request.args.get('tuition_min'):
        query += " AND (c.tuition_non_local >= ? OR c.tuition_local >= ?)"
        tmin = float(request.args['tuition_min'])
        params.extend([tmin, tmin])

    if request.args.get('tuition_max'):
        query += " AND (c.tuition_non_local <= ? OR c.tuition_local <= ?)"
        tmax = float(request.args['tuition_max'])
        params.extend([tmax, tmax])

    if request.args.get('deadline_sort'):
        if request.args['deadline_sort'] == 'asc':
            if USE_PG:
                query += " ORDER BY NULLIF(c.deadline_non_local, '') ASC NULLS LAST"
            else:
                query += " ORDER BY CASE WHEN c.deadline_non_local = '' THEN '9999-99-99' ELSE c.deadline_non_local END ASC"
        elif request.args['deadline_sort'] == 'desc':
            if USE_PG:
                query += " ORDER BY NULLIF(c.deadline_non_local, '') DESC NULLS LAST"
            else:
                query += " ORDER BY CASE WHEN c.deadline_non_local = '' THEN '0000-00-00' ELSE c.deadline_non_local END DESC"
    else:
        query += " ORDER BY c.id DESC"

    courses = sql_all(query, params)
    return jsonify([format_course(c) for c in courses])

@app.route('/api/courses/<int:course_id>', methods=['GET'])
def get_course(course_id):
    """获取单个课程详情"""
    course = sql_one("""
        SELECT c.*, s.abbreviation as school_abbr, s.name_cn as school_name_cn,
               s.name_en as school_name_en, s.website as school_website
        FROM courses c
        JOIN schools s ON c.school_id = s.id
        WHERE c.id = ?
    """, (course_id,))
    if not course:
        return jsonify({'error': '课程不存在'}), 404
    course['chinese_exempt'] = bool(course['chinese_exempt'])
    course['english_exempt'] = bool(course['english_exempt'])
    course['interview_required'] = bool(course['interview_required'])
    course['created_at'] = str(course.get('created_at', ''))
    return jsonify(course)

@app.route('/api/courses', methods=['POST'])
def add_course():
    """添加课程"""
    data = request.json

    last = sql_one("SELECT course_code FROM courses ORDER BY id DESC LIMIT 1")
    if last and last.get('course_code'):
        try:
            last_num = int(last['course_code'].replace('HK-', ''))
        except ValueError:
            last_num = 0
        new_code = f"HK-{last_num + 1:04d}"
    else:
        new_code = "HK-0001"

    try:
        course_id = sql_insert("""
            INSERT INTO courses (
                course_code, school_id, subject_category, course_name_cn, course_name_en,
                teaching_mode, study_mode, study_duration_ft, study_duration_pt,
                teaching_language, academic_year, student_identity,
                tuition_local, tuition_non_local, deadline_local, deadline_non_local,
                qf_level, qr_number, education_requirement,
                chinese_exempt, chinese_dse, chinese_gaokao, chinese_hsk, chinese_other,
                english_exempt, english_dse, english_gaokao, english_toefl_pbt,
                english_toefl_ibt, english_ielts, english_cet4, english_other,
                other_requirements, interview_required,
                course_description, course_page_url, course_brochure_url
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            new_code,
            data['school_id'], data['subject_category'], data['course_name_cn'], data.get('course_name_en', ''),
            data['teaching_mode'], data['study_mode'],
            data.get('study_duration_ft'), data.get('study_duration_pt'),
            data['teaching_language'], data['academic_year'], data['student_identity'],
            data.get('tuition_local', 0), data.get('tuition_non_local', 0),
            data.get('deadline_local', ''), data.get('deadline_non_local', ''),
            data.get('qf_level', ''), data.get('qr_number', ''),
            data.get('education_requirement', ''),
            1 if data.get('chinese_exempt') else 0,
            data.get('chinese_dse', ''), data.get('chinese_gaokao', ''), data.get('chinese_hsk', ''), data.get('chinese_other', ''),
            1 if data.get('english_exempt') else 0,
            data.get('english_dse', ''), data.get('english_gaokao', ''),
            data.get('english_toefl_pbt', ''), data.get('english_toefl_ibt', ''),
            data.get('english_ielts', ''), data.get('english_cet4', ''), data.get('english_other', ''),
            data.get('other_requirements', ''),
            1 if data.get('interview_required') else 0,
            data.get('course_description', ''), data.get('course_page_url', ''), data.get('course_brochure_url', '')
        ))
        sql_commit()
        changes = {k: v for k, v in data.items() if v}
        changes['course_code'] = new_code
        log_audit('courses', course_id, f"{data['course_name_cn']} ({new_code})", 'CREATE', changes,
                  data.get('modified_by', 'admin'))
        return jsonify({'id': course_id, 'course_code': new_code, 'message': '课程添加成功'}), 201
    except Exception as e:
        import traceback
        app.logger.error(f"add_course error: {traceback.format_exc()}")
        return jsonify({'error': str(e) or repr(e)}), 400


@app.route('/api/courses/batch', methods=['POST'])
def batch_sync_courses():
    """批量同步课程（用于 localStorage 版本向服务器同步数据）"""
    data = request.json
    courses = data.get('courses', [])
    modified_by = data.get('modified_by', 'sync')
    if not courses:
        return jsonify({'error': '没有课程数据'}), 400

    results = {'success': 0, 'skipped': 0, 'failed': 0, 'errors': []}

    last_code_row = sql_one("SELECT course_code FROM courses ORDER BY id DESC LIMIT 1")
    if last_code_row and last_code_row.get('course_code'):
        try:
            last_num = int(last_code_row['course_code'].replace('HK-', ''))
        except ValueError:
            last_num = 0
    else:
        last_num = 0

    for idx, course in enumerate(courses):
        try:
            school_id = int(course.get('school_id', 0))
            if not school_id:
                results['failed'] += 1
                results['errors'].append(f"第{idx+1}行: 缺少 school_id")
                continue

            school = sql_one("SELECT id FROM schools WHERE id = ?", (school_id,))
            if not school:
                results['failed'] += 1
                results['errors'].append(f"第{idx+1}行: school_id={school_id} 不存在")
                continue

            existing = sql_one(
                "SELECT id FROM courses WHERE course_name_cn = ? AND school_id = ?",
                (course.get('course_name_cn', ''), school_id)
            )
            if existing:
                results['skipped'] += 1
                continue

            last_num += 1
            new_code = f"HK-{last_num:04d}"

            def get_str(field):
                v = course.get(field, '')
                return str(v) if v is not None else ''

            def get_num(field):
                v = course.get(field)
                if v is None or v == '':
                    return 0
                try:
                    return float(str(v).replace(',', ''))
                except (ValueError, TypeError):
                    return 0

            def get_num_nullable(field):
                v = course.get(field)
                if v is None or v == '':
                    return None
                try:
                    return float(str(v).replace(',', ''))
                except (ValueError, TypeError):
                    return None

            def get_bool(field):
                v = course.get(field)
                if isinstance(v, bool):
                    return 1 if v else 0
                if isinstance(v, (int, float)):
                    return 1 if v else 0
                if isinstance(v, str):
                    return 1 if v.lower() in ('1', 'true', 'yes', '是') else 0
                return 0

            course_id = sql_insert("""
                INSERT INTO courses (
                    course_code, school_id, subject_category, course_name_cn, course_name_en,
                    teaching_mode, study_mode, study_duration_ft, study_duration_pt,
                    teaching_language, academic_year, student_identity,
                    tuition_local, tuition_non_local, deadline_local, deadline_non_local,
                    qf_level, qr_number, education_requirement,
                    chinese_exempt, chinese_dse, chinese_gaokao, chinese_hsk, chinese_other,
                    english_exempt, english_dse, english_gaokao, english_toefl_pbt,
                    english_toefl_ibt, english_ielts, english_cet4, english_other,
                    other_requirements, interview_required,
                    course_description, course_page_url, course_brochure_url
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                new_code, school_id,
                get_str('subject_category'), get_str('course_name_cn'), get_str('course_name_en'),
                get_str('teaching_mode'), get_str('study_mode'),
                get_num_nullable('study_duration_ft'), get_num_nullable('study_duration_pt'),
                get_str('teaching_language'), get_str('academic_year'), get_str('student_identity'),
                get_num('tuition_local'), get_num('tuition_non_local'),
                get_str('deadline_local'), get_str('deadline_non_local'),
                get_str('qf_level'), get_str('qr_number'), get_str('education_requirement'),
                get_bool('chinese_exempt'), get_str('chinese_dse'), get_str('chinese_gaokao'),
                get_str('chinese_hsk'), get_str('chinese_other'),
                get_bool('english_exempt'), get_str('english_dse'), get_str('english_gaokao'),
                get_str('english_toefl_pbt'), get_str('english_toefl_ibt'),
                get_str('english_ielts'), get_str('english_cet4'), get_str('english_other'),
                get_str('other_requirements'), get_bool('interview_required'),
                get_str('course_description'), get_str('course_page_url'), get_str('course_brochure_url')
            ))
            sql_commit()

            log_audit('courses', course_id,
                      f"{course.get('course_name_cn', '')} ({new_code})",
                      'BATCH_SYNC',
                      {'sync_source': 'localStorage', 'course_name': course.get('course_name_cn', '')},
                      modified_by)
            results['success'] += 1

        except Exception as e:
            results['failed'] += 1
            results['errors'].append(f"第{idx+1}行: {str(e)}")

    results['message'] = f"同步完成：成功 {results['success']} 条，跳过 {results['skipped']} 条，失败 {results['failed']} 条"
    return jsonify(results), 200


@app.route('/api/courses/<int:course_id>', methods=['PUT'])
def update_course(course_id):
    """修改课程"""
    data = request.json
    old = sql_one("SELECT * FROM courses WHERE id = ?", (course_id,))
    if not old:
        return jsonify({'error': '课程不存在'}), 404

    field_map = {
        'school_id', 'subject_category', 'course_name_cn', 'course_name_en',
        'teaching_mode', 'study_mode', 'study_duration_ft', 'study_duration_pt',
        'teaching_language', 'academic_year', 'student_identity',
        'tuition_local', 'tuition_non_local', 'deadline_local', 'deadline_non_local',
        'qf_level', 'qr_number', 'education_requirement',
        'chinese_dse', 'chinese_gaokao', 'chinese_hsk', 'chinese_other',
        'english_dse', 'english_gaokao', 'english_toefl_pbt', 'english_toefl_ibt',
        'english_ielts', 'english_cet4', 'english_other', 'other_requirements',
        'course_description', 'course_page_url', 'course_brochure_url',
    }

    changes = {}
    for key in field_map:
        if key in data:
            old_val = str(old[key]) if old[key] is not None else ''
            new_val = str(data[key]) if data[key] is not None else ''
            if old_val != new_val:
                changes[key] = {'old': old[key], 'new': data[key]}

    for bool_field in ['chinese_exempt', 'english_exempt', 'interview_required']:
        if bool_field in data:
            old_val = bool(old[bool_field])
            new_val = bool(data[bool_field])
            if old_val != new_val:
                changes[bool_field] = {'old': old_val, 'new': new_val}

    def gv(field):
        return data.get(field, old[field])

    sql("""
        UPDATE courses SET
            school_id=?, subject_category=?, course_name_cn=?, course_name_en=?,
            teaching_mode=?, study_mode=?, study_duration_ft=?, study_duration_pt=?,
            teaching_language=?, academic_year=?, student_identity=?,
            tuition_local=?, tuition_non_local=?, deadline_local=?, deadline_non_local=?,
            qf_level=?, qr_number=?, education_requirement=?,
            chinese_exempt=?, chinese_dse=?, chinese_gaokao=?, chinese_hsk=?, chinese_other=?,
            english_exempt=?, english_dse=?, english_gaokao=?, english_toefl_pbt=?,
            english_toefl_ibt=?, english_ielts=?, english_cet4=?, english_other=?,
            other_requirements=?, interview_required=?,
            course_description=?, course_page_url=?, course_brochure_url=?,
            updated_at=CURRENT_TIMESTAMP
        WHERE id=?
    """, (
        gv('school_id'), gv('subject_category'), gv('course_name_cn'), gv('course_name_en'),
        gv('teaching_mode'), gv('study_mode'), gv('study_duration_ft'), gv('study_duration_pt'),
        gv('teaching_language'), gv('academic_year'), gv('student_identity'),
        gv('tuition_local'), gv('tuition_non_local'), gv('deadline_local'), gv('deadline_non_local'),
        gv('qf_level'), gv('qr_number'), gv('education_requirement'),
        1 if data.get('chinese_exempt', old['chinese_exempt']) else 0,
        gv('chinese_dse'), gv('chinese_gaokao'), gv('chinese_hsk'), gv('chinese_other'),
        1 if data.get('english_exempt', old['english_exempt']) else 0,
        gv('english_dse'), gv('english_gaokao'), gv('english_toefl_pbt'),
        gv('english_toefl_ibt'), gv('english_ielts'), gv('english_cet4'), gv('english_other'),
        gv('other_requirements'), 1 if data.get('interview_required', old['interview_required']) else 0,
        gv('course_description'), gv('course_page_url'), gv('course_brochure_url'),
        course_id
    ))
    sql_commit()
    log_audit('courses', course_id, f"{old['course_name_cn']} ({old['course_code']})", 'UPDATE', changes,
              data.get('modified_by', 'admin'))
    return jsonify({'message': '课程修改成功'})

@app.route('/api/courses/<int:course_id>', methods=['DELETE'])
def delete_course(course_id):
    """删除课程"""
    old = sql_one("SELECT * FROM courses WHERE id = ?", (course_id,))
    if not old:
        return jsonify({'error': '课程不存在'}), 404

    sql("DELETE FROM courses WHERE id = ?", (course_id,))
    sql_commit()
    log_audit('courses', course_id, f"{old['course_name_cn']} ({old['course_code']})", 'DELETE', old)
    return jsonify({'message': '课程删除成功'})

# ============================================================
# 审计日志 API
# ============================================================

@app.route('/api/audit-log', methods=['GET'])
def get_audit_log():
    """获取审计日志"""
    limit = request.args.get('limit', 100, type=int)
    table = request.args.get('table', '')
    query = "SELECT * FROM audit_log"
    params = []
    if table:
        query += " WHERE table_name = ?"
        params.append(table)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    logs = sql_all(query, params)
    result = []
    for log in logs:
        result.append({
            'id': log['id'],
            'table_name': log['table_name'],
            'record_id': log['record_id'],
            'record_name': log['record_name'],
            'action': log['action'],
            'changes': json.loads(log['changes']) if log['changes'] else {},
            'modified_by': log['modified_by'],
            'modified_date': log['modified_date'],
            'modified_time': log['modified_time'],
        })
    return jsonify(result)

# ============================================================
# 数据库初始化（模块级别，确保 gunicorn 也能执行）
# ============================================================
init_db()
seed_schools()

# ============================================================
# 应用入口
# ============================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    print("=" * 60)
    print("  香港留学课程检索系统 - HK Course Finder")
    print(f"  数据库模式: {'PostgreSQL' if USE_PG else 'SQLite'}")
    print(f"  访问地址: http://{host}:{port}")
    print("=" * 60)
    app.run(host=host, port=port, debug=False)
