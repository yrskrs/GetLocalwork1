#!/usr/bin/env python
"""
Простий тестовий скрипт для перевірки сайту
"""

import sys
import os

# Add project directory to path
sys.path.insert(0, '/home/yuriilinux/project_site/new_projectsite/myproject2')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject2.settings')

import django
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from submissions.models import Submission, ClassGroup, Comment

print("\n" + "="*60)
print("ТЕСТУВАННЯ САЙТУ ЗДАЧІ РОБІТ")
print("="*60 + "\n")

# Database check
print("БАЗА ДАНИХ:")
print(f"  Користувачів: {User.objects.count()}")
print(f"  Класів: {ClassGroup.objects.count()}")
print(f"  Робіт: {Submission.objects.count()}")
print(f"  Коментарів: {Comment.objects.count()}")

client = Client()
tests_passed = 0
tests_failed = 0

print("\n" + "="*60)
print("ТЕСТУВАННЯ ENDPOINTS")
print("="*60 + "\n")

# Test 1: Homepage
try:
    response = client.get('/')
    if response.status_code == 200:
        print("✓ GET / - OK (Homepage)")
        tests_passed += 1
    else:
        print(f"✗ GET / - FAIL (Status: {response.status_code})")
        tests_failed += 1
except Exception as e:
    print(f"✗ GET / - ERROR: {e}")
    tests_failed += 1

# Test 2: Success feed
try:
    response = client.get('/success/')
    if response.status_code == 200:
        print("✓ GET /success/ - OK (Success feed)")
        tests_passed += 1
    else:
        print(f"✗ GET /success/ - FAIL (Status: {response.status_code})")
        tests_failed += 1
except Exception as e:
    print(f"✗ GET /success/ - ERROR: {e}")
    tests_failed += 1

# Test 3: Teacher login page
try:
    response = client.get('/teacher/')
    if response.status_code == 200:
        print("✓ GET /teacher/ - OK (Teacher login)")
        tests_passed += 1
    else:
        print(f"✗ GET /teacher/ - FAIL (Status: {response.status_code})")
        tests_failed += 1
except Exception as e:
    print(f"✗ GET /teacher/ - ERROR: {e}")
    tests_failed += 1

# Test with authentication
teacher = User.objects.filter(is_staff=True).first()
if teacher:
    print(f"\nВикористовую вчителя: {teacher.username}")
    client.force_login(teacher)
    
    # Test 4: Teacher dashboard
    try:
        response = client.get('/teacher/dashboard/')
        if response.status_code == 200:
            print("✓ GET /teacher/dashboard/ - OK (Teacher dashboard)")
            tests_passed += 1
        else:
            print(f"✗ GET /teacher/dashboard/ - FAIL (Status: {response.status_code})")
            tests_failed += 1
    except Exception as e:
        print(f"✗ GET /teacher/dashboard/ - ERROR: {e}")
        tests_failed += 1
    
    # Test 5: File viewer
    submission = Submission.objects.filter(file__isnull=False).first()
    if submission:
        try:
            response = client.get(f'/teacher/view-file/{submission.id}/')
            if response.status_code == 200:
                print(f"✓ GET /teacher/view-file/{submission.id}/ - OK (File viewer)")
                tests_passed += 1
            else:
                print(f"✗ GET /teacher/view-file/{submission.id}/ - FAIL (Status: {response.status_code})")
                tests_failed += 1
        except Exception as e:
            print(f"✗ GET /teacher/view-file/{submission.id}/ - ERROR: {e}")
            tests_failed += 1
    else:
        print("⚠ File viewer - SKIP (No submissions with files)")
    
    # Test 6: Activity log
    try:
        response = client.get('/teacher/activity/')
        if response.status_code == 200:
            print("✓ GET /teacher/activity/ - OK (Activity log)")
            tests_passed += 1
        else:
            print(f"✗ GET /teacher/activity/ - FAIL (Status: {response.status_code})")
            tests_failed += 1
    except Exception as e:
        print(f"✗ GET /teacher/activity/ - ERROR: {e}")
        tests_failed += 1
    
    # Test 7: Gradebook
    try:
        response = client.get('/teacher/gradebook/')
        if response.status_code == 200:
            print("✓ GET /teacher/gradebook/ - OK (Gradebook)")
            tests_passed += 1
        else:
            print(f"✗ GET /teacher/gradebook/ - FAIL (Status: {response.status_code})")
            tests_failed += 1
    except Exception as e:
        print(f"✗ GET /teacher/gradebook/ - ERROR: {e}")
        tests_failed += 1
    
    # Test 8: Comment creation
    if submission:
        try:
            comment_count_before = Comment.objects.filter(submission=submission).count()
            response = client.post(f'/teacher/view-file/{submission.id}/', {
                'action': 'comment',
                'comment': 'Тестовий коментар'
            })
            comment_count_after = Comment.objects.filter(submission=submission).count()
            
            if comment_count_after > comment_count_before:
                print("✓ POST comment - OK (Comment created)")
                tests_passed += 1
                # Clean up
                Comment.objects.filter(submission=submission, text='Тестовий коментар').delete()
            else:
                print("✗ POST comment - FAIL (Comment not created)")
                tests_failed += 1
        except Exception as e:
            print(f"✗ POST comment - ERROR: {e}")
            tests_failed += 1
    
    # Test 9: Grading
    if submission:
        try:
            original_grade = submission.grade
            response = client.post(f'/teacher/grade/{submission.id}/', {
                'grade': '10'
            })
            submission.refresh_from_db()
            
            if submission.grade == '10':
                print("✓ POST grade - OK (Grade saved)")
                tests_passed += 1
                # Restore
                submission.grade = original_grade
                submission.save()
            else:
                print("✗ POST grade - FAIL (Grade not saved)")
                tests_failed += 1
        except Exception as e:
            print(f"✗ POST grade - ERROR: {e}")
            tests_failed += 1

else:
    print("\n⚠ Немає вчителя для тестування")

# Summary
print("\n" + "="*60)
print("ПІДСУМОК")
print("="*60)
print(f"Пройдено: {tests_passed}")
print(f"Провалено: {tests_failed}")
print(f"Всього: {tests_passed + tests_failed}")

if tests_failed == 0:
    print("\n✓ ВСІ ТЕСТИ ПРОЙДЕНО!\n")
    sys.exit(0)
else:
    print(f"\n✗ ЗНАЙДЕНО {tests_failed} ПОМИЛОК\n")
    sys.exit(1)
