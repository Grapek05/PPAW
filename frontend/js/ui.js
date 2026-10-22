const taskList = document.querySelector("#task-list");

function createTaskItem(task) {
  const item = document.createElement("li");
  item.className = "task";
  item.dataset.id = task.id;
  if (task.status === "done") {
    item.classList.add("task-done");
  }

  const title = document.createElement("span");
  title.className = "task-title";
  title.textContent = task.title;

  const priority = document.createElement("span");
  priority.className = `badge badge-${task.priority}`;
  priority.textContent = task.priority;

  item.append(title, priority);
  return item;
}

export function renderTasks(tasks) {
  taskList.replaceChildren(...tasks.map(createTaskItem));
}