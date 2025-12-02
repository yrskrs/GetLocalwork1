from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse, HttpResponse, FileResponse
from django.db.models import Q
from django.core.paginator import Paginator
import csv
import os
from datetime import datetime
from collections import defaultdict
from .models import Submission, ClassGroup, ActivityLog, log_activity
from .forms import SubmissionForm

def submission_create(request):
    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            
            # Parse full_name into first_name and last_name
            full_name = form.cleaned_data.get('full_name', '').strip()
            name_parts = full_name.split(maxsplit=1)
            
            if len(name_parts) == 2:
                submission.last_name = name_parts[0]
                submission.first_name = name_parts[1]
            elif len(name_parts) == 1:
                submission.last_name = name_parts[0]
                submission.first_name = ''
            
            submission.save()
            
            # Log activity
            log_activity(
                None, 
                'submission', 
                f"Учень {submission.last_name} {submission.first_name} здав роботу ({submission.class_group.name})"
            )
            
            return redirect('submission_success')
    else:
        form = SubmissionForm()
    
    return render(request, 'submissions/submission_form.html', {'form': form})

def submission_success(request):
    from django.core.paginator import Paginator
    
    submissions = Submission.objects.all().order_by('-submitted_at')
    
    # Search filter
    search_query = request.GET.get('search', '').strip()
    if search_query:
        submissions = submissions.filter(
            Q(last_name__icontains=search_query) | 
            Q(first_name__icontains=search_query)
        )
    
    paginator = Paginator(submissions, 15)  # 15 per page
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'submissions/success_feed.html', {
        'page_obj': page_obj,
        'search_query': search_query
    })

def teacher_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            user = form.get_user()
            login(request, user)
            log_activity(user, 'login', f"Вчитель {user.username} увійшов в систему")
            return redirect('teacher_dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'submissions/teacher_login.html', {'form': form})

@login_required
def teacher_logout(request):
    logout(request)
    return redirect('submission_success')

@login_required
def teacher_dashboard(request):
    submissions = Submission.objects.all().order_by('-submitted_at')
    class_groups = list(ClassGroup.objects.all())
    
    # Filtering
    class_filter = request.GET.get('class_group')
    search_query = request.GET.get('search')
    date_filter = request.GET.get('date')
    
    selected_class_id = None
    if class_filter:
        try:
            selected_class_id = int(class_filter)
            submissions = submissions.filter(class_group__id=selected_class_id)
        except ValueError:
            pass
    
    if search_query:
        submissions = submissions.filter(
            Q(last_name__icontains=search_query) | 
            Q(first_name__icontains=search_query)
        )
    
    if date_filter:
        try:
            from datetime import datetime
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            submissions = submissions.filter(submitted_at__date=filter_date)
        except ValueError:
            pass

    # Mark selected class
    for cls in class_groups:
        cls.selected = (cls.id == selected_class_id)
    
    # Pagination - 15 per page
    paginator = Paginator(submissions, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'submissions/teacher_dashboard.html', {
        'page_obj': page_obj,
        'class_groups': class_groups,
        'selected_date': date_filter,
    })

@login_required
def grade_submission(request, submission_id):
    if request.method == 'POST':
        submission = get_object_or_404(Submission, id=submission_id)
        action = request.POST.get('action')
        
        if action == 'comment':
            new_comment = request.POST.get('comment')
            if new_comment:
                timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
                # Append new comment to existing ones
                current_comments = submission.comment or ""
                separator = "----------------------------------------"
                
                new_entry = f"📅 {timestamp} | 👤 {request.user.first_name} {request.user.last_name}:\n{new_comment}"
                
                if current_comments:
                    submission.comment = f"{current_comments}\n\n{separator}\n\n{new_entry}"
                else:
                    submission.comment = new_entry
                
                submission.teacher = request.user
                submission.save()
                
                # Log activity
                log_activity(
                    request.user, 
                    'comment', 
                    f"Коментар до роботи: {submission.last_name} {submission.first_name}"
                )
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success', 
                        'message': 'Коментар додано!',
                        'full_comment': submission.comment
                    })
            
            messages.success(request, 'Коментар збережено!')
            
        else: # Default to grading
            grade = request.POST.get('grade')
            submission.grade = grade
            submission.save()
            
            # Log activity
            log_activity(
                request.user, 
                'grading', 
                f"Оцінено роботу: {submission.last_name} {submission.first_name} - {grade}"
            )
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success', 'grade': grade})
            
            messages.success(request, f'Оцінку {grade} успішно збережено!')
            
        return redirect('view_file', submission_id=submission.id)
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def student_detail(request, student_name):
    try:
        last, first = student_name.split('_')
        submissions = Submission.objects.filter(
            last_name__iexact=last, 
            first_name__iexact=first
        ).order_by('-submitted_at')
    except ValueError:
        submissions = []
        
    return render(request, 'submissions/student_detail.html', {
        'submissions': submissions,
        'student_name': student_name.replace('_', ' ')
    })

