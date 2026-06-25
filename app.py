#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
香港留学课程检索系统 - HK Course Finder
Backend: Flask + SQLite
"""

import sqlite3
import json
import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, g

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hk-course-finder-2026'

# 数据库路径
DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db'))

# ============================================================
# 数据库工具函数
# ============================================================

def get_db():
    if 'db' not in g:
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

def init_db():
    """初始化数据库表结构"""
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

def log_audit(table_name, record_id, record_name, action, changes, modified_by='admin'):
    """记录审计日志"""
    now = datetime.now()
    db = get_db()
    db.execute(
        """INSERT INTO audit_log (table_name, record_id, record_name, action, changes, modified_by, modified_date, modified_time)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (table_name, record_id, record_name, action, json.dumps(changes, ensure_ascii=False),
         modified_by, now.strftime('%Y-%m-%d'), now.strftime('%H:%M:%S'))
    )
    db.commit()

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
    db = get_db()
    schools = db.execute("""
        SELECT s.*,
               (SELECT COUNT(*) FROM courses c WHERE c.school_id = s.id AND c.teaching_mode = '授课式') as taught_count,
               (SELECT COUNT(*) FROM courses c WHERE c.school_id = s.id AND c.teaching_mode = '研究式') as research_count
        FROM schools s
        ORDER BY s.id
    """).fetchall()
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
            'created_at': s['created_at'],
        })
    return jsonify(result)

@app.route('/api/schools/<int:school_id>', methods=['GET'])
def get_school(school_id):
    db = get_db()
    school = db.execute("SELECT * FROM schools WHERE id = ?", (school_id,)).fetchone()
    if not school:
        return jsonify({'error': '学校不存在'}), 404
    return jsonify(dict(school))

