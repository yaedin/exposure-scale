// Checks that the skill's script (skills/exposure-scale/scripts/exposure.py) computes the same
// questions, plan and links as the website (index.html) for many random answer sets.
// Run from the repo root: node tools/compare_logic.mjs [count]
import fs from 'fs'; import vm from 'vm'; import {execFileSync} from 'child_process';
const content=JSON.parse(fs.readFileSync('content.json','utf8'));
const html=fs.readFileSync('index.html','utf8');
const el=()=>({innerHTML:'',textContent:''});
const ctx=vm.createContext({document:{getElementById:el,querySelector:()=>null,addEventListener(){}},localStorage:{getItem:()=>null,setItem(){}},
  location:{hash:''},history:{},window:{scrollTo(){}},fetch:()=>({then:()=>({then:g=>{g(content);return{catch(){}}}})})});
vm.runInContext(html.slice(html.indexOf('<script>')+8,html.indexOf('</script>')),ctx);
const js=code=>vm.runInContext(code,ctx);
let seed=11;const rnd=()=>(seed=(seed*1103515245+12345)%2**31)/2**31;
const N=+process.argv[2]||3000,cases=[];
for(let i=0;i<N;i++){
  js('S.a={};S.ov={}');
  for(let g=0;g<30;g++){
    const q=JSON.parse(js('(()=>{const q=current();return JSON.stringify(q?{id:q.id,multi:!!q.multi,opts:optionsOf(q).map(o=>({v:o.value,x:!!o.exclusive}))}:null)})()'));
    if(!q||rnd()<0.03)break;
    let v;if(rnd()<0.08||!q.opts.length)v='skip';
    else if(q.multi){const ex=q.opts.filter(o=>o.x);if(ex.length&&rnd()<0.15)v=[ex[0].v];else{v=q.opts.filter(o=>!o.x&&rnd()<0.4).map(o=>o.v);if(!v.length)v=[q.opts.find(o=>!o.x).v]}}
    else v=q.opts[Math.floor(rnd()*q.opts.length)].v;
    js(`S.a[${JSON.stringify(q.id)}]=${JSON.stringify(v)}`);
  }
  if(rnd()<0.3)js(`S.ov[STEPS[${Math.floor(rnd()*content.steps.length)}].id]=${JSON.stringify(['done','todo','off'][Math.floor(rnd()*3)])}`);
  cases.push(JSON.parse(js(`JSON.stringify({answers:S.a,overrides:S.ov,expect:{visible:visibleQuestions().map(q=>q.id),status:statusMap(),
    options:visibleQuestions().map(q=>optionsOf(q).map(o=>o.value)),
    links:STEPS.map(s=>linksOf(s).map(l=>l.url)),lanes:STEPS.map(lane)}})`)));
}
const py=`
import json,sys,importlib.util
spec=importlib.util.spec_from_file_location("exposure","skills/exposure-scale/scripts/exposure.py");m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
bad=0
for c in json.load(sys.stdin):
    a=c["answers"];st={"answers":a,"overrides":c["overrides"],"checks":{}};v=m.visible(a)
    got={"visible":[q["id"] for q in v],"status":m.status_map(st),"options":[[o["value"] for o in m.options_of(q,a)] for q in v],"links":[[l["url"] for l in m.links_of(s,a)] for s in m.STEPS],"lanes":[m.lane(s) for s in m.STEPS]}
    for k,e in c["expect"].items():
        if got[k]!=e:
            bad+=1
            if bad<5: print("DIFF",k,json.dumps(a),"\\n web",json.dumps(e),"\\n py ",json.dumps(got[k]))
if bad: print(f"{bad} differences")
sys.exit(1 if bad else 0)
`;
try{execFileSync('python3',['-c',py],{input:JSON.stringify(cases),stdio:['pipe','inherit','inherit']});console.log(`Website and skill agree on all ${N} random answer sets.`)}
catch(e){console.log('Website and skill disagree.');process.exit(1)}