@login_required
def export_grades(request):
    class_group_id = request.GET.get('class_group')
    
    # Determine filename and filter submissions
    if class_group_id:
        try:
            selected_class = ClassGroup.objects.get(id=class_group_id)
            submissions = Submission.objects.filter(
                class_group_id=class_group_id,
                grade__isnull=False
            ).order_by('last_name', 'submitted_at')
            filename = f'grades_{selected_class.name}.csv'
        except ClassGroup.DoesNotExist:
            submissions = Submission.objects.filter(grade__isnull=False).order_by('last_name', 'submitted_at')
            filename = 'grades.csv'
    else:
        submissions = Submission.objects.filter(grade__isnull=False).order_by('last_name', 'submitted_at')
        filename = 'grades_all.csv'
    
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow(['Прізвище', "Ім'я", 'Клас', 'Дата', 'Оцінка'])
    
    for sub in submissions:
        writer.writerow([
            sub.last_name, 
            sub.first_name, 
            sub.class_group.name,
            sub.submitted_at.strftime('%Y-%m-%d'), 
            sub.grade
        ])

    return response

@login_required
def gradebook(request):
    class_groups = list(ClassGroup.objects.all())
    selected_class_id = request.GET.get('class_group')
    view_mode = request.GET.get('view')
    
    # Check if user wants to see all grades
    if view_mode == 'all_grades':
        # Get all submissions with grades
        all_submissions = Submission.objects.filter(
            grade__isnull=False
        ).order_by('-submitted_at').select_related('class_group')
        
        # Pagination for all grades
        paginator = Paginator(all_submissions, 15)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        return render(request, 'submissions/gradebook_all.html', {
            'page_obj': page_obj,
        })
    
    # Mark selected class
    for cls in class_groups:
        cls.selected = (str(cls.id) == str(selected_class_id))
    
    if not selected_class_id:
        return render(request, 'submissions/gradebook.html', {
            'class_groups': class_groups,
            'selected_class': None,
        })
    
    try:
        selected_class = ClassGroup.objects.get(id=selected_class_id)
    except ClassGroup.DoesNotExist:
        selected_class = None
        
    # Get all submissions for this class
    submissions = Submission.objects.filter(
        class_group_id=selected_class_id
    ).order_by('last_name', 'first_name', 'submitted_at')
    
    # Group by student (case-insensitive)
    students = {}
    dates = set()
    
    for sub in submissions:
        student_key = (sub.last_name.lower(), sub.first_name.lower())
        date_key = sub.submitted_at.date()
        dates.add(date_key)
        
        if student_key not in students:
            students[student_key] = {
                'last_name': sub.last_name,
                'first_name': sub.first_name,
                'grades': {}
            }
        
        # Store grades as lists to handle multiple grades per date
        if date_key not in students[student_key]['grades']:
            students[student_key]['grades'][date_key] = []
        
        if sub.grade:
            students[student_key]['grades'][date_key].append(sub.grade)
    
    # Sort dates
    sorted_dates = sorted(dates)
    
    # Convert to list for template
    student_list = []
    for key in sorted(students.keys()):
        student = students[key]
        grade_list = [student['grades'].get(date, []) for date in sorted_dates]
        student_list.append({
            'last_name': student['last_name'],
            'first_name': student['first_name'],
            'grades': grade_list
        })
    
    return render(request, 'submissions/gradebook.html', {
        'class_groups': class_groups,
        'selected_class': selected_class,
        'students': student_list,
        'dates': sorted_dates,
    })

