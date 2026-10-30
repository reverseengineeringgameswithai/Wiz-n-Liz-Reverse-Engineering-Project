"""Full retained fields, inactive occupancy and fixed-RTS phase evidence."""
from genesis_actor_capture import require,block,be

def return_only_fields(b):
    require(len(b)==78 and be(b,0x16,4)==be(b,0x46,4)==0x12646 and be(b,0x1a,4)==0,'return-only selectors differ')
    # Unrepresented bytes are verified zero, not silently discarded private state.
    require(b[1]==0 and be(b,0x14)==0 and b[0x1e:0x46]==bytes(40),'unmodeled return-only private/render fields')
    links={0:0,0xffff0690:1,0xffff0838:2};link=be(b,0x4a,4)
    require(link in links,'unmapped return-only control identity')
    return (be(b,2),be(b,4),be(b,18),b[0],be(b,6),be(b,8),be(b,10),b[12],b[13],be(b,14),be(b,16),links[link])

def validate_phase(events,begin,end):
    owner=begin['registers']['M68K A6'];sp=begin['registers']['M68K A7'];b=block(begin,'object')
    selected=[e for e in events if e['frame']==begin['frame'] and e['registers']['M68K A6']==owner]
    require(selected and selected[0]['sequence']==begin['sequence'] and selected[-1]['sequence']==end['sequence'],'return-only invocation outside the ordered phase')
    active=bool(b[0]&128)
    require([e['pc'] for e in selected]==([0x69aa,0xf76c,0x69b6,0x12646,0x69bc,0x69c0,0x12646,0x69c2] if active else [0x69aa,0x69c2]),'return-only dispatch order differs')
    for e in selected:
        return_only_fields(block(e,'object'))
        require(e['registers']['M68K A5']==begin['registers']['M68K A5'],'return-only changed control register')
        require(all(block(e,l)==block(begin,l) for l in ('actor','control','control2','scratch','free','random')),'return-only changed unrelated state')
    if not active:
        require(block(end,'object')==b and end['registers']['M68K A7']==sp and block(end,'stack')==block(begin,'stack'),'inactive return-only state/stack changed')
        return False
    _,pres,call,handler,done,service_call,service,finish=selected
    for e,caller in ((pres,0x69b6),(handler,0x69bc),(service,0x69c2)):
        require(e['registers']['M68K A7']==sp-4 and be(block(e,'stack'),0,4)==caller,'return-only caller stack differs')
    require(all(e['registers']['M68K A7']==sp and block(e,'stack')==block(begin,'stack') for e in (call,done,service_call,finish)),'return-only return stack differs')
    # 69B6 is before loading the handler; verify A0 at the actual RTS instead.
    require(handler['registers']['M68K A0']==service_call['registers']['M68K A0']==service['registers']['M68K A0']==0x12646,'return-only dispatch target differs')
    after=block(call,'object')
    require(all(b[i]==after[i] for i in range(78) if i not in (0,6,7,12)),'presentation changed uncontracted return-only field')
    require(all(block(e,'object')==after for e in selected[2:]),'RTS handler/service changed object')
    return True

def validate_write(e,base,active):
    offset=e['address']-base
    require(active and e['registers']['M68K A6']==base+0xff000000,'inactive/foreign return-only writer')
    presentation={0xf778:(12,1),0xf780:(12,1),0xf7a2:(6,2),0xf7b6:(0,1),0xf7ba:(6,2),
                  0xf7c2:(6,2),0xf7cc:(6,2),0xf7e0:(0,1),0xf7e4:(6,2),0xf7ec:(6,2)}
    require((e['pc'],offset,e['width'],e['value'])==(0xb12a,20,2,0) or presentation.get(e['pc'])==(offset,e['width']),'unmodeled return-only writer')
