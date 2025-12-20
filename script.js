// Task Management System
let tasks = [];
let currentTaskId = null;

// Check authentication on page load
document.addEventListener('DOMContentLoaded', () => {
    checkAuthentication();
    loadTasks();
    loadTeamMembers();
    setupEventListeners();
    renderTasks();
});

// Check if user is authenticated
function checkAuthentication() {
    const token = localStorage.getItem('authToken');
    const username = localStorage.getItem('username');
    
    if (!token) {
        window.location.href = 'login.html';
        return;
    }
    
    // Display user info
    if (username) {
        const userInfoElement = document.getElementById('userInfo');
        if (userInfoElement) {
            userInfoElement.textContent = `👤 ${username}`;
        }
    }
    
    // Setup logout
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            localStorage.removeItem('authToken');
            localStorage.removeItem('userId');
            localStorage.removeItem('username');
            window.location.href = 'login.html';
        });
    }
}

// Use relative URL for API - works both locally and in production
const API_URL = window.location.origin + '/api';

// Get authentication headers
function getAuthHeaders() {
    const token = localStorage.getItem('authToken');
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
}

// Load team members from API
async function loadTeamMembers() {
    try {
        const response = await fetch(`${API_URL}/users`, {
            headers: getAuthHeaders()
        });
        
        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                localStorage.removeItem('authToken');
                localStorage.removeItem('userId');
                localStorage.removeItem('username');
                window.location.href = 'login.html';
                return;
            }
            throw new Error('Failed to load team members');
        }
        
        const users = await response.json();
        renderTeamMembers(users);
    } catch (error) {
        console.error('Error loading team members:', error);
    }
}

// Render team members in header
function renderTeamMembers(users) {
    const teamAvatarsContainer = document.querySelector('.team-avatars');
    if (!teamAvatarsContainer) return;
    
    // Clear existing avatars
    teamAvatarsContainer.innerHTML = '';
    
    // Show first 3 users
    const displayUsers = users.slice(0, 3);
    const remainingCount = users.length - 3;
    
    displayUsers.forEach(user => {
        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        avatar.title = user.fullName || user.username;
        avatar.textContent = user.initials || '?';
        teamAvatarsContainer.appendChild(avatar);
    });
    
    // Show "+X" if there are more users
    if (remainingCount > 0) {
        const moreAvatar = document.createElement('div');
        moreAvatar.className = 'avatar-more';
        moreAvatar.textContent = `+${remainingCount}`;
        moreAvatar.title = `${remainingCount} more team members`;
        teamAvatarsContainer.appendChild(moreAvatar);
    }
    
    // If no users, show placeholder
    if (users.length === 0) {
        const placeholder = document.createElement('div');
        placeholder.className = 'avatar';
        placeholder.textContent = '👤';
        placeholder.title = 'No team members yet';
        teamAvatarsContainer.appendChild(placeholder);
    }
}

// Load tasks from database
async function loadTasks() {
    try {
        const response = await fetch(`${API_URL}/tasks`, {
            headers: getAuthHeaders()
        });
        
        if (response.status === 401 || response.status === 403) {
            localStorage.removeItem('authToken');
            localStorage.removeItem('userId');
            localStorage.removeItem('username');
            window.location.href = 'login.html';
            return;
        }
        
        if (!response.ok) {
            throw new Error('Failed to load tasks');
        }
        
        tasks = await response.json();
        renderTasks();
    } catch (error) {
        console.error('Error loading tasks:', error);
        tasks = [];
        renderTasks();
    }
}

// Setup event listeners
function setupEventListeners() {
    const modal = document.getElementById('taskModal');
    const addTaskBtn = document.getElementById('addTaskBtn');
    const closeBtn = document.querySelector('.close');
    const cancelBtn = document.getElementById('cancelBtn');
    const taskForm = document.getElementById('taskForm');

    addTaskBtn.addEventListener('click', () => openModal());
    closeBtn.addEventListener('click', () => closeModal());
    cancelBtn.addEventListener('click', () => closeModal());
    taskForm.addEventListener('submit', handleFormSubmit);

    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });
}


