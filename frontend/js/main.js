import { createTask, fetchTasks } from "./api.js";
import { renderTasks } from "./ui.js";

async function loadTasks() {
  const tasks = await fetchTasks();
  renderTasks(tasks);
}

loadTasks();

const form = document.querySelector("#task-form");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = new FormData(form);
  await createTask({
    title: data.get("title"),
    priority: data.get("priority"),
  });
  form.reset();
  await loadTasks();
});
