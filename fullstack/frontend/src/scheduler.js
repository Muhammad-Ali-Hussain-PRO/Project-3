export function firstAvailable(earliest, latest, durationMinutes, events) {
  const duration = durationMinutes * 60000;
  if (!Number.isFinite(earliest) || !Number.isFinite(latest) || latest <= earliest || !Number.isInteger(durationMinutes) || durationMinutes < 5 || durationMinutes > 480 || latest - earliest > 7 * 86400000) throw new Error('Choose a valid time window and duration.');
  let cursor = earliest; const conflicts = [];
  for (const event of [...events].sort((a,b)=>a.start-b.start || a.end-b.end)) {
    if (event.end <= cursor) continue;
    if (cursor + duration <= event.start) break;
    if (cursor < event.end && cursor + duration > event.start) {conflicts.push(event); cursor = event.end;}
    if (cursor + duration > latest) return null;
  }
  return cursor + duration <= latest ? {start:cursor,end:cursor+duration,conflicts} : null;
}
export const overlaps = (a,b)=>a.start < b.end && a.end > b.start;
export function localInstant(day, time) {
  const result = new Date(`${day}T${time}:00`);
  const [year,month,date] = day.split('-').map(Number); const [hour,minute] = time.split(':').map(Number);
  if (!Number.isFinite(result.getTime()) || result.getFullYear()!==year || result.getMonth()!==month-1 || result.getDate()!==date || result.getHours()!==hour || result.getMinutes()!==minute) throw new Error('That local time does not exist. Choose another time.');
  return result.getTime();
}
