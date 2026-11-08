from portwatcher import parse

k, r = parse('tcp LISTEN 0 128 [::]:22 [::]:* users:(("sshd",pid=812,fd=4))')
assert r[:8] == [22, "TCP6", "LISTEN", "sshd", "::", "—", "#5eead4", 812], r
k, r = parse('udp UNCONN 0 0 127.0.0.53%lo:53 0.0.0.0:*')
assert r[:6] == [53, "UDP", "UNCONN", "—", "127.0.0.53", "—"], r
k, r = parse('tcp ESTAB 0 0 10.0.0.5:44321 140.82.112.3:443 users:(("firefox",pid=99,fd=7))')
assert r[5] == "140.82.112.3:443" and r[7] == 99, r
print("ok")
