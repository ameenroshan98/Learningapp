const state = { token: localStorage.getItem('token') || '', user: null, courses: [] };

const views = document.querySelectorAll('.view');
document.querySelectorAll('.nav-btn').forEach(btn => btn.addEventListener('click', () => setView(btn.dataset.view, btn)));
function setView(id, btn) {
  views.forEach(v => v.classList.toggle('active', v.id === id));
  document.querySelectorAll('.nav-btn').forEach(n => n.classList.remove('active'));
  if (btn) btn.classList.add('active');
}

async function api(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const response = await fetch(path, { ...options, headers });
  if (!response.ok) throw new Error((await response.json()).detail || 'Request failed');
  const type = response.headers.get('content-type') || '';
  return type.includes('application/json') ? response.json() : response.text();
}

document.getElementById('loginForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const form = new FormData(e.target);
  try {
    const data = await api('/api/auth/login', { method: 'POST', body: JSON.stringify(Object.fromEntries(form.entries())) });
    state.token = data.access_token;
    state.user = data.user;
    localStorage.setItem('token', state.token);
    document.getElementById('loginMessage').textContent = `Welcome ${data.user.full_name}`;
    await loadDashboard();
    setView('dashboard', document.querySelector('[data-view="dashboard"]'));
  } catch (err) {
    document.getElementById('loginMessage').textContent = err.message;
  }
});

async function loadDashboard() {
  const data = await api('/api/dashboard');
  document.getElementById('userMeta').textContent = `${data.user.name} • ${data.user.role} • ${data.user.department} • ${data.user.employee_id}`;
  const metrics = Object.entries(data.metrics).map(([k, v]) => `<div class="metric"><div>${k.replaceAll('_', ' ')}</div><div class="value">${Array.isArray(v) ? v.length : v}</div></div>`).join('');
  document.getElementById('metricCards').innerHTML = metrics;
  document.getElementById('notifications').innerHTML = (data.notifications.length ? data.notifications : [{ message: 'No notifications' }]).map(n => `<p>• ${n.message}</p>`).join('');
  const leaderboard = data.leaderboard.sort((a, b) => b.points - a.points).slice(0, 5);
  document.getElementById('leaderboard').innerHTML = leaderboard.map((u, i) => `<p>${i + 1}. ${u.name} — ${u.department} (${u.points} pts)</p>`).join('');
  const chartData = data.metrics.department_completion || leaderboard.map(item => ({ department: item.department, completion_rate: item.points }));
  document.getElementById('completionChart').innerHTML = chartData.map(row => `<div class="chart-row"><label><span>${row.department}</span><span>${row.completion_rate}%</span></label><div class="progress"><span style="width:${Math.min(row.completion_rate, 100)}%"></span></div></div>`).join('');
}

document.getElementById('refreshDashboard').addEventListener('click', () => loadDashboard().catch(alert));

document.getElementById('loadCourses').addEventListener('click', async () => {
  try {
    state.courses = await api('/api/courses');
    document.getElementById('courseList').innerHTML = state.courses.map(course => `
      <div class="card course-card">
        <div class="badge">${course.department} • ${course.skill_level}</div>
        <h3>${course.title}</h3>
        <p>${course.description}</p>
        <small>${course.estimated_minutes} mins • ${course.module_count} module(s)</small>
        <div class="progress"><span style="width:${course.assignment?.progress_percent || 0}%"></span></div>
        <button onclick="showCourse(${course.id})">View Course</button>
      </div>`).join('');
  } catch (err) { alert(err.message); }
});

window.showCourse = async function(courseId) {
  const course = await api(`/api/courses/${courseId}`);
  const container = document.getElementById('courseDetails');
  container.classList.remove('hidden');
  container.innerHTML = `<h3>${course.title}</h3><p>${course.description}</p><p><strong>Department:</strong> ${course.department} | <strong>Skill:</strong> ${course.skill_level}</p>${course.modules.map(m => `<div class="metric"><strong>${m.title}</strong><p>${m.content_text || ''}</p><small>Module ID: ${m.id} • Questions: ${m.question_count}</small></div>`).join('')}`;
};

document.getElementById('loadQuiz').addEventListener('click', async () => {
  const moduleId = document.getElementById('moduleIdInput').value;
  if (!moduleId) return alert('Enter a module ID');
  try {
    const quiz = await api(`/api/modules/${moduleId}/quiz`);
    const form = document.getElementById('quizForm');
    form.classList.remove('hidden');
    form.dataset.moduleId = quiz.module_id;
    form.innerHTML = `<h3>${quiz.module_title}</h3><p>Pass score: ${quiz.pass_score}%</p>` + quiz.questions.map(q => `
      <div class="quiz-question">
        <p><strong>${q.prompt}</strong></p>
        ${Object.entries(q.options).map(([key, value]) => `<label class="quiz-option"><input type="radio" name="q_${q.id}" value="${key}" required /> ${key}. ${value}</label>`).join('')}
      </div>`).join('') + `<button type="submit">Submit Quiz</button>`;
  } catch (err) { alert(err.message); }
});

document.getElementById('quizForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const moduleId = Number(e.target.dataset.moduleId);
  const answers = {};
  new FormData(e.target).forEach((value, key) => answers[Number(key.replace('q_', ''))] = value);
  try {
    const result = await api('/api/quiz/submit', { method: 'POST', body: JSON.stringify({ module_id: moduleId, answers, time_spent_minutes: 10 }) });
    const panel = document.getElementById('quizResult');
    panel.classList.remove('hidden');
    panel.innerHTML = `<h3>${result.passed ? 'Passed' : 'Needs Retry'}</h3><p>Score: ${result.score}%</p><p>${result.correct_answers}/${result.total_questions} correct answers.</p>`;
  } catch (err) { alert(err.message); }
});

if (state.token) { loadDashboard().catch(() => localStorage.removeItem('token')); }
