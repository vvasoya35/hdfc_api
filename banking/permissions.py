from rest_framework.permissions import BasePermission
from banking.models import Users_ips

class IsAuthorizedIP(BasePermission):

    def has_permission(self, request, view):
        
        user_ips = Users_ips.objects.all()
        if not user_ips:
            return False

        allowed_ips = list(Users_ips.objects.values_list('ip_address', flat=True))
        # request_ip = request.META.get("HTTP_X_FORWARDED_FOR", "")
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            request_ip = x_forwarded_for.split(',')[0].strip()
        else:
            request_ip = request.META.get('REMOTE_ADDR')

        # print("allowed_ips ", allowed_ips)
        # print("request_ip ", request_ip)
        return request_ip in allowed_ips  #
