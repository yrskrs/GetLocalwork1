from django.contrib import admin
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import Comment
from django.shortcuts import get_object_or_404

@login_required
@require_POST  
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Check if user is the author or has permission
    if comment.author == request.user or request.user.is_staff:
        comment.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
        
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.success(request, 'Коментар видалено!')
        return redirect('view_file', submission_id=comment.submission.id)
    
    return JsonResponse({'status': 'error', 'message': 'Немає прав'}, status=403)
