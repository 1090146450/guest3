from django.http import JsonResponse
from sign.models.event import Event
from sign.models.guest import Guest
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.contrib import auth as django_auth
import base64
import time
import hashlib
# from Crypto.Cipher import AES    # 请安装 Crypto
from Crypto.Cipher import AES
import json


"""
用户认证
"""


def user_auth(request):
    """
    用户认证
    """
    get_http_auth = request.META.get('HTTP_AUTHORIZATION', b'')

    auth = get_http_auth.split()
    try:
        auth_parts = base64.b64decode(auth[1]).decode('utf-8').partition(':')
    except IndexError:
        return "null"
    userid, password = auth_parts[0], auth_parts[2]
    user = django_auth.authenticate(username=userid, password=password)
    if user is not None and user.is_active:
        django_auth.login(request, user)
        return "success"
    else:
        return "fail"


def get_event_list(request):
    """
    发布会查询接口---增加用户认证
    """
    auth_result = user_auth(request)
    if auth_result == "null":
        return JsonResponse({'status': 10011, 'message': 'user auth null'})

    if auth_result == "fail":
        return JsonResponse({'status': 10012, 'message': 'user auth fail'})

    eid = request.GET.get("eid", "")      # 发布会id
    name = request.GET.get("name", "")    # 发布会名称

    if eid == '' and name == '':
        return JsonResponse({'status': 10021, 'message': 'parameter error'})

    if eid != '':
        try:
            result = Event.objects.get(id=eid)
        except ObjectDoesNotExist:
            return JsonResponse({'status': 10022, 'message': 'query result is empty'})
        else:
            event = {
                'eid': result.id,
                'name': result.name,
                'limit': result.limit,
                'status': result.status,
                'address': result.address,
                'start_time': result.start_time
            }
            return JsonResponse({'status': 200, 'message': 'success', 'data': event})

    if name != '':
        datas = []
        results = Event.objects.filter(name__contains=name)
        if results:
            for r in results:
                event = {
                    'eid': r.id,
                    'name': r.name,
                    'limit': r.limit,
                    'status': r.status,
                    'address': r.address,
                    'start_time': r.start_time
                }
                datas.append(event)
            return JsonResponse({'status': 200, 'message': 'success', 'data': datas})
        else:
            return JsonResponse({'status': 10022, 'message': 'query result is empty'})


"""
用户签名+时间戳
"""


def user_sign(request):
    """
    用户签名+时间戳
    """
    if request.method == 'POST':
        client_time = request.POST.get('time', '')   # 客户端时间戳
        client_sign = request.POST.get('sign', '')   # 客户端签名
    else:
        return "error"

    if client_time == '' or client_sign == '':
        return "sign null"

    try:
        int(client_time)
    except ValueError:
        return "value error"

    # 服务器时间
    server_time = str(time.time()).split('.')[0]

    # 获取时间差
    time_difference = int(server_time) - int(client_time)
    if time_difference >= 60:
        return "timeout"

    # 签名检查
    md5 = hashlib.md5()
    sign_str = client_time + "&Guest-Bugmaster"
    sign_bytes_utf8 = sign_str.encode(encoding="utf-8")
    md5.update(sign_bytes_utf8)
    sever_sign = md5.hexdigest()
    if sever_sign != client_sign:
        return "sign fail"
    else:
        return "sign right"


def add_event(request):
    """
    添加发布会接口---增加签名+时间戳
    """
    sign_result = user_sign(request)
    if sign_result == "error":
        return JsonResponse({'status': 10011, 'message': 'request error'})
    elif sign_result == "sign null":
        return JsonResponse({'status': 10012, 'message': 'user sign null'})
    elif sign_result == "timeout":
        return JsonResponse({'status': 10013, 'message': 'user sign timeout'})
    elif sign_result == "sign fail":
        return JsonResponse({'status': 10014, 'message': 'user sign error'})
    elif sign_result == "value error":
        return JsonResponse({'status': 10015, 'message': 'user sign type error'})

    eid = request.POST.get('eid', '')                 # 发布会id
    name = request.POST.get('name', '')               # 发布会标题
    limit = request.POST.get('limit', '')             # 限制人数
    status = request.POST.get('status', '')           # 状态
    address = request.POST.get('address', '')         # 地址
    start_time = request.POST.get('start_time', '')   # 发布会时间

    if eid == '' or name == '' or limit == '' or address == '' or start_time == '':
        return JsonResponse({'status': 10021, 'message': 'parameter error'})

    result = Event.objects.filter(id=eid)
    if result:
        return JsonResponse({'status': 10022, 'message': 'event id already exists'})

    result = Event.objects.filter(name=name)
    if result:
        return JsonResponse({'status': 10023, 'message': 'event name already exists'})

    if status == '':
        status = 1

    try:
        Event.objects.create(id=eid, name=name, limit=limit, address=address, status=int(
            status), start_time=start_time)
    except ValidationError:
        error = 'start_time format error. It must be in YYYY-MM-DD HH:MM:SS format.'
        return JsonResponse({'status': 10024, 'message': error})

    return JsonResponse({'status': 200, 'message': 'add event success'})


"""
AES加密算法
"""

BS = 16


def unpad(s): return s[0: - ord(s[-1])]


def decryptBase64(src):
    return base64.urlsafe_b64decode(src)


def decryptAES(src):
    """
    解析AES密文
    """
    src = decryptBase64(src)
    key = b'W7v4D60fds2Cmk2U'
    iv = b"1172311105789011"
    cryptor = AES.new(key, AES.MODE_CBC, iv)
    text = cryptor.decrypt(src).decode()
    return unpad(text)


def aes_encryption(request):
    if request.method == 'POST':
        data = request.POST.get("data", "")
    else:
        return "error"

    if data == "":
        return "data null"

    # 解密
    decode = decryptAES(data)
    # 转化为字典
    dict_data = json.loads(decode)
    return dict_data


def get_guest_list(request):
    """
    嘉宾查询接口----AES算法
    """
    dict_data = aes_encryption(request)

    if dict_data == "data null":
        return JsonResponse({'status': 10010, 'message': 'data null'})

    if dict_data == "error":
        return JsonResponse({'status': 10011, 'message': 'request error'})

    # 取出对应的发布会id和手机号
    try:
        eid = dict_data['eid']
        phone = dict_data['phone']
    except KeyError:
        return JsonResponse({'status': 10012, 'message': 'parameter error'})

    if eid == '':
        return JsonResponse({'status': 10021, 'message': 'eid cannot be empty'})

    if eid != '' and phone == '':
        datas = []
        results = Guest.objects.filter(event_id=eid)
        if results:
            for r in results:
                guest = {
                    'realname': r.realname,
                    'phone': r.phone,
                    'email': r.email,
                    'sign': r.sign
                }
                datas.append(guest)
            return JsonResponse({'status': 200, 'message': 'success', 'data': datas})
        else:
            return JsonResponse({'status': 10022, 'message': 'query result is empty'})

    if eid != '' and phone != '':

        try:
            result = Guest.objects.get(phone=phone, event_id=eid)
        except ObjectDoesNotExist:
            return JsonResponse({'status': 10022, 'message': 'query result is empty'})
        else:
            guest = {
                'realname': result.realname,
                'phone': result.phone,
                'email': result.email,
                'sign': result.sign
            }

            return JsonResponse({'status': 200, 'message': 'success', 'data': guest})
