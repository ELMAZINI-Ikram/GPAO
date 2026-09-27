from core.models import UserProfile

def user_role(request):
    if request.user.is_authenticated:
        try:
            profile = UserProfile.objects.get(user=request.user)
            return {'user_role': profile.role}
        except UserProfile.DoesNotExist:
            return {'user_role': 'OPERATOR'}
    return {'user_role': None}
