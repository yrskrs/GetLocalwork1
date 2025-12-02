
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
            import timedelta
            # Or just filter by date part if possible, but let's keep it simple
            logs = logs.filter(timestamp__date__lte=date_to)
        except ValueError:
            pass
            
    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'submissions/activity_log.html', {
        'page_obj': page_obj,
        'action_choices': ActivityLog.ACTION_CHOICES,
        'selected_action': action_type,
        'date_from': date_from,
        'date_to': date_to,
    })