@app.route('/api/schools', methods=['POST'])
def add_school():
    """添加学校"""
    data = request.json
    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO schools (name_cn, abbreviation, name_en, website) VALUES (?, ?, ?, ?)",
            (data['name_cn'], data['abbreviation'], data['name_en'], data.get('website', ''))
        )
        db.commit()
        school_id = cursor.lastrowid
        log_audit('schools', school_id, data['name_cn'], 'CREATE',
                  {'name_cn': data['name_cn'], 'abbreviation': data['abbreviation'],
                   'name_en': data['name_en'], 'website': data.get('website', '')})
        return jsonify({'id': school_id, 'message': '学校添加成功'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': '学校简称已存在'}), 400

@app.route('/api/schools/<int:school_id>', methods=['PUT'])
def update_school(school_id):
    """修改学校"""
    data = request.json
    db = get_db()
    old = db.execute("SELECT * FROM schools WHERE id = ?", (school_id,)).fetchone()
    if not old:
        return jsonify({'error': '学校不存在'}), 404

    changes = {}
    for field in ['name_cn', 'abbreviation', 'name_en', 'website']:
        if field in data and str(data[field]) != str(old[field]):
            changes[field] = {'old': old[field], 'new': data[field]}

    db.execute(
        "UPDATE schools SET name_cn=?, abbreviation=?, name_en=?, website=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (data.get('name_cn', old['name_cn']),
         data.get('abbreviation', old['abbreviation']),
         data.get('name_en', old['name_en']),
         data.get('website', old['website']),
         school_id)
    )
    db.commit()
    log_audit('schools', school_id, old['name_cn'], 'UPDATE', changes, data.get('modified_by', 'admin'))
    return jsonify({'message': '学校修改成功'})

@app.route('/api/schools/<int:school_id>', methods=['DELETE'])
def delete_school(school_id):
    """删除学校"""
    db = get_db()
    old = db.execute("SELECT * FROM schools WHERE id = ?", (school_id,)).fetchone()
    if not old:
        return jsonify({'error': '学校不存在'}), 404

    # 记录删除前的数据
    old_data = dict(old)
    db.execute("DELETE FROM schools WHERE id = ?", (school_id,))
    db.commit()
    log_audit('schools', school_id, old_data['name_cn'], 'DELETE', old_data)
    return jsonify({'message': '学校删除成功'})

# ============================================================
# 课程 API
# ============================================================

@app.route('/api/courses', methods=['GET'])
def get_courses():
    """获取课程列表（支持多维度筛选）"""
    db = get_db()

    query = """
        SELECT c.*, s.abbreviation as school_abbr, s.name_cn as school_name_cn, s.name_en as school_name_en
        FROM courses c
        JOIN schools s ON c.school_id = s.id
        WHERE 1=1
    """
    params = []

    # 筛选维度
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

    # 截止日期排序
    if request.args.get('deadline_sort'):
        if request.args['deadline_sort'] == 'asc':
            query += " ORDER BY CASE WHEN c.deadline_non_local = '' THEN '9999-99-99' ELSE c.deadline_non_local END ASC"
        elif request.args['deadline_sort'] == 'desc':
            query += " ORDER BY CASE WHEN c.deadline_non_local = '' THEN '0000-00-00' ELSE c.deadline_non_local END DESC"
    else:
        query += " ORDER BY c.id DESC"

    cursor = db.execute(query, params)
    courses = cursor.fetchall()

    result = []
    for c in courses:
        # 格式化修读时间
        study_duration = ''
        if c['study_mode'] == '全日制/非全日制':
            ft = f"{c['study_duration_ft']}年" if c['study_duration_ft'] else '-'
            pt = f"{c['study_duration_pt']}年" if c['study_duration_pt'] else '-'
            study_duration = f"{ft}/{pt}"
        elif c['study_mode'] == '仅全日制':
            study_duration = f"{c['study_duration_ft']}年" if c['study_duration_ft'] else '-'
        elif c['study_mode'] == '仅非全日制':
            study_duration = f"{c['study_duration_pt']}年" if c['study_duration_pt'] else '-'

        # 格式化学费
        tuition = ''
        tl = f"HKD{int(c['tuition_local']):,}" if c['tuition_local'] else 'HKD-'
        tn = f"HKD{int(c['tuition_non_local']):,}" if c['tuition_non_local'] else 'HKD-'
        tuition = f"{tl}（本地生）/ {tn}（非本地生）"

        # 格式化截止日期
        deadline = ''
        dl = c['deadline_local'] if c['deadline_local'] else '-'
        dn = c['deadline_non_local'] if c['deadline_non_local'] else '-'
        deadline = f"{dl}（本地生）/ {dn}（非本地生）"

        result.append({
            'id': c['id'],
            'course_code': c['course_code'],
            'school_id': c['school_id'],
            'school_abbr': c['school_abbr'],
            'school_name_cn': c['school_name_cn'],
            'school_name_en': c['school_name_en'],
            'subject_category': c['subject_category'],
            'course_name_cn': c['course_name_cn'],
            'course_name_en': c['course_name_en'],
            'teaching_mode': c['teaching_mode'],
            'study_mode': c['study_mode'],
            'study_duration_ft': c['study_duration_ft'],
            'study_duration_pt': c['study_duration_pt'],
            'study_duration_display': study_duration,
            'teaching_language': c['teaching_language'],
            'academic_year': c['academic_year'],
            'student_identity': c['student_identity'],
            'tuition_local': c['tuition_local'],
            'tuition_non_local': c['tuition_non_local'],
            'tuition_display': tuition,
            'deadline_local': c['deadline_local'],
            'deadline_non_local': c['deadline_non_local'],
            'deadline_display': deadline,
            'qf_level': c['qf_level'],
            'qr_number': c['qr_number'],
            'education_requirement': c['education_requirement'],
            'chinese_exempt': bool(c['chinese_exempt']),
            'chinese_dse': c['chinese_dse'],
            'chinese_gaokao': c['chinese_gaokao'],
            'chinese_hsk': c['chinese_hsk'],
            'chinese_other': c['chinese_other'],
            'english_exempt': bool(c['english_exempt']),
            'english_dse': c['english_dse'],
            'english_gaokao': c['english_gaokao'],
            'english_toefl_pbt': c['english_toefl_pbt'],
            'english_toefl_ibt': c['english_toefl_ibt'],
            'english_ielts': c['english_ielts'],
            'english_cet4': c['english_cet4'],
            'english_other': c['english_other'],
            'other_requirements': c['other_requirements'],
            'interview_required': bool(c['interview_required']),
            'course_description': c['course_description'],
            'course_page_url': c['course_page_url'],
            'course_brochure_url': c['course_brochure_url'],
            'created_at': c['created_at'],
        })
    return jsonify(result)

@app.route('/api/courses/<int:course_id>', methods=['GET'])
def get_course(course_id):
    """获取单个课程详情"""
    db = get_db()
    course = db.execute("""
        SELECT c.*, s.abbreviation as school_abbr, s.name_cn as school_name_cn,
               s.name_en as school_name_en, s.website as school_website
        FROM courses c
        JOIN schools s ON c.school_id = s.id
        WHERE c.id = ?
    """, (course_id,)).fetchone()
    if not course:
        return jsonify({'error': '课程不存在'}), 404
    result = dict(course)
    result['chinese_exempt'] = bool(result['chinese_exempt'])
    result['english_exempt'] = bool(result['english_exempt'])
    result['interview_required'] = bool(result['interview_required'])
    return jsonify(result)

@app.route('/api/courses', methods=['POST'])
def add_course():
    """添加课程"""
    data = request.json
    db = get_db()

    # 自动生成课程编号
    last = db.execute("SELECT course_code FROM courses ORDER BY id DESC LIMIT 1").fetchone()
    if last:
        last_num = int(last['course_code'].replace('HK-', ''))
        new_code = f"HK-{last_num + 1:04d}"
    else:
        new_code = "HK-0001"

    try:
        cursor = db.execute("""
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
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        db.commit()
        course_id = cursor.lastrowid

        # 审计日志
        changes = {k: v for k, v in data.items() if v}
        changes['course_code'] = new_code
        log_audit('courses', course_id, f"{data['course_name_cn']} ({new_code})", 'CREATE', changes,
                  data.get('modified_by', 'admin'))
        return jsonify({'id': course_id, 'course_code': new_code, 'message': '课程添加成功'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/courses/<int:course_id>', methods=['PUT'])
def update_course(course_id):
    """修改课程"""
    data = request.json
    db = get_db()
    old = db.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
    if not old:
        return jsonify({'error': '课程不存在'}), 404

    # 对比变更
    field_map = {
        'school_id': 'school_id', 'subject_category': 'subject_category',
        'course_name_cn': 'course_name_cn', 'course_name_en': 'course_name_en',
        'teaching_mode': 'teaching_mode', 'study_mode': 'study_mode',
        'study_duration_ft': 'study_duration_ft', 'study_duration_pt': 'study_duration_pt',
        'teaching_language': 'teaching_language', 'academic_year': 'academic_year',
        'student_identity': 'student_identity',
        'tuition_local': 'tuition_local', 'tuition_non_local': 'tuition_non_local',
        'deadline_local': 'deadline_local', 'deadline_non_local': 'deadline_non_local',
        'qf_level': 'qf_level', 'qr_number': 'qr_number',
        'education_requirement': 'education_requirement',
        'chinese_dse': 'chinese_dse', 'chinese_gaokao': 'chinese_gaokao',
        'chinese_hsk': 'chinese_hsk', 'chinese_other': 'chinese_other',
        'english_dse': 'english_dse', 'english_gaokao': 'english_gaokao',
        'english_toefl_pbt': 'english_toefl_pbt', 'english_toefl_ibt': 'english_toefl_ibt',
        'english_ielts': 'english_ielts', 'english_cet4': 'english_cet4',
        'english_other': 'english_other', 'other_requirements': 'other_requirements',
        'course_description': 'course_description', 'course_page_url': 'course_page_url',
        'course_brochure_url': 'course_brochure_url',
    }

    changes = {}
    for key, db_col in field_map.items():
        if key in data:
            old_val = str(old[db_col]) if old[db_col] is not None else ''
            new_val = str(data[key]) if data[key] is not None else ''
            if old_val != new_val:
                changes[key] = {'old': old[db_col], 'new': data[key]}

    # Boolean fields
    for bool_field, db_col in [('chinese_exempt', 'chinese_exempt'), ('english_exempt', 'english_exempt'),
                                 ('interview_required', 'interview_required')]:
        if bool_field in data:
            old_val = bool(old[db_col])
            new_val = bool(data[bool_field])
            if old_val != new_val:
                changes[bool_field] = {'old': old_val, 'new': new_val}

    db.execute("""
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
        data.get('school_id', old['school_id']),
        data.get('subject_category', old['subject_category']),
        data.get('course_name_cn', old['course_name_cn']),
        data.get('course_name_en', old['course_name_en']),
        data.get('teaching_mode', old['teaching_mode']),
        data.get('study_mode', old['study_mode']),
        data.get('study_duration_ft', old['study_duration_ft']),
        data.get('study_duration_pt', old['study_duration_pt']),
        data.get('teaching_language', old['teaching_language']),
        data.get('academic_year', old['academic_year']),
        data.get('student_identity', old['student_identity']),
        data.get('tuition_local', old['tuition_local']),
        data.get('tuition_non_local', old['tuition_non_local']),
        data.get('deadline_local', old['deadline_local']),
        data.get('deadline_non_local', old['deadline_non_local']),
        data.get('qf_level', old['qf_level']),
        data.get('qr_number', old['qr_number']),
        data.get('education_requirement', old['education_requirement']),
        1 if data.get('chinese_exempt') else 0,
        data.get('chinese_dse', old['chinese_dse']),
        data.get('chinese_gaokao', old['chinese_gaokao']),
        data.get('chinese_hsk', old['chinese_hsk']),
        data.get('chinese_other', old['chinese_other']),
        1 if data.get('english_exempt') else 0,
        data.get('english_dse', old['english_dse']),
        data.get('english_gaokao', old['english_gaokao']),
        data.get('english_toefl_pbt', old['english_toefl_pbt']),
        data.get('english_toefl_ibt', old['english_toefl_ibt']),
        data.get('english_ielts', old['english_ielts']),
        data.get('english_cet4', old['english_cet4']),
        data.get('english_other', old['english_other']),
        data.get('other_requirements', old['other_requirements']),
        1 if data.get('interview_required') else 0,
        data.get('course_description', old['course_description']),
        data.get('course_page_url', old['course_page_url']),
        data.get('course_brochure_url', old['course_brochure_url']),
        course_id
    ))
    db.commit()
    log_audit('courses', course_id, f"{old['course_name_cn']} ({old['course_code']})", 'UPDATE', changes,
              data.get('modified_by', 'admin'))
    return jsonify({'message': '课程修改成功'})

