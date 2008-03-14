from ZTUtils import b2a, a2b

def encodeEmail(email):
    if email is None:
        return None
    email = email.strip()
    code = b2a(email)
    while (code[0]=='_' or code[-1]=='_'):
        email = email+" "
        code = b2a(email)
    return code

def decodeEmail(code):
    if code is None:
        return None
    email = a2b(code)
    email = email.strip()
    return email