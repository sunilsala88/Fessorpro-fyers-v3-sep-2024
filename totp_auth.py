

totp_key='asdfgasdf'

import pyotp as tp
t = tp.TOTP(totp_key).now()
print(t)