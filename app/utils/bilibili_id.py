table = 'fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF'
tr = {}
for i in range(58):
	tr[table[i]] = i
s = [11, 10, 3, 8, 4, 6]
xor = 177451812
add = 8728348608
error = "¿你在想桃子？"

def bv2av(bid: str) -> int:
    """把哔哩哔哩视频的bv号转成av号"""
    table = 'fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF'
    tr = {}
    for i in range(58):
        tr[table[i]] = i
    s = [11, 10, 3, 8, 4, 6]
    r = 0
    for i in range(6):
        r += tr[bid[s[i]]] * 58 ** i
    aid = (r - 8728348608) ^ 177451812
    return aid


def av2bv(x: int) -> str:
	x = (x ^ xor) + add
	r = list('BV1  4 1 7  ')
	for i in range(6):
		r[s[i]] = table[x // 58 ** i % 58]
	return ''.join(r)