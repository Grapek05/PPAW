import { ApiError, createTask, deleteTask, fetchTasks } from "./api.js";
import {
  hideFormError,
  hideListStatus,
  renderTasks,
  renderTotal,
  showFormError,
  showListError,
  showListLoading,
} from "./ui.js";

const form = document.querySelector("#task-form");
const submitButton = document.querySelector("#submit-button");
const reloadButton = document.querySelector("#reload-button");
const statusFilter = document.querySelector("#status-filter");
const taskList = document.querySelector("#task-list");

const PROJECT_ID = 1;

function describeError(error) {
  if (error instanceof ApiError) {
    const details = error.errors
      .map(({ field, message }) => `${field}: ${message}`)
      .join("\n");
    const summary = `Serwer odrzucił żądanie (${error.status}): ${error.message}`;
    return details ? `${summary}\n${details}` : summary;
  }
  return "Brak połączenia z API. Sprawdź, czy serwer działa.";
}

async function loadTasks() {
  showListLoading();
  try {
        const { items, totalHeader } = await fetchTasks({
      projectId: PROJECT_ID,
      status: statusFilter.value,
    });
    renderTasks(items);
    renderTotal(totalHeader);
    hideListStatus();
  } catch (error) {
    showListError(describeError(error));
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideFormError();
  const data = new FormData(form);
  submitButton.disabled = true;
  try {
    await createTask({
      project_id: PROJECT_ID,
      title: data.get("title"),
      priority: data.get("priority"),
    });
    form.reset();
    await loadTasks();
  } catch (error) {
    showFormError(describeError(error));
  } finally {
    submitButton.disabled = false;
  }
});

taskList.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-action='delete']");
  if (button === null) {
    return;
  }
  const taskId = button.closest(".task").dataset.id;
  button.disabled = true;
  try {
    await deleteTask(taskId);
    await loadTasks();
  } catch (error) {
    showListError(describeError(error));
    button.disabled = false;
  }
});

reloadButton.addEventListener("click", loadTasks);
statusFilter.addEventListener("change", loadTasks);

loadTasks();
