// Файл: hud/renderer.js
document.addEventListener('DOMContentLoaded', () => {
    // Переключение вкладок
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.dataset.tab;
            
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            tab.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
        });
    });
    
    // Чат
    const messageInput = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');
    const messagesContainer = document.getElementById('messages');
    
    function addMessage(text, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user' : 'assistant'} typing`;
        messageDiv.textContent = text;
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    async function sendMessage() {
        const text = messageInput.value.trim();
        if (!text) return;
        
        addMessage(text, true);
        messageInput.value = '';
        
        try {
            const response = await fetch('http://localhost:8000/ws', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type: 'chat', payload: { text } })
            });
            
            // WebSocket будет использоваться в полной версии
            addMessage('Команда отправлена (демо режим)', false);
        } catch (error) {
            addMessage('Ошибка подключения к серверу', false);
        }
    }
    
    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
    
    // Микрофон (заглушка)
    const micBtn = document.getElementById('micBtn');
    micBtn.addEventListener('click', () => {
        alert('Голосовой ввод будет доступен в следующей версии');
    });
    
    // Загрузка задач
    async function loadTasks() {
        try {
            const response = await fetch('http://localhost:8000/tasks/list');
            const data = await response.json();
            
            const taskList = document.getElementById('taskList');
            taskList.innerHTML = '';
            
            data.tasks?.forEach(task => {
                const taskDiv = document.createElement('div');
                taskDiv.className = `task-item ${task.completed ? 'completed' : ''}`;
                taskDiv.innerHTML = `
                    <strong>${task.title}</strong>
                    <p>${task.description || ''}</p>
                `;
                taskList.appendChild(taskDiv);
            });
        } catch (error) {
            console.error('Error loading tasks:', error);
        }
    }
    
    window.createTask = () => {
        const title = prompt('Название задачи:');
        if (title) {
            addMessage(`Создание задачи: ${title}`, true);
        }
    };
    
    // Загрузка плагинов
    const pluginList = document.getElementById('pluginList');
    const plugins = ['weather', 'news', 'notes', 'calendar', 'daily_planner', 'routines', 'macros', 'tasks'];
    
    plugins.forEach(plugin => {
        const pluginDiv = document.createElement('div');
        pluginDiv.className = 'task-item';
        pluginDiv.innerHTML = `<strong>${plugin}</strong><br><small>Active</small>`;
        pluginList.appendChild(pluginDiv);
    });
});
