// Checks that the skill's script (skills/exposure-scale/scripts/exposure.py) computes the same
// questions, level, plan, cover, first step and links as the website (index.html) for many random answer sets.
// Run from the repo root: node tools/compare_logic.mjs [count]
import fs from 'fs'; import vm from 'vm'; import {execFileSync} from 'child_process';
const content=JSON.parse(fs.readFileSync('content.json','utf8'));
const html=fs.readFileSync('index.html','utf8');
const el=()=>({innerHTML:'',textContent:'',setAttribute(){}});
const ctx=vm.createContext({document:{documentElement:{dataset:{}},getElementById:el,querySelector:()=>null,addEventListener(){}},localStorage:{getItem:()=>null,setItem(){},removeItem(){}},
  location:{hash:''},history:{},window:{scrollTo(){}},fetch:()=>({then:()=>({then:g=>{g(content);return{catch(){}}}})})});
vm.runInContext(html.slice(html.lastIndexOf('<script>')+8,html.lastIndexOf('</script>')),ctx);
const js=code=>vm.runInContext(code,ctx);
let seed=11;const rnd=()=>(seed=(seed*1103515245+12345)%2**31)/2**31;
const N=+process.argv[2]||3000,cases=[];
for(let i=0;i<N;i++){
  js('S.a={};S.ov={};S.around=true'); // the terminal asks the optional questions too
  for(let g=0;g<30;g++){
    const q=JSON.parse(js('(()=>{const q=current();return JSON.stringify(q?{id:q.id,multi:!!q.multi,opts:q.options.map(o=>({v:o.value,x:!!o.exclusive}))}:null)})()'));
    if(!q||rnd()<0.03)break;
    let v;if(rnd()<0.08||!q.opts.length)v='skip';
    else if(q.multi){const ex=q.opts.filter(o=>o.x);if(ex.length&&rnd()<0.15)v=[ex[0].v];else{v=q.opts.filter(o=>!o.x&&rnd()<0.4).map(o=>o.v);if(!v.length)v=[q.opts.find(o=>!o.x).v]}}
    else v=q.opts[Math.floor(rnd()*q.opts.length)].v;
    js(`S.a[${JSON.stringify(q.id)}]=${JSON.stringify(v)}`);
  }
  if(rnd()<0.3)js(`S.ov[STEPS[${Math.floor(rnd()*content.steps.length)}].id]=${JSON.stringify(['done','todo','off'][Math.floor(rnd()*3)])}`);
  // draw every screen this state can show, so a rendering error fails the check too
  js(`for(const around of [true,false])for(const k of [undefined,1,2,3,4,5,'around']){S.around=around;S.lvOpen=k;S.more={0:true,1:true,2:true,3:true,4:true,5:true};S.show=k===1?'answers':k===2?'basis':null;render();if(placed())resultText()}S.around=true;S.cur=null`);
  cases.push(JSON.parse(js(`JSON.stringify({answers:S.a,overrides:S.ov,expect:{visible:visibleQuestions().map(q=>q.id),status:statusMap(),
    links:STEPS.map(s=>linksOf(s).map(l=>l.url)),level:levelOf(),placed:placed(),cover:cover(),first:(firstStep()||{id:null}).id}})`)));
}
const py=`
import json,sys,importlib.util
spec=importlib.util.spec_from_file_location("exposure","skills/exposure-scale/scripts/exposure.py");m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
bad=0
for c in json.load(sys.stdin):
    a=c["answers"];st={"answers":a,"overrides":c["overrides"],"checks":{}};v=m.visible(a)
    got={"visible":[q["id"] for q in v],"status":m.status_map(st),"links":[[l["url"] for l in m.links_of(s,a)] for s in m.STEPS],"level":m.level_of(a),"placed":m.placed(a),"cover":m.cover(st),"first":(m.first_step(st) or {"id":None})["id"]}
    for k,e in c["expect"].items():
        if got[k]!=e:
            bad+=1
            if bad<5: print("DIFF",k,json.dumps(a),"\\n web",json.dumps(e),"\\n py ",json.dumps(got[k]))
if bad: print(f"{bad} differences")
sys.exit(1 if bad else 0)
`;
try{execFileSync('python3',['-c',py],{input:JSON.stringify(cases),stdio:['pipe','inherit','inherit']});console.log(`Website and skill agree on all ${N} random answer sets, and every screen drew without an error.`)}
catch(e){console.log('Website and skill disagree.');process.exit(1)}
