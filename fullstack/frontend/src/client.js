import {firstAvailable,overlaps} from './scheduler';
export const demo = import.meta.env.VITE_DEMO === 'true';
const storageKey = 'chronosai-demo-v2';
let token;
export function dayString(date=new Date()) {return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`;}
function seed() {
 const date=dayString();return [
  {id:'sample-1',title:'Sample · Project planning',start:+new Date(date+'T09:30:00'),end:+new Date(date+'T10:30:00')},
  {id:'sample-2',title:'Sample · Study session',start:+new Date(date+'T11:30:00'),end:+new Date(date+'T12:00:00')}
 ];
}
function readDemo() {
 const raw=localStorage.getItem(storageKey);
 if (!raw) {const data=seed();writeDemo(data);return data;}
 const data=JSON.parse(raw);
 if (!Array.isArray(data)||data.some(e=>typeof e.title!=='string'||!Number.isFinite(e.start)||!Number.isFinite(e.end)||e.end<=e.start)) throw new Error('Saved demo data could not be read. Reset the demo to start again.');
 return data;
}
function writeDemo(events) {localStorage.setItem(storageKey,JSON.stringify(events));}
async function api(path,options={}) {
 if (!token) {token=localStorage.getItem('chronosai-workspace-token');if(!token){token=crypto.randomUUID().replaceAll('-','')+crypto.randomUUID().replaceAll('-','');localStorage.setItem('chronosai-workspace-token',token);}}
 const response=await fetch('/api'+path,{...options,headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`},signal:AbortSignal.timeout(10000)});
 if (response.status===204) return {};
 const result=await response.json();
 if(!response.ok) {let message=typeof result.detail==='string'?result.detail:'Check your event details and try again.';throw new Error(message);}
 return result;
}
export const client = {
 async list(){return demo?readDemo():(await api('/events')).events;},
 async suggest(earliest,latest,duration){
  if(!demo)return api('/suggestions',{method:'POST',body:JSON.stringify({earliest:new Date(earliest).toISOString(),latest:new Date(latest).toISOString(),duration_minutes:duration})});
  const slot=firstAvailable(earliest,latest,duration,readDemo());
  if(!slot)throw new Error('No free slot fits this window. Extend the window or shorten the event.');
  return slot;
 },
 async book(title,slot,key){
  if(!demo)return (await api('/events',{method:'POST',body:JSON.stringify({title,start:new Date(slot.start).toISOString(),end:new Date(slot.end).toISOString(),request_key:key})})).event;
  const events=readDemo();const old=events.find(e=>e.request_key===key);
  if(old){if(old.title!==title||old.start!==slot.start||old.end!==slot.end)throw new Error('This request was already used. Find another time.');return old;}
  if(events.some(e=>overlaps(e,slot)))throw new Error('That slot is no longer free. Find another time and try again.');
  if(events.length>=500)throw new Error('Delete an event before adding another.');
  const event={id:crypto.randomUUID(),title,start:slot.start,end:slot.end,request_key:key};writeDemo([...events,event]);return event;
 },
 async remove(id){if(!demo)return api('/events/'+encodeURIComponent(id),{method:'DELETE'});writeDemo(readDemo().filter(e=>e.id!==id));},
 async reset(){if(demo)writeDemo(seed());}
};
