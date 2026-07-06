const events = [
  // WORLD TOUR
  { date:'2025-11-29', type:'LIVE', title:'Incheon / INSPIRE ARENA' },
  { date:'2025-11-30', type:'LIVE', title:'Incheon / INSPIRE ARENA' },
  { date:'2026-03-17', type:'LIVE', title:'Madrid / PALACIO VISTALEGRE' },
  { date:'2026-03-20', type:'LIVE', title:'Amsterdam / AFAS LIVE' },
  { date:'2026-03-22', type:'LIVE', title:'Paris / SALLE PLEYEL' },
  { date:'2026-03-24', type:'LIVE', title:'Frankfurt / MYTICKET JAHRHUNDERTHALLE' },
  { date:'2026-03-26', type:'LIVE', title:'London / EVENTIM APOLLO' },
  { date:'2026-03-29', type:'LIVE', title:'Toronto / GREAT CANADIAN TORONTO' },
  { date:'2026-03-31', type:'LIVE', title:'Brooklyn / BROOKLYN PARAMOUNT' },
  { date:'2026-04-02', type:'LIVE', title:'National Harbor / MGM NATIONAL HARBOR' },
  { date:'2026-04-04', type:'LIVE', title:'Irving / TOYOTA MUSIC FACTORY' },
  { date:'2026-04-07', type:'LIVE', title:'Oakland / PARAMOUNT THEATRE' },
  { date:'2026-04-09', type:'LIVE', title:'Los Angeles / YOUTUBE THEATER' },
  { date:'2026-08-08', type:'LIVE', title:'Tokyo / KEIO ARENA TOKYO' },
  { date:'2026-08-09', type:'LIVE', title:'Tokyo / KEIO ARENA TOKYO' },

  // JAPAN FC DEADLINES
  { date:'2026-03-13', type:'FC', title:'W会員先行 受付開始' },
  { date:'2026-03-26', type:'FC', title:'W会員先行 締切 23:59' },
  { date:'2026-03-27', type:'FC', title:'NSWER JAPAN先行 受付開始' },
  { date:'2026-04-05', type:'FC', title:'NSWER JAPAN先行 締切 23:59' },
  { date:'2026-04-06', type:'FC', title:'MOBILE先行 受付開始' },
  { date:'2026-04-15', type:'FC', title:'MOBILE先行 締切 23:59' },

  // MEMBER BIRTHDAYS
  { date:'2026-01-26', type:'BIRTHDAY', title:'SULLYOON Birthday' },
  { date:'2026-02-25', type:'BIRTHDAY', title:'HAEWON Birthday' },
  { date:'2026-04-13', type:'BIRTHDAY', title:'JIWOO Birthday' },
  { date:'2026-05-26', type:'BIRTHDAY', title:'KYUJIN Birthday' },
  { date:'2026-10-17', type:'BIRTHDAY', title:'LILY Birthday' },
  { date:'2026-12-28', type:'BIRTHDAY', title:'BAE Birthday' }
];

const TOKYO_START = '2026-08-08';
const upcomingEl = document.getElementById('upcoming');
const countdownDaysEl = document.getElementById('countdownDays');
const countdownMetaEl = document.getElementById('countdownMeta');
const calendarEl = document.getElementById('calendar');
const monthLabelEl = document.getElementById('monthLabel');

const today = new Date();
today.setHours(0,0,0,0);

function fmtJP(dateStr){
  const d = new Date(dateStr + 'T00:00:00');
  const y = d.getFullYear();
  const m = String(d.getMonth()+1).padStart(2,'0');
  const day = String(d.getDate()).padStart(2,'0');
  return `${y}.${m}.${day}`;
}

function typeClass(type){
  return type.toLowerCase();
}

function renderUpcoming(){
  const upcoming = events
    .filter(e => new Date(e.date + 'T00:00:00') >= today)
    .sort((a,b) => new Date(a.date) - new Date(b.date))
    .slice(0, 8);

  upcomingEl.innerHTML = '';
  upcoming.forEach(e => {
    const item = document.createElement('div');
    item.className = 'upcoming-item';
    item.innerHTML = `
      <div class="upcoming-date">${fmtJP(e.date)}</div>
      <div><span class="badge ${typeClass(e.type)}">${e.type}</span></div>
      <div class="upcoming-title">${e.title}</div>
    `;
    upcomingEl.appendChild(item);
  });
}

function renderCountdown(){
  const target = new Date(TOKYO_START + 'T00:00:00');
  const diff = Math.ceil((target - today) / (1000 * 60 * 60 * 24));
  countdownDaysEl.textContent = diff >= 0 ? diff : '0';
  countdownMetaEl.textContent = '2026.08.08 / KEIO ARENA TOKYO';
}

let currentMonth = today.getMonth();
let currentYear = today.getFullYear();

function eventsForDay(y,m,d){
  const dateStr = `${y}-${String(m+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
  return events.filter(e => e.date === dateStr);
}

function renderCalendar(){
  calendarEl.innerHTML = '';
  monthLabelEl.textContent = `${currentYear}.${String(currentMonth+1).padStart(2,'0')}`;

  const firstDay = new Date(currentYear, currentMonth, 1);
  const startWeekday = firstDay.getDay();
  const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
  const prevMonthDays = new Date(currentYear, currentMonth, 0).getDate();

  for(let i=0; i<startWeekday; i++){
    const prevDate = prevMonthDays - startWeekday + i + 1;
    const div = document.createElement('div');
    div.className = 'day other-month';
    div.innerHTML = `<div class="day-num">${prevDate}</div>`;
    calendarEl.appendChild(div);
  }

  for(let day=1; day<=daysInMonth; day++){
    const dayEvents = eventsForDay(currentYear, currentMonth, day);
    const div = document.createElement('div');
    div.className = 'day';
    const inner = document.createElement('div');
    inner.className = 'day-events';
    dayEvents.forEach(e => {
      const pill = document.createElement('div');
      pill.className = `day-pill ${typeClass(e.type)}`;
      pill.textContent = `${e.type} ${e.title}`;
      inner.appendChild(pill);
    });
    div.innerHTML = `<div class="day-num">${day}</div>`;
    div.appendChild(inner);
    calendarEl.appendChild(div);
  }

  const cells = startWeekday + daysInMonth;
  const remain = cells % 7 === 0 ? 0 : 7 - (cells % 7);
  for(let i=1; i<=remain; i++){
    const div = document.createElement('div');
    div.className = 'day other-month';
    div.innerHTML = `<div class="day-num">${i}</div>`;
    calendarEl.appendChild(div);
  }
}

document.getElementById('prevMonth').addEventListener('click', () => {
  currentMonth--;
  if(currentMonth < 0){
    currentMonth = 11;
    currentYear--;
  }
  renderCalendar();
});

document.getElementById('nextMonth').addEventListener('click', () => {
  currentMonth++;
  if(currentMonth > 11){
    currentMonth = 0;
    currentYear++;
  }
  renderCalendar();
});

renderCountdown();
renderUpcoming();
renderCalendar();
