from .models import BaseAuth, ResourceAuth,ResourceVoucherAuth
resource_all = [
    13,#"resource.self.delete",
    14,#"resource.self.update",
    15,#"resource.self.read",
]
voucher_all = [
    17,#"resource.voucher.delete",
    18,#"resource.voucher.update",
    19,#"resource.voucher.read",
]
def protect_perms(user,obj,model,perms_name = 'resource_all'):
    if perms_name == "resource_all":
        perms = resource_all
    else:
        perms = voucher_all
    data = []
    for code in perms:
        auth = model(
            user = user,
            permission_id = code,
            protected = True
        )
        if perms_name == "resource_all":
            auth.resource = obj
        else:
            auth.account = obj
        data.append(auth)
    model.objects.bulk_create(data)

def validate_resource_permission(user,roles:list[int],resource:int,permission_code):
    ret = roles and BaseAuth.objects.filter(role__id__in=roles, permission__code=permission_code).exists()
    ret = ret or (resource and roles and  ResourceAuth.objects.filter(role__id__in=roles, permission__code=permission_code, resource__id=resource).exists())
    ret = ret or (resource and roles and ResourceAuth.objects.filter(user=user, permission__code=permission_code, resource__id=resource).exists())
    return ret

def validate_vorcher_permission(user,roles:list[int],voucher:int,permission_code):
    ret = roles and BaseAuth.objects.filter(role__in=roles, permission__code=permission_code).exists()
    ret = ret or (voucher and roles and ResourceVoucherAuth.objects.filter(role__in=roles, permission__code=permission_code, voucher=voucher).exists())
    ret = ret or (voucher and roles and ResourceVoucherAuth.objects.filter(user=user, permission__code=permission_code, voucher=voucher).exists())
    return ret