

totp_key='3AAB'

import pyotp as tp
t = tp.TOTP(totp_key).now()
print(t)