@app.route('/api/courses/<int:course_id>', methods=['DELETE'])
def delete_course(course_id):
    """删除课程"""
    db = get_db()
    old = db.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
    if not old:
        return jsonify({'error': '课程不存在'}), 404

    old_data = dict(old)
    db.execute("DELETE FROM courses WHERE id = ?", (course_id,))
    db.commit()
    log_audit('courses', course_id, f"{old_data['course_name_cn']} ({old_data['course_code']})", 'DELETE', old_data)
    return jsonify({'message': '课程删除成功'})

# ============================================================
# 审计日志 API
# ============================================================

@app.route('/api/audit-log', methods=['GET'])
def get_audit_log():
    """获取审计日志"""
    db = get_db()
    limit = request.args.get('limit', 100, type=int)
    table = request.args.get('table', '')
    query = "SELECT * FROM audit_log"
    params = []
    if table:
        query += " WHERE table_name = ?"
        params.append(table)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    logs = db.execute(query, params).fetchall()
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
# 应用入口
# ============================================================

if __name__ == '__main__':
    init_db()
    seed_schools()
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    print("=" * 60)
    print("  香港留学课程检索系统 - HK Course Finder")
    print(f"  访问地址: http://{host}:{port}")
    print("=" * 60)
    from waitress import serve
    serve(app, host=host, port=port, threads=4)
