// Checks the chat prompt that "Use your AI" copies (buildPrompt() in index.html): it must name every level,
// every question and option (except the self-guess, which the prompt asks itself), every step and every link,
// and stay under its size limit. The part a person reads, above the reference, has its own limit. Run from the repo root: node tools/check_prompt.mjs [--print]
import fs from 'fs'; import vm from 'vm';
const LIMIT=16000; // characters; long pastes still work, but every extra line costs the model's attention
const READ_LIMIT=1200; // the part above the reference, which a person should be able to read in seconds
const content=JSON.parse(fs.readFileSync('content.json','utf8'));
const html=fs.readFileSync('index.html','utf8');
const el=()=>({innerHTML:'',textContent:'',setAttribute(){}});
const ctx=vm.createContext({document:{documentElement:{dataset:{}},getElementById:el,querySelector:()=>null,addEventListener(){}},localStorage:{getItem:()=>null,setItem(){}},
  location:{hash:''},history:{},window:{scrollTo(){}},navigator:{},fetch:()=>({then:()=>({then:g=>{g(content);return{catch(){}}}})})});
vm.runInContext(html.slice(html.lastIndexOf('<script>')+8,html.lastIndexOf('</script>')),ctx);
const p=vm.runInContext('buildPrompt()',ctx);
if(process.argv.includes('--print')){console.log(p);process.exit(0)}
const missing=[];const need=(what,s)=>{if(!p.includes(s))missing.push(`${what}: ${s}`)};
content.levels.forEach(l=>{need('level',`${l.n} ${l.name}:`);[...l.guards,...l.climb].forEach(id=>need(`level ${l.n} step`,id))});
need('around',content.around.risk);
content.questions.filter(q=>q.place!=='self').forEach(q=>{need('question',`${q.id}: ${q.text}`);(q.options||[]).forEach(o=>need(`option of ${q.id}`,o.label))});
content.questions.find(q=>q.place==='self')||missing.push('no self-guess question');
content.steps.forEach(s=>{need('step',`${s.id}: ${s.title}`);(s.links||[]).forEach(l=>need(`link of ${s.id}`,l.url))});
['ai','aiLines','copied'].forEach(k=>{if(!content.intro[k])missing.push(`content.json intro.${k}`)});
if((content.intro.aiLines||[]).length!==3)missing.push('content.json intro.aiLines: three lines');
const ref=vm.runInContext('PROMPT_REF',ctx),readable=p.indexOf(ref);
if(readable<0)missing.push('reference marker');else if(readable>READ_LIMIT)missing.push(`readable part is ${readable} characters, limit ${READ_LIMIT}`);
missing.forEach(m=>console.log('MISSING',m));
if(p.length>LIMIT)console.log(`TOO LONG: ${p.length} characters, limit ${LIMIT}`);
if(missing.length||p.length>LIMIT)process.exit(1);
console.log(`Prompt covers ${content.levels.length} levels, ${content.questions.length-1} questions and ${content.steps.length} steps in ${p.length} characters (limit ${LIMIT}); the readable part is ${readable} (limit ${READ_LIMIT}).`);
