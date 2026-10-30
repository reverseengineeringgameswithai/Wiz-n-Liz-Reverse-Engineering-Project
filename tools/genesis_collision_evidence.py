"""Strict ordinary-window input writers and 78EE/AC5E dispatch evidence."""
from genesis_actor_capture import require,block,be

def collision_fields(b):
    require(len(b)==78 and be(b,0x16,4)==0x12646 and be(b,0x1a,4)==0 and be(b,0x46,4)==0x78ee and be(b,0x14)==0,'collision selectors/service differ')
    links={0:0,0xffff0690:1,0xffff0838:2};link=be(b,0x4a,4)
    require(link in links,'unmapped collision control identity')
    return (be(b,2),be(b,4),be(b,18),b[0],be(b,6),be(b,8),be(b,10),b[12],b[13],be(b,14),be(b,16),links[link],be(b,0x1e),be(b,0x20))

def validate_inputs(events,writes,before,after,pairs):
    # Retain the fixed collision config once. P1 tracking is produced by the
    # native wrapper; no original coordinate is fed into later native calls.
    fixed=((0x13ae,2),(0x33e2,2),(0x87a,4))
    require((be(before,0x13ae),be(before,0x33e2),before[0x87a:0x87e])==(1023,0,bytes(4)),'ordinary collision context differs')
    require(all(before[o:o+n]==after[o:o+n] for o,n in fixed),'collision context changed at endpoint')
    for e in events:
        require(block(e,'collision_mask')==before[0x13ae:0x13b0] and block(e,'multiplayer')==before[0x33e2:0x33e4] and block(e,'control2')[0x42:0x46]==before[0x87a:0x87e],'collision context changed between hooks')
    tracked=[]
    for e in writes:
        a=e['address'];n=e['width']
        require(not any(a<0xff0000+o+size and 0xff0000+o<a+n for o,size in fixed),'unmodeled collision config/secondary writer')
        if a<0xff06d6 and 0xff06d2<a+n:
            require(e['cpu']=='M68K' and n==2 and (e['pc'],a) in ((0xf91e,0xff06d2),(0xf928,0xff06d4)) and e['registers']['M68K A5']==0xffff0690 and e['registers']['M68K A6']==0xffff1ab4,'unmodeled primary tracking writer')
            tracked.append(e)
    require(len(tracked)==2*len(pairs),'primary tracking write cadence differs')
    for i,p in enumerate(pairs):
        x,y=tracked[2*i:2*i+2];ret=p['return'];c=block(ret,'control')
        require(x['frame']==y['frame']==ret['frame'] and (x['pc'],y['pc'])==(0xf91e,0xf928),'tracking writer order differs')
        require((x['value'],y['value'])==(be(c,0x42),be(c,0x44)),'tracking write values differ')
    require(before[0x6d2:0x6d6]==block(pairs[0]['wrapper'],'control')[0x42:0x46] and after[0x6d2:0x6d6]==block(pairs[-1]['return'],'control')[0x42:0x46],'tracking boundary continuity differs')
    helpers=[e for e in events if e['pc']==0xac5e]
    require(len(helpers)==len(pairs) and all(e['registers']['M68K A6']==0xffff2e82 and e['registers']['M68K A5']==0xffff0690 for e in helpers),'unexpected overlap client/control')
    y_checks=sum(e['pc']==0xac8e for e in events)
    return dict(x_mask=1023,secondary_gate=0,secondary_tracking=[0,0],fixed_writes=0,primary_tracking_writes=len(tracked),primary_queries=len(helpers),x_misses=len(helpers)-y_checks,y_misses=y_checks,
        scope='P1 wrapper F91A/F924 writes control +42/+44 (native write next PCs F91E/F928); no mask, gate or P2 tracking writers in this window. P2 production is unsupported.')

def validate_phase(events,begin,end,pair):
    own=begin['registers']['M68K A6'];sp=begin['registers']['M68K A7']
    selected=[e for e in events if begin['sequence']<=e['sequence']<=end['sequence'] and e['registers']['M68K A6']==own]
    ycomp=[e for e in selected if e['pc']==0xac8e]
    expected=[0x69aa,0xf76c,0x69b6,0x12646,0x69bc,0x69c0,0x78ee,0xac5e,0xac78]+([0xac8e] if ycomp else [])+[0xac9a,0x78f8,0x790e,0x69c2]
    require([e['pc'] for e in selected]==expected,'collision phase/call order differs')
    _,pres,dispatch,handler,done,call,service,helper,cmp,ret,back,miss,finish=[e for e in selected if e['pc']!=0xac8e]
    require(all(e['registers']['M68K A7']==sp for e in (dispatch,done,call,finish)),'collision dispatch stack differs')
    for e,caller,depth in [(pres,0x69b6,4),(handler,0x69bc,4),(service,0x69c2,4),(helper,0x78f8,8),(cmp,0x78f8,8),(ret,0x78f8,8),(back,0x69c2,4),(miss,0x69c2,4)]+[(e,0x78f8,8) for e in ycomp]:
        require(e['registers']['M68K A7']==sp-depth and be(block(e,'stack'),0,4)==caller,'collision caller/return stack differs')
    require(dispatch['registers']['M68K A0']==0x12646 and call['registers']['M68K A0']==0x78ee,'collision selected handler/service differs')
    require(all(e['registers']['M68K A5']==0xffff0690 for e in (helper,cmp,ret,back,miss,finish,*ycomp)),'collision primary control identity differs')
    require(ret['registers']['M68K D0']&65535==0 and ret['registers']['M68K SR']&4 and back['registers']['M68K SR']&4,'collision miss result/flags differ')
    b=block(helper,'object');c=block(helper,'control');d2=((be(b,2)+be(b,0x1e)-be(c,0x42))&65535)&be(block(helper,'collision_mask'),0);d0=(be(b,0x1e)+16)&65535
    require((cmp['registers']['M68K D2']&65535,cmp['registers']['M68K D0']&65535)==(d2,d0) and bool(ycomp)==(d2<=d0),'collision unsigned X arithmetic/branch differs')
    if ycomp:
        y,=ycomp;d2=(be(b,4)+be(b,0x20)-be(c,0x44))&65535;d0=(be(b,0x20)+12)&65535
        require((y['registers']['M68K D2']&65535,y['registers']['M68K D0']&65535)==(d2,d0) and d2>d0,'collision unsigned Y miss arithmetic differs')
    require(all(block(e,'control')[0x42:0x46]==block(pair['return'],'control')[0x42:0x46] for e in selected),'collision input does not follow P1 wrapper')
    for label in ('object','random','owner','free','control','control2','collision_mask','multiplayer'):
        require(all(block(e,label)==block(done,label) for e in selected[5:]),'collision service mutated retained inputs/state')
