"""Independent palette ordering, preservation and deferred-handler expectations."""
from tally_cases import case as tally_case,expected as tally_expected,decode as tally_decode

COLORS=(0x0000,0x000e,0x00e0,0x0e00,0x0eee,0xffff,0x1111,0x0246,0x068a,0x0ace,0x1357,0x89ab,0xcdef,0x1234,0x5678,0x9abc)
COMPONENTS=(0,0,0, 0,0,56, 0,56,0, 56,0,0, 56,56,56, 56,56,56, 0,0,0, 8,16,24, 24,32,40, 40,48,56, 8,16,24, 32,40,40, 48,56,56, 8,8,16, 24,24,32, 40,40,48)
START=dict(handler=26,direction=65535,countdown=6,transition_reload=0,level=0,curve_r=3,curve_g=3,curve_b=3,palette_scope=0)


def case(*,colors=COLORS,components=tuple(range(48)),**changes):
    return (*tally_case(**({'palette_gate':1}|changes)),*colors,*components)


def expected(c,*,components=None,**changes):
    return (*tally_expected(c[:67],**changes),*c[67:83],*(c[83:] if components is None else components))


def decode(data,count):
    rows=[tuple(map(int,l.split())) for l in data.splitlines()]
    if len(rows)!=count or any(len(r)<118 or any(v>255 or v<0 for v in r[-48:]) for r in rows):raise ValueError('palette output extent/range differs')
    tally_decode(('\n'.join(' '.join(map(str,r[:-64])) for r in rows)+'\n').encode(),count)
    return rows


def goldens():
    rows=[]
    def add(changes,**result):
        c=case(**changes);rows.append((c,expected(c,**result)))
    add({},**START,components=COMPONENTS)
    add(dict(repeats=16),**START,components=COMPONENTS) # No implicit timer ticks.
    add(dict(direction=1))
    add(dict(direction=65535,start=255,remaining=0))
    add(dict(palette_gate=32768),**START,components=COMPONENTS)
    add(dict(handler=26,direction=0),handler=25) # No tally decrement now.
    add(dict(handler=26,direction=0,start=255),handler=25)
    add(dict(handler=26,direction=1))
    add(dict(handler=26,direction=65535,palette_gate=0))
    add(dict(handler=26,direction=0,repeats=2),handler=25,tally_countdown=119)
    add(dict(palette_gate=0),tally_countdown=119)
    add(dict(mode=0,service=0))
    add(dict(speed=1),**START,components=COMPONENTS,x=201,y=108,speed=0,sx=85,sy=4,horizontal=1)
    add(dict(speed=65535,flags=0),**START,components=COMPONENTS,x=199,y=108,speed=0,sx=83,sy=4,horizontal=1)
    add(dict(speed=1,x=65535,y=0,sy=4),**START,components=COMPONENTS,x=0,y=65535,speed=0,horizontal=1)
    add(dict(handler=26,direction=0,remaining=0,start=255),handler=25)
    return rows
