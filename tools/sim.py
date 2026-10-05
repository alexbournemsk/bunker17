#!/usr/bin/env python3
"""Симулятор баланса Бункера 17: гоняет игру без отрисовки в headless-браузере, вместо игрока - боты.
Запуск: python3 tools/sim.py [забегов на бота=150] [путь к html]
Боты (играют одним Растом, напарников не нанимают):
  novice - прицел жмет с задержкой, всегда в корпус ближайшему, покупает только винтовку
  mid    - выбирает зону по типу врага и цель по угрозе, покупает винтовку, потом ловушки
  pro    - как mid, но без задержки, взрывает подрывника в толпе, ловушки ставит на путь громил
Цель кривой: novice проигрывает около 5-й волны, mid доходит до 8-й, pro проходит 10."""
import asyncio,sys,json,os
from playwright.async_api import async_playwright
N=int(sys.argv[1]) if len(sys.argv)>1 else 150
SRC=sys.argv[2] if len(sys.argv)>2 else os.path.join(os.path.dirname(__file__),'..','src','bunker17.html')
HOOK=";window.G={get S(){return S},step,startWave,special,aimFire,ZONES,alive,dist,wpn,UNITS,EN,BAL,TRAP,DUR,nxt,canBuild,zChance,aimR,reset,WAVES,WALL,C,ui};"
JS=r"""
(N)=>{const {step,startWave,special,aimFire,ZONES,alive,dist,wpn,UNITS,EN,BAL,TRAP,DUR,nxt,canBuild,zChance,aimR,reset,WAVES,WALL,C}=G;
const Z=k=>ZONES.find(z=>z[0]===k),DT=1/60;
const BOTS={
 novice:{delay:1.6,zone:()=>'body',pick:(u,l)=>l.sort((a,b)=>dist(u,a)-dist(u,b))[0],traps:0},
 mid:{delay:.6,traps:2,
  zone:(e)=>e.type==='gunner'?(e.disarm>1?'body':'arms'):e.type==='bomber'?(e.y<WALL-140?'arms':'body'):e.type==='brute'||e.type==='boss'?(e.crip>2?'head':'legs'):e.type==='rat'?'body':'head',
  pick:(u,l)=>l.sort((a,b)=>dist(u,a)-dist(u,b))[0]},
 pro:{delay:.15,traps:4,
  zone:(e,S)=>{if(e.type==='gunner')return e.disarm>2?'head':'arms';
    if(e.type==='bomber'){const n=alive().filter(o=>o!==e&&dist(e,o)<BAL.bomber.r).length;return n>=1&&e.y<WALL-140?'arms':'legs'}
    if(e.type==='brute'||e.type==='boss')return e.crip>2?'head':'legs';
    return e.type==='rat'?'body':e.hp<wpn(S.units.hero).sp.dmg?'body':'head'},
  pick:(u,l)=>l.sort((a,b)=>thr(b)-thr(a))[0]}};
const thr=e=>(e.type==='gunner'&&e.y>=e.gy&&!(e.disarm>1)&&G.S.units.hero.hp<85?400:0)+(e.type==='bomber'?500:0)+(e.type==='brute'&&!(e.crip>1)?250:0)+e.y;
function run(bot){reset();const S=G.S;S.speed=0;const B=BOTS[bot],h=S.units.hero;let ready=0,stat={wave:0,win:false,door:[],hp:[]};
  while(!S.over){
    // между волнами: покупки
    const ni=nxt(h),nw=UNITS.hero.weapons[ni];if(nw&&S.scrap>=nw.cost&&bot!=='lazy'){S.scrap-=nw.cost;h.w=ni;h.scd=0}
    let tr=0;while(B.traps&&S.traps.length<B.traps+Math.floor(S.wave/3)&&S.scrap>=TRAP+(nxt(h)>=0?60:0)&&tr++<3){
      const c=Math.floor(Math.random()*8),r=bot==='pro'?6+Math.floor(Math.random()*2):3+Math.floor(Math.random()*5);if(canBuild(c,r)){S.scrap-=TRAP;S.traps.push({c,r,dur:DUR})}}
    startWave();let t=0;
    while(S.active&&!S.over&&t<600){step(DT);t+=DT;
      if(h.out||h.scd>0){ready=0;continue}
      const l=alive().filter(e=>dist(h,e)<=aimR(h)+EN[e.type].r);if(!l.length){ready=0;continue}
      ready+=DT;if(ready<B.delay)continue;ready=0;
      const tg=B.pick(h,l);special(h);if(!S.aim)continue;S.aim.tg=tg;aimFire(Z(B.zone(tg,S)))}
    if(t>=600){S.over=true;S.win=false;stat.stuck=1}
    if(!S.over||S.win){stat.wave=S.wave;stat.door.push(Math.round(S.door));stat.hp.push(Math.round(h.hp||0))}
    if(S.win)stat.win=true}
  if(!stat.win){stat.lost=S.wave;stat.why=S.door<=0?'d':stat.stuck?'s':'h'}return stat}
const out={};
for(const bot of ['novice','mid','pro']){const r=[];for(let i=0;i<N;i++)r.push(run(bot));
  const W=WAVES.length,pass=Array(W).fill(0),door=Array(W).fill(0),hp=Array(W).fill(0);
  for(const s of r)for(let w=0;w<s.door.length;w++){pass[w]++;door[w]+=s.door[w];hp[w]+=s.hp[w]}
  const lost=r.filter(s=>!s.win).map(s=>s.lost).sort((a,b)=>a-b);
  out[bot]={pass:pass.map(p=>Math.round(100*p/N)),door:door.map((d,i)=>pass[i]?Math.round(d/pass[i]):0),hp:hp.map((d,i)=>pass[i]?Math.round(d/pass[i]):0),
    win:Math.round(100*r.filter(s=>s.win).length/N),medLost:lost.length?lost[Math.floor(lost.length/2)]:null,stuck:r.filter(s=>s.stuck).length,byHp:Math.round(100*r.filter(s=>s.why==='h').length/N)}}
reset();return out}
"""
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch();pg=await b.new_page()
        h=open(SRC,encoding='utf8').read();i=h.rindex('})();');h=h[:i]+HOOK+h[i:]
        tmp='/tmp/b17sim.html';open(tmp,'w',encoding='utf8').write('<!doctype html><meta charset="utf-8"><body>'+h+'</body>')
        errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('file://'+tmp);await pg.wait_for_timeout(400)
        r=await pg.evaluate(JS,N);await b.close()
        W=len(r['novice']['pass'])
        print(f'забегов на бота: {N}\n')
        print('волна        '+''.join(f'{w+1:>5}' for w in range(W))+'   победа  медиана проигрыша / доля проигрышей по здоровью')
        for bot in r:
            d=r[bot]
            print(f'{bot:7} прош%'+''.join(f'{x:>5}' for x in d['pass'])+f"   {d['win']:>4}%   {d['medLost']}"+f"   выбыл отряд: {d['byHp']}%"+(f"  (зависло {d['stuck']})" if d['stuck'] else ''))
            print('        дверь'+''.join(f'{x:>5}' for x in d['door']))
            print('        hp   '+''.join(f'{x:>5}' for x in d['hp']))
        if errs:print('ошибки страницы:',errs[:3])
asyncio.run(main())