def submission_detail(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    is_teacher = request.user.is_authenticated
    
    return render(request, 'submissions/submission_detail.html', {
        'submission': submission,
        'is_teacher': is_teacher,
    })

@login_required
def update_comment(request, submission_id):
    if request.method == 'POST':
        submission = get_object_or_404(Submission, id=submission_id)
        comment = request.POST.get('comment', '').strip()
        submission.comment = comment
        submission.teacher = request.user
        submission.save()
        
        # Log activity
        log_activity(
            request.user, 
            'comment', 
            f"Коментар до роботи {submission.last_name} {submission.first_name}"
        )
        
        return JsonResponse({'status': 'success', 'comment': comment})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def view_file(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    
    # Handle grading
    if request.method == 'POST':
        grade = request.POST.get('grade')
        if grade:
            submission.grade = grade
            submission.save()
            log_activity(request.user, 'graded', f"Оцінено роботу {submission.first_name} {submission.last_name}: {grade}")
            
            # Add success message
            from django.contrib import messages
            messages.success(request, f'Оцінку {grade} успішно збережено!')
            
            # Redirect to same page to show updated grade
            return redirect('view_file', submission_id=submission_id)

    # Navigation logic - sort by submission date
    all_submissions = Submission.objects.all().order_by('-submitted_at')
    
    submission_list = list(all_submissions)
    try:
        current_index = submission_list.index(submission)
        prev_submission = submission_list[current_index - 1] if current_index > 0 else None
        next_submission = submission_list[current_index + 1] if current_index < len(submission_list) - 1 else None
    except ValueError:
        prev_submission = None
        next_submission = None

    if not submission.file:
        return HttpResponse("Файл не знайдено", status=404)
    
    # Determine file type and content
    file_ext = submission.get_file_extension().lower()
    file_type = 'unknown'
    content = None
    html_content = None
    archive_content = None
    error_message = None

    # List of archive extensions
    archive_files = ['.zip', '.rar', '.7z', '.tar', '.gz']
    
    # List of office preview extensions
    office_preview = ['.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt', '.odt', '.ods', '.odp']
    
    # List of image extensions
    image_files = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']

    if file_ext in ['.py', '.js', '.html', '.css', '.txt', '.md', '.json']:
        file_type = 'code'
        try:
            with open(submission.file.path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            content = f"Помилка при читанні файлу: {str(e)}"
            
    elif file_ext in office_preview:
        file_type = 'office_preview'
        from .utils import (
            convert_docx_to_html, 
            convert_xlsx_to_html, 
            convert_pptx_to_html,
            convert_odt_to_html,
            convert_ods_to_html,
            convert_odp_to_html
        )
        try:
            if file_ext in ['.docx', '.doc']:
                html_content, error_message = convert_docx_to_html(submission.file.path)
            elif file_ext in ['.xlsx', '.xls']:
                html_content, error_message = convert_xlsx_to_html(submission.file.path)
            elif file_ext in ['.pptx', '.ppt']:
                html_content, error_message = convert_pptx_to_html(submission.file.path)
            elif file_ext == '.odt':
                html_content, error_message = convert_odt_to_html(submission.file.path)
            elif file_ext == '.ods':
                html_content, error_message = convert_ods_to_html(submission.file.path)
            elif file_ext == '.odp':
                html_content, error_message = convert_odp_to_html(submission.file.path)
        except Exception as e:
            error_message = f"Помилка конвертації: {str(e)}"

    elif file_ext in archive_files:
        file_type = 'archive'
        from .utils import get_archive_content
        archive_content, error_message = get_archive_content(submission.file.path)
        
    elif file_ext in image_files:
        file_type = 'image'
        # For images, we just need the URL which is available via submission.file.url
        
    elif file_ext in ['.pdf']:
        # PDF handling (browser native)
        return FileResponse(open(submission.file.path, 'rb'), content_type='application/pdf')

    else:
        file_type = 'office' # Default fallback

    context = {
        'submission': submission,
        'file_name': os.path.basename(submission.file.name),
        'file_ext': file_ext,
        'file_type': file_type,
        'content': content,
        'html_content': html_content,
        'archive_content': archive_content,
        'error_message': error_message,
        'prev_submission': prev_submission,
        'next_submission': next_submission,
    }
    return render(request, 'submissions/file_viewer.html', context)


@login_required
def activity_log(request):
    logs = ActivityLog.objects.all()
    
    # Filtering
    action_type = request.GET.get('action_type')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if action_type:
        logs = logs.filter(action_type=action_type)
        
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            logs = logs.filter(timestamp__gte=date_from_obj)
        except ValueError:
            pass
            
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            # Add one day to include the end date fully
            # Or just filter by date part if possible, but let's keep it simple
            logs = logs.filter(timestamp__date__lte=date_to)
        except ValueError:
            pass
            
    # Pagination
    paginator = Paginator(logs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Prepare action choices with selected state
    action_choices_context = []
    for code, name in ActivityLog.ACTION_CHOICES:
        action_choices_context.append({
            'code': code,
            'name': name,
            'selected': (code == action_type)
        })
    
    return render(request, 'submissions/activity_log.html', {
        'page_obj': page_obj,
        'action_choices': action_choices_context,
        'selected_action': action_type,
        'date_from': date_from,
        'date_to': date_to,
    })
