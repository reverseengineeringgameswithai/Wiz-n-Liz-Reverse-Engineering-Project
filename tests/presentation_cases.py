"""Hand-calculated animation boundaries; no ROM or native implementation used."""
from actor_cases import case as actor_case,expected


def case(**changes):
    return actor_case(**(dict(mode=0x81,first=2,begin=0,end=5,counter=1,reload=3)|changes))


def goldens():
    rows=[]
    def add(changes,**result):
        c=case(**changes);rows.append((c,expected(c,**result)))
    add({'mode':0x80})  # disabled leaves even the countdown unchanged
    add({'counter':0},counter=255)
    add({'counter':2},counter=1)
    add({},first=3,counter=3)
    add({'first':5},first=0,counter=3)
    add({'mode':0x83},first=1,counter=3)
    add({'mode':0x83,'first':0},first=5,counter=3)
    add({'mode':0x89,'first':5},first=5,mode=0x8b,counter=3)
    add({'mode':0x8b,'first':0},first=0,mode=0x89,counter=3)
    add({'first':65535},first=0,counter=3)
    add({'mode':0x83,'first':0,'begin':1},first=65535,counter=3)
    add({'reload':0},first=3,counter=0)
    # Reaching a target by this advance does NOT call it until the next expiry.
    add({'mode':0x85,'target':3},first=3,counter=3)
    add({'mode':0x85,'target':2,'counter':2},counter=1)
    for cb,right in ((1,True),(2,False),(3,False),(4,True)):
        add({'mode':0x87,'target':2,'callback':cb,'flags':0xa5a5},
            handler=3 if right else 4,flags=0xada5 if right else 0xa5a5,
            mode=0x81,first=2,begin=0,end=5,counter=4,reload=4)
    for cb in (5,6):
        add({'mode':0x85,'first':63,'begin':62,'end':63,'target':63,'cycles':2,'callback':cb},
            first=62,cycles=1,counter=3)
        add({'mode':0x85,'first':63,'begin':62,'end':63,'target':63,'cycles':1,'callback':cb},
            mode=0x81,first=24,begin=24,end=29,counter=2,reload=2,cycles=0)
        add({'mode':0x85,'target':2,'cycles':0,'callback':cb},first=0,cycles=65535,counter=3)
    return rows