// Open modal for adding/editing task
function openModal(taskId = null) {
    const modal = document.getElementById('taskModal');
    const modalTitle = document.getElementById('modalTitle');
    const form = document.getElementById('taskForm');
    
    currentTaskId = taskId;
    
    if (taskId) {
        // Edit mode
        modalTitle.textContent = 'Edit Task';
        const task = tasks.find(t => t.id === taskId);
        if (task) {
            document.getElementById('taskId').value = task.id;
            document.getElementById('taskType').value = task.type || 'task';
            document.getElementById('taskTitle').value = task.title;
            document.getElementById('taskDescription').value = task.description || '';
            document.getElementById('taskAssignee').value = task.assignee || '';
            document.getElementById('taskPriority').value = task.priority;
            document.getElementById('taskStatus').value = task.status === 'review' ? 'review' : task.status;
        }
    } else {
        // Add mode
        modalTitle.textContent = 'Add New Task';
        form.reset();
        document.getElementById('taskId').value = '';
    }
    
    modal.style.display = 'block';
}

// Close modal
function closeModal() {
    const modal = document.getElementById('taskModal');
    modal.style.display = 'none';
    currentTaskId = null;
    document.getElementById('taskForm').reset();
}

// Handle form submission
async function handleFormSubmit(e) {
    e.preventDefault();
    
    const taskId = document.getElementById('taskId').value;
    const type = document.getElementById('taskType').value;
    const title = document.getElementById('taskTitle').value;
    const description = document.getElementById('taskDescription').value;
    const assignee = document.getElementById('taskAssignee').value;
    const priority = document.getElementById('taskPriority').value;
    const status = document.getElementById('taskStatus').value;
    
    try {
        if (taskId) {
            // Update existing task
            const response = await fetch(`${API_URL}/tasks/${taskId}`, {
                method: 'PUT',
                headers: getAuthHeaders(),
                body: JSON.stringify({
                    type,
                    title,
                    description,
                    assignee,
                    priority,
                    status
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to update task');
            }
        } else {
            // Create new task
            const taskId = `AUTO-${Date.now().toString().slice(-3)}`;
            const response = await fetch(`${API_URL}/tasks`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({
                    type,
                    title,
                    description,
                    assignee,
                    priority,
                    status,
                    taskId
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to create task');
            }
        }
        
        await loadTasks();
        closeModal();
    } catch (error) {
        console.error('Error saving task:', error);
        alert('Failed to save task. Please try again.');
    }
}

// Generate unique ID
function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

// Generate task ID (like NUC-205)
let taskCounter = 1;
function generateTaskId() {
    const prefix = 'AUTO';
    const id = taskCounter++;
    return `${prefix}-${id}`;
}

// Delete task
async function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/tasks/${taskId}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete task');
        }
        
        await loadTasks();
    } catch (error) {
        console.error('Error deleting task:', error);
        alert('Failed to delete task. Please try again.');
    }
}

// Render all tasks
function renderTasks() {
    // Clear all columns
    document.querySelectorAll('.tasks').forEach(column => {
        column.innerHTML = '';
    });
    
    // Group tasks by status
    const tasksByStatus = {
        'backlog': tasks.filter(t => t.status === 'backlog' || !t.status),
        'todo': tasks.filter(t => t.status === 'todo'),
        'in-progress': tasks.filter(t => t.status === 'in-progress'),
        'review': tasks.filter(t => t.status === 'review'),
        'done': tasks.filter(t => t.status === 'done')
    };
    
    // Render tasks in each column
    Object.keys(tasksByStatus).forEach(status => {
        const column = document.getElementById(`${status}-tasks`);
        const taskList = tasksByStatus[status];
        
        if (taskList.length === 0) {
            column.innerHTML = '<div class="empty-state">No tasks</div>';
        } else {
            taskList.forEach(task => {
                column.appendChild(createTaskCard(task));
            });
        }
        
        // Update task count
        const countElement = document.getElementById(`${status}-count`);
        if (countElement) {
            countElement.textContent = taskList.length;
        }
    });
}

// Create task card element
function createTaskCard(task) {
    const card = document.createElement('div');
    card.className = `task-card priority-${task.priority}`;
    card.draggable = true;
    card.dataset.taskId = task.id;
    
    const issueType = task.type || 'task';
    const taskId = task.taskId || `AUTO-${task.id.substring(0, 3).toUpperCase()}`;
    const taskNumber = Math.floor(Math.random() * 9) + 1; // Random number 1-9 for demo
    
    // Get assignee initials for avatar
    const assigneeInitials = task.assignee 
        ? task.assignee.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2)
        : '?';
    
    // Priority icons
    const priorityIcons = {
        'low': '↓',
        'medium': '=',
        'high': '↑',
        'urgent': '⇈'
    };
    const priorityIcon = priorityIcons[task.priority] || '=';
    const priorityColor = task.priority === 'high' || task.priority === 'urgent' ? '#ff9800' : '#0052cc';
    
    // Issue type icon colors
    const typeIcons = {
        'task': '🔵',
        'story': '🟢',
        'bug': '🔴',
        'epic': '🟣'
    };
    const typeIcon = typeIcons[issueType] || '🔵';
    
    // Check if done
    const isDone = task.status === 'done';
    
    card.innerHTML = `
        <div class="task-actions">
            <button onclick="editTask('${task.id}')" title="Edit">✏️</button>
            <button onclick="deleteTask('${task.id}')" title="Delete">🗑️</button>
        </div>
        <div class="task-card-header">
            <div class="task-type-icon">${typeIcon}</div>
            <div class="task-id">${taskId}</div>
            <div class="task-number">${taskNumber}</div>
            ${isDone ? '<div class="task-done-icon">✓</div>' : ''}
        </div>
        <div class="task-title">${escapeHtml(task.title)}</div>
        <div class="task-card-footer">
            <div class="task-priority-icon" style="color: ${priorityColor}">${priorityIcon}</div>
            <div class="task-assignee-avatar-small">${assigneeInitials}</div>
        </div>
    `;
    
    // Add drag event listeners
    card.addEventListener('dragstart', handleDragStart);
    card.addEventListener('dragend', handleDragEnd);
    
    return card;
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Edit task
function editTask(taskId) {
    openModal(taskId);
}

// Drag and Drop handlers
let draggedElement = null;

function handleDragStart(e) {
    draggedElement = this;
    this.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', this.innerHTML);
}

function handleDragEnd(e) {
    this.classList.remove('dragging');
    draggedElement = null;
}

function allowDrop(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
}

async function handleDrop(e) {
    e.preventDefault();
    
    if (draggedElement) {
        const taskId = draggedElement.dataset.taskId;
        const newStatus = e.currentTarget.closest('.column').dataset.status;
        
        // Update task status
        const task = tasks.find(t => t.id === taskId);
        if (task && task.status !== newStatus) {
            try {
                const response = await fetch(`${API_URL}/tasks/${taskId}`, {
                    method: 'PUT',
                    headers: getAuthHeaders(),
                    body: JSON.stringify({
                        type: task.type,
                        title: task.title,
                        description: task.description,
                        assignee: task.assignee,
                        priority: task.priority,
                        status: newStatus
                    })
                });
                
                if (!response.ok) {
                    throw new Error('Failed to update task status');
                }
                
                await loadTasks();
            } catch (error) {
                console.error('Error updating task status:', error);
                await loadTasks(); // Reload to show correct state
            }
        }
    }
}

// Make functions globally available
window.editTask = editTask;
window.deleteTask = deleteTask;
window.handleDrop = handleDrop;
window.allowDrop = allowDrop;
