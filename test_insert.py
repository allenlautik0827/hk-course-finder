#!/usr/bin/env python3
import sqlite3
DB_PATH = 'database.db'
db = sqlite3.connect(DB_PATH)
db.row_factory = sqlite3.Row
db.execute('PRAGMA foreign_keys=ON')

data = {
    'school_id': 1,
    'subject_category': '商科',
    'course_name_cn': '测试课程XYZ',
    'course_name_en': 'Test',
    'teaching_mode': '授课式',
    'study_mode': '全日制',
    'study_duration_ft': 1.0,
    'teaching_language': '英语',
    'academic_year': '2025/26',
    'student_identity': '本地生/非本地生',
    'tuition_local': 150000,
    'tuition_non_local': 180000
}

last = db.execute('SELECT course_code FROM courses ORDER BY id DESC LIMIT 1').fetchone()
print('last:', last)
new_code = 'HK-0001'

try:
    cur = db.execute('''
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
    ''', (
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
    print('SUCCESS! lastrowid:', cur.lastrowid)
    db.execute('DELETE FROM courses WHERE id = ?', (cur.lastrowid,))
    db.commit()
except Exception as e:
    print('ERROR type:', type(e).__name__)
    print('ERROR str:', str(e))
    print('ERROR repr:', repr(e))
db.close()
