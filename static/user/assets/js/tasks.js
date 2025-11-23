let tasks = [
      { name: "Buy Groceries", date: "2025-11-06", status: "pending" },
      { name: "Submit Project", date: "2025-11-07", status: "completed" },
      { name: "Team Meeting", date: "2025-11-18", status: "upcoming" }
    ];

    function renderTasks() {
      const container = document.getElementById('tasksContainer');
      if (!container) {
        console.error("Element with id 'tasksContainer' not found!");
        return;
      }

      container.innerHTML = '';
      const today = new Date().toISOString().split('T')[0]; // "2025-11-10"
      const currentPage = window.location.pathname.split('/').pop().replace('.html', '').toLowerCase();

      tasks.forEach((task, index) => {
        let show = false;

        // Determine which page we are on
        if (currentPage.includes("all")) show = true;
        if (currentPage.includes("pending") && task.status === "pending") show = true;
        if (currentPage.includes("completed") && task.status === "completed") show = true;
        if (currentPage.includes("today") && task.date === today) show = true;
        if (currentPage.includes("upcoming") && task.date > today) show = true;

        if (show) {
          const card = document.createElement('div');
          card.className = 'col-md-4 mb-3';
          card.innerHTML = `
            <div class="task-card">
              <h5>${task.name}</h5>
              <p class="mb-1"><strong>Due:</strong> ${task.date}</p>
              <span class="status ${task.status}">
                ${task.status.charAt(0).toUpperCase() + task.status.slice(1)}
              </span>
              <button onclick="deleteTask(${index})" class="delete-btn btn btn-sm btn-danger">Delete</button>
            </div>
          `;
          container.appendChild(card);
        }
      });
    }

    function deleteTask(index) {
      const task = tasks[index];
      if (confirm(`Delete task "${task.name}"?`)) {
        tasks.splice(index, 1);
        renderTasks();
      }
    }

    // Run when page loads
    document.addEventListener('DOMContentLoaded', renderTasks);